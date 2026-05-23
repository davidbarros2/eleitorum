"""Tests for the eleitorum.core.errors module.

Covers: VAL-01 through VAL-09 error message coverage, plus PT-PT message
verification for all custom exception classes.
"""

from __future__ import annotations

import pathlib

import pytest

from eleitorum.core.errors import (
    ColumnDetectionError,
    EleitorumError,
    EncodingDetectionError,
    FailureRow,
    FileAccessError,
    MecanograficoError,
    OutputPathError,
    UnsupportedFormatError,
    ValidationError,
    format_error_message,
)

# English keywords that must never appear in PT-PT user-facing messages.
_ENGLISH_KEYWORDS = ["error", "exception", "traceback", "file \""]
# Python internals that must never appear in format_error_message output.
_PYTHON_INTERNALS = ["Traceback", "File \"", '.py", line']


class TestEleitorumErrorBase:
    """Requirement: VAL-01 — base error class with PT-PT message and details."""

    def test_eleitourum_error_base_class(self) -> None:
        err = EleitorumError("Mensagem de teste em português.", param1="valor1")
        assert isinstance(err, Exception)
        assert err.message_pt == "Mensagem de teste em português."
        assert err.details == {"param1": "valor1"}
        assert str(err) == "Mensagem de teste em português."

    def test_base_error_no_details(self) -> None:
        err = EleitorumError("Sem detalhes.")
        assert err.details == {}

    def test_base_error_str_returns_pt_pt(self) -> None:
        msg = "Ocorreu um erro durante o processamento."
        err = EleitorumError(msg)
        assert str(err) == msg

    def test_base_error_not_english(self) -> None:
        err = EleitorumError("O ficheiro não pôde ser aberto.")
        msg_lower = err.message_pt.lower()
        for eng in _ENGLISH_KEYWORDS:
            assert eng not in msg_lower, f"English keyword '{eng}' found in message"


class TestUnsupportedFormatError:
    """Requirement: INP-06 — unsupported extension raises with all accepted formats listed."""

    def test_unsupported_format_error_lists_accepted(self) -> None:
        err = UnsupportedFormatError(extension=".docx")
        assert isinstance(err, EleitorumError)
        assert ".docx" in err.message_pt
        assert ".xlsx" in err.message_pt
        assert ".csv" in err.message_pt
        assert ".tsv" in err.message_pt
        assert ".xls" in err.message_pt
        assert ".ods" in err.message_pt

    def test_unsupported_extension_has_no_english(self) -> None:
        err = UnsupportedFormatError(extension=".pdf")
        msg_lower = err.message_pt.lower()
        for eng in _ENGLISH_KEYWORDS:
            assert eng not in msg_lower

    def test_unsupported_extension_is_in_message(self) -> None:
        err = UnsupportedFormatError(extension=".xlsm")
        # Even if xlsm is now supported, the message should reference the extension
        assert ".xlsm" in err.message_pt

    def test_unsupported_format_no_python_internals(self) -> None:
        err = UnsupportedFormatError(extension=".docx")
        output = format_error_message(err)
        for internal in _PYTHON_INTERNALS:
            assert internal not in output


class TestFileAccessError:
    """Requirement: INP-13, VAL-09 — file access error with read/write distinction."""

    def test_permission_error_pt_pt_message(self) -> None:
        path = pathlib.Path("synthetic.xlsx")
        err = FileAccessError(path=path, mode="read")
        assert isinstance(err, EleitorumError)
        # Must reference the path
        assert "synthetic.xlsx" in err.message_pt
        # PT-PT: open/locked message
        assert "aberto" in err.message_pt or "abrir" in err.message_pt

    def test_file_access_write_mode_message(self) -> None:
        path = pathlib.Path("output.csv")
        err = FileAccessError(path=path, mode="write")
        assert "output.csv" in err.message_pt
        assert "gravar" in err.message_pt

    def test_file_access_read_not_write_keyword(self) -> None:
        path = pathlib.Path("synthetic.xlsx")
        err = FileAccessError(path=path, mode="read")
        # Read mode should NOT contain "gravar"
        assert "gravar" not in err.message_pt

    def test_file_access_write_not_read_keyword(self) -> None:
        path = pathlib.Path("synthetic.xlsx")
        err = FileAccessError(path=path, mode="write")
        # Write mode should contain "gravar", not "abrir o ficheiro"
        assert "gravar" in err.message_pt

    def test_file_access_no_english(self) -> None:
        path = pathlib.Path("test.xlsx")
        for mode in ("read", "write"):
            err = FileAccessError(path=path, mode=mode)  # type: ignore[arg-type]
            msg_lower = err.message_pt.lower()
            for eng in _ENGLISH_KEYWORDS:
                assert eng not in msg_lower, f"English '{eng}' in {mode} mode message"


