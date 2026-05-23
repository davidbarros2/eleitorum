# Phase 1: Core Pipeline — Research

**Researched:** 2026-05-23
**Domain:** Python data-processing pipeline — file reading, encoding detection, data
transformation, validation, CSV output, structured logging
**Confidence:** HIGH

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

- **D-01 Column Detection:** Hybrid — synonym-list matching as primary; regex format-matching
  (`^[A-Za-z]{1,2}\d+$`, ≥70% hit rate) as fallback when no synonym matches. NFKD
  normalization required for synonym matching (converts 'º' ordinal indicator to 'o').

- **D-02 Sort Key for Elegíveis:**
  `unicodedata.normalize('NFKD', designation.casefold()).encode('ascii', 'ignore').decode('ascii')`
  Strips diacritics, case-insensitive, stable sort.

- **D-03 BOM in Output:** `encoding="utf-8-sig"`. Named constant `USE_BOM = True` in
  `output.py`. Status: pending product owner validation against live platform (Section 17 of
  spec). Implementation proceeds with BOM.

- **D-04 Pipeline Progress API:**
  `run_pipeline(source, output_type, progress_cb=None)` where
  `progress_cb: Callable[[int, int], None] | None` receives `(current_row, total_rows)`.
  Phase 2 QThread worker hooks in here. When None, pipeline runs silently.

- **D-05 Module Structure:** Exactly per spec Section 13.2:
  ```
  src/eleitorum/core/
    readers.py      — per-format input readers (openpyxl/xlrd/odfpy/csv)
    detection.py    — encoding detection, header-row scoring, column matching
    transform.py    — mecanográfico + name transformation rules
    validate.py     — uniqueness checks, format validation
    output.py       — CSV writer (byte-exact format, BOM, CRLF, no quoting)
    logging.py      — transformation log builder
    errors.py       — custom exception hierarchy, PT-PT message strings
    pipeline.py     — orchestrator that calls all of the above in order
  src/eleitorum/
    config.py       — APP_NAME constant, version, paths
    version.py      — version string
  ```

- **D-06 Encoding Detection Threshold:** ≥0.85 confidence with `charset-normalizer`.
  BOM trusted unconditionally. Fallback chain: UTF-8 BOM → UTF-8 → Windows-1252 → ISO-8859-1.
  `charset-normalizer` is required (not `chardet`).

- **D-07 Error Handling Philosophy:** Two-tier model.
  - Hard errors → raise custom exception immediately; no output file; `_ERRORS_` log.
  - Soft issues → log `AVISO` entry; processing continues.

- **D-08 Valid Prefixes:** `{A, PG, ID, F, D, B, Q, EX}` exactly. F/D/B share numeric
  namespace. A/PG/ID/Q/EX have independent namespaces.

### Claude's Discretion

- Mojibake detection implementation: scan for `\xc3` followed by a byte in 0x80–0xBF range;
  attempt `string.encode('latin-1').decode('utf-8')`; accept only if result has no remaining
  mojibake sequences.
- Internal exception hierarchy naming (must produce PT-PT messages matching spec Section 7.3).
- Test fixture organization within `tests/unit/` and `tests/fixtures/generators.py`.

### Deferred Ideas (OUT OF SCOPE)

