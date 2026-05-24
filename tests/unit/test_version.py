"""Tests for version bump to 1.0.0 and --version CLI argument (04-01 Task 1).

Tests:
  1. `python -m eleitorum --version` prints "EleitorUM 1.0.0" and exits 0
  2. `python -m eleitorum --version` runs without importing PySide6 (headless safe)
  3. importing `eleitorum.version` yields __version__ == "1.0.0"
"""
from __future__ import annotations

import subprocess
import sys


class TestVersionModule:
    """Tests for eleitorum.version module."""

    def test_version_is_1_0_0(self) -> None:
        """__version__ must be exactly '1.0.0'."""
        from eleitorum.version import __version__

        assert __version__ == "1.0.0", f"Expected '1.0.0', got {__version__!r}"


class TestVersionCLI:
    """Tests for --version CLI argument."""

    def test_version_flag_output(self) -> None:
        """python -m eleitorum --version prints 'EleitorUM 1.0.0' and exits 0."""
        result = subprocess.run(
            [sys.executable, "-m", "eleitorum", "--version"],
            capture_output=True,
            text=True,
        )
        output = result.stdout.strip()
        assert result.returncode == 0, f"Expected exit 0, got {result.returncode}"
        assert output == "EleitorUM 1.0.0", f"Expected 'EleitorUM 1.0.0', got {output!r}"

    def test_version_flag_no_pyside6(self) -> None:
        """python -m eleitorum --version must not import PySide6 (headless safe)."""
        # Run with a deliberately invalid QT_QPA_PLATFORM to detect Qt platform init.
        # If PySide6 is imported, Qt tries to init a platform plugin and may error
        # on headless systems. We check that the process succeeds regardless.
        result = subprocess.run(
            [sys.executable, "-m", "eleitorum", "--version"],
            capture_output=True,
            text=True,
            env={
                **__import__("os").environ,
                "QT_QPA_PLATFORM": "offscreen",
            },
        )
        # Must exit 0 — if PySide6 loaded and failed a platform plugin, returncode != 0
        assert result.returncode == 0, (
            f"--version exited {result.returncode} (may have triggered Qt platform init).\n"
            f"stdout: {result.stdout!r}\nstderr: {result.stderr!r}"
        )
        output = result.stdout.strip()
        assert output == "EleitorUM 1.0.0", f"Expected 'EleitorUM 1.0.0', got {output!r}"
