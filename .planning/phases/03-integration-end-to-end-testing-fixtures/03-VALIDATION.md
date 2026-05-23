---
phase: 03
slug: integration-end-to-end-testing-fixtures
status: draft
nyquist_compliant: true
wave_0_complete: true
created: 2026-05-23
---

# Phase 03 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 9.0.3 + pytest-qt 4.5.0 |
| **Config file** | `pyproject.toml` — `[tool.pytest.ini_options]` with `qt_api = "pyside6"` |
| **Quick run command** | `pytest tests/ -x -q` |
| **Full suite command** | `pytest --cov=src/eleitorum/core --cov-report=term-missing` |
| **Estimated runtime** | ~30 seconds (full suite) |

---

## Sampling Rate

- **After every task commit:** Run `pytest tests/ -x -q`
- **After every plan wave:** Run `pytest --cov=src/eleitorum/core --cov-report=term-missing`
- **Before `/gsd-verify-work`:** Full suite must be green AND coverage ≥ 90%
- **Max feedback latency:** 30 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 03-01-01 | 01 | 1 | TST-01/TST-02 | — | N/A | integration | `pytest tests/integration/test_worker_integration.py -v` | ❌ created by task | ⬜ pending |
| 03-01-02 | 01 | 1 | TST-05 | — | N/A | integration | `pytest tests/integration/test_full_pipeline.py::test_happy_path_elegiveis_csv -v` | ✅ | ⬜ pending |
| 03-01-03 | 01 | 1 | TST-09 | — | N/A | coverage | `pytest --cov=src/eleitorum/core --cov-report=term-missing --cov-fail-under=90` | ✅ | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [x] `tests/integration/test_worker_integration.py` — created by Task 1 in Wave 1 (no prior Wave 0 needed — existing infrastructure is complete)
- [x] `qtbot` fixture availability — N/A: pytest-qt provides `qtbot` globally without a conftest.py; verified in RESEARCH.md against live codebase. No conftest.py needed in `tests/integration/`.

*Existing infrastructure (pytest-qt, generators.py, test_full_pipeline.py) is already in place.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Coverage threshold applies to aggregate, not per-module | TST-09 | Aggregate gate is the operative constraint; readers.py (78%) and detection.py (88%) are below per-module but aggregate is 90.39% | Run `pytest --cov=src/eleitorum/core --cov-report=term-missing`; verify overall `TOTAL` row ≥ 90% |

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify (3/3 have automated verify)
- [x] Wave 0 covers all MISSING references (test_worker_integration.py created by Task 1; conftest N/A)
- [x] No watch-mode flags
- [x] Feedback latency < 30s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** 2026-05-23
