# Phase 2: UI Scaffold + Wizard Steps - Pattern Map

**Mapped:** 2026-05-23
**Files analyzed:** 20 new files + 1 modified (`__main__.py`)
**Analogs found:** 21 / 21 (all files have at least a role-match analog in Phase 1)

---

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|-----------|----------------|---------------|
| `src/eleitorum/__main__.py` | entry-point | request-response | `src/eleitorum/__main__.py` (stub) | exact |
| `src/eleitorum/ui/__init__.py` | config | — | `src/eleitorum/core/__init__.py` | role-match |
| `src/eleitorum/ui/app.py` | provider | request-response | `src/eleitorum/config.py` + `__main__.py` | role-match |
| `src/eleitorum/ui/main_window.py` | provider | event-driven | `src/eleitorum/core/pipeline.py` (orchestrator) | role-match |
| `src/eleitorum/ui/wizard.py` | controller | event-driven | `src/eleitorum/core/pipeline.py` (orchestrator) | role-match |
| `src/eleitorum/ui/session.py` | model | — | `src/eleitorum/core/pipeline.py` (`PipelineSource`, `PipelineResult`) | exact (dataclass) |
| `src/eleitorum/ui/theme.py` | config | — | `src/eleitorum/config.py` | role-match |
| `src/eleitorum/ui/strings.py` | config | — | `src/eleitorum/core/errors.py` (PT-PT strings) | exact (PT-PT pattern) |
| `src/eleitorum/ui/worker.py` | service | event-driven | `src/eleitorum/core/pipeline.py` (`run_pipeline`) | role-match |
| `src/eleitorum/ui/steps/step_type.py` | component | event-driven | `src/eleitorum/core/readers.py` (class structure) | partial |
| `src/eleitorum/ui/steps/step_upload.py` | component | file-I/O | `src/eleitorum/core/readers.py` | partial |
| `src/eleitorum/ui/steps/step_sheet.py` | component | request-response | `src/eleitorum/core/readers.py` (`list_sheets`) | partial |
| `src/eleitorum/ui/steps/step_columns.py` | component | request-response | `src/eleitorum/core/detection.py` | partial |
| `src/eleitorum/ui/steps/step_processing.py` | component | event-driven | `src/eleitorum/core/pipeline.py` (progress_cb) | partial |
| `src/eleitorum/ui/steps/step_preview.py` | component | request-response | `src/eleitorum/core/pipeline.py` (`PipelineResult`) | partial |
| `src/eleitorum/ui/steps/step_done.py` | component | request-response | `src/eleitorum/core/errors.py` + `pipeline.py` | partial |
| `src/eleitorum/ui/widgets/navbar.py` | component | event-driven | `src/eleitorum/core/readers.py` (class structure) | partial |
| `src/eleitorum/ui/widgets/option_card.py` | component | event-driven | `src/eleitorum/core/readers.py` (class structure) | partial |
| `src/eleitorum/ui/widgets/drop_zone.py` | component | file-I/O | `src/eleitorum/core/readers.py` (`SUPPORTED_EXTENSIONS`) | partial |
| `src/eleitorum/resources/icon.svg` | config | — | none (new format) | no-analog |
| `src/eleitorum/resources/fonts/Inter/` | config | — | none (assets) | no-analog |
| `tests/ui/__init__.py` | config | — | `tests/__init__.py` | exact |
| `tests/ui/conftest.py` | config | — | `tests/conftest.py` | exact |
| `tests/ui/test_worker.py` | test | event-driven | `tests/unit/test_errors.py` | role-match |
| `tests/ui/test_theme.py` | test | — | `tests/unit/test_errors.py` | role-match |
| `tests/ui/test_step_type.py` | test | event-driven | `tests/unit/test_readers.py` | role-match |
| `tests/ui/test_step_upload.py` | test | file-I/O | `tests/unit/test_readers.py` | role-match |
| `tests/ui/test_step_sheet.py` | test | request-response | `tests/unit/test_readers.py` | role-match |
| `tests/ui/test_step_columns.py` | test | request-response | `tests/unit/test_readers.py` | role-match |
| `tests/ui/test_dialogs.py` | test | event-driven | `tests/unit/test_errors.py` | role-match |

---

## Pattern Assignments

### `src/eleitorum/__main__.py` (entry-point, request-response)

**Analog:** `src/eleitorum/__main__.py` (the stub to be replaced)

**Existing stub pattern** (lines 1-19) — preserve module docstring discipline and the `if __name__ == "__main__"` guard:
```python
"""Entry point for `python -m eleitorum`.

Phase 2 replaces the stub below with the QApplication launcher that wires up
the PySide6 wizard UI. Until then, this module satisfies the smoke-import
requirement and documents the expected signature.
"""


def main() -> int:
    """Launch the EleitorUM application.

    Returns:
        Exit code (0 = success).
    """
    raise NotImplementedError("Phase 2 wires the UI entry point")


if __name__ == "__main__":
    raise SystemExit(main())
```

**Replacement pattern** (from RESEARCH.md Code Examples):
```python
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

Key: `raise SystemExit(main())` pattern comes directly from the existing stub. Keep it.

---

### `src/eleitorum/ui/__init__.py` (config)

**Analog:** `src/eleitorum/core/__init__.py`

The `core/__init__.py` is blank (zero-byte). Follow the same convention — `ui/__init__.py` is an empty package marker with no imports. Do not re-export anything here.

---

### `src/eleitorum/ui/app.py` (provider, request-response)

**Analog:** `src/eleitorum/config.py` (module-level constants) + `__main__.py` (function structure)

**Imports pattern** — copy the `from __future__ import annotations` header and the `from eleitorum.config import APP_NAME` import discipline from `config.py` (lines 1-11):
```python
"""Central configuration constants for EleitorUM.

All UI labels, window titles, log file names, and About dialog references
must read from the constants in this module per Eleitorum.md Section 3.1
(BRAND-01 contract). Changing APP_NAME here is sufficient to update all
user-facing references to the application name.
"""

