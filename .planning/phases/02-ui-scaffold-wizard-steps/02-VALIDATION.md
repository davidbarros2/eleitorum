---
phase: 2
slug: ui-scaffold-wizard-steps
status: draft
nyquist_compliant: true
wave_0_complete: false
created: 2026-05-23
---

# Phase 2 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 9.0.3 + pytest-qt 4.5.0 |
| **Config file** | `pyproject.toml` (`[tool.pytest.ini_options]` with `qt_api = "pyside6"`) |
| **Quick run command** | `pytest tests/unit/ui/ -x -q` |
| **Full suite command** | `pytest --cov=src/eleitorum --cov-report=term-missing` |
| **Estimated runtime** | ~15 seconds |

---

## Sampling Rate

- **After every task commit:** Run `pytest tests/unit/ui/ -x -q`
- **After every plan wave:** Run `pytest --cov=src/eleitorum --cov-report=term-missing`
- **Before `/gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 15 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 02-xx-01 | pyproject/config | 0 | APP-01, TST-10 | — | N/A | unit | `pytest -x -q` | ❌ W0 | ⬜ pending |
| 02-xx-02 | theme.py | 1 | APP-05, APP-06 | — | N/A | unit | `pytest tests/unit/ui/test_theme.py -x -q` | ❌ W0 | ⬜ pending |
| 02-xx-03 | session.py | 1 | WIZ-01 | — | N/A | unit | `pytest tests/unit/ui/test_session.py -x -q` | ❌ W0 | ⬜ pending |
| 02-xx-04 | PipelineWorker | 1 | WIZ-09, PERF-02 | — | No crash on cancel signal | unit | `pytest tests/unit/ui/test_worker.py -x -q` | ❌ W0 | ⬜ pending |
| 02-xx-05 | step_type.py | 2 | WIZ-01, APP-17 | — | N/A | pytest-qt | `pytest tests/unit/ui/test_step_type.py -x -q` | ❌ W0 | ⬜ pending |
| 02-xx-06 | step_upload.py | 2 | WIZ-02, WIZ-03 | — | N/A | pytest-qt | `pytest tests/unit/ui/test_step_upload.py -x -q` | ❌ W0 | ⬜ pending |
| 02-xx-07 | step_sheet.py | 2 | WIZ-04 | — | N/A | pytest-qt | `pytest tests/unit/ui/test_step_sheet.py -x -q` | ❌ W0 | ⬜ pending |
| 02-xx-08 | step_columns.py | 2 | WIZ-05, WIZ-07 | — | N/A | pytest-qt | `pytest tests/unit/ui/test_step_columns.py -x -q` | ❌ W0 | ⬜ pending |
| 02-xx-09 | step_processing.py | 2 | WIZ-08, WIZ-09 | — | Cancel confirmed before abort | pytest-qt | `pytest tests/unit/ui/test_step_processing.py -x -q` | ❌ W0 | ⬜ pending |
| 02-xx-10 | step_preview.py | 2 | WIZ-06, WIZ-11 | — | N/A | pytest-qt | `pytest tests/unit/ui/test_step_preview.py -x -q` | ❌ W0 | ⬜ pending |
| 02-xx-11 | step_done.py | 2 | WIZ-07 | — | N/A | pytest-qt | `pytest tests/unit/ui/test_step_done.py -x -q` | ❌ W0 | ⬜ pending |
| 02-xx-12 | main_window.py | 3 | APP-01, APP-14, APP-15 | — | N/A | pytest-qt | `pytest tests/unit/ui/test_main_window.py -x -q` | ❌ W0 | ⬜ pending |
| 02-xx-13 | QSettings | 3 | APP-08, APP-09, APP-10, APP-11 | — | N/A | pytest-qt | `pytest tests/unit/ui/test_main_window.py -x -q` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

Wave 0 is delivered by **plan 02-01** (single plan, three tasks). After plan 02-01 executes successfully, every checkbox below becomes ✅ and `wave_0_complete` flips to `true`:

- [ ] `tests/unit/ui/__init__.py` — UI test package marker (plan 02-01 Task 3)
- [ ] `tests/unit/ui/conftest.py` — `qtbot` fixtures, `SessionModel` factory placeholder, mock `PipelineResult` (plan 02-01 Task 3)
- [ ] `pyproject.toml` updated with `PySide6==6.11.1`, `pytest-qt==4.5.0`, `qt_api = "pyside6"` (plan 02-01 Task 1)
- [ ] `src/eleitorum/ui/worker.py` defining `PipelineWorker` and `PipelineCancelledError` (plan 02-01 Task 2) — required by step_processing in plan 02-05 and wizard.py in plan 02-06
- [ ] Stub-or-real test files per feature are created by each subsequent plan as that plan executes (test_session.py, test_theme.py, etc.) — no separate "stub" step is needed because TDD discipline embeds test creation into every task

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| WCAG AA contrast for all text in light + dark themes | APP-19 | No automated contrast-check tool in offline stack; requires visual inspection | Load the app in both themes; check all text against palette using a browser dev tools contrast checker or OS accessibility inspector |
| Inter font renders correctly (not falling back to system font) | APP-13 | Font rendering is visual; automated test only confirms file loaded | Launch app, visually inspect all text for Inter letterforms (check 'a', 'g', numbers) |
| First-run welcome dialog appears only once | APP-16 | Requires fresh QSettings state; integration test would need isolated QSettings scope | Delete `HKCU\Software\EleitorUM` registry key, launch app twice; confirm dialog appears on first launch only |
| Drag-and-drop accepts files from Windows Explorer | WIZ-02 | Windows MIME types differ from test-simulated events; real drag required | Drag an XLSX file from Windows Explorer onto the drop zone; confirm file loads and name displays |
| Window geometry restores after minimize/maximize/move | APP-09 | Geometry persistence requires real window manager round-trip | Resize and move window, close, reopen; confirm size and position match |
| Theme toggle visible in both themes (WCAG AA) | APP-05 | Visual + system integration check | Toggle Ver → Tema Escuro / Tema Claro; confirm instant switch with no flicker and readable text in both |

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies (verified across plans 02-01 through 02-06)
- [x] Sampling continuity: no 3 consecutive tasks without automated verify (every task has `<automated>` except the final human checkpoint Task 4 of 02-06, which is intentional)
- [x] Wave 0 covers all MISSING references (plan 02-01 creates pytest-qt infrastructure; subsequent plans add per-feature test files)
- [x] No watch-mode flags
- [x] Feedback latency < 15s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** pending (will flip after plan 02-01 executes and Wave 0 is concretely complete — at that point set `wave_0_complete: true`)
