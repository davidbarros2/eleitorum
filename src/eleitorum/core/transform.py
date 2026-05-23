"""Transformation module: all 15 TRF rules for mecanográfico and name values.

All functions are pure (no I/O side-effects). The module has zero Qt dependencies.

Transformation ordering for transform_name:
  1. NFC normalization (cosmetic — keeps text predictable)
  2. try_fix_mojibake (TRF-09/10)
  3. remove_replacement_characters (TRF-11)
  4. Strip parenthetical annotations (TRF-08)
  5. Remove commas (TRF-07)
  6. Strip + collapse all Unicode whitespace including NBSP, ZWSP (TRF-05, TRF-06)
  7. Preserve case (TRF-12) — no transformation

TRF-04 (case normalization) is a batch operation. The pipeline:
  1. Calls transform_mecanografico on every row → collects list of (prefix, num, changes).
  2. Collects the original prefix substrings as a separate list.
  3. Calls normalize_mecanografico_case once after all rows.
  4. Applies the chosen case when writing each row to output.

This is non-negotiable — see CONTEXT.md Pitfall 4.
"""

from __future__ import annotations

import dataclasses
import re
import unicodedata
from typing import Any, Literal

from eleitorum.core.errors import MecanograficoError

# ---------------------------------------------------------------------------
# Module-level constants (D-08)
# ---------------------------------------------------------------------------

VALID_PREFIXES: frozenset[str] = frozenset({"A", "PG", "ID", "F", "D", "B", "Q", "EX"})
FDB_SHARED: frozenset[str] = frozenset({"F", "D", "B"})

_MEC_PATTERN: re.Pattern[str] = re.compile(r"^([A-Za-z]{1,2})(\d+)$")
_MOJIBAKE_PAT: re.Pattern[str] = re.compile(r"\xc3[\x80-\xbf]")  # Pattern 3
_REPLACEMENT_CHAR: str = "�"  # U+FFFD
_PAREN_PAT: re.Pattern[str] = re.compile(r"\s*\([^)]*\)\s*")  # TRF-08
# Python's \s matches NBSP (U+00A0) but NOT ZWSP (U+200B, category Cf).
# Per TRF-05/06: must strip all Unicode whitespace-like characters.
# We extend the pattern with an explicit character class covering:
#   \s  — standard Python whitespace (space, tab, \n, \r, \f, \v, U+00A0 NBSP)
#   ​ — ZERO-WIDTH SPACE
#   ‌ — ZERO-WIDTH NON-JOINER
#   ‍ — ZERO-WIDTH JOINER
#   ﻿ — ZERO-WIDTH NO-BREAK SPACE (BOM when appearing mid-string)
_WHITESPACE_PAT: re.Pattern[str] = re.compile(r"[\s​‌‍﻿]+")  # includes NBSP, ZWSP, ZWJ, ZWNJ, BOM


# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------


@dataclasses.dataclass(frozen=True)
class ChangeRecord:
    """A single field-level transformation record for logging.py."""

    row_index: int  # 1-based source row (for log); 0 = batch-level
    field: Literal["mecanografico", "name"]
    rule_tag: Literal["LIMPEZA", "CASO", "AVISO"]
    before: str
    after: str
    reason_pt: str  # one-line PT-PT description for the log


@dataclasses.dataclass(frozen=True)
class TransformResult:
    """Result of a single row's transformation (mecanografico + name)."""

    prefix: str  # UPPERCASE for canonical comparison (case is normalized later)
    number: int  # positive int, leading zeros stripped
    name: str  # cleaned name
    changes: list[ChangeRecord]  # all per-row changes for logging.py


# ---------------------------------------------------------------------------
# Mecanográfico transformation — TRF-01, TRF-02, TRF-03
# ---------------------------------------------------------------------------


