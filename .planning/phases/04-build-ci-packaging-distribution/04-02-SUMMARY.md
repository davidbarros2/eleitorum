---
phase: 04-build-ci-packaging-distribution
plan: 2
subsystem: build tooling
tags: [svglib, reportlab, pillow, ico, png, icon-generation, inter-font]

requires:
  - phase: 04-build-ci-packaging-distribution
    provides: icon.svg source (white E on red square, viewBox 256x256)

provides:
  - scripts/generate_icons.py — developer utility to regenerate PNG/ICO from icon.svg
  - src/eleitorum/resources/icons/EleitorUM-{16,32,48,64,128,256,512}.png — RGBA PNGs at all required sizes
  - src/eleitorum/resources/icons/EleitorUM.ico — multi-size ICO (16/32/48/64/128/256 px) for PyInstaller --icon
  - InterVariable.ttf download step — AWAITING HUMAN ACTION (font not yet committed)

affects:
  - 04-03 (build script uses EleitorUM.ico via --icon flag and InterVariable.ttf via --add-data)
  - 04-04 (.gitattributes marks InterVariable.ttf and icon binaries as binary)

tech-stack:
  added: [svglib==1.6.0, reportlab==4.4.10, Pillow==12.1.1 (icon generation only, dev-time)]
  patterns:
    - ICO multi-size: pass largest image (256px) as base to Pillow ICO saver; smaller sizes as append_images

key-files:
  created:
    - scripts/generate_icons.py
    - src/eleitorum/resources/icons/EleitorUM-16.png
    - src/eleitorum/resources/icons/EleitorUM-32.png
    - src/eleitorum/resources/icons/EleitorUM-48.png
    - src/eleitorum/resources/icons/EleitorUM-64.png
    - src/eleitorum/resources/icons/EleitorUM-128.png
    - src/eleitorum/resources/icons/EleitorUM-256.png
    - src/eleitorum/resources/icons/EleitorUM-512.png
    - src/eleitorum/resources/icons/EleitorUM.ico
  modified: []

key-decisions:
  - "Pre-commit generated PNG/ICO files to avoid adding svglib/reportlab to CI install step (per RESEARCH.md recommendation)"
  - "Largest image (256px) must be the base image in Pillow ICO saver — Pillow filters out sizes larger than the base image dimensions"

patterns-established:
  - "ICO multi-size save: ico_images[-1].save(path, format='ICO', sizes=[...], append_images=ico_images[:-1]) where ico_images is sorted smallest-to-largest"
  - "SVG-to-PNG pipeline: svg2rlg(str(path)) -> renderPM.drawToFile(buf, fmt='PNG', dpi=96) -> Image.open(buf).convert('RGBA') -> resize"

requirements-completed:
  - BLD-04
  - BLD-05

duration: 11min
completed: 2026-05-24
---

# Phase 4 Plan 2: Icon Generation and Font Asset Preparation Summary

**svglib+Pillow pipeline generates 7 RGBA PNGs and a 6-size ICO from icon.svg; font awaits human download**

## Performance

- **Duration:** 11 min
- **Started:** 2026-05-24T00:00:00Z
- **Completed:** 2026-05-24T00:11:23Z
- **Tasks:** 1 of 2 auto-executed (Task 1 is checkpoint:human-action for InterVariable.ttf)
- **Files created:** 9 (1 script + 7 PNGs + 1 ICO)

## Accomplishments

- Created `scripts/generate_icons.py` using svglib+reportlab+Pillow — renders icon.svg to all required sizes
- Generated 7 RGBA PNG files (16px through 512px) committed to `src/eleitorum/resources/icons/`
- Generated `EleitorUM.ico` with 6 embedded sizes (16/32/48/64/128/256 px, 11,346 bytes) for PyInstaller --icon flag
- All 383 existing tests still pass; ruff reports no issues on the new script

## Task Commits

1. **Task 2: Create generate_icons.py and run it to produce PNG/ICO assets** - `3bb90e7` (feat)

**Plan metadata:** (see below — committed after SUMMARY creation)

## Files Created/Modified

