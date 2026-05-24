---
phase: 04-build-ci-packaging-distribution
plan: 03
subsystem: infra
tags: [pyinstaller, build, packaging, windows, pe-metadata, zip, sha256]

# Dependency graph
requires:
  - phase: 04-01
    provides: version.py at 1.0.0, icon file at src/eleitorum/resources/icons/EleitorUM.ico
  - phase: 04-02
    provides: Inter font at src/eleitorum/resources/fonts/Inter/InterVariable.ttf, app.py font loading path
provides:
  - scripts/build.py — PyInstaller wrapper that generates PE metadata, produces one-folder build, creates versioned ZIP and BSD-style SHA-256 checksum
affects:
  - 04-04 (CI workflows that invoke scripts/build.py on tag push)

# Tech tracking
tech-stack:
  added: [PyInstaller 6.20.0 (referenced), stdlib zipfile, stdlib hashlib, stdlib argparse, stdlib textwrap]
  patterns:
    - "sys.path.insert(0, '../src') + from eleitorum.version import __version__ for build-time version discovery"
    - "VSVersionInfo literal generation via textwrap.dedent for Windows PE metadata"
    - "PyInstaller deferred import inside main() to avoid loading on --help"
    - "BSD-style SHA-256 checksum: digest + two spaces + filename"

key-files:
  created:
    - scripts/build.py
  modified: []

key-decisions:
  - "--onedir is the default build mode; --onefile is manual opt-in documented in comment per D-07"
  - "CompanyName left empty string in PE metadata — no institution attributed per D-01"
  - "PyInstaller imported inside main() so --help works without PyInstaller installed"
  - "--add-data=src/eleitorum/resources/fonts/Inter:resources/fonts/Inter matches Phase 2 app.py _MEIPASS path"

patterns-established:
  - "Build scripts use sys.path.insert to import eleitorum modules without installation"
  - "Version is always read from eleitorum.version.__version__ — never hardcoded in build tooling"

requirements-completed: [BLD-01, BLD-02, BLD-03, BLD-04]

# Metrics
duration: 2min
completed: 2026-05-24
---

# Phase 04 Plan 03: Build Script Summary

**PyInstaller wrapper generating Windows PE metadata, one-folder EXE build, versioned ZIP, and BSD-style SHA-256 checksum — all driven by eleitorum.version.__version__ with no hardcoded strings**

## Performance

- **Duration:** 2 min
- **Started:** 2026-05-24T00:23:09Z
- **Completed:** 2026-05-24T00:24:51Z
- **Tasks:** 1
- **Files modified:** 1

## Accomplishments

- Created `scripts/build.py` — the single command developers and CI run to produce the distributable artifact
- Version metadata generated dynamically from `eleitorum.version.__version__` (chain: version.py → build.py → version_info.py → PE metadata in EXE)
- `--onedir` is default; `--onefile` documented as manual opt-in with D-07 rationale in comment
- `--add-data` path for Inter font (`resources/fonts/Inter`) matches exactly what `app.py` resolves at `sys._MEIPASS` in Phase 2
- `CompanyName` left empty per D-01; `LegalCopyright = "MIT License"`, `ProductName = "EleitorUM"`

## Task Commits

1. **Task 1: Create scripts/build.py** - `1474230` (feat)

## Files Created/Modified

- `scripts/build.py` — PyInstaller wrapper: version_info.py generation, PyInstaller invocation with correct flags, ZIP creation, SHA-256 checksum

## Decisions Made

- Deferred `import PyInstaller.__main__` inside `main()` so `python scripts/build.py --help` works on machines where PyInstaller is not yet installed (e.g., fresh CI runner before pip install)
- Used `textwrap.dedent` for the `VSVersionInfo` literal to keep indentation clean in both build.py source and the generated version_info.py output
- `_create_zip` skips directories (`if f.is_file()`) to avoid adding empty directory entries to the ZIP

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Removed extraneous f-string prefix and truncated overlong comment**
- **Found during:** Task 1 (ruff check verification)
- **Issue:** `ruff check` flagged `F541` (f-string without placeholders on the `--icon` arg) and `E501` (line too long for the `--onefile` comment)
- **Fix:** Removed the `f` prefix from the icon string literal; shortened the comment to fit within the 100-character line limit while preserving D-07 reference
- **Files modified:** `scripts/build.py`
- **Verification:** `ruff check scripts/build.py` reports "All checks passed!" after fix
- **Committed in:** `1474230` (included in task commit)

---

**Total deviations:** 1 auto-fixed (Rule 1 — minor lint errors caught during verification)
**Impact on plan:** Fix was cosmetic (unnecessary f-prefix) and style (line length). No logic or behavior change.

## Issues Encountered

None — ruff lint errors were caught immediately by the verification step and fixed inline before commit.

## Threat Surface Scan

No new network endpoints, auth paths, file access patterns, or schema changes introduced. `scripts/build.py` is a developer/CI tool only; it writes `version_info.py` (generated file, no user input) and reads `dist/EleitorUM/` (PyInstaller output). No user-controlled strings reach the build subprocess.

Threat register items T-04-03-01 through T-04-03-SC all have `accept` or `mitigate` dispositions as specified in the plan. PyInstaller is pinned to 6.20.0 in pyproject.toml (T-04-03-SC mitigation satisfied).

## User Setup Required

None — `scripts/build.py` is a developer tool. Running it requires `pip install -e ".[dev]"` which installs PyInstaller 6.20.0.

## Next Phase Readiness

- `scripts/build.py` is ready for CI to invoke via `python scripts/build.py` on `v1.0.0` tag push
- `--version-file=version_info.py` integration with the release workflow (plan 04-04) is ready
- The ZIP name pattern `EleitorUM-{version}-win64.zip` matches the release workflow artifact attachment expectation

---
*Phase: 04-build-ci-packaging-distribution*
*Completed: 2026-05-24*
