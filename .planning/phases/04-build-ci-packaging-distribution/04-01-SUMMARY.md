---
phase: "04-build-ci-packaging-distribution"
plan: 1
subsystem: "version, branding, cli"
tags: [version-bump, branding, cli, regression-test, pyproject]
dependency_graph:
  requires: []
  provides:
    - "version.py canonical __version__ = '1.0.0'"
    - "--version CLI flag (exits before Qt, headless-safe)"
    - "clean brand: no institution name in src/, README.md, pyproject.toml"
    - "BRAND-04 regression guard test (test_no_uminho_strings.py)"
  affects:
    - "downstream build script reads version.py"
    - "CI smoke test invokes --version"
    - "grep guard blocks future re-introduction of institution names"
tech_stack:
  added: []
  patterns:
    - "argparse parse_known_args() for --version before Qt import"
    - "PYTHONPATH injection in subprocess tests for src/ layout"
    - "ruff-fixed: auto-sorted imports via --fix"
key_files:
  created:
    - tests/unit/test_version.py
    - tests/unit/test_no_uminho_strings.py
  modified:
    - src/eleitorum/version.py
    - src/eleitorum/__main__.py
    - src/eleitorum/__init__.py
    - src/eleitorum/ui/strings.py
    - src/eleitorum/ui/dialogs.py
    - pyproject.toml
    - tests/unit/ui/test_dialogs.py
    - tests/unit/ui/test_strings.py
decisions:
  - "argparse parse_known_args() used (not parse_args()) so PyInstaller-injected flags do not error"
  - "Qt imports moved inside main() body — version flag exits before any PySide6 import"
  - "PYTHONPATH injected in subprocess tests since package is not installed, only on sys.path via pytest pythonpath config"
metrics:
  duration: "~7 minutes"
  completed: "2026-05-24"
  tasks_completed: 3
  files_changed: 9
---

# Phase 4 Plan 1: Version Bump, CLI Flag, and Brand Cleanup Summary

**One-liner:** Version bumped to 1.0.0 with headless-safe `--version` CLI flag, all institution name references removed from source, and a BRAND-04 regression guard added.

## Tasks Completed

| Task | Name | Commit | Key Files |
|------|------|--------|-----------|
| 1 | Bump version to 1.0.0 and add --version CLI arg | `5f65858` | version.py, __main__.py, pyproject.toml, test_version.py |
| 2 | Remove all UMinho references from strings.py and dialogs.py | `91512b2` | strings.py, dialogs.py, __init__.py, test_dialogs.py, test_strings.py |
| 3 | Add test_no_uminho_strings.py regression guard | `fa4284e` | test_no_uminho_strings.py |

## Verification Results

- `python -m eleitorum --version` prints "EleitorUM 1.0.0" and exits 0: PASS
- `python -c "from eleitorum.version import __version__; assert __version__=='1.0.0'"`: PASS
- `python -c "from eleitorum.ui.dialogs import WelcomeDialog, AboutDialog"` imports cleanly: PASS
- `pytest tests/unit/` — 365 passed, 1 skipped (net +2 from 363 baseline): PASS
- `ruff check` on all modified files: PASS

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed __init__.py module docstring containing institution reference**
- **Found during:** Task 2 verification
- **Issue:** `src/eleitorum/__init__.py` docstring contained "for Universidade do Minho" — not listed in the plan's file list but caught by the grep verification
- **Fix:** Updated docstring to "EleitorUM — electoral roll and eligibility list normalizer."
- **Files modified:** `src/eleitorum/__init__.py`
- **Commit:** `91512b2`

**2. [Rule 1 - Bug] Fixed broken test_dialogs.py import after removing UMINHO_DISCLAIMER**
- **Found during:** Task 2 (running unit tests)
- **Issue:** `tests/unit/ui/test_dialogs.py` imported `UMINHO_DISCLAIMER` from strings.py (which was removed) and had a test asserting the disclaimer appeared in the About dialog
- **Fix:** Removed `UMINHO_DISCLAIMER` import and the `test_about_dialog_shows_uminho_disclaimer` test
- **Files modified:** `tests/unit/ui/test_dialogs.py`
- **Commit:** `91512b2`

**3. [Rule 1 - Bug] Fixed broken test_strings.py REQUIRED_CONSTANTS list**
- **Found during:** Task 2 verification
- **Issue:** `tests/unit/ui/test_strings.py` required `UMINHO_DISCLAIMER` in its `REQUIRED_CONSTANTS` list — would fail now that the constant is removed
- **Fix:** Removed `"UMINHO_DISCLAIMER"` from the required constants list
- **Files modified:** `tests/unit/ui/test_strings.py`
- **Commit:** `91512b2`

**4. [Rule 1 - Bug] Updated test_version.py subprocess tests to inject PYTHONPATH**
- **Found during:** Task 1 GREEN phase
- **Issue:** Subprocess calls to `python -m eleitorum` failed with "No module named eleitorum" because the package is not installed — only on sys.path via pytest's `pythonpath` config, which doesn't apply to subprocess calls
- **Fix:** Added `_subprocess_env()` helper that injects `src/` onto `PYTHONPATH` for all subprocess invocations
- **Files modified:** `tests/unit/test_version.py`
- **Commit:** `5f65858`

## Known Stubs

None. All code changes are fully wired.

## Threat Surface Scan

No new network endpoints, auth paths, file access patterns, or schema changes introduced. The `--version` flag reads a compile-time constant with no user input reaching any eval. `parse_known_args()` prevents PyInstaller-injected flags from erroring (T-04-01-02 mitigation implemented).
