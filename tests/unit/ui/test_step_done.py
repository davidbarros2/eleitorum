"""Tests for StepDone wizard step widget (WIZ-07, WIZ-08, APP-19).

Verifies dual-state success/error widget, QDesktopServices folder opening,
restart/quit signal emission, and "e mais N erros" suffix for >20 failures.

All test data is synthetic (no real personal data per CLAUDE.md privacy constraint).
"""

from __future__ import annotations

import pathlib
import types
from unittest.mock import patch

import pytest
from PySide6.QtCore import QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import QStackedWidget

from eleitorum.core.errors import FailureRow
from eleitorum.ui.session import SessionModel


def _make_success_result(
    *,
    output_path: pathlib.Path | None = None,
    rows_processed: int = 42,
    transformations_applied: int = 5,
) -> types.SimpleNamespace:
    """Build a minimal success PipelineResult-like namespace."""
    return types.SimpleNamespace(
        success=True,
        output_path=output_path or pathlib.Path("/tmp/sintetico_teste.csv"),
        log_path=pathlib.Path("/tmp/sintetico_teste_LOG_.txt"),
        error_log_path=None,
        rows_processed=rows_processed,
        transformations_applied=transformations_applied,
        failures=[],
        log_entries=[],
        preview_rows=[],
        detection={},
    )


def _make_error_result(
    *,
    failures: list | None = None,
    error_log_path: pathlib.Path | None = None,
) -> types.SimpleNamespace:
    """Build a minimal error PipelineResult-like namespace."""
    return types.SimpleNamespace(
        success=False,
        output_path=None,
        log_path=None,
        error_log_path=error_log_path or pathlib.Path("/tmp/sintetico_ERRORS_.txt"),
        rows_processed=0,
        transformations_applied=0,
        failures=failures or [],
        log_entries=[],
        preview_rows=[],
        detection={},
    )


