"""Unit tests for strings.py PT-PT constants (plan 02-02, Task 1).

Tests use AST inspection to enumerate all module-level uppercase assignments
and verify: every required constant is present, every value is a non-empty
PT-PT string (no English keywords), and format placeholders match spec.
"""

from __future__ import annotations

import ast
import pathlib
import re

# Required string constant names per 02-02-PLAN.md <behavior>
REQUIRED_CONSTANTS = [
    "STEP_1_TITLE",
    "STEP_2_TITLE",
    "STEP_25_TITLE",
    "STEP_3_TITLE",
    "STEP_4_TITLE",
    "STEP_DONE_SUCCESS_TITLE",
    "STEP_DONE_ERROR_TITLE",
    "STEP_PROCESSING_TITLE",
    "STEP_INDICATOR",
    "BTN_ANTERIOR",
    "BTN_PROXIMO",
    "BTN_CANCELAR",
    "BTN_GRAVAR",
    "BTN_COMECAR",
    "BTN_SAIR",
    "BTN_PROCESSAR_OUTRO",
    "BTN_ABRIR_PASTA",
    "BTN_ALTERAR",
    "BTN_VER_LOG",
    "BTN_FECHAR_LOG",
    "BTN_ESCOLHER_FICHEIRO",
    "BTN_CONFIRM_CANCEL",
    "BTN_CONTINUE",
    "PROCESSING_LOADING",
    "PROCESSING_PROGRESS",
    "CONFIRM_CANCEL",
    "DROP_ZONE_PLACEHOLDER",
    "ERR_UNSUPPORTED_EXT",
    "ERR_FILE_OPEN",
    "ERR_OUTPUT_SAME_AS_INPUT",
    "ERR_OUTPUT_OPEN",
    "ERR_OUTPUT_EXISTS_PROMPT",
    "ERR_NO_DETECTION_HEADING",
    "ERR_NO_DETECTION_BODY",
    "OPTION_CADERNO_HEADING",
    "OPTION_CADERNO_DESC",
    "OPTION_ELEGIVEIS_HEADING",
    "OPTION_ELEGIVEIS_DESC",
    "OPEN_DIALOG_TITLE",
    "OPEN_DIALOG_FILTER",
    "SAVE_DIALOG_TITLE",
    "SAVE_DIALOG_FILTER",
    "SHEET_PICKER_EMPTY_SUFFIX",
    "SHEET_PICKER_ROWS_TEMPLATE",
    "MENU_FILE",
    "MENU_VIEW",
    "MENU_HELP",
    "MENU_REINICIAR",
    "MENU_SAIR",
    "MENU_TEMA_CLARO",
    "MENU_TEMA_ESCURO",
    "MENU_BOAS_VINDAS",
    "MENU_SOBRE",
    "ABOUT_DESCRIPTION",
    "ABOUT_LICENSE",
    "ABOUT_REPO_LINK_LABEL",
    "WELCOME_HEADING",
    "WELCOME_BODY",
    "DONE_PRONTO",
    "DONE_SUCCESS_SUMMARY",
    "DONE_ERROR_HEADING",
    "DONE_ERROR_BODY",
    "COL_MAPPING_HIGH",
    "COL_MAPPING_LOW",
    "PREVIEW_TOTAL_ROWS",
]

# English words that must NOT appear as standalone words in PT-PT strings
ENGLISH_BLOCKLIST = {"Next", "Cancel", "Open", "Save", "File", "Close", "Help", "About"}


