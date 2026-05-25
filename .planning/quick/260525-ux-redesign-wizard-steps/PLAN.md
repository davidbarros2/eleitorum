---
slug: 260525-ux-redesign-wizard-steps
status: in-progress
created: 2026-05-25
---

# Quick Task: UX Redesign — Wizard Steps 3–5

## Goal

Fix all unacceptable UX issues found during manual testing:
1. Step 3 column picker: replace combo-box approach with visual table + clickable column headers
2. Step 4 preview: add column headers to table, remove confusing log section
3. Routing bug: after write, route to STEP_DONE (step 5) not back to STEP_PREVIEW
4. Auto-written log file on success: remove it (log stays in memory only)
5. Success screen: add "Ver log" toggle button

## Tasks

### T1 — strings.py: add new PT-PT string constants
File: `src/eleitorum/ui/strings.py`
Add constants for:
- Column picker instructions
- QMenu role labels ("Nº Mecanográfico", "Nome")
- Column header format strings ("[MEC]", "[NOME]", unassigned)
- "Ver log" / "Fechar log" button labels
- No-columns-available message

### T2 — session.py: add raw_preview_rows field
File: `src/eleitorum/ui/session.py`
Add: `raw_preview_rows: list[list] | None = None`
This stores the first ~20 raw file rows for the new visual column picker.

### T3 — wizard.py: populate raw_preview_rows + fix routing + reset + connect signal
File: `src/eleitorum/ui/wizard.py`
Changes:
a) `_populate_column_headers`: store first 20 raw rows in `session.raw_preview_rows`
b) `_on_processing_to_preview`: if `result.output_path is not None` → show_success → STEP_DONE; else dry-run → STEP_PREVIEW
c) `reiniciar`: also reset `session.raw_preview_rows = None`
d) `__init__`: connect `self._step_columns.completion_changed` to `_update_navbar_for_current_step`

### T4 — step_columns.py: complete redesign
File: `src/eleitorum/ui/steps/step_columns.py`
New design:
- Show QTableWidget with raw file rows (up to 20)
- QHeaderView.sectionClicked → QMenu with "Nº Mecanográfico" / "Nome" (only "Nome" for elegiveis)
- Header labels updated after each assignment: "[MEC] col_name", "[NOME] col_name", "col_name"
- completion_changed Signal emitted when assignment changes
- is_complete(): True when required columns are assigned (both for caderno, just name for elegiveis)
- Instructions text above the table

### T5 — step_preview.py: add column headers, remove log section
File: `src/eleitorum/ui/steps/step_preview.py`
Changes:
- Remove: _summary_transforms_label, _ver_detalhes_btn, _log_view and all related wiring
- Keep: _summary_rows_label (row count)
- Add: setHorizontalHeaderLabels to table after populate_from_session
  - caderno: ["Nº Mecanográfico", "Nome", "Categoria"]
  - elegiveis: ["Nome"]

### T6 — step_done.py: add "Ver log" to success page
File: `src/eleitorum/ui/steps/step_done.py`
Changes on success page:
- Add BTN_VER_DETALHES_ABRIR button (flat) after summary label
- Add QTextEdit (read-only, max 200px, initially hidden) for log content
- show_success: populate log text from result.log_entries
- Toggle slot: show/hide log view, update button text

### T7 — pipeline.py: remove auto log file write on success
File: `src/eleitorum/core/pipeline.py`
- Remove: `log_path = elt_logging.write_log_file(builder, output_path)` call
- Change success PipelineResult: `log_path=None`
- Keep: write_error_log_file on failure paths (unchanged)

### T8 — Update tests that break
Files: `tests/unit/ui/test_step_columns.py`, potentially `tests/unit/ui/test_step_preview.py`, `tests/unit/ui/test_step_done.py`, `tests/unit/ui/test_step_processing.py`
Update tests to match new widget APIs.

## Acceptance Criteria

- Step 3: user sees raw data table; clicking a column header shows menu; "Próximo" only enables when required columns are assigned
- Step 4: preview table has column headers; no log/transformation count visible
- After write: reaches step 5 (success screen) with "Pronto!" heading
- Success screen: has "Ver log" button; clicking it shows log inline; "Abrir pasta" opens folder
- Only 1 file saved (the .csv); no auto-written .txt log file
- No regression in steps 1–2
