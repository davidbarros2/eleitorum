# EleitorUM

## What This Is

A small, focused Windows desktop utility that normalizes electoral roll and eligibility list files for Universidade do Minho. It accepts any Excel-readable file format (XLSX, XLS, ODS, CSV, TSV), validates and transforms the data according to strict rules, and produces an exact byte-format CSV output accepted by the university's electoral platform — along with a granular transformation log. Built for a non-developer staff member who currently does this by hand in Excel and Notepad.

## Core Value

Receive an arbitrary input file, validate it, transform it into the exact format required by the electoral system, and save the result — zero manual fixing required afterward.

## Requirements

### Validated

Validated in Phase 1 (core-pipeline):

- [x] Accept XLSX, XLSM, XLS, ODS, CSV, and TSV input files
- [x] Auto-detect encoding for text files (charset-normalizer) with PT-PT fallback message
- [x] Auto-detect header row within the first 10 rows; tolerant column name matching (D-01 hybrid)
- [x] Generate caderno eleitoral output: `personnel_number;name;category` (category always empty)
- [x] Generate elegíveis output: `personnel_number;designation` (0-indexed, NFKD alphabetically sorted)
- [x] Output format: UTF-8 with BOM, semicolon separator, CRLF line endings, no quoting, trailing newline
- [x] Mecanográfico validation: valid prefixes (A, PG, ID, F, D, B, Q, EX), positive integer, no leading zeros
- [x] Mecanográfico case normalization: majority-wins (lowercase on tie)
- [x] Mecanográfico uniqueness: no duplicates within prefix; no F/D/B cross-prefix collisions
- [x] Name whitespace normalization: trim, collapse all whitespace types (incl. ZWSP U+200B) to single space
- [x] Name comma removal (logged)
- [x] Name parenthetical annotation removal (logged)
- [x] Mojibake auto-correction for deterministic UTF-8-read-as-Latin-1 patterns
- [x] Unreadable character (`�`) removal with logging (keep rest of name)
- [x] Excel numeric float quirk handling (14891.0 → "14891")
- [x] Skip trailing empty rows silently (log count)
- [x] Fail-fast, never-partial philosophy: no output file if any error occurs
- [x] Error log file (`_ERRORS_`) created on failure with per-row details in PT-PT
- [x] Transformation log file (`_LOG_`) created on success with per-change entries
- [x] Test suite: unit tests for all transformation/validation rules (91.26% coverage); 18 integration tests; synthetic fixtures only
- [x] Performance: 150,000-row pipeline in 3.5s (budget 10s); headless core runs in background-thread-safe mode

### Active

- [ ] Wizard UI with 5–6 sequential steps guiding the user through the full process
- [ ] Scrollable preview of transformed output (~50 rows) before save, with summary panel
- [ ] Never overwrite input file; prompt or auto-rename if destination exists
- [ ] Light and dark themes (follows system default; toggle in UI; persisted)
- [ ] Window state persistence: size, position, last directory, theme
- [ ] UMinho visual identity: `#a21a1c` red accent, Inter font (bundled), WCAG AA contrast
- [ ] WCAG AA keyboard accessibility: full tab navigation, visible focus indicators
- [ ] All user-facing strings in idiomatic European Portuguese (PT-PT), centralized in `strings.py`
- [ ] First-run welcome screen (flag in QSettings; accessible via Ajuda menu afterward)
- [ ] About dialog with app name, version, UMinho disclaimer (PT-PT), license, repo link
- [ ] Minimal menu bar: Ficheiro / Ver / Ajuda
- [ ] APP_NAME constant in config module; `RENAMING.md` checklist for future renames
- [ ] `SPECIFICATION.md` in repo root (this spec is the canonical reference)
- [ ] PyInstaller single-file `.exe` (or single-folder ZIP if startup > 3s); build script
- [ ] Version embedded in executable; build produces `EleitorUM-1.0.0-win64.exe`
- [ ] GitHub Actions CI: ruff lint + format check, mypy/pyright, pytest, build on v1.0.0 tag
- [ ] Test suite: unit tests for all transformation/validation rules (≥ 90% coverage); integration tests for full pipeline; synthetic fixtures only (no real personal data)
- [ ] `pip audit` in CI to surface CVEs
- [ ] Performance: 150,000-row XLSX → validated CSV in under 10 seconds; UI stays responsive (background thread)
- [ ] Minimum window size 600×500; initial size 900×650 centered on primary monitor

### Out of Scope

- General-purpose CSV/Excel tooling — the product normalizes for one specific platform only
- Duplicate detection across multiple files — one file per run, by design
- Data entry / manual row editing in the UI — the tool transforms, not edits
- Network connectivity of any kind — no telemetry, auto-update checks, or HTTP calls
- Multi-platform builds — Windows 10/11 only
- Iterative releases / maintenance — ships once as v1.0.0; archived afterward
- Installer (unless provided as optional, alongside the portable build)
- Extensibility hooks, plugin systems, or abstract base classes for hypothetical future use
- Internationalization framework — product ships in PT-PT only and stays that way
- OAuth or any authentication mechanism — fully offline desktop tool

