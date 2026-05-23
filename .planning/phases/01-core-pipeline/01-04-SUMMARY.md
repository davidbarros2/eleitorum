---
phase: 01-core-pipeline
plan: "04"
subsystem: core-validation-output-logging
tags: [validation, output, logging, csv, bom, crlf, fdb-namespace, tdd]
dependency_graph:
  requires:
    - 01-02 (errors.py — FailureRow, ValidationError, OutputPathError, FileAccessError)
    - 01-03 (transform.py — FDB_SHARED, ChangeRecord, sort_elegiveis)
  provides:
    - src/eleitorum/core/validate.py (UniquenessTracker, ValidationOutcome, validate_rows, validate_output_path)
    - src/eleitorum/core/output.py (write_caderno, write_elegiveis, build_output_filename, USE_BOM, CADERNO_HEADER, ELEGIVEIS_HEADER)
    - src/eleitorum/core/logging.py (LogBuilder, LogTag, TAGS, format_log_line, write_log_file, write_error_log_file)
    - tests/unit/test_validate.py (23 tests, 0 skipped)
    - tests/unit/test_output.py (27 tests, 0 skipped)
    - tests/unit/test_logging.py (20 tests, 0 skipped)
  affects:
    - 01-05 (pipeline.py wires all three modules together; validate_rows is the gate before output.py is called)
tech_stack:
  added: []
  patterns:
    - TDD RED/GREEN/REFACTOR (per-task commit discipline)
    - D-07 aggregated validation: collect all failures before returning, never short-circuit
    - D-08 prefix namespaces: F/D/B share a numeric namespace; A/PG/ID/Q/EX are independent
    - Byte-exact CSV: csv.QUOTE_NONE + escapechar='\\' + lineterminator='\r\n' + encoding='utf-8-sig'
    - LogBuilder with clock injection for deterministic testing
    - Path.resolve(strict=False) for symlink-safe path comparison (ASVS V12)
    - UTF-8 BOM forced on empty log files via f.write("") before content
key_files:
  created:
    - src/eleitorum/core/validate.py
    - src/eleitorum/core/output.py
    - src/eleitorum/core/logging.py
  modified:
    - tests/unit/test_validate.py (replaced 11 Wave 0 stubs with 23 real tests)
    - tests/unit/test_output.py (replaced 10 Wave 0 stubs with 27 real tests)
    - tests/unit/test_logging.py (replaced 8 Wave 0 stubs with 20 real tests)
decisions:
  - "validate_rows collects ALL failures before returning (D-07) — UniquenessTracker.record() returns FailureRow on collision but loop always continues"
  - "F/D/B prefix collision detected via fdb_seen dict keyed by number (not prefix+number) — FDB_SHARED frozenset from transform.py reused"
  - "output.py calls validate_output_path internally as defense-in-depth (T-1-04-03) even though pipeline.py also calls it"
  - "LogBuilder.clock injection makes tests deterministic without monkeypatching datetime"
  - "UTF-8 BOM on empty log files: f.write('') forces utf-8-sig codec to emit BOM even with no content"
  - "csv._writer is not publicly typed — _make_writer returns Any (mypy limitation)"
metrics:
  duration: "9m"
  completed: "2026-05-23"
  tasks_completed: 4
  tasks_total: 4
  files_created: 3
  files_modified: 3
---

# Phase 1 Plan 4: Validate, Output, and Logging Modules Summary

**One-liner:** Aggregated VAL-01..09 validation with F/D/B shared namespace, byte-exact CSV writer (UTF-8 BOM + semicolon + CRLF + no-quote) for both output types, and spec-verbatim PT-PT transformation log builder with all 9 tags.

## What Was Built

### Task 1 — validate.py + test_validate.py (TDD: RED commit `e607d22`, GREEN commit `01be0ce`)

`src/eleitorum/core/validate.py`:
- `UniquenessTracker`: stateful accumulator with `fdb_seen` dict (F/D/B share number namespace) and `independent_seen` dict (A/PG/ID/Q/EX each get their own namespace per D-08). `record()` returns FailureRow on collision, None on success — caller's loop never breaks.
- `ValidationOutcome`: frozen dataclass with `passed: bool` and `failures: list[FailureRow]`.
- `validate_rows`: iterates all rows, checks VAL-06 (empty name), VAL-07 (caderno requires valid mec), VAL-03/04/05 (uniqueness via tracker). Collects ALL failures before returning — never raises.
- `validate_output_path`: VAL-08 (same-as-input via Path.resolve()) + OUT-12 (overwrite guard). Defense-in-depth via `strict=False` resolution.

`tests/unit/test_validate.py`: 23 tests, 0 skipped. All VAL-01..09 + D-07 + D-08 covered.

