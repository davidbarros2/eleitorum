"""Detection module: encoding detection, header-row scoring, and column matching.

This module turns raw bytes and raw row tuples into structured layout information:
  - detect_encoding: determines the text encoding of CSV/TSV bytes
  - detect_header_row: scores the first 10 rows to find the header
  - detect_columns: matches header cells to known synonyms (D-01 hybrid approach)

All functions are pure (no I/O side-effects). The module has zero Qt dependencies.
"""

from __future__ import annotations

import dataclasses
import pathlib
import re
import unicodedata
from typing import Any, Literal

from charset_normalizer import from_bytes  # type: ignore[import-untyped]

from eleitorum.core.errors import EncodingDetectionError

# ---------------------------------------------------------------------------
# Module-level constants
# ---------------------------------------------------------------------------

_CONFIDENCE_THRESHOLD: float = 0.85  # INP-07 (D-06)
_CHAOS_THRESHOLD: float = 0.15  # equivalent threshold for charset-normalizer
_ENCODING_FALLBACK_CHAIN: tuple[str, ...] = ("utf-8", "cp1252", "iso-8859-1")
_HEADER_SCAN_WINDOW: int = 10  # first 10 rows for DET-01
_MEC_FORMAT_PATTERN: re.Pattern[str] = re.compile(r"^[A-Za-z]{1,2}\d+$")
_FORMAT_FALLBACK_HIT_RATIO: float = 0.70
_FORMAT_FALLBACK_SAMPLE_ROWS: int = 50


# ---------------------------------------------------------------------------
# normalize_col_name (Pattern 2 — NFKD normalization)
# ---------------------------------------------------------------------------


def normalize_col_name(s: str) -> str:
    """NFKD normalization for tolerant column matching.

    Strips diacritics, lowercases, trims. Critical: uses NFKD (not NFD) because
    NFKD decomposes 'º' (U+00BA ordinal indicator) → 'o'.
    """
    s = s.strip().lower()
    return "".join(c for c in unicodedata.normalize("NFKD", s) if unicodedata.category(c) != "Mn")


# ---------------------------------------------------------------------------
# Synonym sets — built at module load time by normalizing every spec variant
# ---------------------------------------------------------------------------

# Eleitorum.md Section 6.5 — all mecanográfico synonyms
_RAW_MECANOGRAFICO_SYNONYMS: tuple[str, ...] = (
    "personnel_number",
    "nº mecanográfico",
    "numero mecanografico",
    "n mecanografico",
    "n. mecanografico",
    "n.º mec.",
    "nº mec.",
    "nº mec",
    "n.º mec",
    "nº. mec.",
    "nº necanográfico",  # observed typo variant
    "nmec",
    "nmecanografico",
    "numero de empregado",
    "número de empregado",
    "codigo",
    "código",
    "numaluno",
    "num aluno",
    "n aluno",
)

MECANOGRAFICO_SYNONYMS: frozenset[str] = frozenset(
    normalize_col_name(s) for s in _RAW_MECANOGRAFICO_SYNONYMS
)

# Eleitorum.md Section 6.5 — all name synonyms
_RAW_NAME_SYNONYMS: tuple[str, ...] = (
    "name",
    "nome",
    "nome completo",
    "nome de empregado",
    "nome aluno",
    "nomealuno",
    "aluno",
    "designation",
    "designação",
)

NAME_SYNONYMS: frozenset[str] = frozenset(normalize_col_name(s) for s in _RAW_NAME_SYNONYMS)


# ---------------------------------------------------------------------------
# Result dataclasses
# ---------------------------------------------------------------------------


@dataclasses.dataclass(frozen=True)
class EncodingDetectionResult:
    """Result of encoding detection for a CSV/TSV byte stream."""

    encoding: str  # e.g., "utf-8-sig", "utf-8", "cp1252", "iso-8859-1"
    confidence: float  # 0.0–1.0 proxy (1.0 for BOM; 0.5 for fallback chain)
    via_bom: bool  # True if encoding was determined by BOM detection
    raw_chaos: float | None  # charset-normalizer chaos value; None if fallback chain used


