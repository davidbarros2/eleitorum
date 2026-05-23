---
phase: 01-core-pipeline
verified: 2026-05-23T12:00:00Z
status: gaps_found
score: 9/10 must-haves verified
overrides_applied: 0
re_verification: null
gaps:
  - truth: "mypy src/eleitorum exits 0 against the scaffold"
    status: failed
    reason: "detection.py passes path=None to EncodingDetectionError.__init__ at lines 155 and 171, but errors.py defines the argument as path: pathlib.Path (required, non-optional). mypy reports 2 arg-type errors and exits 1."
    artifacts:
      - path: "src/eleitorum/core/detection.py"
        issue: "Lines 155 and 171 call EncodingDetectionError(path=None) — passes None where pathlib.Path is required"
      - path: "src/eleitorum/core/errors.py"
        issue: "EncodingDetectionError.__init__ signature is def __init__(self, path: pathlib.Path) — does not accept None"
    missing:
      - "Change EncodingDetectionError.__init__ signature in errors.py to accept Optional[pathlib.Path]: def __init__(self, path: pathlib.Path | None = None) — this matches plan 03's original design intent per the interfaces block note: 'Cleanest: EncodingDetectionError accepts an optional path'"
      - "OR change both call sites in detection.py lines 155 and 171 to pass a real pathlib.Path instead of None"
deferred: null
human_verification: null
---

# Phase 1: Core Pipeline Verification Report

**Phase Goal:** Build the complete headless core pipeline — all file reading, encoding detection, data transformation, validation, CSV output, and logging — tested to >=90% coverage with a full integration test suite.
**Verified:** 2026-05-23
**Status:** GAPS_FOUND (1 blocker)
**Re-verification:** No — initial verification

---

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | pytest discovers the entire tests/ tree without import errors | VERIFIED | 237 passed, 1 skipped (documented test_read_xls_legacy). All 8 test files importable. |
| 2 | ruff check . and ruff format --check . both exit 0 | VERIFIED | Both commands exit 0 against the full codebase |
| 3 | mypy src/eleitorum exits 0 | FAILED | 2 type errors in detection.py: `Argument "path" to "EncodingDetectionError" has incompatible type "None"; expected "Path"` at lines 155 and 171 |
| 4 | python -c 'import eleitorum' succeeds from the repository root | VERIFIED | `0.1.0 EleitorUM` — version and APP_NAME correct |
| 5 | tests/fixtures/generators.py exports all 15 fixture functions | VERIFIED | All 15 functions present and produce non-empty synthetic files; mojibake bytes confirmed (0xc3 present) |
| 6 | pyproject.toml pins every dependency at exact versions | VERIFIED | openpyxl==3.1.5, xlrd==2.0.2, odfpy==1.4.1, pandas==3.0.2, charset-normalizer==3.4.7; dev: pytest==9.0.3, pytest-cov==7.1.0, mypy==1.19.1, ruff==0.15.8 |
| 7 | Full pipeline produces byte-exact caderno CSV (BOM + CRLF + no quotes + trailing CRLF) | VERIFIED | Spot-check: raw[:3]==b'\xef\xbb\xbf', ends b'\r\n', no '"' bytes, lone_lf==0 |
| 8 | Duplicate validation produces NO output CSV and creates an _ERRORS_ log | VERIFIED | success=False, out.csv does not exist, error_log exists with ERRORS_ in filename |
| 9 | pytest --cov=src/eleitorum/core --cov-fail-under=90 exits 0 | VERIFIED | 91.26% total coverage; all 7 core modules pass 85% individual gate |
| 10 | PERF-01: 150,000-row XLSX completes under 10 seconds | VERIFIED | Elapsed 6.27s (budget 10s, 1.6x headroom) |

**Score:** 9/10 truths verified