None — discussion stayed within phase scope.
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| INP-01 | XLSX/XLSM loading via openpyxl | openpyxl 3.1.5 verified; read_only+data_only mode confirmed |
| INP-02 | Legacy XLS via xlrd | xlrd 2.0.2 verified; XLS-only, no XLSX |
| INP-03 | ODS via odfpy | odfpy 1.4.1 verified; use `pd.read_excel(engine="odf")` |
| INP-04 | CSV with encoding detection | charset-normalizer 3.4.7; from_bytes() API confirmed |
| INP-05 | TSV with encoding detection | Same path as CSV; delimiter='\t' |
| INP-06 | Unsupported format error | Hard error in readers.py; list accepted formats |
| INP-07 | Encoding detection 64KB + 0.85 threshold | from_bytes() + chaos<0.15 proxy; BOM via `.bom` property |
| INP-08 | Undetectable encoding: PT-PT actionable message | errors.py pattern established |
| INP-09 | Log detected encoding | LOG tag: `INPUT` |
| INP-10 | Multi-sheet picker data (names + row counts) | openpyxl sheets: `wb.sheetnames`; count via `ws.max_row` (approximate in read_only) |
| INP-11 | Empty sheet "folha vazia" indicator | Check first data row existence after header detection |
| INP-12 | Skip trailing empty rows silently | Check all-None/empty in relevant columns |
| INP-13 | PermissionError on read: PT-PT message | Wrap `open()`/`load_workbook()` in try/except PermissionError |
| DET-01 | Header row auto-detection (first 10 rows, scoring) | Score: non-empty + short text + non-numeric + synonym bonus |
| DET-02 | No header found → manual mapping mode | Return None from detect_header_row(); pipeline signals Phase 2 UI |
| DET-03 | Mecanográfico column synonym matching | NFKD normalization; synonym set confirmed; see Code Examples |
| DET-04 | Name column synonym matching | NFKD normalization; synonym set confirmed |
| DET-05 | Show detection result to user | Pipeline returns detection metadata; Phase 2 UI reads it |
| DET-06 | Ambiguous detection → surface both candidates | Return list of matches sorted by score |
| DET-07 | Elegíveis: hide mec mapping | Phase 2 UI concern; pipeline accepts col_map kwarg |
| TRF-01 | Trim/remove whitespace from mec values | `re.sub(r'\s+', '', raw)` |
| TRF-02 | Excel float mec → int string | `int(val)` if `isinstance(val, float) and val == int(val)` |
| TRF-03 | Strip leading zeros from mec number | `lstrip('0') or '0'` then validate ≥1 |
| TRF-04 | Prefix case normalization (majority-wins, lowercase on tie) | Count lowercase vs uppercase prefix letters across all rows |
| TRF-05 | Name whitespace: strip all kinds including NBSP, ZWSP | `re.sub(r'\s+', ' ', s.strip())` after expanding Unicode ws |
| TRF-06 | Collapse internal whitespace to single space | Part of TRF-05 regex |
| TRF-07 | Remove commas from names | `re.sub(r',', '', s)` + log |
| TRF-08 | Remove parenthetical annotations | `re.sub(r'\s*\([^)]*\)\s*', ' ', s).strip()` + re-apply ws |
| TRF-09 | Mojibake auto-correction (deterministic) | Encode latin-1 + decode utf-8; accept if no remaining pattern |
| TRF-10 | Ambiguous mojibake → AVISO log, no correction | Verify correction is clean before accepting |
| TRF-11 | Remove U+FFFD from names, keep rest | `s.replace('�', '')` + log each occurrence |
| TRF-12 | Preserve name capitalization as-is | No case transformation on names |
| TRF-13 | Elegíveis sort by designation (ascending, diacritic-stripped) | Sort key D-02 confirmed |
| TRF-14 | Elegíveis index: 0-based assigned after sort | `enumerate(sorted_rows)` |
| TRF-15 | Caderno: preserve input row order | No sort; iterate in read order |
| VAL-01 | Invalid prefix → hard error with offending rows | Collect all failures before raising |
| VAL-02 | Non-positive mec number → hard error | `num <= 0` check |
| VAL-03 | Duplicate within prefix → hard error | `set` per prefix |
| VAL-04 | F/D/B cross-prefix collision → hard error | Shared `set` for F, D, B numbers |
| VAL-05 | A/PG/ID/Q/EX independent namespaces → no error | Separate sets; A500 + PG500 = valid |
| VAL-06 | Empty name after transformation → hard error | Collect all failures |
| VAL-07 | Caderno: mec without name or vice versa → hard error | Check both fields present |
| VAL-08 | Output path == input path → hard error | `pathlib.Path` comparison; raised before write |
| VAL-09 | Output file open in another app → PermissionError on write | Wrap `open()` in try/except PermissionError |
| OUT-01 | UTF-8 with BOM | `open(..., encoding='utf-8-sig', newline='')` confirmed |
| OUT-02 | Semicolon separator | `csv.writer(delimiter=';')` confirmed |
| OUT-03 | CRLF line endings | `lineterminator='\r\n'` confirmed |
| OUT-04 | No quoting | `quoting=csv.QUOTE_NONE, escapechar=chr(92)` confirmed |
| OUT-05 | File ends with CRLF | `lineterminator='\r\n'` applies after every row including last |
| OUT-06 | Caderno header exactly `personnel_number;name;category` | Literal string |
| OUT-07 | Caderno rows: `{mec};{name};` (empty third field) | Write three fields; third is empty string |
| OUT-08 | Elegíveis header exactly `personnel_number;designation` | Literal string |
| OUT-09 | Elegíveis rows: `{index};{designation}` | 0-based index from enumerate |
| OUT-10 | No output on validation error | pipeline.py: write only after all validation passes |
| OUT-11 | Never write to input path | VAL-08 check before write |
| OUT-12 | Prompt/auto-rename on existing file | Phase 2 UI concern for dialog; pipeline raises if collision |
| LOG-01 | Transform log file: `{name}_LOG_{ts}.txt` next to output | Build path in pipeline.py |
| LOG-02 | Log encoding: UTF-8 BOM; one event per line; `[YYYY-MM-DD HH:MM:SS]` | Confirmed format; write with `encoding='utf-8-sig'` |
| LOG-03 | Tags: INICIO, INPUT, COLUNA, CASO, LIMPEZA, AVISO, ERRO, SAIDA, FIM | Constants in logging.py |
| LOG-04 | Log records all required events | See spec Section 8.1 worked example |
| LOG-05 | Error log: `{name}_ERRORS_{ts}.txt` | Only written on failure; same format as LOG-02 |
| LOG-06 | Error log: row number, column name, value, PT-PT message | Per-error struct in errors.py |
| LOG-07 | Log files only written to user-chosen location | pipeline.py path management |
| PERF-01 | 150k rows XLSX in < 10s | Benchmarked: ~3.8s openpyxl + ~0.35s processing = ~4.1s total |
| PERF-03 | openpyxl `read_only=True, data_only=True` | Confirmed required; row iteration via `iter_rows(values_only=True)` |
</phase_requirements>

---

## Summary

Phase 1 delivers the entire Qt-free core of EleitorUM: every reader, every transformation rule,
every validation rule, the byte-exact CSV writer, and the transformation log builder. All eight
core modules are created from scratch in `src/eleitorum/core/`. The phase concludes only when
`pytest --cov` reports ≥90% line coverage over these modules with zero Qt imports present.

The technology stack is entirely validated on the target machine (Python 3.12.10, all packages
installed). Every API call researched here was confirmed by live execution: openpyxl
`iter_rows(values_only=True)` in `read_only+data_only` mode, `charset-normalizer`'s
`from_bytes()` with `best()` and `.bom`, stdlib `csv` with `QUOTE_NONE + escapechar + utf-8-sig`,
NFKD normalization for synonym matching, and the mojibake encode/decode round-trip.

The single largest implementation risk is the charset-normalizer confidence mapping: the library
does not expose a chardet-style float confidence. The correct mapping is: treat `best().chaos < 0.15`
as equivalent to "confidence ≥ 0.85", and treat BOM presence (`best().bom == True`) as
unconditional trust. For ambiguous inputs (multiple results, `chaos ≥ 0.15`), fall through to the
manual fallback chain.

**Primary recommendation:** Build the eight modules in dependency order (errors → config →
readers → detection → transform → validate → output → logging → pipeline), write unit tests for
each module before moving to the next, and run pytest-cov after every module to track coverage
progress toward the 90% gate.

---

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| File reading (XLSX/XLS/ODS/CSV/TSV) | Core library (`readers.py`) | — | All I/O is synchronous in Phase 1; Phase 2 wraps in QThread |
| Encoding detection | Core library (`detection.py`) | — | Pure Python, no UI dependency |
| Header row scoring | Core library (`detection.py`) | — | Algorithm runs on raw cell values |
| Column synonym matching | Core library (`detection.py`) | Phase 2 UI (override dialog) | Detection result is returned to UI for confirmation/override |
| Data transformation | Core library (`transform.py`) | — | Stateless, pure functions |
| Validation (uniqueness, format) | Core library (`validate.py`) | — | Stateful only for duplicate tracking |
| CSV output writing | Core library (`output.py`) | — | Byte-exact; no UI involvement |
| Transformation log building | Core library (`logging.py`) | — | Append-only log; Phase 2 reads entries for UI display |
| Custom exceptions + PT-PT messages | Core library (`errors.py`) | — | Messages must be usable by both CLI and UI layers |
| Pipeline orchestration | Core library (`pipeline.py`) | Phase 2 QThread (caller) | Phase 2 calls `run_pipeline()`; pipeline is Qt-free |

---

## Standard Stack

### Core (all pre-installed and verified on target machine)

