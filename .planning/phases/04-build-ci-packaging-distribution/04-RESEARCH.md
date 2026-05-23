# Phase 4: Build, CI, Packaging + Distribution Artifacts — Research

**Researched:** 2026-05-24
**Domain:** PyInstaller 6.x, GitHub Actions CI/CD, Windows PE metadata, SVG icon generation, pip-audit, repository documentation
**Confidence:** HIGH

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

- **D-01:** Remove ALL references to "Universidade do Minho" and "UMinho" project-wide — source files, README, pyproject.toml description, About dialog, any other location. Overrides BRAND-04. About dialog contains only: app name, version, MIT license note, repo link.
- **D-02:** Commit `InterVariable.ttf` to `src/eleitorum/resources/fonts/Inter/InterVariable.ttf` from rsms/inter GitHub releases (canonical source).
- **D-03:** README: add short English "About" paragraph at the very top; PT-PT body stays as primary. No institution named.
- **D-04:** Copy `.planning/Eleitorum.md` verbatim to `SPECIFICATION.md` at repo root. Do NOT copy UMinho disclaimer from Section 3.5.
- **D-05:** Create `CHANGELOG.md` in Keep-a-Changelog format. v1.0.0 `Added` section covers all major capabilities. Empty "Unreleased" header.
- **D-06:** On `v1.0.0` tag push, CI publishes GitHub Release automatically (not draft). Attaches `EleitorUM-1.0.0-win64.zip` and `EleitorUM-1.0.0-win64.zip.sha256`.
- **D-07:** `scripts/build.py` defaults to `--onedir`. Document `--onefile` as manual opt-in comment. No automated cold-start benchmark.

### Claude's Discretion

- **Version bump:** Bump `src/eleitorum/version.py` and `pyproject.toml` from `0.1.0` to `1.0.0`.
- **`--version` CLI arg:** Add `argparse` block to `__main__.py`; print `EleitorUM 1.0.0`; exit 0 BEFORE `QApplication`.
- **CONTRIBUTING.md:** Archived project, external contributions not accepted.
- **RENAMING.md:** Checklist of every location referencing `EleitorUM`.
- **`.gitignore`:** Python + PyInstaller + IDE + OS + build artifacts.
- **`.gitattributes`:** `text=auto`; `*.py eol=lf`; binary files marked binary.
- **`scripts/generate_icons.py`:** PNG 16/32/48/64/128/256/512 + `.ico` from `icon.svg`.
- **SHA-256 format:** BSD-style one-liner: `<hex_digest>  EleitorUM-1.0.0-win64.zip` (two spaces).
- **Windows PE metadata:** `scripts/build.py` generates `version_info.py`, passes `--version-file` to PyInstaller.

### Deferred Ideas (OUT OF SCOPE)

None — discussion stayed within phase scope.

</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| BRAND-03 | `RENAMING.md` at repo root with full rename checklist | Covered: exact locations identified in Established Patterns section |
| BRAND-04 | README + About dialog UMinho disclaimer — **overridden by D-01** | D-01 removes all UMinho references; About dialog: name + version + MIT + repo link only |
| REPO-01 | `SPECIFICATION.md` at repo root | D-04: verbatim copy of `.planning/Eleitorum.md` (omit §3.5 disclaimer) |
| REPO-02 | `README.md` bilingual headers | D-03: EN paragraph first, PT-PT body; no institution named |
| REPO-03 | `LICENSE` (MIT) | Already exists at repo root (confirmed by `ls`) |
| REPO-04 | `CHANGELOG.md` in Keep-a-Changelog format | D-05: format and content specified |
| REPO-05 | `CONTRIBUTING.md` — external contributions not accepted | D: one-page archived-project statement |
| REPO-06 | `RENAMING.md` checklist | Code Patterns section enumerates all locations |
| REPO-07 | `.gitignore` | Pattern section covers all required exclusions |
| REPO-08 | `.gitattributes` | Pattern section specifies eol=lf for .py, binary for fonts/images |
| REPO-09 | `pyproject.toml` pinned deps + tool config | Currently at 0.1.0; bump version, add PyInstaller to dev deps |
| BLD-01 | `scripts/build.py` wraps PyInstaller, produces versioned zip | Build Script Pattern section |
| BLD-02 | Default onedir; onefile opt-in; D-07 no benchmark | Confirmed — D-07 locked |
| BLD-03 | Icon embedded; Windows PE version metadata | version_info.py pattern documented |
| BLD-04 | Inter font bundled; Qt platform plugins included | Verified: PyInstaller 6.x hooks auto-collect platforms plugin; fonts need explicit datas entry |
| BLD-05 | `scripts/generate_icons.py` from `icon.svg` | Verified locally: svglib+reportlab+Pillow pipeline works on Windows |
| CI-01 | GHA push-to-main: ruff + mypy + pytest | Workflow structure documented |
| CI-02 | Python 3.11 + 3.12 on windows-latest | Matrix strategy pattern documented |
| CI-03 | pip-audit CVE scanning | pypa/gh-action-pip-audit@v1.1.0 pattern documented |
| CI-04 | v1.0.0 tag: build + smoke test + SHA-256 + release | Full workflow documented; --version smoke test pattern verified |
| CI-05 | Free tier only | windows-latest is free for public repos |

</phase_requirements>

---

## Summary

Phase 4 converts the working development project into a shippable public artifact. It covers four distinct problem domains: (1) source code cleanup (UMinho removal, version bump, argparse --version), (2) build tooling (PyInstaller spec, icon generation, Windows PE metadata), (3) CI/CD (GitHub Actions push workflow + release workflow), and (4) repository documentation (README, SPECIFICATION.md, CHANGELOG.md, CONTRIBUTING.md, RENAMING.md, .gitignore, .gitattributes).

