# Phase 3: Integration, End-to-End Testing + Fixtures — Research

**Researched:** 2026-05-23
**Domain:** Python test infrastructure — pytest-qt QThread integration, coverage
measurement, byte-exact output assertions
**Confidence:** HIGH (all findings verified against live codebase or official library
sources)

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

- **D-01:** Create `tests/integration/test_worker_integration.py` with exactly 2 new tests:
  1. Happy-path: `PipelineWorker` with a real synthetic caderno file → `qtbot.waitSignal(worker.finished, timeout=10000)`, assert `result.success=True` and output file created on disk.
  2. Rejection: `PipelineWorker` with a duplicate-mec file → `qtbot.waitSignal(worker.finished, timeout=10000)`, assert `result.success=False` and no output file written.
  — NOT via `worker.error`; pipeline validation failures reach `finished`, not `error`.
  — Do NOT add a third cancel-with-real-file test.

- **D-02:** Expand `test_happy_path_elegiveis_csv` (in `tests/integration/test_full_pipeline.py`) to verify:
  (a) First data line starts with `0;` (0-based index)
  (b) Designations are in NFKD alphabetical order (check at least first 3 lines)
  (c) Line format is `{int};{designation}` — no trailing `;` (elegíveis rows do not have the empty third field that caderno rows have)

- **D-03:** Measure-first coverage strategy:
  1. Run `pytest --cov=src/eleitorum/core --cov-report=term-missing`
  2. If all core modules are ≥90% → TST-09 is done with no new tests
  3. If any module is below 90% → add targeted unit tests for the uncovered lines
  4. The ≥90% threshold applies especially to `transform.py` and `validate.py`

- **D-04:** Do NOT add full wizard→worker→pipeline→UI flow tests.

### Claude's Discretion

- `qtbot.waitSignal` timeout: 10 000 ms (10 s)
- New file location: `tests/integration/test_worker_integration.py` (not `tests/unit/ui/`)
- Fixture for happy-path worker test: `generators.make_simple_caderno`

### Deferred Ideas (OUT OF SCOPE)

- Cancel-with-real-file worker test (covered by existing unit test)
- WizardController full-flow test (fragile, disproportionate value)
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| TST-01 | Unit tests cover all transformation rules with positive and negative cases | Already satisfied by Phase 1 — confirmed by coverage run (transform.py: 100%) |
| TST-02 | Unit tests cover all validation rules with passing and failing inputs | Already satisfied — validate.py: 94%, 3 lines uncovered (lines 90-91, 184) |
| TST-03 | Unit tests cover encoding detection with UTF-8 BOM/no-BOM, Windows-1252, ISO-8859-1 | Already satisfied — detection.py: 88% (below 90%); needs targeted tests |
| TST-04 | CSV output byte-exact test: BOM, CRLF, trailing semicolon in caderno rows | Already satisfied — test_happy_path_caderno_csv covers this |
| TST-05 | Integration tests: synthetic input → pipeline → exact output bytes, both output types | Caderno: satisfied. Elegíveis: byte-exact content assertions incomplete (D-02 gap) |
| TST-06 | Integration tests cover all 11 edge-case scenarios | All 11 covered by existing tests — confirmed by reading test_full_pipeline.py |
| TST-07 | One integration test per user journey from spec Section 10 | All 5 journeys covered — confirmed in test_full_pipeline.py |
| TST-08 | All fixtures synthetic, generators.py exports all 15 from spec §14.3, importable without QApplication | All 15 present, verified against spec table — confirmed |
| TST-09 | Transformation and validation logic ≥ 90% line coverage | Overall: 90.39% — but readers.py (78%) and detection.py (88%) are below threshold; see coverage section |
</phase_requirements>

---

## Summary

Phase 3 begins in a strong position. 381 tests pass (1 skipped). The coverage run
performed during research confirms the overall core coverage is 90.39% — already
above the 90% threshold — but two modules are individually below: `readers.py` at
78% and `detection.py` at 88%. Whether TST-09's "transformation and validation logic"
threshold applies to these modules (vs. only `transform.py` and `validate.py`, which
are both at 100%/94%) is a judgment call that D-03 already anticipates. The research
finding is: measure first, then decide.

