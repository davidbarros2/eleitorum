"""Step 4 — Preview table + summary panel + Ver detalhes log toggle (WIZ-05, D-03).

Consumes PipelineResult.preview_rows (first 50 output rows snapshotted during
dry-run) and displays them in a read-only QTableWidget. Summary labels show
total rows and transformation count. "Ver detalhes" toggles a max-150px
QTextEdit with the full log content inline below the summary panel.

Requirements: WIZ-05 (scrollable preview ~50 rows before save), D-03 (Ver detalhes
inline collapsible QTextEdit max 150px).
"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from eleitorum.ui.session import SessionModel
from eleitorum.ui.strings import (
    BTN_GRAVAR,
    BTN_VER_DETALHES_ABRIR,
    BTN_VER_DETALHES_FECHAR,
    PREVIEW_TOTAL_ROWS,
    PREVIEW_TRANSFORMATIONS,
    STEP_4_TITLE,
)

# Maximum preview rows shown in the table (WIZ-05: ~50 rows)
_MAX_PREVIEW_ROWS: int = 50

# Maximum height of the Ver detalhes log panel (D-03)
_LOG_VIEW_MAX_HEIGHT: int = 150


class StepPreview(QWidget):
    """Step 4: preview table, summary panel, and Ver detalhes log toggle.

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

        # Summary section
        self._summary_rows_label = QLabel("")
        layout.addWidget(self._summary_rows_label)

        # Transformations row with "Ver detalhes" toggle button
        transforms_row = QHBoxLayout()
        self._summary_transforms_label = QLabel("")
        transforms_row.addWidget(self._summary_transforms_label)

        self._ver_detalhes_btn = QPushButton(BTN_VER_DETALHES_ABRIR)
        self._ver_detalhes_btn.setFlat(True)
        self._ver_detalhes_btn.setVisible(False)  # hidden until transformations > 0
        transforms_row.addWidget(self._ver_detalhes_btn)
        transforms_row.addStretch()
        layout.addLayout(transforms_row)

        # Warnings label (shown only when issues exist)
        self._summary_warnings_label = QLabel("")
        self._summary_warnings_label.setVisible(False)
        layout.addWidget(self._summary_warnings_label)

        # Ver detalhes log panel — max 150px, initially hidden (D-03)
        self._log_view = QTextEdit()
        self._log_view.setReadOnly(True)
        self._log_view.setMaximumHeight(_LOG_VIEW_MAX_HEIGHT)
        self._log_view.setVisible(False)
        layout.addWidget(self._log_view)

        # Preview table — read-only, fills remaining space
        self._table = QTableWidget()
        self._table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self._table, stretch=1)

        # Wire toggle
        self._ver_detalhes_btn.clicked.connect(self._on_ver_detalhes_clicked)

    # ------------------------------------------------------------------
    # Public API consumed by wizard.py
    # ------------------------------------------------------------------

    def populate_from_session(self) -> None:
        """Read session.pipeline_result and update all display elements."""
        result = self._session.pipeline_result
        if result is None:
            return

        # Update summary labels
        self._summary_rows_label.setText(PREVIEW_TOTAL_ROWS.format(n=result.rows_processed))
        self._summary_transforms_label.setText(
            PREVIEW_TRANSFORMATIONS.format(m=result.transformations_applied)
        )

        # Show Ver detalhes button only if there are transformation log entries
        has_transformations = result.transformations_applied > 0
        self._ver_detalhes_btn.setVisible(has_transformations)

        # Reset log view state
        self._log_view.setVisible(False)
        self._ver_detalhes_btn.setText(BTN_VER_DETALHES_ABRIR)

        # Populate log view content
        log_entries = getattr(result, "log_entries", [])
        self._log_view.setPlainText("\n".join(log_entries))

        # Populate preview table (max 50 rows)
        preview_rows: list[list[str]] = getattr(result, "preview_rows", [])
        rows_to_show = preview_rows[:_MAX_PREVIEW_ROWS]
        num_rows = len(rows_to_show)
        num_cols = len(rows_to_show[0]) if rows_to_show else 0

        self._table.setRowCount(num_rows)
        self._table.setColumnCount(num_cols)

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

    # ------------------------------------------------------------------
    # Private slots
    # ------------------------------------------------------------------

    def _on_ver_detalhes_clicked(self) -> None:
        """Toggle the Ver detalhes log view visibility and button text (D-03)."""
        currently_visible = self._log_view.isVisible()
        self._log_view.setVisible(not currently_visible)
        self._ver_detalhes_btn.setText(
            BTN_VER_DETALHES_FECHAR if not currently_visible else BTN_VER_DETALHES_ABRIR
        )
