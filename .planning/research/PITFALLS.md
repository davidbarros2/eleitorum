# Pitfalls Research — EleitorUM

**Domain:** Windows desktop utility — Python + PySide6 + PyInstaller, Excel/CSV normalization, byte-exact output
**Researched:** 2026-05-23
**Overall confidence:** HIGH (all major claims verified against official documentation or authoritative community sources)

---

## PySide6 / Qt Pitfalls

### Pitfall 1: Accessing Qt Widgets Directly from a Worker Thread

**What goes wrong:** Any call that reads or writes a Qt widget property (`.setText()`, `.setEnabled()`, `.setValue()`, etc.) from a non-main thread causes either a silent crash, assertion failure, or undefined behavior. The crash is non-deterministic — it may happen immediately or only under load, making it especially hard to debug.

**Why it happens:** Qt's widget layer is not thread-safe. Only the main thread owns the event loop and is permitted to mutate widgets. The GIL does not protect you — this is a Qt constraint, not a Python constraint.

**Warning signs:**
- Worker function directly updates a `QProgressBar`, `QLabel`, or `QWizardPage` widget
- Worker function calls `self.wizard.next()` or `self.wizard.button(...).setEnabled(False)`
- Crashes only happen under certain timing conditions (race-dependent)

**Prevention strategy:** Use the `QObject` + `moveToThread` pattern. The worker is a `QObject` subclass with typed signals. It never touches widgets — it only emits signals. The main thread connects those signals to widget-updating slots via queued connections (automatic when threads differ).

```python
class ProcessingWorker(QObject):
    progress = Signal(int)         # 0–100
    row_processed = Signal(str)    # log line
    finished = Signal()
    error = Signal(str)            # PT-PT error message

    def run(self):
        for i, row in enumerate(rows):
            # ... process row ...
            self.progress.emit(int(i / total * 100))
        self.finished.emit()

# In main thread:
thread = QThread()
worker = ProcessingWorker()
worker.moveToThread(thread)
thread.started.connect(worker.run)
worker.progress.connect(self.progress_bar.setValue)
worker.finished.connect(thread.quit)
```

Never subclass `QThread` and put processing logic inside `run()` — that approach makes slot invocation from the worker thread unsafe. Use `moveToThread` instead.

**Which phase:** Phase 1 (core processing pipeline) — establish this pattern from the first background task; retrofitting it later is painful.

---

### Pitfall 2: QWizard Styling and Control Limitations

**What goes wrong:** `QWizard` with `ModernStyle` (the Windows default) renders its own title area and side panel that resist QSS styling. Dark/light theme toggling via a QSS stylesheet does not propagate into the wizard chrome (the top banner, watermark area, and button row background). You end up with a hybrid: styled page content inside an unstyled wizard frame.

Additionally, disabling the Back button on specific pages requires calling `self.wizard().button(QWizard.BackButton).setEnabled(False)` inside `initializePage()`, and re-enabling it in `cleanupPage()`. Forgetting the re-enable call on `cleanupPage` leaves the button permanently disabled for all subsequent pages.

**Why it happens:** `QWizard` paints its own non-widget chrome areas, bypassing QSS. The wizard's built-in button state management partially conflicts with manual `setEnabled` calls unless you hook the right virtual methods.

**Warning signs:**
- Light/dark toggle applies to page widgets but the wizard header stays in the wrong color
- Back button is disabled after navigating past a particular page even when it should be active

**Prevention strategy:** Either (a) use `QWizard.ClassicStyle` which is more receptive to QSS, or (b) implement the wizard as a plain `QDialog`/`QMainWindow` with a `QStackedWidget` and your own Anterior/Seguinte buttons. Option (b) gives full styling control and is the right choice given the UMinho branding requirement. Manage your own page stack and navigation state — it is 50–80 lines of code and eliminates all QWizard chrome surprises.

If you keep `QWizard`, set style explicitly:
```python
wizard.setWizardStyle(QWizard.ClassicStyle)
```
And always re-enable the Back button in `cleanupPage`:
```python
def cleanupPage(self):
    self.wizard().button(QWizard.BackButton).setEnabled(True)
```

**Which phase:** Phase 1 (UI scaffold) — choose the custom stack approach before building any pages; switching later requires rebuilding navigation logic.

---

### Pitfall 3: High-DPI Fractional Scaling on Windows

