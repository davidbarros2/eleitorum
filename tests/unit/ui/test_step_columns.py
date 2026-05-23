"""Smoke tests for StepColumns — Step 3 column mapping (WIZ-04, DET-07).

All test data is synthetic per Eleitorum.md §14.1 (no real personal data).

Note: session.pipeline_result is seeded with types.SimpleNamespace for
unit tests; the real PipelineResult from pipeline.py is only used at runtime.
"""
from __future__ import annotations

import types

import pytest

from eleitorum.ui.session import SessionModel
from eleitorum.ui.strings import BTN_ALTERAR, STEP_3_TITLE
from eleitorum.ui.steps.step_columns import StepColumns


def _make_detected_session(
    output_type: str = "caderno",
    mec_col_index: int = 0,
    name_col_index: int = 1,
    detection_method: str = "synonym",
) -> SessionModel:
    """Return a session with synthetic pipeline_result.detection populated."""
    session = SessionModel(output_type=output_type)
    session.column_headers = ["No Mec. Teste", "Nome Completo Teste", "Categoria"]
    session.pipeline_result = types.SimpleNamespace(
        detection={
            "mec_col_index": mec_col_index,
            "name_col_index": name_col_index,
            "detection_method": detection_method,
            "encoding": "utf-8",
            "header_row_index": 0,
        }
    )
    return session


class TestStepColumns:
    """Requirement: WIZ-04 — column mapping step; DET-07 — elegíveis hides mec row."""

    def test_step_columns_constructs(self, qtbot) -> None:
        """StepColumns builds with two mapping rows (mec + name) for caderno."""
        session = SessionModel(output_type="caderno")
        session.column_headers = ["No Mec. Teste", "Nome Completo Teste"]
        step = StepColumns(session=session)
        qtbot.addWidget(step)

        assert hasattr(step, "_mec_row")
        assert hasattr(step, "_name_row")

        # Check stepTitle
        from PySide6.QtWidgets import QLabel
        labels = step.findChildren(QLabel)
        title_labels = [l for l in labels if l.objectName() == "stepTitle"]
        assert len(title_labels) == 1
        assert title_labels[0].text() == STEP_3_TITLE

    def test_step_columns_hides_mec_row_for_elegiveis(self, qtbot) -> None:
        """Mecanográfico row is hidden when output_type == 'elegiveis' (DET-07)."""
        session = SessionModel(output_type="elegiveis")
        session.column_headers = ["No Mec. Teste", "Nome Completo Teste"]
        step = StepColumns(session=session)
        qtbot.addWidget(step)

        # The mec row must not be hidden when we set output_type and call populate
        step.populate_from_session()

        assert step._mec_row.isVisible() is False

    def test_step_columns_shows_mec_row_for_caderno(self, qtbot) -> None:
        """Mecanográfico row is visible when output_type == 'caderno'."""
        session = SessionModel(output_type="caderno")
        session.column_headers = ["No Mec. Teste", "Nome Completo Teste"]
        step = StepColumns(session=session)
        qtbot.addWidget(step)
        step.show()
        step.populate_from_session()

        assert step._mec_row.isVisible() is True

    def test_step_columns_pre_populated_when_detection_succeeded(self, qtbot) -> None:
        """Auto-detected columns: value label shows detected column name; Alterar button present."""
        session = _make_detected_session()
        step = StepColumns(session=session)
        qtbot.addWidget(step)
        step.populate_from_session()

        # Alterar buttons must exist
        from PySide6.QtWidgets import QPushButton
        alterar_buttons = [
            w for w in step.findChildren(QPushButton)
            if w.text() == BTN_ALTERAR
        ]
        assert len(alterar_buttons) >= 1

        # Value label for mec column should reference the detected column name
        assert "No Mec. Teste" in step._mec_value_label.text()

    def test_step_columns_manual_mode_when_no_detection(self, qtbot) -> None:
        """No detection: no-detection message shown; QComboBoxes active."""
        from PySide6.QtWidgets import QComboBox

        session = SessionModel(output_type="caderno")
        session.column_headers = ["No Mec. Teste", "Nome Completo Teste"]
        session.pipeline_result = None  # No detection
        step = StepColumns(session=session)
        qtbot.addWidget(step)
        step.show()
        step.populate_from_session()

        # No-detection label must NOT be hidden
        assert step._no_detection_label.isHidden() is False
        # Name combo must NOT be hidden
        assert step._name_combo.isHidden() is False

    def test_step_columns_alterar_opens_combobox(self, qtbot) -> None:
        """Clicking Alterar reveals the QComboBox for that row."""
        from PySide6.QtWidgets import QComboBox

        session = _make_detected_session()
        step = StepColumns(session=session)
        qtbot.addWidget(step)
        step.show()
        step.populate_from_session()

        # Before click: combo is hidden in auto mode
        assert step._mec_combo.isHidden() is True

        # Click Alterar for mec row
        step._mec_alterar_btn.click()

        # After click: combo becomes visible
        assert step._mec_combo.isHidden() is False

    def test_step_columns_writes_session_column_map_on_change(self, qtbot) -> None:
        """Changing QComboBox selection writes session.column_map."""
        session = SessionModel(output_type="caderno")
        session.column_headers = ["No Mec. Teste", "Nome Completo Teste", "Extra"]
        session.pipeline_result = None
        step = StepColumns(session=session)
        qtbot.addWidget(step)
        step.populate_from_session()

        # Change name combo selection to index 2
        step._name_combo.setCurrentIndex(2)

        assert session.column_map is not None
        assert "name" in session.column_map

    def test_step_columns_is_complete_always_true_when_visible(self, qtbot) -> None:
        """is_complete() returns True unconditionally (WIZ-04 spec)."""
        session = SessionModel(output_type="caderno")
        step = StepColumns(session=session)
        qtbot.addWidget(step)

        assert step.is_complete() is True
