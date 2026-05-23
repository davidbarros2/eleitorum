---
phase: 01-core-pipeline
reviewed: 2026-05-23T10:04:46Z
depth: standard
files_reviewed: 23
files_reviewed_list:
  - src/eleitorum/__init__.py
  - src/eleitorum/__main__.py
  - src/eleitorum/config.py
  - src/eleitorum/core/__init__.py
  - src/eleitorum/core/detection.py
  - src/eleitorum/core/errors.py
  - src/eleitorum/core/logging.py
  - src/eleitorum/core/output.py
  - src/eleitorum/core/pipeline.py
  - src/eleitorum/core/readers.py
  - src/eleitorum/core/transform.py
  - src/eleitorum/core/validate.py
  - src/eleitorum/version.py
  - tests/conftest.py
  - tests/fixtures/generators.py
  - tests/integration/test_full_pipeline.py
  - tests/integration/test_performance.py
  - tests/unit/test_detection.py
  - tests/unit/test_errors.py
  - tests/unit/test_logging.py
  - tests/unit/test_output.py
  - tests/unit/test_readers.py
  - tests/unit/test_transform.py
  - tests/unit/test_validate.py
findings:
  critical: 3
  warning: 4
  info: 3
  total: 10
status: issues_found
---

# Phase 01: Code Review Report

**Reviewed:** 2026-05-23T10:04:46Z
**Depth:** standard
**Files Reviewed:** 23
**Status:** issues_found

## Summary

Reviewed the complete Phase 1 core pipeline: 13 source files and 10 test files. The overall structure is solid — error hierarchy, logging format, output byte-exactness, and validation logic are all well-designed. The three critical findings are concentrated in the encoding re-read path in `pipeline.py` and a type contract violation in `errors.py`/`detection.py`. These bugs mean the explicitly documented use case of CP1252/ISO-8859-1 encoded CSV files is completely broken: such files crash the pipeline with an uncaught `UnicodeDecodeError` rather than returning a graceful failure. The delimiter logic that would run if the crash were fixed is also wrong.

---

## Critical Issues

### CR-01: UnicodeDecodeError crashes pipeline for CP1252/ISO-8859-1 CSV files

**File:** `src/eleitorum/core/readers.py:248-258` and `src/eleitorum/core/pipeline.py:197-199`

**Issue:** `read_csv_like` opens the file in text mode with the default `encoding="utf-8-sig"` and no `errors=` parameter (strict mode). For any CP1252 or ISO-8859-1 CSV file containing Portuguese characters (e.g. `nº mec.` with `º` = 0xBA in CP1252), this raises `UnicodeDecodeError` during the `csv.reader` iteration. `run_pipeline`'s outer `except EleitorumError` handler does **not** catch `UnicodeDecodeError` (it is a `ValueError`, not an `EleitorumError`), so the exception propagates uncaught to the caller. The pipeline crashes instead of returning `PipelineResult(success=False)`.

This fully blocks the spec-documented use case of CP1252-encoded electoral roll files. The encoding re-read path in Step 8 of `_execute_pipeline` is explicitly documented (line 234) as handling this use case, but it can never execute because Step 5 crashes first.

**Fix:** In `read_csv_like`, use `errors="replace"` (or `"surrogateescape"`) for the initial scan read so that the binary sample is captured and encoding detection can proceed. Then re-read with the detected encoding (and correct delimiter — see CR-02). Alternatively, restructure `_execute_pipeline` to read only the binary sample in Step 5 for CSV files and defer text decoding until after Step 8.

```python
# Option A: Initial scan read tolerates decode errors
with open(path, encoding=encoding, newline="", errors="replace") as ft:
    reader = csv.reader(ft, delimiter=delimiter)
    rows_initial: list[tuple[Any, ...]] = [tuple(row) for row in reader]
# Then Step 8 re-reads with detected encoding and correct delimiter (see CR-02)
```

---

### CR-02: Wrong delimiter used when re-reading CP1252 CSV files

**File:** `src/eleitorum/core/pipeline.py:238-244`

**Issue:** When encoding detection in Step 8 determines the CSV file is CP1252 or ISO-8859-1, the pipeline re-reads with the correct encoding — but uses a **comma** as delimiter instead of a **semicolon**. Line 241 reads:

```python
delimiter = (
    src.csv_delimiter if src.csv_delimiter else ("\t" if ext == ".tsv" else ",")
)
```

For a `.csv` file without an explicit `csv_delimiter` override, this falls through to `","`. But the EleitorUM default CSV delimiter is `";"` (used in the initial read at line 198: `readers.read_csv_like(src.path, delimiter=";")`). The re-read therefore produces one-column rows containing the full `mec;name` field as a single cell, causing column detection to fail or produce garbage output.