**What goes wrong:** On 125% or 150% display scaling (common on modern laptops), Qt 6 applies fractional device pixel ratios automatically. Fixed pixel sizes in layouts (`setFixedWidth(600)`, hardcoded icon sizes) become too small or create blurry rendering at non-integer ratios (1.25, 1.5, 1.75).

**Why it happens:** Qt 6 enables high-DPI support by default and cannot be turned off. The old `Qt.AA_EnableHighDpiScaling` attribute is deprecated and ignored. On Windows, the device pixel ratio is derived directly from the system display settings.

**Warning signs:**
- Application tested only at 100% scaling; UI looks wrong at 125% on the user's laptop
- Fixed-size icons appear blurry or too small
- `setFixedWidth`/`setFixedHeight` calls with hardcoded pixel values

**Prevention strategy:**
- Never hardcode pixel sizes for icons or widget dimensions — use layout size hints and `QSizePolicy` instead
- Use SVG icons or Qt's `@2x` high-DPI image convention (e.g., `icon.png` + `icon@2x.png`)
- Test at 125% and 150% display scaling during development, not just at 100%
- For the minimum window size constraint (600x500), express it in logical pixels and test that it translates correctly at all common scale factors

```python
# If you must apply rounding policy for artifacts at fractional scales:
QGuiApplication.setHighDpiScaleFactorRoundingPolicy(
    Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
)
```

**Which phase:** Phase 1 (UI scaffold) — build and test on a 125% scaled display from the start.

---

### Pitfall 4: PyInstaller Missing Qt Platform Plugin (`qwindows.dll`)

**What goes wrong:** The packaged `.exe` launches and immediately crashes with:
```
qt.qpa.plugin: Could not find the Qt platform plugin "windows" in ""
This application failed to start because no Qt platform plugin could be initialized.
```
In `--onefile` builds this is especially common because the temporary extraction path is not on the `QT_QPA_PLATFORM_PLUGIN_PATH` that Qt's loader searches.

**Why it happens:** PyInstaller's hooks for PySide6 have historically missed the `plugins/platforms/` subdirectory, or the directory structure inside the bundle does not match what Qt expects at runtime. Version-specific breakages have occurred when PySide6 was updated without a matching PyInstaller hook update.

**Warning signs:**
- Build succeeds, but the `.exe` crashes on launch on any machine that is not the build machine
- Error appears before any application window opens

**Prevention strategy:** Explicitly declare the plugins directory in the `.spec` file using `collect_data_files`:

```python
from PyInstaller.utils.hooks import collect_data_files

datas = collect_data_files('PySide6', includes=['plugins/**/*'])
```

Or use an explicit path:
```python
import PySide6
pyside6_dir = Path(PySide6.__file__).parent
datas = [(str(pyside6_dir / 'plugins'), 'PySide6/plugins')]
```

Test the packaged build on a clean Windows VM (or a machine without Python installed) as part of the build process — never assume it works because it runs on the developer's machine.

**Which phase:** Phase 4 (packaging) — but write a smoke test that runs the built `.exe` and checks for a successful window open, integrated into CI.

---

### Pitfall 5: PyInstaller Hidden Imports for PySide6 Submodules

**What goes wrong:** Certain PySide6 submodules used at runtime are not discovered by static import analysis (they are imported by Qt internally, not by your Python code). Common missing modules: `PySide6.QtSvg`, `PySide6.QtXml`, style plugins under `plugins/styles/`, and image format plugins under `plugins/imageformats/`.

**Warning signs:**
- SVG icons do not render in the packaged build (appear as broken images or blanks)
- QSS styling that references platform-specific style plugins silently fails
- Works on the development machine, fails on the clean VM

**Prevention strategy:** In the `.spec` file, declare `hiddenimports` explicitly for any PySide6 module you use at runtime, and use `collect_data_files` for plugins:

```python
hiddenimports = ['PySide6.QtSvg', 'PySide6.QtXml', 'PySide6.QtPrintSupport']
```

If using the Inter font (bundled), include it via `datas` as well. Run the packaged build against a checklist: render an SVG icon, apply dark theme, open a file dialog — before tagging a release.

**Which phase:** Phase 4 (packaging).

---

## Excel/CSV Processing Pitfalls

### Pitfall 6: openpyxl Default Mode Loads Entire XLSX into Memory

