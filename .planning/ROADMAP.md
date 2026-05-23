# Roadmap: EleitorUM

## Overview

EleitorUM is built in four sequential horizontal layers. Phase 1 constructs the entire Qt-free core pipeline — all reading, detection, transformation, validation, output writing, and logging — and verifies it to ≥90% unit-test coverage before any UI work begins. Phase 2 builds the full PySide6 application shell and all six wizard steps on top of that validated core. Phase 3 wires the layers together with integration tests, synthetic fixture generators, and end-to-end assertions covering every edge case in the spec. Phase 4 produces the distributable Windows executable, GitHub Actions CI/CD workflows, and all repository documentation artifacts needed for the public v1.0.0 release.

## Phases

**Phase Numbering:**

- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [ ] **Phase 1: Core Pipeline** - All Qt-free processing: file readers, encoding detection, header/column detection, transformation rules, validation, output writer, log builder, custom exceptions, and PT-PT error messages — with ≥90% unit-test coverage before Phase 2 starts
- [ ] **Phase 2: UI Scaffold + Wizard Steps** - QApplication setup, QStackedWidget + SessionModel + NavBar, QThread worker, all six wizard steps, theme system (light + dark), menu bar, About dialog, first-run welcome screen, window chrome, and QSettings persistence
- [ ] **Phase 3: Integration, End-to-End Testing + Fixtures** - Wire pipeline to UI, integration tests for both output types, synthetic fixture generators for all 15 fixture types, pytest-qt smoke tests per wizard step, and byte-exact output assertions
- [ ] **Phase 4: Build, CI, Packaging + Distribution Artifacts** - PyInstaller spec and build script, icon generation, font and plugin bundling, Windows PE metadata, GitHub Actions CI/CD, SHA-256 checksum, CHANGELOG v1.0.0, and all repository documentation files

## Phase Details

### Phase 1: Core Pipeline

**Goal**: The complete processing pipeline runs correctly and is verified to ≥90% unit-test coverage — with zero Qt imports anywhere in the core layer
**Depends on**: Nothing (first phase)
**Requirements**: INP-01, INP-02, INP-03, INP-04, INP-05, INP-06, INP-07, INP-08, INP-09, INP-10, INP-11, INP-12, INP-13, DET-01, DET-02, DET-03, DET-04, DET-05, DET-06, DET-07, TRF-01, TRF-02, TRF-03, TRF-04, TRF-05, TRF-06, TRF-07, TRF-08, TRF-09, TRF-10, TRF-11, TRF-12, TRF-13, TRF-14, TRF-15, VAL-01, VAL-02, VAL-03, VAL-04, VAL-05, VAL-06, VAL-07, VAL-08, VAL-09, OUT-01, OUT-02, OUT-03, OUT-04, OUT-05, OUT-06, OUT-07, OUT-08, OUT-09, OUT-10, OUT-11, OUT-12, LOG-01, LOG-02, LOG-03, LOG-04, LOG-05, LOG-06, LOG-07, PERF-01, PERF-03
**Success Criteria** (what must be TRUE):

  1. Given a synthetic XLSX, XLS, ODS, CSV, or TSV file, the pipeline reads it, applies all transformation rules, and produces a byte-exact output CSV (UTF-8 BOM, semicolon, CRLF, no quotes, trailing CRLF) without any Qt import being present anywhere in reader, normalizer, validator, pipeline, log_builder, or output modules
  2. Given any of the documented real-data quirks (mojibake, parenthetical annotations, trailing commas, Excel float mecanograficos, mixed prefix casing, leading zeros, U+FFFD characters), the transformation layer corrects them and records every change in the `_LOG_` file with the correct PT-PT tag and timestamp
  3. Given an input with any validation violation (invalid prefix, non-positive number, duplicate mecanografico, F/D/B cross-prefix collision, empty name after transformation), processing halts immediately, no output file is written, and an `_ERRORS_` file is created listing each offending row in PT-PT with row number, column name, value, and actionable message
  4. Given a 150,000-row XLSX file, the pipeline completes in under 10 seconds on a typical office laptop, reading in `read_only=True, data_only=True` mode throughout
  5. `pytest --cov` reports ≥90% line coverage over the core pipeline modules (reader, detector, normalizer, validator, output, log_builder, pipeline); no Qt import is present in any of these modules**Plans**: 5 plans

**Wave 1**

- [ ] 01-01-PLAN.md — Wave 0 scaffold: pyproject.toml, src/eleitorum package skeleton, test infrastructure, 15 synthetic fixture generators
- [ ] 01-02-PLAN.md — Wave 1: errors.py (PT-PT exception hierarchy) + readers.py (XLSX/XLS/ODS/CSV/TSV per-format readers with openpyxl streaming)
- [ ] 01-03-PLAN.md — Wave 1: detection.py (encoding + header + columns with D-01 hybrid fallback) + transform.py (all 15 TRF rules including batch case normalization)

**Wave 2** *(blocked on Wave 1 completion)*

- [ ] 01-04-PLAN.md — Wave 2: validate.py (aggregated VAL-01..09) + output.py (byte-exact CSV writer) + logging.py (PT-PT log builder)

**Wave 3** *(blocked on Wave 2 completion)*

- [ ] 01-05-PLAN.md — Wave 3: pipeline.py orchestrator + 5-user-journey integration tests + PERF-01 150k-row benchmark + ≥90% coverage gate

### Phase 2: UI Scaffold + Wizard Steps

