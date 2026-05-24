# Phase 4: Build, CI, Packaging + Distribution Artifacts — Pattern Map

**Mapped:** 2026-05-24
**Files analyzed:** 17 (new/modified)
**Analogs found:** 14 / 17

---

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|-----------|----------------|---------------|
| `src/eleitorum/__main__.py` | utility / entry-point | request-response | self (current `__main__.py`) | exact — extend in place |
| `src/eleitorum/version.py` | config | — | self (current `version.py`) | exact — one-line bump |
| `src/eleitorum/ui/strings.py` | config | — | self (current `strings.py`) | exact — remove 2 constants, update 2 values |
| `src/eleitorum/ui/dialogs.py` | component | request-response | self (current `dialogs.py`) | exact — remove import + widget |
| `pyproject.toml` | config | — | self (current `pyproject.toml`) | exact — bump version, update description, add deps |
| `scripts/build.py` | utility / build script | batch | `src/eleitorum/core/pipeline.py` (pipeline orchestration pattern) | partial — orchestration style only |
| `scripts/generate_icons.py` | utility / build script | transform | no analog exists | no analog |
| `.github/workflows/ci.yml` | config / CI | event-driven | no analog exists | no analog |
| `.github/workflows/release.yml` | config / CI | event-driven | no analog exists | no analog |
| `tests/unit/test_no_uminho_strings.py` | test | batch | `tests/unit/ui/test_strings.py` | role-match — same AST-inspection + file grep pattern |
| `SPECIFICATION.md` | documentation | — | `.planning/Eleitorum.md` (verbatim source) | exact — copy |
| `README.md` | documentation | — | self (current `README.md`) | exact — prepend EN paragraph, strip UMinho refs |
| `CHANGELOG.md` | documentation | — | no analog exists (Keep-a-Changelog format) | no analog |
| `CONTRIBUTING.md` | documentation | — | no analog exists | no analog |
| `RENAMING.md` | documentation | — | no analog exists | no analog |
| `LICENSE` | documentation | — | self (already exists at repo root) | no action — already correct |
| `.gitignore` | config | — | no analog exists | no analog |
| `.gitattributes` | config | — | no analog exists | no analog |

---

## Pattern Assignments

### `src/eleitorum/__main__.py` — extend with `--version` argparse

**Analog:** `src/eleitorum/__main__.py` (current file)

**Current file** (`src/eleitorum/__main__.py`, lines 1–31):
```python
"""Entry point for `python -m eleitorum`."""

from eleitorum.ui.app import create_app
from eleitorum.ui.main_window import MainWindow


def main() -> int:
    app = create_app()
    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
```

**Required change — insert argparse block BEFORE Qt imports:**

The `from eleitorum.ui.app import create_app` line is at line 14. The argparse block must appear before it. `eleitorum.ui.app` imports PySide6 at module level — if that import runs before argparse exits, `--version` will attempt Qt initialisation and fail headlessly.

**Pattern to copy** (from RESEARCH.md Pattern 1):
```python
"""Entry point for `python -m eleitorum` and the bundled EleitorUM.exe."""

from __future__ import annotations

import argparse
import sys


def _check_version_flag() -> None:
    """Handle --version before any Qt import. Exits with code 0 if --version given."""
    from eleitorum.version import __version__

    parser = argparse.ArgumentParser(prog="EleitorUM", add_help=False)
    parser.add_argument(
        "--version",
        action="store_true",
        help="Print version and exit.",
    )
    args, _ = parser.parse_known_args()
    if args.version:
        sys.stdout.write(f"EleitorUM {__version__}\n")
        sys.exit(0)


_check_version_flag()  # Must be before any eleitorum.ui.* import


def main() -> int:
    from eleitorum.ui.app import create_app
    from eleitorum.ui.main_window import MainWindow

    app = create_app()
    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
```

**Key rules:**
- `from eleitorum.version import __version__` is safe (no Qt dependency)
- Move `from eleitorum.ui.app import create_app` and `from eleitorum.ui.main_window import MainWindow` inside `main()` so they are never executed when `--version` exits early
- `parse_known_args()` not `parse_args()` — allows any extra args passed by PyInstaller without error
- `sys.stdout.write(...)` preferred over `print(...)` for testability

---

### `src/eleitorum/version.py` — version bump

**Analog:** `src/eleitorum/version.py` (lines 1–8)

**Current file:**
```python
"""Single source of truth for the EleitorUM version string."""

__version__ = "0.1.0"
```

**Required change:** One line only — `"0.1.0"` → `"1.0.0"`. The module docstring structure, file location, and import path are all correct as-is.

