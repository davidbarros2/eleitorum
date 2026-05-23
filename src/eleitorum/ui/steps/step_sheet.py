"""Step 2.5 — Sheet picker for multi-sheet Excel/ODS files (WIZ-03).

Shown conditionally by the wizard controller when session.sheets has more than
one entry (i.e. the file has multiple sheets). Single-sheet and CSV/TSV files
bypass this step entirely.

The list is populated via populate_from_session() after StepUpload completes.
Empty sheets are visually muted with secondary text color (#878787) per the
UI spec. Single-selection only.

Session write: sheet_name (str) — the raw (unformatted) sheet name from the
workbook, stored on currentItemChanged signal.
"""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QAbstractItemView,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QVBoxLayout,
    QWidget,
)

from eleitorum.core.readers import SheetInfo
from eleitorum.ui.session import SessionModel
from eleitorum.ui.strings import (
    SHEET_PICKER_EMPTY_SUFFIX,
    SHEET_PICKER_ROWS_TEMPLATE,
    STEP_25_TITLE,
)

# Secondary text / muted color from 02-UI-SPEC light theme palette
_MUTED_COLOR: str = "#878787"


class StepSheet(QWidget):
    """Step 2.5: sheet picker for multi-sheet workbooks (WIZ-03).

    Session write: sheet_name (str) set on item selection.
    """

    def __init__(
        self,
        session: SessionModel,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)

        self._session = session
        self._setup_ui()

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # Step title
        title = QLabel(STEP_25_TITLE)
        title.setObjectName("stepTitle")
        layout.addWidget(title)

        # Sheet list — single selection only
        self._list = QListWidget()
        self._list.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self._list.currentItemChanged.connect(self._on_selection_changed)
        layout.addWidget(self._list)

        layout.addStretch()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def populate_from_session(self) -> None:
        """Rebuild the list from session.sheets.

        Clears existing items and repopulates. Empty sheets are muted.
        Item UserRole data stores the original (unformatted) sheet name
        so session.sheet_name receives the raw workbook name, not the
        display text.
        """
        self._list.clear()

        sheets = self._session.sheets or []
        for info in sheets:
            if info.is_empty:
                display_text = info.name + SHEET_PICKER_EMPTY_SUFFIX
            else:
                display_text = (
                    info.name + " " + SHEET_PICKER_ROWS_TEMPLATE.format(rows=info.approximate_row_count)
                )

            item = QListWidgetItem(display_text)
            # Store raw name for session write (display text ≠ raw name)
            item.setData(Qt.ItemDataRole.UserRole, info.name)

            if info.is_empty:
                item.setForeground(QColor(_MUTED_COLOR))

            self._list.addItem(item)

    # ------------------------------------------------------------------
    # Slot
    # ------------------------------------------------------------------

    def _on_selection_changed(
        self,
        current: QListWidgetItem | None,
        previous: QListWidgetItem | None,
    ) -> None:
        """Write session.sheet_name when the user selects a sheet."""
        if current is not None:
            self._session.sheet_name = current.data(Qt.ItemDataRole.UserRole)
        else:
            self._session.sheet_name = None

    # ------------------------------------------------------------------
    # NavBar contract
    # ------------------------------------------------------------------

    def is_complete(self) -> bool:
        """Return True iff the user has selected a sheet (Próximo enabled)."""
        return self._session.sheet_name is not None
