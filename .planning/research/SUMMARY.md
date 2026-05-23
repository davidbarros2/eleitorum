# Research Summary — EleitorUM

**Project:** EleitorUM
**Domain:** Windows desktop data-normalization wizard (single-purpose institutional utility)
**Researched:** 2026-05-23
**Confidence:** HIGH

---

## Recommended Stack (validated)

| Library | Pinned version | Key note |
|---------|---------------|----------|
| Python | 3.11 (min) | Required by pandas 3.0; sweet spot of maturity and performance |
| PySide6 | `>=6.11.1,<7` | LGPL — no source disclosure for closed-source EXE; prefer over GPL PyQt6 |
| pandas | `>=3.0.3,<4` | Input normalization pipeline; CoW is mandatory in 3.0 — use `.loc` everywhere |
| openpyxl | `>=3.1.5,<4` | XLSX/XLSM reading; always use `read_only=True, data_only=True` for large files |
| xlrd | `>=2.0.2,<3` | Legacy `.xls` only; XLS is its only responsibility — never route XLSX through it |
| odfpy | `>=1.4.1,<2` | Required for `pd.read_excel(engine="odf")`; stable, slow cadence, no alternative |
| charset-normalizer | `>=3.4.7,<4` | Clean MIT license; 10–100x faster than chardet; avoids chardet v7 licensing dispute |
| stdlib `csv` | (stdlib) | Byte-exact output control; `newline=""` + `lineterminator="\r\n"` + `utf-8-sig` |
| PyInstaller | `>=6.20.0,<7` | Industry standard; pair with `pyinstaller-hooks-contrib` at all times |
| ruff | `>=0.15.14` | Replaces flake8 + isort + black; single tool for lint and format |
| mypy | `>=2.1.0,<3` | Better pandas-stubs compatibility than pyright for this codebase |
| pytest | `>=9.0.3,<10` | Standard; requires Python >=3.10 |
| pytest-qt | `>=4.5.0,<5` | PySide6-aware test helpers; must set `qt_api = pyside6` in `pyproject.toml` |

---

## Architecture Decisions

- **QStackedWidget over QWizard.** QWizard's chrome resists QSS theming, its button management conflicts with per-step hiding requirements, and its field-registration system adds indirection. A `QStackedWidget` with a custom `NavBar` and `StepIndicator` widget gives full control in ~80 lines and eliminates all wizard-chrome surprises. This decision must be made before any pages are built.

- **Shared `SessionModel` dataclass, not inter-step signals.** A single `@dataclass` owned by `MainWindow` and passed by reference to every step widget is the cleanest cross-step data transport. Each step reads from it on activation and writes to it on completion. Steps remain independently testable with a pre-populated model without a running `QApplication`.

- **`QThread + moveToThread` worker, not `QRunnable`.** EleitorUM has exactly one cancellable pipeline run per session. The `moveToThread` pattern gives clean signal-based progress reporting and mid-row cancellation via a `_cancelled` flag. `QRunnable`/`QThreadPool` is for parallel or repeated tasks — not the right fit here. Workers must never touch widgets directly; they emit signals only.

- **Unified `load_file()` with explicit engine routing.** A single function dispatches to `pd.read_excel` (openpyxl for XLSX, xlrd for XLS, odf for ODS) or `pd.read_csv` (charset-normalizer + sniffer). Always pass `dtype=object, keep_default_na=False` so every cell arrives as a raw Python string, preventing pandas from silently converting numeric mecanograficos to floats or dates to Timestamps.

- **stdlib `csv` for all output, never `pandas.to_csv`.** `pandas.to_csv` has historically been inconsistent about BOM, exact quoting, and line-ending control. The required output recipe opens with `encoding="utf-8-sig", newline=""` and uses `csv.writer(delimiter=";", quoting=csv.QUOTE_NONE, lineterminator="\r\n")`. This produces byte-exact, predictable output with no surprises.

- **Core pipeline has zero Qt imports.** `reader.py`, `normalizer.py`, `validator.py`, `pipeline.py`, `log_builder.py`, and `output.py` import only stdlib and pandas. They can be tested without a `QApplication`. All Qt interaction lives in `src/eleitorum/ui/`. This boundary is enforced from day one.

