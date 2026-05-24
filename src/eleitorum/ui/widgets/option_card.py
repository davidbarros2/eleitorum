"""OptionCard selectable card widget for EleitorUM (WIZ-01, APP-17, APP-18).

Displays a heading and description inside a rounded QFrame. Clicking or using
Space/Return/Enter selects the card; the 'selected' QSS dynamic property is
toggled and the style is refreshed via unpolish/polish so that
OptionCard[selected="true"] selectors in theme.py take effect immediately.

Keyboard accessibility: StrongFocus policy ensures the card is reachable via
Tab and activatable via Space or Return (APP-17 requirement).

Security note: ``key`` is supplied by step_upload code — only "caderno" and
"elegiveis" are used. No user-supplied content flows through this widget
(T-02-03-02 accepted).
"""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QFrame, QLabel, QVBoxLayout


class OptionCard(QFrame):
    """Selectable card widget for output-type selection (WIZ-01).

    Signals
    -------
    selected : Signal(str)
        Emitted when the card transitions to selected state.
        Carries the option key (e.g. "caderno" or "elegiveis").
        NOT emitted when the card is deselected (step widget orchestrates that).
    """

    selected = Signal(str)

    def __init__(
        self,
        key: str,
        heading: str = "",
        description: str = "",
        parent: QFrame | None = None,
    ) -> None:
        super().__init__(parent)

        self._key = key
        self._is_selected = False

        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setProperty("selected", False)

        self._setup_ui(heading, description)

    def _setup_ui(self, heading: str, description: str) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # Icon placeholder: 48×48 reserved space (populated by step widget)
        self._icon_label = QLabel()
        self._icon_label.setFixedSize(48, 48)
        layout.addWidget(self._icon_label)

        # Heading label
        self._heading_label = QLabel(heading)
        self._heading_label.setObjectName("cardHeading")
        layout.addWidget(self._heading_label)

        # Description label
        self._desc_label = QLabel(description)
        self._desc_label.setObjectName("cardDescription")
        self._desc_label.setWordWrap(True)
        layout.addWidget(self._desc_label)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def set_selected(self, value: bool) -> None:
        """Set the selected state and refresh QSS dynamic property.

        Emits ``selected`` signal only when transitioning to True.
        Deselect transitions are silent; the step widget orchestrates
        deselection of the other card.
        """
        if self._is_selected == value:
            return

        self._is_selected = value
        self.setProperty("selected", value)
        # Force QSS re-evaluation of the dynamic property (RESEARCH.md Pattern 7)
        self.style().unpolish(self)
        self.style().polish(self)

        if value:
            self.selected.emit(self._key)

    # ------------------------------------------------------------------
    # Event overrides
    # ------------------------------------------------------------------

    def mousePressEvent(self, event) -> None:
        """Left-click selects the card."""
        self.set_selected(True)
        super().mousePressEvent(event)

    def keyPressEvent(self, event) -> None:
        """Space / Return / Enter activates the card (APP-17 keyboard access)."""
        if event.key() in (Qt.Key.Key_Space, Qt.Key.Key_Return, Qt.Key.Key_Enter):
            self.set_selected(True)
        super().keyPressEvent(event)
