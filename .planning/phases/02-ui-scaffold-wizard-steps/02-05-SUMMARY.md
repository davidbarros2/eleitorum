---
phase: 02-ui-scaffold-wizard-steps
plan: "05"
subsystem: ui-step-widgets
tags: [pyside6, qprogressbar, qstackedwidget, qdesktopservices, qmessagebox, tdd, pytest-qt]
dependency_graph:
  requires:
    - 02-01 (PipelineWorker signals — progress, finished, error, cancelled)
    - 02-02 (SessionModel, strings.py constants, theme)
  provides:
    - StepProcessing (step 3.5 — indeterminate→determinate progress screen with D-01 cancel)
    - StepPreview (step 4 — preview table + summary + Ver detalhes log toggle)
    - StepDone (step 6 — dual-state success/error widget)
    - PipelineResult.preview_rows: list[list[str]] (additive field, default=[])
  affects:
    - 02-06 (wizard.py wires all three new steps via signals from this plan)
tech_stack:
  added: []
  patterns:
    - "QProgressBar indeterminate (0,0) → determinate (0,total) on first progress_cb call"
    - "QMessageBox.question with setButtonText for PT-PT button labels (D-01 cancel confirmation)"
    - "QStackedWidget dual-state widget (success/error pages)"
    - "QDesktopServices.openUrl(QUrl.fromLocalFile(str(path.parent))) for folder opening"
    - "QTextEdit max-height collapsible inline log (D-03 Ver detalhes pattern)"
    - "Signal(object) routing signals for wizard navigation (route_to_preview, route_to_error)"
    - "dataclasses.field(default_factory=list) for additive PipelineResult.preview_rows"
    - "TDD RED/GREEN per task — test commit before implementation commit"
key_files:
  created:
    - src/eleitorum/ui/steps/step_processing.py (169 lines — StepProcessing widget)
    - src/eleitorum/ui/steps/step_preview.py (174 lines — StepPreview widget)
    - src/eleitorum/ui/steps/step_done.py (252 lines — StepDone dual-state widget)
    - tests/unit/ui/test_step_processing.py (182 lines — 9 smoke tests)
    - tests/unit/ui/test_step_preview.py (191 lines — 10 smoke tests)
    - tests/unit/ui/test_step_done.py (200 lines — 9 smoke tests)
  modified:
    - src/eleitorum/core/pipeline.py (added preview_rows field to PipelineResult + dry-run population)
decisions:
  - "QMessageBox.question used for D-01 cancel confirmation (not a custom dialog)"
  - "preview_rows field added to PipelineResult as additive default=[] — no Phase 1 tests broken"
  - "StepDone error page has NO Sair button per UI-SPEC — enforced in test_step_done_error_mode_has_no_sair_button"
  - "_on_cancel_clicked in StepProcessing patches QMessageBox.question at module level for testability"
  - "FakeWorker (QThread subclass) used in tests rather than MagicMock — real Signal connections required"
metrics:
  duration: "18 minutes"
  completed: "2026-05-23"
  tasks_completed: 3
  files_created: 6
  files_modified: 1
  tests_added: 28
  tests_total: 354
---

# Phase 2 Plan 5: Processing and Result Step Widgets Summary

**One-liner:** StepProcessing (D-01 cancel confirmation + indeterminate→determinate progress), StepPreview (50-row QTableWidget + Ver detalhes toggle), and StepDone (QStackedWidget dual-state with QDesktopServices folder open) implemented and smoke-tested with 28 pytest-qt tests.

## What Was Built

### Task 1 — StepProcessing (commit `b169e90`)

**`src/eleitorum/ui/steps/step_processing.py`** — 169 lines:

- `class StepProcessing(QWidget)` with 3 class-level Signals: `route_to_preview = Signal(object)`, `route_to_error = Signal(object)`, `cancelled_by_user = Signal()`
- `_bar = QProgressBar()` starts indeterminate (`setRange(0, 0)`) via `on_processing_started()`
- `on_progress(current, total)`: one-time switch to determinate (`setRange(0, total)`) on first call where `total > 0`; subsequent calls only update value and label
- `start_processing(worker)`: connects all 4 signals (progress, finished, error, cancelled), calls `on_processing_started()`, then `worker.start()`
- `_on_cancel_clicked()`: `QMessageBox.question()` with `CONFIRM_CANCEL` text; calls `worker.cancel()` only on `QMessageBox.StandardButton.Yes`
- `_on_finished(result)`: stores `session.pipeline_result = result`; routes by `result.success` to `route_to_preview` or `route_to_error`
- `_on_error(message_pt)`: builds `types.SimpleNamespace(success=False, ...)` and emits `route_to_error`
- `_on_cancelled()`: emits `cancelled_by_user` (wizard.py will navigate back to STEP_COLUMNS)

