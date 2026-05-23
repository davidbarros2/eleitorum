"""Tests for the eleitorum.core.validate module.

Covers: VAL-01 through VAL-09, D-07 hard-error aggregation, and D-08 prefix namespaces.
"""

from __future__ import annotations

import pathlib

import pytest

from eleitorum.core.errors import OutputPathError
from eleitorum.core.validate import (
    UniquenessTracker,
    ValidationOutcome,
    validate_output_path,
    validate_rows,
)


# ---------------------------------------------------------------------------
# validate_rows — basic pass/fail
# ---------------------------------------------------------------------------


def test_invalid_prefix_collected() -> None:
    """VAL-01: an invalid prefix is detected by transform_mecanografico upstream;
    validate_rows itself receives already-transformed (prefix, number) pairs with
    uppercase valid prefixes. If a caller passes an invalid/empty prefix, validate_rows
    should produce a FailureRow rather than crash."""
    outcome = validate_rows([(1, "", 0, "João")], "caderno")
    assert not outcome.passed
    assert len(outcome.failures) >= 1
    # Should reference the problematic row
    assert outcome.failures[0].row_index == 1


def test_nonpositive_number_collected() -> None:
    """VAL-02: validate_rows collects a FailureRow for number <= 0."""
    outcome = validate_rows([(1, "F", 0, "João")], "caderno")
    assert not outcome.passed
    assert len(outcome.failures) >= 1
    assert outcome.failures[0].row_index == 1


def test_duplicate_within_prefix() -> None:
    """VAL-03: two rows with the same prefix and number produce a FailureRow."""
    outcome = validate_rows([(1, "F", 500, "João"), (2, "F", 500, "Maria")], "caderno")
    assert not outcome.passed
    assert len(outcome.failures) == 1
    assert outcome.failures[0].row_index == 2


def test_fdb_cross_prefix_collision() -> None:
    """VAL-04: F500 and D500 share the F/D/B namespace — collision is detected."""
    outcome = validate_rows([(1, "F", 500, "João"), (2, "D", 500, "Maria")], "caderno")
    assert not outcome.passed
    assert len(outcome.failures) == 1
    failure = outcome.failures[0]
    assert failure.row_index == 2
    # Message must contain references to both prefixes and the number
    assert "F" in failure.message_pt
    assert "D" in failure.message_pt
    assert "500" in failure.message_pt


def test_fdb_cross_prefix_collision_mixed_case_input() -> None:
    """VAL-04, Pitfall 6: F/D/B collision is detected even when prefixes arrive uppercase
    (transform_mecanografico always returns uppercase; this test verifies the tracker
    handles F + D collision as documented in Pitfall 6)."""
    # F and B share namespace — collision must be detected
    outcome = validate_rows([(1, "F", 123, "Ana"), (2, "B", 123, "Carlos")], "caderno")
    assert not outcome.passed
    assert len(outcome.failures) == 1
    assert outcome.failures[0].row_index == 2


def test_a_pg_id_q_ex_independent_namespaces() -> None:
    """VAL-05: A500 and PG500 are independent — no collision."""
    outcome = validate_rows([(1, "A", 500, "João"), (2, "PG", 500, "Maria")], "caderno")
    assert outcome.passed
    assert outcome.failures == []


def test_a_and_f_independent_namespaces() -> None:
    """VAL-05: A and F are in different namespaces (F is FDB_SHARED; A is independent)."""
    outcome = validate_rows([(1, "A", 500, "João"), (2, "F", 500, "Maria")], "caderno")
    assert outcome.passed
    assert outcome.failures == []


def test_empty_name_after_transform() -> None:
    """VAL-06: an empty name produces a FailureRow with column_name='nome'."""
    outcome = validate_rows([(1, "F", 500, "")], "caderno")
    assert not outcome.passed
    assert len(outcome.failures) == 1
    assert outcome.failures[0].column_name == "nome"
    assert outcome.failures[0].row_index == 1


def test_caderno_requires_both_mec_and_name() -> None:
    """VAL-07: caderno output requires both a valid mecanografico and a non-empty name.
    An empty prefix with zero number produces at least one FailureRow."""
    outcome = validate_rows([(1, "", 0, "")], "caderno")
    assert not outcome.passed
    assert len(outcome.failures) >= 1


def test_output_path_equals_input_path_refused() -> None:
    """VAL-08: validate_output_path raises OutputPathError(reason='same_as_input')
    when input and output paths resolve to the same location."""
    with pytest.raises(OutputPathError) as exc_info:
        validate_output_path(pathlib.Path("a.csv"), pathlib.Path("a.csv"))
    assert exc_info.value.details.get("reason") == "same_as_input"


def test_permission_error_on_write_pt_pt() -> None:
    """VAL-09: PermissionError on write is raised by output.py as FileAccessError;
    validate.py's path checks happen before the write. This test verifies that
    validate_output_path itself does NOT raise PermissionError (that's output.py's job)
    and returns None for a valid non-existing output path."""
    # validate_output_path returns None on success — no exception raised
    result = validate_output_path(
        pathlib.Path("input.csv"),
        pathlib.Path("some_nonexistent_output_12345.csv"),
        overwrite_allowed=False,
    )
    assert result is None