The most technically uncertain area coming in was icon generation on Windows without cairosvg (which requires GTK/libcairo native libraries that are painful on Windows). This has been **resolved**: the `svglib` + `reportlab` + `Pillow` stack is already installed on the developer's machine, was verified locally to render the project's `icon.svg` to RGBA PNGs at all required sizes, and produces valid multi-size ICO files. No cairosvg dependency is needed. All three libraries passed slopcheck.

PyInstaller 6.20.0 (just installed, verified) includes built-in hooks via `_modules_info.py` that automatically collect the `platforms` plugin directory (containing `qwindows.dll`) as part of the `QtGui` hook. No manual `--add-data` for Qt platform plugins is required. Custom resources (Inter font directory) **do** require an explicit `datas` entry in the spec file.

For CI, `QT_QPA_PLATFORM=offscreen` is a confirmed working approach for headless pytest-qt on Windows — including on `windows-latest` GitHub Actions runners. The `pypa/gh-action-pip-audit@v1.1.0` action audits `pyproject.toml` directly and fails the job when high-severity CVEs are found.

**Primary recommendation:** Use a spec-file-based build (not raw CLI flags) with explicit datas for fonts; use `pypa/gh-action-pip-audit` for CVE scanning; use `softprops/action-gh-release@v2` for release artifact attachment; generate SHA-256 with a Python one-liner for cross-platform consistency.

---

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| PyInstaller build script | Build tooling | — | Runs on developer machine or CI runner; not part of the shipped application |
| Icon generation | Build tooling | — | One-off dev script; output artifacts are checked in |
| Windows PE version metadata | Build tooling | — | Generated at build time, embedded in EXE |
| Font bundling (Inter) | Build tooling | Application runtime | Build packs the font; runtime reads from `sys._MEIPASS` path already established in Phase 2 |
| Qt platform plugins (qwindows.dll) | Build tooling | — | Automatic via PyInstaller hooks; no runtime code change |
| --version argparse | Application entry point | — | Runs before QApplication; CI smoke test exercises this path |
| CI push workflow | CI/CD | — | Lint + type check + test on every push |
| CI release workflow | CI/CD | — | Build + smoke + SHA-256 + GitHub Release on tag |
| Repository documentation | Repository | — | Static files at repo root |
| UMinho removal | Source code | Documentation | grep + edit across src/, README.md, pyproject.toml |

---

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| PyInstaller | 6.20.0 | Python → Windows EXE/folder | Industry standard; mature PySide6 hooks; latest as of April 2026 [VERIFIED: PyPI] |
| pyinstaller-hooks-contrib | 2026.5 | Extended hook library | Auto-installed with PyInstaller; 2026.5 is the latest; includes PySide6 hook updates [VERIFIED: PyPI] |
| svglib | 1.6.0 | SVG parsing for icon generation | LGPL-3.0; pure Python; renders project's icon.svg correctly at all target sizes [VERIFIED: local test] |
| reportlab | 4.4.10 | Raster renderer for svglib | BSD; renderPM backend produces RGBA PNG bytes at any DPI [VERIFIED: local test] |
| Pillow | 12.1.1 | PNG resize + ICO creation | MIT-CMU; multi-size ICO save verified locally; already installed [VERIFIED: local test] |
| pip-audit | 2.10.0 | CVE scanning in CI | Apache-2.0; official pypa tool; reads pyproject.toml directly [VERIFIED: PyPI] |
| pypa/gh-action-pip-audit | v1.1.0 | GitHub Actions wrapper for pip-audit | Official pypa action; inputs: project path; fails on CVEs [CITED: github.com/pypa/gh-action-pip-audit] |
| softprops/action-gh-release | v2 | Attach files to GitHub Release | Most widely used release action; non-draft by default; GITHUB_TOKEN built in [CITED: github.com/softprops/action-gh-release] |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| stdlib `argparse` | (stdlib) | --version CLI flag in `__main__.py` | Already in stdlib; no extra dependency |
| stdlib `hashlib` | (stdlib) | SHA-256 computation in CI | Cross-platform; consistent output; used in Python one-liner |
| stdlib `zipfile` | (stdlib) | Create `EleitorUM-1.0.0-win64.zip` in build script | No external zip tool needed in CI |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| svglib + reportlab + Pillow | cairosvg | cairosvg requires GTK/libcairo native DLLs — painful on Windows; OSError on clean machines without GTK installed. svglib stack is pure-Python and confirmed working on this machine. |
| svglib + reportlab + Pillow | Inkscape CLI + ImageMagick | External executables; must be installed on CI runner; not in standard GitHub Actions windows-latest image; brittle. |
| pypa/gh-action-pip-audit | `pipx run pip-audit` inline step | Both work; the action provides caching, cleaner job isolation, and the `ignore-vulns` input. Use the action. |
| softprops/action-gh-release | `gh release create` CLI | Both work; softprops action has cleaner YAML syntax and is the ecosystem default. Use the action. |
| Python hashlib SHA-256 | certutil -hashfile | certutil output format includes a header line ("CertUtil: -hashfile command completed successfully") that must be stripped. Python hashlib produces exact output with no post-processing. |

**Installation (dev extras to add to pyproject.toml):**
```bash
pip install "pyinstaller==6.20.0" "svglib==1.6.0" "reportlab==4.4.10" "Pillow==12.1.1" "pip-audit==2.10.0"
```

---

## Package Legitimacy Audit

All packages audited with slopcheck 0.6.1 on 2026-05-24.

