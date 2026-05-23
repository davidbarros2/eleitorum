"""MainWindow QMainWindow host for the EleitorUM wizard (APP-01, APP-03, APP-04, APP-14).

Responsibilities:
  - Window sizing, centering on primary screen (APP-03)
  - QSettings-based geometry persistence/restore (APP-04)
  - Menu bar: Ficheiro, Ver, Ajuda (APP-14)
  - First-run WelcomeDialog gate (APP-16)
  - Theme toggle via Ver menu (APP-11, APP-12)
  - WizardController + QStackedWidget + NavBar assembly
  - quit_requested signal → QApplication.quit

QSettings discipline (RESEARCH.md Pitfall 2): every QSettings.value() call
passes ``type=bool`` or ``type=str`` to avoid the silent string-instead-of-bool
roundtrip bug.

Security note (T-02-06-02): QSettings.value() with ``type=bool`` coerces
tampered/invalid registry values to False per Qt semantics.
"""

from __future__ import annotations

import pathlib

from PySide6.QtCore import QSettings
from PySide6.QtGui import QAction, QIcon
from PySide6.QtWidgets import (
    QApplication,
    QLabel,
    QMainWindow,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from eleitorum.config import APP_NAME
from eleitorum.ui.dialogs import AboutDialog, WelcomeDialog
from eleitorum.ui.session import SessionModel
from eleitorum.ui.strings import (
    MENU_BOAS_VINDAS,
    MENU_FILE,
    MENU_HELP,
    MENU_REINICIAR,
    MENU_SAIR,
    MENU_SOBRE,
    MENU_TEMA_CLARO,
    MENU_TEMA_ESCURO,
    MENU_VIEW,
    STEP_INDICATOR,
)
from eleitorum.ui.theme import apply_theme
from eleitorum.ui.widgets.navbar import NavBar
from eleitorum.ui.wizard import WizardController


class MainWindow(QMainWindow):
    """Main application window hosting the EleitorUM wizard (APP-01, APP-03, APP-04, APP-14).

    On first launch (QSettings ``app/first_run_shown`` == False) shows the
    WelcomeDialog modally after the window is constructed.
    """

    def __init__(self) -> None:
        super().__init__()

        # QSettings (scoped to organizationName/applicationName set in create_app)
        self._settings = QSettings()

        # Shared wizard session state — one instance per session
        self._session = SessionModel()

        # Core window setup
        self._setup_window()

        # Build central widget with step indicator, stack, and navbar
        self._setup_central_widget()

        # Wire wizard controller
        self._setup_wizard()

        # Menu bar
        self._setup_menu()

        # Restore window geometry from QSettings (noop on first launch)
        self._restore_geometry()

        # First-run welcome dialog gate
        self._check_first_run()

    # ------------------------------------------------------------------
    # Window setup
    # ------------------------------------------------------------------

    def _setup_window(self) -> None:
        """Configure window title, icon, size, and position."""
        self.setWindowTitle(APP_NAME)

        # Set window icon (best-effort — icon.svg may not exist yet)
        icon_path = pathlib.Path(__file__).parent.parent / "resources" / "icon.svg"
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))

        # Size constraints (APP-03)
        self.setMinimumSize(600, 500)
        self.resize(900, 650)

        # Center on primary screen (APP-03)
        screen = QApplication.primaryScreen()
        if screen is not None:
            screen_geom = screen.availableGeometry()
            fg = self.frameGeometry()
            fg.moveCenter(screen_geom.center())
            self.move(fg.topLeft())

    def _setup_central_widget(self) -> None:
        """Build the central QWidget containing step indicator, stack, and NavBar."""
        central = QWidget()
        self.setCentralWidget(central)

        layout = QVBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Step indicator label — WizardController updates this on every navigation
        self._step_label = QLabel(STEP_INDICATOR.format(n=1, total=5))
        self._step_label.setObjectName("stepIndicator")
        layout.addWidget(self._step_label)

        # Stacked widget — WizardController inserts all 7 step pages
        self._stack = QStackedWidget()
        layout.addWidget(self._stack, stretch=1)

        # NavBar footer
        self._navbar = NavBar()
        layout.addWidget(self._navbar)

    def _setup_wizard(self) -> None:
        """Construct WizardController and connect quit_requested to app quit."""
        self._wizard = WizardController(
            session=self._session,
            stack=self._stack,
            navbar=self._navbar,
            step_label=self._step_label,
            parent=self,
        )
        self._wizard.quit_requested.connect(QApplication.quit)

    # ------------------------------------------------------------------
    # Menu bar (APP-14)
    # ------------------------------------------------------------------

    def _setup_menu(self) -> None:
        """Build the menu bar with Ficheiro, Ver, Ajuda menus."""
        menu_bar = self.menuBar()

        # --- Ficheiro ---
        ficheiro = menu_bar.addMenu(MENU_FILE)

        reiniciar_action = QAction(MENU_REINICIAR, self)
        reiniciar_action.triggered.connect(self._wizard.reiniciar)
        ficheiro.addAction(reiniciar_action)

        sair_action = QAction(MENU_SAIR, self)
        sair_action.triggered.connect(self.close)
        ficheiro.addAction(sair_action)

        # --- Ver ---
        ver = menu_bar.addMenu(MENU_VIEW)

        # Label reflects the opposite of the current theme (click to switch)
        current_theme = self._settings.value("app/theme", "light", type=str)
        toggle_label = MENU_TEMA_ESCURO if current_theme == "light" else MENU_TEMA_CLARO
        self._theme_action = QAction(toggle_label, self)
        self._theme_action.triggered.connect(self._on_toggle_theme)
        ver.addAction(self._theme_action)

        # --- Ajuda ---
        ajuda = menu_bar.addMenu(MENU_HELP)

        boas_vindas_action = QAction(MENU_BOAS_VINDAS, self)
        boas_vindas_action.triggered.connect(lambda: WelcomeDialog(self).exec())
        ajuda.addAction(boas_vindas_action)

        sobre_action = QAction(MENU_SOBRE, self)
        sobre_action.triggered.connect(lambda: AboutDialog(self).exec())
        ajuda.addAction(sobre_action)

    # ------------------------------------------------------------------
    # Theme toggle (APP-11, APP-12)
    # ------------------------------------------------------------------

    def _on_toggle_theme(self) -> None:
        """Toggle between light and dark themes; persist to QSettings."""
        current = self._settings.value("app/theme", "light", type=str)
        new_theme = "dark" if current == "light" else "light"
        apply_theme(new_theme)
        self._settings.setValue("app/theme", new_theme)

        # Update menu label to reflect the new opposite
        self._theme_action.setText(
            MENU_TEMA_ESCURO if new_theme == "light" else MENU_TEMA_CLARO
        )

    # ------------------------------------------------------------------
    # Geometry persistence (APP-04)
    # ------------------------------------------------------------------

    def _restore_geometry(self) -> None:
        """Restore window geometry from QSettings if available."""
        geom = self._settings.value("window/geometry", None, type=bytes)
        if geom:
            self.restoreGeometry(geom)
        state = self._settings.value("window/state", None, type=bytes)
        if state:
            self.restoreState(state)

    def closeEvent(self, event) -> None:  # type: ignore[override]
        """Persist window geometry and state before closing (APP-04)."""
        self._settings.setValue("window/geometry", self.saveGeometry())
        self._settings.setValue("window/state", self.saveState())
        super().closeEvent(event)

    # ------------------------------------------------------------------
    # First-run welcome (APP-16)
    # ------------------------------------------------------------------

    def _check_first_run(self) -> None:
        """Show WelcomeDialog if first_run_shown flag is not set in QSettings.

        Security note (T-02-06-02): type=bool ensures tampered registry values
        coerce to False (triggering the welcome dialog) rather than crashing.
        """
        shown = self._settings.value("app/first_run_shown", False, type=bool)
        if not shown:
            WelcomeDialog(self).exec()
            self._settings.setValue("app/first_run_shown", True)
