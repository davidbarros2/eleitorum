---
phase: quick-260525-q6z
plan: 01
subsystem: ui
tags: [signal, navbar, wizard, pyside6, tdd]
dependency_graph:
  requires: []
  provides: [completion_changed signals on StepType/StepUpload/StepSheet]
  affects: [src/eleitorum/ui/wizard.py, src/eleitorum/ui/steps/step_type.py, src/eleitorum/ui/steps/step_upload.py, src/eleitorum/ui/steps/step_sheet.py]
tech_stack:
  added: []
  patterns: [PySide6 Signal class attribute, signal-slot wiring in QObject.__init__]
key_files:
  created:
    - tests/unit/ui/test_step_signals.py
    - tests/unit/ui/test_wizard_navbar.py
  modified:
    - src/eleitorum/ui/steps/step_type.py
    - src/eleitorum/ui/steps/step_upload.py
    - src/eleitorum/ui/steps/step_sheet.py
    - src/eleitorum/ui/wizard.py
decisions:
  - Emit completion_changed from both success and EleitorumError paths in StepUpload._on_file_received (state always changed); do NOT emit from invalid-extension early-return (no state change)
  - Emit completion_changed unconditionally in StepSheet._on_selection_changed (both select and deselect change completion state)
  - Remove stale comment block describing planned-but-unimplemented signal wiring in wizard.py
metrics:
  duration: 15m
  completed: "2026-05-25T17:58:54Z"
  tasks_completed: 2
  files_changed: 6
---

# Phase quick-260525-q6z Plan 01: Fix Próximo Button Not Enabling on Steps 1–3 Summary

**One-liner:** Reactive Próximo button via completion_changed Signal on StepType, StepUpload, StepSheet wired to WizardController._update_navbar_for_current_step.

## What Was Built

Added a `completion_changed = Signal()` class attribute to each of the three interactive step widgets and emitted the signal at the correct state-changing points. Wired all three signals to `_update_navbar_for_current_step` in `WizardController.__init__`, replacing the previous once-on-navigation poll with reactive updates.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| RED | Failing tests for step signals + wizard navbar | 05121dc | tests/unit/ui/test_step_signals.py, tests/unit/ui/test_wizard_navbar.py |
| GREEN | completion_changed on steps + wizard wiring | 8b17e41 | step_type.py, step_upload.py, step_sheet.py, wizard.py, test files updated |

## Implementation Details

### StepType (step_type.py)
- Added `from PySide6.QtCore import Signal`
- Added `completion_changed = Signal()` class attribute
- `_on_selection()`: emits after writing session and deselecting the other card

### StepUpload (step_upload.py)
- Added `from PySide6.QtCore import Signal`
- Added `completion_changed = Signal()` class attribute
- `_on_file_received()`: emits in the success path (after `session.sheets = sheets`) and in the EleitorumError path (after clearing `source_path`). Does NOT emit on the invalid-extension early return — no session state changed.

### StepSheet (step_sheet.py)
- Extended `from PySide6.QtCore import Qt` to `from PySide6.QtCore import Qt, Signal`
- Added `completion_changed = Signal()` class attribute
- `_on_selection_changed()`: emits unconditionally — both selection and deselection change completion state.

### WizardController (wizard.py)
- Added three connections immediately after the NavBar signal block:
  ```python
  self._step_type.completion_changed.connect(self._update_navbar_for_current_step)
  self._step_upload.completion_changed.connect(self._update_navbar_for_current_step)
  self._step_sheet.completion_changed.connect(self._update_navbar_for_current_step)
  ```
- Removed the stale comment block (lines 431–436 in original) that described intent but was never implemented.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed EleitorumError constructor call in test**
- **Found during:** Task 1 GREEN — test for EleitorumError path failed with `TypeError`
- **Issue:** `EleitorumError("msg1", "msg2")` — constructor only accepts `message_pt` + keyword args; no second positional arg
- **Fix:** Changed test to use a helper function that calls `EleitorumError("Erro de teste sintético")` and raises it; simplified monkeypatch
- **Files modified:** tests/unit/ui/test_step_signals.py
- **Commit:** 8b17e41

**2. [Rule 1 - Bug] Fixed NavBar button attribute name in test**
- **Found during:** Task 2 — test referenced `navbar._proximo_btn` but actual attribute is `navbar._btn_proximo`
- **Fix:** Renamed all occurrences in test_wizard_navbar.py
- **Files modified:** tests/unit/ui/test_wizard_navbar.py
- **Commit:** 8b17e41

### Structural Note

The plan specified test files at `tests/ui/test_step_signals.py` and `tests/ui/test_wizard_navbar.py`. The actual project test structure uses `tests/unit/ui/`. Files were created at the correct path conforming to the existing project layout.

## Verification Results

- `python -m pytest tests/unit/ui/test_step_signals.py` — 7 passed
- `python -m pytest tests/unit/ui/test_wizard_navbar.py` — 3 passed
- `python -m pytest tests/ --ignore=tests/integration` — 375 passed, 1 skipped
- `ruff check` — all checks passed
- `mypy` on 4 modified files — no issues found

## TDD Gate Compliance

- RED gate: `test(quick-260525-q6z-01)` commit 05121dc — 7 + 3 failing tests
- GREEN gate: `feat(quick-260525-q6z-01)` commit 8b17e41 — all 10 tests pass

## Known Stubs

None.

## Threat Flags

None — changes are pure internal Qt signal wiring; no new network endpoints, auth paths, file access patterns, or schema changes.

## Self-Check: PASSED

- src/eleitorum/ui/steps/step_type.py — FOUND, contains `completion_changed = Signal()`
- src/eleitorum/ui/steps/step_upload.py — FOUND, contains `completion_changed = Signal()`
- src/eleitorum/ui/steps/step_sheet.py — FOUND, contains `completion_changed = Signal()`
- src/eleitorum/ui/wizard.py — FOUND, contains `completion_changed.connect`
- tests/unit/ui/test_step_signals.py — FOUND
- tests/unit/ui/test_wizard_navbar.py — FOUND
- Commit 05121dc — FOUND
- Commit 8b17e41 — FOUND
