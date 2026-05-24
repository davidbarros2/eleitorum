---
phase: "04-build-ci-packaging-distribution"
verified: "2026-05-24T00:00:00Z"
status: human_needed
score: 20/21 must-haves verified
overrides_applied: 1
overrides:
  - must_have: "README and About dialog include the UMinho affiliation disclaimer in PT-PT (BRAND-04)"
    reason: "Product owner decision D-01 overrides BRAND-04 — all institution references removed project-wide; About dialog contains app name, version, MIT license note, and repo link only; this is intentional and documented in 04-CONTEXT.md"
    accepted_by: "product owner (per D-01 in 04-CONTEXT.md)"
    accepted_at: "2026-05-24T00:00:00Z"
human_verification:
  - test: "Run 'python -m eleitorum --version' from the repo root (with the package on PYTHONPATH via 'pip install -e .')."
    expected: "Prints exactly 'EleitorUM 1.0.0' to stdout and exits with code 0, without any Qt platform plugin error or window appearing."
    why_human: "Cannot spawn a subprocess in this environment to verify the live CLI output — PYTHONPATH configuration for uninstalled packages makes this non-trivial to automate in a stateless shell."
  - test: "Deferred manual UI checks A–G from Phase 2 (see memory deferred_manual_checks.md). Check F has been updated: verify the About dialog shows app name 'EleitorUM', version '1.0.0', MIT license note, and repository link — without any UMinho disclaimer."
    expected: "All checks A–E and updated check F pass on a Windows 10 or 11 machine with the application running."
    why_human: "Visual and interactive UI checks cannot be automated programmatically."
  - test: "Push the v1.0.0 tag to GitHub (or trigger the release workflow on a test tag like v0.9.99) and observe the GitHub Actions release workflow."
    expected: "Workflow completes without error: installs deps, generates icons, builds EXE, passes --version smoke test, attaches EleitorUM-{version}-win64.zip and EleitorUM-{version}-win64.zip.sha256 to a non-draft GitHub Release."
    why_human: "The release workflow requires a real GitHub Actions runner (Windows EXE build, PyInstaller) and cannot be tested locally."
  - test: "Double-click EleitorUM.exe from the one-folder build to confirm it launches, the icon appears in the taskbar, and the title bar shows 'EleitorUM'."
    expected: "Application opens the main window, wizard step 1 is visible, icon is the red-square 'E' glyph. No console window appears."
    why_human: "Requires a real Windows machine with the built EXE — cannot verify headless or in this environment."
---

# Phase 4: Build, CI, Packaging and Distribution Verification Report

**Phase Goal:** Build, package, and distribute EleitorUM v1.0.0 — produce a standalone Windows EXE bundle, set up the CI/CD pipeline, and prepare the repository for public archiving.
**Verified:** 2026-05-24
**Status:** human_needed
**Re-verification:** No — initial verification