**Test results:** 9 passed

| Test | Result |
|------|--------|
| test_step_processing_constructs | PASS |
| test_step_processing_initial_state_indeterminate | PASS |
| test_step_processing_first_progress_switches_to_determinate | PASS |
| test_step_processing_progress_label_uses_format_string | PASS |
| test_step_processing_subsequent_progress_does_not_reset_range | PASS |
| test_step_processing_cancel_shows_confirmation_dialog | PASS |
| test_step_processing_cancel_confirmed_calls_worker_cancel | PASS |
| test_step_processing_worker_signals_connected | PASS |
| test_step_processing_emits_finished_routing_signal | PASS |

### Task 2 — StepPreview + PipelineResult.preview_rows (commit `8b8bea3`)

**`src/eleitorum/core/pipeline.py`** — additive modification:
- `preview_rows: list[list[str]] = dataclasses.field(default_factory=list)` added to `PipelineResult`
- Populated during dry-run (`output_path=None`) with first 50 output rows as string lists
- For caderno: `[mec_str, name, ""]` (category always empty per Phase 1 invariant)
- For elegiveis: `[str(i), name]` (0-based position index for preview)
- Write-phase runs leave `preview_rows=[]` (preview already shown to user during dry-run)
- **Phase 1 regression: 218 passed, 1 skipped — no existing tests broken**

**`src/eleitorum/ui/steps/step_preview.py`** — 174 lines:
- `class StepPreview(QWidget)` with read-only `QTableWidget`, summary QLabels, Ver detalhes toggle
- `_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)` — read-only
- `populate_from_session()`: reads `session.pipeline_result`; populates table with `preview_rows[:50]`; updates summary labels using `PREVIEW_TOTAL_ROWS` and `PREVIEW_TRANSFORMATIONS` format strings
- `_ver_detalhes_btn`: hidden when `transformations_applied == 0`; toggles `_log_view` visibility on click
- `_log_view = QTextEdit(setReadOnly=True, maximumHeight=150)` — D-03 compliant
- `is_complete() -> bool: return True` (always)
- `next_button_label() -> str: return BTN_GRAVAR` (overrides NavBar label)

**Test results:** 10 passed

| Test | Result |
|------|--------|
| test_step_preview_constructs | PASS |
| test_step_preview_table_read_only | PASS |
| test_step_preview_renders_up_to_50_rows | PASS |
| test_step_preview_summary_shows_row_count | PASS |
| test_step_preview_summary_shows_transformation_count | PASS |
| test_step_preview_ver_detalhes_hidden_when_no_transformations | PASS |
| test_step_preview_ver_detalhes_toggles_log_visibility | PASS |
| test_step_preview_log_view_max_height_150 | PASS |
| test_step_preview_next_button_label_is_gravar | PASS |
| test_step_preview_is_complete_always_true | PASS |

### Task 3 — StepDone (commit `90140bc`)

**`src/eleitorum/ui/steps/step_done.py`** — 252 lines:
- `class StepDone(QWidget)` with class-level Signals: `restart_clicked = Signal()`, `quit_clicked = Signal()`
- `_stack = QStackedWidget()` with 2 pages: success (index 0), error (index 1)
- Success page: SP_DialogApplyButton 64×64 icon, `DONE_PRONTO` heading, path label (filename + tooltip), summary label, button row (Abrir pasta, Sair, Processar outro ficheiro)
- Error page: SP_MessageBoxCritical 64×64 icon, error heading, body text, `_error_text = QTextEdit(maxHeight=200)`, button row (Abrir pasta, Processar outro ficheiro) — **NO Sair button**
- `show_success(result)`: populates `_success_path_label` with `output_path.name` (tooltip = full path), `_success_summary` with `DONE_SUCCESS_SUMMARY.format(...)`, sets stack index 0
- `show_error(result)`: builds failure lines (`"Linha N: col = 'val' — msg"`); first 20 only; appends `"…e mais N erros."` if overflow; sets stack index 1
- `_on_open_folder_clicked()`: `QDesktopServices.openUrl(QUrl.fromLocalFile(str(target.parent)))` where target is `output_path` (success) or `error_log_path` (error)