**What goes wrong:** `openpyxl.load_workbook('file.xlsx')` loads the complete workbook into RAM. A 150,000-row XLSX can consume approximately 500 MB–1 GB depending on cell types and formulas. On a typical office laptop with the file open in Excel simultaneously, this may trigger an OOM situation or cause the 10-second performance budget to be exceeded.

**Why it happens:** Default mode builds a full in-memory object graph of every cell. Memory usage is approximately 50x the raw file size according to openpyxl's own documentation.

**Warning signs:**
- Processing time grows super-linearly with file size
- Memory usage visible in Task Manager spiking during load
- Performance budget breach on the 150,000-row benchmark

**Prevention strategy:** Always open XLSX files in `read_only=True` mode for the processing pipeline:

```python
wb = openpyxl.load_workbook('file.xlsx', read_only=True, data_only=True)
ws = wb.active
try:
    for row in ws.iter_rows(values_only=True):
        # process row
finally:
    wb.close()  # required — read_only workbooks must be explicitly closed
```

Note: `read_only=True` returns `ReadOnlyCell` objects (not full `Cell`), and `ws.max_row` / `ws.max_column` may be unreliable if the creating application wrote incorrect dimension metadata (see Pitfall 7).

**Which phase:** Phase 2 (input normalization pipeline) — use read_only from the first implementation; never load full workbook in the processing path.

---

### Pitfall 7: openpyxl read_only Mode Reports Wrong Worksheet Dimensions

**What goes wrong:** In `read_only` mode, openpyxl trusts the `<dimension>` element embedded in the XLSX XML by whichever application created the file. Many applications (including some versions of LibreOffice and Excel macros) set incorrect dimension metadata — often reporting `A1:A1` or a range that omits the last N rows. Iterating `ws.iter_rows()` without explicit bounds returns fewer rows than exist in the file.

**Warning signs:**
- Row count from the wizard's preview panel does not match what the user sees in Excel
- Transformation log shows fewer processed rows than expected
- `ws.calculate_dimension()` returns `A1:A1` or a suspiciously small range

**Prevention strategy:** Do not rely on `ws.max_row` or `ws.max_column` for correctness. Always iterate all rows and stop on encountering a sentinel condition (all-None row = trailing empty row, which the spec already handles by skipping silently):

```python
for row in ws.iter_rows(values_only=True):
    if all(cell is None for cell in row):
        continue  # trailing empty row — skip per spec
    # process row
```

If you need a total row count for a progress bar, do a separate pass or use the file's XML to extract row count before streaming — or display an indeterminate progress indicator until streaming is complete.

**Which phase:** Phase 2 (input normalization) — affects progress reporting design in Phase 1 UI.

---

### Pitfall 8: xlrd 2.0+ Does Not Support XLSX

**What goes wrong:** Calling `xlrd.open_workbook('file.xlsx')` with xlrd >= 2.0.0 raises `XLRDError: Excel xlsx file; not supported`. xlrd removed XLSX support in December 2020. Any code path that routes `.xlsx` or `.xlsm` to xlrd will fail silently if the error is not caught, or crash with a confusing error if it is.

**Why it happens:** xlrd 2.0 was explicitly scoped to `.xls` only, and openpyxl was designated the XLSX handler.

**Warning signs:**
- `import xlrd; xlrd.open_workbook('test.xlsx')` — this test alone catches it
- pandas `read_excel` with `engine=None` may pick xlrd for `.xlsx` on some configurations

**Prevention strategy:** Route file extensions explicitly. Never let pandas choose the engine by inference:

```python
def open_workbook(path: Path):
    suffix = path.suffix.lower()
    if suffix in ('.xlsx', '.xlsm'):
        return openpyxl.load_workbook(path, read_only=True, data_only=True)
    elif suffix == '.xls':
        return xlrd.open_workbook(str(path))  # xlrd is correct here
    elif suffix == '.ods':
        # use odfpy or let pandas handle with engine='odf'
        ...
```

Document this routing table in `readers.py` with a comment explaining why xlrd is xls-only.

**Which phase:** Phase 2 (input normalization) — implement routing table on day one.

---

### Pitfall 9: pandas dtype Inference Converts Numeric Mecanográficos to Float