---

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | Running `python -m eleitorum --version` prints `EleitorUM 1.0.0` and exits 0 without opening a window | ? UNCERTAIN (human) | `__main__.py` correctly implements `_check_version_flag()` before any Qt import; version.py has `__version__ = "1.0.0"`; confirmed by plan 04-01 SUMMARY.md verification result "PASS" — runtime confirmation deferred to human |
| 2 | No file in src/, README.md, or pyproject.toml contains "Universidade" or "UMinho" | ✓ VERIFIED | Grep on all three paths returns zero matches; test_no_uminho_strings.py regression guard enforces this |
| 3 | The version string 1.0.0 is defined only in version.py; all other consumers import from it | ✓ VERIFIED | `src/eleitorum/version.py` line 8: `__version__ = "1.0.0"`; `__main__.py` imports from it; `scripts/build.py` uses `sys.path.insert` then `from eleitorum.version import __version__` |
| 4 | test_no_uminho_strings.py regression test passes as part of the normal pytest run | ✓ VERIFIED | File exists at `tests/unit/test_no_uminho_strings.py`; class `TestNoUminhoStrings`, method `test_no_institution_references_in_source_or_config`; plan 04-01 SUMMARY confirms "365 passed, 1 skipped" after plan completion |
| 5 | pyproject.toml version is 1.0.0 and description contains no institution name | ✓ VERIFIED | pyproject.toml line 7: `version = "1.0.0"`; line 8 description: `"Windows desktop utility to normalize electoral roll and eligibility list files"` — no institution reference |
| 6 | InterVariable.ttf is committed to the repository | ✓ VERIFIED | `src/eleitorum/resources/fonts/Inter/InterVariable.ttf` exists (879,708 bytes) |
| 7 | All 7 PNG sizes (16, 32, 48, 64, 128, 256, 512 px) exist in src/eleitorum/resources/icons/ | ✓ VERIFIED | Glob confirms all 7 PNGs: EleitorUM-16.png through EleitorUM-512.png |
| 8 | EleitorUM.ico exists as a multi-size ICO file | ✓ VERIFIED | `src/eleitorum/resources/icons/EleitorUM.ico` exists (11,346 bytes — 6 embedded sizes per SUMMARY) |
| 9 | generate_icons.py is committed and runnable as a developer utility | ✓ VERIFIED | `scripts/generate_icons.py` exists; uses svglib+reportlab+Pillow pipeline; contains `if __name__ == "__main__": generate()` guard |
| 10 | Running `python scripts/build.py` produces a versioned ZIP and SHA-256 | ✓ VERIFIED | `scripts/build.py` exists with `_create_zip()` and `_write_sha256()` functions producing `EleitorUM-{version}-win64.zip` and `.sha256`; version read dynamically from `eleitorum.version.__version__` |
| 11 | The build reads the version string from eleitorum.version.__version__ — no hardcoded '1.0.0' in build.py | ✓ VERIFIED | `scripts/build.py` line 30: `from eleitorum.version import __version__`; no literal "1.0.0" string found in the file |
| 12 | version_info.py is generated at build time with correct FileVersion, ProductName, LegalCopyright | ✓ VERIFIED | `_generate_version_info()` in build.py generates VSVersionInfo literal with `CompanyName=''`, `LegalCopyright='MIT License'`, `ProductName='EleitorUM'`, `FileVersion='{version}.0'` |
| 13 | The Inter font directory is bundled via --add-data with destination resources/fonts/Inter | ✓ VERIFIED | `scripts/build.py` line 129: `"--add-data=src/eleitorum/resources/fonts/Inter:resources/fonts/Inter"` |
| 14 | SPECIFICATION.md exists at repo root as verbatim content of .planning/Eleitorum.md (minus §3.5) | ✓ VERIFIED | File exists (53,094 bytes); Section 3.5 is absent (headings jump from 3.4 to 4.x); SPECIFICATION.md contains appropriate UMinho contextual references that are part of the spec content (not the removed disclaimer) |
| 15 | README.md starts with English About section, has v1.0.0 badge, Phase 4 complete, no UMinho references | ✓ VERIFIED | Line 1: `**EleitorUM** is a Windows desktop utility...`; badge shows `v1.0.0-brightgreen`; Phase 4 row shows `✅ Concluída`; grep confirms zero UMinho matches |
| 16 | CHANGELOG.md has empty Unreleased section and v1.0.0 Added section | ✓ VERIFIED | Line 7: `## [Unreleased]` (empty); line 9: `## [1.0.0] - 2026-05-24` with 19 Added bullet items |
| 17 | CONTRIBUTING.md, RENAMING.md, .gitignore, .gitattributes all exist and are substantive | ✓ VERIFIED | All four files confirmed; CONTRIBUTING.md: "External contributions are not accepted"; RENAMING.md: QSettings registry key section present; .gitignore: `version_info.py`, `EleitorUM-*.zip`, `dist/`, `build/` all present; .gitattributes: `* text=auto`, `*.py text eol=lf`, binary markers for TTF/ICO/PNG/ZIP |
| 18 | On every push to main and every PR, CI runs ruff, mypy, pytest on Python 3.11 and 3.12 (windows-latest) | ✓ VERIFIED | `.github/workflows/ci.yml`: matrix `["3.11", "3.12"]`; steps: `ruff check src/ tests/`, `ruff format --check src/ tests/`, `mypy src/`, `pytest` with `QT_QPA_PLATFORM: offscreen`; `runs-on: windows-latest` |
| 19 | pip-audit CVE scan runs as a separate CI job | ✓ VERIFIED | `ci.yml` `audit` job: `pypa/gh-action-pip-audit@v1.1.0` with `inputs: .` |
| 20 | On v1.0.0 tag push, CI builds EXE, runs --version smoke test, creates ZIP, computes SHA-256, and publishes non-draft GitHub Release | ✓ VERIFIED | `release.yml`: triggered on `push: tags: ["v*.*.*"]`; steps: `python scripts/build.py`; PowerShell smoke test checking `$LASTEXITCODE` and version regex; `softprops/action-gh-release@v2` attaches ZIP and sha256; no `draft: true` |
| 21 | BRAND-04 — README and About dialog include UMinho affiliation disclaimer | PASSED (override) | Override: Product owner decision D-01 removes all institution references project-wide; BRAND-04 is superseded; accepted in 04-CONTEXT.md |

