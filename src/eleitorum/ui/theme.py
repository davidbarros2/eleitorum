"""QSS theme constants and functions for EleitorUM (APP-07, APP-08, APP-09, APP-10, APP-11, APP-12).

LIGHT_QSS and DARK_QSS are the only two theming artifacts; switching themes
calls apply_theme() which sets the stylesheet on QApplication.instance().

IMPORTANT: Fusion style MUST be set via app.setStyle('Fusion') BEFORE
apply_theme() is called — see app.py. Without Fusion, some QSS properties
(e.g. QProgressBar::chunk, QMenuBar) are overridden by platform native styles
on Windows (RESEARCH.md Pitfall §1).

Security note (T-02-02-02): apply_theme() ignores all values except 'dark' —
any other string falls back to LIGHT_QSS. The theme string is NEVER
concatenated into the QSS itself; callers cannot inject arbitrary QSS.
"""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication

# ---------------------------------------------------------------------------
# Light theme  (D-06 — background #FAFAFA | surface #FFFFFF | accent #a21a1c)
# ---------------------------------------------------------------------------

LIGHT_QSS: str = """
/* === EleitorUM LIGHT THEME (D-06) ===
   Background  #FAFAFA  |  Surface    #FFFFFF  |  Accent      #a21a1c
   Text        #1A1A1A  |  Muted      #878787  |  Border      #E5E5E5
   AccentHover #8a1618  |  Success    #2E7D32  |  Warning     #ED6C02
   Focus ring  #a21a1c  2px solid                              */

/* --- Base ---------------------------------------------------------------- */
QWidget {
    background-color: #FAFAFA;
    color: #1A1A1A;
    font-family: Inter, "Segoe UI", sans-serif;
    font-size: 14px;
}

QMainWindow {
    background-color: #FAFAFA;
}

/* --- Buttons ------------------------------------------------------------- */
QPushButton {
    background-color: #FFFFFF;
    color: #1A1A1A;
    border: 1px solid #E5E5E5;
    border-radius: 4px;
    padding: 8px 16px;
    font-size: 13px;
    font-weight: 600;
    min-width: 100px;
}
QPushButton:hover {
    background-color: #F5F5F5;
    border-color: #878787;
}
QPushButton:focus {
    border: 2px solid #a21a1c;
    outline: none;
}
QPushButton:disabled {
    background-color: #F5F5F5;
    color: #878787;
    border-color: #E5E5E5;
}
QPushButton#primary {
    background-color: #a21a1c;
    color: #FFFFFF;
    border: none;
}
QPushButton#primary:hover {
    background-color: #8a1618;
}
QPushButton#primary:focus {
    border: 2px solid #1A1A1A;
    outline: none;
}
QPushButton#primary:disabled {
    background-color: #E5E5E5;
    color: #878787;
}

/* --- Labels -------------------------------------------------------------- */
QLabel {
    background-color: transparent;
    color: #1A1A1A;
}
QLabel#stepTitle {
    font-size: 18px;
    font-weight: 600;
    color: #1A1A1A;
}
QLabel#displayHeading {
    font-size: 28px;
    font-weight: 600;
    color: #1A1A1A;
}
QLabel#mutedText {
    color: #878787;
    font-size: 13px;
}

/* --- Input widgets ------------------------------------------------------- */
QLineEdit {
    background-color: #FFFFFF;
    color: #1A1A1A;
    border: 1px solid #E5E5E5;
    border-radius: 4px;
    padding: 6px 8px;
}
QLineEdit:focus {
    border: 2px solid #a21a1c;
    outline: none;
}

QComboBox {
    background-color: #FFFFFF;
    color: #1A1A1A;
    border: 1px solid #E5E5E5;
    border-radius: 4px;
    padding: 6px 8px;
    min-width: 120px;
}
QComboBox:focus {
    border: 2px solid #a21a1c;
    outline: none;
}
QComboBox::drop-down {
    border: none;
}

/* --- List/Table widgets -------------------------------------------------- */
QListWidget {
    background-color: #FFFFFF;
    color: #1A1A1A;
    border: 1px solid #E5E5E5;
    border-radius: 4px;
    outline: none;
}
QListWidget::item:selected {
    background-color: #a21a1c;
    color: #FFFFFF;
}
QListWidget::item:focus {
    border: 2px solid #a21a1c;
}

QTableWidget {
    background-color: #FFFFFF;
    color: #1A1A1A;
    border: 1px solid #E5E5E5;
    gridline-color: #E5E5E5;
    outline: none;
}
QTableWidget::item:selected {
    background-color: #a21a1c;
    color: #FFFFFF;
}

/* --- Text edit ----------------------------------------------------------- */
QTextEdit {
    background-color: #FFFFFF;
    color: #1A1A1A;
    border: 1px solid #E5E5E5;
    border-radius: 4px;
}
QTextEdit:focus {
    border: 2px solid #a21a1c;
    outline: none;
}

/* --- Progress bar -------------------------------------------------------- */
QProgressBar {
    background-color: #E5E5E5;
    border: none;
    border-radius: 4px;
    height: 8px;
    text-align: center;
}
QProgressBar::chunk {
    background-color: #a21a1c;
    border-radius: 4px;
}

/* --- Menu bar ------------------------------------------------------------ */
QMenuBar {
    background-color: #FAFAFA;
    color: #1A1A1A;
    border-bottom: 1px solid #E5E5E5;
}
QMenuBar::item:selected {
    background-color: #E5E5E5;
}
QMenu {
    background-color: #FFFFFF;
    color: #1A1A1A;
    border: 1px solid #E5E5E5;
}
QMenu::item:selected {
    background-color: #a21a1c;
    color: #FFFFFF;
}

/* --- Card frame ---------------------------------------------------------- */
QFrame#card {
    background-color: #FFFFFF;
    border: 1px solid #E5E5E5;
    border-radius: 8px;
}

/* --- OptionCard (step 1 selection cards) --------------------------------- */
OptionCard {
    background-color: #FFFFFF;
    border: 1px solid #E5E5E5;
    border-radius: 8px;
    padding: 24px;
}
OptionCard[selected="true"] {
    border: 2px solid #a21a1c;
    background-color: #FFFFFF;
}
OptionCard:focus {
    border: 2px solid #a21a1c;
    outline: none;
}

/* --- DropZone (step 2 file upload area) ---------------------------------- */
DropZone {
    background-color: #FFFFFF;
    border: 1px dashed #E5E5E5;
    border-radius: 4px;
}
DropZone[drag_active="true"] {
    border: 2px solid #a21a1c;
    background-color: #FFF8F8;
}

/* --- Dialog -------------------------------------------------------------- */
QDialog {
    background-color: #FAFAFA;
    color: #1A1A1A;
}
"""

