"""Shared pytest fixtures and synthetic data constants for the EleitorUM test suite.

All names are obviously synthetic per Eleitorum.md Section 14.1 — they include
the words "Teste", "Exemplo", or "Sintetica" so they can never be confused with
real personal data. No real personal data may appear in any test file.
"""

import pathlib

import openpyxl  # type: ignore[import-untyped]
import pytest

# ---------------------------------------------------------------------------
# Synthetic data constants
# ---------------------------------------------------------------------------

SYNTHETIC_NAMES: tuple[str, ...] = (
    "João Silva Teste",
    "Maria Costa Exemplo",
    "Ana Pereira Sintetica",
    "Carlos Oliveira Teste",
    "Rui Ferreira Exemplo",
    "Sofia Santos Sintetica",
    "Marta Rodrigues Teste",
    "Pedro Martins Exemplo",
    "Inês Gomes Sintetica",
    "Tiago Lopes Teste",
)

# Valid mecanografico prefixes per D-08 from CONTEXT.md
SYNTHETIC_PREFIXES: tuple[str, ...] = ("A", "PG", "ID", "F", "D", "B", "Q", "EX")


# ---------------------------------------------------------------------------
# Shared pytest fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def tmp_csv_path(tmp_path: pathlib.Path) -> pathlib.Path:
    """Return a temporary path with a .csv extension."""
    return tmp_path / "test_output.csv"


@pytest.fixture
def tmp_xlsx_path(tmp_path: pathlib.Path) -> pathlib.Path:
    """Return a temporary path with a .xlsx extension."""
    return tmp_path / "test_output.xlsx"


@pytest.fixture
def synthetic_names() -> tuple[str, ...]:
    """Return the tuple of synthetic PT names for use in tests."""
    return SYNTHETIC_NAMES


# ---------------------------------------------------------------------------
# Performance fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def huge_caderno_xlsx_path(tmp_path_factory: pytest.TempPathFactory) -> pathlib.Path:
    """Build a 150,000-row synthetic XLSX once per test session (PERF-01).

    Session-scoped so the expensive file creation happens at most once per
    test run, regardless of how many performance tests reference this fixture.

    The generated file uses 'f{i}' mec numbers and 'Sintetico Teste {i}' names
    to satisfy the privacy invariant (all names unmistakably synthetic).
    """
    path = tmp_path_factory.mktemp("perf") / "huge_caderno.xlsx"
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append(["No Mec.", "Nome"])
    for i in range(1, 150_001):
        ws.append([f"f{i}", f"Sintetico Teste {i}"])
    wb.save(path)
    wb.close()
    return path
