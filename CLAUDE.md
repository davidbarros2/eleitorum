<!-- GSD:project-start source:PROJECT.md -->
## Project

**EleitorUM**

A small, focused Windows desktop utility that normalizes electoral roll and eligibility list files for Universidade do Minho. It accepts any Excel-readable file format (XLSX, XLS, ODS, CSV, TSV), validates and transforms the data according to strict rules, and produces an exact byte-format CSV output accepted by the university's electoral platform — along with a granular transformation log. Built for a non-developer staff member who currently does this by hand in Excel and Notepad.

**Core Value:** Receive an arbitrary input file, validate it, transform it into the exact format required by the electoral system, and save the result — zero manual fixing required afterward.

### Constraints

- **Tech stack:** Python 3.11+, PySide6, openpyxl, xlrd, odfpy, pandas (input normalization), stdlib `csv` (output), chardet/charset-normalizer, PyInstaller. Substitutions allowed with justification.
- **Cost:** zero — all dependencies must be open-source and freely redistributable; license compatibility verified for every dependency.
- **Standalone:** double-click `.exe` — no Python, no pip, no terminal required by the user.
- **Offline:** absolutely no network calls at runtime (or in CI tooling that executes on user machines).
- **Platform:** Windows 10 and Windows 11. Builds tested on both.
- **Performance:** 150,000 rows in < 10 seconds on a typical office laptop; UI thread stays live (background worker).
- **Privacy:** no real personal data in the repository; test fixtures are fully synthetic; no data leaves the user's machine except to their chosen output location.
<!-- GSD:project-end -->

<!-- GSD:stack-start source:research/STACK.md -->
## Technology Stack

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
## Known Issues and Gotchas
### PySide6 + PyInstaller: Missing `plugins/` folder
### PyInstaller one-file vs one-folder: startup time
### PyInstaller: antivirus false positives
### pandas 3.0: Copy-on-Write (CoW) is now default
### pandas 3.0: string dtype change
### openpyxl read-only mode: worksheet dimensions
### odfpy: very slow release cadence
### xlrd 2.x: XLS only, no XLSX
### chardet v7.0 license uncertainty
### stdlib csv: BOM and CRLF recipe
### GitHub Actions pricing change (December 2025)
### pytest-qt and PySide6 environment variable
## Versions to Pin
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
<!-- GSD:stack-end -->

<!-- GSD:conventions-start source:CONVENTIONS.md -->
## Conventions

Conventions not yet established. Will populate as patterns emerge during development.
<!-- GSD:conventions-end -->

<!-- GSD:architecture-start source:ARCHITECTURE.md -->
## Architecture

Architecture not yet mapped. Follow existing patterns found in the codebase.
<!-- GSD:architecture-end -->

<!-- GSD:skills-start source:skills/ -->
## Project Skills

No project skills found. Add skills to any of: `.claude/skills/`, `.agents/skills/`, `.cursor/skills/`, `.github/skills/`, or `.codex/skills/` with a `SKILL.md` index file.
<!-- GSD:skills-end -->

<!-- GSD:workflow-start source:GSD defaults -->
## GSD Workflow Enforcement

Before using Edit, Write, or other file-changing tools, start work through a GSD command so planning artifacts and execution context stay in sync.

Use these entry points:
- `/gsd-quick` for small fixes, doc updates, and ad-hoc tasks
- `/gsd-debug` for investigation and bug fixing
- `/gsd-execute-phase` for planned phase work

Do not make direct repo edits outside a GSD workflow unless the user explicitly asks to bypass it.
<!-- GSD:workflow-end -->



<!-- GSD:profile-start -->
## Developer Profile

> Profile not yet configured. Run `/gsd-profile-user` to generate your developer profile.
> This section is managed by `generate-claude-profile` -- do not edit manually.
<!-- GSD:profile-end -->
