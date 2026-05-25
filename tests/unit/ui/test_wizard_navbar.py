"""Tests for WizardController completion_changed signal wiring (WIZ-01, WIZ-02, WIZ-03).

Verifies that WizardController connects the three step completion_changed signals
to _update_navbar_for_current_step so that the Próximo button responds immediately
to user interactions without requiring navigation.

All test data is synthetic per Eleitorum.md §14.1 (no real personal data).
"""

from __future__ import annotations

import pathlib

import pytest
from PySide6.QtWidgets import QLabel, QStackedWidget

from eleitorum.core.readers import SheetInfo
from eleitorum.ui.session import SessionModel
from eleitorum.ui.widgets.navbar import NavBar
from eleitorum.ui.wizard import WizardController


@pytest.fixture
def stack(qtbot) -> QStackedWidget:  # noqa: ANN001
    """Empty QStackedWidget for wizard construction."""
    w = QStackedWidget()
    qtbot.addWidget(w)
    return w


@pytest.fixture
def navbar(qtbot) -> NavBar:  # noqa: ANN001
    """NavBar widget for wizard construction."""
    nb = NavBar()
    qtbot.addWidget(nb)
    return nb


@pytest.fixture
def step_label(qtbot) -> QLabel:  # noqa: ANN001
    """Step indicator QLabel."""
    lbl = QLabel()
    qtbot.addWidget(lbl)
    return lbl


class TestWizardNavbarReactivity:
    """WizardController wires completion_changed to _update_navbar_for_current_step."""

    def test_step_type_completion_changed_connected(
        self,
        qtbot,  # noqa: ANN001
        stack: QStackedWidget,
        navbar: NavBar,
        step_label: QLabel,
    ) -> None:
        """completion_changed on _step_type is wired to _update_navbar_for_current_step.

        When StepType emits completion_changed while the wizard is on STEP_TYPE,
        the NavBar Próximo button must enable.
        """
        session = SessionModel()
        wizard = WizardController(session, stack, navbar, step_label)

        # Ensure on STEP_TYPE
        assert stack.currentIndex() == WizardController.STEP_TYPE

        # Before selection: Próximo disabled
        assert navbar._proximo_btn.isEnabled() is False

        # Trigger selection directly on the step widget
        wizard._step_type._on_selection("caderno")

        # After emission through completion_changed → _update_navbar_for_current_step,
        # Próximo must now be enabled
        assert navbar._proximo_btn.isEnabled() is True

    def test_step_upload_completion_changed_connected(
        self,
        qtbot,  # noqa: ANN001
        stack: QStackedWidget,
        navbar: NavBar,
        step_label: QLabel,
        tmp_path: pathlib.Path,
        monkeypatch,  # noqa: ANN001
    ) -> None:
        """completion_changed on _step_upload is wired to _update_navbar_for_current_step.

        When StepUpload emits completion_changed while wizard is on STEP_UPLOAD,
        the NavBar Próximo button must enable.
        """
        import openpyxl

        # Build a real synthetic xlsx for list_sheets to succeed
        xlsx_path = tmp_path / "sintetico_upload_teste.xlsx"
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.append(["No Mec.", "Nome"])
        ws.append(["B001", "Maria Teste"])
        wb.save(str(xlsx_path))

        session = SessionModel()
        wizard = WizardController(session, stack, navbar, step_label)

        # Navigate to STEP_UPLOAD
        stack.setCurrentIndex(WizardController.STEP_UPLOAD)
        wizard._update_navbar_for_current_step()

        # Before file: Próximo disabled
        assert navbar._proximo_btn.isEnabled() is False

        # Simulate file received
        wizard._step_upload._on_file_received(str(xlsx_path))

        # After emission: Próximo must be enabled
        assert navbar._proximo_btn.isEnabled() is True

    def test_step_sheet_completion_changed_connected(
        self,
        qtbot,  # noqa: ANN001
        stack: QStackedWidget,
        navbar: NavBar,
        step_label: QLabel,
    ) -> None:
        """completion_changed on _step_sheet is wired to _update_navbar_for_current_step.

        When StepSheet emits completion_changed while wizard is on STEP_SHEET,
        the NavBar Próximo button must enable.
        """
        session = SessionModel()
        session.sheets = [
            SheetInfo("Docentes Teste", 247, False),
            SheetInfo("Vazia Teste", 0, True),
        ]
        wizard = WizardController(session, stack, navbar, step_label)

        # Navigate to STEP_SHEET and populate
        stack.setCurrentIndex(WizardController.STEP_SHEET)
        wizard._step_sheet.populate_from_session()
        wizard._update_navbar_for_current_step()

        # Before selection: Próximo disabled
        assert navbar._proximo_btn.isEnabled() is False

        # Simulate sheet selection
        wizard._step_sheet._list.setCurrentRow(0)

        # After emission: Próximo must be enabled
        assert navbar._proximo_btn.isEnabled() is True
