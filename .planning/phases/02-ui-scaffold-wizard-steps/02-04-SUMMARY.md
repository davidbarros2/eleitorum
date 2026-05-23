---
phase: 02-ui-scaffold-wizard-steps
plan: "04"
subsystem: ui-wizard-steps
tags: [pyside6, wizard, steps, option-card, drop-zone, session-model, pytest-qt, tdd]
dependency_graph:
  requires:
    - 02-02 (SessionModel, strings.py, theme.py)
    - 02-03 (OptionCard, DropZone, NavBar widgets)
  provides:
    - src/eleitorum/ui/steps/__init__.py (steps subpackage marker)
    - StepType(QWidget) in src/eleitorum/ui/steps/step_type.py (WIZ-01)
    - StepUpload(QWidget) in src/eleitorum/ui/steps/step_upload.py (WIZ-02)
    - StepSheet(QWidget) in src/eleitorum/ui/steps/step_sheet.py (WIZ-03)
    - StepColumns(QWidget) in src/eleitorum/ui/steps/step_columns.py (WIZ-04)
  affects:
    - Plan 02-05 (step_processing, step_preview, step_done compose the steps package)
    - Plan 02-06 (app entry point + wizard controller assembles all steps)
tech_stack:
  added: []
  patterns:
    - "StepType: OptionCard pair with mutual exclusivity via _on_selection slot"
    - "Session state restored in __init__ for back-navigation (Reiniciar flow)"
    - "StepUpload: extension whitelist check BEFORE any I/O (T-02-04-01)"
    - "EleitorumError caught from list_sheets(); .message_pt displayed inline (T-02-04-02)"
    - "isHidden() used in tests instead of isVisible() for unshown widget checks"
    - "StepSheet: QListWidgetItem.setData(Qt.UserRole, raw_name) for display/raw name split"
    - "StepColumns: auto vs manual mode based on detection_method from pipeline_result.detection"
    - "QComboBox.blockSignals(True/False) during populate to suppress spurious index changes"
    - "DET-07: _mec_row.setVisible(False) when session.output_type == 'elegiveis'"
key_files:
  created:
    - src/eleitorum/ui/steps/__init__.py (0 bytes — package marker)
    - src/eleitorum/ui/steps/step_type.py (111 lines — StepType WIZ-01)
    - src/eleitorum/ui/steps/step_upload.py (155 lines — StepUpload WIZ-02)
    - src/eleitorum/ui/steps/step_sheet.py (131 lines — StepSheet WIZ-03)
    - src/eleitorum/ui/steps/step_columns.py (275 lines — StepColumns WIZ-04)
    - tests/unit/ui/test_step_type.py (83 lines — 6 tests)
    - tests/unit/ui/test_step_upload.py (130 lines — 7 tests)
    - tests/unit/ui/test_step_sheet.py (117 lines — 6 tests)
    - tests/unit/ui/test_step_columns.py (158 lines — 8 tests)
  modified: []
decisions:
  - "isHidden() used in tests instead of isVisible() for widgets not attached to a shown parent — isVisible() in Qt depends on the full parent chain being visible; isHidden() reflects the explicit flag set by setVisible()"
  - "SHEET_PICKER_ROWS_TEMPLATE.format(rows=N) produces '(N linhas)'; display text is 'SheetName (N linhas)' — template has no {name} placeholder, consistent with strings.py"
  - "StepColumns._populate_combo() uses blockSignals(True/False) to suppress spurious currentIndexChanged signals during initial population"
  - "session.column_headers consumed as definitive SessionModel field (list[str] | None) — no duck-typing; added in plan 02-02 Task 1 as documented"
  - "BTN_ALTERAR styled as QPushButton in this plan; QSS inline-link visual treatment deferred to plan 06 QSS refinement (noted in output section)"
metrics:
  duration: "6 minutes"
  completed: "2026-05-23"
  tasks_completed: 3
  files_created: 9
  tests_added: 27
  tests_total: 326
---

# Phase 2 Plan 4: Wizard Step Widgets (Pre-Processing) Summary

**One-liner:** Four pre-processing wizard step widgets — StepType (output type), StepUpload (file drop + chooser), StepSheet (multi-sheet picker), StepColumns (column mapping auto/manual) — with TDD smoke tests, all green at 326 total passed.

## What Was Built

### Task 1 — steps package + StepType (commits `5b39183`, `7c6e77c`)

**`src/eleitorum/ui/steps/__init__.py`** — zero-byte package marker.

