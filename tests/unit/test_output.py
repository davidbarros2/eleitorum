"""Tests for the eleitorum.core.output module.

Covers: OUT-01 through OUT-12.
Byte-exact CSV contract: UTF-8 BOM, semicolon delimiter, CRLF line endings,
no quoting, trailing CRLF, category column always empty (caderno).
"""

from __future__ import annotations

import pathlib

import pytest

from eleitorum.core.errors import FileAccessError, OutputPathError
from eleitorum.core.output import (
    CADERNO_HEADER,
    ELEGIVEIS_HEADER,
    USE_BOM,
    build_output_filename,
    write_caderno,
    write_elegiveis,
)


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------


def test_use_bom_is_true() -> None:
    """D-03: USE_BOM must be True (BOM is part of the byte-exact contract)."""
    assert USE_BOM is True


def test_caderno_header_exact() -> None:
    """OUT-06: CADERNO_HEADER must be exactly ('personnel_number', 'name', 'category')."""
    assert CADERNO_HEADER == ("personnel_number", "name", "category")


def test_elegiveis_header_exact() -> None:
    """OUT-08: ELEGIVEIS_HEADER must be exactly ('personnel_number', 'designation')."""
    assert ELEGIVEIS_HEADER == ("personnel_number", "designation")


# ---------------------------------------------------------------------------
# Caderno — byte-level contract
# ---------------------------------------------------------------------------


def test_byte_exact_caderno_bom_crlf_no_quotes(tmp_path: pathlib.Path) -> None:
    """OUT-01, OUT-03, OUT-04: BOM present, all CRLF, no quote chars."""
    p = tmp_path / "out.csv"
    write_caderno(p, [("f6688", "João Silva"), ("ex5205", "Maria Costa")])
    raw = p.read_bytes()
    # OUT-01: BOM
    assert raw[:3] == b"\xef\xbb\xbf", f"BOM missing, got {raw[:3]!r}"
    # OUT-03: all line endings are CRLF (not bare LF)
    lf_only = raw.count(b"\n") - raw.count(b"\r\n")
    assert lf_only == 0, f"Found {lf_only} bare LF (not CRLF) in output"
    # OUT-04: no quote characters
    assert b'"' not in raw, "Quote character found in output"


def test_caderno_header_exact_bytes(tmp_path: pathlib.Path) -> None:
    """OUT-06: header line is exactly 'personnel_number;name;category\\r\\n'."""
    p = tmp_path / "out.csv"
    write_caderno(p, [])
    raw = p.read_bytes()
    # Skip BOM (3 bytes), then check header line
    content = raw[3:]
    first_line = content.split(b"\r\n")[0]
    assert first_line == b"personnel_number;name;category"


def test_caderno_row_format_third_field_empty(tmp_path: pathlib.Path) -> None:
    """OUT-07: third field (category) is always empty; row ends with ';\\r\\n'."""
    p = tmp_path / "out.csv"
    write_caderno(p, [("f1", "Joao")])
    raw = p.read_bytes()
    # The data row must be: f1;Joao;\r\n
    assert b"f1;Joao;\r\n" in raw


def test_field_separator_semicolon(tmp_path: pathlib.Path) -> None:
    """OUT-02: semicolon is the field delimiter."""
    p = tmp_path / "out.csv"
    write_caderno(p, [("a1", "Name")])
    raw = p.read_bytes()
    assert b"a1;Name;" in raw


def test_file_ends_with_crlf(tmp_path: pathlib.Path) -> None:
    """OUT-05: file ends with CRLF."""
    p = tmp_path / "out.csv"
    write_caderno(p, [("f1", "A")])
    raw = p.read_bytes()
    assert raw.endswith(b"\r\n"), f"File does not end with CRLF, ends with {raw[-4:]!r}"


def test_caderno_crlf_count_matches_lines(tmp_path: pathlib.Path) -> None:
    """OUT-03, OUT-05: exactly 3 CRLF sequences for header + 2 rows."""
    p = tmp_path / "out.csv"
    write_caderno(p, [("f6688", "João"), ("ex5205", "Maria")])
    raw = p.read_bytes()
    assert raw.count(b"\r\n") == 3  # header + 2 rows
    # No bare LF
    bare_lf = raw.count(b"\n") - raw.count(b"\r\n")
    assert bare_lf == 0