**Version propagation chain** (do not hardcode `"1.0.0"` anywhere else):
- `app.py` line 51: `app.setApplicationVersion(__version__)` — reads automatically
- `dialogs.py` line 42: `from eleitorum.version import __version__` — reads automatically
- `__main__.py`: imports in `_check_version_flag()` — reads automatically
- `scripts/build.py`: reads via `sys.path.insert` + `from eleitorum.version import __version__`
- `pyproject.toml` `version =` field: must be manually kept in sync (no dynamic version plugin in current setup)

---

### `src/eleitorum/ui/strings.py` — UMinho removal

**Analog:** `src/eleitorum/ui/strings.py` (full file — already read)

**Exact locations to modify** (from RESEARCH.md Pitfall 6):

Line 166–168 — `ABOUT_DESCRIPTION` — remove institution reference:
```python
# BEFORE:
ABOUT_DESCRIPTION: str = (
    "Utilitário para normalização de ficheiros eleitorais da Universidade do Minho."
)

# AFTER:
ABOUT_DESCRIPTION: str = (
    "Utilitário para normalização de ficheiros eleitorais."
)
```

Lines 172–178 — `UMINHO_DISCLAIMER` — remove entirely (including comment above it):
```python
# DELETE these lines:
# Verbatim from Eleitorum.md §3.5 — do not paraphrase.
UMINHO_DISCLAIMER: str = (
    "O EleitorUM é uma ferramenta independente de código aberto. Não é oficialmente "
    "afiliada nem endossada pela Universidade do Minho. ..."
)
```

Lines 185–193 — `WELCOME_BODY` — remove institution reference:
```python
# BEFORE (line 188):
"eleitorais para o formato exigido pela plataforma da Universidade do Minho.\n\n"

# AFTER:
"eleitorais para o formato exigido pela plataforma eleitoral.\n\n"
```

**Preserve all other constants unchanged** — the existing sectioned structure with `# ---` dividers and the `# Usage: ...` annotation convention must be maintained.

---

### `src/eleitorum/ui/dialogs.py` — UMinho removal

**Analog:** `src/eleitorum/ui/dialogs.py` (full file — already read)

**Exact locations to modify:**

Lines 36–40 — import block, remove `UMINHO_DISCLAIMER`:
```python
# BEFORE:
from eleitorum.ui.strings import (
    ABOUT_DESCRIPTION,
    ABOUT_LICENSE,
    ABOUT_REPO_LINK_LABEL,
    BTN_COMECAR,
    UMINHO_DISCLAIMER,
    WELCOME_BODY,
    WELCOME_HEADING,
)

# AFTER (remove UMINHO_DISCLAIMER line):
from eleitorum.ui.strings import (
    ABOUT_DESCRIPTION,
    ABOUT_LICENSE,
    ABOUT_REPO_LINK_LABEL,
    BTN_COMECAR,
    WELCOME_BODY,
    WELCOME_HEADING,
)
```

Lines 122–125 — remove disclaimer widget block entirely from `AboutDialog._setup_ui()`:
```python
# DELETE these lines:
# UMinho disclaimer — verbatim from Eleitorum.md §3.5
disclaimer = QLabel(UMINHO_DISCLAIMER)
disclaimer.setWordWrap(True)
disclaimer.setObjectName("mutedText")
layout.addWidget(disclaimer)
```

**Update module docstring** (lines 10–11) — remove "UMinho disclaimer" from the AboutDialog description bullet. Replace with: "MIT license note, and repository link".

**All other dialog code stays unchanged** — the `WelcomeDialog` constructor, layout margins/spacing pattern (`setContentsMargins(24, 24, 24, 24)`, `setSpacing(16)`), `QPushButton` primary/secondary pattern, `QLabel.setOpenExternalLinks(True)` pattern for the repo link, and `layout.addStretch()` before the close button are all preserved.

---

### `pyproject.toml` — version bump + description + dev deps

**Analog:** `pyproject.toml` (full file — already read)

**Changes required:**

Line 7 — version bump:
```toml
# BEFORE:
version = "0.1.0"
# AFTER:
version = "1.0.0"
```

Line 8 — description (remove UMinho reference per D-01):
```toml
# BEFORE:
description = "Windows desktop utility to normalize electoral roll and eligibility list files for Universidade do Minho"
# AFTER:
description = "Windows desktop utility to normalize electoral roll and eligibility list files"
```

Lines 22–28 — add build and icon-generation tools to `[project.optional-dependencies] dev`:
```toml
dev = [
    "pytest==9.0.3",
    "pytest-cov==7.1.0",
    "mypy==2.1.0",
    "ruff==0.15.14",
    "pytest-qt==4.5.0",
    "pyinstaller==6.20.0",
    "svglib==1.6.0",
    "reportlab==4.4.10",
    "Pillow==12.1.1",
    "pip-audit==2.10.0",
]
```

