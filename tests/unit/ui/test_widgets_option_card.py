"""Smoke tests for the OptionCard selectable card widget (WIZ-01, APP-17, APP-18).

Tests verify: construction, QSS dynamic property toggling, signal emission,
mouse + keyboard activation, and focus policy.
"""

from __future__ import annotations

from PySide6.QtCore import Qt

from eleitorum.ui.widgets.option_card import OptionCard


class TestOptionCard:
    """Smoke tests for OptionCard widget (WIZ-01)."""

    def test_option_card_constructs_with_key(self, qtbot) -> None:
        """OptionCard stores key; default selected property is False."""
        card = OptionCard("caderno")
        qtbot.addWidget(card)

        assert card._key == "caderno"
        assert card.property("selected") is False

    def test_option_card_set_selected_true_updates_property(self, qtbot) -> None:
        """set_selected(True) updates the 'selected' QSS property to True."""
        card = OptionCard("caderno")
        qtbot.addWidget(card)

        card.set_selected(True)

        assert card.property("selected") is True

    def test_option_card_set_selected_emits_signal(self, qtbot) -> None:
        """set_selected(True) emits the 'selected' signal with the key string."""
        card = OptionCard("elegiveis")
        qtbot.addWidget(card)

        with qtbot.waitSignal(card.selected, timeout=1000) as blocker:
            card.set_selected(True)

        assert blocker.args == ["elegiveis"]

    def test_option_card_set_selected_false_does_not_emit(self, qtbot) -> None:
        """set_selected(False) does NOT emit the signal."""
        card = OptionCard("caderno")
        qtbot.addWidget(card)
        # First select it so we can deselect
        card.set_selected(True)

        # Reset signal spy
        signals_received = []
        card.selected.connect(lambda key: signals_received.append(key))

        card.set_selected(False)

        assert signals_received == [], "Signal must not emit on deselect"

    def test_option_card_mouse_click_selects(self, qtbot) -> None:
        """Left-clicking the card triggers selection and emits signal."""
        card = OptionCard("caderno")
        qtbot.addWidget(card)
        card.show()

        with qtbot.waitSignal(card.selected, timeout=1000):
            qtbot.mouseClick(card, Qt.MouseButton.LeftButton)

    def test_option_card_space_key_selects(self, qtbot) -> None:
        """Pressing Space selects the card."""
        card = OptionCard("caderno")
        qtbot.addWidget(card)
        card.show()
        # Deselect first to allow re-selection
        card._is_selected = False
        card.setProperty("selected", False)

        with qtbot.waitSignal(card.selected, timeout=1000):
            qtbot.keyClick(card, Qt.Key.Key_Space)

    def test_option_card_return_key_selects(self, qtbot) -> None:
        """Pressing Return selects the card."""
        card = OptionCard("elegiveis")
        qtbot.addWidget(card)
        card.show()
        # Ensure unselected before test
        card._is_selected = False
        card.setProperty("selected", False)

        with qtbot.waitSignal(card.selected, timeout=1000):
            qtbot.keyClick(card, Qt.Key.Key_Return)

    def test_option_card_focus_policy_strong(self, qtbot) -> None:
        """OptionCard has StrongFocus policy for keyboard accessibility (APP-17)."""
        card = OptionCard("caderno")
        qtbot.addWidget(card)

        assert card.focusPolicy() == Qt.FocusPolicy.StrongFocus

    def test_option_card_unpolish_polish_called_on_property_change(self, qtbot) -> None:
        """QSS refresh discipline: property toggles correctly on repeated calls."""
        card = OptionCard("caderno")
        qtbot.addWidget(card)

        # Initial state
        assert card.property("selected") is False

        # Select
        card.set_selected(True)
        assert card.property("selected") is True

        # Deselect
        card.set_selected(False)
        assert card.property("selected") is False

        # Re-select
        card.set_selected(True)
        assert card.property("selected") is True
