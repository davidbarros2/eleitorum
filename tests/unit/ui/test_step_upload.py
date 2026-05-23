"""Smoke tests for StepUpload — Step 2 file upload (WIZ-02).

All test data is synthetic per Eleitorum.md §14.1 (no real personal data).
"""
from __future__ import annotations

import pathlib

import openpyxl
import pytest

from eleitorum.ui.session import SessionModel
from eleitorum.ui.strings import BTN_ESCOLHER_FICHEIRO, ERR_UNSUPPORTED_EXT
from eleitorum.ui.steps.step_upload import StepUpload


def _make_synthetic_xlsx(path: pathlib.Path) -> pathlib.Path:
    """Create a minimal synthetic XLSX file for testing."""
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append(["No Mec.", "Nome Completo Teste"])
    ws.append(["A001", "João Silva Teste"])
    wb.save(str(path))
    return path


class TestStepUpload:
    """Requirement: WIZ-02 — file upload step."""

    def test_step_upload_constructs(self, qtbot) -> None:
        """StepUpload constructs with DropZone, button, file label, error label."""
        from PySide6.QtWidgets import QLabel, QPushButton
        from eleitorum.ui.widgets.drop_zone import DropZone

        session = SessionModel()
        step = StepUpload(session=session)
        qtbot.addWidget(step)

        # Check DropZone present
        assert hasattr(step, "_drop_zone")
        assert isinstance(step._drop_zone, DropZone)

        # Check choose button with correct text
        assert hasattr(step, "_choose_btn")
        assert isinstance(step._choose_btn, QPushButton)
        assert step._choose_btn.text() == BTN_ESCOLHER_FICHEIRO

        # Check file name label (initially empty)
        assert hasattr(step, "_file_name_label")
        assert isinstance(step._file_name_label, QLabel)
        assert step._file_name_label.text() == ""

        # Check inline error label (initially hidden)
        assert hasattr(step, "_error_label")
        assert isinstance(step._error_label, QLabel)
        assert step._error_label.isVisible() is False

    def test_step_upload_is_complete_false_initially(self, qtbot) -> None:
        """is_complete() is False when session.source_path is None."""
        session = SessionModel()
        step = StepUpload(session=session)
        qtbot.addWidget(step)

        assert step.is_complete() is False

    def test_step_upload_valid_drop_sets_session(self, qtbot, tmp_path) -> None:
        """Valid xlsx drop sets session.source_path and updates file name label."""
        xlsx_path = _make_synthetic_xlsx(tmp_path / "sintetico_teste.xlsx")
        session = SessionModel()
        step = StepUpload(session=session)
        qtbot.addWidget(step)

        step._on_file_received(str(xlsx_path))

        assert session.source_path == xlsx_path
        assert step._file_name_label.text() == "sintetico_teste.xlsx"

    def test_step_upload_valid_drop_queries_list_sheets(self, qtbot, tmp_path) -> None:
        """Valid xlsx drop populates session.sheets (list of SheetInfo)."""
        xlsx_path = _make_synthetic_xlsx(tmp_path / "sintetico_teste.xlsx")
        session = SessionModel()
        step = StepUpload(session=session)
        qtbot.addWidget(step)

        step._on_file_received(str(xlsx_path))

        # session.sheets is set to a list (may be empty for single-sheet)
        assert session.sheets is not None
        assert isinstance(session.sheets, list)

    def test_step_upload_unsupported_extension_shows_inline_error(
        self, qtbot, tmp_path
    ) -> None:
        """Unsupported extension shows inline error, session.source_path stays None."""
        png_path = tmp_path / "teste.png"
        png_path.write_bytes(b"fake image data")
        session = SessionModel()
        step = StepUpload(session=session)
        qtbot.addWidget(step)

        step._on_file_received(str(png_path))

        assert step._error_label.isVisible() is True
        assert ".png" in step._error_label.text()
        assert session.source_path is None

    def test_step_upload_choose_button_opens_dialog(self, qtbot, tmp_path, monkeypatch) -> None:
        """Choosing via dialog triggers _on_file_received with the selected path."""
        xlsx_path = _make_synthetic_xlsx(tmp_path / "sintetico_dialog_teste.xlsx")
        session = SessionModel()
        step = StepUpload(session=session)
        qtbot.addWidget(step)

        # Monkeypatch the dialog to return the synthetic file path
        monkeypatch.setattr(
            "eleitorum.ui.steps.step_upload.QFileDialog.getOpenFileName",
            lambda *a, **k: (str(xlsx_path), ""),
        )

        step._on_choose_clicked()

        assert session.source_path == xlsx_path

    def test_step_upload_inline_error_clears_on_next_attempt(
        self, qtbot, tmp_path
    ) -> None:
        """After an error, a subsequent valid file clears the error label."""
        png_path = tmp_path / "teste_erro.png"
        png_path.write_bytes(b"fake image data")
        xlsx_path = _make_synthetic_xlsx(tmp_path / "sintetico_teste.xlsx")
        session = SessionModel()
        step = StepUpload(session=session)
        qtbot.addWidget(step)

        # First: bad file → error shown
        step._on_file_received(str(png_path))
        assert step._error_label.isVisible() is True

        # Then: valid file → error hidden
        step._on_file_received(str(xlsx_path))
        assert step._error_label.isVisible() is False