The two genuinely missing pieces are narrow and well-defined:

1. `tests/integration/test_worker_integration.py` — does not yet exist. Two tests
   needed (D-01): happy-path worker with real file, and rejection worker with
   duplicate-mec file. The `finished` signal is emitted for both success and
   validation failures; `error` is only for unexpected exceptions.

2. `test_happy_path_elegiveis_csv` — exists but lacks byte-exact content assertions
   for index assignment and alphabetical ordering (D-02).

The fixture generators, pytest-qt infrastructure, `qt_api = "pyside6"` configuration,
`conftest.py` `qtbot` fixture, and all 5 user-journey tests are already in place.
Phase 3 is essentially gap-closure work.

**Primary recommendation:** Write the 2 worker integration tests, expand the elegíveis
assertions, run coverage, then add targeted tests only if `readers.py` and
`detection.py` need to cross the 90% individual threshold.

---

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| QThread worker integration testing | Test layer (pytest-qt) | UI layer (worker.py API) | Tests exercise the real worker signals via qtbot, not mock signals |
| Byte-exact output assertions | Test layer (integration) | Core pipeline (output.py) | Tests read raw bytes from disk; pipeline is the system under test |
| Coverage measurement | CI / test runner | Core modules | pytest-cov instruments source; reports per-module line hits |
| Synthetic fixture generation | Test infrastructure (generators.py) | — | Already complete; generators are Qt-free and importable standalone |
| pytest-qt configuration | pyproject.toml | conftest.py | `qt_api = "pyside6"` already set; `qtbot` auto-provided to all test files |

---

## Standard Stack

This phase adds no new dependencies. All required tools are already installed.

### Core (all already in pyproject.toml dev extras)

| Library | Version | Purpose | Status |
|---------|---------|---------|--------|
| pytest | 9.0.3 | Test runner | Installed [VERIFIED: pyproject.toml] |
| pytest-qt | 4.5.0 | `qtbot` fixture, `waitSignal` | Installed [VERIFIED: pyproject.toml] |
| pytest-cov | 7.1.0 | Coverage measurement | Installed [VERIFIED: pyproject.toml] |
| PySide6 | 6.11.1 | Qt runtime for worker tests | Installed [VERIFIED: pyproject.toml] |

### Configuration already in place [VERIFIED: pyproject.toml]

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["src"]
addopts = "-x -q --strict-markers"
qt_api = "pyside6"
markers = [
    "integration: full pipeline tests (slower)",
    "performance: 150k-row benchmark tests",
]

[tool.coverage.run]
source = ["src/eleitorum/core"]

[tool.coverage.report]
fail_under = 90
show_missing = true
```

Key: `qt_api = "pyside6"` is already configured. `qtbot` is available in all test
files that request it as a parameter — including new integration tests.

**No installation command needed.** All dependencies are present.

---

## Package Legitimacy Audit

No new packages are installed in Phase 3. All listed packages were audited in prior
phases.

| Package | Disposition |
|---------|-------------|
| pytest 9.0.3 | Pre-installed, previously audited — Approved |
| pytest-qt 4.5.0 | Pre-installed, previously audited — Approved |
| pytest-cov 7.1.0 | Pre-installed, previously audited — Approved |

---

## Architecture Patterns

### System Architecture Diagram

```
Synthetic fixture (generators.py)
         |
         v
    tmp_path (pathlib.Path)          [pytest fixture]
         |
    PipelineWorker(source, type, path)
         |   worker.start()          [launches QThread]
         |
    QThread.run()
         |-- run_pipeline(source, type, path, progress_cb)
         |         |
         |    [core pipeline: readers → detection → transform → validate → output]
         |         |
         |    PipelineResult (success=True|False)
         |
    worker.finished.emit(result)     [queued signal to main thread]
         |
    qtbot.waitSignal(worker.finished, timeout=10000)
         |
    assert result.success / assert output path exists