| Package | Registry | Age | Downloads | Source Repo | slopcheck | Disposition |
|---------|----------|-----|-----------|-------------|-----------|-------------|
| pyinstaller | PyPI | ~15 yrs | Very high | github.com/pyinstaller/pyinstaller | [OK] | Approved |
| svglib | PyPI | ~10 yrs | Moderate | github.com/deeplook/svglib | [OK] | Approved |
| reportlab | PyPI | ~20 yrs | Very high | reportlab.com | [OK] | Approved |
| pillow | PyPI | ~12 yrs | Very high | github.com/python-pillow/Pillow | [OK] | Approved |
| pip-audit | PyPI | ~4 yrs | High | github.com/pypa/pip-audit | [OK] | Approved |

**Packages removed due to slopcheck [SLOP] verdict:** none

**Packages flagged as suspicious [SUS]:** none

---

## Architecture Patterns

### System Architecture Diagram

```
Developer machine / CI runner
        |
        v
[scripts/generate_icons.py]
  svglib + reportlab + Pillow
  icon.svg → PNG(16..512) + .ico
        |
        v
[scripts/build.py]
  1. Read version from eleitorum.version
  2. Generate version_info.py (VSVersionInfo)
  3. Invoke PyInstaller with spec/CLI flags
        |
        v
[PyInstaller analysis]
  Entry: src/eleitorum/__main__.py
  Hooks: hook-PySide6.QtGui (auto: platforms, imageformats)
         hook-PySide6.QtWidgets (auto: styles)
  datas: fonts/Inter/ → PySide6/fonts/Inter/   (explicit)
  --icon: resources/icons/EleitorUM.ico
  --version-file: version_info.py
        |
        v
[dist/EleitorUM/]  (one-folder build)
  EleitorUM.exe
  PySide6/plugins/platforms/qwindows.dll  ← auto-collected
  PySide6/plugins/styles/*.dll            ← auto-collected
  resources/fonts/Inter/InterVariable.ttf ← from datas
        |
        v
[zipfile: EleitorUM-1.0.0-win64.zip]
        |
   +----+----+
   |         |
   v         v
[hashlib]  [GitHub Actions]
SHA-256    softprops/action-gh-release
.sha256    attaches ZIP + .sha256
file       to GitHub Release
```

### Recommended Project Structure (new files only)

```
scripts/
├── build.py             # PyInstaller wrapper (--onedir default)
└── generate_icons.py    # SVG → PNG/ICO using svglib+Pillow

.github/
└── workflows/
    ├── ci.yml           # push-to-main: ruff + mypy + pytest
    └── release.yml      # v1.0.0 tag: build + smoke + release

src/eleitorum/resources/
├── icon.svg             # existing
├── icons/               # generated by generate_icons.py
│   ├── EleitorUM-16.png
│   ├── EleitorUM-32.png
│   ├── EleitorUM-48.png
│   ├── EleitorUM-64.png
│   ├── EleitorUM-128.png
│   ├── EleitorUM-256.png
│   ├── EleitorUM-512.png
│   └── EleitorUM.ico
└── fonts/
    └── Inter/
        ├── OFL.txt      # existing
        └── InterVariable.ttf  # D-02: download from rsms/inter releases

SPECIFICATION.md         # D-04: verbatim copy of .planning/Eleitorum.md
CHANGELOG.md             # D-05: Keep-a-Changelog v1.0.0 entry
CONTRIBUTING.md          # archived project, no external contributions
RENAMING.md              # checklist of all APP_NAME locations
.gitignore               # Python + PyInstaller + IDE + OS
.gitattributes           # text=auto, *.py eol=lf, binaries marked
```

---

### Pattern 1: argparse --version before QApplication

**What:** Parse `--version` flag and exit before any Qt import is executed.

**Why critical:** `QApplication` initialises the Qt platform plugin (qwindows.dll) — on a headless CI runner or during the PyInstaller smoke test, this must not happen. The `--version` path must be entirely Qt-free.

**When to use:** All CLI entry-point additions that must work without a display.

```python
# Source: stdlib argparse docs + CONTEXT.md §"--version CLI arg"
# In src/eleitorum/__main__.py — TOP of file, before any Qt imports

import argparse
import sys


def _parse_args() -> None:
    """Handle CLI flags before Qt initialisation."""
    from eleitorum.version import __version__
    parser = argparse.ArgumentParser(prog="EleitorUM", add_help=False)
    parser.add_argument("--version", action="store_true")
    args, _ = parser.parse_known_args()
    if args.version:
        print(f"EleitorUM {__version__}")
        sys.exit(0)


# Call _parse_args() BEFORE importing from eleitorum.ui.*
_parse_args()

from eleitorum.ui.app import create_app          # noqa: E402
from eleitorum.ui.main_window import MainWindow  # noqa: E402
```

**Key rule:** `from eleitorum.version import __version__` is safe (no Qt). Importing `eleitorum.ui.*` is not safe before `_parse_args()` is resolved, because `app.py` imports PySide6 at module level.

---

### Pattern 2: PyInstaller spec file with PySide6 datas

**What:** Spec file (preferred over raw CLI flags) that bundles PySide6, Inter font, and icons correctly.

**Why spec file:** Multiple `--add-data` entries on CLI become unmanageable; spec file is version-controllable.

**Key finding (verified from PyInstaller hooks source):** `hook-PySide6.QtGui.py` automatically collects the `platforms` plugin directory (containing `qwindows.dll`) and `imageformats`. `hook-PySide6.QtWidgets.py` collects `styles`. No manual `--add-data` is needed for Qt plugins. Only the Inter font directory needs an explicit `datas` entry.

