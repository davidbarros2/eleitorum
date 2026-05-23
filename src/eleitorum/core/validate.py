"""Validation module: aggregated VAL-01..09 checks and output path guards.

All validation collects ALL failures before returning — never short-circuits
on the first failure (D-07 hard-error aggregation model).

Security note (T-1-04-06, ASVS V5):
- UniquenessTracker asserts uppercase prefix on entry (enforces Pitfall 6).
- validate_output_path resolves both paths via Path.resolve() to defeat
  path-traversal and symlink confusion attacks (T-1-04-01, ASVS V12).
"""

from __future__ import annotations

import dataclasses
import pathlib
from dataclasses import field
from typing import Literal

from eleitorum.core.errors import FailureRow, OutputPathError
from eleitorum.core.transform import FDB_SHARED


# ---------------------------------------------------------------------------
# UniquenessTracker
# ---------------------------------------------------------------------------


@dataclasses.dataclass
class UniquenessTracker:
    """Stateful accumulator: tracks seen (prefix, number) pairs for duplicate detection.

    F/D/B share a single numeric namespace (D-08 — FDB_SHARED).
    A/PG/ID/Q/EX each get their own independent namespace (VAL-05).

    Security: the ``record`` method asserts that ``prefix`` is uppercase on entry.
    transform_mecanografico always returns uppercase prefixes; this assertion
    catches any caller that bypasses the transform layer (T-1-04-06).
    """

    # fdb_seen: number → (original_prefix, raw_value, row_index_of_first_occurrence)
    fdb_seen: dict[int, tuple[str, str, int]] = field(default_factory=dict)

    # independent_seen: prefix → {number → (name, row_index_of_first_occurrence)}
    independent_seen: dict[str, dict[int, tuple[str, int]]] = field(default_factory=dict)

    def record(
        self,
        prefix: str,
        number: int,
        row_value: str,
        name: str,
        row_index: int,
    ) -> FailureRow | None:
        """Record a (prefix, number) pair. Returns a FailureRow on collision; None on success.

        Caller (validate_rows) collects all FailureRows before making any decision
        about raising — the loop NEVER breaks early (D-07).

        Args:
            prefix:     Uppercase mecanografico prefix (e.g., "F", "PG").
            number:     Positive integer extracted by transform_mecanografico.
            row_value:  The display form of the mecanografico (e.g., "F500").
            name:       Cleaned name (for inclusion in first-seen metadata).
            row_index:  1-based source row index for error reporting.
        """
        assert prefix == prefix.upper(), (
            f"UniquenessTracker.record() requires an uppercase prefix; "
            f"received {prefix!r}. Call transform_mecanografico before validate_rows."
        )

        if prefix in FDB_SHARED:
            # F, D, B all share one numeric namespace
            existing = self.fdb_seen.get(number)
            if existing is not None:
                first_prefix, _first_value, first_row = existing
                return FailureRow(
                    row_index=row_index,
                    column_name="número mecanográfico",
                    value=row_value,
                    message_pt=(
                        f"colisão F/D/B: o número {number} já existe como "
                        f"'{first_prefix}{number}' (linha {first_row})"
                    ),
                )
            self.fdb_seen[number] = (prefix, row_value, row_index)
            return None
        else:
            # Independent prefix namespace
            bucket = self.independent_seen.setdefault(prefix, {})
            if number in bucket:
                _first_name, first_row = bucket[number]
                return FailureRow(
                    row_index=row_index,
                    column_name="número mecanográfico",
                    value=row_value,
                    message_pt=(
                        f"duplicado dentro do prefixo {prefix}: o número "
                        f"{prefix}{number} já existe (linha {first_row})"
                    ),
                )
            bucket[number] = (name, row_index)
            return None


# ---------------------------------------------------------------------------
# ValidationOutcome
# ---------------------------------------------------------------------------


@dataclasses.dataclass
class ValidationOutcome:
    """Pure data result returned by validate_rows.

    When ``passed`` is True, callers can safely proceed to output.py.
    When ``passed`` is False, callers should write an error log and abort
    without creating any output file (D-07, OUT-10).
    """

    passed: bool
    failures: list[FailureRow]


# ---------------------------------------------------------------------------
# validate_rows
# ---------------------------------------------------------------------------