class TestEncodingDetectionError:
    """Requirement: INP-08 — encoding detection failure with actionable PT-PT message."""

    def test_encoding_detection_error_actionable_message(self) -> None:
        path = pathlib.Path("data.csv")
        err = EncodingDetectionError(path=path)
        assert isinstance(err, EleitorumError)
        # Must contain exact spec sentence
        assert "Tente abri-lo e guardá-lo novamente em UTF-8." in err.message_pt

    def test_encoding_detection_no_english(self) -> None:
        path = pathlib.Path("data.csv")
        err = EncodingDetectionError(path=path)
        msg_lower = err.message_pt.lower()
        for eng in _ENGLISH_KEYWORDS:
            assert eng not in msg_lower


class TestMecanograficoError:
    """Requirement: VAL-01, VAL-02 — invalid mecanográfico number."""

    def test_mecanografico_error_message_is_pt_pt(self) -> None:
        err = MecanograficoError(row_index=47, value="X500", reason="prefixo inválido")
        assert isinstance(err, EleitorumError)
        assert "47" in err.message_pt
        assert "X500" in err.message_pt
        assert "prefixo" in err.message_pt

    def test_mecanografico_error_has_row_index(self) -> None:
        err = MecanograficoError(row_index=1, value="f0", reason="número não positivo")
        assert "1" in err.message_pt

    def test_mecanografico_error_no_english(self) -> None:
        err = MecanograficoError(row_index=5, value="Z999", reason="prefixo desconhecido")
        msg_lower = err.message_pt.lower()
        for eng in _ENGLISH_KEYWORDS:
            assert eng not in msg_lower


class TestValidationError:
    """Requirement: VAL-03, VAL-04 — aggregated validation failures."""

    def test_validation_error_collects_offending_rows(self) -> None:
        failures = [
            FailureRow(1, "nº mec.", "f6688", "duplicado na mesma lista"),
            FailureRow(3, "nº mec.", "f6688", "duplicado na mesma lista"),
        ]
        err = ValidationError(failures=failures, summary_pt="Encontradas 2 linhas inválidas.")
        assert isinstance(err, EleitorumError)
        assert err.failures == failures
        assert "Encontradas 2 linhas inválidas." in err.message_pt

    def test_validation_error_lists_each_failure_with_row_and_value(self) -> None:
        failures = [
            FailureRow(10, "nome", "Silva,", "vírgula no nome"),
            FailureRow(25, "nº mec.", "F500", "colisão entre prefixos"),
            FailureRow(42, "nome", "Ana (Diretora)", "anotação parentética"),
        ]
        err = ValidationError(failures=failures, summary_pt="3 erros de validação.")
        # Each row_index must appear in the message
        assert "10" in err.message_pt
        assert "25" in err.message_pt
        assert "42" in err.message_pt
        # Each value must appear in the message
        assert "Silva," in err.message_pt
        assert "F500" in err.message_pt
        assert "Ana (Diretora)" in err.message_pt
        # Summary must appear
        assert "3 erros de validação." in err.message_pt

    def test_validation_error_failures_accessible(self) -> None:
        failures = [FailureRow(1, "col", "val", "msg")]
        err = ValidationError(failures=failures, summary_pt="1 erro.")
        assert len(err.failures) == 1
        assert err.failures[0].row_index == 1

    def test_validation_error_no_english(self) -> None:
        failures = [FailureRow(1, "col", "v", "mensagem PT")]
        err = ValidationError(failures=failures, summary_pt="Erro encontrado.")
        msg_lower = err.message_pt.lower()
        for eng in _ENGLISH_KEYWORDS:
            assert eng not in msg_lower


