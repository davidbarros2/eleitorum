"""Stub tests for the eleitorum.core.logging module.

Covers: LOG-01 through LOG-07.
Implemented in plan 04 (logging module).
"""

import pytest


def test_log_file_name_pattern() -> None:
    # Requirement: LOG-01
    pytest.skip("implemented in plan 04 — logging module")


def test_log_encoding_utf8_with_bom() -> None:
    # Requirement: LOG-02
    pytest.skip("implemented in plan 04 — logging module")


def test_log_line_format_timestamp_and_tag() -> None:
    # Requirement: LOG-02
    pytest.skip("implemented in plan 04 — logging module")


def test_log_all_nine_tags_defined() -> None:
    # Requirement: LOG-03 (INICIO, INPUT, COLUNA, CASO, LIMPEZA, AVISO, ERRO, SAIDA, FIM)
    pytest.skip("implemented in plan 04 — logging module")


def test_log_records_required_events() -> None:
    # Requirement: LOG-04
    pytest.skip("implemented in plan 04 — logging module")


def test_error_log_file_name_pattern() -> None:
    # Requirement: LOG-05
    pytest.skip("implemented in plan 04 — logging module")


def test_error_log_includes_row_col_value_message() -> None:
    # Requirement: LOG-06
    pytest.skip("implemented in plan 04 — logging module")


def test_log_written_only_to_user_chosen_location() -> None:
    # Requirement: LOG-07
    pytest.skip("implemented in plan 04 — logging module")
