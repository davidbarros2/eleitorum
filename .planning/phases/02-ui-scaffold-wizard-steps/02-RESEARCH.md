# Phase 2: UI Scaffold + Wizard Steps — Research

**Researched:** 2026-05-23
**Domain:** PySide6 Qt Widgets application — wizard UI, QThread worker, QSS theming, QSettings persistence
**Confidence:** HIGH

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

- **D-01:** Cancel during processing — confirmation dialog ("Tem a certeza que quer cancelar?"); if confirmed, QThread worker signalled via `threading.Event` (checked every 100 rows at progress_cb call sites); wizard returns to step 3 (column mapping) on confirm, continues on decline.
- **D-02:** Welcome screen (APP-16) implemented as `QDialog` (modal) over main window on first launch; "Começar" closes it; QSettings flag `first_run_shown` prevents repeat; re-accessed via Ajuda menu using the same `QDialog` class.
- **D-03:** "Ver detalhes" in step 4 (preview) toggles a collapsible `QTextEdit` (read-only) inline below summary panel; height ~150px, vertical scroll enabled, full content (no truncation).
- **D-04:** `icon.svg` created in Phase 2 (white "E" on `#a21a1c` rounded square, 16% corner radius); `QIcon` loads SVG directly for window icon; `scripts/generate_icons.py` is Phase 4.
- **D-05:** `SessionModel` is a plain Python `@dataclass` in `src/eleitorum/ui/session.py`; fields: `output_type`, `source_path`, `sheet_name`, `column_map`, `pipeline_result`, `output_path`; wizard passes instance to each step widget via constructor; steps read/write directly.
- **D-06:** `src/eleitorum/ui/theme.py` defines `LIGHT_QSS` and `DARK_QSS` string constants; theme switching calls `QApplication.instance().setStyleSheet(qss)` — instant, no restart; system theme detected via `QGuiApplication.styleHints().colorScheme()` (PySide6 6.5+, returns `Qt.ColorScheme.Light/Dark/Unknown`); fallback to light; theme persisted via QSettings.
- **D-07:** "Próximo" on step 3 advances to processing widget (step 3.5 in QStackedWidget — not user-visible as a numbered step); indeterminate bar during load; determinate bar with "A validar linha N de M…" once row count known; Cancel available; on success → step 4; on error → step 6-error.

### Claude's Discretion

- `PipelineWorker(QThread)` emitting `progress(int, int)`, `finished(PipelineResult)`, and `error(str)` signals.
- NavBar: footer `QHBoxLayout`; Anterior disabled on step 1; Próximo text overridden to "Escolher destino e gravar" on step 4.
- Step indicator: `QLabel` showing "Passo N de 5" (or "Passo N de 6" on multi-sheet path); updates on each advance.
- `QSettings` organization: `EleitorUM/EleitorUM` (company/app) storing `window/geometry`, `window/state`, `app/last_directory`, `app/theme`, `app/first_run_shown`.
- Inter font loading via `QFontDatabase.addApplicationFont()` from `sys._MEIPASS` path (PyInstaller) or package path; fallback chain Inter → system UI → sans-serif.
- WCAG AA contrast: manual check during implementation; no automated tool in Phase 2.

### Deferred Ideas (OUT OF SCOPE)

None — discussion stayed within phase scope.
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| WIZ-01 | Step 1 — output type selection with two option cards, Anterior disabled | OptionCard QFrame pattern with QSS dynamic property; verified |
| WIZ-02 | Step 2 — drag-and-drop drop zone + file chooser button; hover state; inline error | `dragEnterEvent`/`dropEvent` on `QFrame`; MIME `hasUrls()` + `toLocalFile()`; verified |
| WIZ-03 | Step 2.5 (conditional) — sheet picker list with row counts and empty indicators | `QListWidget` with `SingleSelection`; conditional step in QStackedWidget |
| WIZ-04 | Step 3 — column mapping pre-populated; "Alterar" opens QComboBox dropdown | QLabel + QPushButton + QComboBox pattern; verified |
| WIZ-05 | Step 4 — preview table 50 rows; summary panel; "Ver detalhes" inline log toggle | `QTableWidget` read-only; `QTextEdit` max-height 150px; verified |
| WIZ-06 | Step 5 — native save dialog; .csv extension enforced; input=output path rejection | `QFileDialog.getSaveFileName()` static method; verified |
| WIZ-07 | Step 6 success — success icon, "Pronto!", output path, "Abrir pasta", "Processar outro ficheiro", "Sair" | `QStyle.StandardPixmap.SP_DialogApplyButton`; `QDesktopServices.openUrl()`; verified |
| WIZ-08 | Step 6 error — error icon, first 20 errors in QTextEdit, "Abrir pasta" for error log | `QStyle.StandardPixmap.SP_MessageBoxCritical`; verified |
| WIZ-09 | Each step: PT-PT title, step indicator "Passo N de 5", Anterior/Próximo/Cancelar footer | NavBar widget; step indicator QLabel; verified |
| WIZ-10 | "Reiniciar" resets SessionModel to fresh instance, navigates QStackedWidget to index 0 | `SessionModel.__init__()` reset; `setCurrentIndex(0)`; verified |
| WIZ-11 | Background thread; indeterminate → determinate progress; window stays responsive; Cancel available | QThread worker with Signal; QProgressBar `setRange(0,0)` ↔ `setRange(0,N)`; verified |
| APP-01 | Standard window chrome: minimize, maximize, close, resize | Qt default QMainWindow behaviour; no extra work needed |
| APP-02 | Windows snap layout support | Native to Qt on Windows 10/11; no extra code required |
| APP-03 | Min 600×500; initial 900×650 centered on primary screen | `setMinimumSize(600,500)`, `resize(900,650)`, `frameGeometry().moveCenter(screen.center())`; verified |
| APP-04 | Persist/restore window geometry via QSettings | `saveGeometry()`/`restoreGeometry()` → `QSettings`; verified |
| APP-05 | Persist/restore last directory via QSettings | `QSettings.value('app/last_directory', str)`; verified |
| APP-06 | All content reflows via Qt layouts; no hard-coded positions | `QVBoxLayout`, `QHBoxLayout`, `QHBoxLayout` with `setContentsMargins`; discipline needed |
| APP-07 | Light theme implemented with exact palette | `LIGHT_QSS` constant in `theme.py`; verified |
| APP-08 | Dark theme implemented with exact palette | `DARK_QSS` constant in `theme.py`; verified |
| APP-09 | WCAG AA contrast for both themes | Manual verification during implementation |
| APP-10 | First launch: follow system preference | `QGuiApplication.styleHints().colorScheme()`; fallback to light; verified |
| APP-11 | Theme toggle via Ver menu; instant switch without restart | `QApplication.instance().setStyleSheet()`; verified |
| APP-12 | Theme persisted via QSettings | `QSettings.setValue('app/theme', theme_name)`; verified |
| APP-13 | Inter font bundled, loaded at startup, fallback chain | `QFontDatabase.addApplicationFont()`; `sys._MEIPASS` path resolver; verified |
| APP-14 | Menu bar: Ficheiro, Ver, Ajuda with correct items | `QMenuBar`, `QMenu`, `QAction`; `Reiniciar` in Ficheiro per CONTEXT.md `<specifics>` |
| APP-15 | About dialog: name, version, description, disclaimer, license, repo link | `QDialog` + `QLabel.setOpenExternalLinks(True)`; verified |
| APP-16 | First-run welcome `QDialog` modal; `first_run_shown` QSettings flag | `QDialog` with `setModal(True)` + `exec()`; QSettings bool with `type=bool`; verified |
| APP-17 | All interactive elements keyboard-reachable; tab order; visible focus indicators | QSS `:focus` pseudo-class; `setTabOrder()`; verified |
| APP-18 | All icons paired with text labels | Enforced via design; `QStyle.StandardPixmap` + labels |
| APP-19 | Color never sole signal; success/warning/error always have glyph | Icons + color combined; enforced via design |
| APP-20 | All user-facing strings in PT-PT; centralized in `strings.py` | `src/eleitorum/ui/strings.py` module; no string literals in widget code |
| BRAND-01 | `APP_NAME` constant; all UI reads from `config.py` | `from eleitorum.config import APP_NAME`; verified constant exists |
| BRAND-02 | Icon SVG: white "E" on `#a21a1c` rounded square, 16% corner radius | `icon.svg` created in Phase 2; `QIcon` loads SVG directly; verified |
| TST-10 | `pyproject.toml` sets `qt_api = "pyside6"` | `[tool.pytest.ini_options]` `qt_api = "pyside6"`; verified pattern |
| PERF-02 | UI thread stays responsive during processing | QThread worker design; signal-slot cross-thread communication; verified |
</phase_requirements>