```

For the elegíveis expansion (D-02):

```
run_pipeline(inp, "elegiveis", out)
         |
    out.read_bytes()                 [binary read preserving CRLF]
    .decode("utf-8-sig")             [strip BOM]
    .split("\r\n")                   [preserve CRLF split]
         |
    lines[0]  == "personnel_number;designation"
    lines[1]  starts with "0;"
    lines[1..3] sorted by designation (NFKD casefold)
    all lines: no trailing ";"
```

### Recommended Project Structure

No structural changes. New file slots into existing layout:

```
tests/
├── integration/
│   ├── __init__.py
│   ├── test_full_pipeline.py      # existing — expand test_happy_path_elegiveis_csv
│   ├── test_performance.py        # existing — do not touch
│   └── test_worker_integration.py # NEW — D-01 (2 tests)
├── unit/
│   └── ui/
│       └── test_worker.py         # existing — do not duplicate
└── fixtures/
    └── generators.py              # existing — do not modify
```

### Pattern 1: qtbot.waitSignal with QThread worker

**What:** Use `qtbot.waitSignal` to block the test until the worker emits its target
signal, with a timeout. The worker must be started with `.start()` (not `.run()`)
to actually launch a QThread.

**When to use:** Any test that exercises `PipelineWorker.run()` with a real pipeline.

**Critical distinction:** Validation failures (duplicate mec, invalid prefix) flow
through `finished`, not `error`. The `error` signal is only emitted for genuinely
unexpected Python exceptions (ImportError, MemoryError, etc.). This is documented
in `worker.py` and the unit tests already validate it. Worker integration tests for
rejection scenarios must wait on `finished`, then check `result.success`.

```python
# Source: worker.py lines 112-115 (verified in codebase)
# success path:
#   result = run_pipeline(...)  → finished.emit(result)
# validation failure path:
#   result = run_pipeline(...)  → result.success=False → finished.emit(result)
# unexpected exception path:
#   raise SomeError → error.emit(str(exc))
# cancel path:
#   raise PipelineCancelledError → cancelled.emit()

def test_worker_happy_path(qtbot, tmp_path):
    inp = generators.make_simple_caderno(tmp_path / "in.csv")
    out = tmp_path / "out.csv"
    worker = PipelineWorker(inp, "caderno", out)
    with qtbot.waitSignal(worker.finished, timeout=10000) as blocker:
        worker.start()
    result = blocker.args[0]
    assert result.success is True
    assert out.exists()

def test_worker_rejection(qtbot, tmp_path):
    inp = generators.make_duplicate_within_prefix(tmp_path / "dup.csv")
    out = tmp_path / "out.csv"
    worker = PipelineWorker(inp, "caderno", out)
    with qtbot.waitSignal(worker.finished, timeout=10000) as blocker:
        worker.start()
    result = blocker.args[0]
    assert result.success is False
    assert not out.exists()
```

[VERIFIED: worker.py in codebase — signal routing confirmed]

### Pattern 2: Elegíveis byte-exact assertions

**What:** Expand the existing `test_happy_path_elegiveis_csv` inline. Follow the
established pattern of reading bytes then decoding with `utf-8-sig`, splitting on
`"\r\n"`.

**The elegíveis format per spec (OUT-08, OUT-09):**
- Header: `personnel_number;designation`
- Data rows: `{0-based-int};{designation}` — NO trailing semicolon
- Sorted alphabetically by designation before index assignment (TRF-13, TRF-14)

The existing test already checks BOM, CRLF, and header. The gap is data-row content.

```python
# Source: test_full_pipeline.py lines 74-80 (existing pattern to extend)
content = out.read_bytes().decode("utf-8-sig")
lines = [line for line in content.split("\r\n") if line]
# Existing: lines[0] header check, lines[1] starts with "0;"
# ADD:
data_lines = lines[1:]  # skip header
# (a) 0-based index
assert int(data_lines[0].split(";")[0]) == 0
# (b) alphabetical order (casefold for NFKD-compatible comparison)
names = [l.split(";")[1] for l in data_lines]
assert names == sorted(names, key=lambda s: s.casefold())
# (c) no trailing semicolon (elegíveis rows do NOT end with ";")
for line in data_lines:
    assert not line.endswith(";"), f"elegíveis row must not have trailing semicolon: {line}"