class TestStepDone:
    """Tests for StepDone (step 6 — dual-state success/error widget)."""

    @pytest.fixture()
    def session(self) -> SessionModel:
        return SessionModel()

    @pytest.fixture()
    def step(self, session: SessionModel, qtbot):
        from eleitorum.ui.steps.step_done import StepDone

        widget = StepDone(session)
        qtbot.addWidget(widget)
        widget.show()
        return widget

    def test_step_done_constructs_in_success_mode_by_default(self, step) -> None:
        """StepDone has a QStackedWidget with 2 pages; initial index 0 (success)."""
        assert hasattr(step, "_stack"), "_stack attribute missing"
        assert isinstance(step._stack, QStackedWidget)
        assert step._stack.count() == 2, f"Expected 2 pages, got {step._stack.count()}"
        assert step._stack.currentIndex() == 0, "Initial page should be success (index 0)"

    def test_step_done_show_success_populates_path(self, step) -> None:
        """show_success() populates path label and summary; switches to index 0."""
        result = _make_success_result(
            output_path=pathlib.Path("C:/temp/teste.csv"),
            rows_processed=100,
            transformations_applied=5,
        )
        step.show_success(result)

        assert step._stack.currentIndex() == 0
        # Path label should contain the filename
        assert hasattr(step, "_success_path_label")
        assert "teste.csv" in step._success_path_label.text()
        # Summary should contain the row count
        assert hasattr(step, "_success_summary")
        assert "100" in step._success_summary.text()
        assert "5" in step._success_summary.text()

    def test_step_done_show_error_switches_to_error_page(self, step) -> None:
        """show_error() switches stack to index 1 (error page)."""
        result = _make_error_result()
        step.show_error(result)
        assert step._stack.currentIndex() == 1

    def test_step_done_error_lists_first_20_failures(self, step) -> None:
        """With 25 failures, error text shows 20 lines + '…e mais 5 erros' suffix."""
        failures = [
            FailureRow(i, "mecanografico", f"F{i}", f"Erro sintetico {i}") for i in range(1, 26)
        ]
        result = _make_error_result(failures=failures)
        step.show_error(result)

        assert hasattr(step, "_error_text")
        text = step._error_text.toPlainText()
        lines = [l for l in text.split("\n") if l.strip()]
        # Should have 20 failure lines + 1 "e mais" line
        assert len(lines) == 21, (
            f"Expected 21 lines (20 failures + suffix), got {len(lines)}: {lines}"
        )
        assert "mais 5 erros" in text, f"'mais 5 erros' not found in: {text}"

    def test_step_done_open_folder_uses_QDesktopServices(self, step) -> None:
        """In success mode, clicking Abrir pasta calls QDesktopServices.openUrl."""
        result = _make_success_result(
            output_path=pathlib.Path("C:/temp/sintetico/teste.csv"),
        )
        step.show_success(result)

        called_urls = []

        with patch.object(QDesktopServices, "openUrl", side_effect=called_urls.append):
            step._on_open_folder_clicked()

        assert len(called_urls) == 1, "openUrl should be called once"
        # Should point to parent directory of output_path
        url = called_urls[0]
        assert isinstance(url, QUrl)
        # The URL should contain the parent folder path
        url_str = url.toLocalFile().replace("\\", "/")
        assert "sintetico" in url_str or "temp" in url_str, (
            f"Expected parent folder in URL: {url_str}"
        )

    def test_step_done_open_folder_in_error_mode_points_to_error_log(self, step) -> None:
        """In error mode, Abrir pasta opens error_log_path.parent."""
        result = _make_error_result(
            error_log_path=pathlib.Path("C:/logs/sintetico/_ERRORS_.txt"),
        )
        step.show_error(result)

        called_urls = []
        with patch.object(QDesktopServices, "openUrl", side_effect=called_urls.append):
            step._on_open_folder_clicked()

        assert len(called_urls) == 1
        url_str = called_urls[0].toLocalFile().replace("\\", "/")
        # Should point to parent folder of error_log_path (logs/sintetico/)
        assert "sintetico" in url_str or "logs" in url_str, (
            f"Expected error log parent in URL: {url_str}"
        )

    def test_step_done_processar_outro_emits_restart_signal(self, step, qtbot) -> None:
        """Clicking 'Processar outro ficheiro' emits restart_clicked signal."""
        assert hasattr(step, "restart_clicked"), "restart_clicked signal missing"

        # Find the restart button on the success page
        assert hasattr(step, "_success_restart_btn"), "_success_restart_btn missing"

        with qtbot.waitSignal(step.restart_clicked, timeout=1000):
            from PySide6.QtCore import Qt as _Qt

            qtbot.mouseClick(step._success_restart_btn, _Qt.MouseButton.LeftButton)

    def test_step_done_sair_emits_quit_signal(self, step, qtbot) -> None:
        """Clicking 'Sair' on success page emits quit_clicked signal."""
        assert hasattr(step, "quit_clicked"), "quit_clicked signal missing"
        assert hasattr(step, "_success_quit_btn"), "_success_quit_btn missing"

        with qtbot.waitSignal(step.quit_clicked, timeout=1000):
            from PySide6.QtCore import Qt as _Qt

            qtbot.mouseClick(step._success_quit_btn, _Qt.MouseButton.LeftButton)

    def test_step_done_error_mode_has_no_sair_button(self, step) -> None:
        """Error page has no Sair button (per UI-SPEC 'No Sair on error screen')."""
        # Error page is stack index 1 — get that page's widget
        error_page = step._stack.widget(1)
        assert error_page is not None, "Error page widget not found at stack index 1"

        from PySide6.QtWidgets import QPushButton

        # Find all QPushButtons on the error page only
        error_buttons = error_page.findChildren(QPushButton)
        button_texts = [btn.text() for btn in error_buttons]

        # "Sair" should NOT appear on the error page
        assert not any("Sair" in t for t in button_texts), (
            f"Found 'Sair' button on error page — UI-SPEC prohibits this. Buttons: {button_texts}"
        )
