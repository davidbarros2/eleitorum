"""Stub integration tests for the full EleitorUM pipeline.

Covers: end-to-end pipeline including PERF-01.
Implemented in plan 05 (pipeline module).
"""

import pytest


def test_happy_path_caderno_csv() -> None:
    # Requirement: OUT-01, OUT-02, OUT-03, OUT-04, OUT-05, OUT-06, OUT-07
    pytest.skip("implemented in plan 05 — pipeline module")


def test_happy_path_elegiveis_csv() -> None:
    # Requirement: OUT-01, OUT-08, OUT-09, TRF-13, TRF-14
    pytest.skip("implemented in plan 05 — pipeline module")


def test_multi_sheet_xlsx_processes_selected_sheet() -> None:
    # Requirement: INP-10
    pytest.skip("implemented in plan 05 — pipeline module")


def test_mojibake_file_corrected_end_to_end() -> None:
    # Requirement: TRF-09
    pytest.skip("implemented in plan 05 — pipeline module")


def test_duplicate_rejected_no_output_errors_log_created() -> None:
    # Requirement: VAL-03, OUT-10
    pytest.skip("implemented in plan 05 — pipeline module")


@pytest.mark.performance
def test_150k_rows_under_10_seconds() -> None:
    # Requirement: PERF-01
    pytest.skip("implemented in plan 05 — pipeline module")
