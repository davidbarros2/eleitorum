---
phase: 03-integration-end-to-end-testing-fixtures
reviewed: 2026-05-23T18:10:25Z
depth: standard
files_reviewed: 2
files_reviewed_list:
  - tests/integration/test_worker_integration.py
  - tests/integration/test_full_pipeline.py
findings:
  critical: 1
  warning: 2
  info: 2
  total: 5
status: issues_found
---

# Phase 03: Code Review Report

**Reviewed:** 2026-05-23T18:10:25Z
**Depth:** standard
**Files Reviewed:** 2
**Status:** issues_found

## Summary

Two integration test files were reviewed at standard depth. Cross-referenced against
`tests/fixtures/generators.py`, `src/eleitorum/core/pipeline.py`, `src/eleitorum/core/transform.py`,
`src/eleitorum/core/validate.py`, `src/eleitorum/core/output.py`, `src/eleitorum/core/logging.py`,
and `src/eleitorum/ui/worker.py`.

The overall test structure is sound: signal-routing contracts are respected in the worker tests,
fixture isolation is clean (each test owns its `tmp_path`), and most assertions correctly reflect
the pipeline's documented behaviour. However, one critical dead assertion in the U+FFFD test
means a failure to remove the replacement character from output would go completely undetected,
plus two warnings around a wrong sort key and an incorrect type annotation.

---

## Critical Issues

### CR-01: Dead assertion — `b"fffd"` check never detects U+FFFD in UTF-8 output

**File:** `tests/integration/test_full_pipeline.py:382`

**Issue:** The assertion

```python
assert "fffd".encode("ascii") not in raw.lower(), (
    "replacement character bytes should not appear in output"
)
```

is permanently `True` regardless of file content. `"fffd".encode("ascii")` produces
`b'\x66\x66\x66\x64'` (four printable ASCII bytes). U+FFFD, when encoded as UTF-8,
is `b'\xef\xbf\xbd'` — these three bytes can never match the ASCII sequence `fffd`.
`raw.lower()` does not decode the bytes; it byte-folds ASCII values only, leaving
`\xef\xbf\xbd` unchanged. The check therefore always passes, whether or not the
replacement character was actually removed. If `transform.py`'s `remove_replacement_characters`
stopped working, this assertion would not catch it.

The *string* assertion on line 386 (`assert "â" not in output_text`) provides
real coverage for the transformed text; it is the only effective guard here.
Line 382 provides zero protection and is actively misleading.

**Fix:** Replace the dead bytes check with a correct UTF-8 bytes check:

```python
# CORRECT: U+FFFD in UTF-8 is 3 bytes EF BF BD
assert b"\xef\xbf\xbd" not in raw, (
    "replacement character (U+FFFD) bytes should not appear in UTF-8 output"
)
```

---

## Warnings

### WR-01: Wrong sort key in elegíveis ordering assertion

**File:** `tests/integration/test_full_pipeline.py:92`

**Issue:** The assertion that verifies alphabetical order uses Python's `str.casefold()` as its
sort key:

```python
assert names == sorted(names, key=lambda s: s.casefold()), (
    f"elegíveis must be in alphabetical order; got first 5: {names[:5]}"
)
```

The production code (`transform.sort_elegiveis` / `output.write_elegiveis`) sorts by
`unicodedata.normalize("NFKD", s.casefold()).encode("ascii", "ignore").decode("ascii")` —
a diacritic-stripped NFKD key. These two sort keys are *not* equivalent for strings
containing accented characters. For example, `"Ász Teste"` sorts *before* `"Azul Teste"`
under the NFKD key (accent stripped, `as` < `az`), but *after* under plain `casefold`
(`ász` > `azul` in Unicode code-point order).

The current `make_simple_elegiveis` fixture happens to contain only names whose NFKD
and casefold orderings coincide, so the test passes today. If the fixture is ever
extended with names containing accented first characters at a critical position, the
assertion will either produce false negatives (it claims the output is sorted when it
is not by the real key) or false positives (it fails the sort check on a correctly-sorted
output). Either outcome silently erodes confidence in the test suite.

**Fix:** Use the same NFKD key as the production code:

```python
import unicodedata

def _nfkd_key(s: str) -> str:
    return unicodedata.normalize("NFKD", s.casefold()).encode("ascii", "ignore").decode("ascii")

assert names == sorted(names, key=_nfkd_key), (
    f"elegíveis must be in NFKD alphabetical order; got first 5: {names[:5]}"
)
```

### WR-02: Incorrect type annotation for `qtbot` parameter — defeats static analysis

**File:** `tests/integration/test_worker_integration.py:25`, `test_worker_integration.py:52`

**Issue:** Both test functions annotate `qtbot` as `pytest.FixtureRequest`:

```python
def test_worker_happy_path_caderno(qtbot: pytest.FixtureRequest, ...) -> None:
def test_worker_duplicate_mec_emits_finished_failure(qtbot: pytest.FixtureRequest, ...) -> None:
```

`pytest.FixtureRequest` is the fixture-metadata object; it does not have `waitSignal`,
`waitSignals`, `mouseClick`, or any other `QtBot` method. The correct type is
`pytestqt.qtbot.QtBot`. With the wrong annotation, mypy will silently accept calls to
non-existent `FixtureRequest` attributes while rejecting valid `QtBot` API, making the
type checker useless for these tests.

**Fix:**

```python
from pytestqt.qtbot import QtBot

def test_worker_happy_path_caderno(qtbot: QtBot, tmp_path: pathlib.Path) -> None:
    ...

def test_worker_duplicate_mec_emits_finished_failure(
    qtbot: QtBot, tmp_path: pathlib.Path
) -> None:
    ...
```

---

## Info

### IN-01: Test name implies success but test body asserts failure

**File:** `tests/integration/test_full_pipeline.py:284`

**Issue:** The function is named `test_excel_float_numbers_converted_logged`, which
implies the float values are successfully *converted* and *logged*. In reality the test
asserts `result.success is False` — the float values are *rejected* as invalid mec codes
(no prefix). The docstring on lines 285-298 does explain the correct behaviour, but the
function name contradicts it and will mislead anyone scanning the test suite name list.

**Fix:** Rename to reflect the actual behaviour:

```python
def test_excel_float_numbers_rejected_as_invalid_mec(tmp_path: pathlib.Path) -> None:
```

### IN-02: Missing `from __future__ import annotations` for consistency

**File:** `tests/integration/test_full_pipeline.py:1`

**Issue:** `test_worker_integration.py` includes `from __future__ import annotations`
(line 15) but `test_full_pipeline.py` does not. Both files use identical Python 3.11+
annotation syntax (`pathlib.Path`, `pytest.MonkeyPatch`). While omitting this import is
not a bug in Python 3.11, the inconsistency is a maintenance signal: if a future
maintainer adds a forward reference or a `|`-union annotation expecting lazy evaluation,
`test_full_pipeline.py` will behave differently from its sibling.

**Fix:** Add the import as the first non-docstring line in `test_full_pipeline.py`:

```python
from __future__ import annotations
```

---

_Reviewed: 2026-05-23T18:10:25Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