**Preserve unchanged:** all `[tool.ruff]`, `[tool.mypy]`, `[tool.pytest.ini_options]`, `[tool.coverage.*]` sections — do not reformat or reorder.

---

### `scripts/build.py` — PyInstaller wrapper

**No direct analog exists** in the codebase. Use RESEARCH.md Pattern 2 + Pattern 3 as the authoritative source.

**File header pattern** — copy from `src/eleitorum/core/pipeline.py` module docstring style:
```python
"""PyInstaller build wrapper for EleitorUM.

Reads the canonical version from eleitorum.version.__version__,
generates a Windows PE version resource file (version_info.py),
then invokes PyInstaller to produce a one-folder Windows build.

Usage:
    python scripts/build.py            # --onedir (default)
    python scripts/build.py --onefile  # manual opt-in; slower cold start, AV-scan on launch

Output: dist/EleitorUM/EleitorUM.exe  (one-folder)
"""
```

**Version discovery pattern** (read dynamically — never hardcode):
```python
import os
import sys

# Add src/ to path so eleitorum.version can be imported without installation
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from eleitorum.version import __version__
```

**version_info.py generation** (from RESEARCH.md Pattern 3):
```python
def _generate_version_info(version: str) -> None:
    """Write version_info.py for PyInstaller --version-file."""
    parts = tuple(int(x) for x in version.split(".")) + (0,) * 4
    major, minor, patch, build = parts[:4]
    content = f"""# Auto-generated by scripts/build.py — do not edit.
VSVersionInfo(
  ffi=FixedFileInfo(
    filevers=({major}, {minor}, {patch}, {build}),
    prodvers=({major}, {minor}, {patch}, {build}),
    mask=0x3f, flags=0x0, OS=0x40004, fileType=0x1, subtype=0x0, date=(0, 0)
  ),
  kids=[
    StringFileInfo([
      StringTable('040904B0', [
        StringStruct('CompanyName', ''),
        StringStruct('FileDescription', 'EleitorUM — Normalizador de ficheiros eleitorais'),
        StringStruct('FileVersion', '{version}.0'),
        StringStruct('InternalName', 'EleitorUM'),
        StringStruct('LegalCopyright', 'MIT License'),
        StringStruct('OriginalFilename', 'EleitorUM.exe'),
        StringStruct('ProductName', 'EleitorUM'),
        StringStruct('ProductVersion', '{version}.0'),
      ])
    ]),
    VarFileInfo([VarStruct('Translation', [1033, 1200])])
  ]
)
"""
    with open("version_info.py", "w", encoding="utf-8") as f:
        f.write(content)
```

**PyInstaller invocation pattern** (from RESEARCH.md Pattern 2):
```python
import PyInstaller.__main__ as pyi

ARGS = [
    "src/eleitorum/__main__.py",
    "--name=EleitorUM",
    "--windowed",
    "--onedir",   # default per D-07; --onefile passed as flag overrides this
    "--icon=src/eleitorum/resources/icons/EleitorUM.ico",
    "--version-file=version_info.py",
    # Inter font dir — explicit datas; Qt plugins are auto-collected by hooks
    "--add-data=src/eleitorum/resources/fonts/Inter:resources/fonts/Inter",
    "--clean",
    "--noconfirm",
]

pyi.run(ARGS)
```

**ZIP creation pattern** (from RESEARCH.md Pattern 7):
```python
import zipfile
import pathlib

def _create_zip(version: str) -> pathlib.Path:
    zip_name = f"EleitorUM-{version}-win64.zip"
    with zipfile.ZipFile(zip_name, "w", zipfile.ZIP_DEFLATED) as z:
        for f in pathlib.Path("dist/EleitorUM").rglob("*"):
            z.write(f, f.relative_to("dist"))
    return pathlib.Path(zip_name)
```

**SHA-256 pattern** (from RESEARCH.md Pattern 5):
```python
import hashlib

def _write_sha256(zip_path: pathlib.Path) -> None:
    digest = hashlib.sha256(zip_path.read_bytes()).hexdigest()
    sha_path = zip_path.with_suffix(".zip.sha256")
    sha_path.write_text(f"{digest}  {zip_path.name}\n", encoding="utf-8")
```

---

### `scripts/generate_icons.py` — SVG to PNG/ICO

**No analog exists** in the codebase. Use RESEARCH.md Pattern 4 verbatim — it was verified locally against `src/eleitorum/resources/icon.svg`.

