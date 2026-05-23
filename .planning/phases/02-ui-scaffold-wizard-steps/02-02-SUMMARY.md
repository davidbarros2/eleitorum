---
phase: 02-ui-scaffold-wizard-steps
plan: "02"
subsystem: ui-foundation
tags: [session-model, strings, theme, qss, icon, svg, ofl, wcag, pytest-qt]
dependency_graph:
  requires:
    - 02-01 (tests/unit/ui/ package + conftest.py scaffold)
  provides:
    - SessionModel @dataclass in src/eleitorum/ui/session.py
    - 69 PT-PT string constants in src/eleitorum/ui/strings.py
    - LIGHT_QSS + DARK_QSS + apply_theme + detect_system_theme in src/eleitorum/ui/theme.py
    - src/eleitorum/resources/ package with icon.svg (BRAND-02)
    - src/eleitorum/resources/fonts/Inter/ directory with OFL.txt
  affects:
    - All plans 02-03 through 02-06 (session, strings, theme, icon consumed by every step widget)
tech_stack:
  added: []
  patterns:
    - "@dataclasses.dataclass (NOT frozen) for mutable session state"
    - "AnnAssign AST node handling for annotated typed constants (STEP_1_TITLE: str = ...)"
    - "WCAG 2.1 relative luminance + contrast ratio computation (pure stdlib, no library)"
    - "Dynamic QSS property selectors: OptionCard[selected='true'], DropZone[drag_active='true']"
    - "Qt.ColorScheme.Dark / Light / Unknown detection for theme fallback"
key_files:
  created:
    - src/eleitorum/ui/session.py (58 lines — SessionModel @dataclass, 8 fields, Qt-free)
    - src/eleitorum/ui/strings.py (180 lines — 69 PT-PT string constants)
    - src/eleitorum/ui/theme.py (322 lines — LIGHT_QSS + DARK_QSS + 2 functions)
    - src/eleitorum/resources/__init__.py (0 bytes — package marker)
    - src/eleitorum/resources/icon.svg (4 lines — 256x256 SVG BRAND-02)
    - src/eleitorum/resources/fonts/__init__.py (0 bytes — package marker)
    - src/eleitorum/resources/fonts/Inter/.gitkeep (0 bytes — tracks empty directory)
    - src/eleitorum/resources/fonts/Inter/OFL.txt (102 lines — SIL OFL 1.1 for Inter)
    - tests/unit/ui/test_session.py (108 lines — 9 tests)
    - tests/unit/ui/test_strings.py (175 lines — 9 tests with AST inspection)
    - tests/unit/ui/test_theme.py (120 lines — 8 tests including WCAG AA)
    - tests/unit/ui/test_resources.py (98 lines — 7 tests)
  modified:
    - tests/unit/ui/conftest.py (session_fresh upgraded from None stub to real SessionModel())
decisions:
  - "AST parser uses ast.AnnAssign (not just ast.Assign) for annotated typed constants"
  - "column_headers: list[str] | None added to SessionModel per plan warning — StepColumns needs parsed headers"
  - "UMINHO_DISCLAIMER verbatim from Eleitorum.md §3.5 (confirmed, not a TODO placeholder)"
  - "Inter .ttf files deferred to plan 06 / Phase 4 build prep; OFL.txt + .gitkeep in place"
  - "apply_theme() guards QApplication.instance() is not None before calling setStyleSheet()"
metrics:
  duration: "8 minutes"
  completed: "2026-05-23"
  tasks_completed: 3
  files_created: 12
  tests_added: 33
  tests_total: 275
---

# Phase 2 Plan 2: Foundation Contracts Summary

**One-liner:** Qt-free SessionModel @dataclass, 69 PT-PT string constants, LIGHT/DARK QSS theme system with WCAG AA compliance, and BRAND-02 icon SVG committed as non-widget foundation for all wizard step plans.

## What Was Built

### Task 1 — SessionModel + strings.py (commit `8bff8a8`)

