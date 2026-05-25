"""Step 4 — Preview table with output column headers (WIZ-05).

Consumes PipelineResult.preview_rows (first 50 output rows snapshotted during
dry-run) and displays them in a read-only QTableWidget with labelled headers.
Summary shows total row count. No log or transformation details — those appear
on the success screen after saving.

Requirements: WIZ-05 (scrollable preview ~50 rows before save).
"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QLabel,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from eleitorum.ui.session import SessionModel
from eleitorum.ui.strings import (
    BTN_GRAVAR,
    PREVIEW_COL_CATEGORIA,
    PREVIEW_COL_MEC,
    PREVIEW_COL_NOME,
    PREVIEW_TOTAL_ROWS,
    STEP_4_TITLE,
)

# Maximum preview rows shown in the table (WIZ-05: ~50 rows)
_MAX_PREVIEW_ROWS: int = 50

# Column headers per output type
_HEADERS_CADERNO: list[str] = [PREVIEW_COL_MEC, PREVIEW_COL_NOME, PREVIEW_COL_CATEGORIA]
_HEADERS_ELEGIVEIS: list[str] = [PREVIEW_COL_NOME]


class StepPreview(QWidget):
    """Step 4: preview table with output column headers.

    Populated by ``populate_from_session()`` which reads
    ``session.pipeline_result``. NavBar calls ``next_button_label()`` to
    override the "Próximo" label with "Escolher destino e gravar".
    """

    def __init__(self, session: SessionModel, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._session = session
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # Step title
        title = QLabel(STEP_4_TITLE)
        title.setObjectName("stepTitle")
        layout.addWidget(title)

        # Row count summary
        self._summary_rows_label = QLabel("")
        layout.addWidget(self._summary_rows_label)

        # Preview table — read-only, fills remaining space
        self._table = QTableWidget()
        self._table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self._table, stretch=1)

    # ------------------------------------------------------------------
    # Public API consumed by wizard.py
    # ------------------------------------------------------------------

    def populate_from_session(self) -> None:
        """Read session.pipeline_result and update all display elements."""
        result = self._session.pipeline_result
        if result is None:
            return

        # Update row count label
        self._summary_rows_label.setText(PREVIEW_TOTAL_ROWS.format(n=result.rows_processed))

        # Determine column headers from output type
        output_type = self._session.output_type or "caderno"
        col_headers = _HEADERS_CADERNO if output_type == "caderno" else _HEADERS_ELEGIVEIS

        # Populate preview table (max 50 rows)
        preview_rows: list[list[str]] = getattr(result, "preview_rows", [])
        rows_to_show = preview_rows[:_MAX_PREVIEW_ROWS]
        num_rows = len(rows_to_show)
        num_cols = len(rows_to_show[0]) if rows_to_show else len(col_headers)

        self._table.setRowCount(num_rows)
        self._table.setColumnCount(num_cols)
        self._table.setHorizontalHeaderLabels(col_headers[:num_cols])

        for row_idx, row_data in enumerate(rows_to_show):
            for col_idx, cell_value in enumerate(row_data):
                item = QTableWidgetItem(str(cell_value))
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self._table.setItem(row_idx, col_idx, item)

    def is_complete(self) -> bool:
        """NavBar polls this to enable/disable Próximo. Always True on preview."""
        return True

    def next_button_label(self) -> str:
        """Override NavBar 'Próximo' label on step 4 (WIZ-05 contract)."""
        return BTN_GRAVAR
