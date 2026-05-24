"""Step 3.5 — Processing screen with indeterminate→determinate progress bar (WIZ-11, PERF-02).

Displays an animated progress bar while the PipelineWorker runs in a background
QThread. Connects to worker signals (progress, finished, error, cancelled) and
routes the result to the appropriate wizard step via Signal emissions.

Security note (T-02-05-01): error messages received from the worker via
``error`` signal are passed through as-is without frame introspection. The
worker already strips tracebacks at emission time (T-02-01-02).

Requirements: WIZ-11 (background thread, cancel available), PERF-02 (UI thread
stays responsive — only progress bar + label updates happen on the main thread).
"""

from __future__ import annotations

import types

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from eleitorum.ui.session import SessionModel
from eleitorum.ui.strings import (
    CONFIRM_CANCEL,
    PROCESSING_LOADING,
    PROCESSING_PROGRESS,
    STEP_PROCESSING_TITLE,
)


class StepProcessing(QWidget):
    """Step 3.5: processing screen with progress bar and cancel button.

    Not shown as a numbered user step — it is the invisible processing phase
    between step 3 (column mapping) and step 4 (preview).

    Signals:
        route_to_preview(object): emitted with PipelineResult when
            worker.finished with result.success=True.
        route_to_error(object): emitted with PipelineResult (or SimpleNamespace)
            when worker.finished with result.success=False, or on worker.error.
        cancelled_by_user(): emitted when user confirms cancel (D-01 flow);
            wizard.py connects this to navigate back to STEP_COLUMNS.
    """

    route_to_preview = Signal(object)  # carries PipelineResult on success
    route_to_error = Signal(object)  # carries PipelineResult or error namespace
    cancelled_by_user = Signal()  # D-01: user confirmed cancel → back to step 3

    def __init__(self, session: SessionModel, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._session = session
        self._worker: object | None = None  # PipelineWorker — typed as object to avoid coupling
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # Step title
        title = QLabel(STEP_PROCESSING_TITLE)
        title.setObjectName("stepTitle")
        layout.addWidget(title)

        # Progress bar — starts indeterminate (0,0)
        self._bar = QProgressBar()
        self._bar.setRange(0, 0)
        self._bar.setTextVisible(False)
        layout.addWidget(self._bar)

        # Progress status label
        self._label = QLabel(PROCESSING_LOADING)
        layout.addWidget(self._label)

        layout.addStretch()

        # Cancel button row — centered
        cancel_row = QHBoxLayout()
        cancel_row.addStretch()
        self._cancel_btn = QPushButton("Cancelar")
        cancel_row.addWidget(self._cancel_btn)
        cancel_row.addStretch()
        layout.addLayout(cancel_row)

        self._cancel_btn.clicked.connect(self._on_cancel_clicked)

    # ------------------------------------------------------------------
    # Public API called by wizard.py
    # ------------------------------------------------------------------

    def start_processing(self, worker: object) -> None:
        """Connect to worker signals, then start the worker thread.

        Args:
            worker: a PipelineWorker (or duck-typed equivalent with the same
                    signals and start()/cancel() methods).
        """
        self._worker = worker
        worker.progress.connect(self.on_progress)  # type: ignore[attr-defined]
        worker.finished.connect(self._on_finished)  # type: ignore[attr-defined]
        worker.error.connect(self._on_error)  # type: ignore[attr-defined]
        worker.cancelled.connect(self._on_cancelled)  # type: ignore[attr-defined]
        self.on_processing_started()
        worker.start()  # type: ignore[attr-defined]

    def on_processing_started(self) -> None:
        """Reset to indeterminate state (called before worker.start())."""
        self._bar.setRange(0, 0)
        self._label.setText(PROCESSING_LOADING)

    def on_progress(self, current: int, total: int) -> None:
        """Slot connected to worker.progress(int, int).

        First call with total > 0 switches bar from indeterminate to determinate.
        Subsequent calls only update value and label.
        """
        if total > 0 and self._bar.maximum() == 0:
            # One-time switch to determinate
            self._bar.setRange(0, total)
        self._bar.setValue(current)
        self._label.setText(PROCESSING_PROGRESS.format(current=current, total=total))

    # ------------------------------------------------------------------
    # Private slots
    # ------------------------------------------------------------------

    def _on_cancel_clicked(self) -> None:
        """D-01: show confirmation dialog before calling worker.cancel()."""
        reply = QMessageBox.question(
            self,
            "",
            CONFIRM_CANCEL,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes and self._worker is not None:
            self._worker.cancel()  # type: ignore[attr-defined]

    def _on_finished(self, result: object) -> None:
        """Route completed result to preview or error based on success flag.

        Also writes result into session so downstream steps can read it.
        """
        self._session.pipeline_result = result
        if result.success:  # type: ignore[attr-defined]
            self.route_to_preview.emit(result)
        else:
            self.route_to_error.emit(result)

    def _on_error(self, message_pt: str) -> None:
        """Worker emitted an unexpected exception (not a validation failure).

        Build a minimal result-like namespace so route_to_error consumers receive
        a consistent object shape (success=False, no failures, error in log_entries).
        """
        err_result = types.SimpleNamespace(
            success=False,
            failures=[],
            error_log_path=None,
            log_entries=[message_pt],
        )
        self._session.pipeline_result = err_result
        self.route_to_error.emit(err_result)

    def _on_cancelled(self) -> None:
        """Worker signalled cancel completion — return wizard to step 3 (D-01)."""
        self.cancelled_by_user.emit()
