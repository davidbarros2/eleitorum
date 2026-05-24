"""Unit tests for SessionModel @dataclass (plan 02-02, Task 1).

Tests verify the Qt-free data contract: all fields present, defaults None,
mutable (not frozen), no PySide6 imports.
"""

from __future__ import annotations

import ast
import pathlib


class TestSessionModel:
    """Requirement: D-05 — Qt-free session state contract."""

    def test_session_model_constructs_with_all_none_defaults(self) -> None:
        """SessionModel() produces instance with every field defaulting to None."""
        from eleitorum.ui.session import SessionModel

        s = SessionModel()
        assert s.output_type is None
        assert s.source_path is None
        assert s.sheet_name is None
        assert s.column_map is None
        assert s.pipeline_result is None
        assert s.output_path is None
        assert s.sheets is None
        assert s.column_headers is None

    def test_session_model_is_mutable(self) -> None:
        """SessionModel is NOT frozen — fields can be reassigned."""
        from eleitorum.ui.session import SessionModel

        s = SessionModel()
        s.output_type = "caderno"
        assert s.output_type == "caderno"
        s.output_type = "elegiveis"
        assert s.output_type == "elegiveis"

    def test_session_model_source_path_accepts_path_object(self) -> None:
        """source_path accepts pathlib.Path values."""
        from eleitorum.ui.session import SessionModel

        s = SessionModel()
        p = pathlib.Path("/tmp/sintetico_teste.xlsx")
        s.source_path = p
        assert s.source_path == p

    def test_session_model_output_path_accepts_path_object(self) -> None:
        """output_path accepts pathlib.Path values."""
        from eleitorum.ui.session import SessionModel

        s = SessionModel()
        p = pathlib.Path("/tmp/output_sintetico.csv")
        s.output_path = p
        assert s.output_path == p

    def test_session_model_column_map_accepts_dict(self) -> None:
        """column_map accepts a dict."""
        from eleitorum.ui.session import SessionModel

        s = SessionModel()
        s.column_map = {"mec": 0, "name": 1}
        assert s.column_map == {"mec": 0, "name": 1}

    def test_session_model_column_headers_accepts_list(self) -> None:
        """column_headers accepts a list of strings."""
        from eleitorum.ui.session import SessionModel

        s = SessionModel()
        s.column_headers = ["Mecanográfico", "Nome Completo", "Categoria"]
        assert s.column_headers == ["Mecanográfico", "Nome Completo", "Categoria"]

    def test_session_model_has_no_pyside6_imports(self) -> None:
        """session.py must never import from PySide6 (Qt-free contract)."""

        import eleitorum.ui.session as _mod

        src = pathlib.Path(_mod.__file__).read_text(encoding="utf-8")
        tree = ast.parse(src)
        pyside_imports = [
            node.module
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom) and node.module and "PySide6" in node.module
        ]
        assert not pyside_imports, f"PySide6 imports found in session.py: {pyside_imports}"

    def test_session_model_is_dataclass(self) -> None:
        """SessionModel must be decorated with @dataclasses.dataclass."""
        import dataclasses

        from eleitorum.ui.session import SessionModel

        assert dataclasses.is_dataclass(SessionModel)
        # Must NOT be frozen
        assert not SessionModel.__dataclass_params__.frozen  # type: ignore[attr-defined]

    def test_session_model_field_names(self) -> None:
        """SessionModel has exactly the required field names."""
        import dataclasses

        from eleitorum.ui.session import SessionModel

        field_names = {f.name for f in dataclasses.fields(SessionModel)}
        required = {
            "output_type",
            "source_path",
            "sheet_name",
            "column_map",
            "pipeline_result",
            "output_path",
            "sheets",
            "column_headers",
        }
        assert required.issubset(field_names), f"Missing fields: {required - field_names}"