- **One-folder (`--onedir`) ZIP as the primary deliverable.** University IT environments with Windows Defender real-time protection regularly push `--onefile` cold-start above 8–15 seconds due to temp-directory extraction scanning. One-folder startup is near-instant. Ship as `EleitorUM-1.0.0-win64.zip` containing the folder. Only switch to `--onefile` if a clean-VM benchmark shows cold-start under 3 seconds.

---

## Table Stakes Features

Ordered by user-trust impact. If any of these are missing or broken, the tool will be abandoned.

1. **Fail-fast, no partial output.** Any validation failure must block output entirely. The `_ERRORS_` file is the user's record. A partial CSV submitted to the electoral platform causes silent downstream rejection with no recovery path.

2. **Clear, actionable PT-PT error messages.** Structure: what went wrong → where (1-indexed row matching Excel row, column name as seen in source header) → what to do next. Never expose Python exception types, stack traces, or internal field names.

3. **Progress indication during processing.** Indeterminate bar while loading (row count unknown); determinate bar with "A validar linha N de M…" once row count is known. The window must stay responsive (background thread). A frozen-looking UI is indistinguishable from a crash for the target user.

4. **Drag-and-drop file acceptance.** The drop zone must span the entire first step, change appearance on hover, and populate the same field as the Browse button. Non-developer users reach for drag-and-drop before looking for a button.

5. **Summary panel with transformation statistics before save.** Show input rows, output rows, rows removed (with reason breakdown), fields normalised, encoding detected. The user is about to submit to an institutional system — they need a confidence check.

6. **Never overwrite the input file.** Default output name is `caderno_eleitoral_YYYYMMDD_HHMMSS.csv` in the same directory. Refuse to write to the input path even if the user selects it explicitly. Auto-append counter suffix if the default path exists.

7. **First-run welcome screen.** Single screen explaining the 5-step flow in plain PT-PT. Shown once (flag in QSettings). Re-accessible via Ajuda menu. No "don't show again" checkbox — just close it.

---

## Top 5 Pitfalls to Address Immediately

Ordered by risk to the project. Each entry states the specific prevention action.

1. **Worker thread accessing Qt widgets directly** (non-deterministic crashes, race-dependent).
   Prevention: establish the `QObject + moveToThread` signal pattern in `processing_step.py` before writing any background logic. Workers emit `progress(int)`, `finished(object)`, `error(str)` signals only. Connect to widget slots via queued connections from the main thread. Never call `processEvents()` inside the pipeline.

2. **`csv.writer` double-newline bug on Windows** (`\r\n` in text mode becomes `\r\r\n`, producing blank lines between every row in the output).
   Prevention: every output `open()` call must include `newline=""`. Add a byte-level test immediately: read the output file in binary mode, split on `b"\r\n"`, and assert no unexpected empty elements. This bug cannot be retrofitted across many write sites.

3. **PyInstaller missing Qt platform plugin (`qwindows.dll`)** (EXE crashes before window opens, only on clean machines).
   Prevention: add `collect_data_files('PySide6', includes=['plugins/**/*'])` to the `.spec` `datas` list. Make a clean-VM smoke test (no Python installed) a mandatory gate before any user distribution. Never declare a build done based solely on the developer's machine.

4. **openpyxl default mode peak RAM on 150k-row files + `read_only` dimension bug** (silent row truncation or OOM).
   Prevention: always open XLSX as `load_workbook(path, read_only=True, data_only=True)`. Never rely on `ws.max_row` for correctness — iterate rows and stop on an all-None sentinel. Use an indeterminate progress bar until row count is known from actual iteration.

5. **Encoding misdetection on short or ambiguous CSV files** (mojibake output, no exception raised, platform rejects silently).
   Prevention: read the first 64 KB before calling `charset_normalizer.from_bytes()`. If a BOM is present, trust it unconditionally and skip detection. Set a minimum confidence threshold of 0.85; below that, show a manual encoding selector. Detection must happen at file-select step, not at validation — a misdetected encoding wastes all subsequent user effort.

