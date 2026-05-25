---
slug: fix-step3-column-headers
date: 2026-05-25
status: in-progress
---

# Fix Step 3 column mapping: empty dropdowns and ignored manual picks

`session.column_headers` is never populated, so StepColumns shows empty
QComboBox widgets the user cannot interact with. Additionally, even if the user
somehow chose columns, `_start_dry_run()` and `_on_preview_save_clicked()` never
pass those choices to the pipeline.

## Tasks

- [ ] 1. session.py — add `pre_detection: dict | None = None` field
- [ ] 2. pipeline.py — add `manual_header_row_index` to PipelineSource; fix `manual_mapping` to also trigger on elegiveis when `manual_name_col` is set
- [ ] 3. wizard.py — add `_populate_column_headers()`; call it before STEP_COLUMNS on both navigation paths; update `_start_dry_run()` and `_on_preview_save_clicked()` to construct PipelineSource with sheet + column map; clear `pre_detection` in `reiniciar()`
- [ ] 4. step_columns.py — read `session.pre_detection` when `pipeline_result` is None
- [ ] 5. Run tests and commit
