"""QApplication factory for EleitorUM (APP-01, APP-07–13, BRAND-01).

Creates the QApplication instance, sets Fusion style, loads Inter font via
QFontDatabase, and applies the initial theme from QSettings (or system
preference on first launch).  Called once from __main__.py.

Security note: no network calls; all font paths resolve against sys._MEIPASS
(PyInstaller) or __file__ (dev). sys._MEIPASS is read-only at runtime.

Requirements: APP-01 (standard window chrome), APP-07 (light theme),
APP-08 (dark theme), APP-09 (WCAG contrast), APP-10 (system theme detection),
APP-11 (instant theme toggle), APP-12 (theme persistence), APP-13 (Inter font),
BRAND-01 (APP_NAME constant).
"""

from __future__ import annotations

import pathlib
import sys

from PySide6.QtCore import QSettings
from PySide6.QtGui import QFont, QFontDatabase, QIcon
from PySide6.QtWidgets import QApplication

from eleitorum.config import APP_NAME
from eleitorum.ui.theme import apply_theme, detect_system_theme
from eleitorum.version import __version__


def create_app() -> QApplication:
    """Create and configure the QApplication instance.

    Sets applicationName, organizationName, applicationVersion, Fusion style,
    loads Inter font, and applies the initial theme (from QSettings or system).

    IMPORTANT: app.setStyle('Fusion') is called BEFORE apply_theme() — see
    RESEARCH.md Pitfall 1. The Fusion style is required for reliable QSS dark
    theme rendering on Windows 10/11 (the default Windows Vista style overrides
    QPalette with a forced light palette).

    Returns:
        The configured QApplication instance.
    """
    # Reuse an existing QApplication instance if one already exists (e.g. in tests)
    app = QApplication.instance() or QApplication(sys.argv)

    # Set application identity (used by QSettings to scope storage)
    app.setApplicationName(APP_NAME)
    app.setOrganizationName(APP_NAME)
    app.setApplicationVersion(__version__)

    # CRITICAL: set Fusion style BEFORE any setStyleSheet call (Pitfall 1)
    app.setStyle("Fusion")

    # Load Inter font from resources/; falls back silently to Segoe UI
    _load_inter_font(app)

    # Apply initial theme — read from QSettings if available, else detect system
    theme = _read_or_detect_theme()
    apply_theme(theme)

    return app


def _read_or_detect_theme() -> str:
    """Return the persisted theme or the system-detected theme.

    QSettings is already scoped via applicationName/organizationName set on the
    QApplication instance.  Uses ``type=str`` to avoid silent None on missing key
    (RESEARCH.md Pitfall 2).

    Returns:
        'dark' or 'light'.
    """
    settings = QSettings()
    stored = settings.value("app/theme", "", type=str)
    if stored in ("dark", "light"):
        return stored
    return detect_system_theme()


def _load_inter_font(app: QApplication) -> None:  # noqa: ARG001
    """Load Inter .ttf files from the resources/fonts/Inter/ directory.

    Resolves the base path via sys._MEIPASS (PyInstaller bundle) or
    __file__.parent.parent (development / editable install).

    On failure (font file not found, -1 returned by addApplicationFont), logs a
    warning and falls back to Segoe UI.  Font failure is non-fatal — the
    application continues with the system UI font.

    Args:
        app: The QApplication instance (used to set the application font).
    """
    # Resolve bundle root: PyInstaller sets sys._MEIPASS; in dev use package root
    # app.py lives in src/eleitorum/ui/; resources/ is in src/eleitorum/
    base = pathlib.Path(getattr(sys, "_MEIPASS", str(pathlib.Path(__file__).parent.parent)))
    fonts_dir = base / "resources" / "fonts" / "Inter"

    loaded = 0
    if fonts_dir.exists():
        for ttf in sorted(fonts_dir.glob("*.ttf")):
            result = QFontDatabase.addApplicationFont(str(ttf))
            if result != -1:
                loaded += 1
            else:
                # Non-fatal: log to stderr only (no user-visible message)
                print(  # noqa: T201
                    f"Warning: failed to load Inter font file: {ttf.name}",
                    file=sys.stderr,
                )

    # Set app default font: Inter if loaded, else Segoe UI fallback
    font = QFont("Inter" if loaded > 0 else "Segoe UI")
    font.setPointSize(14)
    app.setFont(font)

    # Set window icon globally (best-effort — SVG load failure is non-fatal)
    icon_path = base / "resources" / "icon.svg"
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))
