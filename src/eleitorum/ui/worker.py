"""PipelineWorker QThread and PipelineCancelledError for EleitorUM (WIZ-11, PERF-02).

Bridges the Qt-free core pipeline to the Qt UI via a QThread subclass.
``PipelineWorker`` runs ``run_pipeline()`` in a background thread and emits
Qt signals to communicate progress, completion, and error states to the main
thread.

Security note (ASVS V7 / T-02-01-02): ``error.emit()`` passes ONLY
``str(exc)`` — never ``traceback.format_exc()`` or any frame introspection.
Python internals must never reach the user-facing UI.

Requirements: WIZ-11 (background thread, cancel available), PERF-02
(UI thread stays responsive during processing).
"""

from __future__ import annotations

import pathlib
import threading

from PySide6.QtCore import QThread, Signal

from eleitorum.core.pipeline import PipelineSource, run_pipeline


class PipelineCancelledError(Exception):
    """Raised by ``_progress_cb`` to abort ``run_pipeline()`` mid-run.

    NOT a subclass of EleitorumError — must propagate through the pipeline's
    ``except EleitorumError`` catch block unchanged so cancellation reaches
    ``PipelineWorker.run()`` which then emits the ``cancelled`` signal.

    Intentional design: ``run_pipeline()`` catches only ``EleitorumError``
    subclasses internally; this exception therefore escapes that handler and
    propagates to the worker, where it is caught first before the generic
    ``Exception`` handler.
    """


class PipelineWorker(QThread):
    """Runs ``run_pipeline()`` in a background QThread.

    Signals (all delivered to the main thread via Qt's queued connection):
        progress(int, int): emitted every 100 rows with (current_row, total_rows).
        finished(object): emitted with the ``PipelineResult`` on completion
            (both success and validation failure — distinguish via
            ``result.success``).
        error(str): emitted with a PT-PT message for genuinely unexpected
            exceptions (ImportError, MemoryError, etc.).
        cancelled(): emitted when ``cancel()`` was called and ``_progress_cb``
            raised ``PipelineCancelledError``.

    Usage::

        worker = PipelineWorker(source, "caderno", output_path=None)
        worker.progress.connect(on_progress)
        worker.finished.connect(on_finished)
        worker.cancelled.connect(on_cancelled)
        worker.start()
        # Later, if user clicks Cancel:
        worker.cancel()
    """

    progress = Signal(int, int)  # (current_row, total_rows)
    finished = Signal(object)  # PipelineResult on success or validation failure
    error = Signal(str)  # PT-PT message for unexpected exceptions only
    cancelled = Signal()  # emitted when cancel flag triggered

    def __init__(
        self,
        source: PipelineSource | pathlib.Path | str,
        output_type: str,
        output_path: object,
        parent: object = None,
    ) -> None:
        super().__init__(parent)  # type: ignore[arg-type]
        self._source = source
        self._output_type = output_type
        self._output_path = output_path
        self._cancel_event = threading.Event()

    def cancel(self) -> None:
        """Signal the worker to stop at the next progress callback checkpoint."""
        self._cancel_event.set()

    def _progress_cb(self, current: int, total: int) -> None:
        """Called by ``run_pipeline()`` every 100 rows (D-04 contract).

        Checks the cancel flag first; raises ``PipelineCancelledError`` if set
        (propagates through pipeline's EleitorumError handler unchanged).
        Otherwise emits the ``progress`` signal for the UI to update.
        """
        if self._cancel_event.is_set():
            raise PipelineCancelledError("Processamento cancelado pelo utilizador.")
        self.progress.emit(current, total)

    def run(self) -> None:
        """Override of ``QThread.run()`` — executes the pipeline in this thread.

        Exception ordering is critical:
        1. ``PipelineCancelledError`` caught first — emits ``cancelled``.
        2. Generic ``Exception`` caught second — emits ``error`` with str(exc)
           only (ASVS V7: no tracebacks).
        3. On success, emits ``finished`` with the ``PipelineResult``.
        """
        try:
            result = run_pipeline(
                self._source,
                self._output_type,  # type: ignore[arg-type]
                self._output_path,  # type: ignore[arg-type]
                progress_cb=self._progress_cb,
                write_success_log=False,  # log available in result.log_entries; no file written
            )
            self.finished.emit(result)
        except PipelineCancelledError:
            self.cancelled.emit()
        except Exception as exc:
            # Genuinely unexpected (ImportError, MemoryError, etc.)
            # ASVS V7 / T-02-01-02: emit only str(exc), never traceback.format_exc()
            self.error.emit(str(exc))
