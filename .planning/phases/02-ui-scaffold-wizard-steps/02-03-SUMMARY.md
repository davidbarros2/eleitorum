---
phase: 02-ui-scaffold-wizard-steps
plan: "03"
subsystem: ui-widgets
tags: [pyside6, widgets, navbar, option-card, drop-zone, qss, drag-drop, pytest-qt, tdd]
dependency_graph:
  requires:
    - 02-01 (PySide6 toolchain + pytest-qt infrastructure)
    - 02-02 (strings.py BTN_* constants; theme.py QSS dynamic property selectors;
             SUPPORTED_EXTENSIONS via core.readers)
  provides:
    - src/eleitorum/ui/widgets/__init__.py (widgets subpackage marker)
    - NavBar(QWidget) in src/eleitorum/ui/widgets/navbar.py
    - OptionCard(QFrame) in src/eleitorum/ui/widgets/option_card.py
    - DropZone(QFrame) in src/eleitorum/ui/widgets/drop_zone.py
  affects:
    - Plans 02-04 and 02-05 (step widgets compose NavBar + OptionCard + DropZone)
    - Plan 02-06 (app entry point uses NavBar via wizard controller)
tech_stack:
  added: []
  patterns:
    - "NavBar(QWidget) — HBoxLayout with Cancelar left, stretch, Anterior+Próximo right"
    - "Signal forwarding via clicked.connect(self.signal_name) (not lambda)"
    - "OptionCard(QFrame) — StrongFocus + setProperty('selected', False) pattern"
    - "QSS Dynamic Property Refresh: setProperty → unpolish → polish (RESEARCH Pattern 6/7)"
    - "Signal-only-on-True-transition: deselect is silent, step widget orchestrates deselection"
    - "DropZone(QFrame) — setAcceptDrops(True) + extension whitelist from core.readers"
    - "Windows PySide6 drag-event test pattern: helper functions scope QDragEnterEvent/QDropEvent
       objects to avoid pytest repr access violations on test failure"
key_files:
  created:
    - src/eleitorum/ui/widgets/__init__.py (0 lines — package marker)
    - src/eleitorum/ui/widgets/navbar.py (84 lines — NavBar footer widget)
    - src/eleitorum/ui/widgets/option_card.py (108 lines — OptionCard selectable card)
    - src/eleitorum/ui/widgets/drop_zone.py (98 lines — DropZone drag target)
    - tests/unit/ui/test_widgets_navbar.py (73 lines — 7 tests)
    - tests/unit/ui/test_widgets_option_card.py (106 lines — 9 tests)
    - tests/unit/ui/test_widgets_drop_zone.py (195 lines — 8 tests)
  modified: []
decisions:
  - "QDragEnterEvent/QDropEvent objects in tests scoped to helper functions — prevents
     Windows access violation when pytest tries to repr() the event objects on test failure
     (PySide6 6.11.1 C++ object lifetime issue specific to Windows + pytest-rerunfailures)"
  - "OptionCard emits 'selected' signal only on True transition; False (deselect) is silent
     per PATTERNS.md — step_type orchestrates deselection of the other card"
  - "_btn_proximo.setObjectName('primary') on NavBar for QSS accent-color targeting"
metrics:
  duration: "8 minutes"
  completed: "2026-05-23"
  tasks_completed: 3
  files_created: 7
  tests_added: 24
  tests_total: 299
---

# Phase 2 Plan 3: Reusable Widget Library Summary

**One-liner:** Three reusable PySide6 widgets — NavBar footer, OptionCard selectable card, DropZone drag target — with QSS dynamic property discipline and 24 pytest-qt smoke tests all green.

## What Was Built

### Task 1 — widgets package + NavBar (commit `54c0069`)

**`src/eleitorum/ui/widgets/__init__.py`** — zero-byte package marker (matches `core/__init__.py` convention).