@dataclasses.dataclass(frozen=True)
class ColumnMapping:
    """Result of column detection for a header row."""

    mec_col_index: int | None  # column index of mecanográfico; None if not detected
    name_col_index: int | None  # column index of name; None if not detected
    mec_col_label: str | None  # original column label as in source header
    name_col_label: str | None  # original column label
    ambiguous_mec_candidates: list[tuple[int, str]]  # (col_index, label) on ambiguity
    ambiguous_name_candidates: list[tuple[int, str]]
    detection_method: Literal["synonym", "format_fallback", "manual"]


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _canonical_bom_encoding(encoding: str) -> str:
    """Normalize a BOM-detected encoding name to the canonical 'utf-8-sig' form.

    charset-normalizer may report BOM-carrying UTF-8 as "utf_8" with bom=True.
    """
    norm = encoding.lower().replace("-", "").replace("_", "")
    if norm in ("utf8", "utf8sig", "utf8bom"):
        return "utf-8-sig"
    return encoding


def _fallback_chain(raw_bytes: bytes) -> EncodingDetectionResult:
    """Try each encoding in the fallback chain; raise EncodingDetectionError if all fail."""
    for enc in _ENCODING_FALLBACK_CHAIN:
        try:
            raw_bytes.decode(enc)
            return EncodingDetectionResult(
                encoding=enc,
                confidence=0.5,
                via_bom=False,
                raw_chaos=None,
            )
        except (UnicodeDecodeError, LookupError):
            continue
    raise EncodingDetectionError(path=None)


# ---------------------------------------------------------------------------
# detect_encoding (Pattern 4 — charset-normalizer mapping)
# ---------------------------------------------------------------------------


def detect_encoding(raw_bytes: bytes) -> EncodingDetectionResult:
    """Detect encoding for CSV/TSV bytes.

    BOM trusted unconditionally. charset-normalizer used when chaos < 0.15
    (≈ confidence ≥ 0.85). Falls through to UTF-8 → CP1252 → ISO-8859-1.
    Raises EncodingDetectionError if no encoding decodes the sample cleanly.
    """
    if not raw_bytes:
        raise EncodingDetectionError(path=None)

    results = from_bytes(raw_bytes)
    if not results:
        return _fallback_chain(raw_bytes)

    best = results.best()
    if best is None:
        return _fallback_chain(raw_bytes)

    # BOM detected — trust unconditionally
    if best.bom:
        return EncodingDetectionResult(
            encoding=_canonical_bom_encoding(best.encoding),
            confidence=1.0,
            via_bom=True,
            raw_chaos=None,
        )

    # Low chaos → high confidence
    if best.chaos < _CHAOS_THRESHOLD:
        # Normalize common encoding name variants
        enc = best.encoding
        enc_norm = enc.lower().replace("-", "").replace("_", "")
        if enc_norm in ("windows1252", "cp1252"):
            enc = "cp1252"
        return EncodingDetectionResult(
            encoding=enc,
            confidence=1.0 - best.chaos,
            via_bom=False,
            raw_chaos=best.chaos,
        )

    return _fallback_chain(raw_bytes)


# ---------------------------------------------------------------------------
# detect_header_row (DET-01, DET-02)
# ---------------------------------------------------------------------------


def detect_header_row(rows: list[tuple[Any, ...]]) -> int | None:
    """Score each of the first 10 rows by header-likeness.

    Returns the index of the highest-scoring row, or None if the maximum score
    is 0 (no plausible header found anywhere — manual-mapping mode per DET-02).
    """
    if not rows:
        return None

    best_index: int | None = None
    best_score = 0
    best_synonym_score = 0

    for i in range(min(_HEADER_SCAN_WINDOW, len(rows))):
        row = rows[i]
        text_score = 0
        synonym_score = 0

        for cell in row:
            if cell is None:
                continue
            cell_str = str(cell).strip()
            if not cell_str:
                continue
            # Text cell: non-empty, short, not purely numeric
            stripped_for_digit = cell_str.replace(".", "").replace("-", "")
            if 1 <= len(cell_str) <= 60 and not stripped_for_digit.isdigit():
                text_score += 1
            # Synonym match: weighted ×5 (definitive evidence of a header)
            if normalize_col_name(cell_str) in (MECANOGRAFICO_SYNONYMS | NAME_SYNONYMS):
                synonym_score += 1

        total = text_score + 5 * synonym_score

        if total > best_score:
            best_score = total
            best_synonym_score = synonym_score
            best_index = i

    # Require at least one synonym match to confirm a header row.
    # Pure text-score rows (data rows with no known column labels) do not
    # qualify as headers — they would trigger false-positive header detection
    # in headerless files where every row has short text in it.
    if best_synonym_score == 0:
        return None

    return best_index


