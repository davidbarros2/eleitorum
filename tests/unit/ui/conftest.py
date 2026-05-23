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

from eleitorum.ui.session import SessionModel


@pytest.fixture
def session_fresh() -> SessionModel:
    """Return a fresh SessionModel with all fields defaulting to None.

    Updated in plan 02-02 from the placeholder None stub.
    """
    return SessionModel()


@pytest.fixture
def session_with_file(tmp_path: pathlib.Path) -> SessionModel:
    """Return a SessionModel with source_path set to a synthetic XLSX path."""
    s = SessionModel()
    s.source_path = tmp_path / "sintetico_teste.xlsx"
    return s
