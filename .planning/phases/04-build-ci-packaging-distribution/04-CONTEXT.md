# Phase 4: Build, CI, Packaging + Distribution Artifacts - Context

**Gathered:** 2026-05-24
**Status:** Ready for planning

<domain>
## Phase Boundary

Convert the working development project into a shippable, publicly archived artifact: a versioned Windows ZIP (one-folder PyInstaller build), a GitHub Actions CI/CD pipeline, and a complete set of repository documentation files. No new application features are added in this phase.

**In scope:** BRAND-03, BRAND-04 (overridden — see D-01), REPO-01–09, BLD-01–05, CI-01–05

**Out of scope:** Any modification to the core pipeline or UI code; integration/unit tests beyond the CI smoke test; new wizard steps or UI features; multi-platform builds

</domain>

<decisions>
## Implementation Decisions

### No institutional attribution anywhere
- **D-01:** Remove ALL references to "Universidade do Minho" and "UMinho" project-wide — source files, README, pyproject.toml description, About dialog, and any other location. Run a full grep across `src/`, `README.md`, and `pyproject.toml` to catch every instance. This overrides BRAND-04 (which required a UMinho disclaimer in README and About dialog). The About dialog drops the disclaimer entirely — it contains only: app name, version, MIT license note, and repo link.
  - Rationale: product owner decision; the tool is not to be associated with any specific institution.
  - Action: `grep -rn "Universidade\|UMinho" src/ README.md pyproject.toml tests/ .planning/phases/04-build-ci-packaging-distribution/` — remove every match.

### Inter font files
- **D-02:** Commit `InterVariable.ttf` to `src/eleitorum/resources/fonts/Inter/InterVariable.ttf`. Download the file from the rsms/inter GitHub releases (canonical source). The `OFL.txt` license file is already present. The single variable font file covers all weights via `font-weight` QSS values.
  - Rationale: OFL license permits redistribution; ~500 KB; zero build complexity; Qt 6.x has full variable font support via QFontDatabase.

### README.md structure
- **D-03:** The existing PT-PT README stays as the primary body. Add a short English paragraph at the very top — before the PT body — as a single-paragraph "About" section for GitHub discoverability. English content: one or two sentences describing what the tool does (no institution named, no install snippet). The PT body follows below. Remove any remaining UMinho references per D-01.
  - Rationale: REPO-02 calls for bilingual headers; PT-primary is correct for the target audience; one EN paragraph is sufficient without duplicating the full document.

### SPECIFICATION.md sourcing
- **D-04 (delegated):** Copy `.planning/Eleitorum.md` verbatim to `SPECIFICATION.md` at the repository root. No modifications. Section 0's "audience: AI development agents and human contributors" preamble is fine to leave in a public archived repository — it is accurate and honest.
  - Rationale: Eleitorum.md is already the complete canonical specification; zero duplication effort; the file content requires no changes.

### CHANGELOG.md
- **D-05:** Create `CHANGELOG.md` in Keep-a-Changelog format. The v1.0.0 entry has a comprehensive `Added` section listing all major capabilities: input formats, encoding detection, transformation rules, validation rules, output format, wizard UI (all steps), theme system, build artifact, CI/CD pipeline. No Changed/Fixed/Removed sections for an initial release. Include the "Unreleased" section as empty (standard Keep-a-Changelog header).

### GitHub Release publication
- **D-06:** On the `v1.0.0` tag push, CI publishes the GitHub Release automatically (not as a draft). The release attaches two files: `EleitorUM-1.0.0-win64.zip` and `EleitorUM-1.0.0-win64.zip.sha256` (SHA-256 checksum file, one line).
  - Rationale: solo project, single-version lifecycle — no need for a manual review gate before publishing.

### Build script behaviour
- **D-07:** `scripts/build.py` defaults to `--onedir` (already decided). Add a comment in `build.py` documenting how to test the `--onefile` build manually (pass `--onefile` flag). No automated cold-start benchmark in the build script or CI — GitHub Actions runners are too variable for a meaningful timing comparison.

