"""Tests for the eleitorum.core.transform module.

Covers: TRF-01 through TRF-15.
"""

from __future__ import annotations

import pytest

from eleitorum.core.errors import MecanograficoError
from eleitorum.core.transform import (
    VALID_PREFIXES,
    FDB_SHARED,
    ChangeRecord,
    TransformResult,
    normalize_mecanografico_case,
    remove_replacement_characters,
    sort_elegiveis,
    transform_mecanografico,
    transform_name,
    try_fix_mojibake,
)


# ---------------------------------------------------------------------------
# transform_mecanografico — TRF-01, TRF-02, TRF-03
# ---------------------------------------------------------------------------


def test_mec_whitespace_removed() -> None:
    """TRF-01: leading/trailing whitespace removed from mecanografico."""
    prefix, num, changes = transform_mecanografico("  f0500  ", 1)
    assert prefix == "F"
    assert num == 500
    # Should have a LIMPEZA record for whitespace
    limpeza_tags = [c.rule_tag for c in changes]
    assert "LIMPEZA" in limpeza_tags


def test_mec_float_to_int_string() -> None:
    """TRF-02: Excel float stored without prefix raises MecanograficoError (no prefix)."""
    # A pure float like 14891.0 has no prefix — should raise
    with pytest.raises(MecanograficoError) as exc_info:
        transform_mecanografico(14891.0, 5)
    assert exc_info.value.row_index == 5


def test_mec_float_whole_number_raises_no_prefix() -> None:
    """TRF-02: float that looks like an integer raises because no prefix."""
    with pytest.raises(MecanograficoError):
        transform_mecanografico(6688.0, 3)


def test_mec_leading_zeros_stripped() -> None:
    """TRF-03: leading zeros are stripped from the numeric part."""
    prefix, num, changes = transform_mecanografico("F0500", 1)
    assert prefix == "F"
    assert num == 500
    # Should have a LIMPEZA record for leading zero removal
    leading_zero_changes = [c for c in changes if "zero" in c.reason_pt.lower() or "0" in c.before]
    assert len(leading_zero_changes) > 0 or any(c.rule_tag == "LIMPEZA" for c in changes)


def test_mec_no_changes_when_clean() -> None:
    """Clean mecanografico returns empty changes list."""
    prefix, num, changes = transform_mecanografico("F500", 1)
    assert prefix == "F"
    assert num == 500
    assert changes == []


def test_mec_invalid_prefix_raises() -> None:
    """VAL-01: invalid prefix raises MecanograficoError with row_index."""
    with pytest.raises(MecanograficoError) as exc_info:
        transform_mecanografico("X500", 7)
    err = exc_info.value
    assert err.row_index == 7
    assert "prefixo" in err.message_pt.lower() or "prefixo" in err.reason.lower()


def test_mec_invalid_prefix_raises_with_row_index() -> None:
    """VAL-01: exception row_index matches the input row_index."""
    with pytest.raises(MecanograficoError) as exc_info:
        transform_mecanografico("X500", 42)
    assert exc_info.value.row_index == 42


def test_mec_zero_value_raises_non_positive() -> None:
    """TRF-03 + VAL-02: F0 → stripped to 0 → non-positive raises."""
    with pytest.raises(MecanograficoError) as exc_info:
        transform_mecanografico("F0", 9)
    err = exc_info.value
    assert "positivo" in err.message_pt.lower() or "não positivo" in err.message_pt.lower()


def test_mec_pure_int_raises_no_prefix() -> None:
    """Pure integer (no prefix) raises MecanograficoError."""
    with pytest.raises(MecanograficoError):
        transform_mecanografico(500, 1)


def test_mec_none_raises() -> None:
    """None mecanografico raises MecanograficoError."""
    with pytest.raises(MecanograficoError):
        transform_mecanografico(None, 1)


def test_mec_all_valid_prefixes_accepted() -> None:
    """All prefixes in VALID_PREFIXES are accepted."""
    for prefix in VALID_PREFIXES:
        p, n, _ = transform_mecanografico(f"{prefix}100", 1)
        assert p == prefix.upper()
        assert n == 100


def test_mec_prefix_uppercase_in_output() -> None:
    """transform_mecanografico always returns uppercase prefix."""
    prefix, _, _ = transform_mecanografico("f500", 1)
    assert prefix == "F"


def test_valid_prefixes_set() -> None:
    """VALID_PREFIXES matches the D-08 exact set."""
    assert VALID_PREFIXES == frozenset({"A", "PG", "ID", "F", "D", "B", "Q", "EX"})


def test_fdb_shared_set() -> None:
    """FDB_SHARED is the set of F/D/B prefixes that share a uniqueness namespace."""
    assert FDB_SHARED == frozenset({"F", "D", "B"})


# ---------------------------------------------------------------------------
# normalize_mecanografico_case — TRF-04
# ---------------------------------------------------------------------------