**What goes wrong:** When the mecanográfico column in an Excel file contains cells stored as numbers (not text) — e.g., `14891` stored as a numeric cell — pandas reads it as `14891.0` (float64). The spec requires handling this explicitly: `14891.0` → `"14891"`. But the failure mode is worse with prefix-less rows: if `pandas` silently reads `14891` as `14891.0` and the code calls `str()` on it, the output is `"14891.0"`, which fails mecanográfico validation downstream.

**Why it happens:** pandas infers column dtypes by scanning values. A column with mostly numeric entries defaults to float64 (not int64, because NaN requires float). This is the documented behavior.

**Warning signs:**
- `F500` (prefix + digits) → read correctly as string
- `14891` (numeric-only cell) → arrives as `14891.0`
- Validation rejects otherwise valid mecanográficos because of the trailing `.0`

**Prevention strategy:** Read the mecanográfico column as `dtype=str` (or `object`) to prevent any numeric coercion. Then apply the float-quirk handler as a normalization step before validation:

```python
def normalize_mecanografico_cell(raw: str) -> str:
    """Convert '14891.0' → '14891'; leave 'F500' untouched."""
    try:
        as_float = float(raw)
        if as_float == int(as_float):
            return str(int(as_float))
    except (ValueError, TypeError):
        pass
    return raw.strip()
```

The spec already calls out the `14891.0` → `"14891"` requirement; this pitfall is the reminder to implement it before any validation step, not after.

**Which phase:** Phase 2 (normalization pipeline).

---

### Pitfall 10: chardet Returns Wrong Encoding with High Confidence on Short Files

**What goes wrong:** chardet's confidence score is not a reliability guarantee. On a CSV file of a few hundred bytes (e.g., a short test file, or a file where the header row is the only non-ASCII content), chardet may report `encoding: 'windows-1252', confidence: 0.73` when the actual encoding is UTF-8. The confidence of 0.73 looks reasonable but is wrong. Processing with the wrong encoding produces mojibake silently — no exception is raised.

**Why it happens:** chardet uses statistical heuristics. With fewer bytes, the statistical signal is weaker. Portuguese text has moderate accented-character density, which can be ambiguous between Windows-1252 and ISO-8859-1 (they largely overlap).

**Warning signs:**
- Short test files with only ASCII header rows → chardet confident about wrong encoding
- Accented names in output contain replacement characters or Latin-1 mojibake
- Unit test with a 20-row file passes but a 3-row file produces wrong output

**Prevention strategy:**
1. If a BOM is present (`\xef\xbb\xbf` for UTF-8, `\xff\xfe` for UTF-16 LE), trust it unconditionally — do not run chardet.
2. Read the first 64 KB (or the full file if smaller) before calling chardet, not the first 4 KB.
3. Set a minimum confidence threshold (0.85 recommended) below which the UI shows a manual encoding selector instead of auto-proceeding.
4. Prefer `charset-normalizer` over `chardet` — it uses a different algorithm that is more accurate on short files with Latin-script languages.

```python
from charset_normalizer import from_bytes

def detect_encoding(raw: bytes) -> str | None:
    result = from_bytes(raw[:65536]).best()
    if result is None or result.encoding is None:
        return None  # trigger manual fallback UI
    return result.encoding
```

**Which phase:** Phase 2 (input normalization) — implement manual fallback UI in Phase 1 wizard.

---

### Pitfall 11: BOM in Input CSV — Misalignment Between pandas and stdlib csv

**What goes wrong:** pandas `read_csv` with `encoding='utf-8'` silently strips the UTF-8 BOM (`\xef\xbb\xbf`) from the first column header, so the header name appears clean. The stdlib `csv.reader` opened with `encoding='utf-8'` does NOT strip the BOM — the first field of the first row will be `'﻿column_name'` (with the BOM character prepended). If you mix the two readers across different code paths (e.g., pandas for detection, stdlib csv for streaming), the BOM handling diverges and column matching fails silently.

**Prevention strategy:** Standardize on `encoding='utf-8-sig'` for all CSV reads, in both pandas and stdlib csv. `utf-8-sig` strips the BOM if present and is a no-op if the BOM is absent:

```python
# pandas
df = pd.read_csv(path, encoding='utf-8-sig')

# stdlib csv
with open(path, encoding='utf-8-sig', newline='') as f:
    reader = csv.reader(f, delimiter=';')
```