# ---------------------------------------------------------------------------
# detect_columns (DET-03, DET-04, DET-05, DET-06, DET-07, D-01)
# ---------------------------------------------------------------------------


def detect_columns(
    header_row: tuple[Any, ...],
    data_rows: list[tuple[Any, ...]],
    output_type: Literal["caderno", "elegiveis"],
) -> ColumnMapping:
    """Match header cells to MECANOGRAFICO_SYNONYMS and NAME_SYNONYMS.

    For caderno output type:
      - If no synonym matches the mec column, scan each column's first 50 data rows
        for ≥70% match against _MEC_FORMAT_PATTERN (D-01 fallback).

    For elegiveis output type:
      - mec_col_index is always None (DET-07).

    Returns ColumnMapping; never raises — None values signal manual-mapping mode.
    """
    # Build normalized header
    normalized_header = [
        normalize_col_name(str(cell)) if cell is not None else "" for cell in header_row
    ]

    # --- Mecanográfico column detection ---
    if output_type == "elegiveis":
        mec_candidates: list[int] = []
    else:
        mec_candidates = [
            i for i, norm in enumerate(normalized_header) if norm in MECANOGRAFICO_SYNONYMS
        ]

    # --- Name column detection ---
    name_candidates: list[int] = [
        i for i, norm in enumerate(normalized_header) if norm in NAME_SYNONYMS
    ]

    # --- Resolve mec column ---
    mec_col_index: int | None = None
    mec_col_label: str | None = None
    ambiguous_mec_candidates: list[tuple[int, str]] = []
    detection_method: Literal["synonym", "format_fallback", "manual"] = "manual"

    if len(mec_candidates) == 1:
        mec_col_index = mec_candidates[0]
        mec_col_label = str(header_row[mec_col_index]) if header_row[mec_col_index] is not None else None
        detection_method = "synonym"
    elif len(mec_candidates) > 1:
        # Ambiguous — report all candidates
        ambiguous_mec_candidates = [
            (i, str(header_row[i]) if header_row[i] is not None else "")
            for i in mec_candidates
        ]
        mec_col_index = None
    elif output_type == "caderno":
        # D-01 format fallback: scan data values for pattern match
        fallback_index: int | None = None
        for col_idx in range(len(header_row)):
            sample_values = []
            for row in data_rows[:_FORMAT_FALLBACK_SAMPLE_ROWS]:
                if col_idx < len(row) and row[col_idx] is not None:
                    cell_str = str(row[col_idx]).strip()
                    if cell_str:
                        sample_values.append(cell_str)
            if not sample_values:
                continue
            hits = sum(1 for v in sample_values if _MEC_FORMAT_PATTERN.match(v))
            ratio = hits / len(sample_values)
            if ratio >= _FORMAT_FALLBACK_HIT_RATIO:
                fallback_index = col_idx
                break  # first qualifying column wins

        if fallback_index is not None:
            mec_col_index = fallback_index
            mec_col_label = (
                str(header_row[fallback_index])
                if fallback_index < len(header_row) and header_row[fallback_index] is not None
                else None
            )
            detection_method = "format_fallback"

    # --- Resolve name column ---
    name_col_index: int | None = None
    name_col_label: str | None = None
    ambiguous_name_candidates: list[tuple[int, str]] = []

    if len(name_candidates) == 1:
        name_col_index = name_candidates[0]
        name_col_label = (
            str(header_row[name_col_index]) if header_row[name_col_index] is not None else None
        )
        # Only update detection_method if mec was also synonym (don't override format_fallback)
        if detection_method == "manual" and mec_col_index is not None:
            detection_method = "synonym"
    elif len(name_candidates) > 1:
        ambiguous_name_candidates = [
            (i, str(header_row[i]) if header_row[i] is not None else "")
            for i in name_candidates
        ]

    return ColumnMapping(
        mec_col_index=mec_col_index,
        name_col_index=name_col_index,
        mec_col_label=mec_col_label,
        name_col_label=name_col_label,
        ambiguous_mec_candidates=ambiguous_mec_candidates,
        ambiguous_name_candidates=ambiguous_name_candidates,
        detection_method=detection_method,
    )