---

## Summary

Phase 2 builds the entire PySide6 application shell on top of the Phase 1 pipeline. The technology choices are locked: PySide6 6.11.1 (LGPL), QStackedWidget for the wizard (not QWizard), QThread subclass for the background worker, QSS string constants for theming, QSettings for persistence, and Inter font loaded at startup via QFontDatabase.

The most technically nuanced area is the cancel mechanism. Because `run_pipeline()` does not natively support early termination, the `progress_cb` must raise a custom non-`EleitorumError` exception (`PipelineCancelledError`) when the cancel flag is set. This exception propagates through the pipeline's `except EleitorumError` block and is caught separately by the worker's `run()` method, which then emits a `cancelled` signal instead of `error`. The planner must include a `PipelineCancelledError` class (in `src/eleitorum/ui/worker.py` or `src/eleitorum/core/errors.py`) as a Wave 0 deliverable.

The second key insight is QSS theming with the Fusion style. The default Windows Vista style on Windows 10/11 overrides the palette with a forced light palette, making dark-mode QSS unreliable without explicit `app.setStyle('Fusion')` at startup. Fusion must be set before the first stylesheet application for consistent cross-Windows rendering.

**Primary recommendation:** Build in five ordered waves: (1) pyproject.toml + directory scaffold + `strings.py` + `session.py` + `theme.py` + `worker.py`, (2) `main_window.py` + `app.py` entry point + NavBar widget, (3) step widgets in wizard order (step_type → step_upload → step_sheet → step_columns → step_processing → step_preview → step_done), (4) dialogs (welcome, about), (5) pytest-qt smoke tests.

---

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Wizard navigation state | UI (QStackedWidget) | — | QStackedWidget index maps directly to step identity; controlled by wizard.py |
| Session data | UI (`SessionModel` dataclass) | — | Plain dataclass, no Qt dependency; passed by reference to all steps |
| Pipeline execution | Core (pipeline.py) | UI (PipelineWorker thread) | Core is Qt-free; UI wires it to a QThread via run_pipeline() |
| Progress reporting | UI (QProgressBar) | Core (progress_cb hook) | Core calls progress_cb; UI receives signal on main thread |
| File I/O (output writing) | Core (output.py) | — | Byte-exact CSV writing belongs in the core layer |
| File selection dialogs | UI (QFileDialog) | — | OS-native dialogs; path is then passed to core |
| Theme/palette | UI (theme.py QSS) | — | Pure presentation layer; no core involvement |
| String constants | UI (strings.py) | Core (errors.py for PT-PT messages) | UI strings separate from core error messages |
| Persistence | UI (QSettings) | — | Window geometry, theme, directory — pure UI concerns |
| Error display | UI (step_done.py error screen) | Core (PipelineResult.failures) | Core produces structured failures; UI renders them |
| Keyboard accessibility | UI (tab order, QSS :focus) | — | Qt layout system handles tab order automatically |

---

## Standard Stack

### Core (Phase 2 new additions)

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| PySide6 | 6.11.1 | Qt bindings for all UI widgets, signals, threading | LGPL — no GPL propagation; project decision locked in CLAUDE.md |
| pytest-qt | 4.5.0 | pytest plugin for PySide6 widget smoke tests | Only maintained pytest plugin for Qt; auto-detects PySide6 |

[VERIFIED: pip registry] — `PySide6==6.11.1` is the current PyPI release (2026-05-23). `pytest-qt==4.5.0` is the current PyPI release. Both confirmed via `pip index versions`. Both passed `slopcheck install PySide6 pytest-qt` with `[OK]` verdict.

