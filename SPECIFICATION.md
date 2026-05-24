# EleitorUM — Project Specification

## 0. About This Document

This is the canonical specification for **EleitorUM**, a desktop utility for normalizing
electoral roll and eligibility list files used at Universidade do Minho. It is the
single source of truth for AI development assistants (Claude Code, get-shit-done, or any
similar agent) working on this project.

**Audience:** AI development agents and human contributors who need to understand or
modify the project.

**Conventions:**

- This document is in English. The product itself (UI, messages, logs) is in
  **European Portuguese (PT-PT), idiomatic**.
- The product owner is a non-coder. All technical decisions not explicitly fixed below
  are delegated to the AI assistant. When in genuine doubt that affects the project's
  direction, present options to the product owner with a clear recommendation rather
  than guessing.
- "Must" / "Required" — non-negotiable.
- "Should" — strong preference; deviate only with clear justification.
- "May" — implementation choice left to the agent.

**How to read this:** Section 1 explains what we are building and why. Sections 2–9
define the contract (inputs, outputs, rules, UI). Sections 10–17 cover engineering
practice. Section 18 lists what was decided during the conceptual phase. New
contributors should read Sections 0–9 in order, then jump to whatever is relevant.

**On scope creep:** The product is intentionally narrow. Do one thing well: receive
an arbitrary input file, validate it, transform it into the exact format required by
the electoral system, save the result. Resist the temptation to add features outside
this scope.

---

## 1. Project Overview

### 1.1. The problem

A staff member at Universidade do Minho regularly receives files from various
departments containing electoral roll data (`cadernos eleitorais`) and eligibility
lists (`listas de elegíveis`). The electoral platform that consumes this data
accepts only a strict, narrow file format. Submitted files are almost always in
some other format: different headers, different encoding, multi-sheet Excel
workbooks, extra columns, whitespace issues, character corruption, etc.

Today this normalization is done manually with Excel and Notepad. It is tedious,
error-prone, and time-consuming. The same problems recur with every new file.

### 1.2. The solution

A small, focused Windows desktop application with a simple wizard interface that:

1. Asks the user which type of output to generate (electoral roll or eligibility list).
2. Accepts any file readable by Excel (XLSX, XLSM, XLS, ODS, CSV, TSV).
3. Detects encoding, columns, and structure automatically (with manual override).
4. Validates the data against well-defined rules.
5. Transforms the data into the strict required output format.
6. Saves the result to a location chosen by the user, never overwriting the original.
7. Produces a detailed transformation log so the user can audit what was changed.

### 1.3. Who it's for

- **Primary user:** the staff member responsible for preparing electoral files at
  Universidade do Minho. Comfortable with Windows and Excel but not a developer.
- **Secondary user:** colleagues or successors who might inherit this responsibility.

### 1.4. Non-goals

The product is **not**:

- A general-purpose CSV/Excel tool.
- A duplicate-detection tool across multiple files (the program processes one input
  at a time).
- A data-entry application (no manual editing of rows in the UI).
- A network-connected service (no telemetry, no auto-update calls, no cloud).
- A multi-platform application (Windows only).
- A long-lived, iterating product. See 1.5 below.

### 1.5. Project lifecycle

This project is **single-version, set-and-forget**:

- Development proceeds through whatever internal phases the agent finds useful
  until v1.0.0 is reached.
- At v1.0.0 the product ships. No MVPs, no beta releases, no iterative rollouts.
- After v1.0.0 the project is **archived**. No v1.1, no v2, no maintenance
  releases, no feature additions, no bug-fix iterations unless a showstopper
  bug is found in v1.
- The agent should make implementation choices accordingly. Do not invest in
  extensibility hooks, plugin systems, abstract base classes "for future
  flexibility", or configurability that has no v1 use case. Build the v1 the
  product needs and stop.

### 1.6. Success criteria

A run of the program is successful when:

- The output file is byte-perfect to the format specified in Section 5.
- All input quirks listed in Section 6 are handled correctly.
- The user has a clear, granular log of every transformation applied.
- The user can take the output and submit it to the electoral system without further
  manual fixing.

---

## 2. Tech Stack & Constraints

### 2.1. Stack

- **Language:** Python (3.11 or newer).
- **GUI framework:** PySide6 (Qt for Python, LGPL).
- **Spreadsheet I/O:** `openpyxl` (XLSX/XLSM), `xlrd` (legacy XLS), `odfpy` (ODS).
- **Data wrangling:** `pandas` for input normalization, plain `csv` module from the
  standard library for output (to control byte-level format precisely).
- **Encoding detection:** `chardet` or `charset-normalizer`.
- **Packaging:** PyInstaller into a single-folder or one-file Windows executable.

The agent may substitute any of these libraries if there is a clearly better
zero-cost alternative, with justification.

### 2.2. Hard constraints

- **Zero cost.** No paid libraries, no paid services, no paid fonts. Everything
  open-source and freely redistributable. License compatibility must be verified for
  every dependency.
- **Standalone.** The end user must be able to run the program by either (a)
  double-clicking a single `.exe`, or (b) running an installer that produces the
  same. No Python install, no pip, no terminal, no dependency resolution by the user.
- **Offline.** The program must function with no network access. No telemetry, no
  update checks, no analytics, no external HTTP calls of any kind.
- **Portable preferred.** A single-file or single-folder portable build is
  preferred over an installer. If an installer is provided, it must be optional and
  not the only distribution form.
- **Windows is the target.** Builds must be tested on Windows 10 and Windows 11.

### 2.3. Performance targets

- The largest expected input is around **150,000 rows**, but the program should not
  hard-fail above this — only become slow.
- Processing 150,000 rows from XLSX to validated CSV output should complete in
  **under 10 seconds** on a typical office laptop.
- UI must remain responsive during processing (use a background thread for the work).

---

## 3. Project Identity

### 3.1. Name

