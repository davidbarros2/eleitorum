# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [Unreleased]

## [1.0.0] - 2026-05-24

### Added

- Input formats: XLSX, XLSM, XLS (xlrd), ODS (odfpy), CSV and TSV with automatic encoding detection
- Encoding detection via charset-normalizer with BOM-first fallback chain (UTF-8 BOM → UTF-8 → Windows-1252 → ISO-8859-1)
- Automatic header row detection (scores first 10 rows)
- Automatic column detection for mecanográfico and name/designation columns with synonym matching
- Manual column mapping with user-override dropdowns
- Multi-sheet Excel support: sheet picker with row counts and empty-sheet indicators
- Transformation rules: mecanográfico prefix normalisation (majority-wins case), leading-zero stripping, float-to-integer conversion, whitespace trimming and collapsing, comma removal, parenthetical annotation removal, mojibake auto-correction, U+FFFD removal
- Validation rules: prefix whitelist (A, PG, ID, F, D, B, Q, EX), positive-integer number, no duplicates within prefix, F/D/B cross-prefix collision detection, empty-name detection
- Caderno eleitoral output: UTF-8 BOM, semicolon separator, CRLF line endings, no quoting, trailing semicolon on data rows
- Lista de elegíveis output: 0-based index, alphabetical sort, same byte-exact format
- Transformation log (_LOG_) and error log (_ERRORS_) written to the output directory in PT-PT
- PySide6 wizard UI with six steps: output type, file upload (drag-and-drop), sheet picker, column mapping, preview table, result screen
- Light and dark themes with WCAG AA contrast; theme persists via QSettings
- Inter variable font bundled; background processing via QThread with progress bar and cancel support
- First-run welcome dialog; About dialog with MIT license note and repository link
- PyInstaller one-folder Windows build (EleitorUM-1.0.0-win64.zip)
- GitHub Actions CI: ruff lint, ruff format check, mypy, pytest on Python 3.11 and 3.12 (windows-latest), pip-audit CVE scanning
- GitHub Actions release workflow: build, --version smoke test, SHA-256 checksum, automatic GitHub Release publication on v1.0.0 tag
- scripts/build.py wrapper for local and CI builds

[Unreleased]: https://github.com/davidbarros2/eleitorum/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/davidbarros2/eleitorum/releases/tag/v1.0.0
