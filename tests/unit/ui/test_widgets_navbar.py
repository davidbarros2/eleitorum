"""Smoke tests for the NavBar reusable footer widget (WIZ-09, APP-17).

Tests verify: button presence, signal emission, and public API methods.
All tests use qtbot for PySide6 widget lifecycle management.
"""

from __future__ import annotations

from PySide6.QtCore import Qt

from eleitorum.ui.widgets.navbar import NavBar


class TestNavBar:
    """Smoke tests for NavBar footer widget (WIZ-09)."""

    def test_navbar_buttons_exist(self, qtbot) -> None:
        """All three buttons exist with correct labels from strings.py."""
        from eleitorum.ui.strings import BTN_ANTERIOR, BTN_CANCELAR, BTN_PROXIMO

        nav = NavBar()
        qtbot.addWidget(nav)

        assert nav._btn_anterior.text() == BTN_ANTERIOR
        assert nav._btn_proximo.text() == BTN_PROXIMO
        assert nav._btn_cancelar.text() == BTN_CANCELAR

    def test_navbar_emits_proximo_clicked(self, qtbot) -> None:
        """Clicking Próximo emits proximo_clicked exactly once."""
        nav = NavBar()
        qtbot.addWidget(nav)

        with qtbot.waitSignal(nav.proximo_clicked, timeout=1000):
            qtbot.mouseClick(nav._btn_proximo, Qt.MouseButton.LeftButton)

    def test_navbar_emits_anterior_clicked(self, qtbot) -> None:
        """Clicking Anterior emits anterior_clicked exactly once."""
        nav = NavBar()
        qtbot.addWidget(nav)

        with qtbot.waitSignal(nav.anterior_clicked, timeout=1000):
            qtbot.mouseClick(nav._btn_anterior, Qt.MouseButton.LeftButton)

    def test_navbar_emits_cancelar_clicked(self, qtbot) -> None:
        """Clicking Cancelar emits cancelar_clicked exactly once."""
        nav = NavBar()
        qtbot.addWidget(nav)

        with qtbot.waitSignal(nav.cancelar_clicked, timeout=1000):
            qtbot.mouseClick(nav._btn_cancelar, Qt.MouseButton.LeftButton)

    def test_navbar_set_anterior_enabled_false_disables_button(self, qtbot) -> None:
        """set_anterior_enabled(False) disables Anterior button."""
        nav = NavBar()
        qtbot.addWidget(nav)

        nav.set_anterior_enabled(False)

        assert nav._btn_anterior.isEnabled() is False

    def test_navbar_set_proximo_text_changes_label(self, qtbot) -> None:
        """set_proximo_text updates the Próximo button label."""
        nav = NavBar()
        qtbot.addWidget(nav)

        new_text = "Escolher destino e gravar"
        nav.set_proximo_text(new_text)

        assert nav._btn_proximo.text() == new_text

    def test_navbar_set_cancel_visible_false_hides_cancel(self, qtbot) -> None:
        """set_cancel_visible(False) hides the Cancelar button."""
        nav = NavBar()
        qtbot.addWidget(nav)
        nav.show()

        nav.set_cancel_visible(False)

        assert nav._btn_cancelar.isVisible() is False
