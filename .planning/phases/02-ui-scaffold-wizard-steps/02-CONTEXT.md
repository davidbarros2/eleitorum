# Phase 2: UI Scaffold + Wizard Steps - Context

**Gathered:** 2026-05-23
**Status:** Ready for planning

<domain>
## Phase Boundary

Build the complete PySide6 application — QApplication entry point, QStackedWidget wizard with all six steps plus a dedicated processing screen, QThread worker with progress reporting, light/dark theme system (QSS-based), menu bar, About dialog, first-run welcome screen (QDialog modal), window chrome, and QSettings persistence — all wired to the Phase 1 pipeline without modifying it.

**In scope:** WIZ-01–11, APP-01–20, BRAND-01–02, TST-10, PERF-02

**Out of scope:** any modification of Phase 1 core modules; integration/E2E tests (Phase 3); icon ICO/PNG generation from SVG (Phase 4); build script and CI (Phase 4)

</domain>

<decisions>
## Implementation Decisions

### Cancel During Processing
- **D-01:** When the user clicks "Cancelar" during processing, a confirmation dialog appears: "Tem a certeza que quer cancelar?" If confirmed, the QThread worker is signalled to stop via a `threading.Event` (checked every 100 rows at the progress_cb call sites); the wizard returns to step 3 (column mapping). If declined, processing continues.
  - Rationale: confirmation prevents accidental cancellation; returning to step 3 (not step 1) allows the user to correct column mapping without reloading the file.

### First-Run Welcome Screen
- **D-02:** The welcome screen (APP-16) is implemented as a `QDialog` (modal) that appears over the main window on first launch, before the QStackedWidget is shown. "Começar" closes the dialog. Re-accessed via Ajuda menu using the same `QDialog`. QSettings flag `first_run_shown` prevents repeat display.
  - Rationale: does not add a step to the QStackedWidget; simpler navigation logic; same component reused for menu access.

### "Ver Detalhes" in Preview Step
- **D-03:** In step 4 (preview), the "Ver detalhes" link toggles a collapsible `QTextEdit` (read-only) inline below the summary panel. Height ~150px, vertical scroll enabled, full content (no truncation). Clicking "Ver detalhes" again collapses it.
  - Rationale: keeps the user in the same step without modal interruption; height-constrained area with scroll handles large logs gracefully.

### Application Icon in Phase 2
- **D-04:** `src/eleitorum/resources/icon.svg` is created in Phase 2, implementing BRAND-02 exactly (white letter "E" centred on a rounded-corner red square, `#a21a1c`, 16% corner radius). `QIcon` loads the SVG directly for the window icon in Phase 2. The `scripts/generate_icons.py` script that exports PNG/ICO sizes is Phase 4 (BLD-05).
  - Rationale: the window has a proper branded icon immediately; no blocking dependency on Phase 4.

### SessionModel Architecture
- **D-05:** A plain Python `@dataclass` (`SessionModel`) is defined in `src/eleitorum/ui/wizard.py` (or a dedicated `src/eleitorum/ui/session.py`). It holds all wizard session state: `output_type`, `source_path`, `sheet_name`, `column_map`, `pipeline_result`, `output_path`. Wizard creates one instance and passes it to each step widget via constructor. Steps read and write it directly.
  - Rationale: no Qt dependency in the data layer; trivially testable without QApplication; type-safe with type hints; no signals needed for state passing.

### Theme System
- **D-06:** `src/eleitorum/ui/theme.py` defines two QSS string constants (light and dark) using the palettes from Spec Section 9.4 and REQUIREMENTS.md:
  - Light: background `#FAFAFA`, primary text `#1A1A1A`, accent `#a21a1c`
  - Dark: background `#1A1A1A`, primary text `#F5F5F5`, accent `#C73E40`
  - Theme switching calls `QApplication.instance().setStyleSheet(qss)` — instant, no restart.
  - On first launch: system theme detected via `Qt.ColorScheme` (PySide6 6.5+); fallback to light if unavailable or indeterminate.
  - Theme choice persisted via `QSettings`.
  - Rationale: full control over accent colours and all widget states; standard PySide6 pattern; avoids QPalette limitations for custom accent.

### Processing Trigger and Flow
- **D-07:** When the user clicks "Próximo" on step 3 (column mapping), the QStackedWidget advances to a dedicated processing widget (step 3.5 — not a numbered step for the user, but a separate QWidget in the stack). This widget shows:
  - Indeterminate progress bar while the reader loads the file
  - Switches to determinate bar ("A validar linha N de M…") once row count is known (first `progress_cb` call with `total_rows > 0`)
  - "Cancelar" button (triggers D-01 flow)
  - On success: auto-advances to step 4 (preview)
  - On pipeline error: auto-advances to step 6-error screen
  - Rationale: cleaner than embedding loading state into step 4; user understands they are in a processing phase, not stuck; Cancel is clearly available.