---

## Flags for Requirements and Roadmap

Items from research that should directly influence how requirements are written or how phases are sequenced.

**Phase sequencing constraint — core before UI.** The dependency graph is strict: `models.py` → `validator.py` → `normalizer.py` → `log_builder.py` → `reader.py` → `detector.py` → `output.py` → `pipeline.py` → UI. Each layer is independently testable before the next is started. Phase 1 (core pipeline) must reach >=90% unit-test coverage before Phase 2 (UI) begins. This prevents the UI from masking pipeline correctness problems until late in the project.

**Row number convention must be decided once and documented.** Every error message, log entry, and preview row label must use the same convention. Recommendation: 1-indexed, matching Excel row numbers (data row 1 = Excel row 2, header is row 1). This must be a stated requirement, not an implementation detail.

**QStackedWidget architecture must be chosen before any UI page is built.** Switching from QWizard after pages exist requires rebuilding all navigation logic. Lock this decision at the start of Phase 2 (UI scaffold).

**Two separate output artifacts with distinct audiences.** `_ERRORS_` (failure only, problem report for user and colleague) and `_LOG_` (success only, audit trail for institutional accountability) must never be merged. Requirements should treat them as separate deliverables with separate formats.

**The eligiveis output is a separate artifact with a different transformation chain.** The caderno is `mecanografico;nome;category(empty)`. The eligiveis is `index(0-based);designation` sorted alphabetically. Requirements should call out their different pipelines explicitly or they will be conflated during implementation.

**Column mapping step should always be shown, even when auto-detection succeeds.** Pre-populating with detected values costs the user 2 seconds. Silently skipping it misses the ~10% of cases where detection is mechanically right but semantically wrong.

**BOM in output requires product owner validation before tagging v1.0.0.** The implementation recipe (`utf-8-sig`) is confirmed correct. However, the product owner must test the output against the live electoral platform before the requirement is confirmed. Design `output.py` so dropping the BOM is a one-line change.

**PyInstaller build mode requires a hardware benchmark, not a research decision.** The requirement should state: build one-folder by default; benchmark cold-start on a representative university laptop with Windows Defender enabled; switch to one-file only if under 3 seconds. The build script must support both modes from the start.

---

## Open Questions Before v1.0.0

Items requiring product owner validation or empirical measurement — not resolvable by further research.

1. **BOM confirmation.** Does the electoral platform accept output with the UTF-8 BOM (`\xef\xbb\xbf`)? The spec assumes yes (inferred from working sample files). One test against the live platform resolves this permanently.

2. **F/D/B cross-prefix uniqueness rule.** The spec states F, D, and B mecanograficos share a numeric namespace for uniqueness checking. Must be confirmed against UMinho HR documentation — cannot be inferred from file samples alone. A wrong assumption here causes valid files to be rejected or invalid files to pass.

3. **Eligiveis sort key.** The spec states alphabetical sort by designation. Confirm: sort by full designation string, or by surname only? Portuguese institutional names sometimes appear surname-first ("SILVA, Joao"). The sort key determines correctness.

4. **Mecanografico valid prefixes are exhaustive.** The spec lists A, PG, ID, F, D, B, Q, EX. Older employees may have unlisted prefixes. The validator's behavior for unknown prefixes (reject vs. warn-and-continue) must be decided with the product owner before implementation.

5. **PyInstaller one-file cold-start on target hardware.** Measure on a representative university administrative laptop (budget CPU, spinning or SATA SSD, Defender real-time enabled). Cannot be known without the measurement.

6. **Trailing CRLF acceptance.** `csv.writer` always writes a lineterminator after the last row. Confirm the platform parser does not treat trailing CRLF as an extra empty row.

7. **Category column format in caderno.** The spec says category is always empty. Confirm: should output be `mec;nome;` (trailing semicolon, three fields) or `mec;nome` (two fields only)? These are not byte-equivalent and the platform's parser behavior on a two-field row is unknown.

---

*Research completed: 2026-05-23*
*Ready for roadmap: yes*
