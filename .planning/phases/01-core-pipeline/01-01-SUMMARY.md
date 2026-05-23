---
phase: 01-core-pipeline
plan: "01"
subsystem: scaffold
tags: [scaffold, config, fixtures, test-infrastructure]
dependency_graph:
  requires: []
  provides:
    - pyproject.toml with pinned dependencies and tool config
    - src/eleitorum package skeleton (version, config, core)
    - tests/ tree with 85 stub tests
    - tests/fixtures/generators.py (15 synthetic fixture functions)
  affects:
    - All Wave 1 plans (02-05) land code in src/eleitorum/core/
tech_stack:
  added:
    - openpyxl==3.1.5 (XLSX read/write)
    - xlrd==2.0.2 (legacy XLS)
    - odfpy==1.4.1 (ODS via pandas)
    - pandas==3.0.2 (input normalization)
    - charset-normalizer==3.4.7 (encoding detection)
    - pytest==9.0.3 (test framework)
    - pytest-cov==7.1.0 (coverage)
    - mypy==1.19.1 (type checking)
    - ruff==0.15.8 (lint + format)
  patterns:
    - PEP 621 pyproject.toml with setuptools.build_meta
    - src/ layout with find packages
    - Stub tests using pytest.skip() with plan reference comments
key_files:
  created:
    - pyproject.toml
    - .gitignore
    - .gitattributes
    - src/eleitorum/__init__.py
    - src/eleitorum/__main__.py
    - src/eleitorum/config.py
    - src/eleitorum/version.py
    - src/eleitorum/core/__init__.py
    - tests/__init__.py
    - tests/conftest.py
    - tests/fixtures/__init__.py
    - tests/fixtures/generators.py
    - tests/unit/__init__.py
    - tests/unit/test_errors.py
    - tests/unit/test_readers.py
    - tests/unit/test_detection.py
    - tests/unit/test_transform.py
    - tests/unit/test_validate.py
    - tests/unit/test_output.py
    - tests/unit/test_logging.py
    - tests/integration/__init__.py
    - tests/integration/test_full_pipeline.py
  modified: []
decisions:
  - "Used setuptools.build_meta (not setuptools.backends.legacy) — legacy path unavailable in Python 3.12 env with setuptools 82.0.1"
  - "ruff B007/B905 fixes: removed unused enumerate index vars, added strict=False to zip()"
metrics:
  duration: "7m 19s"
  completed: "2026-05-23"
  tasks_completed: 5
  tasks_total: 5
  files_created: 22
  files_modified: 2
---

# Phase 1 Plan 1: Scaffold Summary

**One-liner:** Project scaffold with pyproject.toml (pinned deps), eleitorum package skeleton, 85 stub tests across 8 test files, and all 15 synthetic fixture generators ready for Wave 1 consumption.

## What Was Built

### Task 1 — Root config files (commit `9de808f`)

- `pyproject.toml`: PEP 621 project metadata with exact version pins per RESEARCH.md Standard Stack. Setuptools `src/` layout. ruff (line-length=100, E/F/I/B/UP/N/SIM rules), mypy (python_version=3.11, disallow_untyped_defs for core.*), pytest (testpaths=tests, pythonpath=src, --strict-markers), coverage (fail_under=90).
- `.gitignore`: covers __pycache__, .venv, .pytest_cache, .mypy_cache, .ruff_cache, htmlcov, build, dist, *.egg-info.
- `.gitattributes`: `* text=auto eol=lf`, `*.py text eol=lf`, `*.csv text eol=crlf` (electoral platform CRLF requirement), binary rules for ods/xls/xlsx/png/ico.

### Task 2 — Package skeleton (commit `27ead19`)

- `src/eleitorum/version.py`: `__version__ = "0.1.0"` — single source of truth for build versioning.
- `src/eleitorum/config.py`: `APP_NAME = "EleitorUM"` — BRAND-01 contract; Phase 2 wizard reads this.
- `src/eleitorum/__init__.py`: re-exports `__version__` and `APP_NAME`, defines `__all__`.
- `src/eleitorum/__main__.py`: stub `main()` with `NotImplementedError`; Phase 2 replaces with QApplication launcher.
- `src/eleitorum/core/__init__.py`: empty package marker with docstring "Qt-free core processing pipeline modules."

### Task 3 — Test infrastructure (commit `050ee74`)

85 stub tests across 8 files, all using `pytest.skip("implemented in plan XX — module")`:
- `tests/conftest.py`: SYNTHETIC_NAMES (10 entries), SYNTHETIC_PREFIXES per D-08, shared fixtures (tmp_csv_path, tmp_xlsx_path, synthetic_names).
- `tests/unit/test_errors.py`: 6 stubs (VAL-01 to VAL-09 coverage)
- `tests/unit/test_readers.py`: 13 stubs (INP-01 to INP-13)
- `tests/unit/test_detection.py`: 14 stubs (DET-01 to DET-07, INP-07 to INP-09)
- `tests/unit/test_transform.py`: 17 stubs (TRF-01 to TRF-15)
- `tests/unit/test_validate.py`: 11 stubs (VAL-01 to VAL-09, D-07)
- `tests/unit/test_output.py`: 10 stubs (OUT-01 to OUT-12)
- `tests/unit/test_logging.py`: 8 stubs (LOG-01 to LOG-07)
- `tests/integration/test_full_pipeline.py`: 6 stubs (happy path, mojibake, multi-sheet, perf)

