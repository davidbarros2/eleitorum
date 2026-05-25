"""Step 3 — Column mapping with auto-detection and manual override (WIZ-04, DET-07).

Pre-populates the mapping from session.pipeline_result.detection when detection
succeeded. Falls back to manual QComboBox mode when detection_method == 'manual'
or pipeline_result is absent.

DET-07: mecanográfico mapping row is hidden when session.output_type == 'elegiveis'.

Session write: column_map (dict[str, int]) — maps 'mecanografico' and 'name'
to the currently selected column index. Written on every QComboBox change.

Security note (T-02-04-03): QComboBox currentIndex() is bounded by the items
it was populated with; items come exclusively from session.column_headers so
indices are always valid.
"""

from __future__ import annotations

from PySide6.QtWidgets import (
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from eleitorum.ui.session import SessionModel
from eleitorum.ui.strings import (
    BTN_ALTERAR,
    COL_MAPPING_HIGH,
    COL_MAPPING_LOW,
    ERR_NO_DETECTION_BODY,
    ERR_NO_DETECTION_HEADING,
    STEP_3_TITLE,
)

# Confidence threshold: 'synonym' → high; anything else → low
_HIGH_CONFIDENCE_METHODS: frozenset[str] = frozenset({"synonym"})


class StepColumns(QWidget):
    """Step 3: column mapping — auto-detected or manual (WIZ-04, DET-07).

    Session writes: column_map dict keyed by 'mecanografico' and 'name'.
    is_complete() always returns True (Próximo always enabled — WIZ-04 spec).
    """

    # Declared here because _build_mapping_row sets them via setattr()
    _mec_row: QFrame
    _name_row: QFrame
    _mec_value_label: QLabel
    _mec_alterar_btn: QPushButton
    _mec_combo: QComboBox
    _name_value_label: QLabel
    _name_alterar_btn: QPushButton
    _name_combo: QComboBox

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
        title = QLabel(STEP_3_TITLE)
        title.setObjectName("stepTitle")
        layout.addWidget(title)

        # No-detection warning (initially hidden; shown in manual mode)
        self._no_detection_label = QLabel(ERR_NO_DETECTION_HEADING + "\n" + ERR_NO_DETECTION_BODY)
        self._no_detection_label.setObjectName("noDetectionLabel")
        self._no_detection_label.setWordWrap(True)
        self._no_detection_label.setVisible(False)
        layout.addWidget(self._no_detection_label)

        # Mecanográfico mapping row (hidden for elegíveis — DET-07)
        self._mec_row = self._build_mapping_row(
            row_label="Coluna mecanográfica:",
            combo_attr="_mec_combo",
            value_attr="_mec_value_label",
            alterar_attr="_mec_alterar_btn",
            map_key="mecanografico",
        )
        layout.addWidget(self._mec_row)

        # Name mapping row
        self._name_row = self._build_mapping_row(
            row_label="Coluna do nome:",
            combo_attr="_name_combo",
            value_attr="_name_value_label",
            alterar_attr="_name_alterar_btn",
            map_key="name",
        )
        layout.addWidget(self._name_row)

        layout.addStretch()

    def _build_mapping_row(
        self,
        row_label: str,
        combo_attr: str,
        value_attr: str,
        alterar_attr: str,
        map_key: str,
    ) -> QFrame:
        """Build a single mapping row: label + value QLabel + Alterar btn + QComboBox."""
        row = QFrame()
        h_layout = QHBoxLayout(row)
        h_layout.setContentsMargins(0, 0, 0, 0)
        h_layout.setSpacing(8)

        # Row header label
        header = QLabel(row_label)
        h_layout.addWidget(header)

        # Detected value label (shown in auto mode)
        value_label = QLabel("—")
        value_label.setObjectName(f"{map_key}ValueLabel")
        h_layout.addWidget(value_label)
        setattr(self, value_attr, value_label)

        # Alterar button (shown in auto mode; hidden in manual mode)
        alterar_btn = QPushButton(BTN_ALTERAR)
        alterar_btn.setObjectName(f"{map_key}AlterarBtn")
        h_layout.addWidget(alterar_btn)
        setattr(self, alterar_attr, alterar_btn)

        # QComboBox (hidden initially; shown in manual mode or after Alterar click)
        combo = QComboBox()
        combo.setObjectName(f"{map_key}Combo")
        combo.setVisible(False)
        h_layout.addWidget(combo)
        setattr(self, combo_attr, combo)

        h_layout.addStretch()

        # Wire Alterar to open the combo in-place
        alterar_btn.clicked.connect(
            lambda checked=False, c=combo, v=value_label, b=alterar_btn: self._on_alterar_clicked(
                c, v, b
            )
        )
        # Wire combo changes to session.column_map
        combo.currentIndexChanged.connect(lambda idx, key=map_key: self._on_combo_changed(key, idx))

        return row

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def populate_from_session(self) -> None:
        """Read detection results and column headers from session; populate UI.

        Detection present and method != 'manual': auto mode (show value labels).
        Detection absent or method == 'manual': manual mode (show combos, heading).
        DET-07: hide mec_row if session.output_type == 'elegiveis'.
        """
        headers: list[str] = self._session.column_headers or []
        det: dict = {}
        if self._session.pipeline_result is not None:
            det = getattr(self._session.pipeline_result, "detection", {}) or {}
        elif self._session.pre_detection is not None:
            det = self._session.pre_detection

        detection_method = det.get("detection_method", "manual")
        has_detection = bool(det) and detection_method != "manual"

        if has_detection:
            self._enter_auto_mode(det, headers)
        else:
            self._enter_manual_mode(headers)

        # DET-07: hide mecanográfico row for elegíveis
        self._mec_row.setVisible(self._session.output_type != "elegiveis")

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _enter_auto_mode(self, det: dict, headers: list[str]) -> None:
        """Show pre-detected values; hide manual combos and no-detection message."""
        self._no_detection_label.setVisible(False)

        mec_idx = det.get("mec_col_index")
        name_idx = det.get("name_col_index")
        method = det.get("detection_method", "")
        high = method in _HIGH_CONFIDENCE_METHODS

        # Populate mec value label
        if mec_idx is not None and headers and mec_idx < len(headers):
            col_name = headers[mec_idx]
            if high:
                msg = COL_MAPPING_HIGH.format(name=col_name, role="mecanográfica")
                self._mec_value_label.setText(msg)
            else:
                self._mec_value_label.setText(COL_MAPPING_LOW.format(name=col_name))
        self._mec_value_label.setVisible(True)
        self._mec_alterar_btn.setVisible(True)
        self._mec_combo.setVisible(False)
        self._populate_combo(self._mec_combo, headers)

        # Populate name value label
        if name_idx is not None and headers and name_idx < len(headers):
            col_name = headers[name_idx]
            if high:
                msg = COL_MAPPING_HIGH.format(name=col_name, role="do nome")
                self._name_value_label.setText(msg)
            else:
                self._name_value_label.setText(COL_MAPPING_LOW.format(name=col_name))
        self._name_value_label.setVisible(True)
        self._name_alterar_btn.setVisible(True)
        self._name_combo.setVisible(False)
        self._populate_combo(self._name_combo, headers)

        # Initialize session.column_map from detected indices
        self._session.column_map = {
            "mecanografico": mec_idx if mec_idx is not None else 0,
            "name": name_idx if name_idx is not None else 0,
        }

    def _enter_manual_mode(self, headers: list[str]) -> None:
        """Show no-detection message and open combos immediately."""
        self._no_detection_label.setVisible(True)

        self._mec_value_label.setVisible(False)
        self._mec_alterar_btn.setVisible(False)
        self._mec_combo.setVisible(True)
        self._populate_combo(self._mec_combo, headers)

        self._name_value_label.setVisible(False)
        self._name_alterar_btn.setVisible(False)
        self._name_combo.setVisible(True)
        self._populate_combo(self._name_combo, headers)

        # Initialize session.column_map from current indices
        self._session.column_map = {
            "mecanografico": self._mec_combo.currentIndex(),
            "name": self._name_combo.currentIndex(),
        }

    def _populate_combo(self, combo: QComboBox, headers: list[str]) -> None:
        """Populate a QComboBox with the column headers without triggering signals."""
        combo.blockSignals(True)
        combo.clear()
        for h in headers:
            combo.addItem(h)
        combo.blockSignals(False)

    def _on_alterar_clicked(
        self,
        combo: QComboBox,
        value_label: QLabel,
        alterar_btn: QPushButton,
    ) -> None:
        """Hide value label, show QComboBox for in-place edit."""
        value_label.setVisible(False)
        alterar_btn.setVisible(False)
        combo.setVisible(True)

    def _on_combo_changed(self, map_key: str, index: int) -> None:
        """Write updated column index to session.column_map."""
        if self._session.column_map is None:
            self._session.column_map = {}
        self._session.column_map[map_key] = index

    # ------------------------------------------------------------------
    # NavBar contract
    # ------------------------------------------------------------------

    def is_complete(self) -> bool:
        """Always True — Próximo is always enabled once step is visible (WIZ-04)."""
        return True