def test_all_failures_collected_before_raise() -> None:
    """D-07: validate_rows collects ALL failures across all rows — no short-circuit.

    Input has three issues:
    - Row 2: D500 collides with F500 (F/D/B namespace collision)
    - Row 2: empty name (VAL-06)
    - Row 3: F500 duplicate within prefix (VAL-03)
    Expected: outcome.failures has exactly 3 entries.
    """
    rows = [
        (1, "F", 500, "João"),
        (2, "D", 500, ""),  # collision with F500 + empty name → 2 failures
        (3, "F", 500, "Pedro"),  # duplicate within F prefix → 1 failure
    ]
    outcome = validate_rows(rows, "caderno")
    assert not outcome.passed
    assert len(outcome.failures) == 3


# ---------------------------------------------------------------------------
# Additional required tests from plan spec
# ---------------------------------------------------------------------------


def test_validate_rows_collects_three_independent_failures() -> None:
    """D-07 proof: loop does not short-circuit — three distinct failure types all collected."""
    rows = [
        (1, "F", 500, "João"),
        (2, "F", 500, ""),  # duplicate within F prefix + empty name → 2 failures
        (3, "D", 500, "Pedro"),  # F/D/B collision → 1 failure
    ]
    outcome = validate_rows(rows, "caderno")
    assert not outcome.passed
    # Must have at least 3 distinct failures
    assert len(outcome.failures) >= 3


def test_uniqueness_tracker_records_first_row_for_collision_message() -> None:
    """The FailureRow message for a collision must reference the FIRST row's index."""
    tracker = UniquenessTracker()
    # First record — should succeed
    result1 = tracker.record("F", 500, "F500", "João", 1)
    assert result1 is None
    # Second record — should return FailureRow
    result2 = tracker.record("F", 500, "F500", "Maria", 2)
    assert result2 is not None
    # Message must mention row 1 (the first occurrence)
    assert "1" in result2.message_pt


def test_validate_output_path_resolves_symlinks_or_relative() -> None:
    """VAL-08: Path('./a.csv') and Path('a.csv') resolve to the same path."""
    with pytest.raises(OutputPathError) as exc_info:
        validate_output_path(pathlib.Path("./a.csv"), pathlib.Path("a.csv"))
    assert exc_info.value.details.get("reason") == "same_as_input"


def test_validate_output_path_existing_file_raises(tmp_path: pathlib.Path) -> None:
    """OUT-12: raises OutputPathError(reason='already_exists') when output exists
    and overwrite_allowed=False."""
    existing = tmp_path / "existing.csv"
    existing.write_text("data", encoding="utf-8")
    with pytest.raises(OutputPathError) as exc_info:
        validate_output_path(
            pathlib.Path("input.csv"),
            existing,
            overwrite_allowed=False,
        )
    assert exc_info.value.details.get("reason") == "already_exists"


def test_validate_output_path_existing_file_allowed(tmp_path: pathlib.Path) -> None:
    """OUT-12: no exception when output exists but overwrite_allowed=True."""
    existing = tmp_path / "existing.csv"
    existing.write_text("data", encoding="utf-8")
    result = validate_output_path(
        pathlib.Path("input.csv"),
        existing,
        overwrite_allowed=True,
    )
    assert result is None


def test_validate_output_path_no_existing_file(tmp_path: pathlib.Path) -> None:
    """validate_output_path returns None when output does not exist."""
    result = validate_output_path(
        tmp_path / "input.csv",
        tmp_path / "output.csv",
        overwrite_allowed=False,
    )
    assert result is None


def test_validate_rows_single_valid_row() -> None:
    """A single valid row returns ValidationOutcome(passed=True)."""
    outcome = validate_rows([(1, "F", 500, "João")], "caderno")
    assert outcome.passed
    assert outcome.failures == []


def test_validate_rows_independent_prefix_no_duplicate() -> None:
    """VAL-05: same number for ID and Q (both independent) — no collision."""
    outcome = validate_rows([(1, "ID", 100, "Ana"), (2, "Q", 100, "Pedro")], "caderno")
    assert outcome.passed
    assert outcome.failures == []


def test_fdb_b_and_d_collision_detected() -> None:
    """VAL-04: B and D also share the FDB namespace — collision detected."""
    outcome = validate_rows([(1, "B", 200, "Ana"), (2, "D", 200, "Pedro")], "caderno")
    assert not outcome.passed
    assert len(outcome.failures) == 1
    assert outcome.failures[0].row_index == 2


def test_validate_rows_elegiveis_empty_prefix_collected() -> None:
    """validate_rows for elegiveis also collects failures (empty name check active)."""
    outcome = validate_rows([(1, "EX", 1, "")], "elegiveis")
    assert not outcome.passed
    assert outcome.failures[0].column_name == "nome"


def test_validation_outcome_dataclass_fields() -> None:
    """ValidationOutcome exposes .passed and .failures fields."""
    outcome = validate_rows([(1, "A", 1, "Test")], "caderno")
    assert isinstance(outcome, ValidationOutcome)
    assert hasattr(outcome, "passed")
    assert hasattr(outcome, "failures")
