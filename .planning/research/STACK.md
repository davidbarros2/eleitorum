# Stack Research — EleitorUM

**Researched:** 2026-05-23
**Overall confidence:** HIGH (all choices verified against PyPI release dates and official documentation)

---

## Recommended Stack (validated 2026)

| Library | Pin version | Rationale | Confidence |
|---------|-------------|-----------|------------|
| Python | 3.11 | Project spec requires 3.11+; pandas 3.0 requires >=3.11; sweet spot of maturity and performance | HIGH |
| PySide6 | 6.11.1 | LGPL-licensed — no source disclosure obligation for closed-source apps; same Qt6 runtime as PyQt6; officially maintained by Qt Company; supports Python 3.10–3.14 | HIGH |
| openpyxl | 3.1.5 | De-facto standard for XLSX read/write; required by pandas for `engine="openpyxl"`; latest stable as of June 2024 | HIGH |
| xlrd | 2.0.2 | Only maintained library that reads legacy `.xls` binary format; released June 2025; scoped exclusively to XLS | HIGH |
| odfpy | 1.4.1 | Required backend for `pandas.read_excel(engine="odf")`; last release 2020 but stable/no active CVEs; no real alternative for this integration path | MEDIUM |
| pandas | 3.0.3 | Handles XLSX/XLS/ODS/CSV parsing and normalization pipeline; 150k-row performance is adequate with openpyxl read-only mode; latest stable May 2026 | HIGH |
| charset-normalizer | 3.4.7 | Active replacement for chardet (MIT, April 2026); 10–100x faster on large files; default detection backend for `requests`; chardet's relicensing from LGPL to MIT in v7.0+ is legally disputed | HIGH |
| stdlib `csv` | (stdlib) | Zero-dependency, byte-exact control over delimiter, quoting, line endings; `encoding="utf-8-sig"` for BOM; `newline=""` + `lineterminator="\r\n"` for CRLF — only correct choice for this use case | HIGH |
| PyInstaller | 6.20.0 | Industry standard for Python→Windows EXE; full PySide6 hooks via `pyinstaller-hooks-contrib`; latest April 2026 | HIGH |
| ruff | 0.15.14 | Replaces flake8 + isort + black in one Rust binary; 10–100x faster than alternatives; actively developed (May 2026); single tool for lint and format | HIGH |
| mypy | 2.1.0 | Mature, plugin-aware type checker; more permissive by default than pyright (fewer false positives for pandas/Qt stubs); May 2026 | HIGH |
| pytest | 9.0.3 | Standard Python test framework; requires Python >=3.10; April 2026 | HIGH |
| pytest-qt | 4.5.0 | PySide6-aware test utilities; signal waiting, widget interaction helpers; auto-detects PySide6 | HIGH |

---

## Alternatives Considered

| Category | Recommended | Alternative | Why Alternative Lost |
|----------|-------------|-------------|----------------------|
| Qt bindings | PySide6 | PyQt6 | PyQt6 is GPL v3 — distributing a closed-source EXE requires a paid commercial license from Riverbank Computing. PySide6 LGPL allows distribution without source disclosure. Both bind the same Qt 6 runtime. |
| Encoding detection | charset-normalizer | chardet | chardet's v7.0 relicensing (LGPL→MIT) via AI-assisted rewrite is disputed: the original LGPL author contends the rewrite is derivative and the copyright claim is questionable given LLM generation. Using chardet introduces license uncertainty in a PyInstaller bundle (static linking makes LGPL compliance harder). charset-normalizer is clean MIT, 10–100x faster, actively maintained. |
| ODS reading | odfpy + `engine="odf"` | pandas-ods-reader | pandas-ods-reader is a third-party wrapper with lower adoption. `pd.read_excel(engine="odf")` is the canonical pandas path and keeps the codebase consistent with XLSX/XLS handling. |
| ODS reading | odfpy + `engine="odf"` | pyexcel-ods | pyexcel-ods is less maintained, adds a separate abstraction layer, and breaks the pandas-centric pipeline. |
| Excel XLSX reading | openpyxl | calamine / python-calamine | python-calamine (Rust-based) is significantly faster for read-only workloads but is a newer library with less proven production history; not yet a first-class pandas engine. Worth evaluating in a future iteration; for 150k rows openpyxl in read-only mode is sufficient. |
| Type checker | mypy | pyright | pyright is 3–5x faster and stricter, but its strictness produces more friction with pandas (no plugin system; relies on stubs). Mypy has the pandas-stubs ecosystem and is more forgiving during initial development. Running mypy in CI is sufficient for a single-version project. |
| Formatter | ruff | black + isort | ruff replaces both in one tool with a compatible Black-style formatter. No reason to maintain two separate tools. |
| Packaging | PyInstaller | Nuitka | Nuitka produces genuinely native executables with better startup performance, but has a steeper build configuration learning curve. PyInstaller has mature PySide6 hooks and is well-documented for this exact use case. |
| Packaging | PyInstaller | cx_Freeze | Less ecosystem support, fewer maintained hooks, smaller community. |
| Output writing | stdlib csv | pandas `to_csv` | pandas `to_csv` has historically been inconsistent about BOM, quoting, and exact line ending control. stdlib csv with explicit `newline=""`, `lineterminator="\r\n"`, `delimiter=";"`, and `quoting=csv.QUOTE_NONE` gives byte-exact control with no surprises. |

