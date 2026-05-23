"""Smoke tests for StepSheet — Step 2.5 sheet picker (WIZ-03).

All test data is synthetic per Eleitorum.md §14.1 (no real personal data).
"""
from __future__ import annotations

import pytest

from eleitorum.core.readers import SheetInfo
from eleitorum.ui.session import SessionModel
from eleitorum.ui.strings import SHEET_PICKER_EMPTY_SUFFIX, SHEET_PICKER_ROWS_TEMPLATE
from eleitorum.ui.steps.step_sheet import StepSheet


class TestStepSheet:
    """Requirement: WIZ-03 — sheet picker step."""

    def test_step_sheet_constructs_with_empty_sheets(self, qtbot) -> None:
        """StepSheet constructs; QListWidget child present with 0 items."""
        from PySide6.QtWidgets import QListWidget

        session = SessionModel(sheets=[])
        step = StepSheet(session=session)
        qtbot.addWidget(step)

        assert hasattr(step, "_list")
        assert isinstance(step._list, QListWidget)
        assert step._list.count() == 0

    def test_step_sheet_populates_from_session_sheets(self, qtbot) -> None:
        """populate_from_session() builds list items from session.sheets."""
        session = SessionModel()
        session.sheets = [
            SheetInfo("Docentes", 247, False),
            SheetInfo("Vazia", 0, True),
        ]
        step = StepSheet(session=session)
        qtbot.addWidget(step)

        step.populate_from_session()

        assert step._list.count() == 2
        # First item includes name and row count
        item0_text = step._list.item(0).text()
        expected_rows = SHEET_PICKER_ROWS_TEMPLATE.format(rows=247)
        assert "Docentes" in item0_text
        assert expected_rows in item0_text
        # Second item includes empty suffix
        item1_text = step._list.item(1).text()
        assert SHEET_PICKER_EMPTY_SUFFIX in item1_text

    def test_step_sheet_empty_sheet_visually_muted(self, qtbot) -> None:
        """Empty sheet QListWidgetItem has muted foreground color #878787."""
        session = SessionModel()
        session.sheets = [
            SheetInfo("Docentes", 247, False),
            SheetInfo("Vazia", 0, True),
        ]
        step = StepSheet(session=session)
        qtbot.addWidget(step)
        step.populate_from_session()

        # First item (non-empty) should NOT be muted
        item_normal = step._list.item(0)
        # Second item (empty) should have muted color
        item_empty = step._list.item(1)
        assert item_empty.foreground().color().name() == "#878787"

    def test_step_sheet_single_selection_only(self, qtbot) -> None:
        """QListWidget uses SingleSelection mode."""
        from PySide6.QtWidgets import QAbstractItemView

        session = SessionModel(sheets=[])
        step = StepSheet(session=session)
        qtbot.addWidget(step)

        assert (
            step._list.selectionMode()
            == QAbstractItemView.SelectionMode.SingleSelection
        )

    def test_step_sheet_is_complete_false_when_no_selection(self, qtbot) -> None:
        """With sheets populated but nothing selected, is_complete() is False."""
        session = SessionModel()
        session.sheets = [SheetInfo("Docentes", 247, False)]
        step = StepSheet(session=session)
        qtbot.addWidget(step)
        step.populate_from_session()

        assert step.is_complete() is False

    def test_step_sheet_is_complete_true_after_selection_and_writes_session(
        self, qtbot
    ) -> None:
        """Selecting first item: is_complete() True and session.sheet_name == 'Docentes'."""
        session = SessionModel()
        session.sheets = [
            SheetInfo("Docentes", 247, False),
            SheetInfo("Vazia", 0, True),
        ]
        step = StepSheet(session=session)
        qtbot.addWidget(step)
        step.populate_from_session()

        # Select first item programmatically
        step._list.setCurrentRow(0)

        assert step.is_complete() is True
        assert session.sheet_name == "Docentes"
