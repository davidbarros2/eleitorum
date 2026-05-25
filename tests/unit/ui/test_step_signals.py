"""Tests for completion_changed Signal on StepType, StepUpload, StepSheet.

Verifies that each step widget emits completion_changed at the right moments
so WizardController can reactively update the NavBar (WIZ-01, WIZ-02, WIZ-03).

All test data is synthetic per Eleitorum.md §14.1 (no real personal data).
"""

from __future__ import annotations

import pathlib

import openpyxl
import pytest
from PySide6.QtWidgets import QListWidgetItem

from eleitorum.core.readers import SheetInfo
from eleitorum.ui.session import SessionModel
from eleitorum.ui.steps.step_sheet import StepSheet
from eleitorum.ui.steps.step_type import StepType
from eleitorum.ui.steps.step_upload import StepUpload


def _make_synthetic_xlsx(path: pathlib.Path) -> pathlib.Path:
    """Create a minimal synthetic XLSX file for testing."""
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append(["No Mec.", "Nome Completo Teste"])
    ws.append(["A001", "João Silva Teste"])
    wb.save(str(path))
    return path


class TestStepTypeCompletionChanged:
    """completion_changed signal on StepType (WIZ-01)."""

    def test_selecting_caderno_emits_completion_changed_once(self, qtbot) -> None:
        """After _on_selection('caderno'), completion_changed emitted exactly once."""
        session = SessionModel()
        step = StepType(session=session)
        qtbot.addWidget(step)

        with qtbot.waitSignal(step.completion_changed, timeout=1000) as blocker:
            step._on_selection("caderno")

        assert blocker.signal_triggered

    def test_selecting_elegiveis_emits_completion_changed_once(self, qtbot) -> None:
        """After _on_selection('elegiveis'), completion_changed emitted exactly once."""
        session = SessionModel()
        step = StepType(session=session)
        qtbot.addWidget(step)

        emissions: list[None] = []
        step.completion_changed.connect(lambda: emissions.append(None))

        step._on_selection("elegiveis")

        assert len(emissions) == 1


class TestStepUploadCompletionChanged:
    """completion_changed signal on StepUpload (WIZ-02)."""

    def test_valid_file_emits_completion_changed(self, qtbot, tmp_path) -> None:
        """After _on_file_received with valid path, completion_changed emitted."""
        xlsx_path = _make_synthetic_xlsx(tmp_path / "sintetico_teste.xlsx")
        session = SessionModel()
        step = StepUpload(session=session)
        qtbot.addWidget(step)

        with qtbot.waitSignal(step.completion_changed, timeout=1000):
            step._on_file_received(str(xlsx_path))

    def test_invalid_extension_does_not_emit_completion_changed(self, qtbot, tmp_path) -> None:
        """Invalid extension (early return) does NOT emit completion_changed."""
        png_path = tmp_path / "teste.png"
        png_path.write_bytes(b"fake image data")
        session = SessionModel()
        step = StepUpload(session=session)
        qtbot.addWidget(step)

        emissions: list[None] = []
        step.completion_changed.connect(lambda: emissions.append(None))

        step._on_file_received(str(png_path))

        assert len(emissions) == 0

    def test_eleitorumerror_path_emits_completion_changed(self, qtbot, tmp_path, monkeypatch) -> None:
        """EleitorumError path (clears source_path) emits completion_changed."""
        from eleitorum.core.errors import EleitorumError

        xlsx_path = _make_synthetic_xlsx(tmp_path / "sintetico_erro_teste.xlsx")

        def _raise_eleitorumerror(p):  # noqa: ANN001
            raise EleitorumError("Erro de teste sintético")

        # Monkeypatch list_sheets to raise EleitorumError
        monkeypatch.setattr(
            "eleitorum.ui.steps.step_upload.list_sheets",
            _raise_eleitorumerror,
        )

        session = SessionModel()
        step = StepUpload(session=session)
        qtbot.addWidget(step)

        with qtbot.waitSignal(step.completion_changed, timeout=1000):
            step._on_file_received(str(xlsx_path))

        # source_path should have been cleared
        assert session.source_path is None


class TestStepSheetCompletionChanged:
    """completion_changed signal on StepSheet (WIZ-03)."""

    def test_selecting_item_emits_completion_changed(self, qtbot) -> None:
        """After _on_selection_changed(current=item, previous=None), emits completion_changed."""
        session = SessionModel()
        session.sheets = [SheetInfo("Docentes", 247, False)]
        step = StepSheet(session=session)
        qtbot.addWidget(step)
        step.populate_from_session()

        with qtbot.waitSignal(step.completion_changed, timeout=1000):
            step._list.setCurrentRow(0)

    def test_deselecting_item_emits_completion_changed(self, qtbot) -> None:
        """After _on_selection_changed(current=None, previous=item), emits completion_changed."""
        session = SessionModel()
        session.sheets = [SheetInfo("Docentes", 247, False)]
        step = StepSheet(session=session)
        qtbot.addWidget(step)
        step.populate_from_session()

        # Select first
        step._list.setCurrentRow(0)

        emissions: list[None] = []
        step.completion_changed.connect(lambda: emissions.append(None))

        # Programmatically call _on_selection_changed with current=None
        step._on_selection_changed(None, step._list.item(0))

        assert len(emissions) == 1