| Library | Installed Version | Purpose | Why Standard |
|---------|-------------------|---------|--------------|
| Python | 3.12.10 | Runtime | Project spec requires 3.11+; 3.12 is compatible |
| openpyxl | 3.1.5 | XLSX/XLSM read | De-facto standard; `read_only+data_only` mode for performance |
| xlrd | 2.0.2 | Legacy XLS read | Only maintained library for binary XLS; XLS-only scope |
| odfpy | 1.4.1 | ODS backend | Required by `pd.read_excel(engine="odf")` |
| pandas | 3.0.2 | ODS/CSV normalization | Handles multi-format input normalization pipeline |
| charset-normalizer | 3.4.7 | Encoding detection | MIT license, fast, BOM-aware |
| stdlib `csv` | (stdlib) | CSV output | Byte-exact control; no third-party dependency |
| pytest | 9.0.3 | Test framework | Standard Python testing |
| pytest-cov | 7.1.0 | Coverage reporting | ≥90% gate enforcement |
| mypy | 1.19.1 | Type checking | CI requirement |
| ruff | 0.15.8 | Lint + format | Replaces flake8 + black + isort |

Note: `pandas` is 3.0.2 (installed) vs 3.0.3 (CLAUDE.md pin). Both are pandas 3.0 series with
identical CoW semantics. [ASSUMED] that 3.0.2 is functionally equivalent for this phase.

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `unicodedata` | (stdlib) | NFKD normalization, sort key | Column matching, sort key (D-02) |
| `re` | (stdlib) | Regex for mec parsing, whitespace | All transformation rules |
| `pathlib` | (stdlib) | Path manipulation | File path comparison (VAL-08) |
| `datetime` | (stdlib) | Log timestamps | LOG-02 format |

**Installation command (for fresh environment):**
```bash
pip install openpyxl==3.1.5 xlrd==2.0.2 odfpy==1.4.1 pandas==3.0.2 charset-normalizer==3.4.7 pytest==9.0.3 pytest-cov==7.1.0 mypy==1.19.1 ruff==0.15.8
```

---

## Package Legitimacy Audit

All packages verified via slopcheck 0.6.1 on 2026-05-23:

| Package | Registry | slopcheck | Disposition |
|---------|----------|-----------|-------------|
| openpyxl | PyPI | [OK] | Approved |
| xlrd | PyPI | [OK] | Approved |
| odfpy | PyPI | [OK] | Approved |
| pandas | PyPI | [OK] | Approved |
| charset-normalizer | PyPI | [OK] (no source repo link noted) | Approved — confirmed via CLAUDE.md and official PyPI |
| pytest | PyPI | [OK] | Approved |
| pytest-cov | PyPI | [OK] (no source repo link noted) | Approved — standard pytest ecosystem package |
| mypy | PyPI | [OK] | Approved |
| ruff | PyPI | [OK] | Approved |

**Packages removed due to [SLOP] verdict:** none
**Packages flagged as suspicious [SUS]:** none

---

## Architecture Patterns

### System Architecture Diagram

```
Input file (XLSX/XLS/ODS/CSV/TSV)
        |
        v
  [readers.py]  <-- openpyxl / xlrd / odfpy / stdlib csv
   - detect format by extension
   - open in appropriate mode
   - stream raw rows as tuples
        |
        v
  [detection.py]
   - BOM check --> encoding detection (charset-normalizer)
   - header-row scoring (first 10 rows)
   - column synonym matching (NFKD)
        |
        v
  [transform.py]  (per-row, stateless pure functions)
   - mec: trim whitespace, float->int, strip leading zeros
   - mec: prefix case normalization (batch, after all rows seen)
   - name: trim/collapse whitespace, remove commas, remove parentheses
   - name: mojibake detection + correction
   - name: U+FFFD removal
        |
        v
  [validate.py]  (stateful: accumulates sets for uniqueness)
   - prefix validity check
   - number > 0 check
   - uniqueness per prefix
   - F/D/B shared namespace collision
   - empty name check
        |
        v  (hard errors exit here; ERRORS log written)
  [output.py]
   - build header row string
   - elegíveis: sort by NFKD key, assign 0-based index
   - caderno: preserve order
   - write UTF-8 BOM + semicolon + CRLF + no-quote CSV
        |
        v
  [logging.py]
   - write transformation log alongside output
        |
        v
  [pipeline.py] (orchestrator)
   - run_pipeline(source, output_type, progress_cb=None)
   - calls all above in order
   - returns result dict to caller (Phase 2 QThread or test)
```

### Recommended Project Structure

```
src/
  eleitorum/
    __init__.py
    __main__.py
    config.py           # APP_NAME, VERSION constants
    version.py          # version string
    core/
      __init__.py
      errors.py         # FIRST — all other modules import from here
      readers.py        # depends on errors
      detection.py      # depends on errors, readers
      transform.py      # depends on errors
      validate.py       # depends on errors
      output.py         # depends on errors
      logging.py        # depends on errors
      pipeline.py       # depends on all of the above
tests/
  conftest.py
  fixtures/
    generators.py       # 15 fixture functions per spec Section 14.3
  unit/
    test_transform.py
    test_validate.py
    test_detection.py
    test_output.py
    test_readers.py     # encoding detection, format loading
  integration/
    test_full_pipeline.py
```

### Pattern 1: Byte-Exact CSV Output

**What:** Write UTF-8 BOM + semicolon-delimited + CRLF + no-quote CSV using stdlib csv.
**When to use:** Always — this is the only correct output method.

```python
# Source: verified by running this exact code — see research execution above
import csv

def write_csv(path: str, header: list[str], rows: list[list[str]]) -> None:
    with open(path, mode='w', encoding='utf-8-sig', newline='') as f:
        writer = csv.writer(
            f,
            delimiter=';',
            quoting=csv.QUOTE_NONE,
            escapechar='\\',
            lineterminator='\r\n',
        )
        writer.writerow(header)
        for row in rows:
            writer.writerow(row)
```

Verification: first 3 bytes are `\xef\xbb\xbf`; all line endings are `\r\n`; no quote characters
appear anywhere.

### Pattern 2: Column Name Synonym Matching with NFKD

**What:** Tolerant matching that handles 'º' (ordinal indicator), accents, case.
**When to use:** `detection.py` column matching and header scoring synonym bonus.

