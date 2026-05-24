"""Step 2 — File upload via drag-and-drop or file chooser (WIZ-02).

Validates the file extension BEFORE any I/O (T-02-04-01: extension whitelist).
On valid file: sets session.source_path, populates session.sheets via
list_sheets(), and clears any inline error state.
On invalid extension: shows inline PT-PT error, leaves session.source_path None.

Security notes:
- T-02-04-01: SUPPORTED_EXTENSIONS whitelist applied before any file I/O.
- T-02-04-02: inline error text uses err.message_pt only — never a traceback.
"""

from __future__ import annotations

import pathlib

from PySide6.QtWidgets import (
    QFileDialog,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from eleitorum.core.errors import EleitorumError
from eleitorum.core.readers import SUPPORTED_EXTENSIONS, list_sheets
from eleitorum.ui.session import SessionModel
from eleitorum.ui.strings import (
    BTN_ESCOLHER_FICHEIRO,
    ERR_UNSUPPORTED_EXT,
    OPEN_DIALOG_FILTER,
    OPEN_DIALOG_TITLE,
    STEP_2_TITLE,
)
from eleitorum.ui.widgets.drop_zone import DropZone


class StepUpload(QWidget):
    """Step 2: file upload via drag-and-drop or file chooser (WIZ-02).

    Session writes: source_path (pathlib.Path), sheets (list[SheetInfo]).
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
        title = QLabel(STEP_2_TITLE)
        title.setObjectName("stepTitle")
        layout.addWidget(title)

        # Drop zone
        self._drop_zone = DropZone()
        self._drop_zone.file_dropped.connect(self._on_file_received)
        layout.addWidget(self._drop_zone)

        # File chooser button
        self._choose_btn = QPushButton(BTN_ESCOLHER_FICHEIRO)
        self._choose_btn.clicked.connect(self._on_choose_clicked)
        layout.addWidget(self._choose_btn)

        # File name label (empty until file loaded)
        self._file_name_label = QLabel("")
        self._file_name_label.setObjectName("fileNameLabel")
        layout.addWidget(self._file_name_label)

        # Inline error label (hidden until an error occurs)
        self._error_label = QLabel("")
        self._error_label.setObjectName("errorLabel")
        self._error_label.setWordWrap(True)
        self._error_label.setVisible(False)
        layout.addWidget(self._error_label)

        layout.addStretch()

    # ------------------------------------------------------------------
    # Slots
    # ------------------------------------------------------------------

    def _on_choose_clicked(self) -> None:
        """Open the file chooser dialog and forward the selected path."""
        path, _ = QFileDialog.getOpenFileName(
            self,
            OPEN_DIALOG_TITLE,
            "",
            OPEN_DIALOG_FILTER,
        )
        if path:
            self._on_file_received(path)

    def _on_file_received(self, path_str: str) -> None:
        """Validate extension; on accept populate session; on reject show error.

        Security note (T-02-04-01): extension whitelist check happens BEFORE
        any file I/O. pathlib.Path normalises the path.
        """
        p = pathlib.Path(path_str)
        ext = p.suffix.lower()

        if ext not in SUPPORTED_EXTENSIONS:
            self._show_error(ERR_UNSUPPORTED_EXT.format(ext=p.suffix))
            return

        # Clear any prior error
        self._error_label.setVisible(False)
        self._error_label.setText("")

        # Store the source path
        self._session.source_path = p
        self._file_name_label.setText(p.name)
        self._file_name_label.setToolTip(str(p))

        # Populate sheets metadata for wizard routing decision (WIZ-03)
        try:
            sheets = list_sheets(p)
            self._session.sheets = sheets
        except EleitorumError as err:
            # T-02-04-02: display message_pt only — never a traceback
            self._show_error(err.message_pt)
            self._session.source_path = None
            self._file_name_label.setText("")

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _show_error(self, message: str) -> None:
        """Display the inline error label with the given PT-PT message."""
        self._error_label.setText(message)
        self._error_label.setVisible(True)

    # ------------------------------------------------------------------
    # NavBar contract
    # ------------------------------------------------------------------

    def is_complete(self) -> bool:
        """Return True iff session.source_path has been set (Próximo enabled)."""
        return self._session.source_path is not None