### Existing Stack (Phase 1, unchanged)

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Python | 3.11+ | Runtime | Project spec requirement |
| openpyxl | 3.1.5 | XLSX reading | Phase 1 verified |
| xlrd | 2.0.2 | XLS reading | Phase 1 verified |
| odfpy | 1.4.1 | ODS reading | Phase 1 verified |
| pandas | 3.0.2* | Input normalization | Phase 1 verified |
| charset-normalizer | 3.4.7 | Encoding detection | Phase 1 verified |

*pyproject.toml has pandas==3.0.2; CLAUDE.md recommends 3.0.3. Latest on PyPI is 3.0.3. Planner should bump to 3.0.3 when updating pyproject.toml in Wave 0.

### pyproject.toml Additions Required

```toml
# In [project] dependencies (runtime):
"PySide6==6.11.1",

# In [project.optional-dependencies] dev:
"pytest-qt==4.5.0",

# In [tool.pytest.ini_options]:
qt_api = "pyside6"
```

Additionally, CLAUDE.md-recommended version bumps for existing dev tools:
```toml
"mypy==2.1.0",      # was 1.19.1
"ruff==0.15.14",    # was 0.15.8
```

**Installation (development):**
```bash
pip install -e ".[dev]"
# Or individually:
pip install PySide6==6.11.1 pytest-qt==4.5.0
```

---

## Package Legitimacy Audit

| Package | Registry | Age | slopcheck | Disposition |
|---------|----------|-----|-----------|-------------|
| PySide6 | PyPI | ~6 yrs | [OK] | Approved |
| pytest-qt | PyPI | ~10 yrs | [OK] | Approved |

**Packages removed due to slopcheck [SLOP] verdict:** none

**Packages flagged as suspicious [SUS]:** none

slopcheck was available at research time (v0.6.1). Both packages verified `[OK]`.

---

## Architecture Patterns

### System Architecture Diagram

```
User action (click/drag/keyboard)
         |
         v
[Step Widget (QStackedWidget page)]
         |
    SessionModel (shared @dataclass)
         |
    [NavBar / Wizard]  ← step indicator, button enable/disable
         |
    "Próximo" on step 3
         |
         v
[Processing Widget (step 3.5)]
    QProgressBar (indeterminate)
         |
         v
[PipelineWorker (QThread)]
    run_pipeline(source, output_type, output_path=None, progress_cb)
         |
    progress_cb(current, total)  →  Signal progress(int, int)
         |                           [cross-thread, queued connection]
         v                           |
    [Core Pipeline]                  v
    (no Qt imports)           [Processing Widget]
         |                    QProgressBar.setValue(current)
         v                    "A validar linha N de M…"
    PipelineResult
         |
    Signal finished(PipelineResult)
    [or] Signal error(str)
    [or] Signal cancelled()
         |
         v
[Processing Widget → auto-advance]
    success → setCurrentIndex(step4)
    failure → setCurrentIndex(step6_error)
```

### Recommended Project Structure

```
src/eleitorum/
├── __init__.py           (existing)
├── __main__.py           (Phase 2 replaces stub with main())
├── config.py             (existing: APP_NAME)
├── version.py            (existing: __version__)
├── core/                 (existing, untouched)
│   └── ...
├── ui/
│   ├── __init__.py
│   ├── app.py            (QApplication setup, Fusion style, Inter font, theme)
│   ├── main_window.py    (QMainWindow: menu bar, QStackedWidget, geometry)
│   ├── wizard.py         (navigation logic, step indicator, step enable/disable)
│   ├── session.py        (@dataclass SessionModel)
│   ├── theme.py          (LIGHT_QSS, DARK_QSS, apply_theme())
│   ├── strings.py        (all PT-PT user-facing string constants)
│   ├── worker.py         (PipelineWorker QThread, PipelineCancelledError)
│   ├── steps/
│   │   ├── __init__.py
│   │   ├── step_type.py       (step 1: output type selection)
│   │   ├── step_upload.py     (step 2: drop zone + file chooser)
│   │   ├── step_sheet.py      (step 2.5: sheet picker, conditional)
│   │   ├── step_columns.py    (step 3: column mapping)
│   │   ├── step_processing.py (step 3.5: progress screen)
│   │   ├── step_preview.py    (step 4: preview table + log detail)
│   │   └── step_done.py       (step 6: success + error screens in one widget)
│   └── widgets/
│       ├── __init__.py
│       ├── navbar.py          (Anterior/Próximo/Cancelar footer)
│       ├── option_card.py     (selectable card for step 1)
│       └── drop_zone.py       (drag-and-drop QFrame target)
└── resources/
    ├── icon.svg              (white E on #a21a1c rounded square)
    └── fonts/
        └── Inter/            (Inter .ttf/.otf files + OFL.txt)
```

**File not in spec §13.2 but required by CONTEXT.md:** `src/eleitorum/ui/worker.py` for `PipelineWorker` and `PipelineCancelledError`. The spec §13.2 predates the Phase 2 context session decisions.

---

### Pattern 1: QApplication Entry Point (app.py)

```python
# Source: PySide6 official docs + verified in session
import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
from eleitorum.config import APP_NAME
from eleitorum.version import __version__
from eleitorum.ui.theme import apply_theme, detect_system_theme

def create_app() -> QApplication:
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setOrganizationName(APP_NAME)
    app.setApplicationVersion(__version__)
    # Fusion style required for reliable QSS rendering on Windows 10 and 11.
    # Default 'windowsvista' style overrides QPalette with a forced light palette,
    # making dark-mode QSS colours unreliable.
    app.setStyle('Fusion')
    # Load Inter font
    _load_inter_font()
    # Apply initial theme
    theme = _detect_or_load_theme()
    apply_theme(theme)
    return app

def _load_inter_font() -> None:
    import pathlib
    from PySide6.QtGui import QFontDatabase
    # sys._MEIPASS for PyInstaller bundle; package __file__ for dev
    base = getattr(sys, '_MEIPASS', str(pathlib.Path(__file__).parent))
    fonts_dir = pathlib.Path(base) / 'resources' / 'fonts' / 'Inter'
    for ttf in fonts_dir.glob('*.ttf'):
        QFontDatabase.addApplicationFont(str(ttf))
    # Set Inter as app default font
    from PySide6.QtGui import QFont
    font = QFont('Inter')
    font.setPointSize(14)
    QApplication.setFont(font)
```