**`src/eleitorum/ui/widgets/navbar.py`** — 84 lines:
- `class NavBar(QWidget)` with class-level `Signal` attributes: `anterior_clicked`, `proximo_clicked`, `cancelar_clicked`
- Layout: `QHBoxLayout` with `contentsMargins(8, 8, 8, 8)`, `spacing(8)`; Cancelar on far left, `addStretch()`, Anterior + Próximo on right
- Each button `setMinimumWidth(100)` per spacing spec
- `_btn_proximo.setObjectName("primary")` for QSS accent-color rule
- Labels from `strings.py` constants (`BTN_ANTERIOR`, `BTN_PROXIMO`, `BTN_CANCELAR`) — no hardcoded literals
- Public API: `set_anterior_enabled(bool)`, `set_proximo_enabled(bool)`, `set_proximo_text(str)`, `set_cancel_visible(bool)`

**`tests/unit/ui/test_widgets_navbar.py`** — 7 tests:
- Button text from strings.py, 3 signal emission tests, set_anterior_enabled, set_proximo_text, set_cancel_visible

### Task 2 — OptionCard (commit `9f196b1`)

**`src/eleitorum/ui/widgets/option_card.py`** — 108 lines:
- `class OptionCard(QFrame)` with `selected = Signal(str)`
- `__init__(key, heading="", description="", parent=None)`: StrongFocus, `setProperty('selected', False)`, icon placeholder 48×48, cardHeading + cardDescription QLabels
- `set_selected(value: bool)`: early return on no-change; `setProperty` → `unpolish` → `polish`; emits only on True transition
- `mousePressEvent` + `keyPressEvent` (Space, Return, Enter) overrides for APP-17 keyboard access

**`tests/unit/ui/test_widgets_option_card.py`** — 9 tests:
- Construct + key + default property, set_selected True/False, signal emit on True, no signal on False, mouse click, Space key, Return key, StrongFocus policy, property toggle discipline

### Task 3 — DropZone (commit `4c482e9`)

**`src/eleitorum/ui/widgets/drop_zone.py`** — 98 lines:
- `class DropZone(QFrame)` with `file_dropped = Signal(str)`
- `__init__`: `setAcceptDrops(True)`, `setMinimumHeight(120)`, `setProperty('drag_active', False)`, placeholder QLabel centered
- `dragEnterEvent`: validates extension via `SUPPORTED_EXTENSIONS` from `core.readers` (no duplication); calls `acceptProposedAction()` + `_set_active(True)` or `event.ignore()`
- `dragLeaveEvent`: `_set_active(False)`
- `dropEvent`: `_set_active(False)` first; validates extension; `acceptProposedAction()` + `file_dropped.emit(path)`
- `_set_active(value)`: `setProperty('drag_active', value)` → `unpolish` → `polish`

**`tests/unit/ui/test_widgets_drop_zone.py`** — 8 tests:
- Construction, accept .xlsx drag, reject .png drag, file_dropped signal with path, drag leave resets property, drop resets property, SUPPORTED_EXTENSIONS import check (DRY), property toggle discipline

## DRY Enforcement Confirmation

`grep -E '^from eleitorum.core.readers import.*SUPPORTED_EXTENSIONS' src/eleitorum/ui/widgets/drop_zone.py` returns exactly one match. No extension list is duplicated in drop_zone.py.

## APP-06 Verification

`grep -nE 'setGeometry\(\s*[1-9]|move\(\s*[1-9]' src/eleitorum/ui/widgets/*.py` returns no matches. All layout is via `QHBoxLayout` / `QVBoxLayout` — no hard-coded pixel coordinates.

## Test Results

