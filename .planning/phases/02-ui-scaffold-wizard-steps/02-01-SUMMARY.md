---
phase: 02-ui-scaffold-wizard-steps
plan: "01"
subsystem: ui-toolchain
tags: [pyside6, qthread, worker, pytest-qt, toolchain]
dependency_graph:
  requires: []
  provides:
    - PySide6==6.11.1 declared in pyproject.toml (runtime dependency)
    - pytest-qt==4.5.0 declared in pyproject.toml (dev dependency)
    - qt_api=pyside6 in pytest ini_options (TST-10)
    - src/eleitorum/ui/ package (importable)
    - PipelineWorker(QThread) with progress/finished/error/cancelled signals
    - PipelineCancelledError(Exception) — NOT EleitorumError subclass
    - tests/unit/ui/ test package with 5 passing smoke tests
  affects:
    - All Phase 2 plans (PySide6 now available; worker seam established)
tech_stack:
  added:
    - PySide6==6.11.1 (runtime)
    - pytest-qt==4.5.0 (dev)
  patterns:
    - QThread subclass overriding run() — single long-running call pattern
    - threading.Event for cancel signalling across thread boundary
    - Signal(int, int) / Signal(object) / Signal() cross-thread delivery
    - PipelineCancelledError NOT-EleitorumError for cancel propagation
key_files:
  created:
    - pyproject.toml (modified — PySide6, pytest-qt, version bumps, qt_api)
    - src/eleitorum/ui/__init__.py (1 line — package marker)
    - src/eleitorum/ui/worker.py (118 lines — PipelineWorker + PipelineCancelledError)
    - tests/unit/ui/__init__.py (0 bytes — package marker)
    - tests/unit/ui/conftest.py (26 lines — placeholder fixture)
    - tests/unit/ui/test_worker.py (98 lines — 5 smoke tests)
  modified:
    - pyproject.toml
decisions:
  - PipelineCancelledError placed in ui/worker.py (not core/errors.py) — must NOT subclass EleitorumError so it escapes pipeline's catch block
  - PySide6==6.11.1 is a runtime dependency (ships in bundle), not dev-only
  - threading.Event (not QThread.terminate()) for safe cancel — prevents file handle corruption
  - str(exc) only in error.emit() — ASVS V7 / T-02-01-02 enforcement
metrics:
  duration: "4 minutes"
  completed: "2026-05-23"
  tasks_completed: 3
  files_created: 6
  tests_added: 5
  tests_total: 242
---

# Phase 2 Plan 1: Wave 0 Toolchain Scaffold Summary

**One-liner:** PySide6 6.11.1 + pytest-qt 4.5.0 toolchain declared; PipelineWorker QThread with threading.Event cancel mechanism and PipelineCancelledError isolation established.

## What Was Built

### Task 1 — pyproject.toml Updates (commit `6b2f593`)

Updated `pyproject.toml` with all Phase 2 toolchain requirements:

- **Runtime dependency added:** `PySide6==6.11.1` (ships in PyInstaller bundle)
- **Dev dependency added:** `pytest-qt==4.5.0` (TST-10)
- **Version bumps (CLAUDE.md recommended pins):**
  - `pandas` 3.0.2 → 3.0.3
  - `mypy` 1.19.1 → 2.1.0
  - `ruff` 0.15.8 → 0.15.14
- **pytest config:** `qt_api = "pyside6"` added to `[tool.pytest.ini_options]`

**Toolchain versions actually installed:**
- PySide6: 6.11.1 (verified `PySide6.__version__ == '6.11.1'`)
- pytest-qt: 4.5.0 (verified import)

### Task 2 — UI Package + PipelineWorker (commit `d31cd70`)

**`src/eleitorum/ui/__init__.py`** — 1-line package marker (module docstring only), mirrors `src/eleitorum/core/__init__.py` pattern.

**`src/eleitorum/ui/worker.py`** — 118 lines:
- `PipelineCancelledError(Exception)` — intentionally NOT an `EleitorumError` subclass so it propagates through `run_pipeline()`'s `except EleitorumError` catch block unchanged
- `PipelineWorker(QThread)` with 4 class-level `Signal` attributes: `progress = Signal(int, int)`, `finished = Signal(object)`, `error = Signal(str)`, `cancelled = Signal()`
- `cancel()` → `threading.Event.set()` (safe cancel; no QThread.terminate())
- `_progress_cb(current, total)` → raises `PipelineCancelledError` if cancelled, else `self.progress.emit(current, total)`
- `run()` exception ordering: `PipelineCancelledError` first → `cancelled.emit()`; generic `Exception` second → `error.emit(str(exc))` only; success → `finished.emit(result)`