**Which phase:** Phase 2 (input normalization).

---

## Byte-Exact Output Pitfalls

### Pitfall 12: Double CRLF from csv.writer on Windows (the `\r\r\n` bug)

**What goes wrong:** `csv.writer` uses `lineterminator='\r\n'` by default. If the output file is opened in text mode (`open('out.csv', 'w')`) on Windows, Python's text mode translates every `\n` to `\r\n`. The `\n` inside `\r\n` gets translated to `\r\n`, producing `\r\r\n` — visible as a blank line between every data row when opened in Excel or a text editor.

**Why it happens:** A documented Python/Windows interaction. Python bug tracker issue 7198. The `csv` module's documentation explicitly warns about this.

**Warning signs:**
- Output CSV has blank lines between rows when opened in Excel
- Hex dump shows `0D 0D 0A` instead of `0D 0A`
- Only manifests on Windows, not in CI running on Linux

**Prevention strategy:** Always open the output file with `newline=''` to disable Python's text mode translation. Specify `lineterminator='\r\n'` explicitly to document intent:

```python
with open(output_path, 'w', encoding='utf-8-sig', newline='') as f:
    writer = csv.writer(f, delimiter=';', lineterminator='\r\n', quoting=csv.QUOTE_NONE, escapechar='\\')
    for row in rows:
        writer.writerow(row)
```

The `encoding='utf-8-sig'` simultaneously writes the UTF-8 BOM at file open, so you do not need to write it manually.

**Which phase:** Phase 2 (output writer) — get it right in the first implementation; byte-exact testing (Pitfall 17) will catch any regression.

---

### Pitfall 13: csv.QUOTE_NONE Raises Error When Delimiter Appears in Field Data

**What goes wrong:** With `quoting=csv.QUOTE_NONE`, the csv module raises `csv.Error: need to escape, but no escapechar set` if any field contains the delimiter character (`;`) or a quotechar. For the EleitorUM output, names should not contain semicolons after normalization, but if the normalization step missed one (e.g., a rare formatting artifact), the write fails with a cryptic error rather than a meaningful PT-PT message.

**Prevention strategy:** Set `escapechar='\\'` on the writer (required by the stdlib), then add a post-normalization assertion in the name validator that rejects any name containing `;` before writing. The error should be surfaced as a validation failure (added to the error log), not as a writer exception:

```python
writer = csv.writer(f, delimiter=';', quoting=csv.QUOTE_NONE, escapechar='\\')
```

And in validation:
```python
if ';' in normalized_name:
    raise ValidationError(f"Nome contém ponto e vírgula inválido: {normalized_name!r}")
```

**Which phase:** Phase 2 (normalization + output writer).

---

### Pitfall 14: Trailing Semicolon in Caderno Rows Must Be Explicit

**What goes wrong:** The caderno eleitoral format is `mecanografico;nome;categoria` where `categoria` is always empty. A naive `writerow([mec, name])` produces `mec;name` — missing the trailing semicolon. The platform's parser expects exactly three semicolon-delimited fields. Submitting a file with two fields per row causes silent rejection or a confusing platform error.

**Warning signs:**
- Output rows have two fields instead of three
- Platform rejects the file with no useful error message
- Manual inspection of byte output shows no trailing `;`

**Prevention strategy:** Always write the empty third field explicitly:

```python
writer.writerow([mecanografico, name, ''])  # trailing empty field = trailing semicolon
```

And add a byte-level assertion in the test suite:
```python
assert b';;\r\n' not in output  # would mean two consecutive empty fields
# But:
assert all(line.count(b';') == 2 for line in output.splitlines())  # three fields = two separators
```

**Which phase:** Phase 2 (output writer) + Phase 3 (test suite).

---

### Pitfall 15: BOM Written Manually Produces Double BOM

**What goes wrong:** Writing `'﻿'` manually to the file before creating the csv.writer, AND also opening the file with `encoding='utf-8-sig'`, produces a double BOM: `EF BB BF EF BB BF`. Some tools tolerate this; the electoral platform's parser may not.

**Prevention strategy:** Use exactly one BOM mechanism. For EleitorUM, the canonical approach is `encoding='utf-8-sig'` on `open()` — the codec writes the BOM automatically when the file is first opened for writing. Do not write `'﻿'` anywhere in the application code:

