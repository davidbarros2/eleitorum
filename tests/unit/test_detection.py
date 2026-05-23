"""Stub tests for the eleitorum.core.detection module.

Covers: DET-01 through DET-07, INP-07 through INP-09.
Implemented in plan 03 (detection module).
"""

import pytest


def test_detect_encoding_utf8_bom() -> None:
    # Requirement: INP-07
    pytest.skip("implemented in plan 03 — detection module")


def test_detect_encoding_utf8_no_bom() -> None:
    # Requirement: INP-07
    pytest.skip("implemented in plan 03 — detection module")


def test_detect_encoding_cp1252() -> None:
    # Requirement: INP-07
    pytest.skip("implemented in plan 03 — detection module")


def test_detect_encoding_iso_8859_1_fallback() -> None:
    # Requirement: INP-07
    pytest.skip("implemented in plan 03 — detection module")


def test_detect_encoding_undetectable_raises_pt_pt() -> None:
    # Requirement: INP-08
    pytest.skip("implemented in plan 03 — detection module")


def test_detect_encoding_logs_choice() -> None:
    # Requirement: INP-09
    pytest.skip("implemented in plan 03 — detection module")


def test_header_row_scoring_picks_best_of_first_10() -> None:
    # Requirement: DET-01
    pytest.skip("implemented in plan 03 — detection module")


def test_no_header_returns_manual_mapping_signal() -> None:
    # Requirement: DET-02
    pytest.skip("implemented in plan 03 — detection module")


def test_mec_column_synonym_match_nfkd() -> None:
    # Requirement: DET-03
    pytest.skip("implemented in plan 03 — detection module")


def test_name_column_synonym_match_nfkd() -> None:
    # Requirement: DET-04
    pytest.skip("implemented in plan 03 — detection module")


def test_detection_result_metadata_for_ui() -> None:
    # Requirement: DET-05
    pytest.skip("implemented in plan 03 — detection module")


def test_ambiguous_detection_returns_all_candidates() -> None:
    # Requirement: DET-06
    pytest.skip("implemented in plan 03 — detection module")


def test_elegiveis_hides_mec_mapping() -> None:
    # Requirement: DET-07
    pytest.skip("implemented in plan 03 — detection module")


def test_format_fallback_regex_when_no_synonym_matches() -> None:
    # Requirement: DET-01, D-01 hybrid detection
    pytest.skip("implemented in plan 03 — detection module")