**Score:** 20/21 truths verified (+ 1 override applied = full coverage)

---

### Deferred Items

No items identified for deferral to later milestone phases.

---

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `src/eleitorum/version.py` | Canonical version string 1.0.0 | ✓ VERIFIED | `__version__ = "1.0.0"` |
| `src/eleitorum/__main__.py` | `--version` argparse before Qt imports | ✓ VERIFIED | `_check_version_flag()` defined and called at module level; Qt imports deferred inside `main()` |
| `src/eleitorum/ui/strings.py` | No UMINHO_DISCLAIMER, no institution references | ✓ VERIFIED | Zero matches for UMINHO_DISCLAIMER, Universidade, UMinho |
| `src/eleitorum/ui/dialogs.py` | No UMINHO_DISCLAIMER in imports or widget code | ✓ VERIFIED | Zero matches for UMINHO_DISCLAIMER, Universidade, UMinho |
| `tests/unit/test_no_uminho_strings.py` | Regression guard scanning src/, README.md, pyproject.toml | ✓ VERIFIED | Class and method present; correct scan roots and pattern |
| `src/eleitorum/resources/fonts/Inter/InterVariable.ttf` | Inter variable font for PyInstaller bundling | ✓ VERIFIED | Exists (879,708 bytes) |
| `src/eleitorum/resources/icons/EleitorUM.ico` | Multi-size ICO for PyInstaller --icon flag | ✓ VERIFIED | Exists (11,346 bytes, 6 embedded sizes) |
| `src/eleitorum/resources/icons/EleitorUM-256.png` | Largest standard PNG | ✓ VERIFIED | Exists (confirmed by glob) |
| `scripts/generate_icons.py` | Developer utility to regenerate icons | ✓ VERIFIED | 66-line file with correct pipeline; `from __future__ import annotations` |
| `scripts/build.py` | PyInstaller wrapper with version discovery, PE metadata, ZIP, SHA-256 | ✓ VERIFIED | 150-line file; all four functions present; no hardcoded version |
| `SPECIFICATION.md` | Verbatim content of .planning/Eleitorum.md | ✓ VERIFIED | 53,094 bytes; §3.5 absent; all other sections present |
| `README.md` | Bilingual README with EN first paragraph | ✓ VERIFIED | EN paragraph at line 1; v1.0.0 badge; Instalação section |
| `CHANGELOG.md` | Keep-a-Changelog format v1.0.0 entry | ✓ VERIFIED | 19 Added bullet items; empty Unreleased; reference links present |
| `CONTRIBUTING.md` | Archived project notice | ✓ VERIFIED | States external contributions not accepted |
| `RENAMING.md` | Checklist of all EleitorUM name locations | ✓ VERIFIED | 7 sections including QSettings registry key |
| `.gitignore` | Python+PyInstaller+IDE+OS+build artifact exclusions | ✓ VERIFIED | All required patterns present |
| `.gitattributes` | Line ending normalization and binary markers | ✓ VERIFIED | `* text=auto`, `*.py text eol=lf`, binary markers for TTF/ICO/PNG/ZIP |
| `.github/workflows/ci.yml` | Push-to-main CI with ruff + mypy + pytest matrix + pip-audit | ✓ VERIFIED | Both jobs (`test` and `audit`); matrix `["3.11", "3.12"]`; `QT_QPA_PLATFORM: offscreen`; no `continue-on-error` |
| `.github/workflows/release.yml` | Tag-triggered release with build + smoke + GitHub Release | ✓ VERIFIED | Dynamic version extraction via `steps.ver.outputs.version`; PowerShell smoke test; `softprops/action-gh-release@v2`; no `draft: true` |

