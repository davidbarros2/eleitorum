"""WizardController for EleitorUM — step navigation, indicator, pipeline wiring
(WIZ-06, WIZ-09, WIZ-10).

Manages QStackedWidget navigation through the 7-step wizard, updates the step
indicator QLabel, and wires the two-call pipeline architecture:
  1. Dry-run (output_path=None) on STEP_COLUMNS → STEP_PROCESSING → STEP_PREVIEW
  2. Write call after save-dialog on STEP_PREVIEW → STEP_PROCESSING → STEP_DONE

WIZ-06 save-dialog flow: enforces .csv extension, rejects output==input path
with inline PT-PT QMessageBox.warning and re-opens the dialog, persists
app/last_directory to QSettings after a successful selection.

WIZ-09: step indicator updated on every navigation; "Passo N de 5" on standard
path, "Passo N de 6" on multi-sheet path.

WIZ-10: reiniciar() mutates SessionModel fields to None IN PLACE — never
reassigns self._session (step widgets hold the same object reference).

Security note (T-02-06-01): output path collision (output == input) detected
inline in _on_preview_save_clicked(); QFileDialog returns a path, not raw user
input, so path traversal is handled by the OS-native dialog.
"""

from __future__ import annotations

import pathlib

from PySide6.QtCore import QObject, QSettings, Signal
from PySide6.QtWidgets import (
    QFileDialog,
    QLabel,
    QMessageBox,
    QStackedWidget,
)

from eleitorum.ui.session import SessionModel
from eleitorum.ui.steps.step_columns import StepColumns
from eleitorum.ui.steps.step_done import StepDone
from eleitorum.ui.steps.step_preview import StepPreview
from eleitorum.ui.steps.step_processing import StepProcessing
from eleitorum.ui.steps.step_sheet import StepSheet
from eleitorum.ui.steps.step_type import StepType
from eleitorum.ui.steps.step_upload import StepUpload
from eleitorum.ui.strings import (
    BTN_GRAVAR,
    BTN_PROXIMO,
    ERR_OUTPUT_SAME_AS_INPUT,
    SAVE_DIALOG_FILTER,
    SAVE_DIALOG_TITLE,
    STEP_INDICATOR,
)
from eleitorum.ui.widgets.navbar import NavBar
from eleitorum.ui.worker import PipelineWorker