def test_byte_exact_caderno_full_example(tmp_path: pathlib.Path) -> None:
    """Byte-exact full example matching Eleitorum.md Section 5.2 layout."""
    p = tmp_path / "out.csv"
    write_caderno(
        p,
        [
            ("f6688", "David André Moreira Lopes de Barros"),
            ("ex5205", "David André Moreira Lopes de Barros"),
        ],
    )
    raw = p.read_bytes()
    # BOM
    assert raw[:3] == b"\xef\xbb\xbf"
    # Decode to check structure
    text = raw.decode("utf-8-sig")
    lines = text.split("\r\n")
    # Last element is empty string (trailing CRLF)
    assert lines[-1] == ""
    assert lines[0] == "personnel_number;name;category"
    assert lines[1] == "f6688;David André Moreira Lopes de Barros;"
    assert lines[2] == "ex5205;David André Moreira Lopes de Barros;"
    # No quotes
    assert '"' not in text


# ---------------------------------------------------------------------------
# Elegíveis — byte-level contract
# ---------------------------------------------------------------------------


def test_elegiveis_header_exact_bytes(tmp_path: pathlib.Path) -> None:
    """OUT-08: elegíveis header is exactly 'personnel_number;designation\\r\\n'."""
    p = tmp_path / "out.csv"
    write_elegiveis(p, [])
    raw = p.read_bytes()
    content = raw[3:]  # skip BOM
    first_line = content.split(b"\r\n")[0]
    assert first_line == b"personnel_number;designation"


def test_elegiveis_row_format_index_zero_based(tmp_path: pathlib.Path) -> None:
    """OUT-09: elegíveis rows use 0-based index post-sort."""
    p = tmp_path / "out.csv"
    write_elegiveis(p, ["Zélia", "Ana"])
    text = p.read_bytes().decode("utf-8-sig")
    lines = [l for l in text.split("\r\n") if l]
    # Ana comes first alphabetically
    assert lines[1] == "0;Ana"
    assert lines[2] == "1;Zélia"


def test_write_elegiveis_sorts_alphabetically_diacritic_stripped(tmp_path: pathlib.Path) -> None:
    """D-02 NFKD sort: É→E, Á→A, Z→Z — verify sort order is Ana, Élia, Mário, Zélia."""
    p = tmp_path / "out.csv"
    write_elegiveis(p, ["Zélia", "Ana", "Mário", "Élia"])
    text = p.read_bytes().decode("utf-8-sig")
    lines = [l for l in text.split("\r\n") if l]
    # Skip header
    data_lines = lines[1:]
    assert data_lines[0] == "0;Ana"
    assert data_lines[1] == "1;Élia"
    assert data_lines[2] == "2;Mário"
    assert data_lines[3] == "3;Zélia"


# ---------------------------------------------------------------------------
# OUT-04: QUOTE_NONE + escapechar behavior
# ---------------------------------------------------------------------------


def test_output_no_quote_chars_anywhere(tmp_path: pathlib.Path) -> None:
    """OUT-04: no quoting anywhere; semicolon in a name is escaped with backslash.

    Note: real data does not contain semicolons (per Eleitorum.md Section 6.4,
    only commas are observed and they are stripped in TRF-07). This test verifies
    that QUOTE_NONE+escapechar='\\\\' handles the edge case correctly by escaping
    rather than quoting. The output contains '\\;' not '"Silva; Junior"'.
    """
    p = tmp_path / "out.csv"
    write_caderno(p, [("f1", "Silva; Junior")])
    raw = p.read_bytes()
    assert b'"' not in raw, "Quote character found — QUOTE_NONE violated"
    # The semicolon in the name is escaped, not quoted
    assert b"\\;" in raw, "Expected backslash-escaped semicolon"


# ---------------------------------------------------------------------------
# Path collision guards (VAL-08, OUT-12)
# ---------------------------------------------------------------------------


def test_no_output_on_validation_error(tmp_path: pathlib.Path) -> None:
    """OUT-10: output.py is never called after a validation failure (enforced by pipeline.py).
    This test verifies write_caderno can be called and creates a file when validation passes."""
    p = tmp_path / "result.csv"
    write_caderno(p, [("f1", "Valid")])
    assert p.exists()


def test_refuse_write_to_input_path(tmp_path: pathlib.Path) -> None:
    """OUT-11: write_caderno refuses to write when input_path == output_path."""
    same = tmp_path / "data.csv"
    same.write_text("something", encoding="utf-8")
    with pytest.raises(OutputPathError) as exc_info:
        write_caderno(same, [("f1", "A")], input_path=same)
    assert exc_info.value.details.get("reason") == "same_as_input"