def validate_rows(
    transformed_rows: list[tuple[int, str, int, str]],
    output_type: Literal["caderno", "elegiveis"],
) -> ValidationOutcome:
    """Aggregate VAL-03..07 checks across all rows. Never raises; never short-circuits.

    Args:
        transformed_rows: Each element is (row_index, prefix, number, name).
            - row_index: 1-based source row number.
            - prefix:    Uppercase mecanografico prefix (e.g., "F", "PG").
                         This is the output of transform_mecanografico's prefix return.
            - number:    Positive integer (leading zeros already stripped).
            - name:      Cleaned name string (may be empty — VAL-06 catches that here).
        output_type: "caderno" or "elegiveis". Affects VAL-07 (caderno-only check).

    Returns:
        ValidationOutcome(passed=True, failures=[]) when all rows are valid.
        ValidationOutcome(passed=False, failures=[...]) when any row fails.
        failures is always a complete list — every failure from every row is present.

    Requirements covered:
        VAL-03: duplicate within independent prefix namespace
        VAL-04: F/D/B cross-prefix collision
        VAL-05: A/PG/ID/Q/EX independent namespaces (no collision between them)
        VAL-06: empty name after transform
        VAL-07: caderno requires valid mecanografico (non-empty prefix + positive number)
    """
    failures: list[FailureRow] = []
    tracker = UniquenessTracker()

    for row_idx, prefix, number, name in transformed_rows:
        # VAL-06: empty or blank name
        if not name or not name.strip():
            failures.append(
                FailureRow(
                    row_index=row_idx,
                    column_name="nome",
                    value="(vazio)",
                    message_pt="nome em branco após normalização",
                )
            )

        # VAL-07: caderno requires a valid mecanografico (non-empty prefix + positive number)
        if output_type == "caderno" and (not prefix or number <= 0):
            failures.append(
                FailureRow(
                    row_index=row_idx,
                    column_name="número mecanográfico",
                    value=f"{prefix}{number}",
                    message_pt=(
                        "número mecanográfico inválido para caderno: "
                        "prefixo e número positivo são obrigatórios"
                    ),
                )
            )
        elif output_type == "elegiveis" and number <= 0 and prefix:
            # For elegiveis, a non-positive number is also a problem
            failures.append(
                FailureRow(
                    row_index=row_idx,
                    column_name="número mecanográfico",
                    value=f"{prefix}{number}",
                    message_pt="número mecanográfico inválido: número deve ser positivo",
                )
            )

        # VAL-03/04/05: uniqueness tracking (only for rows with a valid prefix)
        if prefix:
            # Ensure prefix is uppercase before calling tracker (Pitfall 6 guard)
            safe_prefix = prefix.upper()
            dup = tracker.record(safe_prefix, number, f"{safe_prefix}{number}", name, row_idx)
            if dup is not None:
                failures.append(dup)

    return ValidationOutcome(passed=not failures, failures=failures)


# ---------------------------------------------------------------------------
# validate_output_path
# ---------------------------------------------------------------------------


def validate_output_path(
    input_path: pathlib.Path,
    output_path: pathlib.Path,
    overwrite_allowed: bool = False,
) -> None:
    """VAL-08 + OUT-12 pre-write guards.

    Security (T-1-04-01, ASVS V12): both paths are resolved via
    ``pathlib.Path.resolve(strict=False)`` before comparison to defeat
    path-traversal tricks, relative-vs-absolute confusion, and symlink
    redirection attacks.

    Args:
        input_path:        Path to the source input file.
        output_path:       Path the caller intends to write to.
        overwrite_allowed: If False, raises OutputPathError when output_path
                           already exists (OUT-12). If True, an existing file
                           is silently overwritten (caller has obtained user consent).

    Raises:
        OutputPathError(reason='same_as_input'):  When resolved paths are equal (VAL-08).
        OutputPathError(reason='already_exists'): When output exists and overwrite is not
                                                   permitted (OUT-12).
    Returns:
        None on success.
    """
    input_resolved = input_path.resolve(strict=False)
    output_resolved = output_path.resolve(strict=False)

    # VAL-08: output must not point to the same file as input
    if input_resolved == output_resolved:
        raise OutputPathError(path=output_path, reason="same_as_input")

    # OUT-12: refuse to overwrite an existing file without explicit consent
    if output_path.exists() and not overwrite_allowed:
        raise OutputPathError(path=output_path, reason="already_exists")

    return None