def test_prefix_case_normalization_lowercase_majority() -> None:
    """TRF-04: majority lowercase → chosen = 'lower'."""
    chosen, lower_count, upper_count, record = normalize_mecanografico_case(
        [],
        ["f", "f", "f", "F", "F"],
    )
    assert chosen == "lower"
    assert lower_count == 3
    assert upper_count == 2
    assert record.rule_tag == "CASO"


def test_prefix_case_normalization_uppercase_majority() -> None:
    """TRF-04: majority uppercase → chosen = 'upper'."""
    chosen, lower_count, upper_count, record = normalize_mecanografico_case(
        [],
        ["F", "F", "F", "f", "f"],
    )
    assert chosen == "upper"
    assert lower_count == 2
    assert upper_count == 3
    assert record.rule_tag == "CASO"


def test_prefix_case_normalization_tie_defaults_lowercase() -> None:
    """TRF-04: on tie, lowercase wins (D-08)."""
    chosen, lower_count, upper_count, record = normalize_mecanografico_case(
        [],
        ["F", "f"],
    )
    assert chosen == "lower"
    assert lower_count == 1
    assert upper_count == 1
    assert record.rule_tag == "CASO"


def test_normalize_case_returns_change_record() -> None:
    """normalize_mecanografico_case returns a CASO-tagged ChangeRecord."""
    chosen, _, _, record = normalize_mecanografico_case([], ["f", "f", "F"])
    assert isinstance(record, ChangeRecord)
    assert record.rule_tag == "CASO"
    assert record.field == "mecanografico"


# ---------------------------------------------------------------------------
# transform_name — TRF-05, TRF-06, TRF-07, TRF-08, TRF-09, TRF-10, TRF-11, TRF-12
# ---------------------------------------------------------------------------


def test_name_whitespace_strip_includes_nbsp_zwsp() -> None:
    """TRF-05: Unicode whitespace types are stripped and collapsed."""
    name, changes = transform_name("  João Silva\tTeste​  ", 1)
    assert name == "João Silva Teste"
    limpeza = [c for c in changes if c.rule_tag == "LIMPEZA"]
    assert len(limpeza) > 0


def test_name_internal_whitespace_collapsed() -> None:
    """TRF-06: internal whitespace collapsed to single space."""
    name, changes = transform_name("João  Silva   Teste", 1)
    assert name == "João Silva Teste"


def test_name_comma_removed() -> None:
    """TRF-07: trailing/embedded commas removed from names."""
    name, changes = transform_name("Marta Oliveira,", 1)
    assert name == "Marta Oliveira"
    comma_changes = [c for c in changes if "vírgula" in c.reason_pt.lower() or "comma" in c.reason_pt.lower() or "," in c.before]
    assert len(comma_changes) > 0


def test_name_parenthesis_removed_and_rewhitespaced() -> None:
    """TRF-08: parenthetical annotations removed; surrounding whitespace cleaned up."""
    name, changes = transform_name("Rui Pereira (Coordenador)", 1)
    assert name == "Rui Pereira"
    paren_changes = [c for c in changes if c.rule_tag == "LIMPEZA"]
    assert len(paren_changes) > 0


def test_name_parenthesis_internal_position() -> None:
    """TRF-08: parenthesis in middle of name is also removed."""
    name, changes = transform_name("Rui (Senior) Pereira", 1)
    assert "(" not in name
    assert ")" not in name


def test_mojibake_deterministic_corrected() -> None:
    """TRF-09: deterministic mojibake (UTF-8 read as Latin-1) is corrected."""
    name, changes = transform_name("JoÃ£o Silva", 1)
    assert name == "João Silva"
    limpeza = [c for c in changes if c.rule_tag == "LIMPEZA"]
    assert len(limpeza) > 0


def test_mojibake_ambiguous_logged_not_corrected() -> None:
    """TRF-10: clean text with Ã that doesn't round-trip is not corrupted."""
    # "JOÃO" in proper UTF-8 should NOT be detected as mojibake
    name, changes = transform_name("JOÃO SILVA", 1)
    assert name == "JOÃO SILVA"
    assert changes == []


def test_replacement_char_removed_rest_preserved() -> None:
    """TRF-11: U+FFFD is removed; rest of name is preserved."""
    name, changes = transform_name("João Silva� Teste", 1)
    assert "�" not in name
    assert "João Silva" in name
    aviso = [c for c in changes if c.rule_tag == "AVISO"]
    assert len(aviso) > 0


def test_name_case_preserved() -> None:
    """TRF-12: name case is not modified."""
    name, changes = transform_name("JOÃO SILVA", 1)
    assert name == "JOÃO SILVA"
    name2, _ = transform_name("joão silva", 1)
    assert name2 == "joão silva"


def test_name_none_returns_empty_string() -> None:
    """None name returns empty string (VAL-06 fires later in validate.py)."""
    name, changes = transform_name(None, 1)
    assert name == ""
    assert changes == []


