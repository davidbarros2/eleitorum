"""Transformation/error log builder with PT-PT tags and spec-verbatim line format.

Module naming note: This module is named ``eleitorum.core.logging``, which shadows
Python's stdlib ``logging`` module within this package. Any code that needs the
stdlib logging module should import it as ``import logging as stdlib_logging`` to
avoid the name collision.

Security notes:
- T-1-04-04: Log files are written only to ``output_csv_path.parent`` (LOG-07).
  Never to system temp, never to any other location. Verified by test.
- T-1-04-05: write_error_log_file writes only FailureRow.message_pt content.
  It never includes Python tracebacks or raw exception data (ASVS V7).

Log format (Eleitorum.md Section 8.1):
  [YYYY-MM-DD HH:MM:SS] {TAG:<7} {message}

The tag field is left-aligned in a 7-character field:
  "INICIO"  (6 chars) → "INICIO " (padded to 7) → "INICIO  " before message
  "LIMPEZA" (7 chars) → "LIMPEZA" (exact fit)   → "LIMPEZA " before message
"""

from __future__ import annotations

import dataclasses
import datetime
import pathlib
from collections.abc import Callable
from dataclasses import field
from typing import Literal, TypeAlias

from eleitorum.core.transform import ChangeRecord

# ---------------------------------------------------------------------------
# Type alias and constants
# ---------------------------------------------------------------------------

LogTag: TypeAlias = Literal[
    "INICIO", "INPUT", "COLUNA", "CASO", "LIMPEZA", "AVISO", "ERRO", "SAIDA", "FIM"
]

TAGS: frozenset[str] = frozenset(
    {"INICIO", "INPUT", "COLUNA", "CASO", "LIMPEZA", "AVISO", "ERRO", "SAIDA", "FIM"}
)
"""LOG-03: all 9 PT-PT tags as a frozenset."""

_TIMESTAMP_FORMAT: str = "%Y-%m-%d %H:%M:%S"
_FILENAME_TIMESTAMP_FORMAT: str = "%Y-%m-%d_%H-%M-%S"
_LOG_ENCODING: str = "utf-8-sig"  # LOG-02: UTF-8 with BOM


# ---------------------------------------------------------------------------
# format_log_line
# ---------------------------------------------------------------------------


def format_log_line(tag: LogTag, message: str, ts: datetime.datetime) -> str:
    """Format a single log line per Eleitorum.md Section 8.1.

    Returns: ``[{timestamp}] {tag:<7} {message}``

    The tag field uses ``{tag:<7}`` (left-aligned, 7-char width):
    - "INICIO"  (6 chars) → "INICIO " → followed by one space separator
    - "LIMPEZA" (7 chars) → "LIMPEZA" → followed by one space separator

    Args:
        tag:     One of the 9 PT-PT log tags (validated against TAGS).
        message: The log message text.
        ts:      The timestamp to use for the log line.

    Returns:
        A fully formatted log line string (no trailing newline).

    Raises:
        AssertionError: If tag is not in TAGS.
    """
    assert tag in TAGS, (
        f"Etiqueta de log desconhecida: {tag!r}. Etiquetas válidas: {', '.join(sorted(TAGS))}"
    )
    return f"[{ts.strftime(_TIMESTAMP_FORMAT)}] {tag:<7} {message}"


# ---------------------------------------------------------------------------
# LogBuilder
# ---------------------------------------------------------------------------


@dataclasses.dataclass
class LogBuilder:
    """Append-only log entry accumulator.

    Pipeline.py creates one instance at the start of each run, calls ``.add()``
    or ``.add_change()`` throughout processing, and then calls
    ``write_log_file`` (success) or ``write_error_log_file`` (failure) at the end.

    The ``clock`` parameter injects a timestamp provider, enabling deterministic
    tests without monkeypatching the datetime module.
    """

    entries: list[str] = field(default_factory=list)
    clock: Callable[[], datetime.datetime] = field(default=datetime.datetime.now)

    def add(
        self,
        tag: LogTag,
        message: str,
        ts: datetime.datetime | None = None,
    ) -> None:
        """Append a formatted log line.

        Args:
            tag:     One of the 9 PT-PT log tags.
            message: The message text.
            ts:      Explicit timestamp; defaults to ``self.clock()``.
        """
        actual_ts = ts if ts is not None else self.clock()
        self.entries.append(format_log_line(tag, message, actual_ts))

    def add_change(
        self,
        row_index: int,
        change: ChangeRecord,
        ts: datetime.datetime | None = None,
    ) -> None:
        """Convenience method: format a ChangeRecord as a log entry.

        Composes message as ``f"Linha {row_index}: {change.reason_pt}"``
        and calls ``self.add(change.rule_tag, message, ts)``.

        Args:
            row_index: 1-based source row number (0 = batch-level event).
            change:    A ChangeRecord produced by transform.py.
            ts:        Explicit timestamp; defaults to ``self.clock()``.
        """
        message = f"Linha {row_index}: {change.reason_pt}"
        self.add(change.rule_tag, message, ts)