```python
# Correct — BOM written once by utf-8-sig codec
with open(path, 'w', encoding='utf-8-sig', newline='') as f:
    writer = csv.writer(f, ...)

# Wrong — double BOM
with open(path, 'w', encoding='utf-8-sig', newline='') as f:
    f.write('﻿')   # DO NOT DO THIS
    writer = csv.writer(f, ...)
```

Add a test that opens the output in binary mode and asserts `output[:3] == b'\xef\xbb\xbf'` and `output[3:6] != b'\xef\xbb\xbf'`.

**Which phase:** Phase 2 (output writer) + Phase 3 (test suite).

---

## Windows-Specific Pitfalls

### Pitfall 16: Output File Locked by Excel — PermissionError with No Useful Message

**What goes wrong:** If the user has previously opened the output file in Excel, or if they double-clicked the output from the previous run, Excel holds an exclusive write lock on the file. The Python `open()` call raises `PermissionError: [Errno 13] Permission denied`. Without specific handling, the user sees a Python traceback dialog (or nothing, in a windowed PyInstaller build) instead of a clear Portuguese message telling them to close Excel.

**Why it happens:** Windows enforces mandatory file locks when Excel opens an `.xlsx` or `.csv` file in editing mode. Even "read-only" mode in Excel creates a lock file (`~$filename`) and may retain a lock. This is OS-level — there is no workaround from the writer's side.

**Warning signs:**
- `PermissionError` on `open(output_path, 'w')`
- File path ends in `.csv` and is in the same directory the user previously chose
- User reports "nothing happened" after clicking save

**Prevention strategy:** Wrap every file write operation in an explicit try/except for `PermissionError` and `OSError`, and surface a specific PT-PT message:

```python
try:
    with open(output_path, 'w', encoding='utf-8-sig', newline='') as f:
        write_output(f, rows)
except PermissionError:
    QMessageBox.critical(
        self,
        "Ficheiro em uso",
        f"Não foi possível guardar o ficheiro:\n{output_path}\n\n"
        "O ficheiro pode estar aberto no Excel ou noutro programa.\n"
        "Feche-o e tente novamente."
    )
    return  # abort — never-partial philosophy
```

Also check for `OSError` with `errno.EACCES` for edge cases where the path is on a network share or protected folder.

**Which phase:** Phase 2 (output writer) — implement error handling before any user testing.

---

### Pitfall 17: Non-ASCII Paths with os.path — Use pathlib Throughout

**What goes wrong:** Portuguese folder names like `"Ficheiros Eleitorais/Câmara"` or user profiles like `"C:\Utilizadores\Inês"` contain accented characters. Legacy `os.path` functions on Windows can mishandle these in certain edge cases, particularly when passed to subprocess calls or when the path is constructed from mixed sources. PyInstaller's temporary extraction path may also contain non-ASCII characters if the user's Windows username is accented.

**Prevention strategy:** Use `pathlib.Path` exclusively throughout the codebase. Never concatenate paths with `+` or `os.path.join`. Accept file paths from Qt file dialogs as strings, convert immediately to `Path`, and pass `Path` objects to all file I/O:

```python
from pathlib import Path

# From Qt file dialog
raw_path: str = file_dialog.selectedFiles()[0]
input_path = Path(raw_path)

# All subsequent operations
output_path = input_path.parent / f"{input_path.stem}_caderno.csv"
with open(output_path, 'w', encoding='utf-8-sig', newline='') as f:
    ...
```

For PyInstaller, use `sys._MEIPASS` (the extraction temp dir) only for bundled resources, and always wrap it in `Path`:

```python
def resource_path(relative: str) -> Path:
    base = Path(getattr(sys, '_MEIPASS', Path(__file__).parent))
    return base / relative
```

**Which phase:** Phase 1 (project scaffold) — establish the pathlib convention in the coding standards before writing any file I/O.

---

### Pitfall 18: Windows SmartScreen Blocks the Executable on First Run

**What goes wrong:** When the user downloads `EleitorUM-1.0.0-win64.exe` and double-clicks it, Windows SmartScreen shows "O Windows protegeu o seu PC" with only a "Não executar" button visible. The user must click "Mais informações" to reveal the "Executar mesmo assim" option. A non-developer user is likely to close the dialog and report that "the program doesn't open."

