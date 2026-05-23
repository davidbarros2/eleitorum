"""NavBar reusable footer widget for EleitorUM wizard steps (WIZ-09, APP-17).

Provides Anterior / Próximo / Cancelar navigation buttons used on every wizard
step. Cancelar is on the far left; Anterior and Próximo are on the right.

The wizard controller connects the three signals to its navigation handlers.
Step widgets call the public API methods to enable/disable/relabel buttons
without touching internal button objects.

Security note: no user-supplied content flows through this widget.
"""
from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QHBoxLayout, QPushButton, QWidget

from eleitorum.ui.strings import BTN_ANTERIOR, BTN_CANCELAR, BTN_PROXIMO


class NavBar(QWidget):
    """Reusable footer widget with Anterior / Próximo / Cancelar buttons.

    Signals
    -------
    anterior_clicked : Signal()
        Emitted when the Anterior button is clicked.
    proximo_clicked : Signal()
        Emitted when the Próximo button is clicked.
    cancelar_clicked : Signal()
        Emitted when the Cancelar button is clicked.
    """

    anterior_clicked = Signal()
    proximo_clicked = Signal()
    cancelar_clicked = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        # Cancelar on the far left
        self._btn_cancelar = QPushButton(BTN_CANCELAR)
        self._btn_cancelar.setMinimumWidth(100)

        # Anterior and Próximo on the right
        self._btn_anterior = QPushButton(BTN_ANTERIOR)
        self._btn_anterior.setMinimumWidth(100)

        self._btn_proximo = QPushButton(BTN_PROXIMO)
        self._btn_proximo.setMinimumWidth(100)
        self._btn_proximo.setObjectName("primary")  # QSS accent-color rule

        layout.addWidget(self._btn_cancelar)
        layout.addStretch()
        layout.addWidget(self._btn_anterior)
        layout.addWidget(self._btn_proximo)

        # Forward button clicks to named signals
        self._btn_cancelar.clicked.connect(self.cancelar_clicked)
        self._btn_anterior.clicked.connect(self.anterior_clicked)
        self._btn_proximo.clicked.connect(self.proximo_clicked)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def set_anterior_enabled(self, enabled: bool) -> None:
        """Enable or disable the Anterior button."""
        self._btn_anterior.setEnabled(enabled)

    def set_proximo_enabled(self, enabled: bool) -> None:
        """Enable or disable the Próximo button."""
        self._btn_proximo.setEnabled(enabled)

    def set_proximo_text(self, text: str) -> None:
        """Override the Próximo button label (e.g. BTN_GRAVAR on step 4)."""
        self._btn_proximo.setText(text)

    def set_cancel_visible(self, visible: bool) -> None:
        """Show or hide the Cancelar button (hidden on step_processing)."""
        self._btn_cancelar.setVisible(visible)