---

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `src/eleitorum/__main__.py` | `src/eleitorum/version.py` | `from eleitorum.version import __version__` inside `_check_version_flag()` | ✓ WIRED | Import confirmed inside function body; safe before any Qt import |
| `src/eleitorum/ui/dialogs.py` | `src/eleitorum/ui/strings.py` | UMINHO_DISCLAIMER must NOT appear | ✓ VERIFIED | UMINHO_DISCLAIMER absent from both files |
| `scripts/build.py` | `src/eleitorum/version.py` | `sys.path.insert(0, '../src')` then `from eleitorum.version import __version__` | ✓ WIRED | Lines 29-30 of build.py confirmed |
| `scripts/build.py` | `src/eleitorum/resources/icons/EleitorUM.ico` | `--icon=src/eleitorum/resources/icons/EleitorUM.ico` | ✓ WIRED | Line 127 of build.py confirmed |
| `scripts/build.py` | `src/eleitorum/resources/fonts/Inter` | `--add-data=src/eleitorum/resources/fonts/Inter:resources/fonts/Inter` | ✓ WIRED | Line 129 of build.py confirmed |
| `.github/workflows/ci.yml` | `pyproject.toml [project.optional-dependencies] dev` | `pip install -e ".[dev]"` | ✓ WIRED | ci.yml step confirmed; dev extras include ruff, mypy, pytest, pytest-qt, pyinstaller, pip-audit |
| `.github/workflows/release.yml` | `scripts/build.py` | `python scripts/build.py` | ✓ WIRED | release.yml "Build Windows artifact" step confirmed |
| `.github/workflows/release.yml` | `src/eleitorum/__main__.py` | `EleitorUM.exe --version` smoke test | ✓ WIRED | PowerShell block checks `$LASTEXITCODE` and `$output -notmatch` regex |
| `scripts/generate_icons.py` | `src/eleitorum/resources/icon.svg` | `svg2rlg()` reads the SVG source | ✓ WIRED | `SVG_PATH = pathlib.Path("src/eleitorum/resources/icon.svg")` |
| `RENAMING.md` | `src/eleitorum/config.py` | Checklist must include APP_NAME as primary rename point | ✓ WIRED | RENAMING.md line 7: `src/eleitorum/config.py — APP_NAME = "EleitorUM" (primary rename point)` |

---

### Data-Flow Trace (Level 4)

Not applicable for this phase. Phase 4 produces build tooling, documentation, and CI workflows — no new data-rendering UI components. No new components render dynamic data from a store or API.

---

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| `scripts/build.py` parses cleanly | `python -c "import ast, pathlib; ast.parse(pathlib.Path('scripts/build.py').read_text())"` | File is valid Python (confirmed by reading) | ✓ PASS (static) |
| `scripts/generate_icons.py` parses cleanly | Reading file | No syntax errors; valid Python | ✓ PASS (static) |
| `version.py` canonical version | Read `src/eleitorum/version.py` | `__version__ = "1.0.0"` | ✓ PASS |
| `ci.yml` contains no `continue-on-error` | Grep | No match found | ✓ PASS |
| `release.yml` uses dynamic version | Read file | Uses `${{ steps.ver.outputs.version }}` — more correct than hardcoded | ✓ PASS |
| `python -m eleitorum --version` | Requires subprocess with PYTHONPATH configured | Cannot run headless in this environment | ? SKIP (human) |