Even if CR-01 were fixed independently, this bug would still corrupt all CP1252 semicolon-delimited CSV files.

**Fix:** Change the fallback delimiter from `","` to `";"` to match the EleitorUM standard:

```python
delimiter = (
    src.csv_delimiter if src.csv_delimiter else ("\t" if ext == ".tsv" else ";")
)
```

---

### CR-03: `EncodingDetectionError(path=None)` produces literal "None" in PT-PT user message

**File:** `src/eleitorum/core/errors.py:128-133` and `src/eleitorum/core/detection.py:155, 171`

**Issue:** `EncodingDetectionError.__init__` has type annotation `path: pathlib.Path` (non-optional), but both callers in `detection.py` pass `path=None`:

- Line 155: `raise EncodingDetectionError(path=None)` (inside `_fallback_chain`)
- Line 171: `raise EncodingDetectionError(path=None)` (empty bytes guard in `detect_encoding`)

The PT-PT message is formatted as:

```python
f"Não foi possível identificar a codificação do ficheiro '{path}'."
```

With `path=None`, the user sees: `"Não foi possível identificar a codificação do ficheiro 'None'."` — a Python literal appearing in a user-facing error message. This violates the spec invariant that user messages must never expose Python internals or technical terms.

In practice this only triggers for empty input files (the fallback chain never exhausts because `iso-8859-1` decodes all byte values), but the contract violation is real.

**Fix:** Either make `path` optional with a None-safe format, or pass a meaningful description when path is unknown:

```python
# In errors.py
def __init__(self, path: pathlib.Path | None) -> None:
    path_str = str(path) if path is not None else "(ficheiro desconhecido)"
    message_pt = (
        f"Não foi possível identificar a codificação do ficheiro '{path_str}'. "
        "Tente abri-lo e guardá-lo novamente em UTF-8."
    )
    super().__init__(message_pt, path=str(path) if path is not None else None)
```

---

## Warnings

### WR-01: File handles leaked on iteration error in `read_xlsx`, `read_xls`, and `list_sheets`

**File:** `src/eleitorum/core/readers.py:133-152, 166-188, 301-318, 320-341`

**Issue:** The openpyxl workbook and xlrd workbook objects are opened but `wb.close()` / `wb_xls.release_resources()` is only called at the end of the normal execution path — there is no `try/finally` guard. If `ws.iter_rows()` (line 143), `sheet.get_rows()` (line 179), or the sheet-iteration loops in `list_sheets` raise any unexpected exception (e.g., a corrupted cell triggers an openpyxl internal error), the file handle is never released. On Windows this prevents the file from being deleted or reopened until the process exits.

**Fix:** Wrap workbook operations in `try/finally`:

```python
# read_xlsx example
try:
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
except PermissionError as err:
    raise FileAccessError(path=path, mode="read") from err
except FileNotFoundError as err:
    raise FileAccessError(path=path, mode="read") from err

try:
    chosen_sheet = sheet_name or wb.sheetnames[0]
    ws = wb[chosen_sheet]
    raw: list[tuple[Any, ...]] = list(ws.iter_rows(values_only=True))
finally:
    wb.close()
```

---

### WR-02: Invalid `sheet_name` raises uncaught `KeyError` or `XLRDError`

**File:** `src/eleitorum/core/readers.py:141-142, 173`

**Issue:** In `read_xlsx`, if the caller passes a `sheet_name` that does not exist in the workbook, `wb[chosen_sheet]` raises `KeyError` (line 142). If `wb.sheetnames` is empty (corrupted workbook), `wb.sheetnames[0]` raises `IndexError` (line 141). In `read_xls`, `wb_xls.sheet_by_name(sheet_name)` raises `xlrd.biffh.XLRDError` for a non-existent sheet (line 173). None of these are caught or translated to `FileAccessError` or a new `EleitorumError` subclass. They propagate as raw Python exceptions through the pipeline's `except EleitorumError` handler, crashing the caller.

Phase 2 will expose sheet selection via UI, making this a real-world path.

**Fix:** Catch `KeyError`, `IndexError`, and `xlrd.biffh.XLRDError` and translate them to an appropriate `EleitorumError`:

```python
try:
    chosen_sheet = sheet_name or wb.sheetnames[0]
    ws = wb[chosen_sheet]
except (KeyError, IndexError) as err:
    wb.close()
    raise FileAccessError(path=path, mode="read") from err
```

---

### WR-03: `_strip_trailing_empty` mutates its argument in place

**File:** `src/eleitorum/core/readers.py:102-115`