APP_NAME = "EleitorUM"
```

**Module docstring pattern** — every Phase 1 module opens with a triple-quoted docstring that names requirements IDs and security invariants. Follow this in `app.py`:
```python
"""QApplication factory for EleitorUM (APP-01, APP-07–13, BRAND-01).

Creates the QApplication instance, sets Fusion style, loads Inter font via
QFontDatabase, and applies the initial theme. Called once from __main__.py.

Security note: no network calls; all font paths resolve against sys._MEIPASS
(PyInstaller) or __file__ (dev). sys._MEIPASS is read-only at runtime.
"""
```

**Core pattern** — create_app() factory; `from eleitorum.config import APP_NAME` is the only external constant reference (mirrors pipeline.py using `from eleitorum.core.errors import ...`). Font loading uses `getattr(sys, '_MEIPASS', ...)` for PyInstaller/dev dual-path (RESEARCH.md Pattern 1):
```python
import sys
import pathlib
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QFont, QFontDatabase
from PySide6.QtCore import Qt
from eleitorum.config import APP_NAME
from eleitorum.version import __version__
from eleitorum.ui.theme import apply_theme, detect_system_theme
from eleitorum.ui.strings import (...)

def create_app() -> QApplication:
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setOrganizationName(APP_NAME)
    app.setApplicationVersion(__version__)
    app.setStyle('Fusion')   # REQUIRED before setStyleSheet — see anti-patterns
    _load_inter_font(app)
    theme = detect_system_theme()
    apply_theme(theme)
    return app
```

**Error handling pattern** — `_load_inter_font()` checks `addApplicationFont()` return value of `-1` and logs a warning (never raises — font failure is non-fatal). Mirrors the `try/except PermissionError` pattern in `readers.py` where errors are caught and re-wrapped rather than silently ignored:
```python
def _load_inter_font(app: QApplication) -> None:
    base = pathlib.Path(getattr(sys, '_MEIPASS', str(pathlib.Path(__file__).parent)))
    fonts_dir = base / 'resources' / 'fonts' / 'Inter'
    loaded = 0
    for ttf in fonts_dir.glob('*.ttf'):
        result = QFontDatabase.addApplicationFont(str(ttf))
        if result != -1:
            loaded += 1
    # Fallback: if no Inter loaded, Qt uses system font automatically
    font = QFont('Inter' if loaded > 0 else 'Segoe UI')
    font.setPointSize(14)
    app.setFont(font)
```

---

### `src/eleitorum/ui/main_window.py` (provider, event-driven)

**Analog:** `src/eleitorum/core/pipeline.py` (orchestrator structure)

**Imports pattern** — mirrors pipeline.py's grouped imports (stdlib, third-party, internal):
```python
from __future__ import annotations

from PySide6.QtWidgets import QMainWindow, QStackedWidget, QMenuBar, QMenu
from PySide6.QtGui import QAction, QIcon
from PySide6.QtCore import QSettings, QByteArray
from eleitorum.config import APP_NAME
from eleitorum.ui.session import SessionModel
from eleitorum.ui.theme import apply_theme
from eleitorum.ui.strings import (MENU_FILE, MENU_VIEW, MENU_HELP, ...)
```

**Core pattern** — `QMainWindow` subclass with `__init__` that mirrors pipeline.py's `_execute_pipeline` step-by-step structure; each responsibility is a discrete method:
```python
class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self._settings = QSettings()
        self._session = SessionModel()
        self._setup_window()
        self._setup_stack()
        self._setup_menu()
        self._restore_geometry()
        self._check_first_run()

    def closeEvent(self, event) -> None:
        self._settings.setValue('window/geometry', self.saveGeometry())
        self._settings.setValue('window/state', self.saveState())
        super().closeEvent(event)
```

**QSettings pattern** — copy from RESEARCH.md Pattern 5. Use `type=bool` for booleans, `type=str` for strings. Organization/app already set on `QApplication` so `QSettings()` with no args uses the correct scope:
```python
# CRITICAL: always pass type= when reading back QSettings values
self._settings.value('app/theme', 'light', type=str)
self._settings.value('app/first_run_shown', False, type=bool)
```

---

### `src/eleitorum/ui/wizard.py` (controller, event-driven)

**Analog:** `src/eleitorum/core/pipeline.py` (step orchestration logic)

**Session passing pattern** — `SessionModel` is created once in `MainWindow` and passed to each step via constructor, mirroring how `pipeline.py` passes `builder` and `src` through `_execute_pipeline`:
```python
# From pipeline.py lines 152-161:
return _execute_pipeline(
    src=src,
    output_type=output_type,
    output_path=output_path,
    progress_cb=progress_cb,
    overwrite_allowed=overwrite_allowed,
    builder=builder,
    intended_error_target=intended_error_target,
)
```
Each step widget receives `session: SessionModel` as a constructor argument; it reads and writes `session` directly (no return value, no signals for state).

**Navigation constants** — define stack indices as class-level integer constants (mirrors `SUPPORTED_EXTENSIONS` frozenset in `readers.py` lines 41-44 — module-level named constants):
```python
class WizardController:
    STEP_TYPE       = 0
    STEP_UPLOAD     = 1
    STEP_SHEET      = 2   # conditional; skipped on single-sheet files
    STEP_COLUMNS    = 3
    STEP_PROCESSING = 4   # not user-visible as a numbered step
    STEP_PREVIEW    = 5
    STEP_DONE       = 6