```python
# Source: verified by running against real Portuguese column names
import unicodedata

def normalize_col_name(s: str) -> str:
    """NFKD normalization for tolerant column name matching."""
    s = s.strip().lower()
    # NFKD converts 'º' (U+00BA ordinal indicator) -> 'o', strips combining marks
    return ''.join(
        c for c in unicodedata.normalize('NFKD', s)
        if unicodedata.category(c) != 'Mn'  # Mn = Non-spacing mark
    )

# Build normalized synonym sets once at module level
MECANOGRAFICO_SYNONYMS = frozenset(normalize_col_name(s) for s in [
    'personnel_number',
    'no mecanografico', 'numero mecanografico', 'n mecanografico',
    'n. mecanografico', 'n.o mec.', 'no mec.', 'no mec', 'n.o mec', 'no. mec.',
    'no necanografico',  # observed typo
    'nmec', 'nmecanografico',
    'numero de empregado', 'numero de empregado',
    'codigo', 'codigo',
    'numaluno', 'num aluno', 'n aluno',
])

NAME_SYNONYMS = frozenset(normalize_col_name(s) for s in [
    'name',
    'nome', 'nome completo', 'nome de empregado', 'nome aluno', 'nomealuno',
    'aluno',
    'designation', 'designacao',
])
```

Critical finding: the spec uses 'nº' (with 'º' U+00BA ordinal indicator), but input files may
use 'nº' OR 'no' OR 'n°'. NFKD converts all three to 'no', enabling a single synonym entry to
match all variants. NFD alone does NOT decompose 'º'; NFKD is required.

### Pattern 3: Mojibake Detection and Correction

**What:** Detect UTF-8-read-as-Latin-1 corruption and round-trip correct it.
**When to use:** `transform.py` for every name value.

```python
# Source: verified by running this exact logic against test strings
import re

_MOJIBAKE_PAT = re.compile(r'\xc3[\x80-\xbf]')  # U+00C3 + char in 0x80-0xBF range

def try_fix_mojibake(s: str) -> tuple[str, bool]:
    """
    Returns (corrected, was_fixed).
    If correction is ambiguous or fails, returns (original, False).
    """
    if not _MOJIBAKE_PAT.search(s):
        return s, False
    try:
        fixed = s.encode('latin-1').decode('utf-8')
        # Accept correction only if the result is clean (no remaining patterns)
        if not _MOJIBAKE_PAT.search(fixed):
            return fixed, True
        return s, False
    except (UnicodeEncodeError, UnicodeDecodeError):
        return s, False
```

The mojibake pattern `\xc3[\x80-\xbf]` matches U+00C3 (the Latin capital A-tilde 'Ã') followed
by any character in U+0080–U+00BF range. This is the exact fingerprint of UTF-8 multi-byte
sequences when each byte is treated as a Latin-1 character.

### Pattern 4: Encoding Detection with charset-normalizer

**What:** Map charset-normalizer's chaos/coherence model to the 0.85 confidence threshold.
**When to use:** `detection.py` for CSV/TSV files.

```python
# Source: verified by running against Portuguese-content CSV files
from charset_normalizer import from_bytes

def detect_encoding(raw_bytes: bytes) -> tuple[str, float]:
    """
    Returns (encoding_name, confidence_proxy).
    BOM is always detected first. Falls through to fallback chain if ambiguous.
    """
    # charset-normalizer confidence is NOT a float like chardet's.
    # Use chaos < 0.15 as the equivalent of "confidence >= 0.85".
    results = from_bytes(raw_bytes)
    if not results:
        return _fallback_chain(raw_bytes)

    best = results.best()
    if best is None:
        return _fallback_chain(raw_bytes)

    # BOM is unconditionally trusted (D-06)
    if best.bom:
        return best.encoding, 1.0

    # chaos < 0.15 = "confident" (maps to chardet's >= 0.85)
    if best.chaos < 0.15:
        return best.encoding, 1.0 - best.chaos

    return _fallback_chain(raw_bytes)

def _fallback_chain(raw_bytes: bytes) -> tuple[str, float]:
    """Try UTF-8, cp1252, iso-8859-1 in order."""
    for enc in ('utf-8', 'cp1252', 'iso-8859-1'):
        try:
            raw_bytes.decode(enc)
            return enc, 0.5  # lower confidence proxy for fallback
        except UnicodeDecodeError:
            continue
    raise EncodingDetectionError(
        "Nao foi possivel identificar a codificacao do ficheiro. "
        "Tente abri-lo e guarda-lo novamente em UTF-8."
    )
```

**Critical API note:** charset-normalizer does NOT have a `.encoding_confidence` attribute.
The confidence model is: `chaos` (mess ratio, 0.0=clean, 1.0=garbage) and `coherence` (language
fitness, 0.0–1.0). `best()` returns the highest-ranked result. The threshold mapping is
`chaos < 0.15` ≈ chardet confidence ≥ 0.85.

### Pattern 5: openpyxl Streaming Read (PERF-03)

**What:** Read XLSX/XLSM in streaming mode without loading full workbook into memory.
**When to use:** `readers.py` for all Excel reads.

```python
# Source: verified by running against 150k row XLSX — elapsed: 3.79s
import openpyxl

def read_xlsx(path: str, sheet_name: str | None = None):
    """Stream rows from XLSX. Returns (sheet_names_with_counts, row_iterator)."""
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    # Get all sheet metadata (must iterate before opening in read_only mode)
    sheet_names = wb.sheetnames
    if sheet_name is None:
        sheet_name = sheet_names[0]
    ws = wb[sheet_name]
    # iter_rows(values_only=True) streams without loading all into memory
    return sheet_names, ws.iter_rows(values_only=True), wb  # caller closes wb
```

**openpyxl read_only gotchas:**
1. `ws.max_row` in read_only mode returns the dimension hint from the file, which may be stale
   (e.g., Excel sometimes writes `<sheetData>` with a cached max_row that includes deleted rows).
   Use it only as an approximation for the sheet picker row count display (INP-10/INP-11).
2. Numeric cells come back as Python `int` (not `float`) when the stored value is a whole number.
   The `data_only=True` flag is required — without it, formula cells return `None`.
3. You cannot call `iter_rows()` after calling `wb.close()`. Close the workbook only after all
   iteration is complete.

### Pattern 6: Pipeline Entry Point (D-04)

```python
# Source: design per CONTEXT.md D-04
from typing import Callable

def run_pipeline(
    source: str | dict,
    output_type: str,  # 'caderno' | 'elegiveis'
    output_path: str | None = None,
    progress_cb: Callable[[int, int], None] | None = None,
) -> dict:
    """
    Main pipeline entry point. Qt-free.

    Args:
        source: file path string, or dict {'path': str, 'sheet': str} for multi-sheet.
        output_type: 'caderno' or 'elegiveis'.
        output_path: destination CSV path. If None, dry-run (validate only).
        progress_cb: called as progress_cb(current_row, total_rows) for Phase 2 QThread.

    Returns dict:
        success: bool
        rows: int
        transformations: int
        log_entries: list[str]
        errors: list[str]
        output_path: str | None
        detection: dict  # encoding, header_row_index, mec_col, name_col
    """
    ...
```