def transform_mecanografico(raw: Any, row_index: int) -> tuple[str, int, list[ChangeRecord]]:
    """TRF-01, TRF-02, TRF-03. Returns (UPPERCASE_PREFIX, positive_int, changes).

    Raises MecanograficoError(row_index, value, reason) for:
      - None/empty input
      - Pure float (no prefix — TRF-02 only applies when the float IS the numeric part
        of a valid mec string, but a raw float cell has no prefix at all)
      - Pure integer (no prefix)
      - Invalid format (does not match prefix+digits pattern)
      - Invalid prefix (VAL-01)
      - Non-positive number (VAL-02)

    Case normalization (TRF-04) is NOT applied here — it is a batch operation;
    see normalize_mecanografico_case below.
    """
    changes: list[ChangeRecord] = []

    # None / empty
    if raw is None:
        raise MecanograficoError(row_index, str(raw), "valor em falta")

    # Pure integer: no prefix → invalid (e.g., Excel stores mec as integer)
    if isinstance(raw, int) and not isinstance(raw, bool):
        raise MecanograficoError(
            row_index,
            str(raw),
            f"número sem prefixo — o número mecanográfico deve incluir o prefixo (ex.: F{raw})",
        )

    # Pure float: if it is a whole number (e.g., 14891.0), it still has no prefix
    if isinstance(raw, float):
        if raw == int(raw):
            raise MecanograficoError(
                row_index,
                str(raw),
                f"número sem prefixo — o número mecanográfico deve incluir o prefixo "
                f"(ex.: F{int(raw)})",
            )
        else:
            raise MecanograficoError(row_index, str(raw), "valor decimal inválido")

    # Stringify
    s_original = str(raw)

    if not s_original.strip():
        raise MecanograficoError(row_index, s_original, "valor em falta")

    # TRF-01: remove all whitespace (not just leading/trailing — spaces inside are also invalid)
    s_nows = re.sub(r"\s+", "", s_original)
    if s_nows != s_original:
        changes.append(
            ChangeRecord(
                row_index=row_index,
                field="mecanografico",
                rule_tag="LIMPEZA",
                before=s_original,
                after=s_nows,
                reason_pt="Espaços removidos do número mecanográfico",
            )
        )
    s = s_nows

    # Pattern match
    m = _MEC_PATTERN.match(s)
    if not m:
        raise MecanograficoError(
            row_index,
            s_original,
            "formato inválido — o número mecanográfico deve ser prefixo + número (ex.: F500)",
        )

    prefix_raw = m.group(1)
    num_str = m.group(2)
    prefix = prefix_raw.upper()

    # TRF-03: strip leading zeros from the numeric part
    stripped = num_str.lstrip("0") or "0"
    if stripped != num_str:
        changes.append(
            ChangeRecord(
                row_index=row_index,
                field="mecanografico",
                rule_tag="LIMPEZA",
                before=s_original,
                after=prefix + stripped,
                reason_pt=f"Zeros iniciais removidos: '{num_str}' → '{stripped}'",
            )
        )

    # VAL-01: prefix must be in VALID_PREFIXES
    if prefix not in VALID_PREFIXES:
        raise MecanograficoError(
            row_index,
            s_original,
            f"prefixo inválido — '{prefix}'. Prefixos válidos: "
            + ", ".join(sorted(VALID_PREFIXES)),
        )

    # VAL-02: number must be positive
    num = int(stripped)
    if num <= 0:
        raise MecanograficoError(
            row_index,
            s_original,
            "número não positivo — o número mecanográfico deve ser maior ou igual a 1",
        )

    return (prefix, num, changes)


# ---------------------------------------------------------------------------
# Batch case normalization — TRF-04
# ---------------------------------------------------------------------------


def normalize_mecanografico_case(
    transforms: list[TransformResult],
    raw_prefix_strings: list[str],
) -> tuple[Literal["lower", "upper"], int, int, ChangeRecord]:
    """TRF-04. Count lowercase vs uppercase across raw_prefix_strings.

    Returns (chosen_case, lower_count, upper_count, ChangeRecord).
    Tie → 'lower' (D-08 default).

    This function ONLY decides; the caller applies the result when writing
    output rows.
    """
    lower_count = 0
    upper_count = 0

    for s in raw_prefix_strings:
        if s.islower():
            lower_count += 1
        elif s.isupper():
            upper_count += 1
        else:
            # Mixed case: vote based on first character
            if s and s[0].islower():
                lower_count += 1
            else:
                upper_count += 1

    chosen: Literal["lower", "upper"] = "upper" if upper_count > lower_count else "lower"

    change_record = ChangeRecord(
        row_index=0,  # batch-level marker
        field="mecanografico",
        rule_tag="CASO",
        before=f"{lower_count} minúsculas vs {upper_count} maiúsculas",
        after=chosen,
        reason_pt=(
            f"Normalização de prefixos: {chosen} "
            f"({lower_count} minúsculas vs {upper_count} maiúsculas)"
        ),
    )

    return (chosen, lower_count, upper_count, change_record)


# ---------------------------------------------------------------------------
# Mojibake detection/correction — TRF-09, TRF-10 (Pattern 3)
# ---------------------------------------------------------------------------


def try_fix_mojibake(s: str) -> tuple[str, bool]:
    """RESEARCH.md Pattern 3.

    Returns (corrected, was_fixed). Detects U+00C3 followed by a char in
    0x80–0xBF range; round-trips via latin-1 → utf-8; accepts only if no
    remaining mojibake pattern. Otherwise returns (s, False).
    """
    if not _MOJIBAKE_PAT.search(s):
        return s, False
    try:
        fixed = s.encode("latin-1").decode("utf-8")
        if not _MOJIBAKE_PAT.search(fixed):
            return fixed, True
        return s, False
    except (UnicodeEncodeError, UnicodeDecodeError):
        return s, False


# ---------------------------------------------------------------------------
# Replacement character removal — TRF-11
# ---------------------------------------------------------------------------


def remove_replacement_characters(s: str) -> tuple[str, int]:
    """TRF-11. Removes every U+FFFD individually; returns (cleaned, count_removed)."""
    count = s.count(_REPLACEMENT_CHAR)
    if count == 0:
        return s, 0
    return s.replace(_REPLACEMENT_CHAR, ""), count


