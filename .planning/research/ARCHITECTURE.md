# Architecture Research — EleitorUM

**Researched:** 2026-05-23
**Confidence:** HIGH (all major claims verified against official Qt docs, PyInstaller docs, pandas docs, and Python stdlib docs)

---

## Wizard UI Architecture

### Recommended Pattern: QStackedWidget + Custom Navigation Bar

**Use QStackedWidget, not QWizard.**

QWizard is the obvious first choice, but it is wrong for this project. The forum discussion at qt.io and practical experience both confirm that QWizard imposes constraints that conflict with EleitorUM's requirements:

- QWizard enforces a rigid button row (Back / Next / Finish / Cancel) at the bottom of each page that is difficult to restyle or hide per-page. EleitorUM needs the Cancel button absent on the first step and the processing step to show a progress bar in place of navigation.
- QWizard raises "Page X: Already met" errors when you attempt non-linear jumps, which is needed for error recovery (jump back to file-select after a fatal parse error).
- QWizard's visual chrome — header watermark, logo area — conflicts with the UMinho QSS-based identity. Stripping it away is more work than building on a plain widget.
- QWizard's field-registration system (`registerField`, `field`) adds indirection for a simple sequential flow with only 5–6 steps.

**QStackedWidget** gives full control with no framework overhead. The pattern is:

```
MainWindow
  ├── QMenuBar (Ficheiro / Ver / Ajuda)
  ├── StepIndicator (custom widget — shows 5 numbered dots/labels)
  ├── QStackedWidget (pages 0–5)
  │     ├── Page 0: WelcomeStep (first-run) or FileSelectStep
  │     ├── Page 1: FileSelectStep
  │     ├── Page 2: SheetPickStep (conditional: hidden for CSV/TSV)
  │     ├── Page 3: ColumnMapStep
  │     ├── Page 4: ProcessingStep (progress bar, cancel)
  │     └── Page 5: PreviewStep (50-row table + summary panel)
  └── NavBar (Back / Next/Finish buttons — hidden on ProcessingStep)
```

**Navigation wiring:**
- `NavBar.next_clicked` → `MainWindow.advance_step()` → validate current page → `stacked.setCurrentIndex(n+1)`
- `NavBar.back_clicked` → `MainWindow.retreat_step()` → `stacked.setCurrentIndex(n-1)`
- Each step exposes a `is_complete() -> bool` method; `advance_step()` calls it before moving
- The step indicator widget connects to `stacked.currentChanged` signal to update dots

**Signals for cross-step data:**

Do not pass data through Qt signals between wizard steps. Instead, use a single shared `SessionModel` dataclass that the `MainWindow` owns and passes (by reference) to each step widget on construction. Steps mutate it during their interaction; downstream steps read from it on activation.

```python
@dataclass
class SessionModel:
    source_path: Path | None = None
    detected_encoding: str | None = None
    sheet_names: list[str] = field(default_factory=list)
    selected_sheet: str | None = None
    column_map: dict[str, str] = field(default_factory=dict)
    raw_df: pd.DataFrame | None = None
    pipeline_result: PipelineResult | None = None
```

This keeps step widgets independently testable (construct with a pre-populated model, call methods, assert model state) without needing a running QApplication.

**Conditional step visibility:**

For CSV/TSV inputs, SheetPickStep should still exist in the stack but be skipped programmatically (the step index list stored in `MainWindow` is a list, not just integer arithmetic). This avoids removing/re-adding widgets to the stack at runtime, which causes geometry flicker.

---

## Background Processing Pattern

### Recommended: QThread + Worker Object (moveToThread)

**Use QThread with the worker-object pattern, not QRunnable + QThreadPool.**

Rationale:

| Criterion | QThread + moveToThread | QRunnable + QThreadPool |
|-----------|------------------------|------------------------|
| Cancellation | Easy: set a flag attribute on worker; worker checks it mid-loop | Awkward: QRunnable has no built-in cancel; must use a shared flag with pool teardown |
| Progress reporting | Worker emits `progress(int)` signal; queued connection delivers to UI thread safely | Requires embedding a QObject `signals` holder class; more boilerplate |
| Single task | Optimal — one thread, dedicated lifetime | Pool overhead unnecessary for a single blocking task |
| Error propagation | Worker emits `error(str)` signal with error text | Same workaround needed |

