"""Smoke tests for eleitorum.ui.wizard — WizardController navigation (WIZ-06, WIZ-09, WIZ-10).

Tests verify:
- 7 steps are inserted into the stack
- STEP_SHEET is skipped on single-sheet files, included on multi-sheet
- Step indicator returns correct (n, total) tuples
- reiniciar() mutates session in place (preserves object identity)
- Dry-run PipelineWorker is constructed with output_path=None at STEP_COLUMNS
- Save dialog rejects output==input path with QMessageBox.warning
"""

from __future__ import annotations

import pathlib
from unittest.mock import MagicMock, patch

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


@pytest.fixture
def session_single_sheet(tmp_path: pathlib.Path) -> SessionModel:
    """SessionModel with source_path set and single-sheet (no sheets list)."""
    s = SessionModel()
    s.source_path = tmp_path / "sintetico_teste.xlsx"
    s.output_type = "caderno"
    # sheets is None (or single-item) → STEP_SHEET should be skipped
    return s


@pytest.fixture
def session_multi_sheet(tmp_path: pathlib.Path) -> SessionModel:
    """SessionModel with source_path and two sheets → STEP_SHEET shown."""
    s = SessionModel()
    s.source_path = tmp_path / "sintetico_multi_teste.xlsx"
    s.output_type = "caderno"
    s.sheets = [
        SheetInfo(name="Folha1 Teste", approximate_row_count=10, is_empty=False),
        SheetInfo(name="Folha2 Teste", approximate_row_count=5, is_empty=False),
    ]
    return s