**Issue:** `_strip_trailing_empty` calls `rows.pop()` on its input list, mutating the caller's list. The function then returns the same mutated object. The docstring says "Returns the surviving rows list and the count of dropped rows" without mentioning the mutation. All current callers construct a new list immediately before calling (so the mutation is harmless), but the implicit side-effect is fragile: any future caller passing a list they still reference after the call will find it silently modified.

**Fix:** Either document the mutation explicitly in the docstring and function name (e.g. rename to `strip_trailing_empty_inplace`), or eliminate the mutation by iterating from the tail without pop:

```python
def _strip_trailing_empty(rows: list[tuple[Any, ...]]) -> tuple[list[tuple[Any, ...]], int]:
    """Strip trailing empty rows. Returns a new list and count. Does NOT mutate input."""
    end = len(rows)
    while end > 0 and _is_empty_row(rows[end - 1]):
        end -= 1
    count = len(rows) - end
    return rows[:end], count  # slice creates a new list
```

---

### WR-04: `make_mojibake_csv` fixture produces three duplicate mecanográfico values

**File:** `tests/fixtures/generators.py:242-266`

**Issue:** All three data rows in `make_mojibake_csv` use the mecanográfico `f6688`:

```python
rows_utf8 = [
    f"f6688;{name}\r\n"
    for name in ["João Silva Teste", "Maria Costa Exemplo", "Ana Pereira Sintetica"]
]
```

Running this fixture through the caderno pipeline will always produce a `VAL-03` duplicate validation failure, making the fixture non-functional for its documented purpose ("Tests TRF-09 deterministic mojibake correction"). The integration test `test_mojibake_file_corrected_end_to_end` explicitly avoids this fixture for this reason, but the fixture remains in the codebase unused and misleading. No test imports `make_mojibake_csv`.

**Fix:** Assign distinct mec values to each row:

```python
rows_utf8 = [
    f"{mec};{name}\r\n"
    for mec, name in [
        ("f6688", "João Silva Teste"),
        ("f1234", "Maria Costa Exemplo"),
        ("f9001", "Ana Pereira Sintetica"),
    ]
]
```

---

## Info

### IN-01: `normalize_mecanografico_case` has an unused `transforms` parameter

**File:** `src/eleitorum/core/transform.py:201-204`

**Issue:** The function signature is `normalize_mecanografico_case(transforms: list[TransformResult], raw_prefix_strings: list[str])`. The `transforms` parameter is never accessed in the function body — only `raw_prefix_strings` is used. All callers pass `[]` for `transforms`. The `TransformResult` import in tests (`from eleitorum.core.transform import TransformResult`) exists partly because of this signature. The parameter adds noise to the public API.

**Fix:** Remove the unused parameter or add a comment explaining why it exists if it is reserved for future use.

---

### IN-02: Misleading comment in `_write_entries` about BOM-lazy-write behaviour

**File:** `src/eleitorum/core/logging.py:234-235`

**Issue:** The comment reads: `"utf-8-sig writes BOM lazily only when the first character is flushed — write an empty string to trigger it"`. This is inaccurate. Python's `utf-8-sig` codec writes the BOM on the first `write()` call regardless of whether the string is empty or not — `f.write("")` does produce the BOM (`b'\xef\xbb\xbf'`). The code works correctly, but the explanation is wrong and would mislead future maintainers into thinking the `f.write("")` call has a special role it does not have in the general case.

**Fix:** Update the comment to accurately describe the behavior:

```python
# Write BOM even for empty log files. utf-8-sig emits the BOM on the first
# write() call. This explicit write('') ensures the BOM is present when
# the entries list is empty.
f.write("")
```

---

### IN-03: `readers.py` comment incorrectly documents TRF-02 as float-to-int conversion

**File:** `src/eleitorum/core/readers.py:163-165`

**Issue:** The comment in `read_xls` states: `"TRF-02 in transform.py handles the 14891.0 -> 14891 conversion downstream."` This is incorrect. `transform_mecanografico` in `transform.py` raises `MecanograficoError` for all pure float inputs (lines 116-125) — there is no float-to-int conversion. The test `test_excel_float_numbers_converted_logged` confirms this: it expects the pipeline to **fail** validation, not succeed with a converted value.

**Fix:** Update the comment to accurately describe the actual behavior:

```python
# Note: xlrd cells carry typed .value attributes. Numeric cells return a Python float.
# A pure float (e.g. 14891.0) has no alphabetic prefix and is rejected by
# transform_mecanografico (MecanograficoError: "número sem prefixo").
# If the source file stores mec values as numbers without a prefix, the user
# must correct the source file.
```

---

_Reviewed: 2026-05-23T10:04:46Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
