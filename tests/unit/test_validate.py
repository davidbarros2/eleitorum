"""Stub tests for the eleitorum.core.validate module.

Covers: VAL-01 through VAL-09.
Implemented in plan 04 (validate module).
"""

import pytest


def test_invalid_prefix_collected() -> None:
    # Requirement: VAL-01
    pytest.skip("implemented in plan 04 — validate module")


def test_nonpositive_number_collected() -> None:
    # Requirement: VAL-02
    pytest.skip("implemented in plan 04 — validate module")


def test_duplicate_within_prefix() -> None:
    # Requirement: VAL-03
    pytest.skip("implemented in plan 04 — validate module")


def test_fdb_cross_prefix_collision() -> None:
    # Requirement: VAL-04
    pytest.skip("implemented in plan 04 — validate module")


def test_fdb_cross_prefix_collision_mixed_case_input() -> None:
    # Requirement: VAL-04, Pitfall 6
    pytest.skip("implemented in plan 04 — validate module")


def test_a_pg_id_q_ex_independent_namespaces() -> None:
    # Requirement: VAL-05
    pytest.skip("implemented in plan 04 — validate module")


def test_empty_name_after_transform() -> None:
    # Requirement: VAL-06
    pytest.skip("implemented in plan 04 — validate module")


def test_caderno_requires_both_mec_and_name() -> None:
    # Requirement: VAL-07
    pytest.skip("implemented in plan 04 — validate module")


def test_output_path_equals_input_path_refused() -> None:
    # Requirement: VAL-08
    pytest.skip("implemented in plan 04 — validate module")


def test_permission_error_on_write_pt_pt() -> None:
    # Requirement: VAL-09
    pytest.skip("implemented in plan 04 — validate module")


def test_all_failures_collected_before_raise() -> None:
    # Requirement: D-07 hard-error aggregation
    pytest.skip("implemented in plan 04 — validate module")