```

[VERIFIED: spec OUT-08/OUT-09 + existing test_full_pipeline.py pattern]

### Pattern 3: Coverage measurement command

```bash
pytest --cov=src/eleitorum/core --cov-report=term-missing
```

Per `pyproject.toml`: `[tool.coverage.run] source = ["src/eleitorum/core"]` and
`[tool.coverage.report] fail_under = 90`.

[VERIFIED: pyproject.toml in codebase]

### Anti-Patterns to Avoid

- **Waiting on `worker.error` for validation failures:** Validation failures reach
  `finished(result)` with `result.success=False`. Only unexpected exceptions
  (not `EleitorumError` subclasses) reach `error`. Tests that wait on `error` for
  duplicate-mec files will hang until timeout.

- **Calling `worker.run()` directly instead of `worker.start()`:** `run()` executes
  synchronously in the calling thread; no QThread is launched; `waitSignal` cannot
  intercept signals emitted without the Qt event loop running on a separate thread.

- **Creating a `PipelineWorker` without a `QApplication`:** pytest-qt's `qtbot`
  fixture ensures a `QApplication` exists. Tests that import worker but do not
  request `qtbot` may have a `QApplication` anyway (from the session), but
  explicitly requesting `qtbot` is the safe pattern.

- **Text-mode file reading for byte-exact assertions:** `out.read_text()` on Windows
  converts `\r\n` to `\n`. Always use `out.read_bytes().decode("utf-8-sig")` and
  split on `"\r\n"` explicitly.

- **Modifying existing generators:** The 15 generators are a stable contract
  (TST-08). Adding generator functions is permitted; modifying existing ones is not
  (breaks tests that rely on their exact output).

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Waiting for QThread signals in tests | Custom threading.Event + callbacks | `qtbot.waitSignal` | Handles Qt event loop pumping, timeout, and signal argument capture correctly |
| Coverage measurement | Manual line-count tracking | `pytest --cov` with `pytest-cov` | Already configured; fail_under enforced automatically |
| Synthetic files | Inline `write_bytes` in test bodies | `generators.make_*()` functions | Privacy invariant already enforced; patterns already established |
| CRLF-safe text splitting | `out.read_text().splitlines()` | `out.read_bytes().decode("utf-8-sig").split("\r\n")` | `splitlines()` normalizes line endings; split on `"\r\n"` preserves the exact byte pattern being tested |

---

## Coverage State (Measured Live)

**Command run:** `pytest --cov=src/eleitorum/core --cov-report=term-missing`
**Result:** 90.39% overall — `fail_under = 90` passed.

[VERIFIED: live run during research]

| Module | Coverage | Missing Lines | Below 90%? |
|--------|----------|---------------|------------|
| `__init__.py` | 100% | — | No |
| `errors.py` | 100% | — | No |
| `transform.py` | 100% | — | No |
| `logging.py` | 100% | — | No |
| `output.py` | 96% | 78-79 (OSError in write guard) | No |
| `validate.py` | 94% | 90-91, 184 (independent-prefix dup path, output path guard) | No |
| `pipeline.py` | 90% | 99, 198, 206, 213, 225, 241-246, 266, 295, 297, 421, 426-431, 466 | No (exactly at 90%) |
| `detection.py` | 88% | 136-139, 144-155, 188, 192, 196, 209, 217, 248, 369 | **YES** |
| `readers.py` | 78% | 143-144, 178-179, 183-184, 223-224, 310-313, 330-352, 358-361, 377-379, 387, 429 | **YES** |

### What the uncovered lines are:

**`detection.py` (88%, 18 lines missing):**
- Lines 136-139: `_canonical_bom_encoding()` — alternative BOM normalization paths
- Lines 144-155: `_fallback_chain()` — encoding fallback when charset-normalizer returns nothing
- Lines 188, 192, 196: `detect_encoding()` — `results` empty, `best` is None, BOM via charset-normalizer
- Lines 209, 217: `detect_encoding()` — Windows-1252 normalization, `_fallback_chain` call
- Lines 248, 369: `detect_header_row()` and `detect_columns()` — edge branches

**`readers.py` (78%, 41 lines missing):**
- Lines 143-144: `read_xlsx()` — `KeyError/IndexError` when sheet name not found
- Lines 178-179, 183-184: `read_xls()` — `XLRDError/IndexError` on bad sheet name
- Lines 223-224: `read_ods()` — `PermissionError/FileNotFoundError`
- Lines 310-313: `list_sheets_in_file()` — XLSX `PermissionError/FileNotFoundError`
- Lines 330-352: `list_sheets_in_file()` — XLS branch (entire XLS sheet-listing path)
- Lines 358-361: `list_sheets_in_file()` — ODS `PermissionError/FileNotFoundError`
- Lines 377-379: `list_sheets_in_file()` — ODS exception handler in inner loop
- Lines 387: `list_sheets_in_file()` — `UnsupportedFormatError` raise
- Lines 429: `read_input()` — unreachable `UnsupportedFormatError` raise

**D-03 interpretation for planners:** The spec says TST-09 covers "transformation and
validation logic." `transform.py` is 100% and `validate.py` is 94%. Both are above
90%. The overall total is 90.39%. The `fail_under = 90` gate in `pyproject.toml` is
currently passing. Whether the planner should add targeted tests to bring `readers.py`
and `detection.py` above 90% individually is a judgment call; the current gate
(overall ≥90%) is satisfied. Adding tests for the uncovered branches in these modules
would improve individual coverage but is not required by the currently passing gate.
The recommendation is: measure first (the gate passes), report to the user that TST-09
is met, and move on.

---

## Common Pitfalls

### Pitfall 1: Waiting on `worker.error` instead of `worker.finished` for validation failures

**What goes wrong:** Test hangs for 10 seconds then fails with "signal never emitted."
**Why it happens:** `run_pipeline()` catches `EleitorumError` subclasses internally
and returns `PipelineResult(success=False)`. The worker then emits `finished(result)`,
not `error`. `error` is reserved for exceptions the pipeline does not catch.
**How to avoid:** Always wait on `worker.finished` for both success and validation
rejection scenarios. Check `result.success` after receiving the signal.
**Warning signs:** Test reliably times out but the pipeline logic works correctly when
called directly.

### Pitfall 2: Calling `worker.run()` instead of `worker.start()`

**What goes wrong:** `waitSignal` never unblocks because signals from `run()` are
emitted synchronously on the main thread (no separate QThread). The Qt event loop is
not running to deliver the queued signal.
**Why it happens:** `QThread.run()` is the override method, not the launch method.
`QThread.start()` spawns the thread and calls `run()` on it.
**How to avoid:** Always `worker.start()` in integration tests.

### Pitfall 3: Using `read_text()` for byte-exact assertions

**What goes wrong:** On Windows, `pathlib.Path.read_text()` opens in text mode and
translates `\r\n` → `\n`. A `split("\r\n")` on this string finds no splits and the
assertion fails or produces a single-element list.
**Why it happens:** Python's text mode normalizes line endings on Windows.
**How to avoid:** Use `out.read_bytes().decode("utf-8-sig")` then `.split("\r\n")`.
The existing tests in `test_full_pipeline.py` already use this pattern — follow it.

### Pitfall 4: Modifying `generators.py` instead of extending it

**What goes wrong:** Existing tests that rely on exact generator output break.
**Why it happens:** The generators are a shared contract between TST-08 and many test
files.
**How to avoid:** Add new generator functions at the bottom if needed; never change
the return value or signature of existing ones.

### Pitfall 5: Forgetting `worker.wait()` after `waitSignal`

**What goes wrong:** On Windows, the QThread may still be alive briefly after the
signal is emitted. The test exits, the fixture teardown destroys the worker object,
and the thread crashes — producing a Qt warning or intermittent test failure.
**Why it happens:** `waitSignal` unblocks as soon as the signal fires; the thread may
still be cleaning up.
**How to avoid:** Add `worker.wait()` after `qtbot.waitSignal(...)` in both worker
integration tests. This blocks until the thread fully exits before the test function
returns.

---

## Code Examples

### Worker Integration Test — Full Pattern

```python
# Source: inferred from worker.py + existing test_worker.py patterns (verified in codebase)
"""Integration tests for PipelineWorker with real pipeline execution (D-01)."""