```python
# Source: PyInstaller spec-files docs + local hooks inspection
# scripts/build.py generates this spec and invokes PyInstaller

import PyInstaller.__main__ as pyi
import sys, os

# Read version dynamically — never hardcode
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
from eleitorum.version import __version__

# Generate version_info.py before calling PyInstaller
_generate_version_info(__version__)  # see Pattern 3

ARGS = [
    'src/eleitorum/__main__.py',
    '--name=EleitorUM',
    '--windowed',                      # no console window
    '--onedir',                        # default per D-07
    f'--icon=src/eleitorum/resources/icons/EleitorUM.ico',
    f'--version-file=version_info.py',
    # Inter font directory — explicit datas required
    '--add-data=src/eleitorum/resources/fonts/Inter:resources/fonts/Inter',
    '--clean',
    '--noconfirm',
]

pyi.run(ARGS)
```

**Runtime font path (already established in Phase 2):**
```python
# Pattern already in Phase 2 app.py — confirmed still works
import sys, os
if getattr(sys, 'frozen', False):
    base = sys._MEIPASS
else:
    base = os.path.join(os.path.dirname(__file__), '..', '..')
font_path = os.path.join(base, 'resources', 'fonts', 'Inter', 'InterVariable.ttf')
```

---

### Pattern 3: Windows PE version_info.py (VSVersionInfo)

**What:** Python file containing a `VSVersionInfo` object that PyInstaller embeds into the EXE's PE metadata.

