"""Output module: byte-exact CSV writer for caderno and elegíveis formats.

Produces the exact byte sequence accepted by the university's electoral platform:
- UTF-8 with BOM (configurable via USE_BOM)
- Semicolon delimiter
- CRLF line endings
- No quoting (csv.QUOTE_NONE + escapechar='\\')
- Trailing CRLF after last data row

Security notes:
- T-1-04-01: validate_output_path resolves both paths via Path.resolve() before
  comparing (defeats relative-vs-absolute and symlink confusion attacks).
- T-1-04-03: OUT-12 refuses silent overwrite; caller must pass overwrite_allowed=True
  after obtaining explicit user consent.
- T-1-04-02: FileAccessError wraps PermissionError and OSError on write failure;
  callers should delete any partial file on FileAccessError.
"""

from __future__ import annotations

import csv
import pathlib
from typing import IO, Any, Literal

from eleitorum.core.errors import FileAccessError, OutputPathError
from eleitorum.core.transform import sort_elegiveis
from eleitorum.core.validate import validate_output_path

# ---------------------------------------------------------------------------
# Public constants
# ---------------------------------------------------------------------------

USE_BOM: bool = True
"""D-03: Toggle to False if the electoral platform rejects the UTF-8 BOM.
This is a one-line change — the rest of the module uses _OUTPUT_ENCODING."""

CADERNO_HEADER: tuple[str, str, str] = ("personnel_number", "name", "category")
"""OUT-06: exact header for caderno eleitoral output."""

ELEGIVEIS_HEADER: tuple[str, str] = ("personnel_number", "designation")
"""OUT-08: exact header for elegíveis output."""

# ---------------------------------------------------------------------------
# Private constants
# ---------------------------------------------------------------------------

_OUTPUT_ENCODING: str = "utf-8-sig" if USE_BOM else "utf-8"
_DELIMITER: str = ";"
_LINETERMINATOR: str = "\r\n"


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _open_writer(path: pathlib.Path) -> IO[str]:
    """Open a file for writing in byte-exact CSV mode.

    Args:
        path: Destination path.

    Returns:
        An open file handle. Caller MUST use this as a context manager.

    Raises:
        FileAccessError(mode='write'): On PermissionError or any other OSError.
    """
    try:
        return open(  # noqa: WPS515
            path,
            mode="w",
            encoding=_OUTPUT_ENCODING,
            newline="",
        )
    except PermissionError as err:
        raise FileAccessError(path=path, mode="write") from err
    except OSError as err:
        raise FileAccessError(path=path, mode="write") from err


def _apply_output_guards(
    path: pathlib.Path,
    input_path: pathlib.Path | None,
    overwrite_allowed: bool,
) -> None:
    """Apply VAL-08 and OUT-12 guards before any write operation.

    Args:
        path:             The intended output path.
        input_path:       If provided, call validate_output_path (which checks both
                          same-as-input and overwrite). If None, only apply the
                          overwrite guard locally.
        overwrite_allowed: If False, raise when output already exists.
    """
    if input_path is not None:
        validate_output_path(input_path, path, overwrite_allowed=overwrite_allowed)
    else:
        # Defense-in-depth: apply OUT-12 even without an input_path
        if path.exists() and not overwrite_allowed:
            raise OutputPathError(path=path, reason="already_exists")


def _make_writer(f: IO[str]) -> Any:
    """Build a csv.writer with the byte-exact settings."""
    return csv.writer(
        f,
        delimiter=_DELIMITER,
        quoting=csv.QUOTE_NONE,
        escapechar="\\",
        lineterminator=_LINETERMINATOR,
    )


# ---------------------------------------------------------------------------
# Public write functions
# ---------------------------------------------------------------------------


def write_caderno(
    path: pathlib.Path,
    rows: list[tuple[str, str]],
    *,
    input_path: pathlib.Path | None = None,
    overwrite_allowed: bool = False,
) -> None:
    """Write a caderno eleitoral CSV with byte-exact formatting.

    OUT-01..07: UTF-8 BOM + semicolon + CRLF + no quotes + empty category field.

    Args:
        path:             Destination path.
        rows:             List of (mec_string, name_string) tuples, already
                          case-normalized and validated.
        input_path:       If provided, validate_output_path is called to enforce
                          the same-as-input guard (VAL-08). Pass the source file path.
        overwrite_allowed: If False, raises OutputPathError when path already exists.

    Raises:
        OutputPathError(reason='same_as_input'):  input_path == path (VAL-08).
        OutputPathError(reason='already_exists'): path exists and overwrite=False (OUT-12).
        FileAccessError(mode='write'):            PermissionError or OSError on write.
    """
    _apply_output_guards(path, input_path, overwrite_allowed)

    with _open_writer(path) as f:
        writer = _make_writer(f)
        writer.writerow(CADERNO_HEADER)
        for mec, name in rows:
            writer.writerow([mec, name, ""])


def write_elegiveis(
    path: pathlib.Path,
    designations: list[str],
    *,
    input_path: pathlib.Path | None = None,
    overwrite_allowed: bool = False,
) -> None:
    """Write an elegíveis CSV with byte-exact formatting.

    OUT-01..05, OUT-08..09: sort designations by D-02 NFKD key (calls
    transform.sort_elegiveis internally), assign 0-based indices, write.

    Args:
        path:             Destination path.
        designations:     List of designation strings, already validated, NOT pre-sorted.
        input_path:       If provided, validate_output_path is called (VAL-08).
        overwrite_allowed: If False, raises OutputPathError when path exists (OUT-12).

    Raises:
        OutputPathError(reason='same_as_input'):  input_path == path (VAL-08).
        OutputPathError(reason='already_exists'): path exists and overwrite=False (OUT-12).
        FileAccessError(mode='write'):            PermissionError or OSError on write.
    """
    _apply_output_guards(path, input_path, overwrite_allowed)

    # Build (index, designation) pairs, then sort via D-02 sort key
    indexed = sort_elegiveis([(i, d) for i, d in enumerate(designations)])

    with _open_writer(path) as f:
        writer = _make_writer(f)
        writer.writerow(ELEGIVEIS_HEADER)
        for idx, designation in indexed:
            writer.writerow([str(idx), designation])


# ---------------------------------------------------------------------------
# Filename helper
# ---------------------------------------------------------------------------


def build_output_filename(
    input_path: pathlib.Path,
    output_type: Literal["caderno", "elegiveis"],
) -> str:
    """Suggest an output filename from the input path and output type.

    Used by Phase 2 UI's save dialog default suggestion. Returns a filename
    string only — the caller composes the full directory path.

    Examples:
        lista.xlsx + caderno  → "caderno_lista.csv"
        lista.xlsx + elegiveis → "elegiveis_lista.csv"
        data.csv + elegiveis  → "elegiveis_data.csv"
        noext + caderno       → "caderno_noext.csv"

    Args:
        input_path:  Path to the source file (used for its stem/name).
        output_type: "caderno" or "elegiveis".

    Returns:
        A filename string of the form "{output_type}_{stem}.csv".
    """
    stem = input_path.stem if input_path.suffix else input_path.name
    return f"{output_type}_{stem}.csv"