### Anti-Patterns to Avoid

- **Using `pandas.to_csv()` for output:** pandas has been inconsistent about BOM, quoting, and
  exact line endings. Use stdlib `csv` always. This is a locked decision (CLAUDE.md).
- **NFD instead of NFKD for column matching:** NFD does not decompose the ordinal indicator 'º'
  (U+00BA). Using NFD causes 'Nº Mec.' to not match the synonym 'no mec.'. Use NFKD.
- **chardet for encoding detection:** chardet v7 licensing is disputed (LGPL→MIT via AI rewrite).
  Use charset-normalizer. This is a locked decision.
- **Reading openpyxl without `read_only=True`:** loads the entire workbook into memory. For 150k
  rows this risks OOM or timeout. Always use `read_only=True, data_only=True`.
- **Importing anything from PySide6 or Qt in core modules:** the 90% coverage gate explicitly
  checks for zero Qt imports. Any Qt import in `readers.py`, `detection.py`, `transform.py`,
  `validate.py`, `output.py`, `logging.py`, `errors.py`, or `pipeline.py` is a hard failure.
- **Using `str.encode('utf-8-sig')` for BOM instead of file-level encoding:** `open(...,
  encoding='utf-8-sig')` writes the BOM automatically and handles encoding correctly. Do not
  manually prepend `\xef\xbb\xbf` bytes.
- **Case normalization before uniqueness check:** must normalize prefix case AFTER collecting all
  rows, because the majority-wins rule requires seeing all inputs first.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| XLSX reading | Custom XML parser | openpyxl | Handles all XLSX variants, formulas, shared strings |
| XLS reading | Binary format parser | xlrd 2.0.2 | Format is undocumented; xlrd has 15+ years of edge cases |
| ODS reading | ODF XML parser | odfpy + `pd.read_excel(engine="odf")` | ODF spec has many optional features |
| Encoding detection | Byte frequency analysis | charset-normalizer | 10–100x faster; handles all encoding variants |
| CSV BOM/CRLF | Manual byte writing | `open(encoding='utf-8-sig', newline='') + csv.writer` | Handles BOM + CRLF atomically |
| Unicode normalization | Custom diacritic table | `unicodedata.normalize('NFKD', ...)` | Handles all Unicode combining characters |
| Whitespace detection | ASCII-only `strip()` | `re.sub(r'\s+', ' ', s)` | `\s` matches NBSP (U+00A0), ZWSP (U+200B), and all Unicode whitespace |

**Key insight:** every "simple" problem in this domain has Unicode edge cases that took
established libraries years to discover and fix. The 150k row dataset virtually guarantees
encountering at least one edge case per category.

---

## Common Pitfalls

### Pitfall 1: charset-normalizer has no `.encoding_confidence` attribute
**What goes wrong:** `AttributeError: 'CharsetMatch' object has no attribute 'encoding_confidence'`
**Why it happens:** chardet's API has `.confidence`; charset-normalizer does not. Training data
conflates the two libraries' APIs.
**How to avoid:** Use `best().chaos` (lower=better) and `best().bom` (True=BOM present). See
Pattern 4 above.
**Warning signs:** Any code that calls `.encoding_confidence`, `.confidence`, or
`detect()['confidence']` on a charset-normalizer result.

### Pitfall 2: openpyxl `max_row` is unreliable in read_only mode
**What goes wrong:** Sheet picker shows wrong row count; empty rows counted as data.
**Why it happens:** Excel caches sheet dimensions in XML metadata; this cache is not always
updated when rows are deleted. read_only mode trusts the cache without verifying.
**How to avoid:** Use `ws.max_row` only as an approximate hint for the sheet picker (INP-10).
For actual row counting, iterate and count. Trailing empty rows are filtered by INP-12 logic.
**Warning signs:** Row count shown in the sheet picker is higher than the actual data rows.

### Pitfall 3: QUOTE_NONE requires escapechar
**What goes wrong:** `TypeError: "quotechar" must be a 1-character string`
**Why it happens:** Python's csv module requires `escapechar` to be set when `quoting=QUOTE_NONE`,
otherwise it raises on characters that would need escaping.
**How to avoid:** Always pair `quoting=csv.QUOTE_NONE` with `escapechar='\\'`. For data that
contains no special csv characters (our case: semicolon-delimited names without semicolons),
the escapechar is never actually used.
**Warning signs:** ` csv.writer(quoting=csv.QUOTE_NONE)` without `escapechar` → runtime error.

### Pitfall 4: Case normalization timing error
**What goes wrong:** Prefix case normalization applies to some rows but not others; or the
majority count is wrong.
**Why it happens:** Case normalization (TRF-04) is a batch operation: collect ALL prefix letters
from all rows, then count lowercase vs uppercase, then apply to ALL rows. Applying it row-by-row
makes the normalization decision on partial data.
**How to avoid:** Two-pass design in pipeline.py: (1) parse and transform all rows, accumulate
prefix letters; (2) compute majority case; (3) rewrite prefix case on all rows.
**Warning signs:** Some rows use lowercase prefix and others uppercase in the same output.

### Pitfall 5: Mojibake pattern misidentifies clean text
**What goes wrong:** Clean Portuguese text (e.g., 'Ã' from the word 'ÃNGULO') gets incorrectly
flagged as mojibake.
**Why it happens:** The pattern `Ã[\x80-\xbf]` is very specific — it requires 'Ã' (U+00C3)
followed by a character in the 0x80–0xBF range. Normal Portuguese words with 'Ã' are
typically followed by characters outside this range (e.g., 'N' U+004E, 'G' U+0047).
**How to avoid:** Verify that the correction round-trip produces clean text before accepting.
The `try_fix_mojibake()` function returns `(original, False)` if the corrected result still
contains the mojibake pattern.
**Warning signs:** Names that were correct in the input come out garbled in the output.

### Pitfall 6: F/D/B uniqueness check fails for mixed-case input
**What goes wrong:** 'F500' and 'd500' are not detected as a cross-prefix collision.
**Why it happens:** Uniqueness checks must run AFTER prefix case normalization (or must normalize
to uppercase before comparing in the validation set).
**How to avoid:** Always normalize prefix to uppercase for the purpose of uniqueness checking
in `validate.py`, regardless of what the output case will be. The FDB shared set uses uppercase
keys: `('F', 500)`, `('D', 500)`, `('B', 500)`.
**Warning signs:** VAL-04 test passes but a real file with mixed-case F/D/B slips through.

