"""Step 6 — Success and error dual-state widget (WIZ-07, WIZ-08, APP-19).

Uses a QStackedWidget with two pages (success at index 0, error at index 1).
``show_success(result)`` and ``show_error(result)`` switch between them.

- Success page: output path label, summary (rows/changes), Abrir pasta,
  Processar outro ficheiro, and Sair buttons.
- Error page: error heading, body text, QTextEdit with first 20 failures
  (plus "…e mais N erros" suffix if > 20), Abrir pasta + Processar outro.
  NO Sair button on error page (per UI-SPEC).

Security note (T-02-05-02): output_path is set by the user via QFileDialog in
step 5 (plan 06). QDesktopServices.openUrl() is the standard Qt API; does not
invoke a shell command.

Icons: QStyle.StandardPixmap.SP_DialogApplyButton (success) and
       QStyle.StandardPixmap.SP_MessageBoxCritical (error). Size: 64×64.

Requirements: WIZ-07 (success screen), WIZ-08 (error screen), APP-19 (icons
paired with text for accessibility).
"""

from __future__ import annotations

from PySide6.QtCore import QUrl, Signal
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPushButton,
    QStackedWidget,
    QStyle,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from eleitorum.ui.session import SessionModel
from eleitorum.ui.strings import (
    BTN_ABRIR_PASTA,
    BTN_PROCESSAR_OUTRO,
    BTN_SAIR,
    DONE_ERROR_BODY,
    DONE_PRONTO,
    DONE_SUCCESS_SUMMARY,
    STEP_DONE_ERROR_TITLE,
)

# Max failures shown in error text before "…e mais N erros" suffix
_MAX_FAILURES_SHOWN: int = 20

# Icon size in pixels (APP-19 — icon paired with heading text)
_ICON_SIZE: int = 64


def _make_icon_label(widget: QWidget, pixmap_id: QStyle.StandardPixmap) -> QLabel:
    """Create a QLabel displaying a standard Qt icon at _ICON_SIZE×_ICON_SIZE."""
    icon = widget.style().standardIcon(pixmap_id)
    label = QLabel()
    label.setPixmap(icon.pixmap(_ICON_SIZE, _ICON_SIZE))
    label.setFixedSize(_ICON_SIZE, _ICON_SIZE)
    return label