### Claude's Discretion
- QThread subclass design: `PipelineWorker(QThread)` emitting `progress(int, int)`, `finished(PipelineResult)`, and `error(str)` signals. The processing widget connects to these signals.
- NavBar layout: footer with Anterior/Próximo/Cancelar using `QHBoxLayout`; Anterior disabled on step 1; Próximo button text overridden to "Escolher destino e gravar" on step 4.
- Step indicator: `QLabel` in header or footer showing "Passo N de 5" (or "Passo N de 6" on multi-sheet path); updates on each step advance.
- `QSettings` organization: `EleitorUM/EleitorUM` (company/app) storing `window/geometry`, `window/state`, `app/last_directory`, `app/theme`, `app/first_run_shown`.
- Inter font loading: `QFontDatabase.addApplicationFont()` from `sys._MEIPASS` path (PyInstaller) or package path; fallback chain Inter → system UI → sans-serif.
- WCAG AA contrast verification: manual check during implementation against the specified palette; no automated tool required in Phase 2.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Primary Specification
- `.planning/Eleitorum.md` — canonical specification — Sections most relevant to Phase 2:
  - Section 9: User Interface (wizard flow, step-by-step spec, accessibility, theming, menu bar, About dialog)
  - Section 9.4: Theming — colour palettes for light and dark themes (WCAG AA requirement)
  - Section 9.5: Wizard flow — full specification of all 6 steps including step 2.5 (multi-sheet)
  - Section 9.6: Menu bar and About dialog — exact content required
  - Section 9.7: Accessibility requirements (keyboard nav, focus indicators, icon+text pairing)
  - Section 13.2: Repository/module structure (exact file layout for `src/eleitorum/ui/`)
  - Section 3.5: UMinho disclaimer text (verbatim required in About dialog and README)

### Requirements (authoritative IDs and precise values)
- `.planning/REQUIREMENTS.md` — requirement IDs WIZ-01–11, APP-01–20, BRAND-01–02, TST-10, PERF-02 with exact numerical values (min window 600×500, initial 900×650, ~50 preview rows, ~150k row performance, QSettings keys)

### Phase Scope and Success Criteria
- `.planning/ROADMAP.md` §"Phase 2: UI Scaffold + Wizard Steps" — five success criteria that define "done" for this phase

### Phase 1 Pipeline API (integration contract)
- `.planning/phases/01-core-pipeline/01-CONTEXT.md` §D-04 — pipeline entry point: `run_pipeline(source, output_type, progress_cb=None)` where `progress_cb: Callable[[int, int], None] | None` receives `(current_row, total_rows)`. Called every 100 rows + final. This signature MUST NOT be changed.
- `src/eleitorum/core/pipeline.py` — actual implementation of `run_pipeline`; read to understand what it returns and what exceptions it raises

### Tech Stack Rationale
- `CLAUDE.md` — technology decisions (PySide6 6.11.1 LGPL, Inter font bundled, QSettings pattern, PyInstaller one-folder primary build)

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `src/eleitorum/config.py` — `APP_NAME = "EleitorUM"` constant. All window titles, log names, About dialog, and QSettings organization MUST read from this. Do not hardcode the string.
- `src/eleitorum/core/pipeline.py` — `run_pipeline(source, output_type, progress_cb)` is the single integration seam between Phase 1 and Phase 2's QThread worker. Signature is fixed.
- `src/eleitorum/core/errors.py` — custom exception hierarchy with PT-PT messages. The QThread worker catches these and emits them via `error(str)` signal to the processing widget.
- `src/eleitorum/__main__.py` — stub `main()` function that raises `NotImplementedError("Phase 2 wires the UI entry point")`. Phase 2 replaces this with the QApplication launcher.

### Established Patterns (from Phase 1)
- All PT-PT user-facing strings centralized in one module — the pattern is `strings.py` for UI (mirrors Phase 1's `errors.py` for core). No scattered string literals in widget code.
- Fail-fast philosophy: if any validation error occurs, no output. The UI must clearly surface this via the error screen (step 6-error).
- `progress_cb` is called every 100 rows + final row — the determinate progress bar updates at this granularity.

### Integration Points
- **`src/eleitorum/__main__.py → main()`** — Phase 2 replaces the stub. Entry point creates `QApplication`, applies theme, shows main window, calls `app.exec()`.
- **`pipeline.run_pipeline()`** — called by `PipelineWorker.run()` in a `QThread`. Worker emits `progress`, `finished`, or `error` signals. Processing widget receives these signals and updates the UI.
- **`src/eleitorum/core/errors.py`** — `PipelineError` subclasses propagate to the error screen via the `error` signal. The error screen reads `.message` (PT-PT string) for display.
- **`tests/conftest.py`** — `PYSIDE6_CALL_MAIN_LOOP = False` and `qt_api = pyside6` already expected by pytest-qt (TST-10 requirement). Phase 2 must set `qt_api = pyside6` in `pyproject.toml`.

</code_context>

<specifics>
## Specific Ideas

- **Processing screen position in QStackedWidget:** The processing widget (step 3.5) is a full widget in the QStackedWidget, not a dialog. It has its own entry in the stack index so the Anterior/Próximo footer is hidden during processing (no navigation during active processing — only Cancel).

- **"Reiniciar" action (WIZ-10):** Menu item in Ficheiro and/or keyboard shortcut. Resets the `SessionModel` to a fresh instance and navigates QStackedWidget back to index 0 (step 1). Does not close the window.

- **Multi-sheet path step count:** The step indicator shows "Passo N de 6" when step 2.5 (sheet picker) is present; "Passo N de 5" on the normal path. The wizard tracks whether the loaded file has multiple sheets and adjusts the indicator accordingly.

- **Icon drop zone hover state (WIZ-02):** The drop zone uses a dashed `QFrame` border that changes colour on `dragEnterEvent` (from neutral grey to accent `#a21a1c`) and resets on `dragLeaveEvent` or `dropEvent`. This is pure QSS + event override, no external library.

- **Output path conflict (VAL-08, WIZ-06):** If the native save-file dialog returns a path equal to the input file path, the dialog is rejected inline with a PT-PT message and the native dialog reopens. Not a separate step — handled within step 5 (save).

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 2-UI Scaffold + Wizard Steps*
*Context gathered: 2026-05-23*