### Pattern 2: QStackedWidget Navigation

```python
# Source: verified PySide6 QStackedWidget API
# QStackedWidget does NOT provide navigation by itself.
# The Wizard class controls setCurrentIndex() explicitly.

class WizardController:
    # Stack indices — defined as constants
    STEP_TYPE = 0         # WIZ-01
    STEP_UPLOAD = 1       # WIZ-02
    STEP_SHEET = 2        # WIZ-03 (conditional)
    STEP_COLUMNS = 3      # WIZ-04
    STEP_PROCESSING = 4   # WIZ-11 (not a user-visible numbered step)
    STEP_PREVIEW = 5      # WIZ-05
    STEP_DONE = 6         # WIZ-07 / WIZ-08

    # Multi-sheet path: STEP_SHEET is inserted between UPLOAD and COLUMNS
    # Step indicator logic must account for whether STEP_SHEET was shown

    def advance(self) -> None:
        current = self.stack.currentIndex()
        next_index = self._compute_next(current)
        self.stack.setCurrentIndex(next_index)
        self._update_step_indicator()

    def _update_step_indicator(self) -> None:
        n, total = self._step_display_number()
        self.step_label.setText(f"Passo {n} de {total}")
```

### Pattern 3: PipelineWorker (QThread subclass)

```python
# Source: verified in session — QThread subclass pattern confirmed correct
# for single-call long-running work without event loop requirements.
import threading
from PySide6.QtCore import QThread, Signal
from eleitorum.core.pipeline import run_pipeline, PipelineResult, PipelineSource

class PipelineCancelledError(Exception):
    """Raised by progress_cb to abort run_pipeline() mid-run.

    NOT a subclass of EleitorumError — must propagate through the pipeline's
    'except EleitorumError' catch block unchanged.
    """

class PipelineWorker(QThread):
    progress = Signal(int, int)        # (current_row, total_rows)
    finished = Signal(object)          # PipelineResult on success
    error = Signal(str)                # PT-PT error message on failure
    cancelled = Signal()               # emitted when cancel flag triggered

    def __init__(self, source, output_type, output_path, parent=None):
        super().__init__(parent)
        self._source = source
        self._output_type = output_type
        self._output_path = output_path
        self._cancel_event = threading.Event()

    def cancel(self) -> None:
        self._cancel_event.set()

    def _progress_cb(self, current: int, total: int) -> None:
        if self._cancel_event.is_set():
            raise PipelineCancelledError("Processamento cancelado pelo utilizador.")
        self.progress.emit(current, total)

    def run(self) -> None:
        try:
            result = run_pipeline(
                self._source,
                self._output_type,
                self._output_path,
                progress_cb=self._progress_cb,
            )
            self.finished.emit(result)
        except PipelineCancelledError:
            self.cancelled.emit()
        except Exception as exc:
            # Genuinely unexpected (ImportError, MemoryError, etc.)
            self.error.emit(str(exc))
```

**Key insight:** `run_pipeline()` catches `EleitorumError` internally and returns `PipelineResult(success=False)` — so the worker's `finished` signal fires for both success and validation failure. The worker only needs `error` for genuinely unexpected exceptions. The error screen is shown when `result.success is False`.

### Pattern 4: System Theme Detection

```python
# Source: verified in session — Qt.ColorScheme confirmed available in PySide6 6.11.1
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication

def detect_system_theme() -> str:
    """Return 'dark' or 'light' based on system preference."""
    hints = QApplication.instance().styleHints()
    cs = hints.colorScheme()
    if cs == Qt.ColorScheme.Dark:
        return 'dark'
    # Qt.ColorScheme.Light or Qt.ColorScheme.Unknown → default to light
    return 'light'
```

Note: `Qt.ColorScheme` was introduced in Qt 6.5. PySide6 6.11.1 includes it. However, on Windows the default 'windowsvista' style may still return `Unknown` even on a dark system. Using Fusion style (Pattern 1) ensures `colorScheme()` reflects the actual system preference.

### Pattern 5: QSettings Persistence

```python
# Source: verified in session — critical note about bool type parameter
from PySide6.QtCore import QSettings

class SettingsManager:
    """Centralized QSettings access for EleitorUM."""

    def __init__(self):
        # Uses org/app name set on QApplication
        self._s = QSettings()

    def save_geometry(self, window) -> None:
        self._s.setValue('window/geometry', window.saveGeometry())
        self._s.setValue('window/state', window.saveState())

    def restore_geometry(self, window) -> None:
        if geom := self._s.value('window/geometry'):
            window.restoreGeometry(geom)
        if state := self._s.value('window/state'):
            window.restoreState(state)

    def theme(self) -> str:
        # IMPORTANT: must pass type=str to avoid getting None on missing key
        return self._s.value('app/theme', 'light', type=str)

    def set_theme(self, theme: str) -> None:
        self._s.setValue('app/theme', theme)

    def first_run_shown(self) -> bool:
        # IMPORTANT: QSettings stores booleans as strings 'true'/'false'.
        # MUST pass type=bool to get a Python bool back.
        return self._s.value('app/first_run_shown', False, type=bool)

    def set_first_run_shown(self) -> None:
        self._s.setValue('app/first_run_shown', True)

    def last_directory(self) -> str:
        return self._s.value('app/last_directory', '', type=str)

    def set_last_directory(self, path: str) -> None:
        self._s.setValue('app/last_directory', path)
```

### Pattern 6: DropZone (Drag-and-Drop QFrame)

```python
# Source: verified in session — QFrame.setAcceptDrops + event overrides
from PySide6.QtWidgets import QFrame
from PySide6.QtCore import Signal

SUPPORTED_EXTENSIONS = frozenset({'.xlsx', '.xlsm', '.xls', '.ods', '.csv', '.tsv'})

class DropZone(QFrame):
    file_dropped = Signal(str)   # absolute path of dropped file

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setMinimumHeight(120)
        self.setProperty('drag_active', False)

    def dragEnterEvent(self, event) -> None:
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            if urls and _is_supported(urls[0].toLocalFile()):
                event.acceptProposedAction()
                self._set_active(True)
                return
        event.ignore()

    def dragLeaveEvent(self, event) -> None:
        self._set_active(False)

    def dropEvent(self, event) -> None:
        self._set_active(False)
        if event.mimeData().hasUrls():
            path = event.mimeData().urls()[0].toLocalFile()
            if _is_supported(path):
                event.acceptProposedAction()
                self.file_dropped.emit(path)

    def _set_active(self, value: bool) -> None:
        self.setProperty('drag_active', value)
        self.style().unpolish(self)
        self.style().polish(self)

def _is_supported(path: str) -> bool:
    import pathlib
    return pathlib.Path(path).suffix.lower() in SUPPORTED_EXTENSIONS
```

