"""Tests for the eleitorum.core.logging module.

Covers: LOG-01 through LOG-07.
The log format is spec-verbatim per Eleitorum.md Section 8.1:
  [YYYY-MM-DD HH:MM:SS] {TAG:<7} {message}
"""

from __future__ import annotations

import datetime
import pathlib
import tempfile

import pytest

from eleitorum.core.errors import FailureRow
from eleitorum.core.logging import (
    TAGS,
    LogBuilder,
    format_log_line,
    write_error_log_file,
    write_log_file,
)
from eleitorum.core.transform import ChangeRecord

# Fixed timestamp for deterministic tests
_FIXED_TS = datetime.datetime(2026, 5, 23, 14, 32, 15)
_FIXED_TS_STR = "2026-05-23 14:32:15"


# ---------------------------------------------------------------------------
# TAGS constant
# ---------------------------------------------------------------------------


def test_log_all_nine_tags_defined() -> None:
    """LOG-03: TAGS must contain exactly the 9 PT-PT tags."""
    assert TAGS == frozenset(
        {"INICIO", "INPUT", "COLUNA", "CASO", "LIMPEZA", "AVISO", "ERRO", "SAIDA", "FIM"}
    )


def test_tags_count() -> None:
    """TAGS must have exactly 9 entries."""
    assert len(TAGS) == 9


# ---------------------------------------------------------------------------
# format_log_line — spec-verbatim format
# ---------------------------------------------------------------------------


def test_log_line_format_timestamp_and_tag() -> None:
    """LOG-02: format_log_line matches the spec Section 8.1 worked example.

    'INICIO' is 6 chars → padded to 7 with one trailing space → then one space separator.
    Result: '[2026-05-23 14:32:15] INICIO  msg' (double space between INICIO and msg).
    """
    result = format_log_line("INICIO", "msg", _FIXED_TS)
    assert result == "[2026-05-23 14:32:15] INICIO  msg"


def test_format_log_line_padding_for_short_tag() -> None:
    """Tag shorter than 7 chars gets padded to 7. 'FIM' is 3 chars → 4 spaces padding."""
    result = format_log_line("FIM", "done", _FIXED_TS)
    assert result == f"[{_FIXED_TS_STR}] FIM     done"


def test_format_log_line_padding_for_seven_char_tag() -> None:
    """LIMPEZA is exactly 7 chars — no padding, then one space separator."""
    result = format_log_line("LIMPEZA", "msg", _FIXED_TS)
    assert result == f"[{_FIXED_TS_STR}] LIMPEZA msg"


def test_format_log_line_spec_example_input() -> None:
    """Reproduce the exact worked example from Eleitorum.md Section 8.1."""
    result = format_log_line(
        "INPUT",
        "Ficheiro: cadernos_originais.xlsx",
        _FIXED_TS,
    )
    assert result == "[2026-05-23 14:32:15] INPUT   Ficheiro: cadernos_originais.xlsx"


def test_format_log_line_caso_tag() -> None:
    """CASO is 4 chars → padded to 7 with 3 spaces, then space separator."""
    result = format_log_line("CASO", "test", _FIXED_TS)
    assert result == f"[{_FIXED_TS_STR}] CASO    test"


def test_format_log_line_invalid_tag_raises() -> None:
    """format_log_line raises AssertionError for unknown tags."""
    with pytest.raises((AssertionError, ValueError)):
        format_log_line("INVALID_TAG", "msg", _FIXED_TS)  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# LogBuilder
# ---------------------------------------------------------------------------


def test_log_builder_add_appends_entry() -> None:
    """LogBuilder.add appends one formatted entry."""
    builder = LogBuilder(clock=lambda: _FIXED_TS)
    builder.add("INICIO", "Tipo de output: caderno eleitoral")
    assert len(builder.entries) == 1
    assert builder.entries[0].startswith(f"[{_FIXED_TS_STR}] INICIO")


def test_log_builder_add_with_explicit_ts() -> None:
    """LogBuilder.add with explicit ts parameter overrides the clock."""
    builder = LogBuilder()
    builder.add("FIM", "concluído", ts=_FIXED_TS)
    assert builder.entries[0] == f"[{_FIXED_TS_STR}] FIM     concluído"


def test_log_builder_add_change_limpeza() -> None:
    """LogBuilder.add_change formats a LIMPEZA ChangeRecord as a log entry."""
    builder = LogBuilder(clock=lambda: _FIXED_TS)
    change = ChangeRecord(
        row_index=12,
        field="name",
        rule_tag="LIMPEZA",
        before="  Maria Santos",
        after="Maria Santos",
        reason_pt='removido espaço inicial em "  Maria Santos"',
    )
    builder.add_change(row_index=12, change=change)
    assert len(builder.entries) == 1
    entry = builder.entries[0]
    assert "Linha 12" in entry
    assert "LIMPEZA" in entry
    assert "removido espaço inicial" in entry


def test_log_builder_add_change_caso() -> None:
    """LogBuilder.add_change works with CASO tag."""
    builder = LogBuilder(clock=lambda: _FIXED_TS)
    change = ChangeRecord(
        row_index=0,
        field="mecanografico",
        rule_tag="CASO",
        before="3 lower vs 2 upper",
        after="lower",
        reason_pt="Normalização: lower (3 minúsculas vs 2 maiúsculas)",
    )
    builder.add_change(row_index=0, change=change)
    entry = builder.entries[0]
    assert "CASO" in entry
    assert "Normalização" in entry


