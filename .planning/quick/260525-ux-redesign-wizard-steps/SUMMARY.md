---
slug: 260525-ux-redesign-wizard-steps
status: complete
completed: 2026-05-25
commit: ffd1d93
---

# Summary

All 7 files changed, 359 tests passing.

## What was done

1. **Step 3 — visual column picker**: Replaced combo-box approach with a QTableWidget showing the raw file rows. Clicking a column header opens a QMenu to assign it as "Nº Mecanográfico" or "Nome". Header labels update to show `[MEC]` / `[NOME]` prefix. `is_complete()` gates the Próximo button — it only enables when the required columns are assigned.

2. **Step 4 — column headers in preview**: Added `setHorizontalHeaderLabels` with "Nº Mecanográfico / Nome / Categoria" (caderno) or "Nome" (elegiveis). Removed the confusing "Alterações aplicadas" counter and "Ver detalhes" log toggle.

3. **Routing fix**: `_on_processing_to_preview` now checks `result.output_path`. If set (actual write), routes to STEP_DONE success screen. If None (dry-run), routes to STEP_PREVIEW. This was the root cause of "Passo 5 de 5" never being reached.

4. **No auto log file**: The UI passes `write_success_log=False` to `run_pipeline`. The pipeline keeps the flag with default `True` so integration tests are unaffected.

5. **Success screen**: Added "Ver log" / "Fechar log" toggle button on the success page. Shows `result.log_entries` inline in a QTextEdit.

6. **session.py**: Added `raw_preview_rows` field — stores first 20 raw rows for the visual picker.
