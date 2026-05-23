---
phase: 1
slug: core-pipeline
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-05-23
---

# Phase 1 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 9.0.3 |
| **Config file** | `pyproject.toml` [tool.pytest.ini_options] — Wave 0 installs |
| **Quick run command** | `pytest tests/unit/ -x -q` |
| **Full suite command** | `pytest tests/ --cov=src/eleitorum/core --cov-report=term-missing --cov-fail-under=90` |
| **Estimated runtime** | ~30 seconds (unit suite); ~60 seconds (full suite with coverage) |

---

## Sampling Rate

- **After every task commit:** Run `pytest tests/unit/ -x -q`
- **After every plan wave:** Run `pytest tests/ --cov=src/eleitorum/core --cov-report=term-missing`
- **Before `/gsd-verify-work`:** `pytest tests/ --cov=src/eleitorum/core --cov-fail-under=90` must be green
- **Max feedback latency:** 60 seconds (full suite)

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 1-W0-setup | 01 | 0 | (infra) | — | N/A | infra | `python -c "import pytest; import openpyxl; import xlrd; import odfpy; import charset_normalizer"` | ❌ W0 | ⬜ pending |
| 1-errors | 01 | 1 | VAL-01–09 | T-1-01 | PT-PT error messages, no stack traces | unit | `pytest tests/unit/test_errors.py -x -q` | ❌ W0 | ⬜ pending |
| 1-readers | 01 | 1 | INP-01–13 | T-1-03 | PermissionError caught, no path traversal | unit | `pytest tests/unit/test_readers.py -x -q` | ❌ W0 | ⬜ pending |
| 1-detection | 02 | 1 | DET-01–07, INP-07–09 | — | N/A | unit | `pytest tests/unit/test_detection.py -x -q` | ❌ W0 | ⬜ pending |
| 1-transform | 02 | 1 | TRF-01–15 | — | N/A | unit | `pytest tests/unit/test_transform.py -x -q` | ❌ W0 | ⬜ pending |
| 1-validate | 03 | 2 | VAL-01–09 | T-1-02 | Collect all failures before raising | unit | `pytest tests/unit/test_validate.py -x -q` | ❌ W0 | ⬜ pending |
| 1-output | 03 | 2 | OUT-01–12 | T-1-04 | Never write to input path, no partial output | unit | `pytest tests/unit/test_output.py -x -q` | ❌ W0 | ⬜ pending |
| 1-logging | 04 | 2 | LOG-01–07 | — | N/A | unit | `pytest tests/unit/test_logging.py -x -q` | ❌ W0 | ⬜ pending |
| 1-pipeline | 04 | 3 | PERF-01, PERF-03 | T-1-01–04 | All threats mitigated end-to-end | integration | `pytest tests/integration/ -x -q` | ❌ W0 | ⬜ pending |
| 1-coverage | 05 | 3 | (gate) | — | N/A | coverage | `pytest tests/ --cov=src/eleitorum/core --cov-fail-under=90` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `pyproject.toml` — project metadata, pinned dependencies, ruff/mypy/pytest config
- [ ] `src/eleitorum/__init__.py` — package init
- [ ] `src/eleitorum/core/__init__.py` — core package init
- [ ] `tests/__init__.py` — test package init
- [ ] `tests/conftest.py` — shared fixtures (tmp_path helpers, sample data constants)
- [ ] `tests/fixtures/__init__.py` — fixtures package init
- [ ] `tests/fixtures/generators.py` — all 15 fixture functions per spec Section 14.3
- [ ] `tests/unit/__init__.py` — unit test package init
- [ ] `tests/unit/test_errors.py` — stub with test function signatures
- [ ] `tests/unit/test_readers.py` — stub with test function signatures
- [ ] `tests/unit/test_detection.py` — stub with test function signatures
- [ ] `tests/unit/test_transform.py` — stub with test function signatures
- [ ] `tests/unit/test_validate.py` — stub with test function signatures
- [ ] `tests/unit/test_output.py` — stub with test function signatures
- [ ] `tests/unit/test_logging.py` — stub with test function signatures
- [ ] `tests/integration/__init__.py` — integration test package init
- [ ] `tests/integration/test_full_pipeline.py` — stub with test function signatures

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| BOM acceptance by electoral platform | OUT-01, D-03 | Requires live platform access | Open output CSV in electoral system; verify it loads without error. Toggle `USE_BOM = False` in `output.py` if rejected. |
| Windows-1252 encoding detection on real UMinho files | INP-07, D-06 | Real files contain personal data (not in repo) | Open a real UMinho file; verify detected encoding is logged as `cp1252` or `windows-1252` with no garbled output. |
| Sheet picker appearance for empty/title-only sheets | INP-11 | Phase 2 UI not yet built | Verify `make_multi_sheet_xlsx()` includes a sheet with only a header row; pipeline returns `is_empty=True` for that sheet. |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 60s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