```

**Step indicator logic** — `_multi_sheet_path: bool` flag set when step_sheet is visited; `_step_display_number()` returns `(n, 5)` or `(n, 6)`:
```python
def _step_display_number(self) -> tuple[int, int]:
    total = 6 if self._multi_sheet_path else 5
    idx = self._stack.currentIndex()
    # STEP_PROCESSING is not a user-visible step; do not increment count for it
    user_step = {
        self.STEP_TYPE: 1,
        self.STEP_UPLOAD: 2,
        self.STEP_SHEET: 3 if self._multi_sheet_path else None,
        self.STEP_COLUMNS: 3 if not self._multi_sheet_path else 4,
        self.STEP_PREVIEW: 4 if not self._multi_sheet_path else 5,
        self.STEP_DONE: 5 if not self._multi_sheet_path else 6,
    }.get(idx)
    return (user_step or 1, total)
```

---

### `src/eleitorum/ui/session.py` (model)

**Analog:** `src/eleitorum/core/pipeline.py` — `PipelineSource` and `PipelineResult` dataclasses (lines 52-80)

**Dataclass pattern** — copy the `@dataclasses.dataclass` pattern exactly; use `from __future__ import annotations` for forward references; fields have explicit type annotations; no `frozen=True` (session is mutable by design):
```python
# From pipeline.py lines 52-64 (PipelineSource — the closest model):
@dataclasses.dataclass
class PipelineSource:
    path: pathlib.Path
    sheet_name: str | None = None
    manual_mec_col: int | None = None
    manual_name_col: int | None = None
    csv_delimiter: str | None = None
    encoding: str | None = None
```

**SessionModel pattern** — follow this exactly, with `None` defaults for all optional fields:
```python
from __future__ import annotations
import dataclasses
import pathlib
from typing import Any, Literal

@dataclasses.dataclass
class SessionModel:
    """All mutable wizard state. One instance per session, reset on Reiniciar."""
    output_type: Literal["caderno", "elegiveis"] | None = None
    source_path: pathlib.Path | None = None
    sheet_name: str | None = None
    column_map: dict[str, Any] | None = None   # populated by step_columns
    pipeline_result: Any | None = None          # PipelineResult from worker
    output_path: pathlib.Path | None = None
```

**No Qt imports** — `SessionModel` must never import from `PySide6`. Same constraint as `pipeline.py` (lines 7-8): "Qt-free contract".

---

### `src/eleitorum/ui/theme.py` (config)

**Analog:** `src/eleitorum/config.py` (module-level string constant pattern)

**Constant pattern** — `config.py` defines `APP_NAME = "EleitorUM"` as a bare module-level constant. `theme.py` follows the exact same pattern for QSS strings:
```python
# From config.py lines 1-11:
"""Central configuration constants for EleitorUM.

All UI labels, window titles, log file names, and About dialog references
must read from the constants in this module per Eleitorum.md Section 3.1
(BRAND-01 contract). Changing APP_NAME here is sufficient to update all
user-facing references to the application name.
"""

APP_NAME = "EleitorUM"
```

**theme.py structure** — two QSS string constants + two functions:
```python
"""QSS theme constants for EleitorUM (APP-07, APP-08, APP-09, APP-10, APP-11).

LIGHT_QSS and DARK_QSS are the only two theming artifacts; switching themes
calls apply_theme() which sets the stylesheet on QApplication.instance().
Fusion style MUST be set before apply_theme() is called — see app.py.
"""
from __future__ import annotations
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt

LIGHT_QSS: str = """
/* Light theme palette (D-06):
   Background #FAFAFA | Surface #FFFFFF | Accent #a21a1c
   Text #1A1A1A | Muted #878787 | Border #E5E5E5 */
QWidget { background-color: #FAFAFA; color: #1A1A1A; font-family: Inter, 'Segoe UI', sans-serif; }
...
"""

DARK_QSS: str = """
/* Dark theme palette (D-06):
   Background #1A1A1A | Surface #262626 | Accent #C73E40
   Text #F5F5F5 | Muted #A3A3A3 | Border #3A3A3A */
...
"""

def apply_theme(theme: str) -> None:
    qss = DARK_QSS if theme == 'dark' else LIGHT_QSS
    QApplication.instance().setStyleSheet(qss)

def detect_system_theme() -> str:
    hints = QApplication.instance().styleHints()
    cs = hints.colorScheme()
    if cs == Qt.ColorScheme.Dark:
        return 'dark'
    return 'light'
```

---

### `src/eleitorum/ui/strings.py` (config)

**Analog:** `src/eleitorum/core/errors.py` — the PT-PT string centralization pattern

**This is the most important pattern to copy.** `errors.py` centralizes all user-facing PT-PT strings in one module using module-level constants and formatted string templates. `strings.py` follows this for UI strings.

**Module docstring pattern** (from `errors.py` lines 1-10):
```python
"""Custom exception hierarchy for EleitorUM.

Every exception class here:
- Subclasses EleitorumError (which subclasses Exception)
- Carries an idiomatic PT-PT message in `message_pt`
- Never includes Python stack traces or English technical terms in user-visible output

Security note (ASVS V7 / T-1-02-01): format_error_message() re-emits only
``message_pt`` and never calls traceback.format_exc() or any frame-introspection.
"""
```

**PT-PT string constant pattern** — `errors.py` uses the module-level `_ACCEPTED_EXTS_TEXT: str = ".xlsx, ..."` constant (line 22) as a reusable PT-PT fragment embedded in multiple error messages. `strings.py` follows this pattern:
```python
"""All PT-PT user-facing string constants for the EleitorUM UI (APP-20).

No string literals may appear in widget code. All user-facing copy is defined
here. Format strings use .format(key=value) syntax for parameterization.

Mirrors Phase 1's errors.py pattern: centralized, typed, PT-PT only.
"""
from __future__ import annotations

