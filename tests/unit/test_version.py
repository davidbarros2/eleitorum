"""Tests for version bump to 1.0.0 and --version CLI argument (04-01 Task 1).

Tests:
  1. `python -m eleitorum --version` prints "EleitorUM 1.0.0" and exits 0
  2. `python -m eleitorum --version` runs without importing PySide6 (headless safe)
  3. importing `eleitorum.version` yields __version__ == "1.0.0"
"""
from __future__ import annotations

import os
import pathlib
import subprocess
import sys

# When running via `pytest` from the repo root, eleitorum is importable via
# the pythonpath configured in pyproject.toml [tool.pytest.ini_options].
# Subprocess invocations need the same PYTHONPATH injected explicitly.
_REPO_ROOT = pathlib.Path(__file__).parent.parent.parent
_SRC_DIR = str(_REPO_ROOT / "src")


def _subprocess_env() -> dict[str, str]:
    """Build subprocess env with src/ on PYTHONPATH."""
    env = dict(os.environ)
    existing = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = f"{_SRC_DIR}{os.pathsep}{existing}" if existing else _SRC_DIR
    return env


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
            env=_subprocess_env(),
        )
        output = result.stdout.strip()
        assert result.returncode == 0, f"Expected exit 0, got {result.returncode}"
        assert output == "EleitorUM 1.0.0", f"Expected 'EleitorUM 1.0.0', got {output!r}"

    def test_version_flag_no_pyside6(self) -> None:
        """python -m eleitorum --version must not import PySide6 (headless safe).

        Runs with QT_QPA_PLATFORM=offscreen which Qt always accepts,
        but verifies the --version path exits 0 regardless of platform plugin
        availability (it should never reach Qt init).
        """
        env = _subprocess_env()
        env["QT_QPA_PLATFORM"] = "offscreen"
        result = subprocess.run(
            [sys.executable, "-m", "eleitorum", "--version"],
            capture_output=True,
            text=True,
            env=env,
        )
        assert result.returncode == 0, (
            f"--version exited {result.returncode} (may have triggered Qt platform init).\n"
            f"stdout: {result.stdout!r}\nstderr: {result.stderr!r}"
        )
        output = result.stdout.strip()
        assert output == "EleitorUM 1.0.0", f"Expected 'EleitorUM 1.0.0', got {output!r}"