**Imports and constants:**
```python
from svglib.svglib import svg2rlg
from reportlab.graphics import renderPM
from PIL import Image
import io
import os
import pathlib

SVG_PATH = pathlib.Path("src/eleitorum/resources/icon.svg")
OUT_DIR = pathlib.Path("src/eleitorum/resources/icons")
SIZES = [16, 32, 48, 64, 128, 256, 512]
```

**Module docstring style** — copy pattern from `src/eleitorum/core/output.py` (single-purpose utility, brief description, no class needed).

---

### `.github/workflows/ci.yml` — push-to-main CI

**No analog exists** in the codebase (`.github/workflows/` directory does not yet exist).

**Use RESEARCH.md Pattern 6 verbatim.** Key elements the planner must enforce:
- `on: push: branches: [main]` + `on: pull_request: branches: [main]`
- Matrix strategy: `python-version: ["3.11", "3.12"]`
- `runs-on: windows-latest` for both `test` and `audit` jobs
- `env: QT_QPA_PLATFORM: offscreen` on the pytest step only
- `pip install -e ".[dev]"` — matches existing `pyproject.toml` extras key
- Steps order: checkout → setup-python → install → ruff check → ruff format --check → mypy → pytest
- Separate `audit` job using `pypa/gh-action-pip-audit@v1.1.0` with `inputs: .`

**ruff and mypy command pattern** — matches `README.md` development commands (lines 94–98):
```bash
ruff check src/ tests/
ruff format --check src/ tests/
mypy src/
```

---

### `.github/workflows/release.yml` — v1.0.0 tag release

**No analog exists** in the codebase.

**Use RESEARCH.md Pattern 7 verbatim.** Key elements:
- `on: push: tags: ["v*.*.*"]`
- `runs-on: windows-latest` (single job, no matrix)
- PowerShell smoke test step (Pattern 7 lines 555–559):
  ```yaml
  - name: Smoke test — --version
    run: |
      $output = & dist\EleitorUM\EleitorUM.exe --version
      if ($LASTEXITCODE -ne 0) { exit 1 }
      if ($output -notmatch "EleitorUM 1\.0\.0") { Write-Error "Version mismatch: $output"; exit 1 }
  ```
- `softprops/action-gh-release@v2` with `files:` block for ZIP + SHA-256
- `GITHUB_TOKEN` is injected automatically — no `permissions:` block needed for public repos

---

### `tests/unit/test_no_uminho_strings.py` — UMinho grep assertion

**Analog:** `tests/unit/ui/test_strings.py` (AST inspection + path-based grep pattern)

**File header pattern** (copy from `tests/unit/ui/test_strings.py` lines 1–11):
```python
"""Regression test: no 'Universidade' or 'UMinho' strings remain in source files (D-01).

Scans src/, README.md, and pyproject.toml for any occurrence of the institution
name. Fails the test if any match is found post-cleanup.
"""
from __future__ import annotations

import pathlib
import re
```

**Core test pattern** — file-content grep, not AST, matching the style of `test_strings.py`'s `_parse_strings_module()` function:
```python
SCAN_PATHS = [
    pathlib.Path("src"),
    pathlib.Path("README.md"),
    pathlib.Path("pyproject.toml"),
]

PATTERN = re.compile(r"Universidade|UMinho")


class TestNoUminhoStrings:
    def test_no_uminho_references_in_source(self) -> None:
        """No file in src/, README.md, or pyproject.toml may contain institution names."""
        violations: list[str] = []
        for root in SCAN_PATHS:
            files = [root] if root.is_file() else root.rglob("*.py")
            for path in files:
                text = path.read_text(encoding="utf-8", errors="replace")
                for lineno, line in enumerate(text.splitlines(), 1):
                    if PATTERN.search(line):
                        violations.append(f"{path}:{lineno}: {line.strip()}")
        assert not violations, (
            "Institution references found — remove per D-01:\n" + "\n".join(violations)
        )
```

**pytest import convention** — matches all existing test files: `from __future__ import annotations` at top, classes as `Test*`, methods as `test_*`.

---

### `README.md` — add EN paragraph, remove UMinho references

**Analog:** `README.md` (current file — already read)

**Change 1 — prepend English paragraph before line 1** (D-03):
```markdown
**EleitorUM** is a Windows desktop utility that normalises electoral roll and eligibility
list files. It accepts Excel and text formats (XLSX, XLS, ODS, CSV, TSV), validates and
transforms the data according to strict rules, and produces a byte-exact CSV output —
with no manual fixing required.

---
```

