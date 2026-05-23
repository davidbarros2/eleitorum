"""Stub tests for the eleitorum.core.transform module.

Covers: TRF-01 through TRF-15.
Implemented in plan 03 (transform module).
"""

import pytest


def test_mec_whitespace_removed() -> None:
    # Requirement: TRF-01
    pytest.skip("implemented in plan 03 — transform module")


def test_mec_float_to_int_string() -> None:
    # Requirement: TRF-02
    pytest.skip("implemented in plan 03 — transform module")


def test_mec_leading_zeros_stripped() -> None:
    # Requirement: TRF-03
    pytest.skip("implemented in plan 03 — transform module")


def test_prefix_case_normalization_lowercase_majority() -> None:
    # Requirement: TRF-04
    pytest.skip("implemented in plan 03 — transform module")


def test_prefix_case_normalization_uppercase_majority() -> None:
    # Requirement: TRF-04
    pytest.skip("implemented in plan 03 — transform module")


def test_prefix_case_normalization_tie_defaults_lowercase() -> None:
    # Requirement: TRF-04
    pytest.skip("implemented in plan 03 — transform module")


def test_name_whitespace_strip_includes_nbsp_zwsp() -> None:
    # Requirement: TRF-05
    pytest.skip("implemented in plan 03 — transform module")


def test_name_internal_whitespace_collapsed() -> None:
    # Requirement: TRF-06
    pytest.skip("implemented in plan 03 — transform module")


def test_name_comma_removed() -> None:
    # Requirement: TRF-07
    pytest.skip("implemented in plan 03 — transform module")


def test_name_parenthesis_removed_and_rewhitespaced() -> None:
    # Requirement: TRF-08
    pytest.skip("implemented in plan 03 — transform module")


def test_mojibake_deterministic_corrected() -> None:
    # Requirement: TRF-09
    pytest.skip("implemented in plan 03 — transform module")


def test_mojibake_ambiguous_logged_not_corrected() -> None:
    # Requirement: TRF-10
    pytest.skip("implemented in plan 03 — transform module")


def test_replacement_char_removed_rest_preserved() -> None:
    # Requirement: TRF-11
    pytest.skip("implemented in plan 03 — transform module")


def test_name_case_preserved() -> None:
    # Requirement: TRF-12
    pytest.skip("implemented in plan 03 — transform module")


def test_elegiveis_sort_diacritic_stripped() -> None:
    # Requirement: TRF-13
    pytest.skip("implemented in plan 03 — transform module")


def test_elegiveis_index_assigned_zero_based_after_sort() -> None:
    # Requirement: TRF-14
    pytest.skip("implemented in plan 03 — transform module")


def test_caderno_preserves_input_order() -> None:
    # Requirement: TRF-15
    pytest.skip("implemented in plan 03 — transform module")