# ---------------------------------------------------------------------------
# Name transformation — TRF-05, TRF-06, TRF-07, TRF-08, TRF-09, TRF-10, TRF-11, TRF-12
# ---------------------------------------------------------------------------


def transform_name(raw: Any, row_index: int) -> tuple[str, list[ChangeRecord]]:
    """TRF-05 through TRF-12. Applies transformations in this order:

    1. NFC normalization (cosmetic)
    2. try_fix_mojibake (TRF-09/10)
    3. remove_replacement_characters (TRF-11)
    4. Strip parenthetical annotations (TRF-08)
    5. Remove commas (TRF-07)
    6. Strip + collapse all Unicode whitespace (TRF-05, TRF-06)
    7. Preserve case (TRF-12) — no transformation

    Returns (cleaned_name, changes). Empty result is NOT raised here — VAL-06
    is validate.py's responsibility.
    """
    if raw is None:
        return ("", [])

    changes: list[ChangeRecord] = []
    s = str(raw)

    # Step 1: NFC normalization (cosmetic)
    s = unicodedata.normalize("NFC", s)

    # Step 2: TRF-09/10 mojibake
    s2, fixed = try_fix_mojibake(s)
    if fixed:
        changes.append(
            ChangeRecord(
                row_index=row_index,
                field="name",
                rule_tag="LIMPEZA",
                before=s,
                after=s2,
                reason_pt="Corrupção de codificação (mojibake) corrigida automaticamente",
            )
        )
        s = s2
    elif _MOJIBAKE_PAT.search(s):
        # Pattern matched but round-trip didn't clean — ambiguous mojibake
        suspicious = _MOJIBAKE_PAT.findall(s)
        changes.append(
            ChangeRecord(
                row_index=row_index,
                field="name",
                rule_tag="AVISO",
                before=s,
                after=s,
                reason_pt=(
                    f"Possível corrupção de codificação não corrigida "
                    f"(sequência suspeita: {suspicious!r})"
                ),
            )
        )

    # Step 3: TRF-11 replacement characters
    s3, removed = remove_replacement_characters(s)
    if removed > 0:
        changes.append(
            ChangeRecord(
                row_index=row_index,
                field="name",
                rule_tag="AVISO",
                before=s,
                after=s3,
                reason_pt=(f"Removido(s) {removed} carácter(es) de substituição (U+FFFD) do nome"),
            )
        )
        s = s3

    # Step 4: TRF-08 parenthetical annotations
    # Use re.findall to capture what we're removing for the log message
    parens_found = re.findall(r"\([^)]*\)", s)
    s4 = _PAREN_PAT.sub(" ", s).strip()
    if s4 != s:
        changes.append(
            ChangeRecord(
                row_index=row_index,
                field="name",
                rule_tag="LIMPEZA",
                before=s,
                after=s4,
                reason_pt=(
                    f"Anotação(ões) entre parênteses removida(s): {', '.join(parens_found)}"
                ),
            )
        )
        s = s4

    # Step 5: TRF-07 commas
    s5 = s.replace(",", "")
    if s5 != s:
        changes.append(
            ChangeRecord(
                row_index=row_index,
                field="name",
                rule_tag="LIMPEZA",
                before=s,
                after=s5,
                reason_pt="Vírgula(s) removida(s) do nome",
            )
        )
        s = s5

    # Step 6: TRF-05/06 whitespace — Python \s matches NBSP (U+00A0), ZWSP (U+200B), tab, etc.
    s6 = _WHITESPACE_PAT.sub(" ", s).strip()
    if s6 != s:
        changes.append(
            ChangeRecord(
                row_index=row_index,
                field="name",
                rule_tag="LIMPEZA",
                before=s,
                after=s6,
                reason_pt="Espaços em branco normalizados (espaços Unicode, tabs, NBSP, etc.)",
            )
        )
        s = s6

    # Step 7: TRF-12 case — no transformation (preserve as-is)

    return (s, changes)


# ---------------------------------------------------------------------------
# Sort key and sort function — TRF-13, TRF-14, TRF-15
# ---------------------------------------------------------------------------


def _designation_sort_key(s: str) -> str:
    """D-02 NFKD diacritic-stripped casefold key for elegíveis sorting."""
    return unicodedata.normalize("NFKD", s.casefold()).encode("ascii", "ignore").decode("ascii")


def sort_elegiveis(rows: list[tuple[int, str]]) -> list[tuple[int, str]]:
    """TRF-13, TRF-14.

    Input: list of (row_index, designation) tuples.
    Sort by D-02 NFKD diacritic-stripped casefold key.
    Assign 0-based output_index by enumerate() after sort.
    Return list of (output_index, designation) tuples.

    Caderno output skips this function entirely — see TRF-15.
    """
    sorted_rows = sorted(rows, key=lambda pair: _designation_sort_key(pair[1]))
    return [(i, designation) for i, (_, designation) in enumerate(sorted_rows)]