**`src/eleitorum/ui/session.py`** — 58 lines:
- `@dataclasses.dataclass class SessionModel` (NOT frozen — mutable by design per D-05)
- 8 fields all defaulting to `None`: `output_type`, `source_path`, `sheet_name`, `column_map`, `pipeline_result`, `output_path`, `sheets`, `column_headers`
- Zero PySide6 imports — Qt-free contract enforced by AST inspection in tests
- `column_headers: list[str] | None = None` added per plan action (StepColumns dropdowns need parsed header row; cleaner than duck-typing at runtime — plan 02-04 Task 3)

**`src/eleitorum/ui/strings.py`** — 180 lines:
- 69 PT-PT string constants (target was ~60; extras cover all menu items, dialog content, and preview labels from 02-UI-SPEC)
- All grouped with comment dividers matching Phase 1 `errors.py` structure
- `UMINHO_DISCLAIMER` is verbatim from `Eleitorum.md §3.5` — confirmed, not a TODO
- Format-string constants with required placeholders: `STEP_INDICATOR` ({n}, {total}), `PROCESSING_PROGRESS` ({current}, {total}), `ERR_UNSUPPORTED_EXT` ({ext}), `SHEET_PICKER_ROWS_TEMPLATE` ({rows}), `DONE_SUCCESS_SUMMARY` ({rows}, {changes})

**`tests/unit/ui/conftest.py`** — upgraded `session_fresh` fixture from `None` stub to real `SessionModel()`.

**Test results:** 18 passed (9 session + 9 strings)

**Deviation noted:** The test's `_parse_strings_module()` helper needed to handle `ast.AnnAssign` nodes (annotated assignments like `STEP_1_TITLE: str = "..."`) in addition to plain `ast.Assign`. The helper was corrected to iterate `tree.body` (module-level only) and check both node types. This is a Rule 1 auto-fix (test bug, not a production code issue).

### Task 2 — theme.py (commit `c625137`)

**`src/eleitorum/ui/theme.py`** — 322 lines:
- `LIGHT_QSS: str` — 130+ lines of QSS covering QWidget, QMainWindow, QPushButton (all states), QLabel (stepTitle/displayHeading/mutedText), QLineEdit, QComboBox, QListWidget, QTableWidget, QTextEdit, QProgressBar, QMenuBar, QMenu, QFrame#card, OptionCard, DropZone, QDialog
- `DARK_QSS: str` — equivalent dark-palette coverage
- Both contain `OptionCard[selected="true"]`, `DropZone[drag_active="true"]` dynamic property selectors
- Both contain `:focus` rules with 2px solid accent border (APP-17)
- Font-family: `Inter, "Segoe UI", sans-serif` (APP-13 fallback chain)
- `apply_theme(theme: str) -> None`: `DARK_QSS if theme == 'dark' else LIGHT_QSS`; guards `QApplication.instance() is not None`
- `detect_system_theme() -> str`: reads `Qt.ColorScheme`; Dark → 'dark'; Light AND Unknown → 'light' (D-06 fallback)

**Test results:** 8 passed
| Test | Result |
|------|--------|
| test_light_qss_is_nonempty_string | PASS — all 6 light hex values present + Inter |
| test_dark_qss_is_nonempty_string | PASS — all 6 dark hex values present + Inter |
| test_both_themes_contain_dynamic_property_selectors | PASS |
| test_both_themes_contain_focus_pseudo | PASS |
| test_detect_system_theme_returns_light_or_dark | PASS |
| test_apply_theme_sets_stylesheet | PASS |
| test_light_palette_passes_wcag_aa_for_primary_text | PASS — #1A1A1A on #FAFAFA ratio ≈ 18.1 >> 4.5 |
| test_dark_palette_passes_wcag_aa_for_primary_text | PASS — #F5F5F5 on #1A1A1A ratio ≈ 16.7 >> 4.5 |

### Task 3 — resources/ package (commit `dbd9ef8`)

**`src/eleitorum/resources/__init__.py`** — zero-byte package marker.

**`src/eleitorum/resources/icon.svg`** — 4-line SVG:
```xml
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 256 256" width="256" height="256">
  <rect width="256" height="256" rx="41" ry="41" fill="#a21a1c"/>
  <text … fill="#FFFFFF" text-anchor="middle">E</text>
</svg>
```
- rx="41" = 16.02% of 256 (spec: 16%; target range 40–42 — confirmed)
- White E on #a21a1c rounded square — BRAND-02 compliant
- Self-contained, no external network references (CLAUDE.md offline constraint)

