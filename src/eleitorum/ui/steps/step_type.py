"""Step 1 — Output type selection (WIZ-01, APP-17, APP-18).

Displays two OptionCard widgets (Caderno Eleitoral / Lista de Elegíveis).
Próximo is enabled only after the user selects one card (is_complete()).

Session contract: writes session.output_type on card selection.
Restores visual state from session.output_type on construction (back-navigation
and Reiniciar flows — WIZ-10).
"""

from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QHBoxLayout, QLabel, QVBoxLayout, QWidget

from eleitorum.ui.session import SessionModel
from eleitorum.ui.strings import (
    OPTION_CADERNO_DESC,
    OPTION_CADERNO_HEADING,
    OPTION_ELEGIVEIS_DESC,
    OPTION_ELEGIVEIS_HEADING,
    STEP_1_TITLE,
)
from eleitorum.ui.widgets.option_card import OptionCard


class StepType(QWidget):
    """Step 1: output type selection widget (WIZ-01).

    Receives a SessionModel, mutates session.output_type in-place,
    and exposes is_complete() so the NavBar can enable/disable Próximo.
    """

    completion_changed = Signal()

    def __init__(
        self,
        session: SessionModel,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)

        self._session = session
        self._setup_ui()
        self._restore_state()

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _setup_ui(self) -> None:
        """Build the vertical layout with title + card row."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # Step title (QSS rule: QLabel[objectName="stepTitle"] in theme.py)
        title = QLabel(STEP_1_TITLE)
        title.setObjectName("stepTitle")
        layout.addWidget(title)

        # Option cards in a horizontal row with 24px spacing (lg)
        cards_row = QHBoxLayout()
        cards_row.setSpacing(24)

        self._card_caderno = OptionCard(
            "caderno",
            heading=OPTION_CADERNO_HEADING,
            description=OPTION_CADERNO_DESC,
        )
        self._card_elegiveis = OptionCard(
            "elegiveis",
            heading=OPTION_ELEGIVEIS_HEADING,
            description=OPTION_ELEGIVEIS_DESC,
        )

        self._card_caderno.selected.connect(self._on_selection)
        self._card_elegiveis.selected.connect(self._on_selection)

        cards_row.addWidget(self._card_caderno)
        cards_row.addWidget(self._card_elegiveis)

        layout.addLayout(cards_row)
        layout.addStretch()

    # ------------------------------------------------------------------
    # State restoration (back-navigation / Reiniciar)
    # ------------------------------------------------------------------

    def _restore_state(self) -> None:
        """Restore visual selection if session already has output_type set."""
        if self._session.output_type == "caderno":
            self._card_caderno.set_selected(True)
        elif self._session.output_type == "elegiveis":
            self._card_elegiveis.set_selected(True)

    # ------------------------------------------------------------------
    # Slot
    # ------------------------------------------------------------------

    def _on_selection(self, key: str) -> None:
        """Handle card selection: write session, deselect the other card."""
        self._session.output_type = key  # type: ignore[assignment]
        if key == "caderno":
            self._card_elegiveis.set_selected(False)
        else:
            self._card_caderno.set_selected(False)
        self.completion_changed.emit()

    # ------------------------------------------------------------------
    # NavBar contract
    # ------------------------------------------------------------------

    def is_complete(self) -> bool:
        """Return True iff session.output_type has been set (Próximo enabled)."""
        return self._session.output_type is not None