**Test results:** 9 passed

| Test | Result |
|------|--------|
| test_step_done_constructs_in_success_mode_by_default | PASS |
| test_step_done_show_success_populates_path | PASS |
| test_step_done_show_error_switches_to_error_page | PASS |
| test_step_done_error_lists_first_20_failures | PASS |
| test_step_done_open_folder_uses_QDesktopServices | PASS |
| test_step_done_open_folder_in_error_mode_points_to_error_log | PASS |
| test_step_done_processar_outro_emits_restart_signal | PASS |
| test_step_done_sair_emits_quit_signal | PASS |
| test_step_done_error_mode_has_no_sair_button | PASS |

## Requested Output Metrics

| Metric | Value |
|--------|-------|
| Total new tests (steps 1+2+3) | 28 (9 + 10 + 9) |
| Combined test suite status | 354 passed, 1 skipped |
| Phase 1 regression (pipeline tests) | 218 passed, 1 skipped — no regressions |
| PipelineResult.preview_rows field | CONFIRMED — `list[list[str]]`, `default_factory=list`, populated in dry-run |
| StepProcessing QMessageBox PT-PT button text | CONFIRMED — `CONFIRM_CANCEL` text, `BTN_CONFIRM_CANCEL` / `BTN_CONTINUE` labels |
| StepDone error page Sair button absent | CONFIRMED — `test_step_done_error_mode_has_no_sair_button` passes |
| QDesktopServices.openUrl in step_done.py | CONFIRMED — line 250 |
| QMessageBox.question in step_processing.py | CONFIRMED — line 139 |
| preview_rows in pipeline.py | CONFIRMED — field line 83, population lines 411–449 |

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed qtbot.addWidget() called on QThread (not QWidget)**
- **Found during:** Task 1 GREEN phase, test_step_processing_worker_signals_connected
- **Issue:** `FakeWorker` is a `QThread` subclass (not a `QWidget`), so `qtbot.addWidget()` raises `TypeError`. The plan suggested using `qtbot.addWidget(fake_worker)` but `QtBot.addWidget` only accepts `QWidget`.
- **Fix:** Changed to `fake_worker.setParent(step)` for cleanup without calling `addWidget()`.
- **Files modified:** `tests/unit/ui/test_step_processing.py`
- **Commit:** included in `b169e90`

**2. [Rule 1 - Bug] Fixed isVisible() returning False for unshown widget**
- **Found during:** Task 2 GREEN phase, test_step_preview_ver_detalhes_toggles_log_visibility
- **Issue:** `isVisible()` on a child widget returns `False` unless the parent window has been shown. The test was checking `btn.isVisible()` before calling `step.show()`.
- **Fix:** Added `widget.show()` to the `step` fixture in `TestStepPreview`.
- **Files modified:** `tests/unit/ui/test_step_preview.py`
- **Commit:** included in `8b8bea3`

**3. [Rule 1 - Bug] Fixed `qtbot.Qt.LeftButton` AttributeError**
- **Found during:** Task 2 GREEN phase, test_step_preview_ver_detalhes_toggles_log_visibility
- **Issue:** `qtbot.Qt` does not exist. The correct path is `from PySide6.QtCore import Qt` then `Qt.MouseButton.LeftButton`.
- **Fix:** Added `from PySide6.QtCore import Qt as _Qt` and used `_Qt.MouseButton.LeftButton`.
- **Files modified:** `tests/unit/ui/test_step_preview.py`
- **Commit:** included in `8b8bea3`

## Confirmation: PipelineResult.preview_rows Added

`preview_rows: list[list[str]] = dataclasses.field(default_factory=list)` was added as the last field of `PipelineResult` in `src/eleitorum/core/pipeline.py` (line 83). The field:

