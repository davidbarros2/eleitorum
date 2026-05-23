# Features Research — EleitorUM

**Domain:** Desktop data-processing wizard — single file in, validated CSV out
**Researched:** 2026-05-23
**Overall confidence:** HIGH (findings verified against wizard UX literature, Microsoft guidelines, and UX research from NN/g, Baymard, Smashing Magazine)

---

## Table Stakes (must have or users won't trust it)

### 1. Drag-and-drop file acceptance on the first step

**Why expected:** File-handling desktop apps on Windows are expected to support drag-and-drop from Explorer. Users with no developer background reach for it first — they will drag a file onto the window before looking for a button. If the drop target is invisible or missing, trust evaporates immediately.

**What "good" looks like:**
- The entire first wizard step (or a dedicated drop zone within it) is a valid drop target.
- The drop zone changes appearance on hover (dashed border → solid, or colour change) so the user knows it is active.
- After drop, the file path appears in the same field that the "Browse" button populates — both paths must be equivalent.
- The cursor changes to a copy icon (Windows shell standard) when hovering over the drop target.
- Keyboard-only alternative: a "Browse…" button that opens a standard `QFileDialog`.

**Confidence:** HIGH — Microsoft's official Windows drag-and-drop guidelines, NN/g, and Smashing Magazine all confirm this is a standard expectation for file-handling apps.

---

### 2. Progress indication for processing steps

**Why expected:** The spec requires processing up to 150,000 rows in a background thread. Even on fast machines, large files will take 3–8 seconds. A frozen-looking UI during that time is indistinguishable from a crash for a non-developer user.

**What "good" looks like:**
- An indeterminate progress bar (spinner or marquee) while file is loading and parsing — row count not yet known.
- Switch to a determinate progress bar once the row count is known and validation is underway. Show `"Validating row N of M…"` or a percentage.
- The "Next" button is disabled (not hidden) during processing so the user can see it will be available.
- Cancel is always available during long operations and returns the wizard to the previous step cleanly.

**Confidence:** HIGH — Qt threading docs confirm the background worker pattern; UX loading pattern research confirms determinate > indeterminate when count is known.

---

### 3. Summary panel with transformation statistics before save

**Why expected:** The user is about to write a file that will be submitted to an institutional system. They need a confidence check. "50 rows → 48 rows output; 2 rows removed (empty); 3 names normalised" is the kind of statement that builds trust. A bare table of data without context leaves them uncertain.

**What "good" looks like:**
- A summary card above (or beside) the preview table showing: input row count, output row count, rows removed (with reason breakdown), fields normalised, encoding detected.
- ~50 rows of scrollable output preview (as specified). 50 rows is the right number: enough to spot systematic problems (e.g., wrong column) without overwhelming. Verified against Smashing Magazine's data import research.
- Transformed values should be visually distinguished from pass-through values where practical (e.g., a subtle badge or tooltip on cells where the name was changed).
- The preview must show the exact output that will be saved — no surprises after save.

**Confidence:** HIGH — The 50-row figure is already in the spec; the summary panel pattern is confirmed by wizard UX literature and data importer case studies.

---

### 4. Clear, actionable error messages in plain language (PT-PT)

**Why expected:** The primary user is comfortable with Windows and Excel, not data formats. A message like `UnicodeDecodeError: codec 'utf-8' can't decode byte 0xe9` will cause panic and a support call. A message like `"O ficheiro parece estar guardado em Latin-1. Não foi possível ler a linha 47."` is actionable.