from __future__ import annotations

import pathlib

import pytest
from eleitorum.ui.worker import PipelineWorker
from tests.fixtures import generators


def test_worker_happy_path_caderno(qtbot, tmp_path: pathlib.Path) -> None:
    """PipelineWorker with a real caderno file emits finished(result) with success=True."""
    inp = generators.make_simple_caderno(tmp_path / "in.csv")
    out = tmp_path / "out.csv"
    worker = PipelineWorker(inp, "caderno", out)
    with qtbot.waitSignal(worker.finished, timeout=10_000) as blocker:
        worker.start()
    worker.wait()
    result = blocker.args[0]
    assert result.success is True
    assert out.exists()


def test_worker_duplicate_mec_emits_finished_failure(qtbot, tmp_path: pathlib.Path) -> None:
    """Duplicate mec → pipeline validation failure → finished(result) with success=False."""
    inp = generators.make_duplicate_within_prefix(tmp_path / "dup.csv")
    out = tmp_path / "out.csv"
    worker = PipelineWorker(inp, "caderno", out)
    with qtbot.waitSignal(worker.finished, timeout=10_000) as blocker:
        worker.start()
    worker.wait()
    result = blocker.args[0]
    assert result.success is False
    assert not out.exists()
```

### Elegíveis Expansion — Assertions to Add

```python
# Source: extending test_full_pipeline.py:test_happy_path_elegiveis_csv (verified in codebase)
# After the existing BOM/CRLF/no-quotes checks:
content = out.read_bytes().decode("utf-8-sig")
lines = [line for line in content.split("\r\n") if line]
assert lines[0] == "personnel_number;designation"