class TestOutputPathError:
    """Requirement: VAL-08, OUT-11, OUT-12 — output path collision."""

    def test_output_path_same_as_input(self) -> None:
        path = pathlib.Path("caderno.csv")
        err = OutputPathError(path=path, reason="same_as_input")
        assert isinstance(err, EleitorumError)
        assert "caderno.csv" in err.message_pt

    def test_output_path_already_exists(self) -> None:
        path = pathlib.Path("resultado.csv")
        err = OutputPathError(path=path, reason="already_exists")
        assert "resultado.csv" in err.message_pt

    def test_output_path_same_vs_exists_differ(self) -> None:
        path = pathlib.Path("x.csv")
        err_same = OutputPathError(path=path, reason="same_as_input")
        err_exists = OutputPathError(path=path, reason="already_exists")
        # The two messages must be different PT-PT messages
        assert err_same.message_pt != err_exists.message_pt

    def test_output_path_no_english(self) -> None:
        path = pathlib.Path("test.csv")
        for reason in ("same_as_input", "already_exists"):
            err = OutputPathError(path=path, reason=reason)  # type: ignore[arg-type]
            msg_lower = err.message_pt.lower()
            for eng in _ENGLISH_KEYWORDS:
                assert eng not in msg_lower, f"English '{eng}' in reason={reason} message"


class TestColumnDetectionError:
    """Requirement: DET-02 — column could not be detected."""

    def test_column_detection_mecanografico(self) -> None:
        err = ColumnDetectionError(missing="mecanografico")
        assert isinstance(err, EleitorumError)
        # Must mention the missing column type
        assert "mecanogr" in err.message_pt.lower() or "mec" in err.message_pt.lower()

    def test_column_detection_name(self) -> None:
        err = ColumnDetectionError(missing="name")
        assert isinstance(err, EleitorumError)
        assert "nome" in err.message_pt.lower() or "designa" in err.message_pt.lower()

    def test_column_detection_no_english(self) -> None:
        err = ColumnDetectionError(missing="mecanografico")
        msg_lower = err.message_pt.lower()
        for eng in _ENGLISH_KEYWORDS:
            assert eng not in msg_lower


class TestFailureRow:
    """FailureRow dataclass — immutable, 1-based row index."""

    def test_failure_row_fields(self) -> None:
        row = FailureRow(row_index=5, column_name="nº mec.", value="f6688", message_pt="duplicado")
        assert row.row_index == 5
        assert row.column_name == "nº mec."
        assert row.value == "f6688"
        assert row.message_pt == "duplicado"

    def test_failure_row_is_frozen(self) -> None:
        row = FailureRow(row_index=1, column_name="col", value="v", message_pt="msg")
        with pytest.raises((AttributeError, TypeError)):
            row.row_index = 99  # type: ignore[misc]

    def test_failure_row_zero_index_rejected(self) -> None:
        with pytest.raises((AssertionError, ValueError)):
            FailureRow(row_index=0, column_name="col", value="v", message_pt="msg")

    def test_failure_row_negative_index_rejected(self) -> None:
        with pytest.raises((AssertionError, ValueError)):
            FailureRow(row_index=-1, column_name="col", value="v", message_pt="msg")


class TestFormatErrorMessage:
    """format_error_message must never leak Python internals."""

    def test_format_error_message_no_python_internals(self) -> None:
        errors: list[EleitorumError] = [
            UnsupportedFormatError(extension=".docx"),
            FileAccessError(path=pathlib.Path("x.xlsx"), mode="read"),
            FileAccessError(path=pathlib.Path("x.xlsx"), mode="write"),
            EncodingDetectionError(path=pathlib.Path("x.csv")),
            MecanograficoError(row_index=1, value="X", reason="prefixo inválido"),
            ValidationError(
                failures=[FailureRow(1, "col", "v", "msg")], summary_pt="1 erro."
            ),
            OutputPathError(path=pathlib.Path("out.csv"), reason="same_as_input"),
            OutputPathError(path=pathlib.Path("out.csv"), reason="already_exists"),
            ColumnDetectionError(missing="mecanografico"),
        ]
        for err in errors:
            output = format_error_message(err)
            for internal in _PYTHON_INTERNALS:
                assert internal not in output, (
                    f"{type(err).__name__}: found '{internal}' in format_error_message output"
                )
            # Additional Python-internal patterns
            assert "Exception" not in output
            assert "ValueError" not in output

    def test_format_error_message_validation_is_multiline(self) -> None:
        failures = [
            FailureRow(1, "col", "v1", "msg1"),
            FailureRow(2, "col", "v2", "msg2"),
        ]
        err = ValidationError(failures=failures, summary_pt="2 erros.")
        output = format_error_message(err)
        assert "\n" in output  # multi-line for ValidationError

    def test_format_error_message_returns_string(self) -> None:
        err = UnsupportedFormatError(extension=".pdf")
        result = format_error_message(err)
        assert isinstance(result, str)
        assert len(result) > 0
