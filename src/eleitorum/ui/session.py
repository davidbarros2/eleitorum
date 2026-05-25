"""Wizard session state model for EleitorUM (WIZ-10, D-05).

Defines the single mutable @dataclass that holds all wizard session state.
One instance is created at wizard start and passed to every step widget.

Qt-free contract: NEVER import from PySide6. SessionModel is a plain Python
dataclass, trivially testable without a running QApplication, and safe to
inspect/reset from any thread.

Reset target: WIZ-10 (Reiniciar) resets the wizard by replacing the session
instance with a fresh SessionModel() — no fields need explicit clearing.
"""

from __future__ import annotations

import dataclasses
import pathlib
from typing import Any, Literal


@dataclasses.dataclass
class SessionModel:
    """All mutable wizard state. One instance per session, reset on Reiniciar.

    Fields:
        output_type: The selected output format — 'caderno' or 'elegiveis'.
        source_path: Absolute path to the input file chosen by the user.
        sheet_name: Name of the selected Excel sheet (None for single-sheet/CSV).
        column_map: Dict mapping pipeline role names to column indices/names,
                    populated by StepColumns after detection or manual mapping.
        pipeline_result: PipelineResult returned by the background worker
                         (typed as Any to avoid importing the core module here).
        output_path: Absolute path where the output CSV was saved.
        sheets: List[SheetInfo] from readers.list_sheets(), stored for wizard
                routing — non-None and len > 1 means the sheet-picker step is
                shown (stored as Any to avoid importing readers here).
        column_headers: List of column header names from the input file, parsed
                        after list_sheets() succeeds. Consumed by StepColumns
                        dropdowns to populate the column-choice combos.
        pre_detection:  Column detection result from the wizard's pre-scan
                        (before the pipeline dry-run). Dict with keys:
                        header_row_index, mec_col_index, name_col_index,
                        detection_method. Populated by WizardController before
                        STEP_COLUMNS is shown; consumed by StepColumns.
    """

    output_type: Literal["caderno", "elegiveis"] | None = None
    source_path: pathlib.Path | None = None
    sheet_name: str | None = None
    column_map: dict[str, Any] | None = None
    pipeline_result: Any | None = None
    output_path: pathlib.Path | None = None
    sheets: Any | None = None
    column_headers: list[str] | None = None
    pre_detection: dict[str, Any] | None = None
