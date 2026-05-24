---
status: partial
phase: 04-build-ci-packaging-distribution
source: [04-VERIFICATION.md]
started: 2026-05-24T00:00:00Z
updated: 2026-05-24T00:00:00Z
---

## Current Test

[awaiting human testing]

## Tests

### 1. --version flag live output
expected: Running `python -m eleitorum --version` (or the built EXE with `--version`) prints `EleitorUM 1.0.0` and exits with code 0
result: [pending]

### 2. Manual UI checks A–G (deferred from Phase 2) + updated F
expected: All UI flows work correctly; About dialog (check F) shows no UMinho disclaimer
result: [pending]

### 3. Release workflow live test
expected: Pushing a `v1.0.0` tag triggers release.yml on GitHub Actions; smoke test passes; EleitorUM-1.0.0-win64.zip and .sha256 are attached to the GitHub Release
result: [pending]

### 4. EXE launch test
expected: Running `python scripts/build.py` completes without error; double-clicking `dist/EleitorUM/EleitorUM.exe` opens the application; `--version` works from the EXE
result: [pending]

## Summary

total: 4
passed: 0
issues: 0
pending: 4
skipped: 0
blocked: 0

## Gaps