---

## Known Issues and Gotchas

### PySide6 + PyInstaller: Missing `plugins/` folder
PyInstaller's auto-detection of Qt plugins has historically left out the `platforms/` plugin folder, causing a "no Qt platform plugin could be initialized" error at runtime. Mitigation: always install and pin `pyinstaller-hooks-contrib` alongside PyInstaller; the hooks package is updated regularly for new Qt versions. Test the built EXE on a clean Windows machine (no Python installed) before shipping.

### PyInstaller one-file vs one-folder: startup time
One-file (`--onefile`) mode extracts to a temp directory (`_MEIxxxxxx`) on every launch, then cleans up on exit. For a PySide6 app with Qt DLLs (typically 80–120 MB uncompressed), this extraction adds 2–5 seconds of startup time on a cold HDD. The project spec says "single-file .exe (or single-folder ZIP if startup > 3s)." Recommendation: build one-folder first, measure startup on a representative office laptop. If under 3s, switch to one-file; otherwise ship a ZIP of the one-folder output. One-folder builds also make antivirus scanning less suspicious because the DLLs are visible files, not packed inside an opaque blob.

### PyInstaller: antivirus false positives
PyInstaller bootloaders are a known vector for antivirus heuristic flags (Windows Defender, Avast, AVG, etc.), particularly with `--onefile`. This is a systemic issue with all PyInstaller-packaged apps, not a project-specific bug. The one-folder approach is less frequently flagged. If false positives occur: rebuild from source bootloader (advanced), or sign the EXE with a code signing certificate (cost), or document the issue for the end user.

### pandas 3.0: Copy-on-Write (CoW) is now default
pandas 3.0 makes CoW mandatory — chained assignment (`df[mask]['col'] = value`) silently does nothing instead of raising. All normalization code must use `.loc` or explicit assignment. Write tests against pandas 3.0 from day one; do not assume pandas 2.x behavior.

### pandas 3.0: string dtype change
String columns now infer as `str` dtype (not `object`). Code that checks `dtype == object` will break. Use `pd.api.types.is_string_dtype()` or check for `str` dtype explicitly.

### openpyxl read-only mode: worksheet dimensions
openpyxl's read-only mode trusts the `<dimension>` tag in the XLSX file to know where data ends. Poorly formed XLSX files (produced by some non-Excel software) omit or miscalculate this tag, causing incomplete reads. When using `pd.read_excel(engine="openpyxl")`, pandas calls openpyxl in normal mode by default (not read-only). For 150k-row files this means ~50× the file size in RAM during parse (a 10 MB XLSX → ~500 MB peak RAM). This is acceptable on a typical 8–16 GB office laptop but worth documenting. If memory proves a problem, consider `openpyxl.load_workbook(read_only=True)` with a custom row iterator instead of `pd.read_excel`.

### odfpy: very slow release cadence
odfpy 1.4.1 was released in January 2020. The library is "stable" in the sense that ODS is a stable format, but it is effectively in maintenance mode. For this project it is acceptable (ODS is an uncommon edge case). If odfpy breaks on a future Python version, the fallback is to parse ODS with a manual XML approach (ODS is a ZIP of XML files).

### xlrd 2.x: XLS only, no XLSX
xlrd deliberately dropped XLSX support in version 2.0 (2020). Never pass an XLSX file to xlrd. The file routing logic must detect format by file extension and magic bytes before dispatching to the correct reader.

### chardet v7.0 license uncertainty
chardet 7.0 was relicensed from LGPL-2.1 to MIT using an AI-assisted rewrite. The original author publicly disputes this relicensing as a derivative work. For a PyInstaller-bundled application (which statically packages all dependencies), using an LGPL library correctly would require allowing users to swap in a modified version — which PyInstaller's one-file format makes impossible. charset-normalizer avoids this entire problem. Do not add chardet as a dependency.

