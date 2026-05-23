"""PERF-01 performance benchmark: 150,000-row XLSX in under 10 seconds.

This test is marked @pytest.mark.performance so it can be excluded from
quick CI runs via ``pytest -m "not performance"``.

Run with: ``python -m pytest tests/integration/test_performance.py -v``
"""

import pathlib
import time

import pytest

from eleitorum.core.pipeline import run_pipeline


@pytest.mark.performance
def test_150k_rows_under_10_seconds(
    huge_caderno_xlsx_path: pathlib.Path,
    tmp_path: pathlib.Path,
) -> None:
    """PERF-01: 150,000-row XLSX must complete in under 10 seconds.

    Per RESEARCH.md benchmark: ~3.8s openpyxl read + ~0.35s processing = ~4.1s
    total on the developer machine. The 10-second limit gives 2.4× headroom for
    CI and slower machines.

    The session-scoped ``huge_caderno_xlsx_path`` fixture builds the file once;
    this test only measures pipeline execution time.
    """
    output = tmp_path / "out.csv"

    start = time.perf_counter()
    result = run_pipeline(huge_caderno_xlsx_path, "caderno", output)
    elapsed = time.perf_counter() - start

    assert result.success, f"pipeline failed on 150k rows: {result.failures[:5]}"
    assert result.rows_processed == 150_000, (
        f"expected 150000 rows processed, got {result.rows_processed}"
    )
    assert elapsed < 10.0, f"PERF-01 violated: {elapsed:.2f}s (budget 10.0s)"

    # Sanity check: output is byte-exact
    raw = output.read_bytes()
    assert raw[:3] == b"\xef\xbb\xbf", "BOM missing in 150k output"
    assert raw.endswith(b"\r\n"), "no trailing CRLF in 150k output"

    # Print timing for visibility (visible with -s or in CI logs)
    print(f"\nPERF-01: {result.rows_processed:,} rows in {elapsed:.2f}s")