class WizardController(QObject):
    """Manages step navigation for the EleitorUM wizard (WIZ-06, WIZ-09, WIZ-10).

    Class constants map semantic step names to QStackedWidget indices.
    STEP_PROCESSING (index 4) is not a user-visible numbered step.

    Signals:
        quit_requested(): emitted when the user clicks "Sair" on the success
            page of StepDone; MainWindow connects this to QApplication.quit().
    """

    # Stack indices — sequential, matches insertion order in __init__
    STEP_TYPE: int = 0
    STEP_UPLOAD: int = 1
    STEP_SHEET: int = 2  # conditional; skipped on single-sheet files
    STEP_COLUMNS: int = 3
    STEP_PROCESSING: int = 4  # not a user-visible numbered step
    STEP_PREVIEW: int = 5
    STEP_DONE: int = 6

    quit_requested = Signal()  # MainWindow connects to QApplication.quit

    def __init__(
        self,
        session: SessionModel,
        stack: QStackedWidget,
        navbar: NavBar,
        step_label: QLabel,
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)

        self._session = session
        self._stack = stack
        self._navbar = navbar
        self._step_label = step_label
        self._settings = QSettings()

        # Track whether the multi-sheet path was taken (affects step indicator)
        self._multi_sheet_path: bool = False

        # Build and insert all 7 step widgets
        self._step_type = StepType(session)
        self._step_upload = StepUpload(session)
        self._step_sheet = StepSheet(session)
        self._step_columns = StepColumns(session)
        self._step_processing = StepProcessing(session)
        self._step_preview = StepPreview(session)
        self._step_done = StepDone(session)

        # Insert in index order — must match STEP_* constants
        stack.insertWidget(self.STEP_TYPE, self._step_type)
        stack.insertWidget(self.STEP_UPLOAD, self._step_upload)
        stack.insertWidget(self.STEP_SHEET, self._step_sheet)
        stack.insertWidget(self.STEP_COLUMNS, self._step_columns)
        stack.insertWidget(self.STEP_PROCESSING, self._step_processing)
        stack.insertWidget(self.STEP_PREVIEW, self._step_preview)
        stack.insertWidget(self.STEP_DONE, self._step_done)

        # Connect NavBar signals
        navbar.proximo_clicked.connect(self.on_proximo)
        navbar.anterior_clicked.connect(self.on_anterior)
        navbar.cancelar_clicked.connect(self.on_cancelar)

        # Reactively update NavBar when a step's completion state changes
        self._step_type.completion_changed.connect(self._update_navbar_for_current_step)
        self._step_upload.completion_changed.connect(self._update_navbar_for_current_step)
        self._step_sheet.completion_changed.connect(self._update_navbar_for_current_step)

        # Connect step_processing routing signals
        self._step_processing.route_to_preview.connect(self._on_processing_to_preview)
        self._step_processing.route_to_error.connect(self._on_processing_to_error)
        self._step_processing.cancelled_by_user.connect(self._on_processing_cancelled)

        # Connect step_done action signals
        self._step_done.restart_clicked.connect(self.reiniciar)
        self._step_done.quit_clicked.connect(self.quit_requested)

        # Initial navbar + indicator state
        stack.setCurrentIndex(self.STEP_TYPE)
        self._update_navbar_for_current_step()
        self._update_step_indicator()

    # ------------------------------------------------------------------
    # NavBar slots
    # ------------------------------------------------------------------

    def on_proximo(self) -> None:
        """Handle Próximo button click for the current step."""
        current = self._stack.currentIndex()

        if current == self.STEP_COLUMNS:
            # Trigger dry-run worker (output_path=None — never writes)
            self._start_dry_run()

        elif current == self.STEP_PREVIEW:
            # Save dialog → second worker call with confirmed output path
            self._on_preview_save_clicked()

        else:
            # Simple navigation: advance to next step (may skip STEP_SHEET)
            self._advance()

    def on_anterior(self) -> None:
        """Handle Anterior button click — navigate to previous step."""
        current = self._stack.currentIndex()

        if current in (self.STEP_TYPE, self.STEP_PROCESSING):
            return  # no backward navigation from these states

        previous = self._compute_previous(current)
        self._stack.setCurrentIndex(previous)
        self._update_navbar_for_current_step()
        self._update_step_indicator()

    def on_cancelar(self) -> None:
        """Cancelar is only relevant on STEP_PROCESSING (handled by the step).

        On other steps Cancelar is hidden; this slot is a no-op for robustness.
        """

    # ------------------------------------------------------------------
    # Reiniciar (WIZ-10)
    # ------------------------------------------------------------------

    def reiniciar(self) -> None:
        """Reset wizard to step 1 by mutating session fields in place (WIZ-10).

        CRITICAL: mutates self._session fields individually — never replaces the
        self._session reference. Step widgets hold the same SessionModel instance.
        """
        self._session.output_type = None
        self._session.source_path = None
        self._session.sheet_name = None
        self._session.column_map = None
        self._session.pipeline_result = None
        self._session.output_path = None
        self._session.sheets = None
        self._session.column_headers = None

        self._multi_sheet_path = False
        self._stack.setCurrentIndex(self.STEP_TYPE)
        self._update_navbar_for_current_step()
        self._update_step_indicator()

    # ------------------------------------------------------------------
    # Private navigation helpers
    # ------------------------------------------------------------------

    def _advance(self) -> None:
        """Navigate forward one step, skipping STEP_SHEET when appropriate."""
        current = self._stack.currentIndex()
        next_idx = self._compute_next(current)
        self._stack.setCurrentIndex(next_idx)
        self._update_navbar_for_current_step()
        self._update_step_indicator()

    def _compute_next(self, current: int) -> int:
        """Return the next stack index from ``current``.

        Skips STEP_SHEET when the session has 0 or 1 sheet (single-sheet files,
        CSV/TSV). Also marks _multi_sheet_path when STEP_SHEET is visited.
        """
        if current == self.STEP_TYPE:
            return self.STEP_UPLOAD

        if current == self.STEP_UPLOAD:
            # Populate sheet list before deciding to show it
            if self._session.sheets and len(self._session.sheets) > 1:
                self._multi_sheet_path = True
                self._step_sheet.populate_from_session()
                return self.STEP_SHEET
            # Single-sheet or non-multi: skip sheet step
            self._multi_sheet_path = False
            self._step_columns.populate_from_session()
            return self.STEP_COLUMNS

        if current == self.STEP_SHEET:
            self._step_columns.populate_from_session()
            return self.STEP_COLUMNS

        if current == self.STEP_PROCESSING:
            return self.STEP_PREVIEW  # handled via signal; direct call unused

        if current == self.STEP_PREVIEW:
            return self.STEP_DONE  # handled via _on_preview_save_clicked

        # Default: sequential +1 (STEP_COLUMNS → ... handled separately)
        return min(current + 1, self.STEP_DONE)

    def _compute_previous(self, current: int) -> int:
        """Return the previous stack index from ``current``.

        Skips STEP_PROCESSING (never a back target) and skips STEP_SHEET when
        the multi-sheet path was not taken.
        """
        if current == self.STEP_UPLOAD:
            return self.STEP_TYPE

        if current == self.STEP_SHEET:
            return self.STEP_UPLOAD

        if current == self.STEP_COLUMNS:
            if self._multi_sheet_path:
                return self.STEP_SHEET
            return self.STEP_UPLOAD

        if current == self.STEP_PREVIEW:
            return self.STEP_COLUMNS

        if current == self.STEP_DONE:
            return self.STEP_PREVIEW

        return max(current - 1, self.STEP_TYPE)

    # ------------------------------------------------------------------
    # Pipeline wiring
    # ------------------------------------------------------------------

    def _start_dry_run(self) -> None:
        """Construct a dry-run PipelineWorker (output_path=None) and start it."""
        source = self._session.source_path
        output_type = self._session.output_type or "caderno"
        worker = PipelineWorker(
            source=source,  # type: ignore[arg-type]
            output_type=output_type,
            output_path=None,  # dry-run — never writes
        )
        self._stack.setCurrentIndex(self.STEP_PROCESSING)
        self._update_navbar_for_current_step()
        self._update_step_indicator()
        self._step_processing.start_processing(worker)

    def _on_preview_save_clicked(self) -> None:
        """WIZ-06 save-dialog flow invoked when Próximo is clicked on STEP_PREVIEW.

        - Reads last_directory from QSettings for dialog starting directory.
        - Suggests filename: ``{stem}_{output_type}.csv``.
        - Enforces .csv extension (appends if missing).
        - Rejects output == input path with inline PT-PT warning, re-opens dialog.
        - On accepted path: stores session.output_path, persists last_directory,
          starts second PipelineWorker with the confirmed output path.
        """
        last_dir: str = self._settings.value("app/last_directory", "", type=str)  # type: ignore[assignment]
        source_path = self._session.source_path
        output_type = self._session.output_type or "caderno"
        suggested_name = f"{source_path.stem}_{output_type}.csv" if source_path else "saida.csv"
        start_path = str(pathlib.Path(last_dir) / suggested_name) if last_dir else suggested_name

        while True:
            chosen, _ = QFileDialog.getSaveFileName(
                self._stack,
                SAVE_DIALOG_TITLE,
                start_path,
                SAVE_DIALOG_FILTER,
            )

            if not chosen:
                # User cancelled — do nothing, stay on STEP_PREVIEW
                return

            # WIZ-06: enforce .csv extension
            if not chosen.lower().endswith(".csv"):
                chosen = chosen + ".csv"

            chosen_path = pathlib.Path(chosen)

            # T-02-06-01: reject output == input (VAL-08)
            if source_path is not None and chosen_path == source_path:
                QMessageBox.warning(
                    self._stack,
                    "",
                    ERR_OUTPUT_SAME_AS_INPUT,
                )
                # Re-open dialog with same start path
                start_path = str(chosen_path)
                continue

            # Accepted path — persist last directory and start write worker
            self._settings.setValue("app/last_directory", str(chosen_path.parent))
            self._session.output_path = chosen_path

            worker = PipelineWorker(
                source=source_path,  # type: ignore[arg-type]
                output_type=output_type,
                output_path=chosen_path,
            )
            self._stack.setCurrentIndex(self.STEP_PROCESSING)
            self._update_navbar_for_current_step()
            self._update_step_indicator()
            self._step_processing.start_processing(worker)
            return

    # ------------------------------------------------------------------
    # Processing signal handlers
    # ------------------------------------------------------------------

    def _on_processing_to_preview(self, result: object) -> None:
        """Route successful dry-run result to STEP_PREVIEW."""
        self._session.pipeline_result = result
        self._step_preview.populate_from_session()
        self._stack.setCurrentIndex(self.STEP_PREVIEW)
        self._update_navbar_for_current_step()
        self._update_step_indicator()

    def _on_processing_to_error(self, result: object) -> None:
        """Route failed result (validation or unexpected error) to STEP_DONE error."""
        self._step_done.show_error(result)
        self._stack.setCurrentIndex(self.STEP_DONE)
        self._update_navbar_for_current_step()
        self._update_step_indicator()

    def _on_processing_cancelled(self) -> None:
        """D-01: user confirmed cancel — return to STEP_COLUMNS."""
        self._stack.setCurrentIndex(self.STEP_COLUMNS)
        self._update_navbar_for_current_step()
        self._update_step_indicator()

    # ------------------------------------------------------------------
    # Step indicator (WIZ-09)
    # ------------------------------------------------------------------

    def _step_display_number(self) -> tuple[int, int]:
        """Return (n, total) for the current step indicator label.

        STEP_PROCESSING is not a user-visible step — it does not increment n.
        Standard path: 5 total steps.
        Multi-sheet path: 6 total steps (STEP_SHEET is step 3).
        """
        total = 6 if self._multi_sheet_path else 5
        idx = self._stack.currentIndex()

        user_step: dict[int, int] = {
            self.STEP_TYPE: 1,
            self.STEP_UPLOAD: 2,
            self.STEP_SHEET: 3 if self._multi_sheet_path else 2,  # only shown on multi-sheet path
            self.STEP_COLUMNS: 4 if self._multi_sheet_path else 3,
            self.STEP_PROCESSING: 4 if self._multi_sheet_path else 3,  # same as COLUMNS
            self.STEP_PREVIEW: 5 if self._multi_sheet_path else 4,
            self.STEP_DONE: 6 if self._multi_sheet_path else 5,
        }
        n = user_step.get(idx, 1)
        return (n, total)

    def _update_step_indicator(self) -> None:
        """Refresh the step indicator QLabel text."""
        n, total = self._step_display_number()
        self._step_label.setText(STEP_INDICATOR.format(n=n, total=total))

    # ------------------------------------------------------------------
    # NavBar state management
    # ------------------------------------------------------------------

    def _update_navbar_for_current_step(self) -> None:
        """Update NavBar button states and Próximo label for the current step."""
        current = self._stack.currentIndex()

        # Anterior enabled unless we're on step 1 or the processing screen
        anterior_enabled = current not in (self.STEP_TYPE, self.STEP_PROCESSING, self.STEP_DONE)
        self._navbar.set_anterior_enabled(anterior_enabled)

        # Próximo label: "Escolher destino e gravar" on preview, else "Próximo"
        if current == self.STEP_PREVIEW:
            self._navbar.set_proximo_text(BTN_GRAVAR)
        else:
            self._navbar.set_proximo_text(BTN_PROXIMO)

        # Próximo enabled based on step completion (or always True for some steps)
        if current == self.STEP_PROCESSING or current == self.STEP_DONE:
            self._navbar.set_proximo_enabled(False)
        else:
            # Poll is_complete() on current step widget
            current_widget = self._stack.currentWidget()
            if hasattr(current_widget, "is_complete"):
                self._navbar.set_proximo_enabled(current_widget.is_complete())
            else:
                self._navbar.set_proximo_enabled(True)

        # Cancelar only visible on STEP_PROCESSING (D-01)
        self._navbar.set_cancel_visible(current == self.STEP_PROCESSING)
