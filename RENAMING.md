# Renaming EleitorUM

This checklist covers every location that references the project name. Use it if the project is ever forked and renamed.

## Python Source

- [ ] `src/eleitorum/config.py` — `APP_NAME = "EleitorUM"` (primary rename point; all UI reads from here)
- [ ] `src/eleitorum/version.py` — module docstring mentions EleitorUM
- [ ] `src/eleitorum/__main__.py` — `argparse.ArgumentParser(prog="EleitorUM")` and `--version` output string
- [ ] `src/eleitorum/ui/strings.py` — `WINDOW_TITLE`, `WELCOME_HEADING` constants
- [ ] `src/eleitorum/ui/dialogs.py` — window title in `setWindowTitle(f"{APP_NAME} — Sobre")`
- [ ] `src/eleitorum/ui/app.py` — `app.setApplicationName(APP_NAME)`, `app.setOrganizationName(APP_NAME)`, `app.setOrganizationDomain(...)`

## QSettings Registry Key

- [ ] QSettings organisation key is `"EleitorUM"` and application key is `"EleitorUM"` (set in `app.py` via `setOrganizationName` / `setApplicationName`). Windows registry path: `HKCU\Software\EleitorUM\EleitorUM`.

## Project Metadata

- [ ] `pyproject.toml` — `name = "eleitorum"`, `description` field, and any `[project.urls]` entries
- [ ] `scripts/build.py` — `--name=EleitorUM`, `OriginalFilename`, `InternalName`, `ProductName`, `FileDescription` in VSVersionInfo
- [ ] Distribution ZIP filename pattern: `EleitorUM-{version}-win64.zip` (hardcoded in `build.py` and `release.yml`)

## CI/CD

- [ ] `.github/workflows/ci.yml` — any `EleitorUM` references in step names or commands
- [ ] `.github/workflows/release.yml` — ZIP filename, smoke test string `"EleitorUM {version}"`, release asset filenames

## Repository Root Files

- [ ] `README.md` — application name in title, body, and install instructions
- [ ] `SPECIFICATION.md` — application name throughout
- [ ] `CHANGELOG.md` — application name in entries
- [ ] `CONTRIBUTING.md` — application name in heading
- [ ] `RENAMING.md` (this file) — all references
- [ ] `LICENSE` — no name reference (MIT boilerplate only)

## Windows Resources

- [ ] `src/eleitorum/resources/icons/EleitorUM.ico` — filename (referenced in `build.py`)
- [ ] `src/eleitorum/resources/icons/EleitorUM-*.png` — filenames (referenced in `generate_icons.py`)

## Package Directory

- [ ] `src/eleitorum/` — the package directory itself; rename requires updating `pyproject.toml` `[tool.setuptools.packages.find]` and all import paths