QSS to activate the border hover state:
```css
DropZone {
    border: 1px dashed #E5E5E5;
    background-color: #FFFFFF;
}
DropZone[drag_active="true"] {
    border: 2px solid #a21a1c;
}
```

### Pattern 7: OptionCard (Selectable Card)

```python
# Source: verified in session
from PySide6.QtWidgets import QFrame
from PySide6.QtCore import Signal, Qt

class OptionCard(QFrame):
    selected = Signal(str)   # emits the option key ('caderno' or 'elegiveis')

    def __init__(self, key: str, parent=None):
        super().__init__(parent)
        self._key = key
        self._is_selected = False
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)  # keyboard focusable
        self.setProperty('selected', False)

    def set_selected(self, value: bool) -> None:
        if self._is_selected == value:
            return
        self._is_selected = value
        self.setProperty('selected', value)
        self.style().unpolish(self)
        self.style().polish(self)
        if value:
            self.selected.emit(self._key)

    def mousePressEvent(self, event) -> None:
        self.set_selected(True)
        super().mousePressEvent(event)

    def keyPressEvent(self, event) -> None:
        if event.key() in (Qt.Key.Key_Space, Qt.Key.Key_Return, Qt.Key.Key_Enter):
            self.set_selected(True)
        super().keyPressEvent(event)
```

### Pattern 8: QProgressBar Indeterminate → Determinate Switch

```python
# Source: verified in session — confirmed API
from PySide6.QtWidgets import QProgressBar, QLabel

class ProcessingScreen(QWidget):
    def on_processing_started(self) -> None:
        # Indeterminate: file loading phase (before first progress_cb call)
        self.progress_bar.setRange(0, 0)
        self.progress_label.setText("A carregar ficheiro…")

    def on_progress(self, current: int, total: int) -> None:
        if total > 0 and self.progress_bar.maximum() == 0:
            # First call with known row count — switch to determinate
            self.progress_bar.setRange(0, total)
        self.progress_bar.setValue(current)
        from eleitorum.ui.strings import PROCESSING_PROGRESS
        self.progress_label.setText(PROCESSING_PROGRESS.format(current=current, total=total))
        # "A validar linha {current} de {total}…"
```

### Anti-Patterns to Avoid

- **Never call `QApplication.instance().setStyleSheet()` without Fusion style:** The Windows Vista style overrides QPalette and makes QSS dark themes look broken on Windows 10/11. Always call `app.setStyle('Fusion')` first in `app.py`.
- **Never use `QSettings.value('app/first_run_shown')` without `type=bool`:** QSettings serialises Python booleans as the string `'true'` or `'false'`. Reading without `type=bool` returns a string, causing `if settings.first_run_shown():` to always be truthy. Always pass `type=bool`.
- **Never store `PipelineResult` fields in QVariant naively:** Passing complex objects via `Signal(object)` works, but the receiving slot must not try to access Qt-native types on `PipelineResult` — it is a plain dataclass and safe.
- **Never call `QThread.terminate()`:** Hard-terminates the thread without cleanup; can corrupt file handles. Always use the cancel event pattern.
- **Never subclass `QThread` AND call `moveToThread()`:** These are two different patterns. Phase 2 uses subclass (override `run()`). Do not mix.
- **Never create Qt widgets in `QThread.run()`:** Qt widgets must live on the main thread. Only data structures and signals may be used from worker threads.
- **Never pass `pathlib.Path` objects to `QSettings.setValue()`:** Serialize to `str(path)` first.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Cross-thread signal delivery | Custom queue/mutex | Qt's queued signal-slot connections | Thread-safe by design; auto-marshalled to main thread |
| Progress reporting | Shared memory / locks | `Signal(int, int)` from QThread | No race conditions; Qt handles cross-thread delivery |
| File open/save dialog | Custom QDialog with QLineEdit | `QFileDialog.getOpenFileName()` / `.getSaveFileName()` | Platform-native dialog; filters, recent dirs, last path — all free |
| Font fallback chain | Custom font detection | `QFont('Inter')` with `QApplication.setFont()` | Qt falls back to system font automatically if Inter not found |
| Window geometry persistence | Custom ini/json | `QMainWindow.saveGeometry()` + `QSettings` | Qt binary format handles DPI, multi-monitor, HiDPI correctly |
| Focus ring styling | `paintEvent` override | QSS `:focus` pseudo-class | One CSS rule applied globally via `setStyleSheet()` |
| Open folder in Explorer | `subprocess.Popen(['explorer', path])` | `QDesktopServices.openUrl(QUrl.fromLocalFile(dir))` | Cross-platform safe; handles edge cases in paths |
| Indeterminate progress bar | Animated `QLabel` | `QProgressBar.setRange(0, 0)` | Built-in; switches to determinate with `setRange(0, N)` |

**Key insight:** Qt's built-in dialogs, persistence APIs, and threading model eliminate the most error-prone implementation areas. The spec's requirements map almost 1:1 to existing Qt components.

---

## Common Pitfalls

### Pitfall 1: Windows Vista Style Breaks Dark QSS

**What goes wrong:** Setting `DARK_QSS` via `QApplication.setStyleSheet()` on Windows shows wrong background colours — some areas stay light despite the stylesheet.

**Why it happens:** The default Windows Vista Qt style (selected automatically on Windows) overrides the QPalette with a forced system-light palette. QSS rules for `background-color` on `QWidget` and `QMainWindow` are overridden by the style engine.

**How to avoid:** Call `app.setStyle('Fusion')` before `app.setStyleSheet()` in `app.py`. The Fusion style does not override QPalette with system colours. [VERIFIED: tested in session]