class TestWizardController:
    """Tests for WizardController step navigation (WIZ-06, WIZ-09, WIZ-10)."""

    def test_wizard_constructs_with_seven_steps(
        self,
        qtbot,  # noqa: ANN001
        stack: QStackedWidget,
        navbar: NavBar,
        step_label: QLabel,
    ) -> None:
        """WizardController must insert exactly 7 step widgets into the stack."""
        session = SessionModel()
        wizard = WizardController(session, stack, navbar, step_label)
        assert stack.count() == 7

    def test_wizard_skips_sheet_step_when_single_sheet(
        self,
        qtbot,  # noqa: ANN001
        stack: QStackedWidget,
        navbar: NavBar,
        step_label: QLabel,
        session_single_sheet: SessionModel,
    ) -> None:
        """on_proximo from STEP_UPLOAD goes to STEP_COLUMNS (skip STEP_SHEET) when <=1 sheet."""
        wizard = WizardController(session_single_sheet, stack, navbar, step_label)
        # Navigate to STEP_UPLOAD first
        stack.setCurrentIndex(WizardController.STEP_UPLOAD)

        # Trigger next from STEP_UPLOAD with single-sheet session
        wizard.on_proximo()

        # Should land on STEP_COLUMNS, not STEP_SHEET
        assert stack.currentIndex() == WizardController.STEP_COLUMNS

    def test_wizard_includes_sheet_step_when_multi_sheet(
        self,
        qtbot,  # noqa: ANN001
        stack: QStackedWidget,
        navbar: NavBar,
        step_label: QLabel,
        session_multi_sheet: SessionModel,
    ) -> None:
        """on_proximo from STEP_UPLOAD goes to STEP_SHEET when session has >1 sheet."""
        wizard = WizardController(session_multi_sheet, stack, navbar, step_label)
        stack.setCurrentIndex(WizardController.STEP_UPLOAD)

        wizard.on_proximo()

        assert stack.currentIndex() == WizardController.STEP_SHEET

    def test_wizard_step_indicator_uses_5_total_on_standard_path(
        self,
        qtbot,  # noqa: ANN001
        stack: QStackedWidget,
        navbar: NavBar,
        step_label: QLabel,
    ) -> None:
        """_step_display_number() returns (3, 5) at STEP_COLUMNS on standard path."""
        session = SessionModel()
        wizard = WizardController(session, stack, navbar, step_label)
        # No multi-sheet path taken
        stack.setCurrentIndex(WizardController.STEP_COLUMNS)
        n, total = wizard._step_display_number()
        assert total == 5
        assert n == 3

    def test_wizard_step_indicator_uses_6_total_on_multi_sheet_path(
        self,
        qtbot,  # noqa: ANN001
        stack: QStackedWidget,
        navbar: NavBar,
        step_label: QLabel,
        session_multi_sheet: SessionModel,
    ) -> None:
        """_step_display_number() returns (4, 6) at STEP_COLUMNS on multi-sheet path."""
        wizard = WizardController(session_multi_sheet, stack, navbar, step_label)
        # Navigate UPLOAD → SHEET to activate multi-sheet path
        stack.setCurrentIndex(WizardController.STEP_UPLOAD)
        wizard.on_proximo()  # goes to STEP_SHEET, sets _multi_sheet_path=True
        # Now advance to STEP_COLUMNS
        wizard.on_proximo()

        # At STEP_COLUMNS with multi-sheet path active
        assert stack.currentIndex() == WizardController.STEP_COLUMNS
        n, total = wizard._step_display_number()
        assert total == 6
        assert n == 4

    def test_wizard_reiniciar_mutates_session_in_place(
        self,
        qtbot,  # noqa: ANN001
        stack: QStackedWidget,
        navbar: NavBar,
        step_label: QLabel,
    ) -> None:
        """reiniciar() must mutate session fields to None, NOT replace the object."""
        session = SessionModel()
        session.output_type = "caderno"
        session.source_path = pathlib.Path("sintetico_teste.xlsx")
        original_id = id(session)

        wizard = WizardController(session, stack, navbar, step_label)
        wizard.reiniciar()

        # Object identity preserved — same SessionModel instance
        assert id(wizard._session) == original_id
        # Fields reset to None
        assert session.output_type is None
        assert session.source_path is None
        # Stack returned to STEP_TYPE
        assert stack.currentIndex() == WizardController.STEP_TYPE

    def test_wizard_proximo_at_step_columns_starts_dry_run_worker(
        self,
        qtbot,  # noqa: ANN001
        stack: QStackedWidget,
        navbar: NavBar,
        step_label: QLabel,
        tmp_path: pathlib.Path,
        monkeypatch,  # noqa: ANN001
    ) -> None:
        """on_proximo at STEP_COLUMNS must construct PipelineWorker with output_path=None."""
        session = SessionModel()
        session.source_path = tmp_path / "sintetico_teste.xlsx"
        session.output_type = "caderno"

        captured_kwargs: dict = {}

        # Patch PipelineWorker in wizard module to capture call args
        class FakeWorker:
            progress = MagicMock()
            finished = MagicMock()
            error = MagicMock()
            cancelled = MagicMock()

            def __init__(self, source, output_type, output_path, **kwargs):  # noqa: ANN001
                captured_kwargs["source"] = source
                captured_kwargs["output_type"] = output_type
                captured_kwargs["output_path"] = output_path

            def start(self):  # noqa: ANN201
                pass

            def progress_connect(self, cb):  # noqa: ANN001, ANN201
                pass

        monkeypatch.setattr("eleitorum.ui.wizard.PipelineWorker", FakeWorker)

        wizard = WizardController(session, stack, navbar, step_label)
        stack.setCurrentIndex(WizardController.STEP_COLUMNS)
        wizard.on_proximo()

        # Dry-run: output_path must be None
        assert captured_kwargs.get("output_path") is None

    def test_wizard_save_dialog_rejects_same_as_input_path(
        self,
        qtbot,  # noqa: ANN001
        stack: QStackedWidget,
        navbar: NavBar,
        step_label: QLabel,
        tmp_path: pathlib.Path,
        monkeypatch,  # noqa: ANN001
    ) -> None:
        """Save dialog must show QMessageBox.warning and re-open when output==input."""
        # Input path as .csv so that the same-as-input check triggers correctly
        # (wizard enforces .csv extension before the collision check)
        input_path = tmp_path / "sintetico_entrada.csv"
        output_path_different = str(tmp_path / "sintetico_saida.csv")

        session = SessionModel()
        session.source_path = input_path
        session.output_type = "caderno"

        warning_calls: list = []
        get_save_calls: list = []

        # First call returns same-as-input path, second returns a different valid path
        def fake_get_save(parent, title, start, filter_):  # noqa: ANN001
            get_save_calls.append(1)
            if len(get_save_calls) == 1:
                # Return the input path — should be rejected
                return (str(input_path), "")
            # Second call — return a different path
            return (output_path_different, "")

        def fake_warning(parent, title, msg):  # noqa: ANN001
            warning_calls.append(msg)

        monkeypatch.setattr("eleitorum.ui.wizard.QFileDialog.getSaveFileName", fake_get_save)
        monkeypatch.setattr("eleitorum.ui.wizard.QMessageBox.warning", fake_warning)

        # Also patch PipelineWorker to avoid actually starting a thread
        class FakeWorker:
            progress = MagicMock()
            finished = MagicMock()
            error = MagicMock()
            cancelled = MagicMock()

            def __init__(self, **kwargs):  # noqa: ANN001
                pass

            def start(self):  # noqa: ANN201
                pass

        monkeypatch.setattr("eleitorum.ui.wizard.PipelineWorker", FakeWorker)

        wizard = WizardController(session, stack, navbar, step_label)
        stack.setCurrentIndex(WizardController.STEP_PREVIEW)
        wizard._on_preview_save_clicked()

        # QMessageBox.warning called once (for the first same-as-input attempt)
        assert len(warning_calls) == 1
        # QFileDialog.getSaveFileName called twice (first rejected, second accepted)
        assert len(get_save_calls) == 2