**`src/eleitorum/resources/fonts/Inter/.gitkeep`** — empty, ensures git tracks directory.

**`src/eleitorum/resources/fonts/Inter/OFL.txt`** — SIL Open Font License Version 1.1 (canonical text) with header comment identifying Inter typeface and noting .ttf files are deferred.

**Test results:** 7 passed

## Requested Output Metrics

| Metric | Value |
|--------|-------|
| String constants in strings.py | 69 (target was ~60) |
| Qt-free verification (session.py) | PASSED — `grep -E '^(import|from) PySide6' session.py` returns zero matches; AST scan confirms no PySide6 ImportFrom nodes |
| Hex color match with 02-UI-SPEC | CONFIRMED — all 9 light-theme and 9 dark-theme hex values match exactly |
| UMINHO_DISCLAIMER verbatim from Eleitorum.md §3.5 | CONFIRMED verbatim — no TODO placeholder |
| Inter .ttf bundling status | DEFERRED — OFL.txt + .gitkeep in place; .ttf download is a human deliverable for plan 06 / Phase 4 build prep |

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed AST parser in test_strings.py to handle AnnAssign nodes**
- **Found during:** Task 1 GREEN phase
- **Issue:** `_parse_strings_module()` used `isinstance(node, ast.Assign)` but Python annotated assignments (`NAME: str = "..."`) produce `ast.AnnAssign` nodes, not `ast.Assign`. All 69 constants were missed.
- **Fix:** Changed the parser to iterate `tree.body` (top-level only) and handle both `ast.AnnAssign` (with `node.target`) and `ast.Assign` (with `node.targets` list).
- **Files modified:** `tests/unit/ui/test_strings.py`
- **Commit:** included in `8bff8a8`

## Threat Model Verification

All T-02-02-* mitigations applied:

| Threat ID | Mitigation Applied |
|-----------|--------------------|
| T-02-02-01 | icon.svg is author-authored, committed; not user-supplied content |
| T-02-02-02 | apply_theme() uses ternary — only 'dark' selects DARK_QSS; no string concat into QSS; guards QApplication.instance() |
| T-02-02-03 | SessionModel in-process only; no serialization, no logging of pipeline_result contents |
| T-02-02-04 | OFL.txt is non-executed text under version control |

## Threat Flags

None — no new security-relevant surface introduced beyond the planned scope.

## Known Stubs

None. All plan goals achieved; no stubs block the plan's objective.

- `strings.py` UMINHO_DISCLAIMER: confirmed verbatim, not a placeholder
- Inter .ttf files: intentionally deferred per D-04 and plan spec; OFL.txt documents the license for when files are added

## Self-Check

## Self-Check: PASSED

| Check | Result |
|-------|--------|
| src/eleitorum/ui/session.py exists | FOUND |
| src/eleitorum/ui/strings.py exists | FOUND |
| src/eleitorum/ui/theme.py exists | FOUND |
| src/eleitorum/resources/__init__.py exists | FOUND |
| src/eleitorum/resources/icon.svg exists | FOUND |
| src/eleitorum/resources/fonts/Inter/.gitkeep exists | FOUND |
| src/eleitorum/resources/fonts/Inter/OFL.txt exists | FOUND |
| tests/unit/ui/test_session.py exists | FOUND |
| tests/unit/ui/test_strings.py exists | FOUND |
| tests/unit/ui/test_theme.py exists | FOUND |
| tests/unit/ui/test_resources.py exists | FOUND |
| Commit 8bff8a8 (session + strings) | FOUND |
| Commit c625137 (theme) | FOUND |
| Commit dbd9ef8 (resources) | FOUND |
| Qt-free check on session.py | PASSED |
| SVG valid XML | PASSED |
| 275 tests pass (1 skipped) | PASSED |
| WCAG AA light theme ratio ≥ 4.5 | PASSED (~18.1) |
| WCAG AA dark theme ratio ≥ 4.5 | PASSED (~16.7) |