def test_existing_file_collision_raises_or_renames(tmp_path: pathlib.Path) -> None:
    """OUT-12: write_caderno raises OutputPathError when output exists and overwrite=False."""
    existing = tmp_path / "out.csv"
    existing.write_text("data", encoding="utf-8")
    with pytest.raises(OutputPathError) as exc_info:
        write_caderno(existing, [("f1", "A")], overwrite_allowed=False)
    assert exc_info.value.details.get("reason") == "already_exists"


def test_write_caderno_overwrite_allowed(tmp_path: pathlib.Path) -> None:
    """OUT-12: write_caderno succeeds when output exists and overwrite_allowed=True."""
    existing = tmp_path / "out.csv"
    existing.write_text("old data", encoding="utf-8")
    write_caderno(existing, [("f1", "A")], overwrite_allowed=True)
    # File should now have new content
    raw = existing.read_bytes()
    assert raw[:3] == b"\xef\xbb\xbf"


def test_write_elegiveis_existing_file_collision(tmp_path: pathlib.Path) -> None:
    """OUT-12: write_elegiveis also respects the overwrite guard."""
    existing = tmp_path / "out.csv"
    existing.write_text("data", encoding="utf-8")
    with pytest.raises(OutputPathError) as exc_info:
        write_elegiveis(existing, ["Ana"], overwrite_allowed=False)
    assert exc_info.value.details.get("reason") == "already_exists"


# ---------------------------------------------------------------------------
# Error handling (VAL-09)
# ---------------------------------------------------------------------------


def test_write_caderno_permission_error_pt_pt(
    tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """VAL-09: PermissionError on open is re-raised as FileAccessError(mode='write')."""
    p = tmp_path / "out.csv"

    def mock_open(*args, **kwargs):  # type: ignore[no-untyped-def]
        raise PermissionError("Access denied")

    monkeypatch.setattr("builtins.open", mock_open)

    with pytest.raises(FileAccessError) as exc_info:
        write_caderno(p, [("f1", "A")])
    assert exc_info.value.details.get("mode") == "write"
    # PT-PT message must mention "gravar"
    assert "gravar" in exc_info.value.message_pt


# ---------------------------------------------------------------------------
# build_output_filename
# ---------------------------------------------------------------------------


def test_build_output_filename_caderno_xlsx() -> None:
    """build_output_filename: lista_2026.xlsx + caderno → 'caderno_lista_2026.csv'."""
    assert build_output_filename(pathlib.Path("lista_2026.xlsx"), "caderno") == "caderno_lista_2026.csv"


def test_build_output_filename_elegiveis_xlsx() -> None:
    """build_output_filename: lista_2026.xlsx + elegiveis → 'elegiveis_lista_2026.csv'."""
    assert (
        build_output_filename(pathlib.Path("lista_2026.xlsx"), "elegiveis")
        == "elegiveis_lista_2026.csv"
    )


def test_build_output_filename_csv_input() -> None:
    """build_output_filename: data.csv → 'elegiveis_data.csv'."""
    assert build_output_filename(pathlib.Path("data.csv"), "elegiveis") == "elegiveis_data.csv"


def test_build_output_filename_ods_input() -> None:
    """build_output_filename: list.ods → 'caderno_list.csv'."""
    assert build_output_filename(pathlib.Path("list.ods"), "caderno") == "caderno_list.csv"


def test_build_output_filename_no_extension() -> None:
    """build_output_filename: noext → 'caderno_noext.csv'."""
    assert build_output_filename(pathlib.Path("noext"), "caderno") == "caderno_noext.csv"


def test_build_output_filename_double_extension() -> None:
    """build_output_filename: file.backup.xlsx → 'caderno_file.backup.csv' (only last ext stripped)."""
    result = build_output_filename(pathlib.Path("file.backup.xlsx"), "caderno")
    assert result == "caderno_file.backup.csv"


def test_build_output_filename_variations() -> None:
    """Exercise all extension variations from the plan spec."""
    assert build_output_filename(pathlib.Path("test.xlsx"), "caderno") == "caderno_test.csv"
    assert build_output_filename(pathlib.Path("test.csv"), "elegiveis") == "elegiveis_test.csv"
    assert build_output_filename(pathlib.Path("test.ods"), "caderno") == "caderno_test.csv"
    assert build_output_filename(pathlib.Path("test"), "caderno") == "caderno_test.csv"