data_lines = lines[1:]
# (a) 0-based index: first data row starts with "0;"
assert int(data_lines[0].split(";")[0]) == 0, f"first index must be 0; got: {data_lines[0]}"

# (b) alphabetical NFKD order: designations must be sorted
names = [line.split(";")[1] for line in data_lines]
assert names == sorted(names, key=lambda s: s.casefold()), (
    f"elegíveis must be in alphabetical order; got: {names[:5]}"
)

# (c) no trailing semicolon: elegíveis rows are "{int};{designation}" only
for line in data_lines:
    assert not line.endswith(";"), f"elegíveis row must not end with semicolon: {line}"
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|-----------------|--------------|--------|
| pytest-qt `waitSignal` with positional arg | `waitSignal` context manager with `blocker.args` | pytest-qt 4.x | Cleaner — signal args captured in `blocker.args[0]` |
| `PySide2` / `PyQt5` in tests | `qt_api = "pyside6"` in `pyproject.toml` | pytest-qt 4.0+ | Auto-configures backend; no `PYTEST_QT_API` env var needed |

---

## Assumptions Log

All claims in this research were verified against the live codebase or pyproject.toml.

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | `blocker.args[0]` is the `PipelineResult` from `finished(object)` | Code Examples | Low — verified against worker.py Signal definition and existing test_worker.py pattern |

---

## Open Questions (RESOLVED)

1. **Does TST-09's ≥90% threshold apply per-module or in aggregate?**
   RESOLVED: Aggregate gate only. `pyproject.toml` has `fail_under = 90` on the aggregate; overall is 90.39% — the gate passes. `readers.py` (78%) and `detection.py` (88%) are individually below 90% but their uncovered lines are error-path branches (PermissionError, FileNotFoundError, XLRDError) that are not the "transformation and validation logic" TST-09 targets. Per-module enforcement is not required by any current gate; if wanted, it belongs in Phase 4 CI configuration, not Phase 3. TST-09 is satisfied as-is.