---

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `pyproject.toml` | Project metadata, pinned deps, tool config | VERIFIED | Valid TOML; exact version pins confirmed; fail_under=90 present |
| `src/eleitorum/__init__.py` | Exposes __version__, APP_NAME | VERIFIED | Re-exports both; __all__ defined |
| `src/eleitorum/config.py` | APP_NAME = "EleitorUM" | VERIFIED | Correct per BRAND-01 contract |
| `src/eleitorum/version.py` | __version__ = "0.1.0" | VERIFIED | Single source of truth |
| `src/eleitorum/core/__init__.py` | Core sub-package marker | VERIFIED | Exists with docstring |
| `src/eleitorum/core/errors.py` | 8 error classes + FailureRow + format_error_message | VERIFIED | All exports present and importable; 100% coverage |
| `src/eleitorum/core/readers.py` | 6 per-format readers + metadata | VERIFIED | SUPPORTED_EXTENSIONS, ReadResult, SheetInfo, read_input, list_sheets all present; read_only=True appears 4 times |
| `src/eleitorum/core/detection.py` | Encoding + header + column detection | VERIFIED (runtime) | Exports present; 88% coverage; runtime behavior correct. NOTE: mypy type error at lines 155+171 (path=None passed to non-optional arg) |
| `src/eleitorum/core/transform.py` | All 15 TRF rules | VERIFIED | All exports present; 100% coverage; VALID_PREFIXES/FDB_SHARED correct |
| `src/eleitorum/core/validate.py` | Aggregated VAL checks + path guards | VERIFIED | UniquenessTracker, ValidationOutcome, validate_rows, validate_output_path present; 94% coverage |
| `src/eleitorum/core/output.py` | Byte-exact CSV writer | VERIFIED | USE_BOM=True, CADERNO_HEADER/ELEGIVEIS_HEADER correct; write_caderno produces correct BOM+CRLF+no-quote output; 96% coverage |
| `src/eleitorum/core/logging.py` | Log builder with 9 PT-PT tags | VERIFIED | TAGS frozenset correct (9 tags); format_log_line matches spec format_log_line("INICIO","msg",ts)=="[...] INICIO  msg"; 100% coverage |
| `src/eleitorum/core/pipeline.py` | Qt-free orchestrator | VERIFIED | run_pipeline, PipelineSource, PipelineResult all exported; 511 lines; no Qt imports |
| `tests/fixtures/generators.py` | All 15 fixture functions | VERIFIED | All 15 present with correct signatures; SYNTHETIC_NAMES and SYNTHETIC_PREFIXES defined at module level |
| `tests/conftest.py` | Shared fixtures + huge_caderno_xlsx_path | VERIFIED | SYNTHETIC_NAMES (10 entries), SYNTHETIC_PREFIXES per D-08, huge_caderno_xlsx_path session-scoped |
| `tests/unit/test_errors.py` | Real tests (no stubs) | VERIFIED | 36 tests passing, 0 skipped |
| `tests/unit/test_readers.py` | Real tests (1 documented skip) | VERIFIED | 38 passing, 1 skipped (test_read_xls_legacy, documented) |
| `tests/unit/test_detection.py` | Real tests (0 skips) | VERIFIED | 29 tests passing |
| `tests/unit/test_transform.py` | Real tests (0 skips) | VERIFIED | 46 tests passing |
| `tests/unit/test_validate.py` | Real tests (0 skips) | VERIFIED | 23 tests passing |
| `tests/unit/test_output.py` | Real tests (0 skips) | VERIFIED | 27 tests passing |
| `tests/unit/test_logging.py` | Real tests (0 skips) | VERIFIED | 20 tests passing |
| `tests/integration/test_full_pipeline.py` | 18 integration tests | VERIFIED | 18 passing; all 5 user journeys covered + PERF-03 streaming assertion |
| `tests/integration/test_performance.py` | PERF-01 benchmark | VERIFIED | 1 test passing in 6.27s |

