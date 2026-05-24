"""Tests for StepPreview wizard step widget (WIZ-05, D-03).

Verifies preview table rendering (≤50 rows), summary panel, "Ver detalhes"
log toggle, and next_button_label override.

All test data is synthetic (no real personal data per CLAUDE.md privacy constraint).
"""

from __future__ import annotations

import types

import pytest
from PySide6.QtWidgets import QAbstractItemView, QApplication, QTextEdit

from eleitorum.ui.session import SessionModel
from eleitorum.ui.strings import (
    BTN_GRAVAR,
    BTN_VER_DETALHES_ABRIR,
    BTN_VER_DETALHES_FECHAR,
)


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

    @pytest.fixture()
    def session(self) -> SessionModel:
        return SessionModel()

    @pytest.fixture()
    def step(self, session: SessionModel, qtbot):
        from eleitorum.ui.steps.step_preview import StepPreview

        widget = StepPreview(session)
        qtbot.addWidget(widget)
        widget.show()  # required so isVisible() returns correct state for children
        return widget

    def test_step_preview_constructs(self, step) -> None:
        """StepPreview builds with title, summary labels, optional detalhes button, table, log view."""
        from PySide6.QtWidgets import QLabel, QPushButton, QTableWidget

        # Step title
        title = step.findChild(QLabel, "stepTitle")
        assert title is not None, "stepTitle QLabel not found"

        # Table
        assert hasattr(step, "_table"), "_table attribute missing"
        assert isinstance(step._table, QTableWidget)

        # Log view (initially hidden)
        assert hasattr(step, "_log_view"), "_log_view attribute missing"
        assert isinstance(step._log_view, QTextEdit)
        assert not step._log_view.isVisible(), "_log_view should be hidden initially"
        assert step._log_view.maximumHeight() == 150

        # Ver detalhes button
        assert hasattr(step, "_ver_detalhes_btn"), "_ver_detalhes_btn attribute missing"
        assert isinstance(step._ver_detalhes_btn, QPushButton)

    def test_step_preview_table_read_only(self, step, session) -> None:
        """After populate_from_session(), table edit triggers are NoEditTriggers."""
        result = _make_result(
            rows_processed=5,
            preview_rows=[["A001", "Nome Teste Sintetico"] for _ in range(5)],
        )
        session.pipeline_result = result
        step.populate_from_session()

        assert step._table.editTriggers() == QAbstractItemView.EditTrigger.NoEditTriggers

    def test_step_preview_renders_up_to_50_rows(self, step, session) -> None:
        """With 200 preview rows in result, table shows exactly 50 rows."""
        preview_rows = [[f"F{i}", f"Nome Sintetico {i}", f"Cat{i}"] for i in range(200)]
        result = _make_result(rows_processed=200, preview_rows=preview_rows)
        session.pipeline_result = result
        step.populate_from_session()

        assert step._table.rowCount() == 50
        # Column count matches the row width
        assert step._table.columnCount() == len(preview_rows[0])

    def test_step_preview_summary_shows_row_count(self, step, session) -> None:
        """Summary text contains the rows_processed count."""
        result = _make_result(rows_processed=123, preview_rows=[["A1", "Nome Exemplo"]])
        session.pipeline_result = result
        step.populate_from_session()

        # Find any label that contains the row count
        from PySide6.QtWidgets import QLabel

        labels = step.findChildren(QLabel)
        texts = [lbl.text() for lbl in labels]
        assert any("123" in t for t in texts), (
            f"Row count 123 not found in any label. Labels: {texts}"
        )

    def test_step_preview_summary_shows_transformation_count(self, step, session) -> None:
        """Summary text contains transformations_applied count."""
        result = _make_result(
            rows_processed=10,
            transformations_applied=7,
            preview_rows=[["A1", "Nome Exemplo"]],
        )
        session.pipeline_result = result
        step.populate_from_session()

        from PySide6.QtWidgets import QLabel

        labels = step.findChildren(QLabel)
        texts = [lbl.text() for lbl in labels]
        assert any("7" in t for t in texts), f"Transformation count 7 not found. Labels: {texts}"

    def test_step_preview_ver_detalhes_hidden_when_no_transformations(self, step, session) -> None:
        """Ver detalhes button is hidden when transformations_applied == 0."""
        result = _make_result(transformations_applied=0, preview_rows=[["A1", "Nome Exemplo"]])
        session.pipeline_result = result
        step.populate_from_session()

        assert not step._ver_detalhes_btn.isVisible(), (
            "Ver detalhes button should be hidden when no transformations"
        )

    def test_step_preview_ver_detalhes_toggles_log_visibility(self, step, session, qtbot) -> None:
        """Clicking Ver detalhes toggles log visibility and button text."""
        result = _make_result(
            transformations_applied=3,
            log_entries=["log line 1", "log line 2"],
            preview_rows=[["A1", "Nome Exemplo"]],
        )
        session.pipeline_result = result
        step.populate_from_session()

        assert step._ver_detalhes_btn.isVisible(), "Ver detalhes button should be visible"
        assert not step._log_view.isVisible(), "_log_view should start hidden"

        from PySide6.QtCore import Qt as _Qt

        # Click to show
        qtbot.mouseClick(step._ver_detalhes_btn, _Qt.MouseButton.LeftButton)
        QApplication.processEvents()
        assert step._log_view.isVisible(), "_log_view should be visible after click"
        assert step._ver_detalhes_btn.text() == BTN_VER_DETALHES_FECHAR

        # Click again to hide
        qtbot.mouseClick(step._ver_detalhes_btn, _Qt.MouseButton.LeftButton)
        QApplication.processEvents()
        assert not step._log_view.isVisible(), "_log_view should be hidden after second click"
        assert step._ver_detalhes_btn.text() == BTN_VER_DETALHES_ABRIR

    def test_step_preview_log_view_max_height_150(self, step) -> None:
        """_log_view.maximumHeight() == 150."""
        assert step._log_view.maximumHeight() == 150

    def test_step_preview_next_button_label_is_gravar(self, step) -> None:
        """next_button_label() returns BTN_GRAVAR ('Escolher destino e gravar')."""
        assert step.next_button_label() == BTN_GRAVAR

    def test_step_preview_is_complete_always_true(self, step) -> None:
        """is_complete() always returns True regardless of state."""
        assert step.is_complete() is True

        # Populate and check again
        session = step._session
        result = _make_result(preview_rows=[["A1", "Nome Exemplo"]])
        session.pipeline_result = result
        step.populate_from_session()
        assert step.is_complete() is True
