---
slug: fix-step3-column-headers
status: complete
date: 2026-05-25
commit: 860b590
---

# Summary

Fixed Step 3 (column mapping) showing empty dropdowns and manual picks being ignored.

## Root cause
`session.column_headers` was never populated. `StepColumns.populate_from_session()`
reads this list to fill the QComboBox widgets; with it always `None`, every combo
was empty and unselectable.

## Changes
- **session.py** — added `pre_detection: dict | None = None` field to carry the
  wizard's pre-scan result (header row index + detected column indices)
- **pipeline.py** — added `manual_header_row_index` to `PipelineSource`; fixed
  `manual_mapping` to activate for elegiveis when only `manual_name_col` is set
- **wizard.py** — added `_populate_column_headers()` that reads the file, detects
  the header row, runs `detect_columns()`, and stores `column_headers` +
  `pre_detection` on the session before STEP_COLUMNS is shown; added
  `_build_pipeline_source()` helper so both the dry-run and write pass honour
  the user's column choices from step 3
- **step_columns.py** — falls back to `session.pre_detection` when
  `pipeline_result` is None (first visit to step 3)

## Result
396 passed, 1 skipped — no regressions.