**Why it happens:** Unsigned executables from the internet have no reputation with Microsoft SmartScreen. PyInstaller-built executables are especially prone because the bootloader extraction pattern resembles malware behavior.

**Warning signs:**
- Any unsigned `.exe` distributed via download will trigger this on Windows 10/11 with default settings
- The issue is 100% certain to occur; it is not a "warning sign" — it will happen

**Prevention strategy and user expectation management:**
- Document the SmartScreen bypass procedure explicitly in the `README.md` with a screenshot
- Consider using a `--onedir` (folder) distribution instead of `--onefile`, which reduces SmartScreen and AV heuristic triggers
- If a code-signing certificate is available (even a self-signed OV certificate), use it — it dramatically improves SmartScreen reputation scores over time
- For an internal-use tool distributed to a known user at UMinho IT, consider providing the file via a UMinho-signed share or having IT pre-approve it in Windows Defender

There is no way to fully prevent the SmartScreen prompt for unsigned executables on Windows 10/11 without a valid code-signing certificate. The user must be prepared for this interaction.

**Which phase:** Phase 4 (packaging) — document the workaround in the build guide and README before any user testing.

---

### Pitfall 19: PyInstaller --onefile Slow Startup (Windows Defender Scan of Extraction)

**What goes wrong:** In `--onefile` mode, PyInstaller extracts all bundled files to a temporary directory on each launch. Windows Defender scans the extracted DLLs and Python files before they execute. On a typical office laptop without SSD, this can add 5–15 seconds to every startup. The spec requires startup to be acceptable; a 10-second delay before the window appears is a poor user experience for a non-developer user who may think the program is broken.

**Why it happens:** `--onefile` extracts to `%TEMP%\MEI<hash>\` on every launch (unless the hash matches a cached extraction). Windows Defender's real-time protection scans every newly extracted file.

**Warning signs:**
- Startup time measured on developer's fast machine: < 2 seconds
- Startup time measured on user's laptop with Defender real-time protection: 8–15 seconds

**Prevention strategy:** Use `--onedir` mode (single-folder ZIP) instead of `--onefile` if startup time exceeds 3 seconds on the target hardware. The spec explicitly acknowledges this trade-off: "single-file `.exe` (or single-folder ZIP if startup > 3s)." Measure startup time on a machine representative of the user's environment (spinning HDD or budget SSD, Defender enabled) before committing to `--onefile`. The `--onedir` output can be zipped for distribution and is functionally equivalent.

**Which phase:** Phase 4 (packaging) — benchmark on real hardware before finalizing the build mode.

---

## Testing Pitfalls

### Pitfall 20: pytest-qt Must Know Which Qt Binding to Use

**What goes wrong:** If both `PyQt5` and `PySide6` are installed in the same virtual environment (common when other tooling pulls in PyQt), `pytest-qt` may autodetect the wrong binding and fail with `ImportError` or silent test breakage where signals do not behave as expected.

**Warning signs:**
- Tests pass in isolation but fail in CI
- `PYTEST_QT_API` not set; multiple Qt bindings present in the environment
- `QApplication` already exists error when running multiple test modules

**Prevention strategy:** Pin the Qt API in `pytest.ini` (or `pyproject.toml`):

```ini
[pytest]
qt_api = pyside6
```

Or set it as an environment variable in CI:
```yaml
env:
  PYTEST_QT_API: pyside6
```

Also ensure the virtual environment only ever has one Qt binding installed. Add a CI step that asserts `pip list | grep -i pyqt` returns nothing.

**Which phase:** Phase 3 (test suite) — set `qt_api` in `pytest.ini` on day one of test setup.

---

### Pitfall 21: pytest-qt qtbot Fixture and QApplication Lifecycle

**What goes wrong:** If any test creates a `QApplication` manually (e.g., in a fixture or in application code loaded at import time), pytest-qt's `qtbot` fixture conflicts with it and raises `RuntimeError: QApplication already created`. Conversely, if no `QApplication` exists and a test tries to create a widget without `qtbot`, it crashes with a cryptic Qt internal assertion.

**Prevention strategy:** Never create `QApplication` in application code at module import time — only inside `if __name__ == '__main__':` or in a dedicated `main()` function. Let `qtbot` own the `QApplication` lifecycle during tests. For integration tests of the full wizard, use:

```python
def test_wizard_opens(qtbot):
    wizard = MainWizard()
    qtbot.addWidget(wizard)
    wizard.show()
    assert wizard.isVisible()