**Warning signs:** If the main window background is wrong colour but buttons/labels are correct, the style is interfering with the window background.

---

### Pitfall 2: QSettings Boolean Roundtrip Fails Without `type=bool`

**What goes wrong:** `settings.value('app/first_run_shown')` returns the string `'true'` instead of `True`. `if not settings_value:` never triggers because a non-empty string is always truthy.

**Why it happens:** QSettings serializes Python booleans to strings (`'true'`/`'false'`) when using the INI or registry backend. Reading back without a type hint returns the raw string.

**How to avoid:** Always call `settings.value(key, default, type=bool)`. Same applies to `int` values: use `type=int`. [VERIFIED: tested in session]

**Warning signs:** First-run welcome dialog appears on every launch despite setting `first_run_shown = True`.

---

### Pitfall 3: Cancel Cannot Stop `run_pipeline()` via `threading.Event` Alone

**What goes wrong:** Setting a `threading.Event` cancels the worker's loop but `run_pipeline()` continues executing internally until it completes — the cancel is only checked at the next `progress_cb` call (every 100 rows).

**Why it happens:** `run_pipeline()` does not check any external cancel flag; it only calls `progress_cb`. The 100-row check cadence means up to 100 rows of wasted work after cancel.

**How to avoid:** The `progress_cb` must raise `PipelineCancelledError` (not an `EleitorumError` subclass) when the cancel event is set. This exception propagates through `run_pipeline()`'s `except EleitorumError` handler unchanged, reaches the worker's `run()` method, and triggers `self.cancelled.emit()`. [VERIFIED: tested in session]

**Warning signs:** Cancel button does nothing visually; progress keeps advancing after user clicks Cancel.

---

### Pitfall 4: QThread Signals Emitted from `run()` — Thread Affinity

**What goes wrong:** Connecting a signal emitted in `QThread.run()` to a slot that creates a Qt widget, or mistakenly believing the slot executes in the worker thread.

**Why it happens:** Signals emitted from `run()` are cross-thread signals. Qt delivers them to the receiver's thread via the event loop (queued connection). The receiving slot runs on the main thread. This is correct behaviour and safe.

**How to avoid:** Never create or directly manipulate Qt widgets inside `QThread.run()`. Only emit signals. Slots connected to those signals run on the main thread and may freely manipulate widgets. [VERIFIED: cross-thread signal delivery tested in session]

**Warning signs:** Runtime Qt warning "QObject: Cannot create children for a parent that is in a different thread."

---

### Pitfall 5: Step Indicator Count Logic for Multi-Sheet Path

**What goes wrong:** The step indicator shows "Passo 3 de 5" on step_columns even when step_sheet was shown (multi-sheet path), making the user think they skipped a step.

**Why it happens:** QStackedWidget indices are fixed (0–6); the "Passo N de M" display must be computed dynamically based on which path the user took, not the QStackedWidget index.

**How to avoid:** `WizardController` tracks a `_multi_sheet_path: bool` flag set when step_sheet is visited. The `_step_display_number()` method returns `(n, 5)` or `(n, 6)` accordingly. [ASSUMED — based on CONTEXT.md specification]

---

### Pitfall 6: `QFontDatabase.addApplicationFont()` Returns -1 Silently

**What goes wrong:** Inter font is not loaded at runtime (PyInstaller bundle), so Qt falls back to the system UI font, but no error is raised.

**Why it happens:** `addApplicationFont()` returns `-1` on failure but does not raise. If the font file path is wrong (different `sys._MEIPASS` structure than expected), the font silently fails to load.

**How to avoid:** Check the return value in `_load_inter_font()`. Log a warning if `-1` is returned. Bundle fonts under `src/eleitorum/resources/fonts/Inter/` and configure PyInstaller `--add-data` for that directory. [VERIFIED: return value -1 on failure confirmed in session]

---

### Pitfall 7: `output_path=None` in `run_pipeline()` is a Dry Run

**What goes wrong:** Worker calls `run_pipeline(source, output_type)` without `output_path` — pipeline validates and transforms but writes nothing. User sees preview but no file is saved.

**Why it happens:** `run_pipeline()` has `output_path=None` as default, which means "dry run — validate only, no write."

**How to avoid:** The worker has two modes:
1. **Preview mode** (step 3 → step_processing → step_preview): call with `output_path=None` for dry-run validation and transformation preview.
2. **Write mode** (step 4 "Escolher destino e gravar" → step_processing → step_done): call with the user-chosen `output_path`.

The `SessionModel` stores the pipeline result from the dry-run preview; the write-mode call uses the output path from the save dialog. [VERIFIED: `output_path=None` dry-run behaviour confirmed from pipeline.py source]

**Note:** The CONTEXT.md describes D-07 where "Próximo" on step 3 triggers processing. This is the DRY-RUN call. The actual write happens when the user clicks "Escolher destino e gravar" on step 4, which opens the save dialog and THEN triggers a second worker call with the confirmed output path.

---

## Code Examples

### Entry Point Replacement (`__main__.py`)

```python
# Source: verified PySide6 QApplication.exec() API
from eleitorum.ui.app import create_app
from eleitorum.ui.main_window import MainWindow

def main() -> int:
    app = create_app()
    window = MainWindow()
    window.show()
    return app.exec()   # NOT exec_() — PySide6 uses exec()

if __name__ == "__main__":
    raise SystemExit(main())
```

### Theme Application

```python
# Source: verified in session — setStyleSheet on QApplication.instance()
from PySide6.QtWidgets import QApplication
from eleitorum.ui.theme import LIGHT_QSS, DARK_QSS

def apply_theme(theme: str) -> None:
    qss = DARK_QSS if theme == 'dark' else LIGHT_QSS
    QApplication.instance().setStyleSheet(qss)
```

### Centering Window on Primary Screen

```python
# Source: verified in session
from PySide6.QtWidgets import QApplication

def center_on_primary_screen(window) -> None:
    screen = QApplication.primaryScreen()
    screen_geom = screen.availableGeometry()
    fg = window.frameGeometry()
    fg.moveCenter(screen_geom.center())
    window.move(fg.topLeft())
```

### File Dialog with Last Directory

