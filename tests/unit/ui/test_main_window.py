"""Smoke tests for eleitorum.ui.main_window — MainWindow (APP-01, APP-03, APP-04, APP-14, APP-16).

Tests verify:
- Minimum size (600, 500)
- Initial size (900, 650)
- Window title equals APP_NAME
- Menu bar has three top-level menus: Ficheiro, Ver, Ajuda
- Ficheiro menu has Reiniciar and Sair actions
- closeEvent persists geometry to QSettings
- First-run welcome dialog appears when first_run_shown is False
- Subsequent launches do NOT show welcome dialog when flag is True
- All self._settings.value() calls include type= keyword argument (AST check)

NOTE: Most tests patch WelcomeDialog to avoid blocking exec() calls during tests.
"""

from __future__ import annotations

import ast
import pathlib

import pytest
from PySide6.QtCore import QSettings
from PySide6.QtWidgets import QMenu

from eleitorum.config import APP_NAME
from eleitorum.ui.strings import MENU_FILE, MENU_HELP, MENU_VIEW


class _FakeWelcomeDialog:
    """Non-blocking WelcomeDialog stub for tests."""

    _exec_count = 0

    def __init__(self, parent=None) -> None:  # noqa: ANN001
        pass

    def exec(self) -> None:
        _FakeWelcomeDialog._exec_count += 1


@pytest.fixture(autouse=True)
def configure_qapp(qapp) -> None:  # noqa: ANN001
    """Ensure QApplication has applicationName/organizationName set for QSettings scoping.

    Without this, QSettings() in tests writes to an unscoped / wrong location
    and MainWindow._settings reads from a different bucket.
    """
    from eleitorum.config import APP_NAME  # noqa: PLC0415

    qapp.setApplicationName(APP_NAME)
    qapp.setOrganizationName(APP_NAME)


@pytest.fixture(autouse=True)
def patch_welcome_dialog(monkeypatch) -> None:  # noqa: ANN001
    """Patch WelcomeDialog in main_window to prevent blocking exec() in all tests."""
    _FakeWelcomeDialog._exec_count = 0
    monkeypatch.setattr("eleitorum.ui.main_window.WelcomeDialog", _FakeWelcomeDialog)


@pytest.fixture(autouse=True)
def isolated_qsettings() -> None:  # noqa: ANN001
    """Clear QSettings first_run_shown before each test to prevent state leakage."""
    # Set first_run_shown=True so the welcome dialog is NOT triggered in most tests
    # (patch_welcome_dialog overrides it anyway, but this prevents any dialog attempt)
    settings = QSettings()
    settings.setValue("app/first_run_shown", True)
    yield
    # Clean up
    settings.remove("window/geometry")
    settings.remove("window/state")


@pytest.fixture
def main_window(qtbot):  # noqa: ANN001
    """Create and return a MainWindow instance for testing."""
    from eleitorum.ui.main_window import MainWindow  # noqa: PLC0415

    window = MainWindow()
    qtbot.addWidget(window)
    return window