The pythonguis.com tutorial explicitly marks QThreadPool as "favor this approach" for parallel or repeated tasks. For EleitorUM there is exactly one pipeline run per session and it must be cancellable mid-row — `QThread + moveToThread` is the right fit.

**Canonical structure:**

```python
class PipelineWorker(QObject):
    progress = Signal(int)       # 0–100 percent
    row_count = Signal(int)      # total rows discovered after read
    finished = Signal(object)    # PipelineResult on success
    error = Signal(str)          # PT-PT error message on failure

    def __init__(self, model: SessionModel) -> None:
        super().__init__()
        self._model = model
        self._cancelled = False

    @Slot()
    def run(self) -> None:
        try:
            result = run_pipeline(self._model, self._check_cancelled, self._emit_progress)
            if not self._cancelled:
                self.finished.emit(result)
        except PipelineError as exc:
            self.error.emit(str(exc))

    def cancel(self) -> None:          # called from main thread; safe: flag write
        self._cancelled = True

    def _check_cancelled(self) -> bool:
        return self._cancelled

    def _emit_progress(self, pct: int) -> None:
        self.progress.emit(pct)
```

**Wiring in ProcessingStep:**

```python
self._thread = QThread()
self._worker = PipelineWorker(model)
self._worker.moveToThread(self._thread)
self._thread.started.connect(self._worker.run)
self._worker.finished.connect(self._thread.quit)
self._worker.finished.connect(self._on_finished)
self._worker.error.connect(self._on_error)
self._worker.progress.connect(self._progress_bar.setValue)
self._thread.finished.connect(self._thread.deleteLater)
self._thread.start()
```

**Cancel button wiring:**

```python
cancel_btn.clicked.connect(self._worker.cancel)  # sets flag, worker checks it
```

Do not call `thread.quit()` from the cancel button directly — let the worker detect `_cancelled`, emit `finished` or let `run()` return, which triggers `quit()` through the connection chain.

**Never call `QApplication.processEvents()`** inside the pipeline. The tutorial explicitly warns this causes unpredictable behavior and race conditions.

