"""Tests for StepProcessing wizard step widget (WIZ-11, PERF-02, D-01).

Verifies indeterminate→determinate QProgressBar transition, cancel confirmation
dialog per D-01 spec, worker signal connections, and routing signals.

All test data is synthetic (no real personal data per CLAUDE.md privacy constraint).
"""

from __future__ import annotations

import types
from unittest.mock import MagicMock, patch

import pytest
from PySide6.QtWidgets import QApplication, QMessageBox, QProgressBar

from eleitorum.ui.session import SessionModel
from eleitorum.ui.strings import (
    PROCESSING_PROGRESS,
    STEP_PROCESSING_TITLE,
)
from eleitorum.ui.worker import PipelineWorker


class TestStepProcessing:
    """Tests for StepProcessing (step 3.5 — processing screen)."""

    @pytest.fixture()
    def session(self) -> SessionModel:
        return SessionModel()

    @pytest.fixture()
    def step(self, session: SessionModel, qtbot):
        from eleitorum.ui.steps.step_processing import StepProcessing

        widget = StepProcessing(session)
        qtbot.addWidget(widget)
        return widget

    def test_step_processing_constructs(self, step) -> None:
        """StepProcessing builds with title, progress bar, label and cancel button."""
        from PySide6.QtWidgets import QLabel, QPushButton

        # Title label with correct objectName
        title = step.findChild(QLabel, "stepTitle")
        assert title is not None, "stepTitle QLabel not found"
        assert title.text() == STEP_PROCESSING_TITLE

        # Progress bar
        assert hasattr(step, "_bar"), "_bar attribute missing"
        assert isinstance(step._bar, QProgressBar)

        # Progress label
        assert hasattr(step, "_label"), "_label attribute missing"
        assert isinstance(step._label, QLabel)

        # Cancel button
        assert hasattr(step, "_cancel_btn"), "_cancel_btn attribute missing"
        assert isinstance(step._cancel_btn, QPushButton)

    def test_step_processing_initial_state_indeterminate(self, step) -> None:
        """After on_processing_started(), progress bar is indeterminate (0,0 range)."""
        step.on_processing_started()
        assert step._bar.minimum() == 0
        assert step._bar.maximum() == 0

    def test_step_processing_first_progress_switches_to_determinate(self, step) -> None:
        """First on_progress(50, 1000) switches bar to determinate (max=1000, value=50)."""
        step.on_processing_started()
        step.on_progress(50, 1000)
        assert step._bar.maximum() == 1000
        assert step._bar.value() == 50

    def test_step_processing_progress_label_uses_format_string(self, step) -> None:
        """After on_progress(50, 1000), label text matches PROCESSING_PROGRESS format."""
        step.on_processing_started()
        step.on_progress(50, 1000)
        expected = PROCESSING_PROGRESS.format(current=50, total=1000)
        assert step._label.text() == expected

    def test_step_processing_subsequent_progress_does_not_reset_range(self, step) -> None:
        """After first progress call, subsequent calls do NOT reset max to 0."""
        step.on_processing_started()
        step.on_progress(50, 1000)
        assert step._bar.maximum() == 1000
        step.on_progress(100, 1000)
        assert step._bar.maximum() == 1000, "Max was reset to 0 — determinate state lost"

    def test_step_processing_cancel_shows_confirmation_dialog(self, step, qtbot) -> None:
        """Clicking cancel with QMessageBox.No does NOT call worker.cancel()."""
        worker_mock = MagicMock(spec=PipelineWorker)
        step._worker = worker_mock

        with patch(
            "eleitorum.ui.steps.step_processing.QMessageBox.question",
            return_value=QMessageBox.StandardButton.No,
        ):
            step._on_cancel_clicked()

        worker_mock.cancel.assert_not_called()

    def test_step_processing_cancel_confirmed_calls_worker_cancel(self, step, qtbot) -> None:
        """Clicking cancel with QMessageBox.Yes calls worker.cancel() once."""
        worker_mock = MagicMock(spec=PipelineWorker)
        step._worker = worker_mock

        with patch(
            "eleitorum.ui.steps.step_processing.QMessageBox.question",
            return_value=QMessageBox.StandardButton.Yes,
        ):
            step._on_cancel_clicked()

        worker_mock.cancel.assert_called_once()

    def test_step_processing_worker_signals_connected(self, step, qtbot) -> None:
        """After start_processing(worker), emitting worker.progress updates the bar."""
        worker = MagicMock(spec=PipelineWorker)

        # We need a real PipelineWorker to test actual signal connections.
        # Use a minimal mock that has connectable signals by using a real worker
        # with a dummy pipeline source (no file needed — we patch run()).
        from PySide6.QtCore import QThread, Signal

        class FakeWorker(QThread):
            progress = Signal(int, int)
            finished = Signal(object)
            error = Signal(str)
            cancelled = Signal()

            def run(self) -> None:
                pass  # no-op

            def cancel(self) -> None:
                pass

        fake_worker = FakeWorker()
        # Note: FakeWorker is a QThread (not QWidget), so we don't call qtbot.addWidget()
        # but we still need to ensure it is cleaned up
        fake_worker.setParent(step)  # parent to step widget for cleanup

        step.start_processing(fake_worker)

        # Emit progress from worker; bar should update
        fake_worker.progress.emit(10, 100)
        # Process Qt events
        QApplication.processEvents()
        assert step._bar.value() == 10

    def test_step_processing_emits_finished_routing_signal(self, step, qtbot) -> None:
        """worker.finished emits route_to_preview on success, route_to_error on failure."""
        from PySide6.QtCore import QThread, Signal

        class FakeWorker(QThread):
            progress = Signal(int, int)
            finished = Signal(object)
            error = Signal(str)
            cancelled = Signal()

            def run(self) -> None:
                pass

            def cancel(self) -> None:
                pass

        fake_worker = FakeWorker()
        fake_worker.setParent(step)

        step.start_processing(fake_worker)

        # Test success routing
        success_result = types.SimpleNamespace(success=True)
        with qtbot.waitSignal(step.route_to_preview, timeout=1000) as blocker:
            fake_worker.finished.emit(success_result)
        assert blocker.args[0] is success_result

        # Reset and test failure routing
        fake_worker2 = FakeWorker()
        fake_worker2.setParent(step)
        step.start_processing(fake_worker2)

        failure_result = types.SimpleNamespace(success=False)
        with qtbot.waitSignal(step.route_to_error, timeout=1000) as blocker:
            fake_worker2.finished.emit(failure_result)
        assert blocker.args[0] is failure_result
