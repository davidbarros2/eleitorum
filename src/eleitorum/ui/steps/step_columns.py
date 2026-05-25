"""Step 3 — Visual column picker: raw data table with clickable column headers (WIZ-04, DET-07).

Shows the raw file rows in a QTableWidget. Clicking a column header opens a
QMenu to assign that column as "Nº Mecanográfico" or "Nome". The header
label updates after each assignment to show the current role.

DET-07: "Nº Mecanográfico" menu item is hidden when session.output_type == 'elegiveis'.

Session write: column_map (dict[str, int | None]) — maps 'mecanografico' and 'name'
to the selected column index. Written on every assignment change.

is_complete(): True when required columns are assigned (both for caderno, name only
for elegiveis). completion_changed emitted after every change so the NavBar updates.
"""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QCursor
from PySide6.QtWidgets import (
    QAbstractItemView,
    QLabel,
    QMenu,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from eleitorum.ui.session import SessionModel
from eleitorum.ui.strings import (
    COL_PICKER_COL_LABEL,
    COL_PICKER_HEADER_MEC,
    COL_PICKER_HEADER_NOME,
    COL_PICKER_INSTRUCTIONS,
    COL_PICKER_INSTRUCTIONS_ELEGIVEIS,
    COL_PICKER_MENU_MEC,
    COL_PICKER_MENU_NOME,
    COL_PICKER_NO_DATA,
    STEP_3_TITLE,
)

_MAX_PREVIEW_ROWS: int = 20


class StepColumns(QWidget):
    """Step 3: visual column picker via clickable table headers (WIZ-04, DET-07).

    Session writes: column_map dict keyed by 'mecanografico' and 'name'.
    is_complete() returns True only when required columns are assigned.
    """

    completion_changed = Signal()

    def __init__(
        self,
        session: SessionModel,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._session = session
        self._mec_col: int | None = None
        self._name_col: int | None = None
        self._file_headers: list[str] = []
        self._setup_ui()

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        title = QLabel(STEP_3_TITLE)
        title.setObjectName("stepTitle")
        layout.addWidget(title)

        self._instructions = QLabel(COL_PICKER_INSTRUCTIONS)
        self._instructions.setWordWrap(True)
        layout.addWidget(self._instructions)

        self._no_data_label = QLabel(COL_PICKER_NO_DATA)
        self._no_data_label.setVisible(False)
        layout.addWidget(self._no_data_label)

        self._table = QTableWidget()
        self._table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._table.horizontalHeader().setStretchLastSection(True)
        self._table.horizontalHeader().sectionClicked.connect(self._on_header_clicked)
        layout.addWidget(self._table, stretch=1)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def populate_from_session(self) -> None:
        """Read raw rows and detection results from session; populate table.

        Detects header row index from session.pre_detection to derive
        file-level column names. Initialises column assignments from
        auto-detection when detection_method != 'manual'.
        DET-07: 'mecanografico' role suppressed for elegiveis output type.
        """
        output_type = self._session.output_type or "caderno"
        self._instructions.setText(
            COL_PICKER_INSTRUCTIONS_ELEGIVEIS if output_type == "elegiveis" else COL_PICKER_INSTRUCTIONS
        )

        raw_rows: list[list] = self._session.raw_preview_rows or []
        det: dict = self._session.pre_detection or {}

        if not raw_rows:
            self._table.setVisible(False)
            self._no_data_label.setVisible(True)
            # Still mark as complete so the user isn't blocked
            self._mec_col = None
            self._name_col = None
            self._sync_session_column_map()
            return

        self._table.setVisible(True)
        self._no_data_label.setVisible(False)

        rows_to_show = raw_rows[:_MAX_PREVIEW_ROWS]
        ncols = max((len(r) for r in rows_to_show), default=0)

        # Build file-level column names from the detected header row (if any)
        header_idx = det.get("header_row_index")
        if header_idx is not None and header_idx < len(rows_to_show):
            raw_header = rows_to_show[header_idx]
            self._file_headers = [
                str(c).strip() if c is not None else "" for c in raw_header
            ]
        else:
            self._file_headers = []

        # Pad file_headers to ncols
        while len(self._file_headers) < ncols:
            self._file_headers.append("")

        # Pre-populate column assignments from auto-detection
        detection_method = det.get("detection_method", "manual")
        if detection_method != "manual":
            self._mec_col = det.get("mec_col_index") if output_type != "elegiveis" else None
            self._name_col = det.get("name_col_index")
        else:
            self._mec_col = None
            self._name_col = None

        self._sync_session_column_map()

        # Populate table rows
        self._table.setRowCount(len(rows_to_show))
        self._table.setColumnCount(ncols)

        for r_idx, row in enumerate(rows_to_show):
            for c_idx in range(ncols):
                cell = row[c_idx] if c_idx < len(row) else None
                item = QTableWidgetItem(str(cell) if cell is not None else "")
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self._table.setItem(r_idx, c_idx, item)

        self._update_header_labels()

    # ------------------------------------------------------------------
    # NavBar contract
    # ------------------------------------------------------------------

    def is_complete(self) -> bool:
        """True when all required columns are assigned."""
        output_type = self._session.output_type or "caderno"
        if output_type == "elegiveis":
            return self._name_col is not None
        return self._mec_col is not None and self._name_col is not None

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _col_display_name(self, col_idx: int) -> str:
        """Return the display name for a column: file header or 'Coluna N'."""
        if col_idx < len(self._file_headers) and self._file_headers[col_idx]:
            return self._file_headers[col_idx]
        return COL_PICKER_COL_LABEL.format(n=col_idx + 1)

    def _update_header_labels(self) -> None:
        """Refresh the QTableWidget horizontal header labels."""
        for col_idx in range(self._table.columnCount()):
            name = self._col_display_name(col_idx)
            if col_idx == self._mec_col:
                label = COL_PICKER_HEADER_MEC.format(name=name)
            elif col_idx == self._name_col:
                label = COL_PICKER_HEADER_NOME.format(name=name)
            else:
                label = name
            item = self._table.horizontalHeaderItem(col_idx)
            if item is None:
                item = QTableWidgetItem(label)
                self._table.setHorizontalHeaderItem(col_idx, item)
            else:
                item.setText(label)

    def _sync_session_column_map(self) -> None:
        """Write current column assignments to session.column_map."""
        self._session.column_map = {
            "mecanografico": self._mec_col,
            "name": self._name_col,
        }

    def _on_header_clicked(self, col_idx: int) -> None:
        """Show a QMenu to assign this column to a role."""
        output_type = self._session.output_type or "caderno"
        menu = QMenu(self)

        if output_type == "caderno":
            act_mec = menu.addAction(COL_PICKER_MENU_MEC)
        else:
            act_mec = None

        act_nome = menu.addAction(COL_PICKER_MENU_NOME)

        chosen = menu.exec(QCursor.pos())
        if chosen is None:
            return

        if act_mec is not None and chosen == act_mec:
            # Clear any column previously assigned as mec
            self._mec_col = col_idx
            # If this column was the name column, free it
            if self._name_col == col_idx:
                self._name_col = None
        elif chosen == act_nome:
            self._name_col = col_idx
            # If this column was the mec column, free it
            if self._mec_col == col_idx:
                self._mec_col = None

        self._update_header_labels()
        self._sync_session_column_map()
        self.completion_changed.emit()