def test_log_records_required_events(tmp_path: pathlib.Path) -> None:
    """LOG-04: write_log_file writes entries for all 9 tags; all appear in file."""
    builder = LogBuilder(clock=lambda: _FIXED_TS)
    for tag in sorted(TAGS):  # sort for determinism
        builder.add(tag, f"Test message for {tag}", ts=_FIXED_TS)  # type: ignore[arg-type]

    output_csv = tmp_path / "out.csv"
    log_path = write_log_file(builder, output_csv, ts=_FIXED_TS)
    content = log_path.read_text(encoding="utf-8-sig")

    for tag in TAGS:
        assert tag in content, f"Tag {tag!r} missing from log file"


# ---------------------------------------------------------------------------
# Log file name patterns
# ---------------------------------------------------------------------------


def test_log_file_name_pattern(tmp_path: pathlib.Path) -> None:
    """LOG-01: log file path is '{stem}_LOG_{YYYY-MM-DD_HH-MM-SS}.txt' in same dir."""
    builder = LogBuilder(clock=lambda: _FIXED_TS)
    output_csv = tmp_path / "caderno_2026.csv"
    log_path = write_log_file(builder, output_csv, ts=_FIXED_TS)
    assert log_path.name == "caderno_2026_LOG_2026-05-23_14-32-15.txt"
    assert log_path.parent == tmp_path


def test_error_log_file_name_pattern(tmp_path: pathlib.Path) -> None:
    """LOG-05: error log name contains '_ERRORS_' not '_LOG_'."""
    builder = LogBuilder(clock=lambda: _FIXED_TS)
    output_csv = tmp_path / "caderno_2026.csv"
    log_path = write_error_log_file(builder, output_csv, ts=_FIXED_TS)
    assert log_path.name == "caderno_2026_ERRORS_2026-05-23_14-32-15.txt"
    assert log_path.parent == tmp_path


def test_log_file_name_different_stem(tmp_path: pathlib.Path) -> None:
    """LOG-01: stem is derived from the output CSV path stem."""
    builder = LogBuilder()
    output_csv = tmp_path / "elegiveis_lista.csv"
    log_path = write_log_file(builder, output_csv, ts=_FIXED_TS)
    assert log_path.name.startswith("elegiveis_lista_LOG_")
    assert log_path.name.endswith(".txt")


# ---------------------------------------------------------------------------
# Encoding
# ---------------------------------------------------------------------------


def test_log_encoding_utf8_with_bom(tmp_path: pathlib.Path) -> None:
    """LOG-02: log file first 3 bytes are UTF-8 BOM (\\xef\\xbb\\xbf)."""
    builder = LogBuilder(clock=lambda: _FIXED_TS)
    builder.add("INICIO", "Test", ts=_FIXED_TS)
    output_csv = tmp_path / "out.csv"
    log_path = write_log_file(builder, output_csv, ts=_FIXED_TS)
    raw = log_path.read_bytes()
    assert raw[:3] == b"\xef\xbb\xbf", f"BOM missing, got {raw[:3]!r}"


def test_error_log_encoding_utf8_with_bom(tmp_path: pathlib.Path) -> None:
    """LOG-02: error log file also has UTF-8 BOM."""
    builder = LogBuilder()
    output_csv = tmp_path / "out.csv"
    log_path = write_error_log_file(builder, output_csv, ts=_FIXED_TS)
    raw = log_path.read_bytes()
    assert raw[:3] == b"\xef\xbb\xbf"


# ---------------------------------------------------------------------------
# Error log content
# ---------------------------------------------------------------------------


def test_error_log_includes_row_col_value_message(tmp_path: pathlib.Path) -> None:
    """LOG-06: error log must contain FailureRow row_index, column_name, value, message_pt."""
    builder = LogBuilder(clock=lambda: _FIXED_TS)
    # Add FailureRow details as ERRO entries
    failures = [
        FailureRow(
            row_index=5,
            column_name="número mecanográfico",
            value="F500",
            message_pt="duplicado dentro do prefixo F: F500 já existe (linha 2)",
        ),
        FailureRow(
            row_index=12,
            column_name="nome",
            value="(vazio)",
            message_pt="nome em branco após normalização",
        ),
    ]
    for f in failures:
        builder.add(
            "ERRO",
            f"Linha {f.row_index}: {f.column_name} '{f.value}' — {f.message_pt}",
            ts=_FIXED_TS,
        )

    output_csv = tmp_path / "out.csv"
    log_path = write_error_log_file(builder, output_csv, ts=_FIXED_TS)
    content = log_path.read_text(encoding="utf-8-sig")

    # Check first failure
    assert "5" in content  # row_index
    assert "número mecanográfico" in content
    assert "F500" in content
    assert "duplicado" in content

    # Check second failure
    assert "12" in content
    assert "nome" in content
    assert "(vazio)" in content


# ---------------------------------------------------------------------------
# LOG-07: file written only to user-chosen location
# ---------------------------------------------------------------------------


def test_log_written_only_to_user_chosen_location(tmp_path: pathlib.Path) -> None:
    """LOG-07: log file is created in output_csv.parent, NOT in system temp dir."""
    builder = LogBuilder(clock=lambda: _FIXED_TS)
    builder.add("INICIO", "start", ts=_FIXED_TS)
    output_csv = tmp_path / "out.csv"
    log_path = write_log_file(builder, output_csv, ts=_FIXED_TS)

    # File must be in tmp_path (user's chosen location)
    assert log_path.parent == tmp_path
    assert log_path.exists()

    # No log file with the same stem should appear in system temp
    sys_temp = pathlib.Path(tempfile.gettempdir())
    stray_files = list(sys_temp.glob("out_LOG*"))
    assert not stray_files, f"Log file found in system temp: {stray_files}"