**`src/eleitorum/ui/steps/step_type.py`** — 111 lines:
- `class StepType(QWidget)` with `__init__(session: SessionModel, parent=None)`
- Vertical layout: `contentsMargins(24,24,24,24)`, `spacing(16)` per lg/md spec
- `QLabel(STEP_1_TITLE)` with `setObjectName("stepTitle")`
- `QHBoxLayout` with 24px spacing holding `self._card_caderno` and `self._card_elegiveis` (OptionCard instances)
- Both `.selected` signals connected to `_on_selection(key)` slot
- `_on_selection`: writes `session.output_type = key`, deselects other card
- `_restore_state()` in `__init__`: reads `session.output_type` and calls `set_selected(True)` on the matching card (back-navigation / Reiniciar restoration — WIZ-10)
- `is_complete() -> bool: return self._session.output_type is not None`

**`tests/unit/ui/test_step_type.py`** — 6 tests:

| Test | Result |
|------|--------|
| test_step_type_constructs_with_session | PASS |
| test_step_type_is_complete_false_initially | PASS |
| test_step_type_selecting_caderno_sets_session_output_type | PASS |
| test_step_type_selecting_caderno_deselects_elegiveis | PASS |
| test_step_type_is_complete_true_after_selection | PASS |
| test_step_type_preserves_existing_session_state | PASS |

### Task 2 — StepUpload + StepSheet (commits `b2b811c`, `be85d51`)

**`src/eleitorum/ui/steps/step_upload.py`** — 155 lines:
- `class StepUpload(QWidget)` with `_drop_zone` (DropZone), `_choose_btn` (QPushButton), `_file_name_label` (QLabel, empty), `_error_label` (QLabel, `setVisible(False)`)
- `DropZone.file_dropped` connected to `_on_file_received(path_str)`
- `_on_choose_clicked()`: calls `QFileDialog.getOpenFileName` with `OPEN_DIALOG_TITLE` and `OPEN_DIALOG_FILTER`
- `_on_file_received(path_str)`: extension check FIRST (`SUPPORTED_EXTENSIONS`) → on invalid: `_show_error(ERR_UNSUPPORTED_EXT.format(ext=...))`, return; on valid: hide error, set `session.source_path`, update file-name label, call `list_sheets(p)` → store `session.sheets`; on `EleitorumError`: show `err.message_pt`, reset `source_path`
- `is_complete() -> bool: return self._session.source_path is not None`

**`src/eleitorum/ui/steps/step_sheet.py`** — 131 lines:
- `class StepSheet(QWidget)` with `_list` (QListWidget, `SingleSelection` mode)
- `populate_from_session()`: clears list, iterates `session.sheets`; display text = `name + " " + SHEET_PICKER_ROWS_TEMPLATE.format(rows=N)` for non-empty, `name + SHEET_PICKER_EMPTY_SUFFIX` for empty
- `QListWidgetItem.setData(Qt.UserRole, info.name)` for raw-name storage
- `item.setForeground(QColor("#878787"))` for empty sheets
- `currentItemChanged` → `_on_selection_changed` → writes `session.sheet_name = current.data(Qt.UserRole)`
- `is_complete() -> bool: return self._session.sheet_name is not None`

**Test deviation — `isHidden()` instead of `isVisible()`:** In Qt, `isVisible()` depends on the full parent chain being shown. When testing inline error state on a widget not yet attached to a visible window, `isVisible()` returns `False` even after `setVisible(True)`. Used `isHidden()` (reflects the explicit flag) to avoid false negatives. This is a Rule 1 auto-fix: test correctness.

| Test File | Tests | Result |
|-----------|-------|--------|
| test_step_upload.py | 7 | PASSED |
| test_step_sheet.py | 6 | PASSED |

### Task 3 — StepColumns (commits `501ccd8`, `7290c73`)

**`src/eleitorum/ui/steps/step_columns.py`** — 275 lines:
- `class StepColumns(QWidget)` with `_mec_row` (QFrame), `_name_row` (QFrame), `_no_detection_label`, `_mec_combo` / `_name_combo` (QComboBox), `_mec_alterar_btn` / `_name_alterar_btn` (QPushButton), `_mec_value_label` / `_name_value_label` (QLabel)
- `populate_from_session()`: reads `session.pipeline_result.detection`; if absent or `detection_method == 'manual'` → `_enter_manual_mode()` (show no-detection label + combos); else → `_enter_auto_mode()` (show value labels + Alterar btns)
- `_enter_auto_mode()`: reads `mec_col_index` + `name_col_index` from detection dict, looks up `session.column_headers`, formats with `COL_MAPPING_HIGH` (synonym) or `COL_MAPPING_LOW` (other)
- DET-07: `self._mec_row.setVisible(self._session.output_type != "elegiveis")` in `populate_from_session()`
- Alterar slot: hides value label + button, shows QComboBox
- `QComboBox.currentIndexChanged` → `_on_combo_changed(key, idx)` → writes `session.column_map[key] = idx`
- `is_complete() -> bool: return True` (WIZ-04 spec: always enabled)

