---
phase: 03-integration-end-to-end-testing-fixtures
fixed_at: 2026-05-23T18:30:00Z
review_path: .planning/phases/03-integration-end-to-end-testing-fixtures/03-REVIEW.md
iteration: 1
findings_in_scope: 5
fixed: 5
skipped: 0
status: all_fixed
---

# Phase 03: Code Review Fix Report

**Fixed at:** 2026-05-23T18:30:00Z
**Source review:** .planning/phases/03-integration-end-to-end-testing-fixtures/03-REVIEW.md
**Iteration:** 1

**Summary:**
- Findings in scope: 5
- Fixed: 5
- Skipped: 0

## Fixed Issues

### CR-01: Dead assertion — `b"fffd"` check never detects U+FFFD in UTF-8 output

**Files modified:** `tests/integration/test_full_pipeline.py`
**Commit:** dfc509f
**Applied fix:** Replaced `assert "fffd".encode("ascii") not in raw.lower()` with `assert b"\xef\xbf\xbd" not in raw`. The old check used the ASCII byte sequence for the string "fffd" (four printable bytes `\x66\x66\x66\x64`) which could never match U+FFFD's actual UTF-8 encoding (`\xef\xbf\xbd`). The new check uses the correct three-byte UTF-8 sequence directly.

### WR-01: Wrong sort key in elegíveis ordering assertion

**Files modified:** `tests/integration/test_full_pipeline.py`
**Commit:** 08520cb
**Applied fix:** Added `import unicodedata` to the imports. Replaced the `lambda s: s.casefold()` sort key with a `_nfkd_key` helper function that matches the production sort: `unicodedata.normalize("NFKD", s.casefold()).encode("ascii", "ignore").decode("ascii")`. Also updated the assertion message to say "NFKD alphabetical order".

### WR-02: Incorrect type annotation for `qtbot` parameter — defeats static analysis

**Files modified:** `tests/integration/test_worker_integration.py`
**Commit:** f0c7e14
**Applied fix:** Added `from pytestqt.qtbot import QtBot` import. Replaced both `qtbot: pytest.FixtureRequest` annotations with `qtbot: QtBot` in `test_worker_happy_path_caderno` and `test_worker_duplicate_mec_emits_finished_failure`.

### IN-01: Test name implies success but test body asserts failure

**Files modified:** `tests/integration/test_full_pipeline.py`
**Commit:** f9ff5ae
**Applied fix:** Renamed `test_excel_float_numbers_converted_logged` to `test_excel_float_numbers_rejected_as_invalid_mec` to accurately reflect that the test asserts `result.success is False` (float mec values without prefix are rejected, not converted).

### IN-02: Missing `from __future__ import annotations` for consistency

**Files modified:** `tests/integration/test_full_pipeline.py`
**Commit:** 99e00c1
**Applied fix:** Added `from __future__ import annotations` as the first non-docstring line in `test_full_pipeline.py`, matching the existing import in `test_worker_integration.py`.

---

_Fixed: 2026-05-23T18:30:00Z_
_Fixer: Claude (gsd-code-fixer)_
_Iteration: 1_