# Window / app
WINDOW_TITLE: str = "EleitorUM"   # Note: code reads from APP_NAME, not this

# Step titles
STEP_1_TITLE: str = "Tipo de ficheiro de saída"
STEP_2_TITLE: str = "Carregar ficheiro"
STEP_25_TITLE: str = "Escolher folha"
STEP_3_TITLE: str = "Mapeamento de colunas"
STEP_4_TITLE: str = "Pré-visualização"
STEP_DONE_SUCCESS_TITLE: str = "Concluído"
STEP_DONE_ERROR_TITLE: str = "Erro no processamento"
STEP_PROCESSING_TITLE: str = "A processar…"

# Step indicator
STEP_INDICATOR: str = "Passo {n} de {total}"   # format with .format(n=n, total=total)

# NavBar buttons
BTN_ANTERIOR: str = "Anterior"
BTN_PROXIMO: str = "Próximo"
BTN_CANCELAR: str = "Cancelar"
BTN_GRAVAR: str = "Escolher destino e gravar"   # overrides BTN_PROXIMO on step 4

# Processing screen
PROCESSING_LOADING: str = "A carregar ficheiro…"
PROCESSING_PROGRESS: str = "A validar linha {current} de {total}…"

# Error / warning messages (mirrors errors.py _ACCEPTED_EXTS_TEXT fragment pattern)
ERR_UNSUPPORTED_EXT: str = (
    "O formato '{ext}' não é suportado. "
    "Formatos aceites: XLSX, XLSM, XLS, ODS, CSV, TSV."
)
ERR_FILE_OPEN: str = "Não foi possível ler o ficheiro. Feche-o noutro programa e tente novamente."
ERR_OUTPUT_SAME_AS_INPUT: str = (
    "O destino não pode ser o mesmo ficheiro que o original. Escolha outro local."
)
CONFIRM_CANCEL: str = "Tem a certeza que quer cancelar? O processamento será interrompido."
...
```

---

### `src/eleitorum/ui/worker.py` (service, event-driven)

**Analog:** `src/eleitorum/core/pipeline.py` — `run_pipeline()` as the task being wrapped; `readers.py` for the try/except PermissionError pattern

**PipelineCancelledError placement** — defined in `worker.py` (not `errors.py`) because it is NOT an `EleitorumError` subclass; it must propagate through pipeline.py's `except EleitorumError` block unchanged. Mirror the `EleitorumError` docstring discipline from `errors.py` lines 52-70:
```python
class PipelineCancelledError(Exception):
    """Raised by _progress_cb to abort run_pipeline() mid-run.

    NOT a subclass of EleitorumError — must propagate through the pipeline's
    'except EleitorumError' catch block unchanged.
    Caught separately by PipelineWorker.run() which emits cancelled().
    """
```

**Signal declaration pattern** — `Signal` objects declared as class attributes (not instance attributes), matching the `@dataclasses.dataclass` field pattern in `pipeline.py`:
```python
from PySide6.QtCore import QThread, Signal

class PipelineWorker(QThread):
    progress  = Signal(int, int)   # (current_row, total_rows)
    finished  = Signal(object)     # PipelineResult on success or validation failure
    error     = Signal(str)        # PT-PT message for unexpected exceptions only
    cancelled = Signal()           # emitted when cancel flag triggered
```

**run() pattern** — mirrors pipeline.py's `run_pipeline()` try/except structure (lines 151-167): outer try catches `EleitorumError`; inner `_execute_pipeline` does the real work. Worker reverses this: inner `run_pipeline()` does the work; outer try catches `PipelineCancelledError` first, then `Exception`:
```python
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
        # Never emit Python tracebacks — emit PT-PT string only (ASVS V7)
        self.error.emit(str(exc))
```

**Cancel pattern** — `threading.Event` (not `QThread.terminate()`; see RESEARCH.md anti-patterns):
```python
import threading

def __init__(self, source, output_type, output_path, parent=None):
    super().__init__(parent)
    self._cancel_event = threading.Event()

def cancel(self) -> None:
    self._cancel_event.set()

def _progress_cb(self, current: int, total: int) -> None:
    if self._cancel_event.is_set():
        raise PipelineCancelledError("Processamento cancelado pelo utilizador.")
    self.progress.emit(current, total)
```

---

### `src/eleitorum/ui/steps/step_type.py` (component, event-driven)

**Analog:** `src/eleitorum/core/readers.py` — class structure with `__init__`, typed dataclasses, module-level constants

**Step widget pattern** — all step widgets follow this structure (use this template for ALL step files):
```python
"""Step 1 — Output type selection (WIZ-01).

Displays two OptionCard widgets; "Próximo" enabled only after selection.
"""
from __future__ import annotations

from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel
from PySide6.QtCore import Qt
from eleitorum.ui.session import SessionModel
from eleitorum.ui.strings import (STEP_1_TITLE, OPTION_CADERNO_HEADING, ...)
from eleitorum.ui.widgets.option_card import OptionCard


