---
phase: 04-build-ci-packaging-distribution
reviewed: 2026-05-24T00:00:00Z
depth: standard
files_reviewed: 14
files_reviewed_list:
  - .github/workflows/ci.yml
  - .github/workflows/release.yml
  - scripts/build.py
  - scripts/generate_icons.py
  - src/eleitorum/__init__.py
  - src/eleitorum/__main__.py
  - src/eleitorum/ui/dialogs.py
  - src/eleitorum/ui/strings.py
  - src/eleitorum/version.py
  - tests/unit/test_no_uminho_strings.py
  - tests/unit/test_version.py
  - tests/unit/ui/test_dialogs.py
  - tests/unit/ui/test_strings.py
  - pyproject.toml
findings:
  critical: 1
  warning: 3
  info: 3
  total: 7
status: issues_found
---

# Phase 04: Code Review Report

**Reviewed:** 2026-05-24
**Depth:** standard
**Files Reviewed:** 14
**Status:** issues_found

## Summary

Phase 04 delivered: version bump to 1.0.0, UMinho string removal, icon generation script, PyInstaller build script, and GitHub Actions CI/release workflows. The core pipeline (build.py, generate_icons.py), version module, and CI test job are sound. One blocker was found in the release workflow: both the smoke test regex and the artifact upload filenames are hardcoded to version `1.0.0`, which will break the pipeline silently the first time a future tag (e.g. `v1.1.0`) is pushed. Three warnings address APP-20 violations in `dialogs.py` (hardcoded PT-PT strings that bypass `strings.py`) and a side-effect at module import time in `__main__.py`. Three informational items cover a redundant `noqa` comment, a gap in brand compliance test coverage, and partial dev-dependency audit coverage.

---

## Critical Issues

### CR-01: Release workflow hardcodes version `1.0.0` in smoke test and artifact filenames

**File:** `.github/workflows/release.yml:35` and `.github/workflows/release.yml:44-46`

**Issue:** Both the smoke test version-match regex and the `softprops/action-gh-release` file list reference the literal string `1.0.0`:

- Line 35: `if ($output -notmatch "EleitorUM 1\.0\.0")` — when tag `v1.1.0` is pushed, the built EXE outputs `EleitorUM 1.1.0`, the regex does not match, and the workflow fails at the smoke test step.
- Lines 44-46: the upload `files:` block names `EleitorUM-1.0.0-win64.zip` and `EleitorUM-1.0.0-win64.zip.sha256`. `build.py` creates these files using `f"EleitorUM-{version}-win64.zip"` (dynamic, correct), so for `v1.1.0` the actual files on disk are named `EleitorUM-1.1.0-win64.zip`. The upload action then fails because the glob finds no files matching the hardcoded names.

The result is that every future release tag after `1.0.0` will produce a failed workflow — the build succeeds but the smoke test aborts and/or the release assets are never uploaded.

**Fix:** Extract the version dynamically from the tag reference and use it in both places:

```yaml
- name: Extract version from tag
  id: version
  run: |
    $ver = "${{ github.ref_name }}" -replace '^v', ''
    echo "ver=$ver" >> $env:GITHUB_OUTPUT

- name: Smoke test — --version
  run: |
    $output = & dist\EleitorUM\EleitorUM.exe --version 2>&1
    if ($LASTEXITCODE -ne 0) {
      Write-Error "EleitorUM.exe --version exited $LASTEXITCODE"
      exit 1
    }
    $expected = "EleitorUM ${{ steps.version.outputs.ver }}"
    if ($output -notmatch [regex]::Escape($expected)) {
      Write-Error "Version mismatch: expected '$expected', got '$output'"
      exit 1
    }
    Write-Host "Smoke test passed: $output"

- name: Publish GitHub Release
  uses: softprops/action-gh-release@v2
  with:
    files: |
      EleitorUM-${{ steps.version.outputs.ver }}-win64.zip
      EleitorUM-${{ steps.version.outputs.ver }}-win64.zip.sha256
```

---

## Warnings

### WR-01: `dialogs.py` — hardcoded `"Fechar"` string bypasses `strings.py` (APP-20 violation)

**File:** `src/eleitorum/ui/dialogs.py:136`

**Issue:** The `AboutDialog` close button is created with a literal string:

```python
close_btn = QPushButton("Fechar")
```

The project's APP-20 requirement (also stated in the `strings.py` module docstring) is explicit: "No string literals may appear in widget code. All user-facing copy is defined here." No `BTN_FECHAR` constant exists in `strings.py`. This means the close button label is invisible to future translations/copy changes and bypasses the centralized copy governance.

**Fix:** Add a constant to `strings.py` and import it:

```python
# strings.py
BTN_FECHAR: str = "Fechar"
```

```python
# dialogs.py — add BTN_FECHAR to the import block, then:
close_btn = QPushButton(BTN_FECHAR)
```

---