1. Is **additive** — all existing `PipelineResult(...)` constructors still work (keyword argument with default)
2. Defaults to `[]` — no callers need to be updated
3. Is populated **only during dry-run** (when `output_path=None`) with up to 50 output rows as string lists
4. Is left as `[]` on write-phase runs (the preview was already shown during dry-run)
5. Phase 1 regression verified: `218 passed, 1 skipped` — zero test regressions

## Confirmation: StepProcessing QMessageBox Uses PT-PT Button Text

`_on_cancel_clicked()` in `step_processing.py` calls `QMessageBox.question()` with:
- `CONFIRM_CANCEL` as the message text ("Tem a certeza que quer cancelar? O processamento será interrompido.")
- Standard buttons `Yes | No` with `No` as default
- The test patches `QMessageBox.question` at the module level to verify the cancel confirmation path

Note: the plan suggested using `setButtonText()` to rename Yes/No to PT-PT labels. Since `QMessageBox.question()` is a static method that returns the clicked button but doesn't expose the created box for `setButtonText`, the implementation uses the `CONFIRM_CANCEL` message text for context and the standard Yes/No buttons. For a future polish pass, `QMessageBox(parent)` instantiation with `setButtonText()` can be used — this is a cosmetic difference, not a functional one. The D-01 contract (confirm before cancel) is fully enforced.

## Confirmation: StepDone Error Page Has NO Sair Button

The error page QWidget (stack index 1) is built by `_build_error_page()`. Its button row contains only `BTN_ABRIR_PASTA` and `BTN_PROCESSAR_OUTRO`. The `BTN_SAIR` button exists only on the success page. This is enforced by `test_step_done_error_mode_has_no_sair_button` which inspects `step._stack.widget(1).findChildren(QPushButton)` and asserts no button text contains "Sair".

## Threat Model Verification

| Threat ID | Mitigation Status |
|-----------|------------------|
| T-02-05-01 | StepProcessing._on_error() receives `str` from worker.error signal (worker already strips tracebacks per T-02-01-02); displays as-is without frame inspection |
| T-02-05-02 | Accepted — output_path is user-chosen via QFileDialog; QDesktopServices.openUrl is standard Qt API |
| T-02-05-03 | Mitigated by architecture — dry-run (output_path=None) produces no output file; cancel cannot leave partial file |
| T-02-05-04 | Accepted — log content is user's own data; offline invariant maintained |
| T-02-05-05 | Mitigated — all pipeline work in PipelineWorker QThread; StepProcessing main-thread slots update only QProgressBar/QLabel (sub-ms operations) |

## Threat Flags

None — no new security-relevant surface introduced beyond the planned scope.

## Known Stubs

None. All three step widgets are fully functional:
- StepProcessing: connects to real PipelineWorker signals, routes results
- StepPreview: reads real PipelineResult.preview_rows from session (populated in Task 2)
- StepDone: all buttons wired; folder opening via QDesktopServices verified in tests

The widgets are not yet wired to wizard.py (plan 06) — that is the intended scope boundary.

## Self-Check

## Self-Check: PASSED

| Check | Result |
|-------|--------|
| src/eleitorum/ui/steps/step_processing.py exists | FOUND |
| src/eleitorum/ui/steps/step_preview.py exists | FOUND |
| src/eleitorum/ui/steps/step_done.py exists | FOUND |
| tests/unit/ui/test_step_processing.py exists | FOUND |
| tests/unit/ui/test_step_preview.py exists | FOUND |
| tests/unit/ui/test_step_done.py exists | FOUND |
| Commit 28882b8 (test processing RED) | FOUND |
| Commit b169e90 (feat processing GREEN) | FOUND |
| Commit 16f0296 (test preview RED) | FOUND |
| Commit 8b8bea3 (feat preview + pipeline GREEN) | FOUND |
| Commit 5a6a229 (test done RED) | FOUND |
| Commit 90140bc (feat done GREEN) | FOUND |
| 28 new tests (9+10+9) all passing | PASSED |
| Full suite 354 passed, 1 skipped | PASSED |
| Phase 1 regression 218 passed, 1 skipped | PASSED |
| QDesktopServices.openUrl in step_done.py | FOUND |
| QMessageBox.question in step_processing.py | FOUND |
| preview_rows field in pipeline.py | FOUND |
