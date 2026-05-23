# Phase 1: Core Pipeline - Context

**Gathered:** 2026-05-23
**Status:** Ready for planning

<domain>
## Phase Boundary

Deliver the complete Qt-free processing pipeline: file reading (XLSX/XLSM/XLS/ODS/CSV/TSV), encoding detection, header-row detection, column detection, all transformation rules, all validation rules, CSV output writing, and log file generation. Zero Qt imports in any of these modules. Phase ends with ≥90% unit-test coverage over core modules — this is the hard gate before Phase 2 begins.

**In scope:** INP-01–13, DET-01–07, TRF-01–15, VAL-01–09, OUT-01–12, LOG-01–07, PERF-01, PERF-03

**Out of scope:** anything PySide6, QWidget, QThread, QApplication, or UI-related — those are Phase 2.

</domain>

<decisions>
## Implementation Decisions

### Column Detection Strategy
- **D-01:** Use **hybrid detection** — synonym-list matching (per spec Section 6.5) as the primary method; regex format-matching (prefix+number pattern `^[A-Za-z]{1,2}\d+$`) as fallback when no column name matches any synonym.
  - Rationale: the product owner confirmed that real UMinho files use 10–50+ different column name variants; format-based detection is more robust as a fallback than failing to manual-mapping mode unnecessarily.
  - The format-based fallback scans each non-name column's data values; if ≥ 70% match the mecanográfico pattern, that column is flagged as the mecanográfico candidate.

### Sort Order for Elegíveis Output
- **D-02:** Sort key: `unicodedata.normalize('NFKD', designation.casefold()).encode('ascii', 'ignore').decode('ascii')`
  - Strips diacritics before comparison: ã→a, é→e, ç→c, etc.
  - Case-insensitive (casefold before normalization).
  - Produces consistent, reproducible ordering matching Portuguese alphabetical convention.
  - Handles both person names and non-person designations (parish names like `Gualtar`, `São Vítor`) correctly.
  - Sort is stable (preserves original order for identical sort keys, though duplicates are already rejected by VAL-03/VAL-04).

### BOM in Output
- **D-03:** Implement with BOM (`encoding="utf-8-sig"` in stdlib csv) per spec Section 5.1. Keep BOM as a named constant `USE_BOM = True` in `output.py` — a one-line change if the electoral platform rejects BOM.
  - **Status:** pending product owner validation against live platform (Section 17 of spec). No test conducted yet. Implementation proceeds with BOM.

### Pipeline Progress API (Phase 2 compatibility)
- **D-04:** The pipeline entry point accepts an optional progress callback: `run_pipeline(source, output_type, progress_cb=None)` where `progress_cb: Callable[[int, int], None] | None` receives `(current_row, total_rows)`.
  - This allows Phase 2's QThread worker to hook in without modifying core modules.
  - When `progress_cb` is None (unit tests, CLI), the pipeline runs silently.

### Module Structure
- **D-05:** Exactly per spec Section 13.2 — no deviations:
  ```
  src/eleitorum/core/
    readers.py      — per-format input readers (openpyxl/xlrd/odfpy/csv)
    detection.py    — encoding detection, header-row scoring, column matching
    transform.py    — mecanográfico + name transformation rules
    validate.py     — uniqueness checks, format validation
    output.py       — CSV writer (byte-exact format, BOM, CRLF, no quoting)
    logging.py      — transformation log builder
    errors.py       — custom exception hierarchy, PT-PT message strings
    pipeline.py     — orchestrator that calls all of the above in order
  src/eleitorum/
    config.py       — APP_NAME constant, version, paths
    version.py      — version string
  ```