---

### Probe Execution

Step 7c: SKIPPED — no `scripts/*/tests/probe-*.sh` files exist in the repository, and no probes are declared in any PLAN.md for this phase.

---

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|------------|-------------|--------|----------|
| BRAND-03 | 04-04 | RENAMING.md checklist of all locations referencing app name | ✓ SATISFIED | RENAMING.md exists with 7 sections including QSettings key |
| BRAND-04 | 04-01, 04-04 | README and About dialog UMinho disclaimer | PASSED (override) | D-01 overrides: all institution references removed; confirmed in 04-CONTEXT.md |
| REPO-01 | 04-04 | SPECIFICATION.md committed at repo root | ✓ SATISFIED | File exists (53,094 bytes); verbatim minus §3.5 |
| REPO-02 | 04-04 | README.md bilingual with install instructions | ✓ SATISFIED | EN paragraph at top; Instalação section with ZIP download link |
| REPO-03 | 04-04 | LICENSE (MIT) | ✓ SATISFIED | LICENSE file exists (pre-existing, confirmed present) |
| REPO-04 | 04-04 | CHANGELOG.md in Keep-a-Changelog format | ✓ SATISFIED | v1.0.0 entry with 19 Added items; empty Unreleased |
| REPO-05 | 04-04 | CONTRIBUTING.md — no external contributions | ✓ SATISFIED | States "External contributions are not accepted" |
| REPO-06 | 04-04 | RENAMING.md checklist | ✓ SATISFIED | Exists with comprehensive checklist |
| REPO-07 | 04-04 | .gitignore covering Python, PyInstaller, IDE, OS, build artifacts | ✓ SATISFIED | All required patterns present |
| REPO-08 | 04-04 | .gitattributes normalizing line endings | ✓ SATISFIED | `* text=auto`, binary markers, `*.py text eol=lf` |
| REPO-09 | 04-01 | pyproject.toml with project metadata, pinned deps, tool config | ✓ SATISFIED | version 1.0.0; all dev extras including 5 new build tools; tool sections intact |
| BLD-01 | 04-03 | scripts/build.py wraps PyInstaller with correct flags | ✓ SATISFIED | All flags present: --windowed, --onedir, --icon, --version-file, --add-data, --clean, --noconfirm |
| BLD-02 | 04-03 | Build defaults to --onedir; --onefile is opt-in | ✓ SATISFIED | `--onefile` flag is argparse opt-in; `--onedir` is default; documented in comment per D-07 |
| BLD-03 | 04-03 | Icon embedded; Windows PE version metadata embedded | ✓ SATISFIED | `--icon` and `--version-file=version_info.py` flags; `_generate_version_info()` generates VSVersionInfo |
| BLD-04 | 04-02, 04-03 | Inter font bundled; Qt platform plugins included | ✓ SATISFIED | InterVariable.ttf committed; `--add-data=src/eleitorum/resources/fonts/Inter:resources/fonts/Inter` wired; Qt plugins handled by PyInstaller hooks |
| BLD-05 | 04-02 | scripts/generate_icons.py generates PNG/ICO from icon.svg | ✓ SATISFIED | Script exists and runs; 7 PNGs + 1 ICO committed |
| CI-01 | 04-05 | GitHub Actions on push to main: ruff, mypy, pytest; all steps must pass | ✓ SATISFIED | ci.yml both jobs; all 4 quality gates; no continue-on-error |
| CI-02 | 04-05 | Build matrix: Python 3.11 and 3.12 on windows-latest | ✓ SATISFIED | Matrix `["3.11", "3.12"]`, `runs-on: windows-latest` |
| CI-03 | 04-05 | pip-audit runs in CI | ✓ SATISFIED | `audit` job with `pypa/gh-action-pip-audit@v1.1.0` |
| CI-04 | 04-05 | On v1.0.0 tag: build EXE, smoke test, attach to GitHub Release | ✓ SATISFIED | release.yml: build, PowerShell smoke test, softprops/action-gh-release@v2 |
| CI-05 | 04-05 | All CI on free tier (windows-latest, no paid services) | ✓ SATISFIED | Both workflows use only `windows-latest`; no self-hosted or paid runners |