The project is named **EleitorUM**. The name is composed of *Eleitor* (voter in
Portuguese) and *UM* (Universidade do Minho's abbreviation). It is the application's
display name, executable name, repository name, and the basis for the icon glyph.

The name **must be trivially changeable** in the future. Implementation requirements:

- Define a single constant `APP_NAME` in a central configuration module (e.g.,
  `eleitorum/config.py` or `eleitorum/branding.py`). All UI labels, window titles,
  log file names, and About dialog references must read from this constant.
- The icon file should be regeneratable from a single source (see 3.4) so changing
  the displayed letter requires editing one file.
- The repository name itself, the package name (`eleitorum`), and the executable
  filename will require coordinated changes; document these locations in a
  `RENAMING.md` file at the repository root so any future renaming is a checklist
  rather than a search.

### 3.2. Visual identity

The visual identity draws from Universidade do Minho's official graphic norms while
remaining independent of and not officially endorsed by the university (see 3.5).

**Color palette — Light theme:**

| Role | Hex | Notes |
|---|---|---|
| Background | `#FAFAFA` | Soft white, not pure |
| Surface (cards, panels) | `#FFFFFF` | |
| Primary text | `#1A1A1A` | |
| Secondary text | `#878787` | UMinho secondary grey |
| Accent / Primary action | `#a21a1c` | UMinho red |
| Accent hover | `#8a1618` | Slightly darker |
| Borders, dividers | `#E5E5E5` | |
| Success | `#2E7D32` | |
| Warning | `#ED6C02` | |
| Error | `#a21a1c` | Reuses UMinho red |

**Color palette — Dark theme:**

| Role | Hex | Notes |
|---|---|---|
| Background | `#1A1A1A` | Not pure black |
| Surface | `#262626` | |
| Primary text | `#F5F5F5` | |
| Secondary text | `#A3A3A3` | |
| Accent | `#C73E40` | UMinho red lightened for WCAG AA contrast on dark |
| Accent hover | `#D85759` | |
| Borders, dividers | `#3A3A3A` | |
| Success | `#66BB6A` | |
| Warning | `#FFA726` | |
| Error | `#C73E40` | |

Both themes must meet **WCAG AA contrast** for all text/background combinations.

### 3.3. Typography

- **Primary font:** **Inter** (Open Font License, free). Bundled with the
  application so it renders identically regardless of system fonts installed.
- **Fallback chain:** Inter → system UI font → sans-serif.
- Do not use UMinho's official institutional fonts (News Gothic T, Gotham); they
  are proprietary and cannot be redistributed.

### 3.4. Logo / icon

A type-glyph mark: the letter **E** in white, centered on a rounded-corner red
square (`#a21a1c`), 16% corner radius. Generated from a single SVG source file.
Multiple PNG/ICO sizes exported from it during build. Replacing the letter or the
color requires editing only the source SVG and rerunning the export.

---

## 4. Input Support

### 4.1. Supported file types

The program accepts as input **any file that Excel can open**:

| Extension | Library | Notes |
|---|---|---|
| `.xlsx` | openpyxl | Primary modern format |
| `.xlsm` | openpyxl | Macro-enabled, treated as XLSX |
| `.xls` | xlrd | Legacy binary format, **read-only** support |
| `.ods` | odfpy or pandas with `engine="odf"` | OpenDocument |
| `.csv` | csv + chardet | Encoding auto-detected |
| `.tsv` | csv + chardet | Same as CSV, tab-separated |

Any other extension must produce a **clear error message** explaining that the
file type is not supported and listing the accepted formats.

### 4.2. Encoding detection

For text-based inputs (CSV, TSV):

1. Read the first ~64 KB of bytes.
2. Run encoding detection (chardet or charset-normalizer).
3. If confidence is high (>= 0.8), use that encoding.
4. If low, try in order: UTF-8 with BOM, UTF-8 without BOM, Windows-1252,
   ISO-8859-1, and pick the first that decodes without errors and produces
   plausible Portuguese characters.
5. If all fail, error with a clear message: "Não foi possível identificar a
   codificação do ficheiro. Tente abri-lo e guardá-lo novamente em UTF-8."

The detected encoding **must be logged** as part of the transformation log.

### 4.3. Multi-sheet handling

When the input is an Excel file with more than one sheet:

- The wizard inserts an extra step between "upload" and "column detection" where
  the user is shown all sheet names and chooses one.
- The user processes one sheet per run. To produce multiple output files from a
  multi-sheet workbook, the user runs the program multiple times.
- Sheets that contain no usable data (entirely empty, or only title rows with no
  tabular data below) should still be listed but flagged with a small "sheet
  vazia" hint so the user knows.

### 4.4. Header row detection

The header row is not always row 0. Some inputs have title rows or blank rows
before the actual header. Strategy:

1. For each candidate row in the first 10 rows of the sheet:
   - Compute the count of cells that look like headers (non-empty, short text,
     non-numeric).
   - Compute the count of cells that match any known synonym for "personnel
     number" or "name" (see 6.5).
2. The row with the highest "header-likeness" score is the header row.
3. If no plausible header row is found, treat the file as headerless and ask the
   user to manually map columns (see 6.5).

### 4.5. Column detection

After identifying the header row, the program looks for the relevant columns
using a tolerant matcher (see 6.5). The detection result is shown to the user,
who can confirm or override.

---

## 5. Output Specifications

These specifications are **fixed and non-negotiable**. They were extracted by
inspecting working files accepted by the electoral system.

### 5.1. Common output properties (both file types)

| Property | Value |
|---|---|
| Encoding | **UTF-8 with BOM** (the 3 bytes `0xEF 0xBB 0xBF` at the start) |
| Field separator | `;` (semicolon) |
| Line endings | `\r\n` (CRLF, Windows-style) |
| Quoting | **None.** Fields are written literally, with no surrounding quotes |
| Trailing newline | Yes — the file ends with `\r\n` after the last data row |
| Header row | Yes, present as the first line |

### 5.2. Caderno eleitoral (electoral roll)

**Header (literal, exact):**

```
personnel_number;name;category
```

**Per-row format:** `{mecanográfico};{nome};` — the third field (`category`) is
**always empty**. Each row ends with a `;` followed by `\r\n`.

**Example:**

```
personnel_number;name;category
f6688;David André Moreira Lopes de Barros;
ex5205;David André Moreira Lopes de Barros;
f7065;Elsa Filomena Lopes Moura;
```

**Row ordering:** preserved from the input. The caderno does **not** sort.

### 5.3. Elegíveis (eligibility list)

**Header (literal, exact):**

```
personnel_number;designation
```

**Per-row format:** `{index};{designation}` where `{index}` is a non-negative
integer starting at 0, incremented by 1 per row.

**Row ordering:** **alphabetically ascending** by `designation`. The `index`
is assigned **after** sorting (so row 0 is always the alphabetically first
entry).

**Example:**

```
personnel_number;designation
0;Carla Isabel Gomes Grenha
1;Clara Sofia Rocha Pinto Moreira
2;David André Moreira Lopes de Barros
3;Elsa Filomena Lopes Moura
```

**Note on `designation` content:** the field can contain person names *or*
non-person designations (e.g., parish names like `Gualtar`, `São Vítor`,
`Padim da Graça`). Short values (e.g., `Sé` with 2 characters) are valid.

### 5.4. Choosing the output type vs input content

The user chooses the **output type** to generate (caderno or elegíveis) before
uploading the file. The input file's original purpose is irrelevant — only its
data matters.

- For **caderno eleitoral output**, the input must yield both a mecanográfico
  column and a name column.
- For **elegíveis output**, the input only needs to yield a name column (the
  index is generated by the program). Any other columns in the input are ignored.

If the user picks "caderno" but the input has no usable mecanográfico data, the
program errors out clearly. It never invents data.

---

## 6. Transformation Rules

### 6.1. Mecanográfico format

A valid mecanográfico is composed of a **prefix** followed by a **positive
integer**, with no separator.

**Valid prefixes:** `A`, `PG`, `ID`, `F`, `D`, `B`, `Q`, `EX`.

**Case:** prefixes are case-insensitive when read. The output normalizes case
across all mecanográficos in the run to a single chosen case (see 6.2).

**Number portion rules:**

- Must be a positive integer (≥ 1).
- No leading zeros in the canonical form: `F500`, not `F0500` or `F00500`.
- If the input contains leading zeros, strip them and log the change.
- A mecanográfico whose number is 0 or all-zeros (e.g., `F0`, `D00`) is invalid
  and must produce a clear error.

**Whitespace rules:**

- No spaces between prefix and number, before the prefix, or after the number.
- Trim and remove internal whitespace silently, logging the change.

### 6.2. Case normalization for mecanográficos

After cleaning all mecanográficos in the input:

1. Count how many would be in **lowercase canonical form** if normalized
   (i.e., count entries that arrived already in lowercase).
2. Count how many would be in **uppercase canonical form**.
3. Use the majority case for the entire output.
4. If tied, default to **lowercase**.
5. The chosen case is logged at the top of the transformation log.

### 6.3. Mecanográfico uniqueness rules

- **Within the same prefix**, no duplicates allowed. If `A500` appears twice,
  this is an error.
- **Across prefixes F, D, and B**, the numeric portion shares a single namespace.
  If `F500`, `D500`, or `B500` appear in any combination in the same input,
  this is an error. (This reflects how mecanográficos are issued at UMinho:
  the F/D/B groups draw from a single pool.)
- **Prefixes A, PG, ID, Q, and EX** each have independent namespaces. `A500`
  and `PG500` in the same input is **fine**.

When a uniqueness violation is detected, processing stops, no output file is
created, and the user is shown a clear message identifying the conflicting rows.

### 6.4. Name format

Names are treated **as-is for capitalization** — the program does not normalize
case. If the input has `MÓNICA RITA DA VENDA LIRA` (all caps), the output has
`MÓNICA RITA DA VENDA LIRA`. If the input has `georgina margarida martins
araujo`, the output has the same. This is deliberate: the program does not alter
the substance of names, only their formatting.

**Whitespace normalization:**

- Strip all leading and trailing whitespace.
- Collapse any sequence of whitespace within the name to a single space.
- Whitespace here includes ASCII space, tab (`\t`), no-break space (` `),
  zero-width space (`​`), and any Unicode character classified as whitespace.

**Accents and special characters:**

- Preserve all accents and diacritics as-is.
- If a character is corrupted in a **deterministic** way (mojibake — see 6.6),
  auto-correct it.
- If a character is corrupted in a **non-deterministic** way (e.g., a Unicode
  replacement character `�`, or unparseable bytes), **remove that single
  character** while keeping the rest of the name intact, and log the removal.

**Commas:**

- Commas are not expected in names. If a comma is found, **remove it** and log
  the removal. (Decision made after observing only accidental trailing commas in
  real data, e.g., `Maria Manuela Marques Raposo,`.)

**Parenthetical annotations:**

- Content enclosed in parentheses is not expected to be part of a name. If
  present, **remove both the parentheses and their contents**, then re-apply
  whitespace normalization. Log the removal showing what was removed. (Decision
  made after observing `Rui Manuel Sá Pereira Lima (Coordenador)` in real data.)

**Empty names:** if a row has a mecanográfico but no name (or vice versa for
caderno output), this is an error. Stop processing.

### 6.5. Column detection (tolerant matching)

Inputs use a wide variety of column names. The program detects columns by
matching against a list of synonyms, normalized (trimmed, lowercased, accent-
stripped) for comparison.

**Synonyms for mecanográfico column:**

- `personnel_number`
- `nº mecanográfico`, `numero mecanografico`, `n mecanografico`,
  `n. mecanografico`, `n.º mec.`, `nº mec.`, `nº mec`, `n.º mec`, `nº. mec.`
- `nº necanográfico` (observed typo)
- `nmec`, `nmecanografico`
- `numero de empregado`, `número de empregado`
- `codigo`, `código`
- `numaluno`, `num aluno`, `n aluno`

**Synonyms for name column:**

- `name`
- `nome`, `nome completo`, `nome de empregado`, `nome aluno`, `nomealuno`
- `aluno`
- `designation`, `designação`

If detection is ambiguous (multiple plausible columns) or fails entirely, the
user is presented with a column-mapping dialog showing the input's column names
and dropdowns to choose which corresponds to mecanográfico and which to name.

### 6.6. Mojibake auto-correction

Mojibake is what happens when text encoded in UTF-8 is incorrectly decoded as
Windows-1252 or ISO-8859-1 (or vice versa). It produces deterministic, easily
recognizable patterns:

| Original | Mojibake (UTF-8 read as Latin-1) |
|---|---|
| `é` | `Ã©` |
| `ã` | `Ã£` |
| `ç` | `Ã§` |
| `á` | `Ã¡` |
| `í` | `Ã­` |
| `ó` | `Ã³` |
| `ú` | `Ãº` |
| `Á` | `Ã` (yes, capital A with tilde-like; less common) |

The program detects mojibake by:

1. Scanning each string for the characteristic patterns (`Ã` followed by a
   single character in the 0x80–0xBF range, or specific combinations).
2. If found, attempt to re-encode the string: take the string as Latin-1 bytes,
   then decode as UTF-8. If the result contains valid Portuguese characters and
   no longer matches mojibake patterns, accept the correction and log it.

If correction is ambiguous (the result doesn't decode cleanly), **do not
correct** — log the suspicious string for human attention.

### 6.7. Excel numeric quirks

- Numbers stored as numeric type in Excel may appear as floats (`14891.0`).
  When the mecanográfico column contains numeric values, convert them to
  integer strings before applying validation. Log this conversion.
- Excel may strip leading zeros automatically. The program cannot recover these
  if Excel has already done it before reading, but if a CSV input has leading
  zeros they will be visible and stripping is handled in 6.1.

### 6.8. Trailing empty rows

Excel often persists empty rows at the bottom of a sheet. After identifying the
header row and data range, skip any rows where **all relevant columns** are
empty. Do not error on these; just ignore them. Log the count of skipped empty
rows.

---

## 7. Validation & Error Handling

### 7.1. Philosophy

The program follows a **fail-fast, never-partial** philosophy:

- If any error is encountered during validation or transformation, processing
  stops immediately.
- **No output file is created** when there is an error. Partial outputs would
  be dangerous (the user might submit them by mistake).
- An **error log file** is created alongside where the output would have been,
  with a name like `{output_name}_ERRORS_{timestamp}.txt`. This log contains
  full details of every error found.
- The UI shows a clear summary of the errors with line/row references.

### 7.2. Error categories

| Category | Behavior | Examples |
|---|---|---|
| Unsupported file type | Stop, clear message at upload step | `.docx`, `.pdf` |
| Cannot read file | Stop, clear message | Corrupted file, file open in Excel, no permissions |
| Cannot detect encoding | Stop, clear message | Highly mangled CSV |
| No header row found and user dismisses mapping | Stop | |
| Required column missing | Stop, clear message naming the column | Caderno output but no mecanográfico column |
| Mecanográfico with invalid prefix | Stop, list offending rows | `X500` (X is not a valid prefix) |
| Mecanográfico with number 0 or empty | Stop, list offending rows | `F0`, `D` |
| Duplicate mecanográfico within prefix | Stop, list offending rows | `A500` twice |
| Cross-prefix collision F/D/B | Stop, list offending rows | `F500` and `D500` together |
| Empty name | Stop, list offending rows | |
| Unreadable character with no certain correction | Continue but log; user reviews in preview | `�` in a name |
| Output destination is the input file | Stop, clear message | User tried to overwrite |
| Output destination is open in Excel | Stop, clear message | "Feche o ficheiro no Excel e tente novamente." |

### 7.3. Error message style

All error messages must be:

- Written in idiomatic European Portuguese.
- Specific (which row, which column, what value).
- Actionable (tell the user what to do next).
- Free of technical jargon. The user does not know what "UTF-8" or "BOM" means;
  surface only what affects their action.

Example of a good error message:

> O ficheiro contém dois números mecanográficos repetidos:
>
> - Linha 47: `f6688` (David André Moreira Lopes de Barros)
> - Linha 102: `f6688` (Maria Costa Silva)
>
> Cada número mecanográfico só pode aparecer uma vez. Corrija o ficheiro de
> origem e tente novamente.

Example of a bad error message:

> ValueError: duplicate key 'f6688' in dataframe column 'personnel_number'.

---

## 8. Logging

### 8.1. Transformation log

A granular, per-change log is produced during every run. It is shown in the
final wizard step (the "result" screen) and saved as a `.txt` file next to the
output CSV, with a name pattern like `{output_name}_LOG_{timestamp}.txt`.

**Format:** plain text, UTF-8 with BOM (consistent with the output CSV), one
event per line. Each line starts with a timestamp and a short tag, then the
description.

**Example:**

```
[2026-05-23 14:32:15] INICIO  Tipo de output: caderno eleitoral
[2026-05-23 14:32:15] INPUT   Ficheiro: cadernos_originais.xlsx
[2026-05-23 14:32:15] INPUT   Codificação detetada: UTF-8 com BOM (confiança 0.99)
[2026-05-23 14:32:15] INPUT   Folha selecionada: "Folha1" (247 linhas, 5 colunas)
[2026-05-23 14:32:15] COLUNA  Coluna "Nº Mec." detetada como número mecanográfico
[2026-05-23 14:32:15] COLUNA  Coluna "Nome" detetada como nome
[2026-05-23 14:32:15] CASO    Normalização de prefixos: minúsculas (215 minúsculas vs 32 maiúsculas)
[2026-05-23 14:32:16] LIMPEZA Linha 12: removido espaço inicial em "  Maria Santos"
[2026-05-23 14:32:16] LIMPEZA Linha 45: removido espaço final em "João Silva "
[2026-05-23 14:32:16] LIMPEZA Linha 78: número "12345 " normalizado para "12345"
[2026-05-23 14:32:16] LIMPEZA Linha 91: vírgula removida do nome "Marta Oliveira,"
[2026-05-23 14:32:16] LIMPEZA Linha 103: anotação "(Coordenador)" removida do nome "Rui Pereira (Coordenador)"
[2026-05-23 14:32:16] LIMPEZA Linha 127: mojibake corrigido — "JoÃ£o" → "João"
[2026-05-23 14:32:16] AVISO   Linha 156: carácter ilegível removido do nome (sem correção certa)
[2026-05-23 14:32:16] SAIDA   Ficheiro gerado: caderno_2026.csv (245 linhas)
[2026-05-23 14:32:16] FIM     Processamento concluído com sucesso. 18 alterações.
```

Tags used: `INICIO`, `INPUT`, `COLUNA`, `CASO`, `LIMPEZA`, `AVISO`, `ERRO`,
`SAIDA`, `FIM`.

### 8.2. Error log

When processing fails, an error log is produced instead of the transformation
log. Same naming convention but with `_ERRORS_` instead of `_LOG_`. Same format
but with `ERRO` lines describing each problem.

### 8.3. Log scope

- **No personal data leaves the user's machine.** The log file is written only
  to the location the user chose for the output. It is never sent anywhere.
- **No logs are written to system temp directories** unless explicitly required
  for a transient operation that the user has consented to.

---

## 9. User Interface

### 9.1. Overall principles

- **Wizard pattern** with sequential steps. One thing at a time, clear forward
  progress.
- **PT-PT idiomatic.** No machine-translated phrasing. No anglicisms unless they
  are the natural Portuguese term (e.g., "encoding" is acceptable in technical
  contexts; "drag and drop" is not — use "arrastar e largar").
- **No surprise.** Every action the user takes has a clear preview before
  commitment. No destructive defaults.
- **No data lost.** Never overwrite the input file. Never overwrite the output
  file silently — if a file with the destination name exists, prompt for
  confirmation or auto-rename.

### 9.2. Language

All user-facing strings (window titles, button labels, wizard step copy, log
tags, error messages, About dialog) are written directly in European
Portuguese. No translation framework is set up — the product ships in
Portuguese only and stays in Portuguese only.

For consistency, all UI strings are still **centralized in one module per
area** (e.g., `eleitorum/ui/strings.py`) rather than scattered throughout the
code. This makes proof-reading and idiomatic-phrasing review easier during
development.

### 9.3. Window behavior

- Standard window chrome: minimize, maximize, close, resize from any edge or
  corner.
- Supports Windows snap layouts (Win+Arrow, drag to corners, Win+Z on Win 11).
- **Minimum window size:** 600 × 500 pixels.
- **Initial window size:** 900 × 650 pixels, centered on the primary monitor.
- **Persisted state:** the last window size and position are saved on close
  (via `QSettings`) and restored on next launch. Also persisted: last directory
  used for opening/saving, theme choice (light/dark).
- **Resize behavior:** all content reflows using Qt layouts. No hard-coded
  pixel positions. Test that the UI is usable at the minimum size and at all
  snap positions.

### 9.4. Theming

- A toggle (icon button in the header or a menu item) switches between **light
  and dark** themes.
- Default on first launch: **follow system theme** if detectable; otherwise
  light.
- Theme choice is persisted.
- Theme switching is instant — no application restart required.

### 9.5. Wizard flow — full specification

The wizard has 5 (or 6, in the multi-sheet case) sequential steps. Each step
has:

- A clear title at the top.
- The relevant content area in the middle.
- A footer with **Anterior** / **Próximo** buttons (and **Cancelar** to abort).
- A subtle step indicator (e.g., "Passo 2 de 5") in the header or footer.

**Step 1 — Escolher tipo de output**

Two large, clear options:

- `Caderno Eleitoral` (icon + short description: "Lista de votantes elegíveis a
  participar numa eleição")
- `Lista de Elegíveis` (icon + description: "Lista de candidatos ou opções
  disponíveis numa eleição")

Selecting one moves to step 2. Anterior is disabled (this is the first step).

**Step 2 — Carregar ficheiro**

A central drop zone with text "Arraste o ficheiro para aqui" and below it a
button "ou escolher ficheiro…". Both methods produce the same effect — the
selected file path is shown and the wizard advances.

Accepted extensions are filtered in the native file dialog. Drop zone rejects
unsupported types with a brief inline error.

The drop zone should be a clearly visible bordered area, large enough to make
the drag target obvious, with a hover state.

**Step 2.5 — Escolher folha (only if multi-sheet)**

A list of sheet names with the number of rows in each. The user selects one and
proceeds. Empty sheets are listed but shown in a muted style.

**Step 3 — Confirmar mapeamento de colunas**

The wizard shows the detected column mapping:

- "A coluna **Nº Mec.** será usada como número mecanográfico." (with a green
  check icon if confident, or a yellow icon if guessed)
- "A coluna **Nome** será usada como nome."

For elegíveis output, only the name mapping is shown.

The user can click "Alterar" next to either mapping to open a dropdown showing
all available columns and pick a different one.

If the program could not detect a mapping at all, this step begins in
"manual mapping" mode with dropdowns active and a friendly message: "Não foi
possível detetar as colunas automaticamente. Por favor, escolha quais usar."

**Step 4 — Pré-visualização**

A scrollable table showing the first ~50 rows of the **transformed** output,
exactly as it will be written to the file (header row included, formatting
applied).

Above the table, a summary panel:

- Total rows: N
- Transformations applied: M (with a "Ver detalhes" link that expands the log)
- Issues that need your attention: K (visible only if K > 0)

If issues exist (e.g., characters removed without certain correction), they are
highlighted in the table and called out in the summary.

The Próximo button reads "Escolher destino e gravar".

**Step 5 — Escolher destino**

A native save-file dialog opens. The default filename is suggested based on the
input filename and the output type, e.g., `caderno_2026.csv`. The default
directory is the last used directory.

The dialog enforces a `.csv` extension. If the chosen destination is the
input file's path, the wizard refuses and prompts for a different location.

Once a destination is confirmed, the wizard writes the output file and the
log file. This step is briefly modal during the write (which should complete
in well under a second for typical inputs).

**Step 6 — Concluído**

A success screen with:

- A large success icon and "Pronto!"
- The path to the output file (with a "Abrir pasta" button that opens Windows
  Explorer at that location).
- A summary of what was done (rows processed, transformations applied).
- A button to "Processar outro ficheiro" that restarts the wizard from step 1.
- A button to "Sair" that closes the program.

If errors were encountered (and processing stopped before reaching this step),
the user is shown an error screen with the same layout but the success icon
replaced by an error icon, the message replaced by a clear summary, and the
"Abrir pasta" button pointing to the error log file.

### 9.6. Menu bar and About dialog

A minimal menu bar:

- **Ficheiro** — Sair
- **Ver** — Toggle Tema Claro/Escuro
- **Ajuda** — Sobre…

The About dialog shows:

- App name and version
- One-line description
- UMinho disclaimer (from 3.5)
- Open-source license note (linking to the LICENSE file)
- Credit / link to the source repository

### 9.7. Accessibility

- All interactive elements reachable by keyboard.
- Tab order follows visual order.
- Focus indicators clearly visible in both themes.
- All icons paired with text labels (no icon-only buttons in the main flow).
- Color is not the only signal — success/warning/error always paired with a
  glyph or text.

---

## 10. User Journeys

### 10.1. Happy path — simple CSV, single sheet

1. User opens the program.
2. Picks "Caderno Eleitoral".
3. Drags `lista_docentes.csv` into the drop zone.
4. Confirms detected columns.
5. Reviews preview (everything looks right).
6. Picks destination, clicks save.
7. Success screen. Done in under a minute.

### 10.2. Multi-sheet Excel

1. User picks "Caderno Eleitoral".
2. Drops `cadernos_provisorios.xlsx` (3 sheets: Docentes, PTAG, Alunos).
3. Sheet picker appears. User picks "Docentes".
4. Column detection works automatically.
5. Preview, save, done. Repeats for PTAG and Alunos as separate runs.

### 10.3. File with issues (mojibake + trailing whitespace)

1. User picks "Lista de Elegíveis".
2. Drops a CSV that turns out to be encoded as Windows-1252.
3. Encoding auto-detected; mojibake corrected.
4. Preview shows clean names; summary says "12 alterações aplicadas".
5. User clicks "Ver detalhes" to confirm the changes are sensible.
6. Save, done. Transformation log captures every change.

### 10.4. File rejection (duplicate mecanográfico)

1. User picks "Caderno Eleitoral".
2. Uploads a file with two `f6688` entries.
3. Preview step is replaced with an error screen.
4. Error log file is created at the chosen output location (with
   `_ERRORS_` in the name).
5. User reads the error, fixes the source file, tries again.

### 10.5. Manual column mapping

1. User picks "Caderno Eleitoral".
2. Uploads a file with custom headers like `MeuNumero` and `Pessoa`.
3. Auto-detection fails.
4. Manual mapping dialog appears with dropdowns.
5. User picks `MeuNumero` for mecanográfico and `Pessoa` for nome.
6. Flow continues normally.

---

## 11. First-Run Welcome

Because the project ships once and is archived (see 1.5), v1 must be complete
and self-explanatory. The single optional addition worth including is a
**first-run welcome screen**:

- Shown only the first time the application is launched on a given machine
  (a flag in `QSettings` records that it has been shown).
- A single screen with the project name, a one-paragraph description of what
  it does, a brief outline of the wizard flow, and a button "Começar".
- Accessible afterwards via the **Ajuda** menu.

No other complementary features are in scope. The agent does not implement
recent-files lists, batch processing, plugin systems, or any other extension
beyond what is specified in this document.

---

## 12. Build & Distribution

### 12.1. Build tooling

- **PyInstaller** in one-file mode for the simplest user experience. If the
  resulting `.exe` is unreasonably slow to start (> 3 seconds cold), switch to
  one-folder mode and ship a ZIP.
- Build artifacts are produced by a script `scripts/build.py` that wraps
  PyInstaller with the correct flags and produces a versioned filename like
  `EleitorUM-1.0.0-win64.exe`.
- The icon is embedded in the executable.
- Version information (file version, product name, copyright) is embedded via a
  PyInstaller version file.

### 12.2. Code signing

Code signing certificates cost money and are out of scope. The app will trigger
Windows SmartScreen on first run for some users. Document this in the README
so users know to click "Mais informações" → "Executar mesmo assim" if they
trust the source.

### 12.3. Distribution

The product has a **single public release: v1.0.0**, published on GitHub
Releases. The release page contains:

- The `.exe` file (or ZIP if one-folder).
- SHA-256 checksum of the artifact.
- Manually written release notes summarizing the product.

The README links directly to this release.

### 12.4. Continuous integration

GitHub Actions workflow that runs on push to `main` during the development
phase:

- Install Python and dependencies.
- Run linter (ruff).
- Run formatter check (ruff format).
- Run type checker (mypy or pyright).
- Run the test suite (pytest).
- On the v1.0.0 tag, additionally build the Windows executable, smoke-test it
  (launch + version check), and attach it to the GitHub Release.

All CI runs on the free tier of GitHub Actions. Build matrix: Python 3.11 and
3.12 on `windows-latest`. After v1.0.0 is released, no further CI runs are
expected because no further commits are expected.

---

## 13. Repository Structure & GitHub Setup

### 13.1. Top-level files

| File | Purpose |
|---|---|
| `README.md` | Human-facing intro: what it is, who it's for, screenshots, install instructions, disclaimer, license. Bilingual headers (PT primary, EN summary). Explicitly states the repository is read-only to the public and contributions are not accepted. |
| `LICENSE` | **MIT License**. Permissive, well-known, compatible with all chosen dependencies. |
| `CHANGELOG.md` | Keep-a-Changelog format. Maintained during development phases. Final entry is the v1.0.0 release; no entries beyond that. |
| `CONTRIBUTING.md` | Single short statement: this project does not accept external contributions. The repository is published so the source code is auditable, not so it can be jointly developed. Issues, Pull Requests, and Discussions are disabled at the repository level. |
| `RENAMING.md` | Checklist of every place to touch if the project name changes. |
| `.gitignore` | Python, PyInstaller, IDE, OS, build artifacts. |
| `.gitattributes` | Normalize line endings appropriately per file type. |
| `pyproject.toml` | Project metadata, dependencies, tool configuration. |
| `SPECIFICATION.md` | This document. |

### 13.2. Directory layout

```
eleitorum/
├── README.md
├── LICENSE
├── CHANGELOG.md
├── CONTRIBUTING.md
├── RENAMING.md
├── SPECIFICATION.md
├── pyproject.toml
├── .gitignore
├── .gitattributes
├── .github/
│   └── workflows/
│       ├── ci.yml
│       └── release.yml
├── src/
│   └── eleitorum/
│       ├── __init__.py
│       ├── __main__.py
│       ├── config.py            (APP_NAME, version, paths)
│       ├── branding.py          (colors, font, icon)
│       ├── core/
│       │   ├── readers.py       (per-format input readers)
│       │   ├── detection.py     (encoding, header row, columns)
│       │   ├── transform.py     (mecanográfico + name rules)
│       │   ├── validate.py      (uniqueness, format checks)
│       │   ├── output.py        (CSV writer with exact byte format)
│       │   ├── logging.py       (transformation log builder)
│       │   └── errors.py        (custom exceptions, PT messages)
│       ├── ui/
│       │   ├── app.py           (QApplication setup)
│       │   ├── main_window.py
│       │   ├── wizard.py
│       │   ├── steps/
│       │   │   ├── step_type.py
│       │   │   ├── step_upload.py
│       │   │   ├── step_sheet.py
│       │   │   ├── step_columns.py
│       │   │   ├── step_preview.py
│       │   │   ├── step_save.py
│       │   │   └── step_done.py
│       │   ├── widgets/         (reusable components)
│       │   ├── theme.py         (light/dark palette application)
│       │   └── strings.py       (centralized PT-PT user-facing strings)
│       ├── resources/
│       │   ├── icon.svg         (source of the logo)
│       │   ├── icon.ico         (generated)
│       │   └── fonts/Inter/     (bundled font files)
│       └── version.py
├── tests/
│   ├── conftest.py
│   ├── fixtures/
│   │   └── generators.py        (synthetic file generation)
│   ├── unit/
│   │   ├── test_transform.py
│   │   ├── test_validate.py
│   │   ├── test_detection.py
│   │   └── test_output.py
│   └── integration/
│       └── test_full_pipeline.py
├── scripts/
│   ├── build.py                 (PyInstaller wrapper)
│   └── generate_icons.py        (from icon.svg → multiple PNG/ICO sizes)
└── docs/
    └── user-manual-pt.md        (end-user guide in PT)
```

### 13.3. GitHub repository settings

The repository is a **read-only public mirror** of the work, not a collaboration
space. The agent configures the repository accordingly:

- Default branch: `main`.
- Branch protection on `main`: no force pushes, no direct deletion.
- **Issues: disabled.** No bug reports, no feature requests via GitHub.
- **Pull Requests: effectively disabled.** Since there are no collaborators,
  no external PRs will be reviewed. The CONTRIBUTING.md states this clearly.
  If GitHub UI allows it, PRs from forks are blocked by repository settings;
  otherwise the policy is enforced socially via the CONTRIBUTING.md.
- **Discussions: disabled.**
- **Wiki: disabled** (documentation lives in `docs/`).
- **Sponsorships: disabled.**
- **Projects: disabled.**
- "About" section filled in with a one-line description in PT and a link to
  the UMinho-affiliation disclaimer in the README.
- Topics: `electoral`, `csv`, `desktop-app`, `pyside6`, `python`,
  `portuguese`, `university-of-minho`.
- A `social preview` image generated from the icon for nice cards on shares.
- Release notes for v1.0.0 are written manually from the CHANGELOG.

---

## 14. Testing Strategy

### 14.1. Principles

- **Tests are the primary validation mechanism.** Every change made by the agent
  must keep all tests passing.
- **Fixtures are synthetic.** All test input files are generated by code in
  `tests/fixtures/generators.py` with fictional Portuguese names (e.g.,
  `João Silva Teste`, `Maria Costa Exemplo`) and invented mecanográficos. No
  real personal data ever enters the repository.
- **Coverage targets:** transformation and validation logic ≥ 90% line
  coverage. UI code is exempt from coverage targets but should have at least
  smoke tests for each wizard step.

### 14.2. Test categories

**Unit tests** (`tests/unit/`)

- Each transformation rule (whitespace, comma removal, parenthesis removal,
  mojibake correction, leading-zero strip, etc.) tested in isolation with
  positive and negative cases.
- Each validation rule tested with passing and failing inputs.
- Encoding detection tested with fixtures in UTF-8 (with and without BOM),
  Windows-1252, ISO-8859-1.
- CSV output byte-exact test: write a known input, read raw bytes, compare to
  expected bytes (including BOM and CRLF).

**Integration tests** (`tests/integration/`)

- Full pipeline tests: synthetic input file → run the same code paths the GUI
  uses → assert exact output bytes.
- Edge cases: multi-sheet XLSX, headerless CSV, mojibake-corrupted Latin-1
  file, file with all whitespace types, file with cross-prefix collision
  (should fail), file with duplicates within prefix (should fail), file with
  parenthetical annotations, etc.
- One integration test per non-trivial scenario from Section 10 (user
  journeys).

**Smoke tests** (run only during release builds)

- Build the executable.
- Launch it with `--version` flag (returns version string and exits).
- (Optional, if time permits) automated GUI smoke test using `pytest-qt`.

### 14.3. Synthetic fixture generation

The `tests/fixtures/generators.py` module exports functions that produce, in
memory or as temp files, synthetic input files covering every quirk identified
during the conceptual phase:

| Function | Produces |
|---|---|
| `make_simple_caderno()` | Clean 2-column CSV |
| `make_simple_elegiveis()` | Clean 2-column CSV |
| `make_multi_sheet_xlsx()` | XLSX with Docentes/PTAG/Alunos sheets |
| `make_titled_xlsx()` | XLSX where row 0 is a title and headers are in row 2 |
| `make_headerless_xlsx()` | XLSX with no headers at all |
| `make_mojibake_csv()` | CSV with deterministic UTF-8-read-as-Latin-1 corruption |
| `make_whitespace_chaos_xlsx()` | Names with tabs, NBSP, leading/trailing spaces |
| `make_with_commas()` | Names with accidental trailing commas |
| `make_with_parentheses()` | Names with `(annotations)` |
| `make_duplicate_within_prefix()` | Two rows with the same mecanográfico |
| `make_cross_prefix_collision()` | F500 and D500 in the same file |
| `make_leading_zeros()` | Mecanográficos like `F0500` |
| `make_excel_float_numbers()` | Numeric mecanográficos stored as float |
| `make_mixed_case_prefixes()` | Mix of `f6688` and `F1234` |
| `make_unicode_replacement()` | Name containing `�` |

Fixtures use a small set of fictional Portuguese names defined as constants at
the top of the generators module, so changing them is trivial.

---

## 15. Development Workflow for AI Assistants

### 15.1. Iteration loop

After every code change, the agent runs (in this order):

1. **Linter:** `ruff check .` — must pass with no errors.
2. **Formatter:** `ruff format --check .` — must report no changes needed.
3. **Type checker:** `mypy src/eleitorum` (or `pyright`) — must pass.
4. **Test suite:** `pytest tests/` — must pass entirely.
5. **Smoke import:** `python -c "import eleitorum"` — must succeed.

If any step fails, the agent fixes the failure before considering the change
complete. The agent does **not** ask the human to approve a change that fails
its own checks.

### 15.2. What the agent validates without human input

- All linter / formatter / type / test results.
- Whether new tests pass alongside existing ones.
- Whether a built executable launches and exits cleanly (when building).
- Whether all test fixtures still generate valid example files.
- Whether the user-facing strings are in Portuguese (heuristic: scanning UI code
  for strings that look like English UI text).
- Whether the documentation references match the current code (e.g., function
  names referenced in this spec still exist).

### 15.3. What requires human validation

The agent presents to the human, with step-by-step instructions in lay
Portuguese, only the things a machine cannot judge:

- **Visual / UX decisions.** "Abra o programa, clique no botão de tema escuro,
  e diga-me se o contraste do texto sobre o fundo está confortável de ler."
- **Idiomatic phrasing.** New user-facing strings are listed for the human to
  approve or rephrase.
- **Behavior on real files** the human has on their machine (which never enter
  the repository): "Por favor, abra o programa, carregue o ficheiro X que tem
  no seu computador, e confirme se o preview mostra Y."
- **Decisions about scope.** When two valid implementation approaches exist
  and they meaningfully differ in user experience, the agent lists them with
  pros/cons and a recommendation.

When asking for human validation, the agent provides:

- The exact steps to reproduce (open program → click here → drag this file →
  observe).
- What "good" looks like, in concrete terms.
- A clear question with closed-form answers where possible (yes/no, or A/B/C).

### 15.4. Communication style

- The agent writes in Portuguese when addressing the human (the product owner
  prefers PT). Code and comments stay in English.
- Updates are concise. Status reports list what was done, what was validated,
  and what (if anything) needs human input — nothing else.
- When in doubt, ask. Do not silently guess in domains where a wrong guess
  costs work to undo (file formats, UI flows, naming).

### 15.5. Versioning and release

The project ships exactly once. Versioning works as follows:

- During development the version stays at `0.x.y` in `src/eleitorum/version.py`,
  bumping `y` for incremental work and `x` for meaningful milestone phases the
  agent chooses to define.
- When the product owner declares the work complete and ready to ship, the
  version becomes `1.0.0`. The agent updates the CHANGELOG with the final
  release entry, tags the commit `v1.0.0`, and lets CI build and attach the
  Windows executable to the GitHub Release.
- After `v1.0.0` is released, no further development is expected. The
  repository is then archived via GitHub's "Archive this repository" setting,
  which makes it read-only at the platform level (no commits, no Issues, no
  PRs even if someone tries).
- If a critical, showstopper-level bug is discovered post-archive, the
  repository is temporarily unarchived for a fix and re-released as `v1.0.1`,
  then archived again. This is expected to be rare or never.

---

## 16. Privacy & Security

- **No telemetry. No analytics. No network calls. Ever.** This is a hard
  invariant. Any future change that adds a network call must be flagged
  explicitly and require human approval.
- **Personal data flow:** user input → in-memory processing → output file at
  user-chosen location + log at the same location. No other paths.
- **No data lingers.** The program writes nothing outside the user-chosen
  output location (other than the `QSettings` config, which contains UI
  preferences only — no names, no mecanográficos).
- **The repository is open source and public**, but contains **no real personal
  data**. Test fixtures are synthetic.
- **Dependencies** are kept minimal and audited. The agent runs `pip audit` (or
  equivalent) in CI to surface known CVEs. Vulnerable dependencies are updated
  promptly.

---

## 17. Open Questions & Decisions Pending

One item remains pending validation before v1.0.0 is shipped:

- **BOM in output:** Section 5.1 specifies UTF-8 **with BOM**, inferred from
  the working sample files. The product owner will test BOM vs no-BOM
  submission to the electoral platform during development. If a test shows the
  electoral system rejects BOM, the value flips and this is a one-line change
  in `output.py`.

There are no post-v1 items because there is no post-v1 phase (see 1.5).

---

## 18. Decision Log

A snapshot of decisions made during the conceptual phase of this project, for
context.

**Tech stack and platform**

- Python + PySide6 + PyInstaller, standalone Windows executable.
- Zero-cost requirement: open-source dependencies only.
- Offline: no network calls of any kind.

**Output format**

- UTF-8 with BOM, `;` separator, CRLF line endings, no quoting, trailing
  newline.
- Caderno: `personnel_number;name;category` (category always empty).
- Elegíveis: `personnel_number;designation` (index 0..N, alphabetically
  ordered).

**UI**

- Wizard pattern with sequential steps.
- Drag-and-drop **and** button upload (both supported).
- Preview always shown before save.
- Never overwrites the original or any existing file silently.
- Light and dark themes with toggle.
- PT-PT idiomatic, single language. No internationalization framework.
- Window resizable, snap-layout-friendly, persists size and position.

**Transformation rules**

- Mecanográfico: prefix (A, PG, ID, F, D, B, Q, EX) + positive integer; no
  leading zeros; case normalized by majority (lowercase if tied); no
  duplicates within prefix; no F/D/B cross-prefix collisions.
- Name: capitalization as-is; whitespace normalized (all kinds collapsed and
  trimmed); commas removed; parenthetical annotations removed; mojibake auto-
  corrected when deterministic; unreadable characters removed individually.

**Behavior**

- Multi-sheet inputs: user picks one sheet per run.
- Column detection: automatic with manual override available.
- Errors stop processing immediately; no partial outputs; error log is
  produced.
- Granular per-change transformation log saved alongside the output.

**Identity**

- Name: **EleitorUM** (changeable via single constant).
- Visual identity: UMinho colors (`#a21a1c` red, complementary greys), Inter
  font, glyph icon with red rounded square + white "E".
- Disclaimer: not officially affiliated with UMinho.
- License: MIT.

**Privacy**

- Synthetic test data only.
- No telemetry, no network calls.
- Repository public; real personal data stays on the user's machine.

---