---

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `tests/conftest.py` | `tests/fixtures/generators.py` | from tests.fixtures.generators import | VERIFIED | Import confirmed in conftest |
| `pyproject.toml` | `src/eleitorum/` | [tool.setuptools.packages.find] where = ['src'] | VERIFIED | where = ["src"] present |
| `pyproject.toml` | `pytest tests/` | testpaths | VERIFIED | testpaths = ["tests"] present |
| `src/eleitorum/core/readers.py` | `src/eleitorum/core/errors.py` | from eleitorum.core.errors import | VERIFIED | UnsupportedFormatError, FileAccessError imported |
| `src/eleitorum/core/readers.py` | `openpyxl` | load_workbook(read_only=True, data_only=True) | VERIFIED | Exact call pattern present 4 times |
| `src/eleitorum/core/detection.py` | `src/eleitorum/core/errors.py` | from eleitorum.core.errors import | VERIFIED | EncodingDetectionError, ColumnDetectionError imported |
| `src/eleitorum/core/detection.py` | `charset_normalizer.from_bytes` | from charset_normalizer import from_bytes | VERIFIED | Import present |
| `src/eleitorum/core/detection.py` | `unicodedata.normalize NFKD` | normalize('NFKD', ...) | VERIFIED | NFKD normalization used in normalize_col_name |
| `src/eleitorum/core/transform.py` | `src/eleitorum/core/errors.py` | from eleitorum.core.errors import MecanograficoError | VERIFIED | Import confirmed |
| `src/eleitorum/core/validate.py` | `src/eleitorum/core/errors.py` | from eleitorum.core.errors import | VERIFIED | FailureRow, OutputPathError imported |
| `src/eleitorum/core/output.py` | stdlib csv with QUOTE_NONE | csv.QUOTE_NONE present | VERIFIED | QUOTE_NONE in output.py |
| `src/eleitorum/core/output.py` | `src/eleitorum/core/transform.py` | from eleitorum.core.transform import sort_elegiveis | VERIFIED | Import confirmed |
| `src/eleitorum/core/logging.py` | `%Y-%m-%d %H:%M:%S` timestamp format | format_log_line uses strftime | VERIFIED | Exact format string present |
| `src/eleitorum/core/pipeline.py` | all other core modules | from eleitorum.core import readers, detection, transform, validate, output | VERIFIED | All module imports present |
| `src/eleitorum/core/pipeline.py` | progress_cb | Callable[[int, int], None] | VERIFIED | progress_cb parameter; called every 100 rows |

---

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
|----------|---------------|--------|--------------------|--------|
| `pipeline.py / run_pipeline` | read_result.rows | readers.read_input() | Yes — reads actual file bytes via openpyxl/pandas/csv | FLOWING |
| `output.py / write_caderno` | rows | parameter from pipeline | Yes — pipeline passes validated, transformed rows | FLOWING |
| `logging.py / write_log_file` | builder.entries | LogBuilder.add() calls throughout pipeline | Yes — events accumulated during real processing | FLOWING |

---

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| Happy-path caderno: BOM + CRLF + no quotes | run_pipeline(make_simple_caderno, 'caderno', out) | BOM: efbbbf, ends CRLF: True, no quotes: True | PASS |
| Duplicate rejection: no CSV, error log created | run_pipeline(make_duplicate_within_prefix, 'caderno', out) | success=False, out.csv absent, error_log exists | PASS |
| Elegiveis: sorted alphabetically with 0-based index | run_pipeline(make_simple_elegiveis, 'elegiveis', out) | Lines: personnel_number;designation, 0;Ana..., 1;Beatriz... | PASS |
| D-07 aggregation: 3 failures collected, no short-circuit | validate_rows(3-failure input) | len(failures)==3 confirmed | PASS |
| Coverage gate: 90% minimum | pytest --cov-fail-under=90 | 91.26% total — gate green | PASS |
| PERF-01: 150k rows under 10s | test_performance.py | 6.27s elapsed | PASS |
| mypy src/eleitorum | mypy src/eleitorum | 2 errors in detection.py (path=None type mismatch) | FAIL |