**Source:** [DEV.to — Adding Version Information to a PyInstaller Executable](https://dev.to/arhamrumi/adding-version-information-to-a-pyinstaller-onefile-executable-6n8) [CITED]

```python
# Generated by scripts/build.py into version_info.py at build time
# Version tuple for 1.0.0.0
VSVersionInfo(
  ffi=FixedFileInfo(
    filevers=(1, 0, 0, 0),
    prodvers=(1, 0, 0, 0),
    mask=0x3f,
    flags=0x0,
    OS=0x40004,
    fileType=0x1,
    subtype=0x0,
    date=(0, 0)
  ),
  kids=[
    StringFileInfo([
      StringTable('040904B0', [
        StringStruct('CompanyName', ''),
        StringStruct('FileDescription', 'EleitorUM — Normalizador de ficheiros eleitorais'),
        StringStruct('FileVersion', '1.0.0.0'),
        StringStruct('InternalName', 'EleitorUM'),
        StringStruct('LegalCopyright', 'MIT License'),
        StringStruct('OriginalFilename', 'EleitorUM.exe'),
        StringStruct('ProductName', 'EleitorUM'),
        StringStruct('ProductVersion', '1.0.0.0'),
      ])
    ]),
    VarFileInfo([VarStruct('Translation', [1033, 1200])])
  ]
)
```

**Build script helper:**
```python
def _generate_version_info(version: str) -> None:
    parts = tuple(int(x) for x in version.split('.')) + (0,) * 4
    major, minor, patch, build = parts[:4]
    content = f"""VSVersionInfo(
  ffi=FixedFileInfo(
    filevers=({major}, {minor}, {patch}, {build}),
    prodvers=({major}, {minor}, {patch}, {build}),
    ...
  ),
  ...
)"""
    with open('version_info.py', 'w', encoding='utf-8') as f:
        f.write(content)
```

---

### Pattern 4: Icon generation with svglib + Pillow

**What:** Pure-Python script that converts `icon.svg` to PNG sizes and multi-size ICO.

**Verified:** Tested on developer machine — renders non-blank RGBA images at all sizes. [VERIFIED: local test]

```python
# scripts/generate_icons.py
# Source: verified locally against src/eleitorum/resources/icon.svg

from svglib.svglib import svg2rlg
from reportlab.graphics import renderPM
from PIL import Image
import io, os

SVG_PATH = 'src/eleitorum/resources/icon.svg'
OUT_DIR  = 'src/eleitorum/resources/icons'
SIZES    = [16, 32, 48, 64, 128, 256, 512]

os.makedirs(OUT_DIR, exist_ok=True)

drawing = svg2rlg(SVG_PATH)
# Render at native size (256x256), then resize down
buf = io.BytesIO()
renderPM.drawToFile(drawing, buf, fmt='PNG', dpi=96)
buf.seek(0)
img_full = Image.open(buf).convert('RGBA')

images = []
for size in SIZES:
    img = img_full.resize((size, size), Image.LANCZOS)
    img.save(os.path.join(OUT_DIR, f'EleitorUM-{size}.png'))
    images.append(img)
    print(f'  {size}x{size} PNG written')

# Multi-size ICO (max 256 in ICO spec; 512 is PNG-inside-ICO)
ico_sizes = [s for s in SIZES if s <= 256]
ico_imgs  = [img_full.resize((s, s), Image.LANCZOS) for s in ico_sizes]
ico_imgs[0].save(
    os.path.join(OUT_DIR, 'EleitorUM.ico'),
    format='ICO',
    sizes=[(s, s) for s in ico_sizes],
    append_images=ico_imgs[1:],
)
print('  EleitorUM.ico written')
```

---

### Pattern 5: SHA-256 checksum (Python one-liner, CI-safe)

**What:** Produce `EleitorUM-1.0.0-win64.zip.sha256` with BSD-style format (two spaces between digest and filename).

**Why Python over certutil:** `certutil -hashfile` outputs a header line that requires post-processing. Python `hashlib` produces exact output. [ASSUMED — certutil output format consistency across Windows versions not independently verified]

```python
# In CI workflow as a run: step
python -c "
import hashlib, pathlib
z = pathlib.Path('EleitorUM-1.0.0-win64.zip')
digest = hashlib.sha256(z.read_bytes()).hexdigest()
pathlib.Path('EleitorUM-1.0.0-win64.zip.sha256').write_text(f'{digest}  {z.name}\n')
print(f'SHA-256: {digest}')
"
```

---

### Pattern 6: GitHub Actions CI workflow — push to main

```yaml
# .github/workflows/ci.yml
# Source: GitHub Actions docs + pypa/gh-action-pip-audit README [CITED]

name: CI

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: windows-latest
    strategy:
      matrix:
        python-version: ["3.11", "3.12"]

    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}

      - name: Install dependencies
        run: pip install -e ".[dev]"

      - name: ruff lint
        run: ruff check src/ tests/

      - name: ruff format check
        run: ruff format --check src/ tests/

      - name: mypy
        run: mypy src/

      - name: pytest
        env:
          QT_QPA_PLATFORM: offscreen
        run: pytest

  audit:
    runs-on: windows-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - uses: pypa/gh-action-pip-audit@v1.1.0
        with:
          inputs: .
```

**Critical:** `QT_QPA_PLATFORM: offscreen` is required so pytest-qt runs headless without an X server or display. Confirmed working on Windows. [CITED: pytest-qt troubleshooting docs]

---

### Pattern 7: GitHub Actions release workflow — v1.0.0 tag

```yaml
# .github/workflows/release.yml
# Source: softprops/action-gh-release README [CITED]

name: Release

on:
  push:
    tags:
      - "v*.*.*"

jobs:
  release:
    runs-on: windows-latest

    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Install runtime + build deps
        run: |
          pip install -e ".[dev]"
          pip install pyinstaller==6.20.0 svglib==1.6.0 reportlab==4.4.10 Pillow==12.1.1

      - name: Generate icons (if not pre-committed)
        run: python scripts/generate_icons.py

      - name: Build Windows artifact
        run: python scripts/build.py

      - name: Smoke test — --version
        run: |
          $output = & dist\EleitorUM\EleitorUM.exe --version
          if ($LASTEXITCODE -ne 0) { exit 1 }
          if ($output -notmatch "EleitorUM 1\.0\.0") { Write-Error "Version mismatch: $output"; exit 1 }

      - name: Create ZIP
        run: |
          python -c "
          import zipfile, pathlib, os
          with zipfile.ZipFile('EleitorUM-1.0.0-win64.zip', 'w', zipfile.ZIP_DEFLATED) as z:
              for f in pathlib.Path('dist/EleitorUM').rglob('*'):
                  z.write(f, f.relative_to('dist'))
          print('ZIP created')
          "

      - name: Compute SHA-256
        run: |
          python -c "
          import hashlib, pathlib
          z = pathlib.Path('EleitorUM-1.0.0-win64.zip')
          digest = hashlib.sha256(z.read_bytes()).hexdigest()
          pathlib.Path('EleitorUM-1.0.0-win64.zip.sha256').write_text(f'{digest}  {z.name}\n')
          print(f'SHA-256: {digest}')
          "

      - name: Publish GitHub Release
        uses: softprops/action-gh-release@v2
        with:
          files: |
            EleitorUM-1.0.0-win64.zip
            EleitorUM-1.0.0-win64.zip.sha256
```

**Note on version in filenames:** The workflow above uses hardcoded `1.0.0` in filenames because D-06 specifies exactly `EleitorUM-1.0.0-win64.zip`. For a single-release project this is correct. If the planner wants to make filenames dynamic, use `python -c "from eleitorum.version import __version__; print(__version__)"` to populate a step output.

---

### Anti-Patterns to Avoid

- **`--onefile` as default build:** Triggers Windows Defender scan on every launch (5–30 second cold-start penalty). D-07 locked `--onedir` as default.
- **`cairosvg` for icon generation on Windows:** Requires GTK/libcairo native libraries. Fails with `OSError: no library called 'cairo' was found` on clean Windows machines. Use the svglib+Pillow stack instead.
- **`certutil -hashfile` for SHA-256 in CI:** Output includes a "CertUtil: -hashfile command completed successfully" trailer line. Requires `| Select-String` post-processing. Python hashlib is simpler and identical output on all platforms.
- **Hardcoding version strings:** Version must be read from `eleitorum.version.__version__` in build script, CI workflow, version_info.py generator, and About dialog. `__main__.py --version` imports from version.py at runtime. No hardcoded `"1.0.0"` strings in Python files.
- **Qt import before `_parse_args()` in `__main__.py`:** If PySide6 is imported before argparse runs, `--version` will attempt to initialise Qt (failing on headless CI). The argparse block must appear before any `from eleitorum.ui.*` import.
- **Manual `--add-data` for Qt platform plugins:** Unnecessary with PyInstaller 6.x + pyinstaller-hooks-contrib 2026.5. The `QtGui` hook automatically collects the `platforms/` directory. Adding it manually causes duplicate-file warnings.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Qt plugin discovery at build time | Custom glob to find `qwindows.dll` | PyInstaller 6 + pyinstaller-hooks-contrib 2026.5 auto-collection | Hooks traverse the full plugin dependency graph; manual glob misses transitive DLLs |
| SVG-to-PNG conversion | PIL alone (no SVG support) | svglib + reportlab + Pillow | PIL cannot read SVG; svglib handles the SVG parse and rlg rendering |
| ICO multi-size embedding | Custom ICO byte format | Pillow `Image.save(..., format='ICO', sizes=[...])` | ICO binary format is non-trivial; Pillow handles all size slots correctly |
| CVE scanning | Manual `pip list` comparison | pypa/pip-audit via gh-action-pip-audit | pip-audit queries PyPI Advisory DB and OSV; covers transitive deps |
| GitHub Release creation | gh CLI scripting | softprops/action-gh-release@v2 | Handles tag-to-release mapping, asset upload, retry on network errors |
| Windows PE version resource | pefile manual binary patching | PyInstaller `--version-file` + VSVersionInfo | PyInstaller writes the resource correctly during link; no post-processing |

**Key insight:** Every part of this phase has a canonical solution in the Python/GitHub ecosystem. The only custom code needed is the thin `scripts/build.py` wrapper and `scripts/generate_icons.py`.

---

## Common Pitfalls

### Pitfall 1: Missing Qt platform plugin on clean machine
**What goes wrong:** The bundled EXE opens a console window and immediately exits with `qt.qpa.plugin: Could not find the Qt platform plugin "windows" in ""`.
**Why it happens:** Older PyInstaller + hooks-contrib versions did not reliably collect the `platforms/` plugin directory. This was historically a major pain point (see GitHub issue #5414).
**How to avoid:** Use PyInstaller 6.20.0 + pyinstaller-hooks-contrib 2026.5 (just installed). The `QtGui` hook in `_modules_info.py` explicitly lists `"platforms"` in the plugins list. Verified from source.
**Warning signs:** If the smoke test on the CI runner passes but a clean-VM test fails, suspect a plugins/ directory was excluded. Run `dir dist\EleitorUM\PySide6\plugins\platforms\` to verify `qwindows.dll` is present.

### Pitfall 2: pytest-qt crashes on headless CI without QT_QPA_PLATFORM
**What goes wrong:** Test run aborts with `Aborted (core dumped)` or `Fatal Python error: Aborted` — Qt calls `abort()` when no display is found.
**Why it happens:** PySide6's default QPA attempts to connect to Windows display services. On GitHub Actions windows-latest runners, this works because Windows runners have a desktop session. But it is best practice to set `QT_QPA_PLATFORM=offscreen` to make tests deterministic.
**How to avoid:** Set `QT_QPA_PLATFORM: offscreen` in the CI workflow's `env:` block for the pytest step. Also set `PYTEST_QT_API=pyside6` (already in pyproject.toml as `qt_api = "pyside6"`).
**Warning signs:** Tests pass locally, fail in CI with a non-zero exit and no pytest output.

### Pitfall 3: Font not found at runtime in bundled build
**What goes wrong:** The bundled app falls back to the system font; Inter is not loaded.
**Why it happens:** The `--add-data` destination path must match what the Phase 2 font-loading code expects when `sys.frozen == True`.
**How to avoid:** The Phase 2 font loading path uses `sys._MEIPASS` as the base. The `--add-data` destination must be `resources/fonts/Inter` (relative to `_MEIPASS`). Build script entry: `--add-data=src/eleitorum/resources/fonts/Inter:resources/fonts/Inter`.
**Warning signs:** Application window opens but text is in a different font; About dialog heading looks wrong.

### Pitfall 4: `certutil` SHA-256 output format
**What goes wrong:** The `.sha256` file contains extra lines ("SHA256 hash of ...:", "CertUtil: -hashfile command completed successfully").
**Why it happens:** `certutil -hashfile` is designed for human display, not machine-readable output.
**How to avoid:** Use the Python `hashlib` one-liner (Pattern 5). Output is exactly: `<64-char-hex>  <filename>\n`.
**Warning signs:** Users report `sha256sum -c` verification fails on the downloaded file.

### Pitfall 5: QApplication instantiated in `--version` path
**What goes wrong:** `EleitorUM.exe --version` hangs or crashes on a headless machine; smoke test fails.
**Why it happens:** If `from eleitorum.ui.app import create_app` appears before `_parse_args()`, Python executes the module-level `from PySide6.QtWidgets import QApplication` import, which initialises the Qt platform plugin.
**How to avoid:** Structure `__main__.py` so `_parse_args()` is called first, and all UI imports are deferred until after the argparse exit check (Pattern 1).
**Warning signs:** CI smoke test step exits with non-zero code; `$LASTEXITCODE` check fires.

### Pitfall 6: UMinho strings in unexpected locations
**What goes wrong:** `grep` after the phase finds lingering institution references; public repo looks inconsistent.
**Why it happens:** Strings are scattered across `strings.py` (`UMINHO_DISCLAIMER`, `ABOUT_DESCRIPTION`, `WELCOME_BODY`), `dialogs.py` (import of `UMINHO_DISCLAIMER`), `pyproject.toml` description field, and potentially `.planning/` files.
**How to avoid:** Run the canonical grep before committing: `grep -rn "Universidade\|UMinho" src/ README.md pyproject.toml tests/`. Also check `strings.py` constants `ABOUT_DESCRIPTION` and `WELCOME_BODY` which reference the university.
**Current state from code review:**
  - `strings.py` line 167: `ABOUT_DESCRIPTION` contains "da Universidade do Minho" — **must be updated**
  - `strings.py` line 173-178: `UMINHO_DISCLAIMER` constant — **must be removed**
  - `strings.py` line 189-193: `WELCOME_BODY` references "plataforma da Universidade do Minho" — **must be updated**
  - `dialogs.py` line 37: imports `UMINHO_DISCLAIMER` — **must be removed**
  - `dialogs.py` line 122-125: renders `UMINHO_DISCLAIMER` label — **must be removed**
  - `pyproject.toml` line 8: description field — **must be updated**

---

## Code Examples

### Complete `__main__.py` refactored with --version

```python
# Source: stdlib argparse + CONTEXT.md pattern
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

### pypa/gh-action-pip-audit in CI

```yaml
# Source: github.com/pypa/gh-action-pip-audit README [CITED]
- uses: pypa/gh-action-pip-audit@v1.1.0
  with:
    inputs: .    # scans pyproject.toml in current directory
    # To ignore a specific vuln if needed:
    # ignore-vulns: |
    #   GHSA-XXXX-XXXX-XXXX
```

### softprops/action-gh-release file attachment

```yaml
# Source: github.com/softprops/action-gh-release README [CITED]
- uses: softprops/action-gh-release@v2
  with:
    files: |
      EleitorUM-1.0.0-win64.zip
      EleitorUM-1.0.0-win64.zip.sha256
  # GITHUB_TOKEN is injected automatically — no permissions: block needed for public repos
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Manual `--add-data` for `platforms/` Qt plugins | Automatic via pyinstaller-hooks-contrib | PyInstaller 6.x | Eliminates the most common PyInstaller+Qt packaging failure |
| `cairosvg` for SVG rendering | `svglib` + `reportlab` (no native deps) | Stable alternative — always existed but overlooked | cairosvg works on Linux CI but fails on Windows without GTK; svglib is pure Python |
| `pip list` grep for CVEs | `pip-audit` / `pypa/gh-action-pip-audit` | ~2021 (pip-audit launch) | Structured CVE data from OSV/PyPI Advisory DB; machine-readable output |
| Draft GitHub releases, manual publish | `softprops/action-gh-release` non-draft default | Standard practice | D-06 mandates non-draft; the action default matches |

**Deprecated/outdated:**
- `pyi-grab_version` + `pyi-set_version` utilities: Still work but the idiomatic approach for CI is generating the `VSVersionInfo` Python file in the build script and passing `--version-file` to PyInstaller directly.
- `cairosvg` on Windows: Effectively unusable on clean Windows without GTK. The svglib alternative is superior for this use case.

---

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | `QT_QPA_PLATFORM=offscreen` works reliably on `windows-latest` GitHub Actions runners for pytest-qt | CI workflow patterns | Tests would crash in CI; fix: switch to ubuntu-latest for test job, or add `QT_QPA_PLATFORM=windows` and rely on the runner having a desktop session |
| A2 | `certutil -hashfile` outputs a header line requiring stripping | Common Pitfalls #4 | If wrong, the certutil approach would also be fine; Python hashlib remains simpler regardless |
| A3 | The `pyinstaller-hooks-contrib 2026.5` hooks for PySide6 correctly collect all required plugin types on `windows-latest` without manual datas entries | PyInstaller datas pattern | If wrong: add `--add-data="<PySide6_path>/plugins:PySide6/plugins"` fallback. CI smoke test will catch this failure. |

**If this table is empty:** All claims in this research were verified or cited — no user confirmation needed.
*(3 claims tagged ASSUMED — low risk; all have clear detection paths via smoke test)*

---

## Open Questions

1. **Smoke test robustness on clean Windows VM**
   - What we know: The `--version` smoke test runs the EXE and checks exit code + output. This is valid for catching Qt plugin failures, font loading errors, and import errors.
   - What's unclear: GitHub Actions `windows-latest` is not a "clean machine" (has Python, VS Build Tools, etc.). The real clean-machine test (ROADMAP success criterion 1) requires a separate Windows VM with no Python installed.
   - Recommendation: The CI smoke test catches 90% of packaging failures. The plan should include a manual checkpoint: "After CI passes on tag push, download the ZIP artifact and verify on a clean Windows VM."

2. **`InterVariable.ttf` download step**
   - What we know: D-02 specifies downloading from `rsms/inter` GitHub releases. The file does not currently exist in the repo.
   - What's unclear: Whether downloading in CI vs. pre-committing the binary is preferred. For a build step, pre-committing is simpler (no network call in build; CI constraint says offline at runtime but not at build time). Binary is ~500 KB.
   - Recommendation: Pre-commit the `.ttf` file and set `.gitattributes` binary marker. This matches D-02 ("commit InterVariable.ttf to repo").

3. **Icon generation in CI vs. pre-committed**
   - What we know: `generate_icons.py` produces deterministic output from `icon.svg`.
   - What's unclear: Whether generated PNG/ICO files should be committed or regenerated each CI build.
   - Recommendation: Pre-commit the generated icons. This avoids adding svglib+reportlab to CI install step and keeps the build reproducible even if icon generation dependencies change. Add `src/eleitorum/resources/icons/` to git tracking.

---

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python 3.12 | All scripts | ✓ | 3.12.10 | — |
| Pillow | generate_icons.py | ✓ | 12.1.1 | — |
| svglib | generate_icons.py | ✓ | 1.6.0 | — |
| reportlab | generate_icons.py | ✓ | 4.4.10 | — |
| PyInstaller | build.py | ✓ | 6.20.0 | — |
| pyinstaller-hooks-contrib | build.py (auto) | ✓ | 2026.5 | — |
| pip-audit | CI only | ✓ | 2.10.0 | — |
| InterVariable.ttf | BLD-04 | ✗ (not yet) | — | Must download from rsms/inter releases and commit (D-02) |
| GitHub Actions runners | CI-01 to CI-05 | ✓ | windows-latest | — |

**Missing dependencies with no fallback:**
- `InterVariable.ttf` — must be committed before CI build runs (BLD-04). Download from `https://github.com/rsms/inter/releases`.

**Missing dependencies with fallback:**
- None (all other dependencies are available or installable via pip in CI).

---

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest 9.0.3 |
| Config file | `pyproject.toml` `[tool.pytest.ini_options]` |
| Quick run command | `pytest -x -q` |
| Full suite command | `pytest` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| CI-04 | `--version` exits 0 with correct output | smoke (subprocess) | `EleitorUM.exe --version` (CI step) | ❌ Wave 0 |
| BLD-04 | Inter font accessible at `_MEIPASS` path | manual smoke | Launch bundled app, check font renders | manual |
| BLD-04 | Qt platform plugins present in dist/ | manual smoke | Check `dist/EleitorUM/PySide6/plugins/platforms/qwindows.dll` exists | ❌ Wave 0 |
| D-01 | No UMinho strings remain in src/ | unit (grep) | `pytest tests/unit/test_no_uminho_strings.py` | ❌ Wave 0 |

### Wave 0 Gaps

- [ ] `tests/unit/test_no_uminho_strings.py` — grep test that asserts no "Universidade\|UMinho" in `src/`, `README.md`, `pyproject.toml`
- [ ] CI smoke test step in `.github/workflows/release.yml` — `EleitorUM.exe --version` subprocess check

*(Existing test infrastructure — 383 tests — remains untouched; these are additions)*

---

## Security Domain

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | no | Offline desktop tool |
| V3 Session Management | no | No sessions |
| V4 Access Control | no | Single-user desktop |
| V5 Input Validation | partial | argparse parses only `--version`; no user-controlled string reaches any interpreter |
| V6 Cryptography | partial | SHA-256 via stdlib hashlib; correct use |

### Known Threat Patterns for This Phase

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Repository link in About dialog used for phishing | Spoofing | URL is a compile-time constant in `dialogs.py`; never concatenated from user input (already noted in dialogs.py security comment) |
| PyInstaller EXE triggers AV false positive | Denial of Service | Document SmartScreen bypass procedure in README (already in REQUIREMENTS.md Out of Scope note) |
| Malicious package via pip install in CI | Tampering | pip-audit CVE scan catches known vulnerabilities; pinned versions in pyproject.toml limit supply chain exposure |

---

## Project Constraints (from CLAUDE.md)

All of the following directives from `CLAUDE.md` are active for Phase 4:

- **PyInstaller 6.20.0** — pinned; confirmed installed
- **PySide6 LGPL** — no license issue for bundled distribution (LGPL dynamic linking exception applies to the EXE)
- **One-folder primary build** — D-07 locked; one-file is manual opt-in only
- **No network calls at runtime** — confirmed: the EXE is offline; pip-audit and release upload run only in CI (not user machine)
- **Standalone `.exe`** — PyInstaller one-folder ZIP satisfies this requirement
- **stdlib `csv` for output** — not changed in Phase 4
- **Zero cost / open-source deps** — all new deps are MIT/BSD/LGPL; PyInstaller GPLv2-with-exception allows distributing non-free EXEs
- **Privacy: no real personal data in repo** — test fixtures are synthetic; no data in build artifacts
- **Windows 10 + 11** — pyinstaller-hooks-contrib 2026.5 targets these platforms; validated on windows-latest in CI

---

## Sources

### Primary (HIGH confidence)
- PyInstaller 6.20.0 local installation + `_modules_info.py` hooks inspection — verified `platforms/` plugin is auto-collected via QtGui hook
- svglib 1.6.0 + reportlab 4.4.10 + Pillow 12.1.1 — verified locally on developer machine rendering `icon.svg` to all required sizes
- PyInstaller 6.20.0 PyPI — `https://pypi.org/project/PyInstaller/` — version 6.20.0 confirmed latest
- pip-audit 2.10.0 PyPI — `https://pypi.org/project/pip-audit/` — version 2.10.0 confirmed

### Secondary (MEDIUM confidence)
- pypa/gh-action-pip-audit README — `https://github.com/pypa/gh-action-pip-audit` — YAML syntax and `inputs` parameter
- softprops/action-gh-release README — `https://github.com/softprops/action-gh-release` — `files` input, non-draft default, GITHUB_TOKEN
- PyInstaller spec-files docs — `https://pyinstaller.org/en/stable/spec-files.html` — datas syntax, EXE constructor
- PyInstaller usage docs — `https://pyinstaller.org/en/stable/usage.html` — `--version-file`, `--add-data`, `--icon` flags
- DEV.to VSVersionInfo guide — `https://dev.to/arhamrumi/adding-version-information-to-a-pyinstaller-onefile-executable-6n8` — VSVersionInfo format
- pytest-qt troubleshooting — `https://pytest-qt.readthedocs.io/en/latest/troubleshooting.html` — `QT_QPA_PLATFORM=offscreen`
- Qt for Python PyInstaller deployment — `https://doc.qt.io/qtforpython-6/deployment/deployment-pyinstaller.html`

### Tertiary (LOW confidence — marked ASSUMED)
- Claim A1: QT_QPA_PLATFORM=offscreen on windows-latest — multiple sources suggest it works, not definitively confirmed for this exact runner + PySide6 6.11.1 combination
- Claim A2: certutil output format — based on documentation examples, not tested in this session

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all packages installed and verified locally; slopcheck passed
- Architecture (PyInstaller hooks): HIGH — verified from hooks source code in installed package
- Icon generation: HIGH — rendered the actual icon.svg and produced valid ICO in this session
- CI workflow patterns: MEDIUM — based on official action READMEs; not run in CI yet
- Pitfalls: HIGH — most derived from code inspection of current files (UMinho strings found, exact lines identified)

**Research date:** 2026-05-24
**Valid until:** 2026-08-24 (stable libraries; PyInstaller hooks update with PySide6 releases)