### Encoding Detection Threshold
- **D-06:** Use confidence threshold **≥ 0.85** (from REQUIREMENTS.md INP-07 — more conservative than spec Section 4.2's 0.80; prefer the tighter value).
  - BOM is trusted unconditionally (no confidence check needed).
  - Fallback chain: UTF-8 BOM → UTF-8 → Windows-1252 → ISO-8859-1.
  - Library: `charset-normalizer` (not `chardet` — see CLAUDE.md for licensing rationale).

### Error Handling Philosophy
- **D-07:** Two-tier error model per spec Section 7.2:
  - **Hard errors** (invalid prefix, duplicate mecanográfico, F/D/B collision, empty name, missing required column, unsupported file type) → raise a custom exception immediately; no output file; `_ERRORS_` log produced.
  - **Soft issues** (`�` removal, ambiguous mojibake not corrected) → log `AVISO` entry; processing continues; issues surfaced in preview for user review.

### Mecanográfico Prefix List
- **D-08:** Valid prefixes are exactly `{A, PG, ID, F, D, B, Q, EX}` — confirmed complete per spec Section 6.1. Any other prefix → hard error. F/D/B share a numeric namespace; A/PG/ID/Q/EX have independent namespaces.

### Claude's Discretion
- Mojibake detection implementation: scan for `Ã` followed by a byte in 0x80–0xBF range; attempt `string.encode('latin-1').decode('utf-8')`; accept only if result is clean (no remaining Ã sequences, decodes without error).
- Internal exception hierarchy naming and structure (must produce PT-PT messages matching spec Section 7.3 examples).
- Test fixture organization within `tests/unit/` and `tests/fixtures/generators.py` (per spec Section 14.3 fixture list — all 15 fixture functions specified).

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Primary Specification
- `.planning/eleitorum.md` — **canonical specification** — single source of truth for all business rules, output format, transformation rules, validation rules, logging format, module structure, and UI flow. Sections most relevant to Phase 1:
  - Section 4: Input handling (file types, encoding detection, multi-sheet, header detection, column detection)
  - Section 5: Output specifications (byte-exact format, caderno and elegíveis formats with examples)
  - Section 6: Transformation rules (mecanográfico format, case normalization, uniqueness, names, column synonyms, mojibake, Excel quirks, trailing rows)
  - Section 7: Validation and error handling (fail-fast philosophy, error categories, PT-PT message style with examples)
  - Section 8: Logging (format, tags, example log with timestamps, error log)
  - Section 13.2: Repository structure (exact module layout to follow)
  - Section 14: Testing strategy (coverage targets, fixture function list)
  - Section 17: Open questions (BOM pending validation)

### Requirements (authoritative IDs and precise values)
- `.planning/REQUIREMENTS.md` — requirement IDs (INP-01–13, DET-01–07, TRF-01–15, VAL-01–09, OUT-01–12, LOG-01–07, PERF-01, PERF-03) with exact numerical values (e.g., confidence threshold 0.85, 10-row header scan window, ~64 KB encoding read, 150k rows / 10s target).

### Phase Scope and Success Criteria
- `.planning/ROADMAP.md` §"Phase 1: Core Pipeline" — five success criteria that define "done" for this phase (byte-exact output, all real-data quirks handled, fail-fast with `_ERRORS_` log, 150k-row performance, ≥90% pytest-cov with no Qt imports).

### Tech Stack Rationale
- `CLAUDE.md` — technology stack decisions (charset-normalizer over chardet, pandas 3.0 CoW semantics, openpyxl read_only mode, stdlib csv for output).

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- None — this is Phase 1. The repository contains no application code yet. All modules are created from scratch in this phase.

### Established Patterns
- None yet — patterns will be established by this phase and documented for Phase 2.

### Integration Points
- **Phase 2 hook:** `pipeline.run_pipeline(source, output_type, progress_cb)` is the single seam Phase 2's QThread worker will call. Design this function signature carefully — it cannot change between phases without breaking Phase 2.
- **Test fixtures:** `tests/fixtures/generators.py` with all 15 functions (per spec Section 14.3) is consumed by Phase 1 unit tests and later by Phase 3 integration tests. Make it importable without QApplication.

</code_context>

<specifics>
## Specific Ideas

- **Column name detection note:** the product owner confirmed there is no single standard column header for mecanográfico across UMinho departments — 10 to 50+ variants observed. The format-based fallback (regex scan on data values) is not a nice-to-have — it materially reduces the frequency of "manual mapping required" dialogs.

- **Log format example:** spec Section 8.1 provides a concrete worked log with all tags and formatting. Use it verbatim as the test fixture for LOG-04 (exact log format test).

- **PT-PT error message style:** spec Section 7.3 provides good and bad examples. Bad = technical Python tracebacks. Good = specific row references, what the problem is, and what to do next. All `errors.py` messages must follow the good example pattern.

- **Elegíveis sort note:** the `designation` field can contain short parish names (e.g., `Sé` — 2 characters) and place names (`Padim da Graça`), not just person names. The sort key must handle these gracefully — the Unicode-normalized approach does.

- **Confidence threshold conflict:** spec Section 4.2 says 0.8; REQUIREMENTS.md INP-07 says 0.85. Use **0.85** (more conservative; written specifically for charset-normalizer).

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope. All Phase 1 requirements are clearly bounded by ROADMAP.md and the spec.

</deferred>

---

*Phase: 1-Core Pipeline*
*Context gathered: 2026-05-23*
