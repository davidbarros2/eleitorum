"""Tests for PipelineWorker QThread and PipelineCancelledError (WIZ-11, PERF-02).

Covers the cancel mechanism contract and signal emission behaviour of
PipelineWorker. All synthetic data uses names containing 'Teste', 'Exemplo',
or 'Sintetica' per Eleitorum.md Section 14.1.
"""

from __future__ import annotations

import pathlib

import pytest

from eleitorum.core.errors import EleitorumError
from eleitorum.ui.worker import PipelineCancelledError, PipelineWorker


class TestPipelineWorker:
    """Requirement: WIZ-11, PERF-02 — background thread; cancel mechanism;
    progress/finished/cancelled/error signals emitted correctly.
    """

    def test_cancelled_error_not_eleitorumerror_subclass(self) -> None:
        """PipelineCancelledError must NOT subclass EleitorumError.

        This is the cancel-propagation contract: run_pipeline() catches
        EleitorumError internally and returns PipelineResult(success=False).
        PipelineCancelledError must escape that handler unchanged so that
        PipelineWorker.run() can distinguish cancel from validation failure.
        """
        assert not issubclass(PipelineCancelledError, EleitorumError)
        assert issubclass(PipelineCancelledError, Exception)

    def test_worker_signals_are_class_attributes(self) -> None:
        """progress, finished, error, cancelled must be class-level Signal attributes."""
        from PySide6.QtCore import Signal

        # Access via the class, not an instance — confirms class-level declaration
        assert hasattr(PipelineWorker, "progress")
        assert hasattr(PipelineWorker, "finished")
        assert hasattr(PipelineWorker, "error")
        assert hasattr(PipelineWorker, "cancelled")
        # Each attribute on the class should be a Signal descriptor
        assert isinstance(PipelineWorker.progress, Signal)
        assert isinstance(PipelineWorker.finished, Signal)
        assert isinstance(PipelineWorker.error, Signal)
        assert isinstance(PipelineWorker.cancelled, Signal)

    def test_progress_cb_raises_on_cancel(self) -> None:
        """_progress_cb raises PipelineCancelledError after cancel() is called."""
        worker = PipelineWorker(
            source=pathlib.Path("sintetico_teste.csv"),
            output_type="caderno",
            output_path=None,
        )
        worker.cancel()
        with pytest.raises(PipelineCancelledError):
            worker._progress_cb(50, 100)

    def test_progress_cb_emits_when_not_cancelled(self, qtbot) -> None:
        """_progress_cb emits progress signal with (current, total) when not cancelled."""
        worker = PipelineWorker(
            source=pathlib.Path("sintetico_teste.csv"),
            output_type="caderno",
            output_path=None,
        )
        # Call _progress_cb from the main thread while waiting for the signal
        with qtbot.waitSignal(worker.progress, timeout=1000) as blocker:
            worker._progress_cb(50, 100)

        assert blocker.args == [50, 100]

    def test_worker_run_emits_cancelled_when_cancelled(self, qtbot, tmp_path) -> None:
        """Worker emits cancelled (not error or finished) when cancel() is called before start().

        A synthetic CSV with >100 rows ensures progress_cb is called during the
        transform loop so the cancel check fires. The worker is cancelled before
        start() so the very first progress_cb call raises PipelineCancelledError.

        Synthetic data uses 'Sintetico Teste {i}' per the privacy invariant.
        """
        # Build a synthetic semicolon-delimited CSV with 200 data rows
        csv_path = tmp_path / "sintetico_teste.csv"
        lines = ["personnel_number;name"]
        for i in range(1, 201):
            lines.append(f"f{i};Sintetico Teste {i}")
        csv_path.write_text("\n".join(lines), encoding="utf-8")

        worker = PipelineWorker(
            source=str(csv_path),
            output_type="caderno",
            output_path=None,
        )
        # Cancel before starting — first progress_cb call will raise immediately
        worker.cancel()

        with qtbot.waitSignal(worker.cancelled, timeout=5000):
            worker.start()