**What "good" looks like:**
- Every error message follows the structure: what happened → where it happened (row number, column name) → what to do next.
- Row numbers in error messages must be 1-indexed and match what the user sees in Excel (the source file's row number, not the internal 0-indexed row).
- Never expose Python exception types, stack traces, or internal field names in user-facing messages.
- Errors that refer to the source file must name the column in human terms ("coluna Mecanográfico") not internal names ("column index 2").
- For encoding failures: tell the user the file appears to be in a different encoding, and instruct them to re-save from Excel as UTF-8 or share the file with the tool's maintainer.

**Confidence:** HIGH — NN/g 10-point error design guidelines, Baymard validation/warning research, and multiple UX writing guides confirm this pattern.

---

### 5. Never overwrite the input file; safe output naming

**Why expected:** Non-developer users may select their only copy of the input file as the output location. Overwriting it silently would be catastrophic. This is a zero-tolerance trust item — if it happens once, the tool is abandoned.

**What "good" looks like:**
- Output path defaults to the same directory as the input file with a generated name (e.g., `caderno_eleitoral_YYYYMMDD_HHMMSS.csv`).
- The tool must refuse to write to a path that would overwrite the input file, even if the user explicitly selects it.
- If the default output path already exists (from a prior run), auto-append a counter suffix rather than prompting — the prompt adds friction for a routine re-run.

**Confidence:** HIGH — Specified in PROJECT.md; the UX rationale is well-established (file safety is a basic trust signal).

---

### 6. First-run welcome screen explaining what the tool does

**Why expected:** The tool will be handed to a staff member without training. A welcome screen that explains the 5-step flow in plain language prevents the first confusion from becoming a support request. It doubles as onboarding documentation.

**What "good" looks like:**
- A single screen, shown once (flag persisted in QSettings), with 3–4 sentences describing the process: "Selecione o ficheiro de entrada → Confirme as colunas → Reveja o resultado → Guarde."
- Re-accessible via Ajuda menu — users who dismissed it accidentally should not be stuck.
- No checkbox "don't show again" that requires an extra click — just close it and it is gone.

**Confidence:** HIGH — Standard onboarding pattern for single-function desktop utilities. Specified in PROJECT.md.

---

### 7. Fail-fast: no output file on any validation error

**Why expected:** The output is consumed by an institutional electoral system. A partial or corrupt file submitted to that system causes a downstream error that the user cannot diagnose. The tool must make "no output is better than bad output" the invariant.

**What "good" looks like:**
- If any row fails a hard validation rule, the wizard stops at the validation step and does not advance to the preview or save steps.
- The error log file (`_ERRORS_`) is created so the user has a record of exactly what went wrong.
- The error screen shows the first N errors (e.g., 20) with row-level detail, plus a message like "Foram encontrados 47 erros. Consulte o ficheiro _ERRORS_ para a lista completa."
- The wizard offers two actions: go back to select a corrected file, or close.

**Confidence:** HIGH — Specified in PROJECT.md with explicit rationale; confirmed as the right pattern for systems with a strict downstream format contract.

---

## Differentiators (worth adding if scope allows)

### 1. Transformation log file (`_LOG_`) written alongside output

**Value:** After the user submits the output to the electoral platform, they may be asked "why does this person's name look different from the source file?" The log provides an audit trail: `"Linha 14: Nome 'SILVA, João (Coordenador)' → 'João SILVA' (vírgula removida; anotação entre parêntesis removida)"`. This is a meaningful differentiator for an institutional tool where accountability matters.

**Complexity:** Low — already specified. The transformation pipeline must log changes as it processes; writing a structured text file at the end is trivial.

**Recommendation:** Include. Already in spec. The log is essential for institutional accountability, not a nice-to-have.

---

### 2. Visual diff cues in the preview table

**Value:** Instead of just showing the output, highlight cells where the value was changed from the input. A subtle background colour or an icon in the cell makes it immediately obvious that "this name was normalised" without the user having to compare two files mentally.

**Complexity:** Medium — requires the preview model to carry both original and transformed values per cell, and the table view to render conditionally. It is not a simple table dump.

**Recommendation:** Include a simplified version — at minimum, a "changes" badge on rows that had any transformation. Full per-cell diff is nice but not critical for v1.0.0.

---

### 3. "Start over" (Reiniciar) button throughout the wizard

**Value:** When the user discovers an error on step 4, the fastest recovery is often "load a corrected file" — not click Back four times. A persistent "Reiniciar" action (in the menu bar or as a secondary button) that resets the wizard to step 1 without restarting the application removes friction.

**Complexity:** Low — wizard reset means clearing the application state and returning `currentId()` to the first page.

**Recommendation:** Include. The user is not an undo-style undo user; they think in terms of "start over with the correct file." Back navigation per step is still needed for minor corrections (e.g., wrong sheet selection), but Reiniciar covers the common error case.

**Note on Undo:** Full undo-per-transformation is an anti-feature for this tool (see below). The choice is between Reiniciar (load new file) and nothing. Reiniciar wins.

---

### 4. Column mapping confirmation step when auto-detection succeeds

**Value:** Even when auto-detection finds the columns correctly, showing the user "I found: Mecanográfico → column B, Nome → column C" with a simple confirm/correct UI catches the 10% of cases where detection is right mechanically but wrong semantically (e.g., two similar column names in a multi-sheet file). This step costs the user 2 seconds when everything is fine and saves them from a silent wrong-column output.

**Complexity:** Low — the mapping UI is already required for the failure case. Showing it as a confirmation step even on success is a configuration choice, not extra code.

**Recommendation:** Always show the mapping step (pre-populated with auto-detected values); never silently skip it. The 2-second cost is worth the safety.

---

### 5. Persistent window state (size, position, last directory, theme)

**Value:** Non-developer users use the same tool the same way every time. Remembering the window position and the last input directory removes micro-friction. It signals that the tool "knows" the user. For a recurring task, this matters.

**Complexity:** Low — `QSettings` with 4–5 keys.

**Recommendation:** Include. Already in spec. Do not skip this.

---

## Anti-Features (deliberately excluded — with reasoning)

### 1. Manual data editing in the UI

**Why excluded:** The tool's contract is: accept a file, transform it, output it. If the user can edit rows in the preview table, the tool becomes a spreadsheet editor — a category it is not equipped to be (no undo history, no formula support, no save-draft state). More importantly, it creates a new failure mode: the user edits a value that still violates a validation rule, and the tool must now re-validate incrementally. This is a significant engineering burden with no justification given the actual use case.

**What to do instead:** Surface the exact error with the row number and column name. The user opens their source file (Excel), fixes it, and re-runs. This is the correct workflow and must be the only workflow.

---

### 2. Batch processing (multiple files per run)

**Why excluded:** The spec explicitly limits each run to one input file producing one output set. The user's workflow processes one electoral list at a time. Supporting multiple files introduces questions about combined validation, output naming, partial success handling, and ordering — all complexity with no benefit for the actual user.

---

### 3. Settings / preferences screen for options that have no real user choice

**Why excluded:** Feature creep in small utilities often manifests as a settings screen. For EleitorUM, there are no meaningful user-configurable options: the output format is fixed by the electoral platform, the validation rules are fixed by UMinho's mecanográfico specification, and the encoding is fixed (UTF-8 with BOM). A settings screen with nothing meaningful in it communicates confusion, not power. The only persisted preference is the theme (light/dark), which belongs in the "Ver" menu, not a settings dialog.

---

### 4. Undo / redo within the wizard

**Why excluded:** The wizard processes data deterministically. "Undo" in this context would mean "un-transform a name" — which is meaningless because the source file is unchanged and accessible. The correct recovery from "I made a mistake" is Reiniciar (load the corrected source file). Adding undo machinery would require a mutable transformation state with a history stack — engineering cost with no user value.

---

### 5. Recent files list (MRU menu)

**Why excluded:** MRU menus are valuable when a user switches between multiple different files frequently (e.g., Office documents). For EleitorUM, the user runs the tool against a new file each electoral season — typically once or twice a year. They do not need quick access to last year's file; if they open it again, they will re-navigate from Explorer as they always do. An MRU list adds complexity (persistence, file-exists checks, privacy questions around institutional file paths visible in the UI) with no practical benefit for the usage pattern.

---

### 6. Network connectivity of any kind

**Why excluded:** The tool processes personal data (names and personnel numbers). No data should leave the user's machine. Additionally, the deployment environment may be on a restricted institutional network. Any network call — telemetry, update check, font download — is unacceptable. Already in scope exclusions; noted here as a UX anti-feature because some frameworks add telemetry by default.

---

### 7. Extensibility / plugin hooks for hypothetical future formats

**Why excluded:** The tool is single-version. There is no v1.1. Abstract base classes for "future output formats" or "pluggable validation rules" would add dead code with no user value and maintenance cost with no maintainer. Build what is needed for v1.0.0 and stop.

---

## UX Patterns for Error States

### Pattern 1: Stop-vs-continue decision rule

**Rule:** Fail hard on data integrity errors; warn and continue for cosmetic or ambiguous normalizations.

| Error type | Example | Correct response |
|------------|---------|-----------------|
| Invalid mecanográfico (unknown prefix, duplicates, leading zeros) | `ABC123`, `A001` | Stop. Cannot produce a valid output. Block advance. |
| Unreadable file format | Wrong XLSX structure, encrypted file | Stop immediately at file-load step. |
| Missing required column after mapping | Header not found after 10 rows | Stop at mapping step. |
| Name contains replacement character (`�`) | `Jo�o Silva` | Warn in log; remove character; continue. |
| Mojibake-correctable pattern | `Ã£o` → `ão` | Auto-correct silently; log the change; continue. |
| Name contains comma | `Silva, João` | Auto-correct; log; continue. |
| Trailing empty rows | Last 5 rows are blank | Skip silently; log count; continue. |
| Duplicate mecanográfico (same prefix) | Two rows with `A12345` | Stop. Duplicate uniqueness constraint violation. |

**Rationale:** Baymard's validation-vs-warning research: use stop (validation) when the rule can be checked flawlessly and violation means invalid output. Use warn-and-continue when the correction is deterministic and safe. Never use warn-and-continue when the output would be ambiguous.

---

### Pattern 2: Error message structure for non-technical users

Every hard error message must contain exactly these components, in this order:

1. **What went wrong** — one sentence, no technical terms.
2. **Where it happened** — row number (1-indexed, matching Excel row), column name (as seen in the source file header, not an internal name).
3. **What to do next** — concrete instruction about fixing the source file.

**Example (bad):** `"ValidationError: duplicate key 'A12345' in column index 0"`

**Example (good):** `"Linha 14, coluna Mecanográfico: o número 'A12345' já existe na linha 7. Corrija o ficheiro de origem e tente novamente."`

---

### Pattern 3: Error log file as the authoritative record, not the UI

The UI shows a capped summary (first 20 errors) with a count of total errors. The `_ERRORS_` file is the complete record. This is the right split for this use case:
- The UI message handles the "what do I do right now?" question.
- The `_ERRORS_` file handles the "what exactly is wrong in each row?" question, which the user may share with a colleague.

The UI must tell the user exactly where the error file was saved (absolute path or directory button).

---

### Pattern 4: Guiding the user back to the source file

When an error requires fixing the source file (the most common recovery action), the error screen should:

1. State clearly: "O ficheiro de origem não foi alterado. Corrija-o em Excel e selecione-o novamente."
2. Offer a "Selecionar novo ficheiro" action button that resets to step 1 with the same directory pre-selected.
3. Never offer an "Edit in place" option (see anti-features).

This prevents the user's worst-case misunderstanding: "did the tool corrupt my file?" The answer is always no, and the UI must communicate that proactively.

---

### Pattern 5: Column mapping failure — specific guidance

When auto-detection fails to find a required column, the error must tell the user:

- Which column was not found (by the expected name).
- What column names were found (list them, truncated to 10).
- That they can map manually.

**Example:** `"Não foi possível identificar a coluna Mecanográfico automaticamente. As colunas encontradas são: Nome, Categoria, Número de Pessoal. Selecione a coluna que contém o número mecanográfico."`

This is more useful than "column not found" and avoids a support call.

---

### Pattern 6: Processing state — the UI must never look frozen

- During any operation > 300ms, show a spinner or progress indicator.
- The window title or status bar should change to indicate work is in progress (e.g., `"EleitorUM — A processar…"`).
- The application must remain responsive (window can be moved, resized) even during processing — enforced by the background thread requirement.
- Cancel must be available during processing and must cleanly stop the worker thread.

---

## Notes for Requirements Definition

**1. Row number convention must be decided and documented once.**
All error messages, log entries, and preview row numbers should use the same convention. Recommendation: 1-indexed, matching the row number the user would see if they open the source file in Excel (i.e., include the header row in the count so data row 1 = Excel row 2).

**2. The preview table is not a validation step.**
The preview shows the already-validated, already-transformed output. If the user reaches the preview, validation has passed. Do not re-validate on preview.

**3. Encoding detection belongs at file load, not at validation.**
Chardet/charset-normalizer runs at the moment the file is selected. If encoding cannot be determined with sufficient confidence, the user sees an error at step 1, not step 3. This prevents wasted effort mapping columns for an unreadable file.

**4. The error log and transformation log are distinct files with distinct audiences.**
`_ERRORS_` is created on failure; it is a problem report for the user to read and share.
`_LOG_` is created on success; it is an audit trail for institutional accountability.
They must never be merged into one file.

**5. Keyboard navigation expectations for the wizard.**
Windows users expect: Tab/Shift+Tab to move between controls, Enter to activate the focused button (Next/Finish), Escape to cancel or go back, and Alt+underlined-letter for menu access. PySide6/Qt implements most of this by default; the requirement is not to break it with custom widgets.

**6. Visual transformation indicators in the preview: minimum viable version.**
Full per-cell diff colouring is aspirational. The minimum viable version is a row-level indicator: a small icon or count badge on any row where at least one field was modified. This is sufficient for the user to scan for unexpected changes without complex table model code.

**7. The "Start over" (Reiniciar) affordance is the primary error recovery path.**
Back navigation per step handles minor course corrections. Reiniciar (reset to step 1) handles the common recovery: "I need to fix the source file." Design both. The Back button must preserve state (e.g., sheet selection) when navigating backward within the same file. Reiniciar clears all state.