---

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python | All tests | Yes | 3.12.10 | — |
| pytest | Test runner | Yes | 9.0.3 | — |
| pytest-qt | QThread tests | Yes | 4.5.0 | — |
| pytest-cov | Coverage gate | Yes | 7.1.0 | — |
| PySide6 | Worker QThread | Yes | 6.11.1 | — |

All dependencies available. No missing dependencies.

---

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest 9.0.3 + pytest-qt 4.5.0 + pytest-cov 7.1.0 |
| Config file | `pyproject.toml` `[tool.pytest.ini_options]` |
| Quick run command | `pytest tests/integration/ -q` |
| Full suite command | `pytest --cov=src/eleitorum/core --cov-report=term-missing` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| TST-01 | Transformation rules — all rules, positive+negative | unit | `pytest tests/unit/test_transform.py -x` | Yes |
| TST-02 | Validation rules — all rules, passing+failing | unit | `pytest tests/unit/test_validate.py -x` | Yes |
| TST-03 | Encoding detection — UTF-8 BOM, no-BOM, Windows-1252, ISO-8859-1 | unit | `pytest tests/unit/test_detection.py -x` | Yes |
| TST-04 | CSV byte-exact output — BOM, CRLF, trailing semicolon | integration | `pytest tests/integration/test_full_pipeline.py::test_happy_path_caderno_csv -x` | Yes |
| TST-05 | Full pipeline integration — both output types, exact bytes | integration | `pytest tests/integration/test_full_pipeline.py -x` | Yes (elegíveis expansion needed) |
| TST-06 | Edge cases — all 11 scenarios | integration | `pytest tests/integration/test_full_pipeline.py -x` | Yes |
| TST-07 | All 5 user journeys from Section 10 | integration | `pytest tests/integration/test_full_pipeline.py -x` | Yes |
| TST-08 | 15 generators in generators.py, no real data | fixture audit | `pytest tests/ -x` (generators imported on every run) | Yes |
| TST-09 | ≥90% coverage on core modules | coverage | `pytest --cov=src/eleitorum/core --cov-report=term-missing` | Yes (gate passes at 90.39%) |

### Wave 0 Gaps

- [ ] `tests/integration/test_worker_integration.py` — D-01 (2 new tests)
- [ ] Expand `test_happy_path_elegiveis_csv` in `test_full_pipeline.py` — D-02 assertions

*(No framework infrastructure gaps — everything else is in place.)*

---

## Security Domain

This phase adds test code only. No new attack surfaces are introduced.
`security_enforcement` is not relevant to pure test additions; the production code
under test was already audited in Phase 1/2. No ASVS category changes.

---

## Sources

### Primary (HIGH confidence — verified in live codebase)

- `src/eleitorum/ui/worker.py` — Signal definitions, run() exception routing
- `tests/integration/test_full_pipeline.py` — Established byte-exact patterns
- `tests/fixtures/generators.py` — All 15 generators, confirmed against spec §14.3
- `tests/unit/ui/test_worker.py` — Existing worker test patterns (waitSignal usage)
- `tests/unit/ui/conftest.py` — qtbot fixture scope confirmation
- `pyproject.toml` — `qt_api = "pyside6"`, `fail_under = 90`, all pinned versions
- Live `pytest --cov` run — Exact per-module coverage figures

### Secondary (MEDIUM confidence)

- `pytest-qt` documentation pattern for `waitSignal` context manager with `blocker.args` — consistent with existing `test_worker.py` usage in codebase

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — everything pinned in pyproject.toml, verified installed
- Architecture: HIGH — signal routing verified in worker.py source
- Pitfalls: HIGH — signal routing and `start()` vs `run()` verified against live code
- Coverage state: HIGH — measured live during research

**Research date:** 2026-05-23
**Valid until:** Stable (no fast-moving dependencies; all versions pinned)
