---
phase: "04-build-ci-packaging-distribution"
plan: 5
subsystem: "ci-cd"
tags: ["github-actions", "ci", "release", "pyinstaller", "pip-audit"]
dependency_graph:
  requires:
    - "04-03"  # build.py and scripts/ directory
    - "04-04"  # pyproject.toml dev extras (ruff, mypy, pytest, pyinstaller, pip-audit)
  provides:
    - ".github/workflows/ci.yml"
    - ".github/workflows/release.yml"
  affects:
    - "Every push to main (CI gate)"
    - "v1.0.0 tag push (automated release)"
tech_stack:
  added:
    - "pypa/gh-action-pip-audit@v1.1.0 — CVE scanning in GitHub Actions"
    - "softprops/action-gh-release@v2 — artifact attachment and release publication"
    - "actions/checkout@v4 — repository checkout in CI"
    - "actions/setup-python@v5 — Python environment setup in CI"
  patterns:
    - "Matrix strategy for Python 3.11 + 3.12 on windows-latest"
    - "QT_QPA_PLATFORM=offscreen for headless pytest-qt stability"
    - "PowerShell multi-line run block for smoke test (windows-latest default shell)"
    - "pip install -e \".[dev]\" installs all tools from pyproject.toml dev extras"
key_files:
  created:
    - ".github/workflows/ci.yml"
    - ".github/workflows/release.yml"
  modified: []
decisions:
  - "release.yml delegates ZIP and SHA-256 creation to scripts/build.py (already handles both) rather than duplicating those steps in the workflow"
  - "No separate 'Create ZIP' or 'Compute SHA-256' steps in release.yml — build.py encapsulates the full artifact pipeline per plan 04-03"
  - "QT_QPA_PLATFORM=offscreen on pytest step only (not audit job) — audit does not instantiate Qt"
  - "No permissions: block in release.yml — not needed for public repositories with default GITHUB_TOKEN scope"
metrics:
  duration: "2 minutes"
  completed_date: "2026-05-24"
  tasks_completed: 2
  tasks_total: 2
  files_created: 2
  files_modified: 0
---

# Phase 4 Plan 5: GitHub Actions CI/CD Workflows Summary

**One-liner:** Push-to-main CI (ruff + mypy + pytest matrix 3.11/3.12 + pip-audit) and tag-triggered release workflow (build + PowerShell smoke test + GitHub Release publication).

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Create .github/workflows/ci.yml | 793188b | `.github/workflows/ci.yml` |
| 2 | Create .github/workflows/release.yml | aee84e9 | `.github/workflows/release.yml` |

## What Was Built

### ci.yml — Push-to-main quality gate

Two-job workflow triggered on `push` to `main` and `pull_request` targeting `main`:

**test job** (matrix: Python 3.11 + 3.12, windows-latest):
1. `actions/checkout@v4`
2. `actions/setup-python@v5` with matrix version
3. `pip install -e ".[dev]"` — installs ruff, mypy, pytest, pytest-qt from pyproject.toml
4. `ruff check src/ tests/` — lint gate
5. `ruff format --check src/ tests/` — format gate
6. `mypy src/` — type check gate
7. `pytest` with `QT_QPA_PLATFORM: offscreen` — test gate

**audit job** (windows-latest, Python 3.11):
- `pypa/gh-action-pip-audit@v1.1.0` with `inputs: .` — scans pyproject.toml; fails on high-severity CVEs

### release.yml — Tag-triggered release

Single-job workflow triggered on `push: tags: ["v*.*.*"]` (windows-latest, Python 3.11):
1. Checkout
2. Setup Python 3.11
3. `pip install -e ".[dev]"` — installs pyinstaller, svglib, reportlab, Pillow, plus all dev tools
4. `python scripts/generate_icons.py` — idempotent icon generation
5. `python scripts/build.py` — produces `dist/EleitorUM/`, `EleitorUM-1.0.0-win64.zip`, `EleitorUM-1.0.0-win64.zip.sha256`
6. PowerShell smoke test — checks `$LASTEXITCODE -ne 0` and `$output -notmatch "EleitorUM 1\.0\.0"`
7. `softprops/action-gh-release@v2` — publishes non-draft GitHub Release with ZIP + SHA-256

## Deviations from Plan

None — plan executed exactly as written.

The one design clarification (not a deviation): the plan's `<interfaces>` section referenced a Pattern 7 from RESEARCH.md that included separate "Create ZIP" and "Compute SHA-256" steps. However, `scripts/build.py` (created in plan 04-03) already handles ZIP creation and SHA-256 computation internally. The release.yml correctly calls only `python scripts/build.py` and relies on it to produce all artifacts, matching the plan's step 5 description exactly: "Produces dist/EleitorUM/, EleitorUM-1.0.0-win64.zip, EleitorUM-1.0.0-win64.zip.sha256".

## Known Stubs

None — both workflow files are complete and wired to the actual build script and test suite.

## Threat Flags

None beyond the threat model already documented in the plan:

| Mitigation Applied | File | Description |
|-------------------|------|-------------|
| T-04-05-02: pip-audit CVE scan | `.github/workflows/ci.yml` | `pypa/gh-action-pip-audit@v1.1.0` runs on every push to main |
| T-04-05-SC: softprops pinned to @v2 | `.github/workflows/release.yml` | Semantic tag pin; widely used action from trusted source |

## Verification Results

All acceptance criteria verified:

**ci.yml:**
- `.github/workflows/ci.yml` exists
- Contains `runs-on: windows-latest`
- Matrix: `python-version: ["3.11", "3.12"]`
- Contains `QT_QPA_PLATFORM: offscreen` on pytest step
- Contains `ruff check src/ tests/`
- Contains `ruff format --check src/ tests/`
- Contains `mypy src/`
- Contains `pypa/gh-action-pip-audit@v1.1.0`
- Contains `inputs: .`
- Does NOT contain `continue-on-error: true`
- YAML syntactically valid (parsed successfully with PyYAML)

**release.yml:**
- `.github/workflows/release.yml` exists
- Triggers on `push: tags: ["v*.*.*"]`
- Contains `python scripts/build.py`
- Contains `EleitorUM.exe --version` in smoke test step
- Smoke test checks `$LASTEXITCODE -ne 0`
- Smoke test checks output matches `EleitorUM 1\.0\.0`
- Contains `softprops/action-gh-release@v2`
- Lists `EleitorUM-1.0.0-win64.zip` in release files
- Lists `EleitorUM-1.0.0-win64.zip.sha256` in release files
- Does NOT contain `draft: true`
- YAML syntactically valid (parsed successfully with PyYAML)
- Does NOT use `shell: bash` or `shell: cmd`

## Self-Check: PASSED

Files created:
- `.github/workflows/ci.yml` — FOUND
- `.github/workflows/release.yml` — FOUND

Commits:
- `793188b` — FOUND (feat(04-05): add CI workflow)
- `aee84e9` — FOUND (feat(04-05): add release workflow)