## Context

- **Primary user:** a single staff member at UMinho responsible for preparing electoral files; comfortable with Windows and Excel but not a developer. Secondary users are colleagues or successors.
- **Current pain:** normalization is done manually with Excel and Notepad — tedious, error-prone, recurrent.
- **Electoral platform constraint:** the consuming system accepts only one specific byte-exact CSV format (Section 5 of SPECIFICATION.md). Deviations cause rejection.
- **Real data quirks documented:** mojibake corruption, parenthetical annotations (`(Coordenador)`), trailing commas in names, mixed prefix casing, Excel numeric floats for mecanográficos, multi-sheet workbooks with empty sheets, title rows before the actual header.
- **One open question before v1.0.0:** BOM in output (spec says with BOM; product owner will test against platform). One-line change in `output.py` if BOM must be dropped.
- **Lifecycle:** single-version. Development → v1.0.0 → archive. No v1.1 planned.
- **Repository:** public, read-only mirror. Issues, PRs, Discussions, Wiki, Sponsors, Projects all disabled. MIT license.

## Constraints

- **Tech stack:** Python 3.11+, PySide6, openpyxl, xlrd, odfpy, pandas (input normalization), stdlib `csv` (output), chardet/charset-normalizer, PyInstaller. Substitutions allowed with justification.
- **Cost:** zero — all dependencies must be open-source and freely redistributable; license compatibility verified for every dependency.
- **Standalone:** double-click `.exe` — no Python, no pip, no terminal required by the user.
- **Offline:** absolutely no network calls at runtime (or in CI tooling that executes on user machines).
- **Platform:** Windows 10 and Windows 11. Builds tested on both.
- **Performance:** 150,000 rows in < 10 seconds on a typical office laptop; UI thread stays live (background worker).
- **Privacy:** no real personal data in the repository; test fixtures are fully synthetic; no data leaves the user's machine except to their chosen output location.

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Python + PySide6 + PyInstaller | Zero-cost, cross-dev ergonomics, standalone Windows EXE | — Pending |
| UTF-8 with BOM output | Inferred from working sample files accepted by electoral platform | — Pending (owner to validate) |
| Semicolon separator, CRLF, no quoting | Exact byte format extracted from platform-accepted working files | ✓ Validated Phase 1 |
| Caderno: category column always empty | Observed in working files; platform may require the column even if unused | ✓ Validated Phase 1 |
| Elegíveis: 0-indexed, alphabetically sorted, index generated by tool | Observed in working files | ✓ Validated Phase 1 |
| Case normalization by majority (lowercase on tie) | Avoids silent all-caps or all-lowercase without human input | ✓ Validated Phase 1 |
| F/D/B share a numeric namespace for uniqueness | Reflects how UMinho issues mecanográficos | ✓ Validated Phase 1 |
| Fail-fast, never-partial output | Prevents user submitting corrupt partial files to platform | ✓ Validated Phase 1 |
| Commas removed from names | Only accidental trailing commas observed in real data; no valid use case | ✓ Validated Phase 1 |
| Parenthetical annotations removed | Observed `(Coordenador)` in real data; not part of the name | ✓ Validated Phase 1 |
| ZWSP and exotic whitespace collapsed | Python `\s` does not match U+200B; explicit char class required | ✓ Validated Phase 1 |
| charset-normalizer replaces chardet | Faster, MIT-clean, no relicensing dispute | ✓ Validated Phase 1 |
| Wizard UI pattern | Sequential, one-thing-at-a-time — appropriate for non-developer user | — Pending |
| APP_NAME as a single constant + RENAMING.md | Product owner wanted name to be trivially changeable | — Pending |
| Disclaimer required in README + About dialog | Tool is independent; not officially affiliated with UMinho | — Pending |
| Synthetic-only test fixtures | Real personal data must never enter the repository | ✓ Validated Phase 1 |
| Single-version lifecycle; archive after v1.0.0 | Deliberate: build the v1 it needs and stop | — Pending |

## Current State

Phase 1 complete (2026-05-23). Headless core pipeline fully implemented and verified: 8 core modules (`errors`, `readers`, `detection`, `transform`, `validate`, `output`, `logging`, `pipeline`), 237 tests passing, 91.26% coverage, 3.5s for 150k rows.

Phase 2 (ui-scaffold-+-wizard-steps) is next: PySide6 application skeleton, wizard framework, and file picker step.

## Evolution

This document evolves at phase transitions and milestone boundaries.

Last updated: 2026-05-23

**After each phase transition** (via `/gsd-transition`):
1. Requirements invalidated? → Move to Out of Scope with reason
2. Requirements validated? → Move to Validated with phase reference
3. New requirements emerged? → Add to Active
4. Decisions to log? → Add to Key Decisions
5. "What This Is" still accurate? → Update if drifted

**After each milestone** (via `/gsd-complete-milestone`):
1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-05-23 after initialization*