class TestMainWindow:
    """Tests for MainWindow QMainWindow (APP-01, APP-03, APP-04, APP-14, APP-16)."""

    def test_main_window_min_size_600_500(self, main_window) -> None:  # noqa: ANN001
        """MainWindow must have minimum size (600, 500)."""
        assert main_window.minimumSize().width() == 600
        assert main_window.minimumSize().height() == 500

    def test_main_window_initial_size_900_650(self, qtbot) -> None:  # noqa: ANN001
        """MainWindow size must be (900, 650) on fresh launch (no saved geometry)."""
        # Remove any stored geometry to get the default size
        settings = QSettings()
        settings.remove("window/geometry")
        settings.remove("window/state")

        from eleitorum.ui.main_window import MainWindow  # noqa: PLC0415

        window = MainWindow()
        qtbot.addWidget(window)
        assert window.size().width() == 900
        assert window.size().height() == 650

    def test_main_window_window_title_is_app_name(self, main_window) -> None:  # noqa: ANN001
        """MainWindow window title must equal APP_NAME."""
        assert main_window.windowTitle() == APP_NAME

    def test_main_window_menu_bar_has_three_top_menus(self, main_window) -> None:  # noqa: ANN001
        """Menu bar must contain Ficheiro, Ver, and Ajuda top-level menus."""
        top_menu_titles = [m.title() for m in main_window.menuBar().findChildren(QMenu)]
        assert MENU_FILE in top_menu_titles
        assert MENU_VIEW in top_menu_titles
        assert MENU_HELP in top_menu_titles

    def test_main_window_ficheiro_menu_has_reiniciar_and_sair(self, main_window) -> None:  # noqa: ANN001
        """Ficheiro menu must contain Reiniciar and Sair QActions."""
        from eleitorum.ui.strings import MENU_REINICIAR, MENU_SAIR  # noqa: PLC0415

        ficheiro_menus = [
            m for m in main_window.menuBar().findChildren(QMenu) if m.title() == MENU_FILE
        ]
        assert ficheiro_menus, f"No menu titled '{MENU_FILE}' found"
        ficheiro = ficheiro_menus[0]

        action_texts = [a.text() for a in ficheiro.actions()]
        assert MENU_REINICIAR in action_texts
        assert MENU_SAIR in action_texts

    def test_main_window_close_event_persists_geometry(
        self,
        main_window,
        qtbot,  # noqa: ANN001
    ) -> None:
        """closeEvent must save window/geometry to QSettings."""
        settings = main_window._settings
        # Remove any stale geometry
        settings.remove("window/geometry")

        main_window.show()
        qtbot.waitExposed(main_window)

        # Trigger close to fire closeEvent
        main_window.close()

        # Geometry should have been persisted
        assert settings.value("window/geometry", None, type=bytes) is not None

    def test_main_window_first_run_shows_welcome_dialog(
        self,
        qtbot,
        monkeypatch,  # noqa: ANN001
    ) -> None:
        """WelcomeDialog.exec() must be called once when first_run_shown is False."""
        exec_calls: list = []

        class TrackedDialog:
            def __init__(self, parent=None):  # noqa: ANN001
                pass

            def exec(self):  # noqa: ANN201
                exec_calls.append(1)

        monkeypatch.setattr("eleitorum.ui.main_window.WelcomeDialog", TrackedDialog)

        # Clear the first_run_shown flag to trigger the welcome dialog
        settings = QSettings()
        settings.remove("app/first_run_shown")

        from eleitorum.ui.main_window import MainWindow  # noqa: PLC0415

        window = MainWindow()
        qtbot.addWidget(window)

        assert len(exec_calls) == 1

    def test_main_window_subsequent_run_does_not_show_welcome(
        self,
        qtbot,
        monkeypatch,  # noqa: ANN001
    ) -> None:
        """WelcomeDialog.exec() must NOT be called when first_run_shown is True."""
        exec_calls: list = []

        class TrackedDialog:
            def __init__(self, parent=None):  # noqa: ANN001
                pass

            def exec(self):  # noqa: ANN201
                exec_calls.append(1)

        monkeypatch.setattr("eleitorum.ui.main_window.WelcomeDialog", TrackedDialog)

        # Set first_run_shown=True to suppress the welcome dialog
        settings = QSettings()
        settings.setValue("app/first_run_shown", True)

        from eleitorum.ui.main_window import MainWindow  # noqa: PLC0415

        window = MainWindow()
        qtbot.addWidget(window)

        assert len(exec_calls) == 0

    def test_main_window_qsettings_reads_use_type_kwarg(self) -> None:
        """AST check: every self._settings.value() call in main_window.py must include type=."""
        main_window_path = (
            pathlib.Path(__file__).parent.parent.parent.parent
            / "src"
            / "eleitorum"
            / "ui"
            / "main_window.py"
        )
        source = main_window_path.read_text(encoding="utf-8")
        tree = ast.parse(source)

        violations: list[str] = []

        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            # Check for self._settings.value(...) calls
            func = node.func
            if not (
                isinstance(func, ast.Attribute)
                and func.attr == "value"
                and isinstance(func.value, ast.Attribute)
                and func.value.attr == "_settings"
            ):
                continue

            # Verify 'type' keyword argument is present
            has_type_kwarg = any(kw.arg == "type" for kw in node.keywords)
            if not has_type_kwarg:
                violations.append(f"Line {node.lineno}: self._settings.value() missing type= kwarg")

        assert violations == [], "\n".join(violations)
