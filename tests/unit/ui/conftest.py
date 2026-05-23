"""Shared pytest-qt fixtures for the EleitorUM UI unit test suite (TST-10).

All synthetic data used in fixtures must include the word 'Teste', 'Exemplo',
or 'Sintetica' per Eleitorum.md Section 14.1. No real personal data may appear
in any test file.

pytest-qt automatically creates a QApplication via the ``qtbot`` fixture;
no explicit ``qapp`` autouse fixture is needed here.
"""

from __future__ import annotations

import pathlib

import pytest


@pytest.fixture
def session_fresh() -> None:
    """Placeholder fixture returning None.

    The real SessionModel fixture will be added in plan 02-02 once
    ``src/eleitorum/ui/session.py`` exists. Tests in this plan that need
    a source path construct it directly via ``tmp_path``.
    """
    return None
