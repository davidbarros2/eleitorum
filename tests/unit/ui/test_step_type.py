"""Smoke tests for StepType — Step 1 output type selection (WIZ-01).

All test data is synthetic per Eleitorum.md §14.1 (no real personal data).
"""
from __future__ import annotations

import pytest

from eleitorum.ui.session import SessionModel
from eleitorum.ui.strings import STEP_1_TITLE
from eleitorum.ui.steps.step_type import StepType


class TestStepType:
    """Requirement: WIZ-01 — output type selection step."""

    def test_step_type_constructs_with_session(self, qtbot) -> None:
        """StepType constructs; two OptionCard children; stepTitle label present."""
        session = SessionModel()
        step = StepType(session=session)
        qtbot.addWidget(step)

        # Check for OptionCard children by attribute names
        assert hasattr(step, "_card_caderno")
        assert hasattr(step, "_card_elegiveis")

        # Find stepTitle label
        from PySide6.QtWidgets import QLabel
        labels = step.findChildren(QLabel)
        title_labels = [l for l in labels if l.objectName() == "stepTitle"]
        assert len(title_labels) == 1
        assert title_labels[0].text() == STEP_1_TITLE

    def test_step_type_is_complete_false_initially(self, qtbot) -> None:
        """Fresh session: is_complete() returns False."""
        session = SessionModel()
        step = StepType(session=session)
        qtbot.addWidget(step)

        assert step.is_complete() is False

    def test_step_type_selecting_caderno_sets_session_output_type(self, qtbot) -> None:
        """Programmatic select of caderno card writes session.output_type == 'caderno'."""
        session = SessionModel()
        step = StepType(session=session)
        qtbot.addWidget(step)

        step._card_caderno.set_selected(True)

        assert session.output_type == "caderno"

    def test_step_type_selecting_caderno_deselects_elegiveis(self, qtbot) -> None:
        """After selecting caderno, elegiveis card is deselected."""
        session = SessionModel()
        step = StepType(session=session)
        qtbot.addWidget(step)

        # Select elegiveis first
        step._card_elegiveis.set_selected(True)
        # Then select caderno — elegiveis should be deselected
        step._card_caderno.set_selected(True)

        assert step._card_elegiveis.property("selected") is False

    def test_step_type_is_complete_true_after_selection(self, qtbot) -> None:
        """After selecting a card, is_complete() returns True."""
        session = SessionModel()
        step = StepType(session=session)
        qtbot.addWidget(step)

        step._card_caderno.set_selected(True)

        assert step.is_complete() is True

    def test_step_type_preserves_existing_session_state(self, qtbot) -> None:
        """Construct with existing output_type; card shows selected on init."""
        session = SessionModel(output_type="elegiveis")
        step = StepType(session=session)
        qtbot.addWidget(step)

        # The elegiveis card should visually show selected (back-navigation restoration)
        assert step._card_elegiveis.property("selected") is True
        assert step._card_caderno.property("selected") is False