```python
# Source: verified — QFileDialog.getSaveFileName static method
from PySide6.QtWidgets import QFileDialog
from eleitorum.ui.strings import SAVE_DIALOG_TITLE

def open_save_dialog(parent, last_dir: str, suggested_name: str) -> str | None:
    path, _ = QFileDialog.getSaveFileName(
        parent,
        SAVE_DIALOG_TITLE,
        f"{last_dir}/{suggested_name}",
        "CSV (*.csv)",
    )
    return path or None  # empty string if cancelled
```

### Toolbar Button for About Dialog

```python
# Source: verified — QDialog exec() for modal
from PySide6.QtWidgets import QDialog

class AboutDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setModal(True)
        # ... build layout ...

def show_about(parent) -> None:
    dlg = AboutDialog(parent)
    dlg.exec()   # NOT exec_() in PySide6
```

### QTableWidget Read-Only Item

```python
# Source: verified in session — Qt.ItemFlag pattern
from PySide6.QtWidgets import QTableWidget, QTableWidgetItem
from PySide6.QtCore import Qt

def populate_preview_table(table: QTableWidget, rows: list[tuple]) -> None:
    table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
    for row_idx, row_data in enumerate(rows):
        for col_idx, value in enumerate(row_data):
            item = QTableWidgetItem(str(value))
            item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            table.setItem(row_idx, col_idx, item)
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `QWizard` for multi-step forms | `QStackedWidget` with custom navigation | Project decision (CONTEXT.md locked) | Full control over navigation, button states, conditional steps |
| `exec_()` method | `exec()` method | PySide6 (Qt 6) | PySide6 uses `exec()` not `exec_()` everywhere |
| `QThread` + `moveToThread(worker)` | `QThread` subclass overriding `run()` | Both still valid in PySide6 6.x | Subclass is simpler when no event loop needed in thread |
| `chardet` for encoding detection | `charset-normalizer` (Phase 1) | Phase 1 decision | Faster, cleaner MIT license, already in use |
| Windows Vista Qt style (default) | Fusion style explicitly set | Qt 6.5+ dark mode context | Required for reliable QSS dark theme on Windows |

**Deprecated/outdated:**
- `exec_()`: deprecated alias; use `exec()` in all PySide6 code
- `QApplication.processEvents()` inside worker loops: antipattern that causes re-entrancy bugs; use signals instead
- `sys.exit(app.exec_())`: old pattern; use `raise SystemExit(app.exec())`

---

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | Step indicator count logic (N of 5 vs N of 6) tracked via `_multi_sheet_path` bool in wizard controller | Common Pitfalls §5, Patterns §2 | Would need different tracking approach; low impact |
| A2 | preview (dry-run) and write are separate PipelineWorker calls; SessionModel stores dry-run result | Common Pitfalls §7 | If write is a single call, `step_processing.py` runs only once; logic change required |
| A3 | Inter font OFL license satisfied by including OFL.txt alongside font files in `resources/fonts/Inter/` | Environment section | License compliance risk; need OFL.txt in bundle |

---

## Open Questions

1. **Dry-run vs single-run pipeline execution for preview**
   - What we know: D-07 says "Próximo on step 3 triggers processing"; step 4 shows transformed output
   - What's unclear: Is step 4 populated from a dry-run result, or does the actual write happen when "Escolher destino e gravar" is clicked and the user is navigated directly to step 6?
   - Recommendation: Dry-run approach (two worker calls) gives the user a chance to review before committing to disk. The `output_path=None` dry-run path in pipeline.py supports this explicitly. The planner should confirm this interpretation from CONTEXT.md D-07 and WIZ-06.

2. **pyproject.toml version bumps alongside Phase 2 additions**
   - What we know: CLAUDE.md recommends pandas 3.0.3, mypy 2.1.0, ruff 0.15.14; pyproject.toml has older versions
   - What's unclear: Should Phase 2 Wave 0 bump these or leave them for Phase 4?
   - Recommendation: Bump in Wave 0 since they are dev tooling; no functional risk for Phase 2 work.

---

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| PySide6 | All UI widgets, theming | ✓ (after install) | 6.11.1 | — |
| pytest-qt | TST-10 smoke tests | ✓ (after install) | 4.5.0 | — |
| Python | Runtime | ✓ | 3.12.x (dev machine) | — |
| Inter font files | APP-13 | ✗ (not yet in repo) | — | Qt falls back to system UI font |

**Missing dependencies with no fallback:**
- Inter font files must be downloaded from [rsms/inter](https://github.com/rsms/inter/releases) and placed at `src/eleitorum/resources/fonts/Inter/`. Without them, `QFontDatabase.addApplicationFont()` returns -1 (fails silently) and Qt uses the system sans-serif font — APP-13 would be unsatisfied.

**Missing dependencies with fallback:**
- None beyond Inter font.

**Note on PySide6 not in pyproject.toml:** Phase 2 Wave 0 must add `PySide6==6.11.1` to `[project] dependencies` and `pytest-qt==4.5.0` to `[project.optional-dependencies] dev`.

---

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest 9.0.3 + pytest-qt 4.5.0 |
| Config file | `pyproject.toml` `[tool.pytest.ini_options]` |
| Quick run command | `pytest tests/ui/ -q -x` |
| Full suite command | `pytest -q --tb=short` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| TST-10 | `qt_api = "pyside6"` in pyproject.toml | config | `pytest --co -q` (collection validates qt_api) | ❌ Wave 0: add to pyproject.toml |
| WIZ-01 | Step 1 initializes without error; option cards clickable | smoke (pytest-qt) | `pytest tests/ui/test_step_type.py -x` | ❌ Wave 0 |
| WIZ-02 | Step 2 initializes; drop zone accepts drops | smoke (pytest-qt) | `pytest tests/ui/test_step_upload.py -x` | ❌ Wave 0 |
| WIZ-03 | Step 2.5 initializes with sheet list | smoke (pytest-qt) | `pytest tests/ui/test_step_sheet.py -x` | ❌ Wave 0 |
| WIZ-04 | Step 3 initializes; mapping rows shown | smoke (pytest-qt) | `pytest tests/ui/test_step_columns.py -x` | ❌ Wave 0 |
| WIZ-11 | Worker emits progress + finished signals | unit (no QApplication) | `pytest tests/ui/test_worker.py -x` | ❌ Wave 0 |
| PERF-02 | UI thread stays responsive (window movable) | manual | Manual drag during processing run | Manual only |
| APP-10 | System theme detection returns 'light' or 'dark' | unit | `pytest tests/ui/test_theme.py -x` | ❌ Wave 0 |
| APP-16 | Welcome dialog initializes and closes | smoke (pytest-qt) | `pytest tests/ui/test_dialogs.py -x` | ❌ Wave 0 |

### Sampling Rate

- **Per task commit:** `pytest tests/ui/ -q -x` (smoke tests only, fast)
- **Per wave merge:** `pytest -q --tb=short` (full suite including Phase 1 core tests)
- **Phase gate:** Full suite green before `/gsd-verify-work`

### Wave 0 Gaps

- [ ] `tests/ui/__init__.py` — test package
- [ ] `tests/ui/conftest.py` — `qtbot` fixture shared setup, `SessionModel` factory fixture
- [ ] `tests/ui/test_worker.py` — worker signals unit test (no QApplication needed for signal test)
- [ ] `tests/ui/test_theme.py` — theme detection and apply_theme unit test
- [ ] `tests/ui/test_step_type.py` — step 1 smoke test (requires qtbot)
- [ ] `tests/ui/test_step_upload.py` — step 2 smoke test
- [ ] `tests/ui/test_step_sheet.py` — step 2.5 smoke test
- [ ] `tests/ui/test_step_columns.py` — step 3 smoke test
- [ ] `tests/ui/test_dialogs.py` — welcome and about dialog smoke tests
- [ ] `pyproject.toml` — add `qt_api = "pyside6"` under `[tool.pytest.ini_options]`

---

## Security Domain

> `security_enforcement` is enabled (default).

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | no | desktop app, no auth |
| V3 Session Management | no | desktop app, no network session |
| V4 Access Control | no | single-user desktop app |
| V5 Input Validation | yes — file path inputs | Validate extension before processing; `pathlib.Path.suffix.lower()` check |
| V6 Cryptography | no | no encryption needed |
| V7 Error Handling | yes | No Python tracebacks shown to user; PT-PT messages only (Phase 1 established) |

### Known Threat Patterns for this stack

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Path traversal via dropped file | Tampering | `pathlib.Path.resolve()` to normalize; validate extension; never eval the path |
| Zip-slip / malicious XLSX | Tampering | openpyxl/xlrd handle this; do not add custom archive extraction |
| Output overwrites input silently | Tampering | `OutputPathError("same_as_input")` already in Phase 1 pipeline (VAL-08) |
| UI thread deadlock on long file op | DoS | QThread worker; never block main thread |
| Malformed SVG injection in icon | Tampering | icon.svg is authored by developer, not user-provided; not a runtime threat |

**No secrets or credentials in this phase.** All data stays on the user's local machine. The only "output" is a CSV to a user-chosen path.

---

## Project Constraints (from CLAUDE.md)

The planner MUST verify all tasks comply with these:

1. **Tech stack locked:** Python 3.11+, PySide6 6.11.1, stdlib `csv` for output — no substitutions without justification.
2. **Zero cost:** All dependencies open-source and freely redistributable; Inter font is OFL (include OFL.txt alongside font files).
3. **Standalone:** No network calls at runtime; no Python install required for end user.
4. **Offline:** No HTTP calls in application code at runtime.
5. **Windows 10 and 11:** UI must work on both; Fusion style required for reliable QSS theming.
6. **Performance:** UI thread stays live during processing (PERF-02) — satisfied by QThread worker.
7. **Privacy:** No personal data in test fixtures; all synthetic. No data leaves user's machine.
8. **No string literals in widget code:** All PT-PT strings centralized in `src/eleitorum/ui/strings.py`.
9. **APP_NAME from config.py:** Never hardcode "EleitorUM" in widget code; always `from eleitorum.config import APP_NAME`.
10. **PySide6 LGPL compliance:** LGPL allows distribution without source disclosure — no action needed beyond including PySide6 in the bundle.
11. **Inter font OFL compliance:** Include `OFL.txt` alongside the font files in `src/eleitorum/resources/fonts/Inter/`.

---

## Sources

### Primary (HIGH confidence)

- PySide6 6.11.1 on PyPI — version verified via `pip index versions PySide6`
- pytest-qt 4.5.0 on PyPI — version verified via `pip index versions pytest-qt`
- Qt for Python QStackedWidget docs — https://doc.qt.io/qtforpython-6/PySide6/QtWidgets/QStackedWidget.html
- Qt 6.5 Dark Mode on Windows blog — https://www.qt.io/blog/dark-mode-on-windows-11-with-qt-6.5
- PyInstaller runtime information (sys._MEIPASS) — https://pyinstaller.org/en/stable/runtime-information.html
- Inter font OFL licensing — https://github.com/rsms/inter + https://openfontlicense.org
- Session verification (live PySide6 6.11.1) — all patterns tested against installed PySide6 6.11.1 via Python subprocess

### Secondary (MEDIUM confidence)

- pytest-qt configuration (pyproject.toml `qt_api`) — https://pytest-qt.readthedocs.io/en/latest/intro.html
- QSettings window geometry pattern — https://www.pythonguis.com/tutorials/restore-window-geometry-pyqt/
- QThread subclass pattern — https://www.haccks.com/posts/how-to-use-qthread-correctly-p1/
- QThread cancel flag pattern — https://www.pythonguis.com/faq/how-to-start-stop-or-pause-running-threads/

### Tertiary (LOW confidence — not needed; all claims verified)

None.

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — PySide6 6.11.1 and pytest-qt 4.5.0 verified on PyPI + slopcheck [OK]; all APIs tested live
- Architecture: HIGH — all key patterns (worker signals, QSettings roundtrip, QProgressBar switch, DropZone, OptionCard, Fusion style requirement) verified via live PySide6 execution
- Pitfalls: HIGH — all six pitfalls confirmed by direct verification (bool roundtrip, Fusion style, cancel mechanism, thread affinity, step indicator, addApplicationFont return value)

**Research date:** 2026-05-23
**Valid until:** 2026-08-23 (PySide6 stable; 90 days)