# ---------------------------------------------------------------------------
# Dark theme  (D-06 — background #1A1A1A | surface #262626 | accent #C73E40)
# ---------------------------------------------------------------------------

DARK_QSS: str = """
/* === EleitorUM DARK THEME (D-06) ===
   Background  #1A1A1A  |  Surface    #262626  |  Accent      #C73E40
   Text        #F5F5F5  |  Muted      #A3A3A3  |  Border      #3A3A3A
   AccentHover #D85759  |  Success    #66BB6A  |  Warning     #FFA726
   Focus ring  #C73E40  2px solid                              */

/* --- Base ---------------------------------------------------------------- */
QWidget {
    background-color: #1A1A1A;
    color: #F5F5F5;
    font-family: Inter, "Segoe UI", sans-serif;
    font-size: 14px;
}

QMainWindow {
    background-color: #1A1A1A;
}

/* --- Buttons ------------------------------------------------------------- */
QPushButton {
    background-color: #262626;
    color: #F5F5F5;
    border: 1px solid #3A3A3A;
    border-radius: 4px;
    padding: 8px 16px;
    font-size: 13px;
    font-weight: 600;
    min-width: 100px;
}
QPushButton:hover {
    background-color: #3A3A3A;
    border-color: #A3A3A3;
}
QPushButton:focus {
    border: 2px solid #C73E40;
    outline: none;
}
QPushButton:disabled {
    background-color: #262626;
    color: #A3A3A3;
    border-color: #3A3A3A;
}
QPushButton#primary {
    background-color: #C73E40;
    color: #F5F5F5;
    border: none;
}
QPushButton#primary:hover {
    background-color: #D85759;
}
QPushButton#primary:focus {
    border: 2px solid #F5F5F5;
    outline: none;
}
QPushButton#primary:disabled {
    background-color: #3A3A3A;
    color: #A3A3A3;
}

/* --- Labels -------------------------------------------------------------- */
QLabel {
    background-color: transparent;
    color: #F5F5F5;
}
QLabel#stepTitle {
    font-size: 18px;
    font-weight: 600;
    color: #F5F5F5;
}
QLabel#displayHeading {
    font-size: 28px;
    font-weight: 600;
    color: #F5F5F5;
}
QLabel#mutedText {
    color: #A3A3A3;
    font-size: 13px;
}

/* --- Input widgets ------------------------------------------------------- */
QLineEdit {
    background-color: #262626;
    color: #F5F5F5;
    border: 1px solid #3A3A3A;
    border-radius: 4px;
    padding: 6px 8px;
}
QLineEdit:focus {
    border: 2px solid #C73E40;
    outline: none;
}

QComboBox {
    background-color: #262626;
    color: #F5F5F5;
    border: 1px solid #3A3A3A;
    border-radius: 4px;
    padding: 6px 8px;
    min-width: 120px;
}
QComboBox:focus {
    border: 2px solid #C73E40;
    outline: none;
}
QComboBox::drop-down {
    border: none;
}

/* --- List/Table widgets -------------------------------------------------- */
QListWidget {
    background-color: #262626;
    color: #F5F5F5;
    border: 1px solid #3A3A3A;
    border-radius: 4px;
    outline: none;
}
QListWidget::item:selected {
    background-color: #C73E40;
    color: #F5F5F5;
}
QListWidget::item:focus {
    border: 2px solid #C73E40;
}

QTableWidget {
    background-color: #262626;
    color: #F5F5F5;
    border: 1px solid #3A3A3A;
    gridline-color: #3A3A3A;
    outline: none;
}
QTableWidget::item:selected {
    background-color: #C73E40;
    color: #F5F5F5;
}

/* --- Text edit ----------------------------------------------------------- */
QTextEdit {
    background-color: #262626;
    color: #F5F5F5;
    border: 1px solid #3A3A3A;
    border-radius: 4px;
}
QTextEdit:focus {
    border: 2px solid #C73E40;
    outline: none;
}

/* --- Progress bar -------------------------------------------------------- */
QProgressBar {
    background-color: #3A3A3A;
    border: none;
    border-radius: 4px;
    height: 8px;
    text-align: center;
    color: #F5F5F5;
}
QProgressBar::chunk {
    background-color: #C73E40;
    border-radius: 4px;
}

/* --- Menu bar ------------------------------------------------------------ */
QMenuBar {
    background-color: #1A1A1A;
    color: #F5F5F5;
    border-bottom: 1px solid #3A3A3A;
}
QMenuBar::item:selected {
    background-color: #3A3A3A;
}
QMenu {
    background-color: #262626;
    color: #F5F5F5;
    border: 1px solid #3A3A3A;
}
QMenu::item:selected {
    background-color: #C73E40;
    color: #F5F5F5;
}

/* --- Card frame ---------------------------------------------------------- */
QFrame#card {
    background-color: #262626;
    border: 1px solid #3A3A3A;
    border-radius: 8px;
}

/* --- OptionCard (step 1 selection cards) --------------------------------- */
OptionCard {
    background-color: #262626;
    border: 1px solid #3A3A3A;
    border-radius: 8px;
    padding: 24px;
}
OptionCard[selected="true"] {
    border: 2px solid #C73E40;
    background-color: #262626;
}
OptionCard:focus {
    border: 2px solid #C73E40;
    outline: none;
}

/* --- DropZone (step 2 file upload area) ---------------------------------- */
DropZone {
    background-color: #262626;
    border: 1px dashed #3A3A3A;
    border-radius: 4px;
}
DropZone[drag_active="true"] {
    border: 2px solid #C73E40;
    background-color: #2A1A1B;
}

/* --- Dialog -------------------------------------------------------------- */
QDialog {
    background-color: #1A1A1A;
    color: #F5F5F5;
}
"""


# ---------------------------------------------------------------------------
# Theme functions
# ---------------------------------------------------------------------------


def apply_theme(theme: str) -> None:
    """Apply QSS theme to the running QApplication.

    Security note (T-02-02-02): any value other than 'dark' falls back to
    LIGHT_QSS. The theme string is never concatenated into the QSS.

    Args:
        theme: 'dark' selects DARK_QSS; any other value selects LIGHT_QSS.
    """
    qss = DARK_QSS if theme == "dark" else LIGHT_QSS
    app = QApplication.instance()
    if app is not None:
        app.setStyleSheet(qss)


def detect_system_theme() -> str:
    """Return 'light' or 'dark' based on the current system color scheme.

    Reads QApplication.instance().styleHints().colorScheme() (PySide6 6.5+).
    Both Qt.ColorScheme.Light AND Qt.ColorScheme.Unknown map to 'light'
    per D-06 fallback — only Dark explicitly maps to 'dark'.

    Returns:
        'dark' if the system reports a dark color scheme; 'light' otherwise.
    """
    app = QApplication.instance()
    if app is None:
        return "light"
    hints = app.styleHints()
    cs = hints.colorScheme()
    if cs == Qt.ColorScheme.Dark:
        return "dark"
    return "light"