### Task 3 — Test Infrastructure + Smoke Tests (commit `08d7ee3`)

**`tests/unit/ui/__init__.py`** — zero-byte package marker.

**`tests/unit/ui/conftest.py`** — 26 lines. Module docstring references TST-10 and synthetic-data invariant. `session_fresh` placeholder fixture (returns `None`; real `SessionModel` fixture added in plan 02-02).

**`tests/unit/ui/test_worker.py`** — 98 lines, `class TestPipelineWorker` with 5 tests:

| Test | What it verifies |
|------|-----------------|
| `test_cancelled_error_not_eleitorumerror_subclass` | Cancel propagation contract — `PipelineCancelledError` NOT in EleitorumError hierarchy |
| `test_worker_signals_are_class_attributes` | Class-level `Signal` descriptors (not per-instance) |
| `test_progress_cb_raises_on_cancel` | `cancel()` → `_progress_cb()` raises `PipelineCancelledError` |
| `test_progress_cb_emits_when_not_cancelled` | `qtbot.waitSignal(worker.progress)` receives `(50, 100)` |
| `test_worker_run_emits_cancelled_when_cancelled` | End-to-end: cancel before start → `cancelled` signal emits (not `error`) |

**Test results:**
- `pytest tests/unit/ui/test_worker.py -x -q`: **5 passed** in 0.57s
- `pytest` (full suite): **242 passed, 1 skipped** (237 Phase 1 + 5 new)

## Deviations from Plan

None — plan executed exactly as written.

The plan listed `tests/unit/ui/` as the test directory (not `tests/ui/` as mentioned in RESEARCH.md Wave 0 gap list). The plan's `<files>` block and VALIDATION.md both use `tests/unit/ui/` which matches the existing Phase 1 test structure. Followed the plan's specification.

## Confirmation: PipelineCancelledError NOT in eleitorum.core.errors

`PipelineCancelledError` is defined exclusively in `src/eleitorum/ui/worker.py`.

It does NOT appear in `src/eleitorum/core/errors.py`. This is intentional: the class must not subclass `EleitorumError` (which would cause `run_pipeline()` to swallow it and return `PipelineResult(success=False)` instead of propagating it to the worker's `run()` method).

## Threat Model Verification

All T-02-01-* mitigations applied:

| Threat ID | Mitigation Applied |
|-----------|--------------------|
| T-02-01-01 | PySide6==6.11.1 exact pin in pyproject.toml |
| T-02-01-02 | `error.emit(str(exc))` only — no `traceback.format_exc()` anywhere in worker.py |
| T-02-01-03 | threading.Event checked in `_progress_cb`; PipelineCancelledError is NOT EleitorumError |
| T-02-01-04 | Qt queued connections used (accepted — thread-safe by design) |

## Threat Flags

None — no new security-relevant surface beyond what was planned. PipelineWorker only emits signals; no new file access patterns, network endpoints, or schema changes.

## Known Stubs

**`tests/unit/ui/conftest.py` — `session_fresh` fixture returns `None`.**
This is intentional. The real `SessionModel` fixture requires `src/eleitorum/ui/session.py` which is created in plan 02-02. The stub is documented in the fixture docstring and will be replaced in 02-02.

No stubs that block this plan's goal. The worker is fully functional and tested.

## Self-Check

## Self-Check: PASSED

| Check | Result |
|-------|--------|
| pyproject.toml exists | FOUND |
| src/eleitorum/ui/__init__.py exists | FOUND |
| src/eleitorum/ui/worker.py exists | FOUND |
| tests/unit/ui/__init__.py exists | FOUND |
| tests/unit/ui/conftest.py exists | FOUND |
| tests/unit/ui/test_worker.py exists | FOUND |
| Commit 6b2f593 (pyproject.toml) | FOUND |
| Commit d31cd70 (worker) | FOUND |
| Commit 08d7ee3 (tests) | FOUND |
| PySide6==6.11.1 importable | PASSED |
| PipelineCancelledError NOT EleitorumError subclass | PASSED |
| qt_api = "pyside6" in pyproject.toml | PASSED |
| PySide6==6.11.1 in dependencies | PASSED |
| pytest-qt==4.5.0 in dev dependencies | PASSED |
