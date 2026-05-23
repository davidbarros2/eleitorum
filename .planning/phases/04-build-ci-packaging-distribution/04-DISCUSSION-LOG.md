# Phase 4: Build, CI, Packaging + Distribution Artifacts - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-05-24
**Phase:** 04-build-ci-packaging-distribution
**Areas discussed:** Inter font files, README bilingual format, No UMinho attribution, SPECIFICATION.md sourcing, CHANGELOG v1.0.0 entry, GitHub Release publication, Cold-start benchmark, Inter font variant

---

## Inter font files

| Option | Description | Selected |
|--------|-------------|----------|
| Commit to git | OFL license permits it, ~1–5 MB, zero build complexity. Download once, commit, done. | ✓ |
| Build-script download | Build script fetches from Google Fonts API at build time. Keeps git lean; requires internet on build machine. | |
| Manual prereq, documented | README and build docs say "download Inter and drop in fonts/Inter/ before building". Fragile. | |

**User's choice:** Commit to git  
**Notes:** Simplest approach. OFL license explicitly allows redistribution.

---

## Inter font variant

| Option | Description | Selected |
|--------|-------------|----------|
| InterVariable.ttf only | ~500KB. One file covers all weights via font-weight QSS values. Qt 6.x has full variable font support. | ✓ |
| Individual weight TTFs (Regular + Medium + SemiBold) | ~600KB total for 3 files. More conservative, guaranteed to work on any Qt 6.x version. | |
| You decide | Claude chooses the most appropriate Inter font variant. | |

**User's choice:** InterVariable.ttf only  
**Notes:** Modern approach; single file keeps the repo lean.

---

## README bilingual format

| Option | Description | Selected |
|--------|-------------|----------|
| PT primary, one EN section at top | Add a short English "About" paragraph at the top, then full PT body below. Existing PT content stays. | ✓ |
| Parallel bilingual — every section in PT then EN | Each section appears twice (PT first, EN below). Doubles document length. | |
| PT only — what's there now is fine | The tool is for a single Portuguese institution. PT-only is honest and correct. | |

**User's choice:** PT primary, one EN section at top  
**Notes:** —

---

## No institutional attribution (UMinho removal)

| Option | Description | Selected |
|--------|-------------|----------|
| Drop the disclaimer entirely | About dialog has app name, version, license note, and repo link. No institutional affiliation text at all. | ✓ |
| Generic disclaimer only | One-line: "This tool is independent and not affiliated with any institution." No institution named. | |
| You decide | Claude writes the most appropriate About dialog content. | |

**User's choice:** Drop the disclaimer entirely  
**Context provided by user:** "No mention of Universidade do Minho whatsoever, not in the code, not in the github repo, not in the GUI, no mention at all."  
**Notes:** This overrides BRAND-04 (which specified a UMinho disclaimer in README and About dialog). The planner must grep the entire project for "Universidade" and "UMinho" and remove all instances. Affected files include at minimum: `pyproject.toml` description, `src/eleitorum/ui/dialogs.py`, `src/eleitorum/ui/strings.py`.

---

## SPECIFICATION.md sourcing

| Option | Description | Selected |
|--------|-------------|----------|
| Copy Eleitorum.md verbatim | `.planning/Eleitorum.md` copied to `SPECIFICATION.md`. Already IS the spec — no duplication work. | ✓ (delegated) |
| Symlink / reference only | SPECIFICATION.md contains just a pointer. GitHub doesn't follow relative references. | |
| Trimmed user-facing version | Strip AI-agent instructions, keep only product contract (Sections 1–9). | |

**User's choice:** Delegated to Claude — "I don't know what a specification.md is and for what is it used, so feel free to decide this one"  
**Claude's decision:** Copy `.planning/Eleitorum.md` verbatim — it is already the complete spec and requires no modification.

---

## CHANGELOG v1.0.0 entry

| Option | Description | Selected |
|--------|-------------|----------|
| Full feature list — comprehensive | All major capabilities listed under Added. The permanent record of what was shipped. | ✓ |
| Brief — just "initial release" | One line: "Initial release of EleitorUM v1.0.0." Minimal but loses historical record. | |
| You decide | Claude writes the most appropriate CHANGELOG entry. | |

**User's choice:** Full feature list — comprehensive  
**Notes:** Keep-a-Changelog format; Added section only (initial release has no Changed/Fixed/Removed).

---

## GitHub Release publication

| Option | Description | Selected |
|--------|-------------|----------|
| Publish automatically | Tag push → CI builds → smoke test passes → release published with ZIP + SHA-256. One step. | ✓ |
| Create as draft | CI creates a draft release. Manual review and click Publish before going public. | |

**User's choice:** Publish automatically  
**Notes:** Solo project, single-version lifecycle. No review gate needed.

---

## Cold-start benchmark (--onedir vs --onefile)

| Option | Description | Selected |
|--------|-------------|----------|
| --onedir by default, manual test documented | build.py defaults to --onedir. Comment explains how to test --onefile manually. No automated benchmark. | ✓ |
| build.py runs both and prints times | Build script builds both modes and measures cold-start time. Useful data; adds ~2 min per run. | |

**User's choice:** --onedir by default, manual test documented  
**Notes:** BLD-02 advisory benchmark requirement satisfied by the manual test documentation. GitHub Actions runners too variable for meaningful timing.

---

## Claude's Discretion

- **SPECIFICATION.md:** Copy `.planning/Eleitorum.md` verbatim (user explicitly delegated this)
- **Version bump timing:** Bump to `1.0.0` within Phase 4 plan work (not a separate final commit)
- **`--version` CLI arg:** Add `argparse` block in `__main__.py` before Qt init; exit code 0
- **CONTRIBUTING.md:** Brief "archived project, external contributions not accepted"
- **RENAMING.md:** Checklist covering `config.py`, `pyproject.toml`, `README.md`, `SPECIFICATION.md`, `CHANGELOG.md`, `CONTRIBUTING.md`, `scripts/build.py`, CI workflows, About dialog, window title, distribution ZIP filename
- **`.gitignore`:** Standard Python + PyInstaller + IDE + OS
- **`.gitattributes`:** `* text=auto`; Python source `eol=lf`; binary assets marked binary
- **SHA-256 format:** BSD-style one-liner (`<hex>  filename`)
- **Windows PE metadata:** PyInstaller version file generated in build script
- **Icon generation:** PNG sizes 16, 32, 48, 64, 128, 256, 512 + multi-size ICO from icon.svg

## Deferred Ideas

None — discussion stayed within phase scope.