class StepDone(QWidget):
    """Step 6: dual-state success / error result widget.

    Signals:
        restart_clicked(): emitted when user clicks "Processar outro ficheiro"
            on either page; wizard.py connects this to restart the session.
        quit_clicked(): emitted when user clicks "Sair" on the success page.
            Error page has no Sair button (UI-SPEC invariant).
    """

    restart_clicked = Signal()
    quit_clicked = Signal()

    def __init__(self, session: SessionModel, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._session = session
        self._result_for_open: object | None = None  # last PipelineResult shown
        self._setup_ui()

    def _setup_ui(self) -> None:
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(24, 24, 24, 24)
        root_layout.setSpacing(16)

        self._stack = QStackedWidget()
        root_layout.addWidget(self._stack)

        self._stack.addWidget(self._build_success_page())  # index 0
        self._stack.addWidget(self._build_error_page())  # index 1

        # Start on success page
        self._stack.setCurrentIndex(0)

    # ------------------------------------------------------------------
    # Page builders
    # ------------------------------------------------------------------

    def _build_success_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)

        # Icon — SP_DialogApplyButton (check mark / ok)
        icon_lbl = _make_icon_label(self, QStyle.StandardPixmap.SP_DialogApplyButton)
        layout.addWidget(icon_lbl)

        # "Pronto!" heading
        pronto = QLabel(DONE_PRONTO)
        pronto.setObjectName("displayHeading")
        layout.addWidget(pronto)

        # Output path label (filename only; tooltip = full path)
        self._success_path_label = QLabel("")
        self._success_path_label.setObjectName("mutedText")
        layout.addWidget(self._success_path_label)

        # Summary label: rows + changes
        self._success_summary = QLabel("")
        layout.addWidget(self._success_summary)

        layout.addStretch()

        # Button row
        btn_row = QHBoxLayout()
        self._success_open_folder_btn = QPushButton(BTN_ABRIR_PASTA)
        self._success_restart_btn = QPushButton(BTN_PROCESSAR_OUTRO)
        self._success_restart_btn.setObjectName("primaryButton")
        self._success_quit_btn = QPushButton(BTN_SAIR)

        btn_row.addWidget(self._success_open_folder_btn)
        btn_row.addStretch()
        btn_row.addWidget(self._success_quit_btn)
        btn_row.addWidget(self._success_restart_btn)
        layout.addLayout(btn_row)

        # Connect buttons
        self._success_open_folder_btn.clicked.connect(self._on_open_folder_clicked)
        self._success_restart_btn.clicked.connect(self.restart_clicked)
        self._success_quit_btn.clicked.connect(self.quit_clicked)

        return page

    def _build_error_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)

        # Icon — SP_MessageBoxCritical (x / warning)
        icon_lbl = _make_icon_label(self, QStyle.StandardPixmap.SP_MessageBoxCritical)
        layout.addWidget(icon_lbl)

        # Error heading
        error_heading = QLabel(STEP_DONE_ERROR_TITLE)
        error_heading.setObjectName("displayHeading")
        layout.addWidget(error_heading)

        # Error body text
        self._error_body_lbl = QLabel(DONE_ERROR_BODY)
        self._error_body_lbl.setWordWrap(True)
        layout.addWidget(self._error_body_lbl)

        # Failure list (first 20 + optional suffix)
        self._error_text = QTextEdit()
        self._error_text.setReadOnly(True)
        self._error_text.setMaximumHeight(200)
        layout.addWidget(self._error_text)

        layout.addStretch()

        # Button row — NO Sair on error page (UI-SPEC)
        btn_row = QHBoxLayout()
        self._error_open_folder_btn = QPushButton(BTN_ABRIR_PASTA)
        self._error_restart_btn = QPushButton(BTN_PROCESSAR_OUTRO)
        self._error_restart_btn.setObjectName("primaryButton")

        btn_row.addWidget(self._error_open_folder_btn)
        btn_row.addStretch()
        btn_row.addWidget(self._error_restart_btn)
        layout.addLayout(btn_row)

        # Connect buttons
        self._error_open_folder_btn.clicked.connect(self._on_open_folder_clicked)
        self._error_restart_btn.clicked.connect(self.restart_clicked)

        return page

    # ------------------------------------------------------------------
    # Public API called by wizard.py
    # ------------------------------------------------------------------

    def show_success(self, result: object) -> None:
        """Switch to success page and populate with result data."""
        self._result_for_open = result
        output_path = result.output_path  # type: ignore[attr-defined]
        if output_path is not None:
            self._success_path_label.setText(output_path.name)
            self._success_path_label.setToolTip(str(output_path))
        else:
            self._success_path_label.setText("")
        self._success_summary.setText(
            DONE_SUCCESS_SUMMARY.format(
                rows=result.rows_processed,  # type: ignore[attr-defined]
                changes=result.transformations_applied,  # type: ignore[attr-defined]
            )
        )
        self._stack.setCurrentIndex(0)

    def show_error(self, result: object) -> None:
        """Switch to error page and populate with failure list."""
        self._result_for_open = result
        failures = result.failures  # type: ignore[attr-defined]
        lines: list[str] = []
        for f in failures[:_MAX_FAILURES_SHOWN]:
            lines.append(f"Linha {f.row_index}: {f.column_name} = '{f.value}' — {f.message_pt}")
        if len(failures) > _MAX_FAILURES_SHOWN:
            remaining = len(failures) - _MAX_FAILURES_SHOWN
            lines.append(f"…e mais {remaining} erros.")
        self._error_text.setPlainText("\n".join(lines))
        self._stack.setCurrentIndex(1)

    # ------------------------------------------------------------------
    # Private slots
    # ------------------------------------------------------------------

    def _on_open_folder_clicked(self) -> None:
        """Open the output folder (success) or error log folder (error) in Explorer."""
        if self._result_for_open is None:
            return

        if self._stack.currentIndex() == 1:
            # Error page — open error log folder
            target = self._result_for_open.error_log_path  # type: ignore[attr-defined]
        else:
            # Success page — open output folder
            target = self._result_for_open.output_path  # type: ignore[attr-defined]

        if target is not None:
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(target.parent)))