```

The `qtbot.addWidget()` call registers the widget for proper cleanup after the test — omitting it causes widgets to outlive their test scope and contaminate subsequent tests.

**Which phase:** Phase 3 (test suite).

---

### Pitfall 22: Testing Byte-Exact Output — Compare Bytes, Not Strings

**What goes wrong:** Comparing CSV output as strings (`str`) loses information about encoding and line endings. A test that asserts `output_text == expected_text` will pass even if the BOM is missing, the line endings are `\n` instead of `\r\n`, or the encoding is wrong — because Python's `str` comparison works on decoded Unicode code points, not bytes.

**Prevention strategy:** Read the output file in binary mode and compare bytes directly:

```python
def test_caderno_output_is_byte_exact(tmp_path):
    # ... run pipeline ...
    output = (tmp_path / 'output_caderno.csv').read_bytes()
    assert output[:3] == b'\xef\xbb\xbf', "Missing UTF-8 BOM"
    lines = output[3:].split(b'\r\n')
    assert lines[-1] == b'', "File must end with CRLF (trailing newline)"
    for line in lines[:-1]:
        parts = line.split(b';')
        assert len(parts) == 3, f"Expected 3 fields, got {len(parts)}: {line!r}"
```

Never use `output.decode('utf-8-sig')` and then compare strings in byte-exact tests — decode only for readability in failure messages.

**Which phase:** Phase 3 (test suite).

---

### Pitfall 23: Synthetic Fixtures Must Cover Portuguese Accented Characters Explicitly

**What goes wrong:** Generic random test data generators (Faker, testdata) produce names with ASCII-only characters by default. Tests pass because the normalization logic never encounters `ã`, `ç`, `é`, `ô`, or `ü`. Mojibake correction, whitespace normalization on multi-byte characters, and encoding detection are never exercised.

**Prevention strategy:** Create a hand-crafted fixture set in `tests/fixtures/` that includes:
- Names with all Portuguese-specific accented characters (`ã à á â ç é ê í ó ô ú`)
- Names with mojibake patterns (`MÃƒÂ£o` → `Mão`)
- Names with parenthetical annotations (`Silva (Coordenador)`)
- Names with trailing commas (`Costa,`)
- Mecanográficos with all valid prefixes, including mixed case (`f500`, `F500`, `F500`)
- A file where the mecanográfico column contains numeric cells (stored as floats in XLSX)
- A file with a BOM and one without

Do not rely on `faker` with `locale='pt_PT'` as the only source — it generates plausible names but not the pathological patterns actually observed in real data (which are documented in the spec).

**Which phase:** Phase 3 (test suite) — but the fixture design informs the normalization spec in Phase 2.

---

## Summary: Top 5 Risks to Address Early

| Rank | Risk | Why It Matters | When to Address |
|------|------|---------------|-----------------|
| 1 | **Thread safety: worker signals pattern** (Pitfall 1) | A wrong threading implementation causes non-deterministic crashes that are hard to reproduce and painful to refactor. The background processing thread is central to the UI remaining responsive on 150k-row files. | Phase 1 — before writing any background task |
| 2 | **csv.writer CRLF double-newline bug** (Pitfall 12) | The output format is byte-exact. A `\r\r\n` bug in the first implementation will require finding and fixing every file write call, plus re-running all byte-exact tests. | Phase 2 — first line of the output writer |
| 3 | **PyInstaller platform plugin not found** (Pitfall 4) | The application is worthless if the packaged `.exe` crashes before showing a window. This failure only appears on clean machines, not on the developer's machine. | Phase 4 — verified on a clean VM before any user testing |
| 4 | **openpyxl read_only for large files + dimension bug** (Pitfalls 6 & 7) | Default workbook loading may fail the 10-second performance budget on the 150k-row benchmark. The dimension bug silently truncates processing. Both must be designed in from the start. | Phase 2 — use read_only from the first XLSX reader |
| 5 | **Encoding detection failure on short/ambiguous CSV** (Pitfall 10) | A wrong encoding silently produces mojibake output. The electoral platform will reject or silently misprocess the file. The user has no way to detect this without a manual hex inspection. | Phase 2 — implement charset-normalizer + confidence threshold + manual fallback UI |
