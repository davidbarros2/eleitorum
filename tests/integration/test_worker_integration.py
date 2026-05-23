"""Integration tests for PipelineWorker with real pipeline execution (D-01, TST-05).

Exercises PipelineWorker end-to-end via QThread signals using real synthetic
caderno fixtures. Validates the load-bearing signal routing contract:
- Validation failures (duplicate mec) reach ``finished`` with ``success=False``.
- Unexpected exceptions would reach ``error`` (not tested here; covered by unit tests).

D-01 scope: exactly 2 tests.
TST-05: integration tests for both output types with exact signal assertions.

Do NOT add a cancel-with-real-file test here — that path is already covered
in tests/unit/ui/test_worker.py::TestPipelineWorker::test_worker_run_emits_cancelled_when_cancelled.
"""

from __future__ import annotations

import pathlib

import pytest
from pytestqt.qtbot import QtBot

from eleitorum.ui.worker import PipelineWorker
from tests.fixtures import generators


def test_worker_happy_path_caderno(qtbot: QtBot, tmp_path: pathlib.Path) -> None:
    """PipelineWorker with a real caderno file emits finished(result) with success=True.

    Requirements: D-01 (happy-path integration test), TST-05 (pipeline + worker integration).

    Signal routing contract (load-bearing):
    - worker.start() launches the QThread (NOT worker.run(), which executes synchronously).
    - qtbot.waitSignal(worker.finished, timeout=10_000) blocks until finished fires.
    - Validation failures also reach finished (not error) — see test below.
    - worker.wait() is called after the context manager to avoid Windows QThread
      teardown warnings (RESEARCH §Common Pitfalls Pitfall 5).
    """
    inp = generators.make_simple_caderno(tmp_path / "in.csv")
    out = tmp_path / "out.csv"

    worker = PipelineWorker(inp, "caderno", out)
    with qtbot.waitSignal(worker.finished, timeout=10_000) as blocker:
        worker.start()
    worker.wait()

    result = blocker.args[0]
    assert result.success is True, (
        f"expected success for clean caderno fixture, got failures: {result.failures}"
    )
    assert out.exists(), "output CSV must be created on success"


def test_worker_duplicate_mec_emits_finished_failure(
    qtbot: QtBot, tmp_path: pathlib.Path
) -> None:
    """Duplicate mec → pipeline validation failure → finished(result) with success=False.

    Requirements: D-01 (rejection integration test), TST-05 (pipeline + worker integration).

    Critical signal routing (load-bearing — DO NOT change to worker.error):
    - run_pipeline() catches EleitorumError subclasses internally and returns
      PipelineResult(success=False). The worker then emits finished(result).
    - worker.error is ONLY emitted for unexpected exceptions (ImportError, MemoryError, …)
      that are NOT EleitorumError subclasses.
    - Waiting on worker.error for a validation failure would hang for the full timeout.

    See also: RESEARCH §Common Pitfalls Pitfall 1, worker.py lines 112-115.
    """
    inp = generators.make_duplicate_within_prefix(tmp_path / "dup.csv")
    out = tmp_path / "out.csv"

    worker = PipelineWorker(inp, "caderno", out)
    with qtbot.waitSignal(worker.finished, timeout=10_000) as blocker:
        worker.start()
    worker.wait()

    result = blocker.args[0]
    assert result.success is False, (
        "expected failure for duplicate-mec caderno fixture"
    )
    assert not out.exists(), (
        "output CSV must NOT be created when the pipeline rejects the input"
    )