def _parse_strings_module() -> dict[str, str]:
    """Parse strings.py and return dict of name -> value for uppercase module-level strings.

    Handles both plain assignments (ast.Assign) and annotated assignments
    (ast.AnnAssign — e.g. STEP_1_TITLE: str = "...").
    """
    import eleitorum.ui.strings as _mod

    src = pathlib.Path(_mod.__file__).read_text(encoding="utf-8")
    tree = ast.parse(src)
    constants: dict[str, str] = {}

    for node in tree.body:  # only top-level module statements
        # Annotated assignment: NAME: type = value
        if isinstance(node, ast.AnnAssign):
            if not isinstance(node.target, ast.Name):
                continue
            name = node.target.id
            if not name.isupper():
                continue
            if node.value is None:
                continue
            try:
                value = ast.literal_eval(node.value)
                if isinstance(value, str):
                    constants[name] = value
            except (ValueError, TypeError):
                pass

        # Plain assignment: NAME = value  (or NAME = NAME1 + NAME2)
        elif isinstance(node, ast.Assign):
            for target in node.targets:
                if not isinstance(target, ast.Name):
                    continue
                name = target.id
                if not name.isupper():
                    continue
                try:
                    value = ast.literal_eval(node.value)
                    if isinstance(value, str):
                        constants[name] = value
                except (ValueError, TypeError):
                    pass

    return constants


class TestStrings:
    """Requirement: APP-20 — all PT-PT UI strings centralized in strings.py."""

    def test_strings_importable_without_qapplication(self) -> None:
        """strings.py must import without a running QApplication."""
        from eleitorum.ui import strings  # noqa: F401

        assert strings is not None

    def test_all_required_constants_present(self) -> None:
        """Every constant in the required list must be defined."""
        constants = _parse_strings_module()
        missing = [name for name in REQUIRED_CONSTANTS if name not in constants]
        assert not missing, f"Missing constants in strings.py: {missing}"

    def test_all_values_are_nonempty_strings(self) -> None:
        """Every uppercase constant must be a non-empty string."""
        constants = _parse_strings_module()
        empty = [name for name, value in constants.items() if not value.strip()]
        assert not empty, f"Empty string constants: {empty}"

    def test_no_english_keywords_in_values(self) -> None:
        """No English keywords from the blocklist should appear as standalone words."""
        constants = _parse_strings_module()
        violations: list[str] = []
        for name, value in constants.items():
            for word in ENGLISH_BLOCKLIST:
                # Word boundary match — case sensitive
                if re.search(rf"\b{re.escape(word)}\b", value):
                    violations.append(f"{name}: contains English word '{word}'")
        assert not violations, "English keywords found in PT-PT strings:\n" + "\n".join(violations)

    def test_step_indicator_has_n_and_total_placeholders(self) -> None:
        """STEP_INDICATOR must contain {n} and {total} format placeholders."""
        from eleitorum.ui.strings import STEP_INDICATOR

        assert "{n}" in STEP_INDICATOR, "STEP_INDICATOR missing {n} placeholder"
        assert "{total}" in STEP_INDICATOR, "STEP_INDICATOR missing {total} placeholder"
        # Verify it formats correctly
        result = STEP_INDICATOR.format(n=2, total=5)
        assert "2" in result and "5" in result

    def test_processing_progress_has_current_and_total(self) -> None:
        """PROCESSING_PROGRESS must contain {current} and {total} placeholders."""
        from eleitorum.ui.strings import PROCESSING_PROGRESS

        assert "{current}" in PROCESSING_PROGRESS
        assert "{total}" in PROCESSING_PROGRESS

    def test_err_unsupported_ext_has_ext_placeholder(self) -> None:
        """ERR_UNSUPPORTED_EXT must contain {ext} placeholder."""
        from eleitorum.ui.strings import ERR_UNSUPPORTED_EXT

        assert "{ext}" in ERR_UNSUPPORTED_EXT
        result = ERR_UNSUPPORTED_EXT.format(ext=".docx")
        assert ".docx" in result

    def test_sheet_picker_rows_template_has_rows_placeholder(self) -> None:
        """SHEET_PICKER_ROWS_TEMPLATE must contain {rows} placeholder."""
        from eleitorum.ui.strings import SHEET_PICKER_ROWS_TEMPLATE

        assert "{rows}" in SHEET_PICKER_ROWS_TEMPLATE

    def test_done_success_summary_has_rows_and_changes(self) -> None:
        """DONE_SUCCESS_SUMMARY must contain {rows} and {changes} placeholders."""
        from eleitorum.ui.strings import DONE_SUCCESS_SUMMARY

        assert "{rows}" in DONE_SUCCESS_SUMMARY
        assert "{changes}" in DONE_SUCCESS_SUMMARY