**Performance note:** 150,000-row XLSX reading via openpyxl (pandas' engine) is the single slowest step. pandas `read_excel` with `dtype=object, keep_default_na=False` reads everything as raw strings, which avoids pandas' per-cell type inference overhead. Emit progress after the read (25%), then per-batch during the row transforms (25%–95%), then on write (100%).

---

## Core Pipeline Structure

### Component Boundaries

```
src/eleitorum/
  core/
    reader.py       — load_file(path, encoding, sheet) -> pd.DataFrame
    detector.py     — detect_encoding(path) -> str, detect_header(df) -> int, detect_columns(df) -> dict
    normalizer.py   — normalize_row(row, log) -> NormalizedRow | RowError
    validator.py    — validate_mecanografico(s) -> str | ValidationError
    pipeline.py     — run_pipeline(model, cancel_fn, progress_fn) -> PipelineResult
    output.py       — write_caderno(rows, path), write_elegiveis(rows, path)
    log_builder.py  — build_log(changes: list[Change]) -> str
    models.py       — SessionModel, PipelineResult, Change, NormalizedRow, RowError
  ui/
    main_window.py
    steps/
      file_select_step.py
      sheet_pick_step.py
      column_map_step.py
      processing_step.py
      preview_step.py
    widgets/
      step_indicator.py
      column_map_dialog.py
    theme.py        — load_theme(name: str) -> str (returns QSS string)
    strings.py      — all PT-PT user-facing strings
  config.py         — APP_NAME, VERSION, SETTINGS_ORG, SETTINGS_APP constants
```

**Data flow direction (strictly one-way, no cycles):**

```
reader.py
  → raw DataFrame
    → detector.py (header row, column candidates)
      → SessionModel.column_map (user confirms/edits in ColumnMapStep)
        → pipeline.py
            calls: normalizer.py (per-row transforms + logging)
            calls: validator.py (mecanográfico rules)
            calls: log_builder.py (accumulates Change objects)
          → PipelineResult { caderno_rows, elegiveis_rows, log_lines, error_lines }
            → output.py (writes both CSVs, writes log file)
            → PreviewStep (displays caderno_rows[:50])
```

**Reader abstraction — pandas unified approach (not one-reader-per-format):**

Use a single `load_file()` function backed by `pd.read_excel` / `pd.read_csv`. Engine selection follows pandas' automatic dispatch:

| Format | Engine |
|--------|--------|
| .xlsx, .xlsm | openpyxl (auto) |
| .xls | xlrd (auto) |
| .ods | odf / odfpy (auto) |
| .csv, .tsv | `pd.read_csv` (separate branch) |

Always pass `dtype=object, keep_default_na=False` so all cells arrive as Python strings or `None`. This prevents pandas from silently converting `14891` to `14891.0` (the Excel numeric float quirk), turning date cells into `Timestamp`, or converting empty cells to `NaN` that later fail `str()` calls.

For multi-sheet Excel: call `pd.read_excel(path, sheet_name=None, ...)` to get `dict[str, DataFrame]`. Extract sheet names from the keys. Display names in SheetPickStep. Then re-read the selected sheet only with the same parameters (avoids holding all sheets in memory).

**CSV/TSV encoding detection:**

```python
import chardet

def detect_encoding(path: Path, sample_bytes: int = 32_768) -> str:
    with open(path, "rb") as fh:
        raw = fh.read(sample_bytes)
    result = chardet.detect(raw)
    return result["encoding"] or "utf-8"
```

Pass the detected encoding to `pd.read_csv(path, encoding=enc, sep=None, engine="python")`. Use `sep=None` with `engine="python"` to let Python's `csv.Sniffer` detect the delimiter (semicolon, comma, tab). This is slower than specifying the delimiter explicitly, but the file is read once and the performance hit is acceptable for text files.

**Byte-exact output with stdlib csv:**

The exact pattern for the required format (UTF-8 BOM, semicolon, CRLF, no quoting):

```python
import csv

def write_csv(rows: list[list[str]], path: Path) -> None:
    with open(path, "w", encoding="utf-8-sig", newline="") as fh:
        writer = csv.writer(
            fh,
            delimiter=";",
            quoting=csv.QUOTE_NONE,
            escapechar=None,    # raises Error if a semicolon appears in data
            lineterminator="\r\n",
        )
        for row in rows:
            writer.writerow(row)
```

`encoding="utf-8-sig"` writes the UTF-8 BOM (`\xef\xbb\xbf`) automatically. `newline=""` on `open()` ensures the `lineterminator="\r\n"` from the writer is not double-converted by the OS. `QUOTE_NONE` with no `escapechar` means the writer will raise `csv.Error` if any field contains a semicolon — this is safe because the pipeline has already stripped commas and the mecanográfico validation ensures no semicolons in any field. This is the correct behavior: crash loudly rather than silently produce malformed output.

**Trailing newline:** `csv.writer` writes a `lineterminator` after every row including the last. This produces a trailing newline as required.

**`log_builder.py` — testability rule:**

`log_builder.py` must have zero imports from `src/eleitorum/ui/`. It receives `list[Change]` objects (plain dataclasses) and returns a string. Tests can call it with a handcrafted `[Change(...)]` list and assert on the returned string without ever importing Qt.

---

## PyInstaller + PySide6 Packaging

### Hook Requirements

`pyinstaller-hooks-contrib` is installed automatically as a PyInstaller dependency and provides the PySide6 hooks. The hooks handle Qt plugin collection (platform plugins, imageformats, iconengines) automatically. The only manual requirement is keeping both packages current:

```
pip install --upgrade pyinstaller pyinstaller-hooks-contrib
```

No custom hook file is needed for EleitorUM's dependencies (PySide6, pandas, openpyxl, xlrd, odfpy, chardet are all covered by `pyinstaller-hooks-contrib`).

**Exclusions to reduce binary size** (add to `excludes` in the `.spec` `Analysis` block):

```python
excludes=[
    "PySide6.QtWebEngine",
    "PySide6.QtWebEngineCore",
    "PySide6.QtWebEngineWidgets",
    "PySide6.QtNetwork",
    "PySide6.QtMultimedia",
    "PySide6.Qt3DCore",
    "PySide6.QtBluetooth",
    "PySide6.QtNfc",
    "PySide6.QtLocation",
    "PySide6.QtPositioning",
    "PySide6.QtCharts",
    "PySide6.QtDataVisualization",
    "PySide6.QtRemoteObjects",
    "PySide6.QtSensors",
    "PySide6.QtSerialPort",
    "PySide6.QtTest",
    "matplotlib",
    "scipy",
    "sklearn",
    "IPython",
    "notebook",
]
```

EleitorUM only needs QtWidgets, QtCore, QtGui, QtSvg (for SVG icon), and QtSvgWidgets. Aggressively excluding WebEngine alone saves 50–80 MB.

### Font Bundling (Inter)

Bundle font files via the `datas` list in the `.spec` file:

```python
datas=[
    ("src/eleitorum/resources/fonts/Inter*.ttf", "resources/fonts"),
    ("src/eleitorum/resources/icons/eleitorum.ico", "resources/icons"),
    ("src/eleitorum/resources/icons/eleitorum.svg", "resources/icons"),
],
```

In the application, resolve the resource path with a PyInstaller-safe helper:

```python
import sys
from pathlib import Path

def resource_path(relative: str) -> Path:
    """Works both from source and from a PyInstaller bundle."""
    base = Path(getattr(sys, "_MEIPASS", Path(__file__).parent))
    return base / relative
```

Then load the font before creating any widgets:

```python
font_path = resource_path("resources/fonts/Inter-Regular.ttf")
font_id = QFontDatabase.addApplicationFont(str(font_path))
families = QFontDatabase.applicationFontFamilies(font_id)
if families:
    app.setFont(QFont(families[0], 10))
```

Load all Inter weights (Regular, Medium, SemiBold, Bold) in the same way — each `addApplicationFont` call returns an ID; the family name from any one of them is sufficient for the `QFont` family argument because Qt merges them by weight.

### One-File vs One-Folder: Decision

**Use one-folder (`--onedir`) as the primary deliverable; offer one-file only if explicitly requested.**

Evidence:

- PyInstaller onefile must extract ~100–200 MB of compressed Qt/Python libraries to `%TEMP%\_MEIxxxxx` on every cold start. Benchmarks show 2–5 seconds extraction on modern hardware, but on locked-down corporate Windows machines with aggressive antivirus (common in university administrative environments), the first-run scan of the extracted files can push startup to 8–15 seconds — well beyond the 3-second threshold in the spec.
- One-folder startup is near-instant (DLL loading only, no extraction). The folder can be ZIP-archived for distribution (`EleitorUM-1.0.0-win64.zip` containing the folder).
- The spec requirement says: "PyInstaller single-file `.exe` (or single-folder ZIP if startup > 3s)". Given the target environment (university IT, Windows Defender), one-folder ZIP is safer.

**Build strategy:** produce one-folder by default. Benchmark onefile on a clean VM with Windows Defender enabled. If cold-start is under 3 seconds, include onefile as a convenience artifact. If not, ship only the folder ZIP.

### Windows Version File

Use `pyinstaller-versionfile` to embed Windows PE version metadata (visible in Explorer → Properties → Details):

```yaml
# version_info.yml
Version: 1.0.0.0
CompanyName: Universidade do Minho (ferramenta independente)
FileDescription: EleitorUM — Normalizador de cadernos eleitorais
InternalName: EleitorUM
LegalCopyright: MIT License
OriginalFilename: EleitorUM-1.0.0-win64.exe
ProductName: EleitorUM
Translation:
  - langID: 2070   # Portuguese (Portugal)
    charsetID: 1200
```

Generate and reference in the `.spec`:

```python
# build step before pyinstaller
# pyivf-make_version --source-format yaml --metadata-source version_info.yml --outfile file_version_info.txt

exe = EXE(
    ...,
    version="file_version_info.txt",
    ...
)
```

Include version generation as a step in the `build.py` / `Makefile` / GitHub Actions workflow before invoking PyInstaller.

---

## QSettings Usage

### Initialization

Set organization and application name once on `QApplication` before any `QSettings` instance is created:

```python
app = QApplication(sys.argv)
app.setOrganizationName("UMinho-EleitorUM")
app.setApplicationName("EleitorUM")
```

This allows constructing `QSettings()` with no arguments anywhere in the codebase, which is cleaner than passing org/app strings everywhere.

### Format and Scope

**On Windows, `QSettings()` with no format argument uses `NativeFormat` → HKEY_CURRENT_USER\Software\UMinho-EleitorUM\EleitorUM.** This is per-user by default (UserScope). This is correct — geometry and preferences are personal.

Do NOT switch to `IniFormat`. The registry is appropriate for a Windows-only tool, avoids file permission issues in restricted environments, and is what Windows users expect. `IniFormat` would write a `.ini` file to `%APPDATA%`, which is non-standard for Windows apps.

### What to Persist

| Key | Type | Default | Notes |
|-----|------|---------|-------|
| `window/geometry` | `bytes` | (center 900×650) | Use `saveGeometry()` / `restoreGeometry()` |
| `window/state` | `bytes` | — | Use `saveState()` / `restoreState()` for dockable state if any |
| `app/theme` | `str` | `"system"` | Values: `"light"`, `"dark"`, `"system"` |
| `app/last_directory` | `str` | `""` | Last directory used in file-open dialog |
| `app/first_run_done` | `bool` | `False` | Set to True after welcome screen is shown |

**Save geometry in `closeEvent`:**

```python
def closeEvent(self, event: QCloseEvent) -> None:
    settings = QSettings()
    settings.setValue("window/geometry", self.saveGeometry())
    settings.setValue("app/theme", self._current_theme)
    settings.setValue("app/last_directory", str(self._last_directory))
    settings.setValue("app/first_run_done", True)
    super().closeEvent(event)
```

**Restore geometry in `__init__` after `show()`:**

```python
settings = QSettings()
geom = settings.value("window/geometry")
if geom:
    self.restoreGeometry(geom)
else:
    self.resize(900, 650)
    self._center_on_screen()
```

Always restore after `show()`, not before, to avoid geometry being overridden by the window manager.

### What NOT to Persist

- Any file path from the input or output (privacy — the path itself reveals nothing, but the habit is correct)
- Any data content, row counts, or transformation results
- The session state mid-wizard (no resume-session feature; each launch starts fresh)
- Column mapping choices (these are file-specific; persisting them would be incorrect for a different input file)

### Theme Switching Without Restart

QSS theme switching at runtime is straightforward — call `QApplication.instance().setStyleSheet(qss_string)` at any point and Qt repaints all widgets immediately:

```python
# theme.py
def load_theme(name: str) -> str:  # name: "light" | "dark"
    path = resource_path(f"resources/themes/{name}.qss")
    return path.read_text(encoding="utf-8")

# In MainWindow._apply_theme():
def _apply_theme(self, name: str) -> None:
    qss = load_theme(name)
    QApplication.instance().setStyleSheet(qss)
    self._current_theme = name
    QSettings().setValue("app/theme", name)
```

No restart required. All existing widgets inherit the updated stylesheet immediately.

For system theme detection (the `"system"` default), use `QStyleHints.colorScheme()` (Qt 6.5+) which returns `Qt.ColorScheme.Dark` or `Qt.ColorScheme.Light`. Connect `QGuiApplication.styleHints().colorSchemeChanged` signal to `_apply_theme()` to follow system changes automatically when the user hasn't manually overridden.

---

## Suggested Build Order

Dependencies flow strictly from core outward to UI. Build in this order to keep each layer independently testable before the next is written.

**Phase 1 — Core foundation (no UI, full test coverage)**

1. `models.py` — define all dataclasses (`SessionModel`, `PipelineResult`, `Change`, `NormalizedRow`, `RowError`). No external deps.
2. `validator.py` — mecanográfico validation rules. Pure functions, exhaustive unit tests.
3. `normalizer.py` — per-row transformations (mojibake, whitespace, comma removal, parenthetical removal, float quirk). Pure functions, synthetic fixtures.
4. `log_builder.py` — builds log/error text from `list[Change]`. Pure function. No Qt imports.
5. `reader.py` — `load_file()` with pandas. Integration tests with synthetic XLSX/ODS/CSV/TSV fixtures.
6. `detector.py` — encoding detection, header-row detection, column name matching. Unit tests with DataFrame fixtures.
7. `output.py` — `write_caderno()`, `write_elegiveis()`. Assert byte-exact output in tests (open in binary mode, compare bytes).
8. `pipeline.py` — orchestrates reader → detector → normalizer → validator → output. End-to-end integration tests.

**Phase 2 — UI scaffolding**

9. `config.py`, `strings.py` — constants and strings. Trivial; no deps.
10. `theme.py` — QSS loader. Requires Qt but no application logic.
11. `main_window.py` skeleton — menu bar, empty QStackedWidget, nav bar. No step content yet.
12. `step_indicator.py` — custom widget showing step dots/numbers. Independently testable with pytest-qt.

**Phase 3 — Step widgets (in pipeline order)**

13. `file_select_step.py` — file dialog, encoding display, populates `model.source_path` + `model.detected_encoding`.
14. `sheet_pick_step.py` — sheet list widget, populates `model.selected_sheet`.
15. `column_map_step.py` + `column_map_dialog.py` — column matching UI, populates `model.column_map`.
16. `processing_step.py` — progress bar + cancel, wires `PipelineWorker`.
17. `preview_step.py` — table view of first 50 rows, summary panel, save button.

**Phase 4 — Integration + Packaging**

18. Wire all steps into `main_window.py`; end-to-end UI test with pytest-qt.
19. QSettings persistence (geometry, theme, last directory, first-run flag).
20. PyInstaller `.spec` file + `version_info.yml` + `build.py` script.
21. GitHub Actions CI (ruff, mypy, pytest, build on tag).

---

## Sources

- Qt for Python — QStackedWidget: https://doc.qt.io/qtforpython-6/PySide6/QtWidgets/QStackedWidget.html
- Qt for Python — QWizardPage: https://doc.qt.io/qtforpython-6/PySide6/QtWidgets/QWizardPage.html
- Qt for Python — QThread: https://doc.qt.io/qtforpython-6/PySide6/QtCore/QThread.html
- Qt for Python — QFontDatabase: https://doc.qt.io/qtforpython-6/PySide6/QtGui/QFontDatabase.html
- Qt for Python — QSettings: https://doc.qt.io/qtforpython-6/PySide6/QtCore/QSettings.html
- pythonguis.com — Multithreading PySide6 with QThreadPool: https://www.pythonguis.com/tutorials/multithreading-pyside6-applications-qthreadpool/
- pythonguis.com — Packaging PySide6 with PyInstaller + InstallForge: https://www.pythonguis.com/tutorials/packaging-pyside6-applications-windows-pyinstaller-installforge/
- pythonguis.com — Save and Restore Window Geometry: https://www.pythonguis.com/tutorials/restore-window-geometry-pyqt/
- pythonguis.com — QSettings Tutorial: https://www.pythonguis.com/faq/pyside6-qsettings-how-to-use-qsettings/
- Qt Forum — QWizard vs QStackedWidget: https://forum.qt.io/topic/66971/is-changing-a-qwizard-into-a-qstackedwidget-the-best-option
- PyInstaller docs — Hook Configuration: https://pyinstaller.org/en/stable/hooks-config.html
- pyinstaller-versionfile — PyPI: https://pypi.org/project/pyinstaller-versionfile/
- pandas docs — read_excel: https://pandas.pydata.org/docs/reference/api/pandas.read_excel.html
- Python stdlib — csv module: https://docs.python.org/3/library/csv.html
- Real Python — QThread: https://realpython.com/python-pyqt-qthread/