**Coverage: validate.py 94%**

### Task 2 — output.py + test_output.py (TDD: RED commit `ff3e400`, GREEN commit `9c8cde4`)

`src/eleitorum/core/output.py`:
- Constants: `USE_BOM=True`, `CADERNO_HEADER`, `ELEGIVEIS_HEADER`, `_OUTPUT_ENCODING="utf-8-sig"`, `_DELIMITER=";"`, `_LINETERMINATOR="\r\n"`.
- `_open_writer(path) -> IO[str]`: wraps `open()` with PermissionError/OSError → FileAccessError(mode="write").
- `_make_writer(f) -> Any`: builds `csv.writer(QUOTE_NONE + escapechar='\\' + lineterminator='\r\n')`.
- `write_caderno(path, rows, *, input_path, overwrite_allowed)`: applies output guards, writes header + data rows with empty third field (OUT-07).
- `write_elegiveis(path, designations, ...)`: calls `sort_elegiveis` (D-02 NFKD sort), assigns 0-based indices, writes header + rows.
- `build_output_filename(input_path, output_type)`: derives `{type}_{stem}.csv` for UI save dialog.

`tests/unit/test_output.py`: 27 tests, 0 skipped. All OUT-01..12 covered.

**Coverage: output.py 96%**

### Task 3 — logging.py + test_logging.py (TDD: RED commit `b45b52b`, GREEN commit `84cf0a2`)

`src/eleitorum/core/logging.py`:
- `LogTag` TypeAlias + `TAGS` frozenset: all 9 PT-PT tags (INICIO, INPUT, COLUNA, CASO, LIMPEZA, AVISO, ERRO, SAIDA, FIM).
- `format_log_line(tag, message, ts)`: spec-verbatim `[{ts}] {tag:<7} {message}` — tag field is 7-char wide left-aligned.
- `LogBuilder`: `add(tag, message, ts)` + `add_change(row_index, ChangeRecord)`. Clock injection (`clock: Callable`) for deterministic tests.
- `write_log_file(builder, output_csv_path, ts)`: writes `{stem}_LOG_{ts}.txt` in same dir as output CSV (LOG-01, LOG-07).
- `write_error_log_file(builder, intended_output_path, ts)`: writes `{stem}_ERRORS_{ts}.txt` (LOG-05).
- Both write functions write UTF-8 with BOM (LOG-02); BOM forced via `f.write("")` before content.

`tests/unit/test_logging.py`: 20 tests, 0 skipped. All LOG-01..07 covered.

**Coverage: logging.py 100%**

### Task 4 — Iteration loop (commit `9a9d9d0`)

| Check | Command | Result |
|-------|---------|--------|
| 1 | `ruff check` on plan 04 files | PASS |
| 2 | `ruff format --check` | PASS (2 files auto-formatted) |
| 3 | `mypy` on 3 core modules | PASS (0 issues) |
| 4 | `pytest tests/unit/ -x -q` | PASS (218 passed, 1 skipped) |
| 5 | Coverage report | 91.65% total (above 90% gate) |
| 6 | Smoke import | PASS |
| 7 | Qt guard | PASS (no matches) |
| 8 | Anti-pattern guard | PASS (no pandas.to_csv/chardet) |

**Per-module coverage:**
| Module | Coverage |
|--------|----------|
| validate.py | 94% |
| output.py | 96% |
| logging.py | 100% |
| Cumulative (all 7 core modules) | 91.65% |

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] BOM not written to empty log files**
- **Found during:** Task 3 GREEN phase — `test_error_log_encoding_utf8_with_bom` failed
- **Issue:** Python's `utf-8-sig` codec writes the BOM lazily only when the first character is flushed. An empty `write_log_file` call produced a zero-byte file.
- **Fix:** Added `f.write("")` before the entry loop — this forces the codec to emit the UTF-8 BOM even when `builder.entries` is empty.
- **Files modified:** `src/eleitorum/core/logging.py`
- **Commit:** 84cf0a2 (part of GREEN phase)

**2. [Rule 1 - Bug] ruff UP035: Callable import from wrong module**
- **Found during:** Task 4 — `ruff check` Step 1
- **Issue:** `from typing import Callable` triggers UP035 in Python 3.10+; should be `from collections.abc import Callable`.
- **Fix:** Auto-fixed by `ruff --fix`.
- **Files modified:** `src/eleitorum/core/logging.py`
- **Commit:** 9a9d9d0

**3. [Rule 1 - Bug] ruff F401: unused FailureRow import in logging.py**
- **Found during:** Task 4 — `ruff check` Step 1
- **Issue:** Plan spec included `from eleitorum.core.errors import FailureRow` in logging.py imports, but FailureRow is not used directly in the module (write_error_log_file accepts a LogBuilder, not FailureRow objects directly).
- **Fix:** Auto-removed by `ruff --fix`.
- **Files modified:** `src/eleitorum/core/logging.py`
- **Commit:** 9a9d9d0

