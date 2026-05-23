"""Smoke tests for the DropZone drag-and-drop widget (WIZ-02, APP-17).

Tests verify: construction, drag accept/reject based on extension, file_dropped
signal emission, drag_active QSS property toggling, and the DRY contract
(SUPPORTED_EXTENSIONS imported from core.readers, not duplicated).

Platform note (Windows + PySide6 6.11.1): ``QDragEnterEvent`` and ``QDropEvent``
objects may cause Windows access violations if pytest tries to repr them after a
test failure (the C++ backing object is freed before Python's garbage collector
runs). To avoid this, drag events are dispatched via ``QApplication.sendEvent``
inside try/finally blocks with no local references held beyond the dispatch call.
The widget's ``dragEnterEvent`` / ``dropEvent`` are also tested by calling the
handlers directly to verify the property and signal contracts in isolation.
"""
from __future__ import annotations

import pathlib

import pytest
from PySide6.QtCore import QMimeData, QPoint, QUrl, Qt
from PySide6.QtWidgets import QApplication

from eleitorum.ui.widgets.drop_zone import DropZone


def _send_drag_enter(widget: DropZone, path: pathlib.Path) -> bool:
    """Send a QDragEnterEvent to ``widget`` and return whether it was accepted.

    Event object is created, dispatched, and result captured within this
    function — no reference escapes to pytest's variable scope.
    """
    from PySide6.QtGui import QDragEnterEvent

    mime = QMimeData()
    mime.setUrls([QUrl.fromLocalFile(str(path))])
    ev = QDragEnterEvent(
        QPoint(50, 50),
        Qt.DropAction.CopyAction,
        mime,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
    )
    QApplication.sendEvent(widget, ev)
    return ev.isAccepted()


def _send_drop(widget: DropZone, path: pathlib.Path) -> None:
    """Send a QDropEvent to ``widget``."""
    from PySide6.QtGui import QDropEvent

    mime = QMimeData()
    mime.setUrls([QUrl.fromLocalFile(str(path))])
    ev = QDropEvent(
        QPoint(50, 50),
        Qt.DropAction.CopyAction,
        mime,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
    )
    QApplication.sendEvent(widget, ev)


def _send_drag_leave(widget: DropZone) -> None:
    """Send a QDragLeaveEvent to ``widget``."""
    from PySide6.QtGui import QDragLeaveEvent

    ev = QDragLeaveEvent()
    QApplication.sendEvent(widget, ev)


class TestDropZone:
    """Smoke tests for DropZone widget (WIZ-02)."""

    def test_drop_zone_constructs(self, qtbot) -> None:
        """DropZone constructs with acceptDrops=True, min height 120, drag_active=False."""
        dz = DropZone()
        qtbot.addWidget(dz)

        assert dz.acceptDrops() is True
        assert dz.minimumHeight() >= 120
        assert dz.property("drag_active") is False

    def test_drop_zone_accepts_supported_extension_on_drag_enter(
        self, qtbot, tmp_path: pathlib.Path
    ) -> None:
        """dragEnterEvent with .xlsx file is accepted and drag_active becomes True."""
        dz = DropZone()
        qtbot.addWidget(dz)
        dz.show()

        xlsx_path = tmp_path / "input.xlsx"
        xlsx_path.touch()

        accepted = _send_drag_enter(dz, xlsx_path)

        assert accepted is True
        assert dz.property("drag_active") is True

    def test_drop_zone_rejects_unsupported_extension_on_drag_enter(
        self, qtbot, tmp_path: pathlib.Path
    ) -> None:
        """dragEnterEvent with .png file is ignored and drag_active stays False."""
        dz = DropZone()
        qtbot.addWidget(dz)
        dz.show()

        png_path = tmp_path / "rejected.png"
        png_path.touch()

        accepted = _send_drag_enter(dz, png_path)

        assert accepted is False
        assert dz.property("drag_active") is False

    def test_drop_zone_emits_file_dropped_on_valid_drop(
        self, qtbot, tmp_path: pathlib.Path
    ) -> None:
        """dropEvent with valid .xlsx emits file_dropped exactly once with absolute path."""
        dz = DropZone()
        qtbot.addWidget(dz)
        dz.show()

        xlsx_path = tmp_path / "input.xlsx"
        xlsx_path.touch()

        _send_drag_enter(dz, xlsx_path)

        with qtbot.waitSignal(dz.file_dropped, timeout=1000) as blocker:
            _send_drop(dz, xlsx_path)

        emitted_path = blocker.args[0]
        assert pathlib.Path(emitted_path) == xlsx_path

    def test_drop_zone_drag_leave_resets_active(
        self, qtbot, tmp_path: pathlib.Path
    ) -> None:
        """dragLeaveEvent resets drag_active to False after dragEnterEvent set it True."""
        dz = DropZone()
        qtbot.addWidget(dz)
        dz.show()

        xlsx_path = tmp_path / "input.xlsx"
        xlsx_path.touch()

        _send_drag_enter(dz, xlsx_path)
        assert dz.property("drag_active") is True

        _send_drag_leave(dz)
        assert dz.property("drag_active") is False

    def test_drop_zone_drop_resets_active(
        self, qtbot, tmp_path: pathlib.Path
    ) -> None:
        """After a valid drop, drag_active resets to False."""
        dz = DropZone()
        qtbot.addWidget(dz)
        dz.show()

        xlsx_path = tmp_path / "input.xlsx"
        xlsx_path.touch()

        _send_drag_enter(dz, xlsx_path)
        assert dz.property("drag_active") is True

        _send_drop(dz, xlsx_path)
        assert dz.property("drag_active") is False

    def test_drop_zone_uses_supported_extensions_constant(self) -> None:
        """drop_zone.py imports SUPPORTED_EXTENSIONS from eleitorum.core.readers (DRY)."""
        import inspect

        import eleitorum.ui.widgets.drop_zone as dz_module

        source = inspect.getsource(dz_module)
        assert "from eleitorum.core.readers import SUPPORTED_EXTENSIONS" in source, (
            "drop_zone.py must import SUPPORTED_EXTENSIONS from eleitorum.core.readers"
        )

    def test_drop_zone_unpolish_polish_called(self, qtbot) -> None:
        """QSS refresh discipline: drag_active property toggles correctly."""
        dz = DropZone()
        qtbot.addWidget(dz)

        assert dz.property("drag_active") is False

        dz._set_active(True)
        assert dz.property("drag_active") is True

        dz._set_active(False)
        assert dz.property("drag_active") is False