### Task 4 — Fixture generators (commit `98518e2`)

`tests/fixtures/generators.py`: all 15 functions per Eleitorum.md Section 14.3. Each function takes `path: pathlib.Path`, writes the synthetic fixture, returns the path. SYNTHETIC_NAMES and SYNTHETIC_PREFIXES defined at module level for pytest-free import.

Fixtures produced and verified:
1. `make_simple_caderno` — 582 bytes UTF-8 BOM CSV with 20 rows, mixed prefixes
2. `make_simple_elegiveis` — 278 bytes UTF-8 BOM CSV with name column only
3. `make_multi_sheet_xlsx` — 6234 bytes, sheets: Docentes (10 rows), PTAG (5 rows), Alunos (header only)
4. `make_titled_xlsx` — 5218 bytes, row 0=title, row 2=header, rows 3+=data
5. `make_headerless_xlsx` — 5092 bytes, no header, first row is data
6. `make_mojibake_csv` — 96 bytes, Latin-1 on-disk with `\xc3` byte sequences confirmed
7. `make_whitespace_chaos_xlsx` — 4986 bytes, names with TAB/NBSP/ZWSP/spaces
8. `make_with_commas` — 159 bytes, names ending in `,` before line terminator
9. `make_with_parentheses` — 197 bytes, `(Coordenador)` annotation confirmed
10. `make_duplicate_within_prefix` — 128 bytes, f6688 appears twice
11. `make_cross_prefix_collision` — 126 bytes, F500 + D500 in same file
12. `make_leading_zeros` — 159 bytes, F0500/D00123/b007
13. `make_excel_float_numbers` — 4999 bytes, float cell values (14891.0 etc.)
14. `make_mixed_case_prefixes` — 156 bytes, 3 lowercase + 2 uppercase F rows
15. `make_unicode_replacement` — 105 bytes, U+FFFD in name confirmed

### Task 5 — Iteration loop (commit `e440728`)

Dependency install: `pip install -e ".[dev]"` succeeded after fixing build backend.

Iteration loop result:
- `ruff check .` — All checks passed!
- `ruff format --check .` — 19 files already formatted
- `mypy src/eleitorum` — Success: no issues found in 5 source files
- `python -m pytest tests/ -x -q` — 85 skipped in 0.23s (exit 0)
- Smoke import: `0.1.0 EleitorUM` (exit 0)
- Qt import AST scan: no actual PySide6/PyQt imports in src/eleitorum/ or tests/

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Fixed setuptools build backend path**
- **Found during:** Task 5 — `pip install -e ".[dev]"` failed
- **Issue:** `setuptools.backends.legacy:build` path does not exist in setuptools 82.0.1 on Python 3.12
- **Fix:** Changed `build-backend` to `"setuptools.build_meta"` (the standard PEP 517 backend)
- **Files modified:** `pyproject.toml`
- **Commit:** e440728

**2. [Rule 1 - Bug] Fixed ruff lint violations in generators.py**
- **Found during:** Task 5 — ruff check
- **Issue:** B007 (unused loop variable `i` in enumerate), B905 (zip() without strict=)
- **Fix:** Removed `enumerate()` (not needed since index unused), added `strict=False` to `zip()`, applied `ruff format`
- **Files modified:** `tests/fixtures/generators.py`
- **Commit:** e440728

## Verification Evidence

```
scaffold_ready=true; tests_collected=85; coverage_target=>=90% (will fail in wave 0 — expected)
```

All 22 files created successfully. pyproject.toml is valid TOML. No Qt imports in src/ or tests/. Privacy invariant holds — all names contain Teste/Exemplo/Sintetica markers.

## Dependency Install Command Used

```
pip install -e ".[dev]"
```

Equivalent: `pip install openpyxl==3.1.5 xlrd==2.0.2 odfpy==1.4.1 pandas==3.0.2 charset-normalizer==3.4.7 pytest==9.0.3 pytest-cov==7.1.0 mypy==1.19.1 ruff==0.15.8`

## Self-Check: PASSED

All 22 created files exist on disk. All 5 task commits found in git history:
- 9de808f: chore(01-01): create root config files with pinned dependencies
- 27ead19: feat(01-01): create eleitorum package skeleton with version and config
- 050ee74: test(01-01): create test infrastructure with 85 stub tests
- 98518e2: feat(01-01): implement all 15 synthetic fixture generators
- e440728: fix(01-01): fix build backend and ruff lint issues found in Task 5 iteration loop
