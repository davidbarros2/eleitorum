"""Smoke tests for eleitorum.ui.dialogs — WelcomeDialog and AboutDialog (APP-15, APP-16).

Tests verify:
- WelcomeDialog is modal
- WelcomeDialog has a "Começar" QPushButton that calls dialog.accept()
- AboutDialog shows APP_NAME and __version__ in a QLabel
- AboutDialog has a QLabel with openExternalLinks() == True (repo link)
- AboutDialog shows MIT license text
"""

from __future__ import annotations

from PySide6.QtWidgets import QLabel, QPushButton

from eleitorum.config import APP_NAME
from eleitorum.ui.strings import BTN_COMECAR
from eleitorum.version import __version__


class TestWelcomeDialog:
    """Tests for WelcomeDialog (APP-16, D-02)."""

    def test_welcome_dialog_is_modal(self, qtbot) -> None:  # noqa: ANN001
        """WelcomeDialog must have setModal(True)."""
        from eleitorum.ui.dialogs import WelcomeDialog  # noqa: PLC0415

        dialog = WelcomeDialog(None)
        qtbot.addWidget(dialog)
        assert dialog.isModal() is True

    def test_welcome_dialog_has_comecar_button(self, qtbot) -> None:  # noqa: ANN001
        """WelcomeDialog must have a QPushButton with BTN_COMECAR text.

        Clicking it must call dialog.accept() — verified by checking dialog result
        after triggering the button click.
        """
        from eleitorum.ui.dialogs import WelcomeDialog  # noqa: PLC0415

        dialog = WelcomeDialog(None)
        qtbot.addWidget(dialog)
        dialog.show()
        qtbot.waitExposed(dialog)

        # Find the Começar button
        buttons = dialog.findChildren(QPushButton)
        comecar_btn = next((b for b in buttons if b.text() == BTN_COMECAR), None)
        assert comecar_btn is not None, f"No button with text '{BTN_COMECAR}' found"

        # Clicking the button should accept the dialog
        comecar_btn.click()

        # After accept(), QDialog.Accepted == 1
        from PySide6.QtWidgets import QDialog  # noqa: PLC0415

        assert dialog.result() == QDialog.DialogCode.Accepted


class TestAboutDialog:
    """Tests for AboutDialog (APP-15)."""

    def test_about_dialog_shows_app_name_and_version(self, qtbot) -> None:  # noqa: ANN001
        """AboutDialog must contain a QLabel with both APP_NAME and __version__."""
        from eleitorum.ui.dialogs import AboutDialog  # noqa: PLC0415

        dialog = AboutDialog(None)
        qtbot.addWidget(dialog)
        dialog.show()
        qtbot.waitExposed(dialog)

        labels = dialog.findChildren(QLabel)
        texts = [lbl.text() for lbl in labels]

        # Find a label that contains both the app name and version
        heading_match = any(
            APP_NAME in text and __version__ in text
            for text in texts
        )
        assert heading_match, (
            f"No QLabel found containing both '{APP_NAME}' and '{__version__}'. "
            f"Labels found: {texts}"
        )

    def test_about_dialog_repo_link_opens_externally(self, qtbot) -> None:  # noqa: ANN001
        """AboutDialog must contain a QLabel with openExternalLinks() == True."""
        from eleitorum.ui.dialogs import AboutDialog  # noqa: PLC0415

        dialog = AboutDialog(None)
        qtbot.addWidget(dialog)
        dialog.show()
        qtbot.waitExposed(dialog)

        labels = dialog.findChildren(QLabel)
        external_link_labels = [lbl for lbl in labels if lbl.openExternalLinks()]

        assert external_link_labels, "No QLabel with openExternalLinks()==True found in AboutDialog"

    def test_about_dialog_shows_mit_license(self, qtbot) -> None:  # noqa: ANN001
        """AboutDialog must contain a QLabel whose text contains 'MIT'."""
        from eleitorum.ui.dialogs import AboutDialog  # noqa: PLC0415

        dialog = AboutDialog(None)
        qtbot.addWidget(dialog)
        dialog.show()
        qtbot.waitExposed(dialog)

        labels = dialog.findChildren(QLabel)
        texts = [lbl.text() for lbl in labels]

        mit_match = any("MIT" in text for text in texts)
        assert mit_match, f"No QLabel containing 'MIT' found. Labels: {texts}"

    def test_about_dialog_is_modal(self, qtbot) -> None:  # noqa: ANN001
        """AboutDialog must be modal (setModal(True))."""
        from eleitorum.ui.dialogs import AboutDialog  # noqa: PLC0415

        dialog = AboutDialog(None)
        qtbot.addWidget(dialog)
        assert dialog.isModal() is True
