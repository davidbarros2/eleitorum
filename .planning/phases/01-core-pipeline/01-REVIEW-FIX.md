---
phase: 01-core-pipeline
fixed_at: 2026-05-23T11:15:00Z
review_path: .planning/phases/01-core-pipeline/01-REVIEW.md
iteration: 1
findings_in_scope: 7
fixed: 6
skipped: 1
status: partial
---

# Phase 01: Code Review Fix Report

**Fixed at:** 2026-05-23T11:15:00Z
**Source review:** .planning/phases/01-core-pipeline/01-REVIEW.md
**Iteration:** 1

**Summary:**
- Findings in scope: 7 (CR-01, CR-02, CR-03, WR-01, WR-02, WR-03, WR-04)
- Fixed: 6
- Skipped: 1 (CR-03 already fixed in codebase)

## Fixed Issues

### CR-01: UnicodeDecodeError crashes pipeline for CP1252/ISO-8859-1 CSV files

**Files modified:** `src/eleitorum/core/readers.py`
**Commit:** 540060c
**Applied fix:** Added `errors="replace"` to the `open()` call for the initial text-mode scan read in `read_csv_like`. The initial pass now tolerates characters that cannot be decoded under the default encoding, allowing the binary sample to be captured and encoding detection to proceed. Step 8 in `_execute_pipeline` then re-reads with the correctly detected encoding.

---

### CR-02: Wrong delimiter used when re-reading CP1252 CSV files

**Files modified:** `src/eleitorum/core/pipeline.py`
**Commit:** ad6997b
**Applied fix:** Changed the fallback delimiter in Step 8's re-read path from `","` to `";"`. The fallback in `_execute_pipeline` now matches the initial read at line 199 (`delimiter=";"`), so CP1252/ISO-8859-1 semicolon-delimited CSV files are parsed correctly on re-read.

---

### WR-01: File handles leaked on iteration error in `read_xlsx`, `read_xls`, and `list_sheets`

**Files modified:** `src/eleitorum/core/readers.py`
**Commit:** cba42e2
**Applied fix:** Wrapped all workbook operations in `try/finally` blocks in four locations: `read_xlsx` (wraps `iter_rows` call), `read_xls` (wraps sheet access and `get_rows`), and both the XLSX and XLS branches of `list_sheets` (wrap the sheet iteration loops). `wb.close()` and `wb_xls.release_resources()` are now guaranteed to execute even when an unexpected exception occurs during iteration.

---

### WR-02: Invalid `sheet_name` raises uncaught `KeyError` or `XLRDError`

**Files modified:** `src/eleitorum/core/readers.py`
**Commit:** 75176ce
**Applied fix:** Added inner `try/except` blocks inside the existing `try/finally` guards from WR-01. In `read_xlsx`, `(KeyError, IndexError)` from `wb.sheetnames[0]` and `wb[chosen_sheet]` is caught and re-raised as `FileAccessError`. In `read_xls`, `(xlrd.biffh.XLRDError, IndexError)` from `sheet_by_name` and `sheet_by_index` is caught and re-raised as `FileAccessError`. The nested structure ensures `wb.close()` / `wb_xls.release_resources()` still executes via the outer `finally`.

---

### WR-03: `_strip_trailing_empty` mutates its argument in place

**Files modified:** `src/eleitorum/core/readers.py`
**Commit:** 9bb7f2c
**Applied fix:** Replaced the `pop()`-based loop with an index scan (`end` pointer) that computes the tail boundary without mutating the input. Returns `rows[:end]` (a new list slice) instead of the mutated input. Updated the docstring to document the non-mutation guarantee explicitly.

---

### WR-04: `make_mojibake_csv` fixture produces three duplicate mecanográfico values

**Files modified:** `tests/fixtures/generators.py`
**Commit:** 6769ac6
**Applied fix:** Changed the list comprehension from iterating over names only (all sharing `f6688`) to iterating over `(mec, name)` tuples with distinct mec values: `f6688`, `f1234`, `f9001`. The fixture can now be used to test TRF-09 mojibake correction without triggering a VAL-03 duplicate-mec validation failure.

---

## Skipped Issues

### CR-03: `EncodingDetectionError(path=None)` produces literal "None" in PT-PT user message

**File:** `src/eleitorum/core/errors.py:128-133`
**Reason:** Already fixed in codebase. The `EncodingDetectionError.__init__` signature already reads `path: pathlib.Path | None = None` and uses `path_display = str(path) if path is not None else "(ficheiro desconhecido)"` with a None-safe format. The REVIEW.md itself notes "The path parameter is already typed as `pathlib.Path | None` per a prior fix." No change was needed.

---

_Fixed: 2026-05-23T11:15:00Z_
_Fixer: Claude (gsd-code-fixer)_
_Iteration: 1_