**4. [Rule 1 - Bug] mypy: _open_writer missing return type annotation**
- **Found during:** Task 4 — `mypy` Step 3
- **Issue:** `_open_writer(path)` had no return type annotation; `_make_writer` had `csv.writer` as return type annotation, but `csv.writer` is a function not a type in Python's csv module.
- **Fix:** Changed `_open_writer` return type to `IO[str]`; changed `_make_writer` return type to `Any` (csv's internal writer class is not publicly typed).
- **Files modified:** `src/eleitorum/core/output.py`
- **Commit:** 9a9d9d0

**5. [Rule 1 - Bug] ruff E741: ambiguous variable name `l` in test_output.py**
- **Found during:** Task 4 — `ruff check` Step 1
- **Issue:** Two list comprehensions used `l` as the loop variable.
- **Fix:** Renamed to `line`.
- **Files modified:** `tests/unit/test_output.py`
- **Commit:** 9a9d9d0

## Known Stubs

None. All three modules are fully implemented.

## Threat Flags

No new security-relevant surface introduced beyond what was planned in the threat_model section.

Mitigations verified:
- T-1-04-01: `validate_output_path` uses `Path.resolve(strict=False)` for symlink-safe comparison — tested by `test_validate_output_path_resolves_symlinks_or_relative`
- T-1-04-02: Partial-write responsibility documented in output.py docstring (pipeline.py must call `unlink(missing_ok=True)` on FileAccessError)
- T-1-04-03: OUT-12 overwrite guard present in both `write_caderno` and `write_elegiveis` — tested by `test_existing_file_collision_raises_or_renames` and `test_write_elegiveis_existing_file_collision`
- T-1-04-04: LOG-07 user-location-only guarantee tested by `test_log_written_only_to_user_chosen_location` (asserts no file in `tempfile.gettempdir()`)
- T-1-04-05: write_error_log_file writes only `message_pt` content, never tracebacks
- T-1-04-06: UniquenessTracker asserts uppercase prefix on entry (Pitfall 6 guard) — tested by `test_fdb_cross_prefix_collision_mixed_case_input`

## TDD Gate Compliance

All three tasks followed the RED/GREEN cycle:

| Task | RED commit | GREEN commit |
|------|-----------|--------------|
| validate.py | e607d22 (test) | 01be0ce (feat) |
| output.py | ff3e400 (test) | 9c8cde4 (feat) |
| logging.py | b45b52b (test) | 84cf0a2 (feat) |

REFACTOR phase not needed — all three implementations passed mypy, ruff, and pytest after the GREEN commit with only iteration-loop-discovered fixes (committed as chore in Task 4).

## Verification Evidence

```
ruff check (plan 04 files): All checks passed!
ruff format --check: 6 files already formatted
mypy: Success: no issues found in 3 source files
pytest tests/unit/: 218 passed, 1 skipped in 1.03s

Module coverage:
  validate.py:   94% (54 stmts, 3 missed)
  output.py:     96% (48 stmts, 2 missed)
  logging.py:   100% (45 stmts, 0 missed)
  
Total core coverage: 91.65% (>= 90% gate reached)

Qt guard: no matches in src/eleitorum/core/
Anti-pattern guard: no pandas.to_csv/chardet in src/eleitorum/core/

Smoke import: from eleitorum.core import validate, output; from eleitorum.core import logging as elt_logging → OK
BOM inline test: raw[:3] == b'\xef\xbb\xbf' → OK
CRLF inline test: b'\r\n' in raw AND raw.endswith(b'\r\n') → OK
No-quote inline test: b'"' not in raw → OK
```

## Self-Check: PASSED

All 3 created files exist on disk:
- FOUND: src/eleitorum/core/validate.py
- FOUND: src/eleitorum/core/output.py
- FOUND: src/eleitorum/core/logging.py

All 7 task commits found in git history:
- e607d22: test(01-04): add failing tests for validate.py (RED phase)
- 01be0ce: feat(01-04): implement validate.py — aggregated VAL-01..09 checks
- ff3e400: test(01-04): add failing tests for output.py (RED phase)
- 9c8cde4: feat(01-04): implement output.py — byte-exact CSV writer for caderno + elegíveis
- b45b52b: test(01-04): add failing tests for logging.py (RED phase)
- 84cf0a2: feat(01-04): implement logging.py — transformation/error log with 9 PT-PT tags
- 9a9d9d0: chore(01-04): iteration loop green — ruff, mypy, pytest all pass for plan 04
