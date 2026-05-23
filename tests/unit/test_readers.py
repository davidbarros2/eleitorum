"""Stub tests for the eleitorum.core.readers module.

Covers: INP-01 through INP-13.
Implemented in plan 02 (readers module).
"""

import pytest


def test_read_xlsx_basic() -> None:
    # Requirement: INP-01
    pytest.skip("implemented in plan 02 — readers module")


def test_read_xls_legacy() -> None:
    # Requirement: INP-02
    pytest.skip("implemented in plan 02 — readers module")


def test_read_ods() -> None:
    # Requirement: INP-03
    pytest.skip("implemented in plan 02 — readers module")


def test_read_csv_utf8_bom() -> None:
    # Requirement: INP-04, INP-07
    pytest.skip("implemented in plan 02 — readers module")


def test_read_csv_utf8_no_bom() -> None:
    # Requirement: INP-07
    pytest.skip("implemented in plan 02 — readers module")


def test_read_csv_cp1252() -> None:
    # Requirement: INP-07
    pytest.skip("implemented in plan 02 — readers module")


def test_read_tsv() -> None:
    # Requirement: INP-05
    pytest.skip("implemented in plan 02 — readers module")


def test_unsupported_extension_raises() -> None:
    # Requirement: INP-06
    pytest.skip("implemented in plan 02 — readers module")


def test_permission_error_on_locked_file() -> None:
    # Requirement: INP-13
    pytest.skip("implemented in plan 02 — readers module")


def test_xlsx_uses_read_only_and_data_only() -> None:
    # Requirement: PERF-03
    pytest.skip("implemented in plan 02 — readers module")


def test_multi_sheet_xlsx_returns_sheet_names_and_counts() -> None:
    # Requirement: INP-10
    pytest.skip("implemented in plan 02 — readers module")


def test_empty_sheet_flagged() -> None:
    # Requirement: INP-11
    pytest.skip("implemented in plan 02 — readers module")


def test_skip_trailing_empty_rows_logged_count() -> None:
    # Requirement: INP-12
    pytest.skip("implemented in plan 02 — readers module")
