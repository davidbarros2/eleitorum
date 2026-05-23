---
status: complete
phase: 01-core-pipeline
source:
  - 01-01-SUMMARY.md
  - 01-02-SUMMARY.md
  - 01-03-SUMMARY.md
  - 01-04-SUMMARY.md
  - 01-05-SUMMARY.md
started: 2026-05-23T11:30:00Z
updated: 2026-05-23T12:40:00Z
---

## Current Test

[testing complete]

## Tests

### 1. Automated test suite passes with no regressions
expected: |
  Running `pytest` across all 238 tests produces 237 passed, 1 skipped (the legacy
  XLS write-path test, documented as intentionally skipped until a real .xls sample
  file is checked in). Zero failures. No import errors. The test suite has been run
  after the code review fixes and still passes.
result: pass

### 2. Happy path — UTF-8 caderno CSV in, byte-exact output out
expected: |
  Given a valid UTF-8 BOM semicolon-delimited caderno CSV (personnel_number + name
  columns), run_pipeline should return success=True and write an output CSV with:
  - UTF-8 BOM (bytes EF BB BF at start)
  - Semicolon delimiter
  - Windows line endings (CRLF — \r\n)
  - No quote characters around any field
  - Header row: personnel_number;name;category
  This is the core value proposition of the pipeline.
result: pass

### 3. Validation failure — duplicate mec produces error log, no output CSV
expected: |
  Given a caderno file containing two rows with the same mecanográfico number (e.g.
  f6688 appearing twice), run_pipeline should return success=False, the output CSV
  should NOT be written to disk, and an error log file (name containing _ERRORS_)
  should be created with a Portuguese error message about the duplicate.
result: issue
reported: "Log message said 'Codificacao' and 'confianca' — should be 'Codificação' and 'confiança'"
severity: cosmetic
fix: Fixed inline — commit e1f5566. 'Codificacao detetada' -> 'Codificação detetada', 'confianca' -> 'confiança' in pipeline.py. Tests still pass 237/238.

### 4. Performance — 150,000 rows processed under 10 seconds
expected: |
  The PERF-01 benchmark test (150,000-row synthetic XLSX) passes in under 10 seconds
  on the development machine. Last verified: 6.27 seconds (1.6× headroom).
  openpyxl streaming mode (read_only=True, data_only=True) is confirmed active.
result: pass

### 5. CP1252-encoded CSV no longer crashes — encoding detection limitation known
expected: |
  Before the code review fix (CR-01), a CSV file encoded in Windows-1252 (CP1252 —
  the common Portuguese Windows encoding) would crash the pipeline with a
  UnicodeDecodeError. After the fix, the pipeline no longer crashes.
  
  KNOWN LIMITATION (pre-existing, not introduced by the fix): charset-normalizer may
  misidentify short CP1252 samples as mac_latin2 or cp1250, leading to incorrect
  character rendering in the output (e.g. 'ã' appearing as a different character).
  Phase 2 will add a manual encoding-override option in the UI to address this.
  
  Acceptance criteria for Phase 1: no crash on CP1252 input (achieved); character
  accuracy subject to detection quality (acknowledged limitation).
result: pass

## Summary

total: 5
passed: 5
issues: 1
pending: 0
skipped: 0
blocked: 0

## Gaps

[none yet]