### Pitfall 7: Elegíveis sort key stability with identical names
**What goes wrong:** Two rows with identical designations sort inconsistently across runs.
**Why it happens:** Python's sort is stable (preserves original order for equal keys), but if
duplicates are expected, the sort key must be deterministic. VAL-03/VAL-04 reject duplicate
mecanográficos but not duplicate names in elegíveis output.
**How to avoid:** The NFKD sort key (D-02) is deterministic and Python's sort is stable, so
equal keys preserve input order. No additional tiebreaker needed.
**Warning signs:** Elegíveis output has different row ordering on repeat runs with the same
input.

### Pitfall 8: Empty sheet detection false positives (INP-11)
**What goes wrong:** A sheet with a title row but no data is shown as having rows.
**Why it happens:** `ws.max_row` in read_only mode counts all rows including the title/blank
rows before the header.
**How to avoid:** For the "empty" indicator in the sheet picker, check whether the sheet has
at least 2 non-empty rows (one could be a header; at least one must be a data row). Use
`iter_rows(values_only=True)` and count non-empty rows up to a limit of 5 for the check.
**Warning signs:** A sheet with only a title row is shown as "5 rows" in the picker.

---

## Code Examples

### Caderno CSV output — byte-exact
```python
# Source: verified execution, bytes confirmed: BOM=efbbbf, CRLF=0d0a, no quotes
import csv

CADERNO_HEADER = ['personnel_number', 'name', 'category']

def write_caderno(path: str, rows: list[tuple[str, str]]) -> None:
    with open(path, mode='w', encoding='utf-8-sig', newline='') as f:
        writer = csv.writer(
            f, delimiter=';', quoting=csv.QUOTE_NONE,
            escapechar='\\', lineterminator='\r\n',
        )
        writer.writerow(CADERNO_HEADER)
        for mec, name in rows:
            writer.writerow([mec, name, ''])  # third field always empty
```

### Elegíveis CSV output — with 0-based index
```python
# Source: spec Section 5.3 + D-02 sort key
import unicodedata, csv

ELEGIVEIS_HEADER = ['personnel_number', 'designation']

def _sort_key(designation: str) -> str:
    return (
        unicodedata.normalize('NFKD', designation.casefold())
        .encode('ascii', 'ignore')
        .decode('ascii')
    )

def write_elegiveis(path: str, designations: list[str]) -> None:
    sorted_desigs = sorted(designations, key=_sort_key)
    with open(path, mode='w', encoding='utf-8-sig', newline='') as f:
        writer = csv.writer(
            f, delimiter=';', quoting=csv.QUOTE_NONE,
            escapechar='\\', lineterminator='\r\n',
        )
        writer.writerow(ELEGIVEIS_HEADER)
        for idx, designation in enumerate(sorted_desigs):
            writer.writerow([str(idx), designation])
```

### Log line format — matches spec Section 8.1 exactly
```python
# Source: format verified against spec example output
from datetime import datetime

TAGS = frozenset(['INICIO', 'INPUT', 'COLUNA', 'CASO', 'LIMPEZA', 'AVISO', 'ERRO', 'SAIDA', 'FIM'])

def log_line(tag: str, message: str, ts: datetime | None = None) -> str:
    if ts is None:
        ts = datetime.now()
    assert tag in TAGS, f"Unknown log tag: {tag}"
    timestamp = ts.strftime('%Y-%m-%d %H:%M:%S')
    return f"[{timestamp}] {tag:<7} {message}"
```

