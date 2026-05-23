# Phase 3 Coverage Report — TST-09 Verification

**Measured:** 2026-05-23
**Strategy:** D-03 (measure-first — add targeted tests only if aggregate gate fails)
**Gate:** `fail_under = 90` on aggregate `src/eleitorum/core` (pyproject.toml)

---

## Command Used

```
pytest --cov=src/eleitorum/core --cov-report=term-missing
```

Executed from the worktree root after Tasks 1 and 2 (the 2 new worker integration
tests and the elegíveis D-02 assertions) were in place.

---

## Per-Module Coverage Table

| Module | Statements | Missing | Cover | Missing Lines |
|--------|-----------|---------|-------|---------------|
| `src/eleitorum/core/__init__.py` | 0 | 0 | 100% | — |
| `src/eleitorum/core/detection.py` | 147 | 18 | 88% | 136-139, 144-155, 188, 192, 196, 209, 217, 248, 369 |
| `src/eleitorum/core/errors.py` | 68 | 0 | 100% | — |
| `src/eleitorum/core/logging.py` | 45 | 0 | 100% | — |
| `src/eleitorum/core/output.py` | 48 | 2 | 96% | 78-79 |
| `src/eleitorum/core/pipeline.py` | 173 | 17 | 90% | 99, 198, 206, 213, 225, 241-246, 266, 295, 297, 421, 426-431, 466 |
| `src/eleitorum/core/readers.py` | 184 | 41 | 78% | 143-144, 178-179, 183-184, 223-224, 310-313, 330-352, 358-361, 377-379, 387, 429 |
| `src/eleitorum/core/transform.py` | 124 | 0 | 100% | — |
| `src/eleitorum/core/validate.py` | 54 | 3 | 94% | 90-91, 184 |
| **TOTAL** | **843** | **81** | **90%** | |

**Reported total:** `Required test coverage of 90.0% reached. Total coverage: 90.39%`

---

## Gate Result

**TST-09 satisfied: aggregate TOTAL >= 90% with fail_under=90 passing.**

`pytest --cov=src/eleitorum/core --cov-report=term-missing --cov-fail-under=90` exits 0.

Test counts: **383 passed, 1 skipped** (381 prior + 2 new D-01 worker integration tests).

---

## Modules Below 90% (Individual Threshold)

Per D-03 and RESEARCH §Open Questions (RESOLVED), per-module enforcement is NOT
part of the current gate. The `fail_under = 90` in `pyproject.toml` applies to the
aggregate TOTAL only. The two modules below 90% individually are:

### `detection.py` — 88% (18 missing lines)

Missing lines are error-path branches in the encoding detection subsystem:
- Lines 136-139: `_canonical_bom_encoding()` — alternative BOM normalisation paths
- Lines 144-155: `_fallback_chain()` — encoding fallback when charset-normalizer returns nothing
- Lines 188, 192, 196: `detect_encoding()` — empty results, None best, BOM via charset-normalizer
- Lines 209, 217: `detect_encoding()` — Windows-1252 normalisation, `_fallback_chain` call
- Lines 248, 369: `detect_header_row()` and `detect_columns()` — edge branches

**Note:** Per-module enforcement of the 90% threshold for `detection.py` is NOT part
of the current gate (D-03 decision + RESEARCH §Open Questions RESOLVED). These
uncovered branches cover encoding edge cases that are not the "transformation and
validation logic" TST-09 targets. If per-module enforcement is desired, it belongs in
Phase 4 CI configuration.

### `readers.py` — 78% (41 missing lines)

Missing lines are exception-handler branches in the file-reading subsystem:
- Lines 143-144: `read_xlsx()` — `KeyError/IndexError` when sheet name not found
- Lines 178-179, 183-184: `read_xls()` — `XLRDError/IndexError` on bad sheet name
- Lines 223-224: `read_ods()` — `PermissionError/FileNotFoundError`
- Lines 310-313: `list_sheets_in_file()` — XLSX `PermissionError/FileNotFoundError`
- Lines 330-352: `list_sheets_in_file()` — XLS branch (entire XLS sheet-listing path)
- Lines 358-361: `list_sheets_in_file()` — ODS `PermissionError/FileNotFoundError`
- Lines 377-379: `list_sheets_in_file()` — ODS exception handler in inner loop
- Lines 387: `list_sheets_in_file()` — `UnsupportedFormatError` raise
- Lines 429: `read_input()` — unreachable `UnsupportedFormatError` raise

**Note:** Per-module enforcement of the 90% threshold for `readers.py` is NOT part
of the current gate (D-03 decision + RESEARCH §Open Questions RESOLVED). These
uncovered branches are PermissionError/FileNotFoundError/XLRDError handlers that
represent OS-level failure conditions, not transformation or validation logic. If
per-module enforcement is desired, it belongs in Phase 4 CI configuration.

---

## Conclusion

The aggregate gate (`fail_under = 90`) is satisfied at 90.39% coverage across
`src/eleitorum/core/`. No production code was modified to achieve this result.
The two new test files (Tasks 1 and 2) added coverage via real pipeline execution,
and the aggregate coverage remained at the research baseline (90.39%) — confirming
that the gate was already passing before Phase 3 additions.