# ---------------------------------------------------------------------------
# Internal filename helper
# ---------------------------------------------------------------------------


def _build_log_filename(
    output_csv_path: pathlib.Path,
    suffix: Literal["LOG", "ERRORS"],
    ts: datetime.datetime | None = None,
) -> pathlib.Path:
    """Build a log file path in the same directory as the output CSV.

    Args:
        output_csv_path: Path to the output CSV file (used for stem + parent).
        suffix:          "LOG" for success logs, "ERRORS" for failure logs.
        ts:              Timestamp for the filename; defaults to now().

    Returns:
        A Path: ``output_csv_path.parent / f"{stem}_{suffix}_{ts_str}.txt"``
    """
    actual_ts = ts if ts is not None else datetime.datetime.now()
    stem = output_csv_path.stem
    filename = f"{stem}_{suffix}_{actual_ts.strftime(_FILENAME_TIMESTAMP_FORMAT)}.txt"
    return output_csv_path.parent / filename


# ---------------------------------------------------------------------------
# write_log_file / write_error_log_file
# ---------------------------------------------------------------------------


def write_log_file(
    builder: LogBuilder,
    output_csv_path: pathlib.Path,
    ts: datetime.datetime | None = None,
) -> pathlib.Path:
    """Write a success transformation log file.

    LOG-01: file named ``{output_csv_path.stem}_LOG_{YYYY-MM-DD_HH-MM-SS}.txt``.
    LOG-02: UTF-8 with BOM encoding.
    LOG-07: written only to ``output_csv_path.parent``.

    Args:
        builder:          LogBuilder populated during the processing run.
        output_csv_path:  Path to the output CSV (determines log location + stem).
        ts:               Timestamp for filename; defaults to now().

    Returns:
        The path of the written log file.
    """
    path = _build_log_filename(output_csv_path, "LOG", ts)
    _write_entries(builder.entries, path)
    return path


def write_error_log_file(
    builder: LogBuilder,
    intended_output_path: pathlib.Path,
    ts: datetime.datetime | None = None,
) -> pathlib.Path:
    """Write a failure error log file.

    LOG-05: file named ``{stem}_ERRORS_{YYYY-MM-DD_HH-MM-SS}.txt``.
    Called by pipeline.py when ``ValidationOutcome.passed == False`` (D-07 hard-error path).
    The output CSV is never written when this function is called.

    Security (T-1-04-05): only ``FailureRow.message_pt`` content reaches the log.
    Python tracebacks and English technical terms are never written here.

    Args:
        builder:               LogBuilder populated with ERRO entries.
        intended_output_path:  The output path the caller would have written to
                               (determines log location + stem), even though the CSV
                               was never created.
        ts:                    Timestamp for filename; defaults to now().

    Returns:
        The path of the written error log file.
    """
    path = _build_log_filename(intended_output_path, "ERRORS", ts)
    _write_entries(builder.entries, path)
    return path


def _write_entries(entries: list[str], path: pathlib.Path) -> None:
    """Write log entries to a file with UTF-8 BOM encoding.

    Each entry is written on its own line (LF line ending — log files are plain
    text; the CRLF rule applies only to CSV output per spec Section 8.1).

    Args:
        entries: Formatted log lines (from LogBuilder.entries).
        path:    Destination file path.
    """
    with open(path, mode="w", encoding=_LOG_ENCODING, newline="") as f:
        # Force BOM to be written even for empty logs (utf-8-sig writes BOM lazily
        # only when the first character is flushed — write an empty string to trigger it)
        f.write("")
        for entry in entries:
            f.write(entry + "\n")