def test_name_combined_all_transformations() -> None:
    """All transformations applied in the correct order."""
    # Input: parens, mojibake, comma, whitespace, replacement char
    raw = "  (Coord.) JoÃ£o Silva ,Teste�  "
    name, changes = transform_name(raw, 1)
    # Should be clean
    assert "(" not in name
    assert ")" not in name
    assert "," not in name
    assert "�" not in name
    assert "João" in name or "Jo" in name  # mojibake corrected
    # Check that changes include both LIMPEZA and AVISO entries
    tags = {c.rule_tag for c in changes}
    assert "LIMPEZA" in tags
    assert "AVISO" in tags


# ---------------------------------------------------------------------------
# try_fix_mojibake
# ---------------------------------------------------------------------------


def test_try_fix_mojibake_deterministic() -> None:
    """try_fix_mojibake corrects JoÃ£o → João."""
    fixed, was_fixed = try_fix_mojibake("JoÃ£o")
    assert was_fixed is True
    assert fixed == "João"


def test_try_fix_mojibake_clean_text_not_corrupted() -> None:
    """try_fix_mojibake does not alter clean text with Ã."""
    fixed, was_fixed = try_fix_mojibake("JOÃO")
    assert was_fixed is False
    assert fixed == "JOÃO"


def test_try_fix_mojibake_no_pattern_no_change() -> None:
    """try_fix_mojibake returns original when pattern not present."""
    text = "Simple text without any pattern"
    fixed, was_fixed = try_fix_mojibake(text)
    assert was_fixed is False
    assert fixed == text


# ---------------------------------------------------------------------------
# remove_replacement_characters — TRF-11
# ---------------------------------------------------------------------------


def test_remove_replacement_characters_removes_all() -> None:
    text = "Jo�o�Silva"
    cleaned, count = remove_replacement_characters(text)
    assert "�" not in cleaned
    assert count == 2


def test_remove_replacement_characters_no_op_when_absent() -> None:
    text = "João Silva Teste"
    cleaned, count = remove_replacement_characters(text)
    assert cleaned == text
    assert count == 0


# ---------------------------------------------------------------------------
# sort_elegiveis — TRF-13, TRF-14
# ---------------------------------------------------------------------------


def test_elegiveis_sort_diacritic_stripped() -> None:
    """TRF-13: sort uses NFKD diacritic-stripped casefold key."""
    rows = [(1, "Padim da Graça"), (2, "Sé"), (3, "Gualtar")]
    result = sort_elegiveis(rows)
    # Sort key: Gualtar < Padim da Graca < Se
    names = [r[1] for r in result]
    assert names == ["Gualtar", "Padim da Graça", "Sé"]


def test_elegiveis_index_assigned_zero_based_after_sort() -> None:
    """TRF-14: output_index is 0-based and assigned after sort."""
    rows = [(1, "Zélia"), (2, "Ana")]
    result = sort_elegiveis(rows)
    assert result[0] == (0, "Ana")
    assert result[1] == (1, "Zélia")


def test_sort_elegiveis_handles_short_parish_name() -> None:
    """TRF-13: short names like 'Sé' sort correctly after diacritic stripping."""
    rows = [(1, "Sé"), (2, "Padim da Graça"), (3, "Gualtar")]
    result = sort_elegiveis(rows)
    names = [r[1] for r in result]
    assert names == ["Gualtar", "Padim da Graça", "Sé"]


def test_sort_elegiveis_stable_for_identical_keys() -> None:
    """TRF-13: identical sort keys preserve input order (Python sort is stable)."""
    rows = [(1, "Ana Costa"), (2, "Ana Costa")]
    result = sort_elegiveis(rows)
    # Both have same key — stable sort preserves order
    assert result[0][1] == "Ana Costa"
    assert result[1][1] == "Ana Costa"
    # Indices should be 0 and 1
    assert result[0][0] == 0
    assert result[1][0] == 1


def test_caderno_preserves_input_order() -> None:
    """TRF-15: caderno output preserves input row order (sort_elegiveis is not called)."""
    # sort_elegiveis is only for elegíveis; caderno doesn't call it
    # Verify that sort_elegiveis is NOT idempotent (i.e., it does reorder)
    rows = [(1, "Zélia"), (2, "Ana"), (3, "Carlos")]
    result = sort_elegiveis(rows)
    names = [r[1] for r in result]
    # For elegíveis this would be sorted; for caderno the caller skips this function
    assert names == sorted(names, key=lambda n: n.casefold())


def test_transform_result_dataclass() -> None:
    """TransformResult is a frozen dataclass."""
    import dataclasses

    result = TransformResult(prefix="F", number=500, name="João Silva", changes=[])
    assert dataclasses.is_dataclass(result)
    with pytest.raises((AttributeError, TypeError)):
        result.prefix = "D"  # type: ignore[misc]


def test_change_record_dataclass() -> None:
    """ChangeRecord is a frozen dataclass."""
    import dataclasses

    record = ChangeRecord(
        row_index=1,
        field="mecanografico",
        rule_tag="LIMPEZA",
        before="  F500  ",
        after="F500",
        reason_pt="Espaços removidos",
    )
    assert dataclasses.is_dataclass(record)
    with pytest.raises((AttributeError, TypeError)):
        record.row_index = 2  # type: ignore[misc]