---

### Probe Execution

No probe scripts declared or conventional in this phase. Step 7c: SKIPPED.

---

### Requirements Coverage

All 65 Phase 1 requirements (INP-01 to INP-13, DET-01 to DET-07, TRF-01 to TRF-15, VAL-01 to VAL-09, OUT-01 to OUT-12, LOG-01 to LOG-07, PERF-01, PERF-03) have at least one passing test.

Evidence:
- INP-01 through INP-13: tests/unit/test_readers.py (38 passing, 1 documented skip for INP-02 XLS write path)
- DET-01 through DET-07: tests/unit/test_detection.py (29 passing)
- TRF-01 through TRF-15: tests/unit/test_transform.py (46 passing)
- VAL-01 through VAL-09: tests/unit/test_validate.py (23 passing)
- OUT-01 through OUT-12: tests/unit/test_output.py (27 passing)
- LOG-01 through LOG-07: tests/unit/test_logging.py (20 passing)
- PERF-01: tests/integration/test_performance.py (1 passing, 6.27s < 10s)
- PERF-03: tests/integration/test_full_pipeline.py::test_perf_03_streaming_mode_assertion (passing; monkeypatched kwargs confirmed read_only=True, data_only=True)

| Requirement Group | Source Plan | Status |
|-------------------|-------------|--------|
| INP-01..13 | 01-02, 01-05 | SATISFIED |
| DET-01..07 | 01-03, 01-05 | SATISFIED |
| TRF-01..15 | 01-03, 01-05 | SATISFIED |
| VAL-01..09 | 01-04, 01-05 | SATISFIED |
| OUT-01..12 | 01-04, 01-05 | SATISFIED |
| LOG-01..07 | 01-04, 01-05 | SATISFIED |
| PERF-01, PERF-03 | 01-05 | SATISFIED |

---

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| `src/eleitorum/core/detection.py` | 155, 171 | `EncodingDetectionError(path=None)` — None passed to non-optional Path argument | WARNING | mypy exits 1; runtime produces ugly "ficheiro 'None'" in error message when encoding detection fails on empty bytes or undecodable content |

No TBD, FIXME, XXX debt markers in any core module file. No TODO/HACK/PLACEHOLDER markers. No `pandas.to_csv` or `chardet` usage.

---

### Gaps Summary

**1 gap blocking complete status:**

The SUMMARY documentation claims "mypy: Success: no issues found in X source files" across multiple plans, but the actual codebase currently fails `mypy src/eleitorum` with 2 errors in `src/eleitorum/core/detection.py`.

Root cause: Plan 03 ran in a parallel worktree and created its own version of `errors.py` with `EncodingDetectionError(path: pathlib.Path | None = None)` (accepting None). Plan 02's version (which won after merge) used the stricter signature `EncodingDetectionError(path: pathlib.Path)`. After merge, detection.py retained the `path=None` call sites from Plan 03's assumption, but errors.py reflects Plan 02's stricter signature. The two call sites at lines 155 and 171 of detection.py pass `None` where `pathlib.Path` is now required.

The fix is a one-line change to errors.py: `def __init__(self, path: pathlib.Path | None = None)`. This was the original design intent per the Plan 03 interfaces block note: "Cleanest: EncodingDetectionError accepts an optional path."

All other phase objectives are fully met:
- 237 passing tests (218 unit + 1 skipped + 18 integration + 1 performance)
- 91.26% test coverage (hard gate 90% met)
- PERF-01 150k rows in 6.27s (budget 10s)
- Zero Qt imports in core/
- Zero forbidden patterns (pandas.to_csv, chardet)
- Byte-exact output verified by spot-checks
- D-07 aggregation verified (3 failures collected, no short-circuit)
- All 65 Phase 1 requirements have passing tests

---

_Verified: 2026-05-23_
_Verifier: Claude (gsd-verifier)_
