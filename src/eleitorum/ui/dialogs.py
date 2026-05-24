"""WelcomeDialog and AboutDialog QDialog subclasses for EleitorUM (APP-15, APP-16).

WelcomeDialog:
  - Modal QDialog shown on first launch (APP-16).
  - Contains app name heading, PT-PT description + wizard outline, "Começar" button.
  - Re-opened via Ajuda → Boas-vindas… menu action.

AboutDialog:
  - Modal QDialog for Ajuda → Sobre… (APP-15).
  - Contains APP_NAME + version heading, PT-PT description, MIT license
    note, and repository link via QLabel.setOpenExternalLinks(True).

Security note (T-02-06-06): the repository link URL is a compile-time constant
sourced from strings.py. It is never concatenated from user input. Qt's
setOpenExternalLinks(True) delegates to the OS default browser — no shell
injection risk.
"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from eleitorum.config import APP_NAME
from eleitorum.ui.strings import (
    ABOUT_DESCRIPTION,
    ABOUT_LICENSE,
    ABOUT_REPO_LINK_LABEL,
    BTN_COMECAR,
    WELCOME_BODY,
    WELCOME_HEADING,
)
from eleitorum.version import __version__

# Repository URL — sourced from project metadata; constant, never user-derived
_REPO_URL: str = "https://github.com/davidbarros2/eleitorum"


class WelcomeDialog(QDialog):
    """First-run welcome dialog (APP-16, D-02).

    Shown modally on first application launch; re-opened via the
    Ajuda → Boas-vindas… menu item.  "Começar" button calls ``accept()``.

    The QSettings ``first_run_shown`` flag is managed by MainWindow, not here —
    this dialog is pure presentation with no persistence logic.
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setModal(True)
        self.setWindowTitle(WELCOME_HEADING)
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # App name heading
        heading = QLabel(WELCOME_HEADING)
        heading.setObjectName("displayHeading")
        heading.setWordWrap(True)
        layout.addWidget(heading)

        # PT-PT description + wizard outline
        body = QLabel(WELCOME_BODY)
        body.setWordWrap(True)
        body.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(body)

        layout.addStretch()

        # "Começar" primary action — closes the dialog
        comecar_btn = QPushButton(BTN_COMECAR)
        comecar_btn.setObjectName("primary")
        comecar_btn.clicked.connect(self.accept)
        layout.addWidget(comecar_btn)


class AboutDialog(QDialog):
    """About dialog showing app info and license (APP-15).

    Opened via Ajuda → Sobre… menu item.  Contains:
    - ``APP_NAME v__version__`` heading
    - PT-PT description (ABOUT_DESCRIPTION)
    - MIT license note
    - Repository link as clickable QLabel with setOpenExternalLinks(True)
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setModal(True)
        self.setWindowTitle(f"{APP_NAME} — Sobre")
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(12)

        # Heading: "APP_NAME version"
        heading = QLabel(f"{APP_NAME} {__version__}")
        heading.setObjectName("displayHeading")
        layout.addWidget(heading)

        # PT-PT short description
        description = QLabel(ABOUT_DESCRIPTION)
        description.setWordWrap(True)
        layout.addWidget(description)

        # MIT license note
        license_lbl = QLabel(ABOUT_LICENSE)
        license_lbl.setWordWrap(True)
        layout.addWidget(license_lbl)

        # Repository link — opens in default browser via Qt
        repo_link = QLabel(f'<a href="{_REPO_URL}">{ABOUT_REPO_LINK_LABEL}</a>')
        repo_link.setOpenExternalLinks(True)
        repo_link.setTextInteractionFlags(Qt.TextInteractionFlag.TextBrowserInteraction)
        layout.addWidget(repo_link)

        layout.addStretch()

        # Close button
        close_btn = QPushButton("Fechar")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)
