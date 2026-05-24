"""Regression test: no institution name strings remain in source or config files.

Requirement: D-01 — BRAND-04. Scans src/, README.md, and pyproject.toml for any
occurrence of institution names ('Universidade' or 'UMinho').
Fails if any match is found, listing every offending file, line number, and content.
"""
from __future__ import annotations

import pathlib
import re

_SCAN_ROOTS: list[pathlib.Path] = [
    pathlib.Path("src"),
    pathlib.Path("README.md"),
    pathlib.Path("pyproject.toml"),
]
_PATTERN: re.Pattern[str] = re.compile(r"Universidade|UMinho")


class TestNoUminhoStrings:
    """Requirement: BRAND-04 — no institution name references in source or config."""

    def test_no_institution_references_in_source_or_config(self) -> None:
        """No file in src/, README.md, or pyproject.toml may reference institution names per D-01."""  # noqa: E501
        violations: list[str] = []
        for root in _SCAN_ROOTS:
            if root.is_file():
                files = [root]
            elif root.is_dir():
                files = list(root.rglob("*.py"))
            else:
                continue
            for path in files:
                text = path.read_text(encoding="utf-8", errors="replace")
                for lineno, line in enumerate(text.splitlines(), start=1):
                    if _PATTERN.search(line):
                        violations.append(f"{path}:{lineno}: {line.strip()}")
        assert not violations, (
            "Institution references found — remove per D-01:\n" + "\n".join(violations)
        )