**Change 2 — update badge on line 8** — "Em Desenvolvimento" → "v1.0.0":
```markdown
[![Estado: v1.0.0](https://img.shields.io/badge/estado-v1.0.0-brightgreen)]()
```

**Change 3 — update Phase 4 row in the status table** (lines 53–54):
```markdown
| 4 — Build e Distribuição | PyInstaller `.exe`, CI/CD, v1.0.0 | ✅ Concluída |
```

**No UMinho references exist in the current README body** (confirmed by grep — the institution name does not appear in `README.md`). Only the badge and status table rows need updating.

---

### `SPECIFICATION.md` — verbatim copy

**Source:** `.planning/Eleitorum.md` — copy verbatim per D-04.

**One exception:** D-04 notes "Do NOT copy UMinho disclaimer from Section 3.5." Open `.planning/Eleitorum.md`, locate Section 3.5, and omit that specific block. All other sections copy unchanged — the "audience: AI development agents and human contributors" preamble in Section 0 is fine to retain.

---

## Shared Patterns

### Module docstring style
**Source:** Every file in `src/eleitorum/` — consistent pattern throughout
**Apply to:** `scripts/build.py`, `scripts/generate_icons.py`, `tests/unit/test_no_uminho_strings.py`

```python
"""One-line summary ending with period.

Optional longer description. References requirement IDs where applicable.

Usage:
    python scripts/build.py            # inline if a script
"""
```

### `from __future__ import annotations`
**Source:** `src/eleitorum/__main__.py` (after modification), `src/eleitorum/ui/dialogs.py` line 20, `src/eleitorum/ui/strings.py` line 10, all test files
**Apply to:** All new `.py` files — this is a project-wide convention

### Import ordering (ruff I rules)
**Source:** All existing `.py` files — stdlib before third-party before local
**Apply to:** All new `.py` files
```python
# stdlib
import os
import pathlib
import sys

# third-party
from PySide6.QtWidgets import QDialog

# local
from eleitorum.config import APP_NAME
from eleitorum.version import __version__
```

### Test class/method naming
**Source:** `tests/unit/ui/test_dialogs.py` (lines 25–141), `tests/unit/ui/test_strings.py` (lines 137–206)
**Apply to:** `tests/unit/test_no_uminho_strings.py`
```python
class TestFoo:
    def test_specific_behaviour(self, ...) -> None:
        """Docstring: what must be true."""
        ...
```

### Version single source of truth
**Source:** `src/eleitorum/version.py`, referenced from `app.py` line 51, `dialogs.py` line 42
**Apply to:** `scripts/build.py`, `__main__.py --version` output
```python
# In any script needing the version:
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from eleitorum.version import __version__
# Never: VERSION = "1.0.0"
```

### Font loading path (PyInstaller-aware)
**Source:** `src/eleitorum/ui/app.py` lines 97–98
**Apply to:** `scripts/build.py` `--add-data` argument — the destination path in the spec must match what app.py expects at `_MEIPASS`
```python
# app.py resolves:
base = pathlib.Path(getattr(sys, "_MEIPASS", str(pathlib.Path(__file__).parent.parent)))
fonts_dir = base / "resources" / "fonts" / "Inter"
# Therefore --add-data must be:
"--add-data=src/eleitorum/resources/fonts/Inter:resources/fonts/Inter"
```

---

## No Analog Found

Files with no close match in the codebase (planner references RESEARCH.md patterns instead):

| File | Role | Data Flow | Reason |
|------|------|-----------|--------|
| `scripts/generate_icons.py` | utility | transform | No image processing scripts exist; use RESEARCH.md Pattern 4 verbatim |
| `.github/workflows/ci.yml` | CI config | event-driven | No workflows exist; use RESEARCH.md Pattern 6 verbatim |
| `.github/workflows/release.yml` | CI config | event-driven | No workflows exist; use RESEARCH.md Pattern 7 verbatim |
| `CHANGELOG.md` | documentation | — | No changelog exists; use Keep-a-Changelog 1.0.0 format from D-05 |
| `CONTRIBUTING.md` | documentation | — | No contributing guide exists; content specified in Claude's Discretion |
| `RENAMING.md` | documentation | — | No rename guide exists; content fully specified in Claude's Discretion |
| `.gitignore` | config | — | Not yet committed; content fully specified in Claude's Discretion |
| `.gitattributes` | config | — | Not yet committed; content fully specified in Claude's Discretion |

---

## Metadata

**Analog search scope:** `src/eleitorum/`, `tests/`, `pyproject.toml`, `README.md`, `LICENSE`
**Files scanned:** 38 Python source files + 3 config/documentation files
**Pattern extraction date:** 2026-05-24