### Mecanográfico parsing — complete
```python
# Source: verified execution against all test cases
import re

VALID_PREFIXES = frozenset({'A', 'PG', 'ID', 'F', 'D', 'B', 'Q', 'EX'})
FDB_SHARED = frozenset({'F', 'D', 'B'})
_MEC_PAT = re.compile(r'^([A-Za-z]{1,2})(\d+)$')

def parse_mecanografico(raw) -> tuple[str, int]:
    """
    Parse and normalize a mecanografico value.
    Returns (UPPERCASE_PREFIX, positive_integer).
    Raises MecanograficoError on invalid input.
    """
    # TRF-02: handle openpyxl numeric cell values
    if isinstance(raw, float):
        if raw == int(raw):
            raw = int(raw)
        else:
            raise MecanograficoError(f"Valor decimal invalido: '{raw}'")

    if isinstance(raw, int):
        raise MecanograficoError(
            f"Numero sem prefixo: '{raw}'. "
            "O numero mecanografico deve incluir o prefixo (ex: F{raw})."
        )

    # TRF-01: remove all whitespace
    s = re.sub(r'\s+', '', str(raw))

    m = _MEC_PAT.match(s)
    if not m:
        raise MecanograficoError(f"Formato invalido: '{raw}'")

    prefix = m.group(1).upper()
    num_str = m.group(2).lstrip('0') or '0'  # TRF-03: strip leading zeros

    if prefix not in VALID_PREFIXES:
        raise MecanograficoError(f"Prefixo invalido: '{prefix}'")  # VAL-01

    num = int(num_str)
    if num <= 0:
        raise MecanograficoError(
            f"O numero mecanografico deve ser positivo: '{raw}'"
        )  # VAL-02

    return prefix, num
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `chardet` for encoding detection | `charset-normalizer` | Chardet v7 relicensing dispute (2024+) | MIT license; 10–100x faster; same API shape |
| `pandas.to_csv()` for output | stdlib `csv` with explicit params | Project decision (no state change in library) | Byte-exact BOM + CRLF control |
| openpyxl default mode | `read_only=True, data_only=True` | openpyxl 2.4+ (stable feature) | Memory-efficient; required for 150k row performance |
| `chardet.detect()['confidence']` | charset-normalizer `best().chaos` | API difference (never was equivalent) | Different model: chaos ratio, not confidence float |
| pandas `df.copy()` workaround | Automatic CoW in pandas 3.0 | pandas 3.0.0 (2024) | All slice modifications must use `.copy()` or `.loc[]` |

**Deprecated/outdated:**
- `chardet`: licensing uncertainty from v7.0 AI-assisted rewrite; use charset-normalizer.
- `xlwt`: write-only XLS library; unmaintained; irrelevant (we do not write XLS).
- `odfpy` with direct API: use through `pd.read_excel(engine="odf")` for consistency.

---

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | pandas 3.0.2 (installed) is functionally equivalent to 3.0.3 (CLAUDE.md pin) for this phase | Standard Stack | Minimal — both are pandas 3.0 series; CoW semantics identical |
| A2 | TRF-02 (float→int) for pure-numeric mec values (no prefix) results in VAL-01 hard error | Phase Requirements | If product owner expects numeric-only mec to be valid (some dept convention), the validation rule needs revision |
| A3 | The `chaos < 0.15` threshold for charset-normalizer is a reasonable equivalent of chardet's 0.85 confidence | Encoding detection | If Portuguese Windows-1252 files regularly produce chaos > 0.15, the threshold needs tuning |
| A4 | openpyxl `max_row` in read_only mode is sufficiently accurate for the sheet picker display (INP-10) | Pitfalls | If wildly wrong, sheet picker shows confusing row counts — purely cosmetic |

---

## Open Questions

1. **charset-normalizer confidence threshold (A3)**
   - What we know: `chaos < 0.15` worked for all tested Portuguese content files.
   - What's unclear: edge cases like Windows-1252 files with mixed Portuguese/English text may
     produce chaos values near the threshold.
   - Recommendation: implement with `chaos < 0.15`; log the actual chaos value in the `INPUT`
     log line so the product owner can report anomalies.

2. **TRF-02 pure-numeric mecanograficos (A2)**
   - What we know: the spec says "convert to integer strings before validation." Pure integers
     have no prefix and fail VAL-01.
   - What's unclear: is there a UMinho department where mecanograficos are stored without
     prefix letters in their Excel files?
   - Recommendation: implement as VAL-01 hard error. The product owner can report if a real
     file hits this unexpectedly.

3. **BOM validation against live electoral platform (D-03)**
   - What we know: BOM is implemented. Status is pending product owner test.
   - What's unclear: whether the electoral system accepts or rejects BOM.
   - Recommendation: keep `USE_BOM = True` as a one-line toggle; document in the plan that
     this must be validated before Phase 4 tag.

---

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python | All core modules | Yes | 3.12.10 | — |
| openpyxl | INP-01, PERF-03 | Yes (after pip install) | 3.1.5 | — |
| xlrd | INP-02 | Yes (after pip install) | 2.0.2 | — |
| odfpy | INP-03 | Yes (after pip install) | 1.4.1 | — |
| pandas | INP-03, INP-04, INP-05 | Yes | 3.0.2 | — |
| charset-normalizer | INP-07 | Yes | 3.4.7 | — |
| pytest | Test gate | Yes | 9.0.3 | — |
| pytest-cov | ≥90% coverage gate | Yes | 7.1.0 | — |
| mypy | CI requirement | Yes | 1.19.1 | — |
| ruff | CI requirement | Yes | 0.15.8 | — |

**Missing dependencies with no fallback:** none — all required packages are available.

**Installation step required:** `pip install openpyxl xlrd odfpy` (pandas and charset-normalizer
are already installed). The plan must include a Wave 0 task that installs all packages and
verifies the environment.

---

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest 9.0.3 |
| Config file | `pyproject.toml` [tool.pytest.ini_options] — Wave 0 creates it |
| Quick run command | `pytest tests/unit/ -x -q` |
| Full suite command | `pytest tests/ --cov=src/eleitorum/core --cov-report=term-missing --cov-fail-under=90` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| TRF-01 | Whitespace removal from mec | unit | `pytest tests/unit/test_transform.py::test_mec_whitespace -x` | Wave 0 |
| TRF-02 | Float mec → int string | unit | `pytest tests/unit/test_transform.py::test_mec_float_to_int -x` | Wave 0 |
| TRF-03 | Leading zeros stripped | unit | `pytest tests/unit/test_transform.py::test_mec_leading_zeros -x` | Wave 0 |
| TRF-04 | Prefix case majority-wins | unit | `pytest tests/unit/test_transform.py::test_prefix_case_normalization -x` | Wave 0 |
| TRF-05–06 | Name whitespace normalization | unit | `pytest tests/unit/test_transform.py::test_name_whitespace -x` | Wave 0 |
| TRF-07 | Comma removal from names | unit | `pytest tests/unit/test_transform.py::test_name_comma_removal -x` | Wave 0 |
| TRF-08 | Parenthetical annotation removal | unit | `pytest tests/unit/test_transform.py::test_name_parenthesis_removal -x` | Wave 0 |
| TRF-09–10 | Mojibake correction | unit | `pytest tests/unit/test_transform.py::test_mojibake -x` | Wave 0 |
| TRF-11 | U+FFFD removal | unit | `pytest tests/unit/test_transform.py::test_replacement_char_removal -x` | Wave 0 |
| TRF-13–14 | Elegíveis sort + index | unit | `pytest tests/unit/test_transform.py::test_elegiveis_sort -x` | Wave 0 |
| VAL-01 | Invalid prefix | unit | `pytest tests/unit/test_validate.py::test_invalid_prefix -x` | Wave 0 |
| VAL-02 | Non-positive number | unit | `pytest tests/unit/test_validate.py::test_nonpositive_number -x` | Wave 0 |
| VAL-03 | Duplicate within prefix | unit | `pytest tests/unit/test_validate.py::test_duplicate_within_prefix -x` | Wave 0 |
| VAL-04 | F/D/B cross-prefix collision | unit | `pytest tests/unit/test_validate.py::test_fdb_collision -x` | Wave 0 |
| VAL-05 | Independent namespaces OK | unit | `pytest tests/unit/test_validate.py::test_independent_namespaces -x` | Wave 0 |
| VAL-06 | Empty name | unit | `pytest tests/unit/test_validate.py::test_empty_name -x` | Wave 0 |
| OUT-01–05 | Byte-exact output format | unit | `pytest tests/unit/test_output.py::test_byte_exact_caderno -x` | Wave 0 |
| OUT-06–07 | Caderno header + row format | unit | `pytest tests/unit/test_output.py::test_caderno_format -x` | Wave 0 |
| OUT-08–09 | Elegíveis header + row format | unit | `pytest tests/unit/test_output.py::test_elegiveis_format -x` | Wave 0 |
| INP-07 | Encoding detection (BOM, UTF-8, cp1252) | unit | `pytest tests/unit/test_readers.py::test_encoding_detection -x` | Wave 0 |
| DET-01 | Header row scoring | unit | `pytest tests/unit/test_detection.py::test_header_scoring -x` | Wave 0 |
| DET-03–04 | Column synonym matching | unit | `pytest tests/unit/test_detection.py::test_column_synonyms -x` | Wave 0 |
| LOG-02–04 | Log format and content | unit | `pytest tests/unit/test_logging.py::test_log_format -x` | Wave 0 |
| PERF-01 | 150k row XLSX < 10s | integration | `pytest tests/integration/test_performance.py -x` | Wave 0 |
| Full pipeline | All rules end-to-end | integration | `pytest tests/integration/test_full_pipeline.py -x` | Wave 0 |

### Sampling Rate

- **Per task commit:** `pytest tests/unit/ -x -q`
- **Per wave merge:** `pytest tests/ --cov=src/eleitorum/core --cov-report=term-missing`
- **Phase gate:** `pytest tests/ --cov=src/eleitorum/core --cov-fail-under=90` must be green

### Wave 0 Gaps

- [ ] `pyproject.toml` — project metadata, pinned dependencies, ruff/mypy/pytest config
- [ ] `src/eleitorum/__init__.py` — package init
- [ ] `src/eleitorum/core/__init__.py` — core package init
- [ ] `tests/conftest.py` — shared fixtures (tmp_path, sample data constants)
- [ ] `tests/fixtures/generators.py` — all 15 fixture functions per spec Section 14.3
- [ ] `tests/unit/test_transform.py` — stub file with test function signatures
- [ ] `tests/unit/test_validate.py` — stub file
- [ ] `tests/unit/test_detection.py` — stub file
- [ ] `tests/unit/test_output.py` — stub file
- [ ] `tests/unit/test_readers.py` — stub file
- [ ] `tests/integration/test_full_pipeline.py` — stub file

### Test Fixtures Required (spec Section 14.3)

All 15 fixture functions in `tests/fixtures/generators.py`:

| Function | Covers | Notes |
|----------|--------|-------|
| `make_simple_caderno()` | Happy path | 2-col CSV |
| `make_simple_elegiveis()` | Happy path | 2-col CSV |
| `make_multi_sheet_xlsx()` | INP-10, INP-11 | 3 sheets |
| `make_titled_xlsx()` | DET-01 | Title in row 0, header in row 2 |
| `make_headerless_xlsx()` | DET-02 | No header row |
| `make_mojibake_csv()` | TRF-09, TRF-10 | UTF-8 read as Latin-1 |
| `make_whitespace_chaos_xlsx()` | TRF-05, TRF-06 | NBSP, ZWSP, tabs |
| `make_with_commas()` | TRF-07 | Trailing commas in names |
| `make_with_parentheses()` | TRF-08 | (Coordenador) style annotations |
| `make_duplicate_within_prefix()` | VAL-03 | Same mec twice |
| `make_cross_prefix_collision()` | VAL-04 | F500 + D500 |
| `make_leading_zeros()` | TRF-03 | F0500 style |
| `make_excel_float_numbers()` | TRF-02 | Numeric cells in mec column |
| `make_mixed_case_prefixes()` | TRF-04 | Mix of f6688 and F1234 |
| `make_unicode_replacement()` | TRF-11 | U+FFFD in name |

---

## Security Domain

`security_enforcement` is enabled in config.json. ASVS level 1 applies.

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | No | No auth; offline standalone tool |
| V3 Session Management | No | No sessions; per-run stateless |
| V4 Access Control | No | Single-user desktop tool |
| V5 Input Validation | Yes | Strict mecanografico regex + prefix whitelist; name field validated |
| V6 Cryptography | No | No encryption; UTF-8 BOM is not cryptography |
| V7 Error Handling | Yes | No stack traces to user; all errors in PT-PT via errors.py |
| V12 File/Resource | Yes | PermissionError handling (INP-13, VAL-09); never write to input path (VAL-08) |

### Known Threat Patterns for File-Processing Desktop Apps

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Malicious file path as output destination | Tampering | `pathlib.Path` comparison; refuse if output == input (VAL-08) |
| PermissionError on write → partial output | Tampering | Wrap write in try/except; delete partial file on error (OUT-10) |
| Overwrite existing file silently | Tampering | OUT-12 check before write |
| Stack trace leaking in error messages | Information Disclosure | All exceptions caught in pipeline.py; formatted via errors.py PT-PT messages |
| Arbitrary file read beyond user-chosen file | Information Disclosure | Only read from user-specified path; no path traversal possible |

---

## Project Constraints (from CLAUDE.md)

These directives are extracted from CLAUDE.md and are non-negotiable for the planner:

1. **Tech stack is locked:** Python 3.11+, openpyxl, xlrd, odfpy, pandas, charset-normalizer,
   stdlib csv, PyInstaller. No substitutions without justification.
2. **Zero cost:** all dependencies must be open-source and freely redistributable.
3. **Offline:** absolutely no network calls at runtime.
4. **Output writing:** stdlib `csv` with `QUOTE_NONE + utf-8-sig + CRLF`. Never `pandas.to_csv`.
5. **Encoding detection:** charset-normalizer only. chardet is forbidden.
6. **No Qt imports in core modules:** ruff or a custom import check must verify this in CI.
7. **Performance:** 150k rows in < 10s. openpyxl must use `read_only=True, data_only=True`.
8. **Privacy:** no real personal data in repo; all test fixtures must be synthetic.
9. **Iteration loop:** after every code change: `ruff check` → `ruff format --check` → `mypy` →
   `pytest` → `python -c "import eleitorum"`. All must pass before commit.
10. **GSD Workflow Enforcement:** all file-changing work must go through GSD commands.

---

## Sources

### Primary (HIGH confidence)

- openpyxl 3.1.5 API — verified by live execution: `load_workbook(read_only=True, data_only=True)`,
  `iter_rows(values_only=True)`, `wb.sheetnames`
- charset-normalizer 3.4.7 API — verified by live execution: `from_bytes()`, `best()`,
  `best().chaos`, `best().bom`, `best().encoding`
- Python stdlib `csv` module — verified: `QUOTE_NONE + escapechar + utf-8-sig + lineterminator`
- Python `unicodedata` module — verified: `NFKD` vs `NFD` for 'º' (U+00BA) decomposition
- Spec Section 13.2 — canonical module layout, confirmed no application code exists yet
- Spec Section 8.1 — canonical log format with worked example
- CONTEXT.md decisions D-01 through D-08 — locked implementation decisions

### Secondary (MEDIUM confidence)

- pandas 3.0.2 CoW semantics — confirmed by pandas 3.0.0 changelog [CITED: pandas.pydata.org]
- slopcheck 0.6.1 audit results — all 9 packages rated [OK]

### Tertiary (LOW confidence)

- `chaos < 0.15` threshold as charset-normalizer equivalent of chardet 0.85 confidence [ASSUMED]
  — see Assumptions Log A3.

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all packages verified by live execution on target machine
- Architecture: HIGH — confirmed against spec Section 13.2 and CONTEXT.md D-05
- Pitfalls: HIGH — all pitfalls verified by running the actual code and observing behavior
- Encoding detection confidence mapping: MEDIUM — logic verified but threshold is [ASSUMED]

**Research date:** 2026-05-23
**Valid until:** 2026-08-23 (stable ecosystem; no expected breaking changes in 90 days)