- `scripts/generate_icons.py` — SVG-to-PNG/ICO generation script using svglib+reportlab+Pillow; runnable from repo root
- `src/eleitorum/resources/icons/EleitorUM-16.png` — 16x16 RGBA PNG (535 bytes)
- `src/eleitorum/resources/icons/EleitorUM-32.png` — 32x32 RGBA PNG (846 bytes)
- `src/eleitorum/resources/icons/EleitorUM-48.png` — 48x48 RGBA PNG (1,123 bytes)
- `src/eleitorum/resources/icons/EleitorUM-64.png` — 64x64 RGBA PNG (1,391 bytes)
- `src/eleitorum/resources/icons/EleitorUM-128.png` — 128x128 RGBA PNG (2,515 bytes)
- `src/eleitorum/resources/icons/EleitorUM-256.png` — 256x256 RGBA PNG (4,834 bytes)
- `src/eleitorum/resources/icons/EleitorUM-512.png` — 512x512 RGBA PNG (12,468 bytes)
- `src/eleitorum/resources/icons/EleitorUM.ico` — multi-size ICO with 6 embedded sizes (11,346 bytes)

## Decisions Made

- Pre-committed generated PNG/ICO files instead of generating them in CI, per RESEARCH.md recommendation — avoids adding svglib/reportlab to CI install and keeps build reproducible
- Task 1 (InterVariable.ttf download) executed out-of-order relative to Task 2 — Task 2 has no dependency on the font and was committed first to maximise value; the font checkpoint is still pending

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Pillow ICO saver requires largest image as base**
- **Found during:** Task 2 (ICO creation)
- **Issue:** Passing the 16px image as the first (base) argument to Pillow's ICO saver caused Pillow to filter out all sizes larger than the base image's dimensions — resulting in a 557-byte ICO containing only 16x16
- **Fix:** Changed `ico_images[0].save(...)` to `ico_images[-1].save(...)` (256px base) with `append_images=ico_images[:-1]` — Pillow's `_save` filters `size[0] > width or size[1] > height` against the base image, so the largest must be first
- **Files modified:** scripts/generate_icons.py
- **Verification:** ICO reopened with IcoImagePlugin.IcoFile — confirmed 6 embedded sizes; file is 11,346 bytes
- **Committed in:** 3bb90e7

**2. [Rule 1 - Bug] Remove unused `os` import (ruff F401)**
- **Found during:** Task 2 (ruff check acceptance criteria)
- **Issue:** `import os` was included in the initial script but `os` was not used anywhere in the implementation (pathlib.Path used throughout)
- **Fix:** Removed `import os` from the stdlib imports block
- **Files modified:** scripts/generate_icons.py
- **Verification:** `ruff check scripts/generate_icons.py` reports no issues
- **Committed in:** 3bb90e7

---

**Total deviations:** 2 auto-fixed (2 Rule 1 bugs)
**Impact on plan:** Both auto-fixes required for correctness. The ICO fix is essential — a single-size ICO would produce a very low-quality icon in Windows Explorer and the PyInstaller --icon embedding. No scope creep.

## Issues Encountered

Task 1 (checkpoint:human-action): InterVariable.ttf must be downloaded manually from https://github.com/rsms/inter/releases and placed at `src/eleitorum/resources/fonts/Inter/InterVariable.ttf`. This file was not available for automated download (no network calls in repo setup). The font directory already contains `OFL.txt`. Once placed, the file should be committed to the repo (plan 04-04 will mark it binary in .gitattributes).

## Known Stubs

None — all icon assets are fully generated and non-empty.

## User Setup Required

**InterVariable.ttf must be downloaded manually before plan 04-03 (build script) can be tested end-to-end.**

Steps:
1. Open https://github.com/rsms/inter/releases in a browser
2. Find the latest stable release (v4.x.x)
3. Download the release zip (e.g., Inter-4.1.zip)
4. Extract `InterVariable.ttf` (not InterVariable-Italic.ttf)
5. Copy to: `src\eleitorum\resources\fonts\Inter\InterVariable.ttf`
6. Verify the file is approximately 300–600 KB
7. Run `git add src/eleitorum/resources/fonts/Inter/InterVariable.ttf && git commit -m "feat(04-02): commit InterVariable.ttf from rsms/inter releases (D-02)"`

## Next Phase Readiness

- `EleitorUM.ico` ready for PyInstaller `--icon` flag in plan 04-03
- `EleitorUM-256.png` ready for any UI usage
- `scripts/generate_icons.py` committed and runnable for future icon regeneration
- **Blocker for full build:** `InterVariable.ttf` must be committed before plan 04-03's PyInstaller build can bundle the font

---
*Phase: 04-build-ci-packaging-distribution*
*Completed: 2026-05-24*