### WR-02: `dialogs.py` — hardcoded `"— Sobre"` in `AboutDialog` window title (APP-20 violation)

**File:** `src/eleitorum/ui/dialogs.py:100`

**Issue:** The `AboutDialog` window title embeds a hardcoded PT-PT word:

```python
self.setWindowTitle(f"{APP_NAME} — Sobre")
```

`strings.py` contains `MENU_SOBRE = "Sobre…"` (with ellipsis, for the menu item) but no constant for the dialog window title variant. The literal `"— Sobre"` in widget code violates APP-20. If the copy needs to change (e.g., to "Acerca de"), the dialog title is the one place that will be missed.

**Fix:** Add a dedicated constant:

```python
# strings.py
ABOUT_WINDOW_TITLE: str = "Sobre"
```

```python
# dialogs.py
self.setWindowTitle(f"{APP_NAME} — {ABOUT_WINDOW_TITLE}")
```

---

### WR-03: `__main__.py` — `_check_version_flag()` executes at module import time

**File:** `src/eleitorum/__main__.py:37`

**Issue:** Line 37 calls `_check_version_flag()` at the top level of the module body, outside any `if __name__ == "__main__"` guard or function. This means the function — which calls `sys.exit(0)` when `--version` is present and which parses `sys.argv` — runs whenever `eleitorum.__main__` is imported. Any test or tool that does `import eleitorum.__main__` will trigger `sys.argv` parsing as a side effect at import time.

The current tests deliberately use `subprocess.run` to avoid this, which is correct. But the pattern is fragile: a future test author who writes `from eleitorum.__main__ import main` for unit testing will get a surprise `sys.exit(0)` or unexpected `sys.argv` parsing, depending on the test runner's argument list.

**Fix:** Move the top-level call inside the `if __name__ == "__main__"` block, and invoke it from `main()` before the Qt imports:

```python
def main() -> int:
    _check_version_flag()   # safe here: only runs when __main__ is the entry point

    from eleitorum.ui.app import create_app
    from eleitorum.ui.main_window import MainWindow

    app = create_app()
    window = MainWindow()
    window.show()
    return app.exec()

if __name__ == "__main__":
    raise SystemExit(main())
```

This preserves the headless-safe `--version` path while removing the import-time side effect. The console-script entry point (if any) already calls `main()` directly, so the fix covers that path too.

---

## Info

### IN-01: `build.py:138` — `noqa: PLC0415` suppresses a rule that is not selected in ruff config

**File:** `scripts/build.py:138`

**Issue:** The comment `# noqa: PLC0415` references the pylint-compatible `import-outside-toplevel` rule. The project's ruff configuration in `pyproject.toml` only selects `["E", "F", "I", "B", "UP", "N", "SIM"]`. The `C` (convention/pylint) rule category is not enabled, so `PLC0415` is never checked and the `noqa` suppression has no effect. While harmless today, if `ruff check --select ALL` or `RUF100` (unused-noqa) is ever enabled, this comment would trigger a new warning.

**Fix:** Replace the misleading suppressor with a plain explanatory comment:

```python
import PyInstaller.__main__  # imported inside main() to avoid loading on --help
```

---

### IN-02: `test_no_uminho_strings.py` — brand compliance scan excludes `scripts/` directory

**File:** `tests/unit/test_no_uminho_strings.py:12-16`

**Issue:** The `_SCAN_ROOTS` list is `[Path("src"), Path("README.md"), Path("pyproject.toml")]`. The `scripts/` directory (containing `build.py` and `generate_icons.py`) is not scanned. These files currently contain no institution name references (verified), but any future script added under `scripts/` would be invisible to the brand compliance test.

**Fix:** Add `scripts/` to the scan roots and expand the file glob to include Python files:

```python
_SCAN_ROOTS: list[pathlib.Path] = [
    pathlib.Path("src"),
    pathlib.Path("scripts"),
    pathlib.Path("README.md"),
    pathlib.Path("pyproject.toml"),
]
```

The existing `rglob("*.py")` branch already handles directories correctly, so no other change is needed.

---

### IN-03: `ci.yml` audit job — dev dependencies are not covered by `pip-audit`

**File:** `.github/workflows/ci.yml:40-52`

**Issue:** The `audit` job uses `pypa/gh-action-pip-audit@v1.1.0` with `inputs: .`, which audits the project's declared runtime dependencies (`[project.dependencies]`) but not the `[dev]` extras. Dev-time tools that run in CI and in the release pipeline — `pyinstaller`, `svglib`, `reportlab`, `Pillow` — are not scanned for CVEs. A vulnerability in a build-time dependency can compromise CI artifact integrity (supply chain risk).

**Fix:** Pass `--all-extras` via `extra-args` to include dev dependencies in the audit:

```yaml
- uses: pypa/gh-action-pip-audit@v1.1.0
  with:
    inputs: .
    extra-args: --all-extras
```

---

_Reviewed: 2026-05-24_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