### Claude's Discretion
- **Version bump:** Bump `src/eleitorum/version.py` and `pyproject.toml` from `0.1.0` to `1.0.0` as part of the Phase 4 plan work — not a separate final commit. The version must be `1.0.0` before the PyInstaller build runs.
- **`--version` CLI arg:** Add `--version` support to `src/eleitorum/__main__.py` via `argparse`. It must print `EleitorUM 1.0.0` and exit cleanly (exit code 0). This is required for the CI-04 smoke test.
- **CONTRIBUTING.md:** One-page document stating clearly that this is an archived project, external contributions are not accepted, and no pull requests will be reviewed.
- **RENAMING.md:** Checklist of every location that references the app name `EleitorUM`, including: `src/eleitorum/config.py`, `pyproject.toml`, `README.md`, `SPECIFICATION.md`, `CHANGELOG.md`, `CONTRIBUTING.md`, `scripts/build.py`, `.github/workflows/*.yml`, the About dialog, the window title, and the distribution ZIP filename.
- **`.gitignore`:** Standard Python + PyInstaller (`dist/`, `build/`, `*.spec.bak`) + IDE (`.vscode/`, `.idea/`) + OS (`.DS_Store`, `Thumbs.db`) + build artifacts (`EleitorUM-*.zip`).
- **`.gitattributes`:** `* text=auto` baseline; Python source `*.py text eol=lf`; binary files (`*.ttf`, `*.svg`, `*.ico`, `*.png`, `*.zip`) as `binary`.
- **`scripts/generate_icons.py`:** Generate PNG sizes 16, 32, 48, 64, 128, 256, 512 px and one `.ico` (multi-size) from `src/eleitorum/resources/icon.svg`. Use `cairosvg` or `rsvg-convert` for the conversion; add it as a `[dev]` optional dependency if needed.
- **SHA-256 format:** One-line text file: `<hex_digest>  EleitorUM-1.0.0-win64.zip` (BSD-style, two spaces).
- **Windows PE metadata:** `scripts/build.py` generates a PyInstaller version file (`version_info.py`) with `FileVersion`, `ProductName = "EleitorUM"`, `FileDescription`, `LegalCopyright`. Pass via `--version-file` to PyInstaller.

### Pre-release human-action blockers (must resolve before v1.0.0 tag push)
The following open questions are NOT blockers for writing Phase 4 plans, but ARE blockers for tagging v1.0.0. Surface these to the product owner before the release tag is pushed:

1. **BOM validation:** Output uses UTF-8 with BOM. Product owner must test the generated CSV against the live electoral platform. One-line change in `src/eleitorum/core/output.py` if BOM must be dropped.
2. **F/D/B cross-prefix uniqueness rule:** Product owner must confirm this rule is correct based on how mecanográfico numbers are actually issued.
3. **Elegíveis sort key:** Product owner must confirm: full designation string sorted alphabetically, or surname-first?
4. **Mecanográfico prefix list exhaustiveness:** Confirm that A, PG, ID, F, D, B, Q, EX covers all valid prefixes.
5. **Manual UI checks A–G:** Deferred from Phase 2 checkpoint (see memory `deferred_manual_checks.md`). Must be done before tagging v1.0.0. Note: Check F ("About dialog shows UMinho disclaimer") is now obsolete — the disclaimer was removed per D-01. Check F should verify: app name, version 1.0.0, MIT license note, repo link.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Phase Scope and Requirements
- `.planning/ROADMAP.md` §"Phase 4: Build, CI, Packaging + Distribution Artifacts" — success criteria and full requirement list (BRAND-03, BRAND-04, REPO-01–09, BLD-01–05, CI-01–05)
- `.planning/REQUIREMENTS.md` — authoritative requirement definitions for all Phase 4 IDs

### Specification (source of truth)
- `.planning/Eleitorum.md` — canonical project spec; verbatim source for `SPECIFICATION.md` (D-04). **Do NOT copy UMinho disclaimer from Section 3.5 — it is superseded by D-01.**

### Version and Identity
- `src/eleitorum/version.py` — current version `0.1.0`; bump to `1.0.0` as Phase 4 plan work
- `src/eleitorum/config.py` — `APP_NAME = "EleitorUM"`; RENAMING.md checklist must include this file