### stdlib csv: BOM and CRLF recipe
```python
with open(output_path, "w", encoding="utf-8-sig", newline="") as fh:
    writer = csv.writer(fh, delimiter=";", quoting=csv.QUOTE_NONE, lineterminator="\r\n")
```
`encoding="utf-8-sig"` writes the BOM (0xEF 0xBB 0xBF) once at file open. `newline=""` disables Python's universal newline translation so the explicit `lineterminator="\r\n"` controls line endings exactly. `QUOTE_NONE` with no `quotechar` produces unquoted output — if any field ever contains the delimiter, this will raise; enforce that constraint upstream in validation.

### GitHub Actions pricing change (December 2025)
GitHub announced pricing changes for Actions effective 2026. Public repositories remain free and unlimited. Confirm at workflow authoring time whether `windows-latest` maps to `windows-2025` (Windows Server 2025) or `windows-2022`; pin to an explicit label (`windows-2025`) to avoid silent runner upgrades mid-project.

### pytest-qt and PySide6 environment variable
pytest-qt requires the environment variable `PYTEST_QT_API=pyside6` or the `qt_api` ini option set to `pyside6` when multiple Qt bindings are installed, otherwise it may pick PyQt5/PyQt6 first. Set in `pyproject.toml`:
```toml
[tool.pytest.ini_options]
qt_api = "pyside6"
```

---

## Versions to Pin

For `pyproject.toml` (using `>=` lower bounds with tested upper bounds, not exact pins, to allow security patches):

```toml
[project]
requires-python = ">=3.11"
dependencies = [
    "PySide6>=6.11.1,<7",
    "openpyxl>=3.1.5,<4",
    "xlrd>=2.0.2,<3",
    "odfpy>=1.4.1,<2",
    "pandas>=3.0.3,<4",
    "charset-normalizer>=3.4.7,<4",
]

[project.optional-dependencies]
dev = [
    "pyinstaller>=6.20.0,<7",
    "pyinstaller-hooks-contrib>=2025.0",   # always keep in sync with pyinstaller
    "ruff>=0.15.14",
    "mypy>=2.1.0,<3",
    "pandas-stubs>=2.2",                   # type stubs for mypy + pandas
    "pytest>=9.0.3,<10",
    "pytest-qt>=4.5.0,<5",
    "pip-audit>=2.7",                      # for CI CVE scanning
]
```

**Lock file:** generate `requirements-lock.txt` (or use `uv lock`) from the above. The PyInstaller build must use exact locked versions for reproducibility.

---

## Sources

- PySide6 vs PyQt6 licensing: https://www.pythonguis.com/faq/pyqt6-vs-pyside6/ and https://www.pythonguis.com/faq/licensing-differences-between-pyqt6-and-pyside6/
- PySide6 6.11.1 on PyPI: https://pypi.org/project/PySide6/
- openpyxl 3.1.5 on PyPI: https://pypi.org/project/openpyxl/
- openpyxl read-only mode docs: https://openpyxl.readthedocs.io/en/stable/optimized.html
- xlrd 2.0.2 on PyPI: https://pypi.org/project/xlrd/
- odfpy 1.4.1 on PyPI: https://pypi.org/project/odfpy/
- charset-normalizer 3.4.7 on PyPI: https://pypi.org/project/charset-normalizer/
- chardet vs charset-normalizer analysis: https://bytetunnels.com/posts/charset-detection-python-chardet-cchardet-charset-normalizer/
- pandas 3.0.3 on PyPI: https://pypi.org/project/pandas/
- pandas 3.0 breaking changes: https://pandas.pydata.org/docs/whatsnew/v3.0.0.html
- PyInstaller 6.20.0 on PyPI: https://pypi.org/project/PyInstaller/
- PyInstaller PySide6 deployment guide: https://doc.qt.io/qtforpython-6/deployment/deployment-pyinstaller.html
- PyInstaller packaging tutorial for PySide6: https://www.pythonguis.com/tutorials/packaging-pyside6-applications-windows-pyinstaller-installforge/
- PyInstaller antivirus false positive issue: https://www.pythonguis.com/faq/problems-with-antivirus-software-and-pyinstaller/
- ruff 0.15.14 on PyPI: https://pypi.org/project/ruff/
- ruff configuration docs: https://docs.astral.sh/ruff/configuration/
- mypy 2.1.0 on PyPI: https://pypi.org/project/mypy/
- pyright 1.1.409 on PyPI: https://pypi.org/project/pyright/
- pytest 9.0.3 on PyPI: https://pypi.org/project/pytest/
- pytest-qt 4.5.0 on PyPI: https://pypi.org/project/pytest-qt/
- GitHub Actions runner specs: https://docs.github.com/en/actions/reference/runners/github-hosted-runners
- GitHub Actions pricing (public repos free): https://resources.github.com/actions/2026-pricing-changes-for-github-actions/