**Goal**: The full PySide6 application runs end-to-end — QStackedWidget wizard with all six steps, light/dark theming, QThread worker with progress reporting, and all window chrome — built on top of the Phase 1 pipeline without modifying it
**Depends on**: Phase 1
**Requirements**: WIZ-01, WIZ-02, WIZ-03, WIZ-04, WIZ-05, WIZ-06, WIZ-07, WIZ-08, WIZ-09, WIZ-10, WIZ-11, APP-01, APP-02, APP-03, APP-04, APP-05, APP-06, APP-07, APP-08, APP-09, APP-10, APP-11, APP-12, APP-13, APP-14, APP-15, APP-16, APP-17, APP-18, APP-19, APP-20, BRAND-01, BRAND-02, TST-10, PERF-02
**Success Criteria** (what must be TRUE):

  1. A user can launch the application, see the first-run welcome screen once, dismiss it, and then proceed through all six wizard steps — output type selection, file upload (drag-and-drop and button), sheet picker (when applicable), column mapping, preview with summary panel, save-file dialog — without freezing the UI window at any point
  2. The window switches between light and dark themes instantly via the Ver menu toggle, the chosen theme persists across restarts, and both themes meet WCAG AA contrast for all visible text; the Inter font is used as the primary typeface throughout
  3. During processing, an indeterminate progress bar is shown while the file loads, transitioning to a determinate bar showing "A validar linha N de M…" once the row count is known; the window remains movable and a Cancel button is functional throughout
  4. All user-facing strings are in idiomatic PT-PT with no English text visible in the shipped UI; every interactive element is reachable by keyboard in visual tab order with visible focus indicators in both themes
  5. Window size, position, last directory, and theme are all restored correctly on relaunch; the About dialog displays the correct app name, version, UMinho disclaimer in PT-PT, license note, and repository link

**Plans**: TBD
**UI hint**: yes

### Phase 3: Integration, End-to-End Testing + Fixtures

**Goal**: The full stack — pipeline wired to UI worker — is verified by integration tests and synthetic fixtures covering every edge case in the spec, with byte-exact output assertions and pytest-qt smoke tests for each wizard step
**Depends on**: Phase 2
**Requirements**: TST-01, TST-02, TST-03, TST-04, TST-05, TST-06, TST-07, TST-08, TST-09
**Success Criteria** (what must be TRUE):

  1. For each of the five user journeys in spec Section 10 (happy-path CSV, multi-sheet Excel, mojibake Latin-1 file, duplicate rejection, manual column mapping), a dedicated integration test runs the full pipeline from synthetic input through to output bytes and asserts the exact expected output without any mocking of pipeline internals
  2. A byte-exact output test reads the written CSV in binary mode and confirms the first three bytes are `\xEF\xBB\xBF` (UTF-8 BOM), all row delimiters are `\r\n` (not `\n`), caderno rows end with `;` before `\r\n`, and no quoting characters appear anywhere in the file
  3. `tests/fixtures/generators.py` exports a fixture function for every fixture type listed in spec Section 14.3; all fixture data is fully synthetic with no real personal data; the fixture functions are importable and callable without a running QApplication
  4. Every wizard step has at least one pytest-qt smoke test confirming it initializes without error given a pre-populated SessionModel; tests run cleanly with `qt_api = pyside6` configured in `pyproject.toml`

**Plans**: TBD

### Phase 4: Build, CI, Packaging + Distribution Artifacts

**Goal**: A clean-machine Windows smoke test passes against the PyInstaller build, GitHub Actions CI runs all checks on push and publishes the release artifact on the v1.0.0 tag, and the repository contains every documentation file needed for public archiving
**Depends on**: Phase 3
**Requirements**: BRAND-03, BRAND-04, REPO-01, REPO-02, REPO-03, REPO-04, REPO-05, REPO-06, REPO-07, REPO-08, REPO-09, BLD-01, BLD-02, BLD-03, BLD-04, BLD-05, CI-01, CI-02, CI-03, CI-04, CI-05
**Success Criteria** (what must be TRUE):

  1. Running `python scripts/build.py` on a Windows machine with no prior build state produces `EleitorUM-1.0.0-win64.zip` (one-folder build); on a clean Windows VM with no Python installed, double-clicking the exe inside the ZIP opens the wizard window within 3 seconds; the window title and About dialog show the correct version
  2. The GitHub Actions CI workflow runs ruff lint, ruff format check, mypy, and pytest (Python 3.11 and 3.12 on windows-latest) on every push to main and all steps pass; `pip audit` runs and surfaces no unpatched high-severity CVEs
  3. On the `v1.0.0` tag, CI additionally builds the Windows executable, runs a smoke test (launch with `--version`, verify output and clean exit), computes a SHA-256 checksum, and attaches both the artifact and checksum to the GitHub Release
  4. The repository root contains: `SPECIFICATION.md`, `README.md` (bilingual headers, disclaimer, install instructions), `LICENSE` (MIT), `CHANGELOG.md` (v1.0.0 entry in Keep-a-Changelog format), `CONTRIBUTING.md` (external contributions not accepted), `RENAMING.md` (full rename checklist), `.gitignore`, `.gitattributes`, and `pyproject.toml` with pinned dependencies and tool configuration

**Plans**: TBD

## Progress

**Execution Order:**
Phases execute in numeric order: 1 → 2 → 3 → 4

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Core Pipeline | 0/5 | Planned | - |
| 2. UI Scaffold + Wizard Steps | 0/TBD | Not started | - |
| 3. Integration, End-to-End Testing + Fixtures | 0/TBD | Not started | - |
| 4. Build, CI, Packaging + Distribution Artifacts | 0/TBD | Not started | - |