### Files to Modify (UMinho removal — D-01)
- `pyproject.toml` — `description` field mentions UMinho; remove it
- `src/eleitorum/__main__.py` — extend with `--version` argparse arg
- `src/eleitorum/ui/dialogs.py` — About dialog; remove disclaimer text, keep: name, version, MIT, repo link
- `src/eleitorum/ui/strings.py` — grep for institution references; remove any found

### Existing Assets (reuse in build)
- `src/eleitorum/resources/icon.svg` — source for `scripts/generate_icons.py` (BLD-05)
- `src/eleitorum/resources/fonts/Inter/` — Inter font directory; `InterVariable.ttf` to be added here (D-02)
- `README.md` — existing PT-PT body; add English paragraph at top per D-03; remove any UMinho mentions per D-01

### Prior phase decisions affecting Phase 4
- `.planning/phases/02-ui-scaffold-wizard-steps/02-CONTEXT.md` §D-06 — `QSettings` organization: `EleitorUM/EleitorUM` (company/app key) — RENAMING.md must document this
- `.planning/phases/02-ui-scaffold-wizard-steps/02-CONTEXT.md` §"Claude's Discretion" — Inter font loading path (`sys._MEIPASS` vs package path) — PyInstaller spec must bundle fonts so `sys._MEIPASS` path works

### Tech Stack
- `CLAUDE.md` — technology decisions including PyInstaller 6.20.0, one-folder primary build, pip audit, PySide6 LGPL

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `src/eleitorum/version.py` — `__version__ = "0.1.0"`: bump to `"1.0.0"` here; `__main__.py --version` and About dialog read from this
- `src/eleitorum/config.py` — `APP_NAME = "EleitorUM"`: window title and log file naming; RENAMING.md lists this as the primary rename point
- `src/eleitorum/resources/icon.svg` — existing branded SVG (white "E" on red rounded-corner square); input for `generate_icons.py`
- `src/eleitorum/resources/fonts/Inter/OFL.txt` — OFL license already committed; `InterVariable.ttf` goes alongside it

### Established Patterns
- Version string single source of truth: `version.py.__version__` — do not hardcode the version string anywhere else (build script, CI workflow, Windows PE metadata should all read from this or from `python -c "from eleitorum.version import __version__; print(__version__)"`)
- Font loading: Phase 2 established `QFontDatabase.addApplicationFont()` with `sys._MEIPASS` fallback to package path — PyInstaller spec must add the Inter font directory to `datas`
- Test suite: 383 tests, all green — do not break them; CI workflow runs `pytest` and expects all to pass

### Integration Points
- `src/eleitorum/__main__.py` — entry point; needs `argparse` block before `main()` call; `--version` must exit before creating `QApplication` (no GUI instantiated for `--version`)
- `.github/workflows/` — directory does not yet exist; CI-01, CI-04 workflows go here
- `scripts/` — directory does not yet exist; `build.py`, `generate_icons.py` go here
- `pyproject.toml` — add `pip-audit` (or note it's run via `pipx run pip-audit` in CI); `PyInstaller==6.20.0` and `cairosvg` (if used) added to `[dev]` extras

</code_context>

<specifics>
## Specific Ideas

- The `--version` smoke test in CI-04 must work on a clean Windows machine with no Python installed. The PyInstaller bundle's executable must handle `EleitorUM.exe --version` and exit with code 0 printing `EleitorUM 1.0.0`. The argparse block in `__main__.py` runs before any Qt import.

- For the GitHub Release workflow, use `softprops/action-gh-release` or the native `gh release create` CLI — both produce the desired artifact attachment on a tag push. `GITHUB_TOKEN` is automatically available in GitHub Actions.

- The SHA-256 file (`EleitorUM-1.0.0-win64.zip.sha256`) can be generated in CI with `certutil -hashfile EleitorUM-1.0.0-win64.zip SHA256 > EleitorUM-1.0.0-win64.zip.sha256` (Windows) or a cross-platform Python one-liner.

- Manual UI Check F from `deferred_manual_checks.md` is now updated: it should verify About dialog shows "EleitorUM 1.0.0" with MIT license and repo link — no disclaimer text.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 4-Build, CI, Packaging + Distribution Artifacts*
*Context gathered: 2026-05-24*