| Suite | Tests | Result |
|-------|-------|--------|
| test_widgets_navbar.py | 7 | PASSED |
| test_widgets_option_card.py | 9 | PASSED |
| test_widgets_drop_zone.py | 8 | PASSED |
| **Widget total** | **24** | **PASSED** |
| Full suite (pytest -q) | 299 passed, 1 skipped | PASSED |

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed Windows PySide6 drag-event repr access violation in pytest**
- **Found during:** Task 3 GREEN phase
- **Issue:** When `QDragEnterEvent` / `QDropEvent` objects are held as local variables in pytest test functions, pytest's `_pytest._io.saferepr.repr_instance` attempts to call `repr()` on them after the C++ backing object has been freed. This triggers a Windows access violation (segfault exit 139). The root cause is PySide6 6.11.1's C++ object lifetime: Qt frees event objects after dispatch, but Python keeps the reference alive long enough for pytest's failure reporter to attempt repr.
- **Fix:** Moved event construction and dispatch into module-level helper functions (`_send_drag_enter`, `_send_drop`, `_send_drag_leave`) that capture only the boolean result (accepted/not) or dispatch-only, so no `QDragEnterEvent`/`QDropEvent` reference escapes to pytest's variable frame.
- **Impact:** Test intent fully preserved — all 8 tests pass and verify the same contracts. Production code (drop_zone.py) unchanged.
- **Files modified:** `tests/unit/ui/test_widgets_drop_zone.py`
- **Commit:** included in `4c482e9`

## Threat Model Verification

All T-02-03-* dispositions applied:

| Threat ID | Disposition | Mitigation Applied |
|-----------|-------------|-------------------|
| T-02-03-01 | mitigate | SUPPORTED_EXTENSIONS whitelist check in `dragEnterEvent` runs BEFORE any I/O; DropZone emits only path string; actual file opened by readers.py |
| T-02-03-02 | accept | OptionCard `key` is step_upload code; only "caderno"/"elegiveis" passed |
| T-02-03-03 | accept | Absolute path shown only in-app to same user; never written to disk or transmitted |
| T-02-03-04 | accept | DropZone reads only `urls[0]`; no loop over URL list |

## Threat Flags

None — no new security-relevant surface introduced beyond the planned scope.

## Known Stubs

None. All plan goals achieved; no stubs block the plan's objective.

- OptionCard icon placeholder (`_icon_label` 48×48 reserved) is intentional per plan spec — step widget populates QPixmap
- NavBar layout, signals, and public API fully functional

## Platform Note: Windows Headless Drag Event Construction

`QDragEnterEvent` and `QDropEvent` construction works correctly on Windows with PySide6 6.11.1 via `QApplication.sendEvent()`. The access violation only manifests when pytest's failure reporter tries to `repr()` these objects after a test failure. The workaround (scoping events to helper functions) is documented in the test module docstring.

## Self-Check

| Check | Result |
|-------|--------|
| src/eleitorum/ui/widgets/__init__.py exists | FOUND |
| src/eleitorum/ui/widgets/navbar.py exists | FOUND |
| src/eleitorum/ui/widgets/option_card.py exists | FOUND |
| src/eleitorum/ui/widgets/drop_zone.py exists | FOUND |
| tests/unit/ui/test_widgets_navbar.py exists | FOUND |
| tests/unit/ui/test_widgets_option_card.py exists | FOUND |
| tests/unit/ui/test_widgets_drop_zone.py exists | FOUND |
| Commit 54c0069 (widgets + NavBar) | FOUND |
| Commit 9f196b1 (OptionCard) | FOUND |
| Commit 4c482e9 (DropZone) | FOUND |
| NavBar signals fire | PASSED — 3 signal tests green |
| NavBar public API | PASSED — set_anterior_enabled, set_proximo_text, set_cancel_visible tested |
| OptionCard StrongFocus | PASSED |
| OptionCard QSS property toggles | PASSED |
| OptionCard emits only on True | PASSED |
| DropZone SUPPORTED_EXTENSIONS import | PASSED — single import, no duplication |
| DropZone accept/reject by extension | PASSED |
| DropZone file_dropped signal | PASSED |
| DropZone drag_active property toggles | PASSED |
| APP-06: no setGeometry/move non-zero | PASSED — grep returns no matches |
| 24 widget tests pass | PASSED |
| 299 total tests pass (1 skipped) | PASSED |

## Self-Check: PASSED