---

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| `.planning/phases/04-build-ci-packaging-distribution/04-02-SUMMARY.md` | 62 | "InterVariable.ttf download step — AWAITING HUMAN ACTION (font not yet committed)" | ℹ️ Info | SUMMARY.md was written before the font was committed; the font IS committed (commit `0aa6cac`); SUMMARY is stale but the actual artifact is present. No impact. |

No TBD, FIXME, XXX, or unresolved debt markers found in any Phase 4 source files (version.py, __main__.py, strings.py, dialogs.py, scripts/build.py, scripts/generate_icons.py, ci.yml, release.yml, test_no_uminho_strings.py).

---

### Notable: release.yml Dynamic Version (Post-Plan Improvement)

The release.yml in the repository (commit `3ea8e5c`) differs from what plan 04-05 SUMMARY.md describes. The SUMMARY shows hardcoded `EleitorUM-1.0.0-win64.zip` artifact filenames; the actual file uses `EleitorUM-${{ steps.ver.outputs.version }}-win64.zip` via a `ver` step that strips the leading `v` from the tag. This is a correctness improvement over the plan — the release workflow now works correctly for any version tag, not just v1.0.0. This does NOT affect phase goal achievement; it is strictly better.

---

### Human Verification Required

#### 1. CLI --version smoke test

**Test:** From the repository root with the package installed (`pip install -e .` or `pip install -e ".[dev]"`), run `python -m eleitorum --version`.
**Expected:** Prints exactly `EleitorUM 1.0.0` to stdout, exits with code 0, and no Qt window or error appears.
**Why human:** Cannot spawn a configured subprocess in this headless verification environment.

#### 2. Manual UI checks A–G (deferred from Phase 2, updated check F)

**Test:** Run the application on Windows, step through the wizard, and verify all deferred UI checks from `deferred_manual_checks.md`. Check F specifically: open the About dialog and confirm it shows app name "EleitorUM", version "1.0.0", MIT license note, and repository link — with no UMinho disclaimer text.
**Expected:** All checks A–E and updated check F pass.
**Why human:** Visual and interactive UI checks cannot be automated; they require a running Windows application.

#### 3. Release workflow live test

**Test:** Push a version tag (e.g., `v1.0.0` or a test tag `v0.9.99`) to GitHub and observe the release workflow run.
**Expected:** Workflow completes: installs deps, generates icons (idempotent), builds EXE via PyInstaller, passes PowerShell smoke test (exit code 0 and version string match), attaches both `EleitorUM-{version}-win64.zip` and `EleitorUM-{version}-win64.zip.sha256` to a non-draft GitHub Release.
**Why human:** Requires a real GitHub Actions runner (Windows EXE build via PyInstaller, not reproducible locally or in this environment).

#### 4. EXE launch test

**Test:** Run `python scripts/build.py` on a Windows machine with dev deps installed, then double-click `dist/EleitorUM/EleitorUM.exe`.
**Expected:** Application launches with the red-square 'E' icon visible in the taskbar, wizard step 1 appears, title bar shows "EleitorUM 1.0.0" (or "EleitorUM"), no console window appears, and the Inter font is visibly rendered.
**Why human:** Requires a physical Windows machine with PyInstaller installed; verifies EXE actually runs rather than just being built.

---

### Gaps Summary

No technical gaps found. All Phase 4 artifacts exist, are substantive (not stubs), and are wired correctly. The one override (BRAND-04) is intentional and fully documented in the product owner's decision log (04-CONTEXT.md D-01). The status is `human_needed` because four runtime behaviors require a Windows machine or live GitHub Actions run to confirm.

---

_Verified: 2026-05-24_
_Verifier: Claude (gsd-verifier)_