class StepType(QWidget):
    """Step 1: output type selection."""

    def __init__(self, session: SessionModel, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._session = session
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        # Title
        title = QLabel(STEP_1_TITLE)
        title.setObjectName("stepTitle")
        layout.addWidget(title)
        # Option cards
        cards_row = QHBoxLayout()
        self._card_caderno = OptionCard("caderno")
        self._card_elegiveis = OptionCard("elegiveis")
        self._card_caderno.selected.connect(self._on_selection)
        self._card_elegiveis.selected.connect(self._on_selection)
        cards_row.addWidget(self._card_caderno)
        cards_row.addWidget(self._card_elegiveis)
        layout.addLayout(cards_row)

    def _on_selection(self, key: str) -> None:
        self._session.output_type = key
        # Deselect the other card
        if key == "caderno":
            self._card_elegiveis.set_selected(False)
        else:
            self._card_caderno.set_selected(False)

    def is_complete(self) -> bool:
        """NavBar calls this to enable/disable Próximo."""
        return self._session.output_type is not None
```

Key: `is_complete() -> bool` on every step widget; NavBar polls this to control Próximo enable state.

---

### `src/eleitorum/ui/steps/step_upload.py` (component, file-I/O)

**Analog:** `src/eleitorum/core/readers.py` — `SUPPORTED_EXTENSIONS` constant and `read_input()` dispatch

**SUPPORTED_EXTENSIONS reuse** — import directly from `readers.py` rather than duplicating:
```python
from eleitorum.core.readers import SUPPORTED_EXTENSIONS, list_sheets
```

**File validation pattern** — mirrors `read_input()` lines 409-411 (extension check before I/O):
```python
def _validate_and_load(self, path: str) -> None:
    p = pathlib.Path(path)
    if p.suffix.lower() not in SUPPORTED_EXTENSIONS:
        self._show_error(ERR_UNSUPPORTED_EXT.format(ext=p.suffix))
        return
    self._session.source_path = p
    # Check for multiple sheets to determine if step_sheet is needed
    sheets = list_sheets(p)
    self._session._sheets = sheets  # stored for wizard routing decision
    self._update_file_label(p.name)
```

**QFileDialog pattern** (from RESEARCH.md Code Examples):
```python
from PySide6.QtWidgets import QFileDialog
from eleitorum.ui.strings import OPEN_DIALOG_TITLE, OPEN_DIALOG_FILTER

def _on_choose_file(self) -> None:
    path, _ = QFileDialog.getOpenFileName(
        self,
        OPEN_DIALOG_TITLE,
        self._last_dir,
        OPEN_DIALOG_FILTER,   # "Ficheiros suportados (*.xlsx *.xlsm *.xls *.ods *.csv *.tsv)"
    )
    if path:
        self._validate_and_load(path)
```

---

### `src/eleitorum/ui/steps/step_sheet.py` (component, request-response)

**Analog:** `src/eleitorum/core/readers.py` — `SheetInfo` dataclass (lines 52-67) and `list_sheets()` return value

**SheetInfo consumption pattern** — `list_sheets()` returns `list[SheetInfo]`; each `SheetInfo.is_empty` drives the secondary text color. Mirror how `readers.py` uses `SheetInfo` for display data:
```python
# SheetInfo from readers.py lines 52-67:
@dataclasses.dataclass(frozen=True)
class SheetInfo:
    name: str
    approximate_row_count: int  # approximate only — per RESEARCH.md Pitfall 2
    is_empty: bool

# In step_sheet.py:
def _populate_list(self, sheets: list[SheetInfo]) -> None:
    for info in sheets:
        if info.is_empty:
            label = f"{info.name} — folha vazia"
        else:
            label = f"{info.name} ({info.approximate_row_count} linhas)"
        item = QListWidgetItem(label)
        if info.is_empty:
            item.setForeground(QColor(SECONDARY_TEXT_COLOR))
        self._list.addItem(item)
```

---

### `src/eleitorum/ui/steps/step_columns.py` (component, request-response)

**Analog:** `src/eleitorum/core/pipeline.py` — column detection logic (lines 274-303) and `ColumnDetectionError` handling

**Column mapping consumption pattern** — `PipelineSource.manual_mec_col` and `manual_name_col` are set from this step's output. The detection result (from `pipeline_result.detection` dict) provides the auto-detected column names:
```python
# From pipeline.py lines 77-80 (PipelineResult.detection dict keys):
detection: dict[str, Any]
# keys: encoding, header_row_index, mec_col_index, name_col_index, detection_method

# In step_columns.py — read detection result to pre-populate:
def populate_from_session(self) -> None:
    det = self._session.pipeline_result.detection if self._session.pipeline_result else {}
    mec_col = det.get("mec_col_index")
    name_col = det.get("name_col_index")
    method = det.get("detection_method", "manual")
    # Pre-populate QLabel or QComboBox based on detected vs manual
```

**Elegíveis output_type hiding pattern** — mirrors pipeline.py lines 290-293 where `output_type == "caderno"` check gates mecanográfico processing:
```python
# From pipeline.py lines 290-293:
if output_type == "caderno" and col_mapping.mec_col_index is None:
    raise ColumnDetectionError(missing="mecanografico")

# In step_columns.py:
def _setup_ui(self) -> None:
    ...
    self._mec_row.setVisible(self._session.output_type == "caderno")
```

---

### `src/eleitorum/ui/steps/step_processing.py` (component, event-driven)

**Analog:** `src/eleitorum/core/pipeline.py` — `progress_cb` contract (lines 364-366)

**Progress callback contract** (from pipeline.py lines 364-366):
```python
# D-04 progress callback — every 100 rows and on final row
if progress_cb is not None and (i % 100 == 0 or i == total - 1):
    progress_cb(i + 1, total)
```

**QProgressBar switch pattern** (from RESEARCH.md Pattern 8):
```python
def on_processing_started(self) -> None:
    self._bar.setRange(0, 0)        # indeterminate — file loading phase
    self._label.setText(PROCESSING_LOADING)

def on_progress(self, current: int, total: int) -> None:
    if total > 0 and self._bar.maximum() == 0:
        self._bar.setRange(0, total)    # switch to determinate on first progress call
    self._bar.setValue(current)
    self._label.setText(PROCESSING_PROGRESS.format(current=current, total=total))
```

**Worker signal connection pattern** — connect in `start_processing()`, disconnect in completion handlers to avoid stale connections:
```python
def start_processing(self, worker: PipelineWorker) -> None:
    self._worker = worker
    worker.progress.connect(self.on_progress)
    worker.finished.connect(self._on_finished)
    worker.error.connect(self._on_error)
    worker.cancelled.connect(self._on_cancelled)
    self.on_processing_started()
    worker.start()
```

**Cancel flow** (D-01 from CONTEXT.md) — confirm dialog before stopping:
```python
def _on_cancel_clicked(self) -> None:
    from PySide6.QtWidgets import QMessageBox
    from eleitorum.ui.strings import CONFIRM_CANCEL, BTN_CONFIRM_CANCEL, BTN_CONTINUE
    reply = QMessageBox.question(self, "", CONFIRM_CANCEL)
    if reply == QMessageBox.StandardButton.Yes:
        self._worker.cancel()
```

---

### `src/eleitorum/ui/steps/step_preview.py` (component, request-response)

**Analog:** `src/eleitorum/core/pipeline.py` — `PipelineResult` dataclass (lines 67-80)

**PipelineResult fields consumed by this step:**
```python
# From pipeline.py lines 67-80:
@dataclasses.dataclass
class PipelineResult:
    success: bool
    output_path: pathlib.Path | None
    log_path: pathlib.Path | None
    error_log_path: pathlib.Path | None
    rows_processed: int
    transformations_applied: int
    detection: dict[str, Any]
    failures: list[FailureRow]
    log_entries: list[str]          # full log — drives "Ver detalhes" QTextEdit
```

**QTableWidget read-only pattern** (from RESEARCH.md Code Examples):
```python
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

**"Ver detalhes" toggle pattern** (D-03 from CONTEXT.md):
```python
# QTextEdit collapsed/expanded toggle:
def _on_ver_detalhes(self) -> None:
    visible = self._log_view.isVisible()
    self._log_view.setVisible(not visible)
    self._ver_detalhes_btn.setText(
        VER_DETALHES_FECHAR if not visible else VER_DETALHES_ABRIR
    )
```

**Próximo label override pattern** — NavBar receives step-specific button text; `is_complete()` always `True` on this step:
```python
def next_button_label(self) -> str:
    return BTN_GRAVAR   # "Escolher destino e gravar"

def is_complete(self) -> bool:
    return True   # always enabled on preview step
```

---

### `src/eleitorum/ui/steps/step_done.py` (component, request-response)

**Analog:** `src/eleitorum/core/errors.py` — `ValidationError` and `FailureRow` pattern (lines 155-170)

**Dual-state widget pattern** — one `QWidget` with two visual states (success / error), switched via method call. Mirrors how `ValidationError.__init__` builds either a success summary or a multi-line failure list:
```python
class StepDone(QWidget):
    def show_success(self, result: PipelineResult) -> None:
        self._stack.setCurrentIndex(0)   # success page
        self._success_path_label.setText(str(result.output_path))
        self._summary.setText(
            DONE_SUCCESS_SUMMARY.format(
                rows=result.rows_processed,
                changes=result.transformations_applied,
            )
        )

    def show_error(self, result: PipelineResult) -> None:
        self._stack.setCurrentIndex(1)   # error page
        # First 20 failures from PipelineResult.failures (mirrors ValidationError pattern)
        lines = []
        for f in result.failures[:20]:
            lines.append(f"Linha {f.row_index}: {f.column_name} = '{f.value}' — {f.message_pt}")
        if len(result.failures) > 20:
            lines.append(f"…e mais {len(result.failures) - 20} erros.")
        self._error_text.setPlainText("\n".join(lines))
```

**`QDesktopServices.openUrl()` pattern** (from RESEARCH.md "Don't Hand-Roll"):
```python
from PySide6.QtGui import QDesktopServices
from PySide6.QtCore import QUrl

def _on_open_folder(self, path: pathlib.Path) -> None:
    QDesktopServices.openUrl(QUrl.fromLocalFile(str(path.parent)))
```

---

### `src/eleitorum/ui/widgets/navbar.py` (component, event-driven)

**Analog:** `src/eleitorum/core/readers.py` — class structure with typed public API

**NavBar pattern** — reusable footer widget; wizard connects its signals to navigation methods:
```python
from __future__ import annotations
from PySide6.QtWidgets import QWidget, QHBoxLayout, QPushButton
from PySide6.QtCore import Signal
from eleitorum.ui.strings import BTN_ANTERIOR, BTN_PROXIMO, BTN_CANCELAR


class NavBar(QWidget):
    anterior_clicked = Signal()
    proximo_clicked  = Signal()
    cancelar_clicked = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)
        self._btn_cancelar = QPushButton(BTN_CANCELAR)
        self._btn_anterior = QPushButton(BTN_ANTERIOR)
        self._btn_proximo  = QPushButton(BTN_PROXIMO)
        layout.addWidget(self._btn_cancelar)
        layout.addStretch()
        layout.addWidget(self._btn_anterior)
        layout.addWidget(self._btn_proximo)
        self._btn_cancelar.clicked.connect(self.cancelar_clicked)
        self._btn_anterior.clicked.connect(self.anterior_clicked)
        self._btn_proximo.clicked.connect(self.proximo_clicked)

    def set_anterior_enabled(self, enabled: bool) -> None:
        self._btn_anterior.setEnabled(enabled)

    def set_proximo_enabled(self, enabled: bool) -> None:
        self._btn_proximo.setEnabled(enabled)

    def set_proximo_text(self, text: str) -> None:
        self._btn_proximo.setText(text)

    def set_cancel_visible(self, visible: bool) -> None:
        self._btn_cancelar.setVisible(visible)
```

---

### `src/eleitorum/ui/widgets/option_card.py` (component, event-driven)

**Analog:** `src/eleitorum/core/readers.py` — `SheetInfo` dataclass (typed, immutable view) + `_is_empty_row()` (single-responsibility helper)

**OptionCard pattern** (from RESEARCH.md Pattern 7) — `QFrame` subclass with dynamic QSS property:
```python
from PySide6.QtWidgets import QFrame, QVBoxLayout, QLabel
from PySide6.QtCore import Signal, Qt

class OptionCard(QFrame):
    selected = Signal(str)   # emits the option key ('caderno' or 'elegiveis')

    def __init__(self, key: str, parent: QFrame | None = None) -> None:
        super().__init__(parent)
        self._key = key
        self._is_selected = False
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setProperty('selected', False)
        self._setup_ui()

    def set_selected(self, value: bool) -> None:
        if self._is_selected == value:
            return
        self._is_selected = value
        self.setProperty('selected', value)
        self.style().unpolish(self)
        self.style().polish(self)   # force QSS re-evaluation of dynamic property
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

**QSS selector for dynamic property** — add to `LIGHT_QSS` / `DARK_QSS`:
```css
OptionCard {
    border: 1px solid #E5E5E5;
    border-radius: 8px;
    background-color: #FFFFFF;
    padding: 24px;
}
OptionCard[selected="true"] {
    border: 2px solid #a21a1c;
}
OptionCard:focus {
    outline: 2px solid #a21a1c;
}
```

---

### `src/eleitorum/ui/widgets/drop_zone.py` (component, file-I/O)

**Analog:** `src/eleitorum/core/readers.py` — `SUPPORTED_EXTENSIONS` (line 41), `read_input()` extension guard (lines 409-411), `FileAccessError` wrapping pattern

**DropZone pattern** (from RESEARCH.md Pattern 6) — `QFrame` subclass with drag event overrides and dynamic QSS property:
```python
from pathlib import Path
from PySide6.QtWidgets import QFrame
from PySide6.QtCore import Signal
from eleitorum.core.readers import SUPPORTED_EXTENSIONS   # reuse Phase 1 constant

class DropZone(QFrame):
    file_dropped = Signal(str)   # absolute path of dropped valid file

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setMinimumHeight(120)
        self.setProperty('drag_active', False)

    def dragEnterEvent(self, event) -> None:
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            if urls and Path(urls[0].toLocalFile()).suffix.lower() in SUPPORTED_EXTENSIONS:
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
            if Path(path).suffix.lower() in SUPPORTED_EXTENSIONS:
                event.acceptProposedAction()
                self.file_dropped.emit(path)

    def _set_active(self, value: bool) -> None:
        self.setProperty('drag_active', value)
        self.style().unpolish(self)
        self.style().polish(self)
```

**QSS hover state** (add to both LIGHT_QSS and DARK_QSS):
```css
DropZone {
    border: 1px dashed #E5E5E5;
    background-color: #FFFFFF;
    border-radius: 4px;
}
DropZone[drag_active="true"] {
    border: 2px solid #a21a1c;
}
```

---

### `tests/ui/conftest.py` (config, test infrastructure)

**Analog:** `tests/conftest.py` — the established fixture pattern (lines 1-81)

**Fixture pattern** — copy the module docstring discipline and synthetic data comment from `conftest.py` lines 1-7:
```python
"""Shared pytest-qt fixtures for the EleitorUM UI test suite (TST-10).

All synthetic data used in fixtures must include the word 'Teste', 'Exemplo',
or 'Sintetica' per Eleitorum.md Section 14.1.
"""
import pathlib
import pytest
from PySide6.QtWidgets import QApplication
from eleitorum.ui.session import SessionModel
```

**SessionModel factory fixture** — mirrors `tmp_csv_path` pattern (simple, typed, `tmp_path`-based):
```python
@pytest.fixture
def session() -> SessionModel:
    """Return a fresh SessionModel with no state (default all-None)."""
    return SessionModel()

@pytest.fixture
def session_with_file(tmp_path: pathlib.Path) -> SessionModel:
    """Return a SessionModel with source_path set to a synthetic XLSX."""
    s = SessionModel()
    s.source_path = tmp_path / "sintetico_teste.xlsx"
    return s
```

**qt_api setting** — add to `pyproject.toml` `[tool.pytest.ini_options]`, NOT to `conftest.py`:
```toml
[tool.pytest.ini_options]
qt_api = "pyside6"
```

---

### `tests/ui/test_worker.py` (test, event-driven)

**Analog:** `tests/unit/test_errors.py` — class-per-requirement structure, PT-PT assertion helpers

**Test class structure** (from `test_errors.py` lines 32-55):
```python
class TestPipelineWorker:
    """Requirement: WIZ-11 — background thread emits progress + finished signals."""

    def test_worker_emits_finished_on_success(self, qtbot, tmp_path) -> None:
        ...

    def test_worker_emits_cancelled_on_cancel(self, qtbot, tmp_path) -> None:
        ...

    def test_cancelled_error_not_eleitorumerror_subclass(self) -> None:
        from eleitorum.ui.worker import PipelineCancelledError
        from eleitorum.core.errors import EleitorumError
        assert not issubclass(PipelineCancelledError, EleitorumError)
```

**`qtbot.waitSignal` pattern** for async signal tests:
```python
def test_worker_emits_finished(self, qtbot, tmp_path) -> None:
    worker = PipelineWorker(source=..., output_type="caderno", output_path=None)
    with qtbot.waitSignal(worker.finished, timeout=5000):
        worker.start()
```

---

## Shared Patterns

### PT-PT String Centralization
**Source:** `src/eleitorum/core/errors.py` (lines 1-22, 68-73)
**Apply to:** `strings.py`, ALL step widgets, `worker.py`, `main_window.py`

The rule from `errors.py`: every user-visible string lives in a dedicated module as a typed constant. Widget code imports strings by name — no inline string literals. The module-level `_ACCEPTED_EXTS_TEXT` fragment (line 22) shows the pattern for reusable PT-PT fragments embedded in longer messages. `strings.py` follows this exactly.

```python
# errors.py line 22 — the fragment-constant pattern:
_ACCEPTED_EXTS_TEXT: str = ".xlsx, .xlsm, .xls, .ods, .csv, .tsv"
```

### `from __future__ import annotations`
**Source:** `src/eleitorum/core/errors.py` (line 13), `pipeline.py` (line 21), `readers.py` (line 25)
**Apply to:** ALL new `.py` files in `src/eleitorum/ui/`

Every Phase 1 module starts with `from __future__ import annotations`. Phase 2 must continue this.

### Module Docstring with Requirements IDs
**Source:** `src/eleitorum/core/pipeline.py` (lines 1-19), `readers.py` (lines 1-23), `errors.py` (lines 1-10)
**Apply to:** ALL new `.py` files in `src/eleitorum/ui/`

Every module opens with a triple-quoted docstring that: (a) states what the module does, (b) names the requirement IDs it satisfies, (c) includes security notes where applicable (ASVS V7, T-1-xx-xx).

### `from eleitorum.config import APP_NAME`
**Source:** `src/eleitorum/config.py` (line 11) — documented as mandatory in the file's own docstring
**Apply to:** `app.py`, `main_window.py`, any dialog that displays the app name

Never hardcode `"EleitorUM"` in widget code. Always import `APP_NAME`.

### `from eleitorum.version import __version__`
**Source:** `src/eleitorum/version.py` (line 8)
**Apply to:** `app.py` (sets `QApplication.setApplicationVersion()`), About dialog

### try/except with Domain-Specific Exception Wrapping
**Source:** `src/eleitorum/core/readers.py` (lines 132-136, 170-174)
**Apply to:** `worker.py`, `step_upload.py`, `step_done.py`

```python
# readers.py lines 132-136 — the wrapping pattern:
try:
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
except PermissionError as err:
    raise FileAccessError(path=path, mode="read") from err
except FileNotFoundError as err:
    raise FileAccessError(path=path, mode="read") from err
```

In `worker.py`: the analogous pattern is catching `PipelineCancelledError` before `Exception`. In `step_upload.py`: catching `EleitorumError` from `readers` and displaying `err.message_pt` in the inline error label.

### @dataclasses.dataclass for Plain Data Objects
**Source:** `src/eleitorum/core/pipeline.py` (lines 52-80), `readers.py` (lines 52-89), `errors.py` (lines 30-45)
**Apply to:** `session.py`

Use `@dataclasses.dataclass` (not `@dataclasses.dataclass(frozen=True)`) for mutable session state. Use `frozen=True` only for immutable value objects (like `FailureRow` and `SheetInfo`).

### QSS Dynamic Property Refresh
**Source:** RESEARCH.md Pattern 6 (DropZone), Pattern 7 (OptionCard)
**Apply to:** `option_card.py`, `drop_zone.py`, any widget with dynamic QSS state

```python
# Required after changing a dynamic QSS property — forces style re-evaluation:
self.setProperty('drag_active', value)
self.style().unpolish(self)
self.style().polish(self)
```

### `type=bool` / `type=str` for QSettings Reads
**Source:** RESEARCH.md Pattern 5 + Pitfall 2
**Apply to:** `main_window.py` everywhere `QSettings.value()` is called

```python
# CRITICAL: always pass type=
self._settings.value('app/first_run_shown', False, type=bool)
self._settings.value('app/theme', 'light', type=str)
# Pitfall: omitting type= returns a string 'true' which is always truthy
```

### Synthetic Data in Tests
**Source:** `tests/conftest.py` (lines 1-7, 17-31)
**Apply to:** `tests/ui/conftest.py`, all `tests/ui/test_*.py` files

```python
# conftest.py lines 17-31 — naming rule:
SYNTHETIC_NAMES: tuple[str, ...] = (
    "João Silva Teste",
    "Maria Costa Exemplo",
    ...
)
# Rule: all test names include "Teste", "Exemplo", or "Sintetica"
```

---

## No Analog Found

| File | Role | Data Flow | Reason |
|------|------|-----------|--------|
| `src/eleitorum/resources/icon.svg` | config | — | No SVG assets exist in Phase 1; SVG is author-created content |
| `src/eleitorum/resources/fonts/Inter/` | config | — | No bundled font assets in Phase 1; font files are binary downloads (OFL license) |

Both are pure content/asset files, not code. The planner should treat `icon.svg` as a BRAND-02 spec deliverable (white "E" on `#a21a1c` rounded square, 16% corner radius) rather than a code pattern.

---

## Metadata

**Analog search scope:** `src/eleitorum/core/`, `src/eleitorum/`, `tests/`
**Files read:** 11 source files (all Phase 1 Python modules + pyproject.toml)
**Pattern extraction date:** 2026-05-23