| Test | Result |
|------|--------|
| test_step_columns_constructs | PASS |
| test_step_columns_hides_mec_row_for_elegiveis | PASS |
| test_step_columns_shows_mec_row_for_caderno | PASS |
| test_step_columns_pre_populated_when_detection_succeeded | PASS |
| test_step_columns_manual_mode_when_no_detection | PASS |
| test_step_columns_alterar_opens_combobox | PASS |
| test_step_columns_writes_session_column_map_on_change | PASS |
| test_step_columns_is_complete_always_true_when_visible | PASS |

## Requested Output Confirmations

| Item | Status |
|------|--------|
| session.column_headers consumed as definitive field (not duck-typed) | CONFIRMED — `list[str] \| None` field added in plan 02-02 Task 1; step_columns reads `self._session.column_headers or []` |
| BTN_ALTERAR interaction matches UI spec inline-link styling | NOTED FOR PLAN 06 — currently a plain QPushButton; QSS inline-link visual treatment (underline, color, no border) deferred to plan 06 QSS refinement |
| is_complete() exists on every step | CONFIRMED — grep shows 4 definitions across 4 step files |
| Test count and pass status | 6 (step_type) + 7 (step_upload) + 6 (step_sheet) + 8 (step_columns) = 27 new tests, all PASSED; full suite 326 passed, 1 skipped |

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] isHidden() used in tests instead of isVisible() for unshown widgets**
- **Found during:** Task 2 GREEN phase
- **Issue:** `isVisible()` in Qt returns `False` for both "explicitly hidden" and "not yet shown via parent chain". Test `test_step_upload_unsupported_extension_shows_inline_error` checked `isVisible() is True` after `setVisible(True)` on a widget whose parent had not been `.show()`n. The assertion failed even though the label was correctly set visible.
- **Fix:** Changed affected assertions to `isHidden() is False` (error shown) and `isHidden() is True` (error cleared). `isHidden()` reflects only the explicit visibility flag, independent of parent chain state.
- **Files modified:** `tests/unit/ui/test_step_upload.py`
- **Commit:** included in `be85d51`

## Threat Model Verification

All T-02-04-* dispositions applied:

| Threat ID | Disposition | Mitigation Applied |
|-----------|-------------|-------------------|
| T-02-04-01 | mitigate | `SUPPORTED_EXTENSIONS` check before any I/O in `_on_file_received()` — pathlib normalizes path, extension extracted via `.suffix.lower()` |
| T-02-04-02 | mitigate | `err.message_pt` displayed inline — never a traceback; EleitorumError contract guarantees PT-PT prose |
| T-02-04-03 | mitigate | QComboBox items populated only from `session.column_headers`; `currentIndex()` is bounded by item count |
| T-02-04-04 | accept | Out of scope — accepted per plan |

## Threat Flags

None — no new security-relevant surface introduced beyond the planned scope.

## Known Stubs

None. All plan goals achieved.

- `BTN_ALTERAR` is a plain `QPushButton` — QSS inline-link visual treatment is intentionally deferred to plan 06 per PATTERNS.md note; the button is functional (click triggers combo reveal) and noted in the output section above.
- `session.column_headers` populated by `StepUpload._on_file_received()` as part of `list_sheets()` call — for single-sheet CSV files, headers are NOT pre-loaded here (list_sheets returns [] for CSV/TSV); StepColumns will show manual mode in that case. This is correct behavior per the plan spec.

## TDD Gate Compliance

All three tasks used TDD RED/GREEN cycle:

| Task | RED commit | GREEN commit |
|------|-----------|--------------|
| 1 (StepType) | `5b39183` | `7c6e77c` |
| 2 (StepUpload + StepSheet) | `b2b811c` | `be85d51` |
| 3 (StepColumns) | `501ccd8` | `7290c73` |

## Self-Check

| Check | Result |
|-------|--------|
| src/eleitorum/ui/steps/__init__.py exists | FOUND |
| src/eleitorum/ui/steps/step_type.py exists | FOUND |
| src/eleitorum/ui/steps/step_upload.py exists | FOUND |
| src/eleitorum/ui/steps/step_sheet.py exists | FOUND |
| src/eleitorum/ui/steps/step_columns.py exists | FOUND |
| tests/unit/ui/test_step_type.py exists | FOUND |
| tests/unit/ui/test_step_upload.py exists | FOUND |
| tests/unit/ui/test_step_sheet.py exists | FOUND |
| tests/unit/ui/test_step_columns.py exists | FOUND |
| Commit 5b39183 (RED task 1) | FOUND |
| Commit 7c6e77c (GREEN task 1) | FOUND |
| Commit b2b811c (RED task 2) | FOUND |
| Commit be85d51 (GREEN task 2) | FOUND |
| Commit 501ccd8 (RED task 3) | FOUND |
| Commit 7290c73 (GREEN task 3) | FOUND |
| is_complete() in all 4 step files | CONFIRMED |
| 27 step tests pass | PASSED |
| Full suite 326 passed, 1 skipped | PASSED |

## Self-Check: PASSED
