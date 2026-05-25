"""Tests for StepPreview wizard step widget (WIZ-05).

Verifies preview table rendering (≤50 rows), column headers, summary row count,
and next_button_label override.

All test data is synthetic (no real personal data per CLAUDE.md privacy constraint).
"""

from __future__ import annotations

import types

from PySide6.QtWidgets import QAbstractItemView

from eleitorum.ui.session import SessionModel
from eleitorum.ui.strings import BTN_GRAVAR


def _make_result(
    *,
    rows_processed: int = 10,
    transformations_applied: int = 0,
    log_entries: list[str] | None = None,
    preview_rows: list[list[str]] | None = None,
    failures: list | None = None,
) -> types.SimpleNamespace:
    """Build a minimal PipelineResult-like namespace for testing."""
    return types.SimpleNamespace(
        success=True,
        rows_processed=rows_processed,
        transformations_applied=transformations_applied,
        log_entries=log_entries or [],
        preview_rows=preview_rows or [],
        failures=failures or [],
        output_path=None,
        log_path=None,
        error_log_path=None,
        detection={},
    )


class TestStepPreview:
    """Tests for StepPreview (step 4 — preview table + summary panel)."""

    def _make_step(self, qtbot, output_type: str = "caderno"):
        from eleitorum.ui.steps.step_preview import StepPreview

        session = SessionModel(output_type=output_type)
        widget = StepPreview(session)
        qtbot.addWidget(widget)
        widget.show()
        return widget, session

    def test_step_preview_constructs(self, qtbot) -> None:
        """StepPreview builds with title, summary label, and table."""
        from PySide6.QtWidgets import QLabel, QTableWidget

        step, _ = self._make_step(qtbot)

        title = step.findChild(QLabel, "stepTitle")
        assert title is not None

        assert hasattr(step, "_table")
        assert isinstance(step._table, QTableWidget)

        assert hasattr(step, "_summary_rows_label")

    def test_step_preview_no_log_view(self, qtbot) -> None:
        """StepPreview no longer has _log_view or _ver_detalhes_btn."""
        step, _ = self._make_step(qtbot)

        assert not hasattr(step, "_log_view"), "_log_view should not exist"
        assert not hasattr(step, "_ver_detalhes_btn"), "_ver_detalhes_btn should not exist"

    def test_step_preview_table_read_only(self, qtbot) -> None:
        """After populate_from_session(), table edit triggers are NoEditTriggers."""
        step, session = self._make_step(qtbot)
        result = _make_result(
            rows_processed=5,
            preview_rows=[["A001", "Nome Teste Sintetico", ""] for _ in range(5)],
        )
        session.pipeline_result = result
        step.populate_from_session()

        assert step._table.editTriggers() == QAbstractItemView.EditTrigger.NoEditTriggers

    def test_step_preview_renders_up_to_50_rows(self, qtbot) -> None:
        """With 200 preview rows in result, table shows exactly 50 rows."""
        step, session = self._make_step(qtbot)
        preview_rows = [[f"F{i}", f"Nome Sintetico {i}", f"Cat{i}"] for i in range(200)]
        result = _make_result(rows_processed=200, preview_rows=preview_rows)
        session.pipeline_result = result
        step.populate_from_session()

        assert step._table.rowCount() == 50
        assert step._table.columnCount() == len(preview_rows[0])

    def test_step_preview_summary_shows_row_count(self, qtbot) -> None:
        """Summary text contains the rows_processed count."""
        step, session = self._make_step(qtbot)
        result = _make_result(rows_processed=123, preview_rows=[["A1", "Nome Exemplo", ""]])
        session.pipeline_result = result
        step.populate_from_session()

        from PySide6.QtWidgets import QLabel

        labels = step.findChildren(QLabel)
        texts = [lbl.text() for lbl in labels]
        assert any("123" in t for t in texts), f"Row count 123 not found. Labels: {texts}"

    def test_step_preview_caderno_has_column_headers(self, qtbot) -> None:
        """Caderno preview table has 'Nº Mecanográfico', 'Nome', 'Categoria' headers."""
        step, session = self._make_step(qtbot, output_type="caderno")
        result = _make_result(preview_rows=[["a1234", "Silva Teste", ""]])
        session.pipeline_result = result
        step.populate_from_session()

        headers = [
            step._table.horizontalHeaderItem(c).text()
            for c in range(step._table.columnCount())
            if step._table.horizontalHeaderItem(c) is not None
        ]
        assert "Nº Mecanográfico" in headers
        assert "Nome" in headers

    def test_step_preview_elegiveis_has_nome_header(self, qtbot) -> None:
        """Elegiveis preview table has 'Nome' header."""
        step, session = self._make_step(qtbot, output_type="elegiveis")
        result = _make_result(preview_rows=[["Silva Teste"]])
        session.pipeline_result = result
        step.populate_from_session()

        headers = [
            step._table.horizontalHeaderItem(c).text()
            for c in range(step._table.columnCount())
            if step._table.horizontalHeaderItem(c) is not None
        ]
        assert "Nome" in headers

    def test_step_preview_next_button_label_is_gravar(self, qtbot) -> None:
        """next_button_label() returns BTN_GRAVAR ('Escolher destino e gravar')."""
        step, _ = self._make_step(qtbot)
        assert step.next_button_label() == BTN_GRAVAR

    def test_step_preview_is_complete_always_true(self, qtbot) -> None:
        """is_complete() always returns True regardless of state."""
        step, session = self._make_step(qtbot)
        assert step.is_complete() is True

        result = _make_result(preview_rows=[["A1", "Nome Exemplo", ""]])
        session.pipeline_result = result
        step.populate_from_session()
        assert step.is_complete() is True
