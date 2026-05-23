"""DropZone drag-and-drop QFrame target for EleitorUM (WIZ-02).

Accepts file drops when the dragged file's extension is in
``core.readers.SUPPORTED_EXTENSIONS`` (single source of truth — never
duplicated here). Emits ``file_dropped`` with the absolute path on a valid
drop. Toggles the ``drag_active`` QSS dynamic property on dragEnter/dragLeave
so the theme.py DropZone[drag_active="true"] selector applies immediately.

The "ou escolher ficheiro…" button is owned by the parent step_upload widget;
DropZone is solely the drag target.

Security note (T-02-03-01): extension whitelist check via SUPPORTED_EXTENSIONS
runs BEFORE any I/O. The actual file is opened later by readers.py. DropZone
only emits the absolute path string — no file contents are read here.
"""
from __future__ import annotations

import pathlib

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QFrame, QLabel, QVBoxLayout

from eleitorum.core.readers import SUPPORTED_EXTENSIONS
from eleitorum.ui.strings import DROP_ZONE_PLACEHOLDER


class DropZone(QFrame):
    """Drag-and-drop file target that validates file extensions.

    Signals
    -------
    file_dropped : Signal(str)
        Emitted when a file with a supported extension is dropped.
        Carries the absolute path of the dropped file as a string.
    """

    file_dropped = Signal(str)

    def __init__(self, parent: QFrame | None = None) -> None:
        super().__init__(parent)

        self.setAcceptDrops(True)
        self.setMinimumHeight(120)
        self.setProperty("drag_active", False)

        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        placeholder = QLabel(DROP_ZONE_PLACEHOLDER)
        placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        placeholder.setWordWrap(True)
        layout.addWidget(placeholder)

    # ------------------------------------------------------------------
    # Drag event overrides
    # ------------------------------------------------------------------

    def dragEnterEvent(self, event) -> None:  # type: ignore[override]
        """Accept the drag if the first URL has a supported extension."""
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            if urls:
                suffix = pathlib.Path(urls[0].toLocalFile()).suffix.lower()
                if suffix in SUPPORTED_EXTENSIONS:
                    event.acceptProposedAction()
                    self._set_active(True)
                    return
        event.ignore()

    def dragLeaveEvent(self, event) -> None:  # type: ignore[override]
        """Reset drag_active when the drag leaves the widget."""
        self._set_active(False)

    def dropEvent(self, event) -> None:  # type: ignore[override]
        """Accept a valid drop and emit file_dropped with the absolute path."""
        self._set_active(False)
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            if urls:
                path = urls[0].toLocalFile()
                if pathlib.Path(path).suffix.lower() in SUPPORTED_EXTENSIONS:
                    event.acceptProposedAction()
                    self.file_dropped.emit(path)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _set_active(self, value: bool) -> None:
        """Toggle the drag_active QSS dynamic property and refresh style."""
        self.setProperty("drag_active", value)
        # Force QSS re-evaluation (RESEARCH.md Pattern 6 / QSS Dynamic Property Refresh)
        self.style().unpolish(self)
        self.style().polish(self)
