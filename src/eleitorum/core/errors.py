"""Custom exception hierarchy for EleitorUM.

Every exception class carries an idiomatic PT-PT message (never English, never
Python traceback fragments) and optional structured details for programmatic use.

This module is the import target of every core module. Its API is stable from
Wave 1 onward.
"""

from __future__ import annotations

import dataclasses
import pathlib
from typing import Any, Literal

# ---------------------------------------------------------------------------
# Accepted extensions text (shared between errors.py and readers.py display)
# ---------------------------------------------------------------------------

_ACCEPTED_EXTS_TEXT: tuple[str, ...] = (
    ".xlsx",
    ".xlsm",
    ".xls",
    ".ods",
    ".csv",
    ".tsv",
)


# ---------------------------------------------------------------------------
# FailureRow dataclass (used by ValidationError)
# ---------------------------------------------------------------------------


@dataclasses.dataclass(frozen=True)
class FailureRow:
    """A single validation failure, referenced by row index and offending value."""

    row_index: int  # 1-based source row (for user display)
    column_name: str  # column name as seen in source header
    value: str  # offending raw value (stringified)
    message_pt: str  # one-line PT-PT description

    def __post_init__(self) -> None:
        if self.row_index < 1:
            raise ValueError(f"row_index must be >= 1 (got {self.row_index})")


# ---------------------------------------------------------------------------
# Base exception
# ---------------------------------------------------------------------------


class EleitorumError(Exception):
    """Base for all custom exceptions.

    Carries ``message_pt`` (idiomatic PT-PT) and optional ``details`` dict
    (row/col/value/action). Never raised directly; subclasses are.
    """

    def __init__(self, message_pt: str, **details: Any) -> None:
        self.message_pt: str = message_pt
        self.details: dict[str, Any] = details
        super().__init__(message_pt)

    def __str__(self) -> str:
        return self.message_pt


# ---------------------------------------------------------------------------
# Concrete exception subclasses
# ---------------------------------------------------------------------------


class UnsupportedFormatError(EleitorumError):
    """INP-06: extension not in SUPPORTED_EXTENSIONS.

    Message lists all accepted formats.
    """

    def __init__(self, extension: str) -> None:
        accepted = ", ".join(_ACCEPTED_EXTS_TEXT)
        message_pt = (
            f"O tipo de ficheiro '{extension}' não é suportado. "
            f"Formatos aceites: {accepted}."
        )
        super().__init__(message_pt, extension=extension)


class FileAccessError(EleitorumError):
    """INP-13 / VAL-09: PermissionError on read or write.

    PT-PT message instructs the user to close the file in the other application
    and retry.
    """

    def __init__(self, path: pathlib.Path, mode: Literal["read", "write"]) -> None:
        if mode == "read":
            message_pt = (
                f"Não foi possível abrir o ficheiro '{path}'. "
                "Verifique se está aberto noutro programa (por exemplo, no Excel) "
                "e tente novamente."
            )
        else:
            message_pt = (
                f"Não foi possível gravar em '{path}'. "
                "Feche o ficheiro no programa que o tem aberto e tente novamente."
            )
        super().__init__(message_pt, path=str(path), mode=mode)


class EncodingDetectionError(EleitorumError):
    """INP-08: encoding could not be determined.

    PT-PT actionable message (suggests re-saving as UTF-8).
    """

    def __init__(self, path: pathlib.Path | None = None) -> None:
        message_pt = (
            "Não foi possível identificar a codificação do ficheiro. "
            "Tente abri-lo e guardá-lo novamente em UTF-8."
        )
        super().__init__(message_pt, path=str(path) if path is not None else None)


class MecanograficoError(EleitorumError):
    """VAL-01, VAL-02: invalid prefix or non-positive number.

    Carries the row index and the offending raw value in ``details``.
    """

    def __init__(self, row_index: int, value: str, reason: str) -> None:
        message_pt = (
            f"Linha {row_index}: o número mecanográfico '{value}' é inválido "
            f"— {reason}. Corrija o ficheiro de origem e tente novamente."
        )
        super().__init__(message_pt, row_index=row_index, value=value, reason=reason)
        self.row_index = row_index
        self.value = value
        self.reason = reason


class ValidationError(EleitorumError):
    """VAL-03, VAL-04, VAL-06, VAL-07: aggregated validation failures.

    Carries ``failures: list[FailureRow]`` where each FailureRow has
    (row_index, column_name, value, message_pt).
    """

    def __init__(self, failures: list[FailureRow], summary_pt: str) -> None:
        lines = [summary_pt]
        for f in failures:
            lines.append(f"  - Linha {f.row_index}: {f.value} ({f.message_pt})")
        message_pt = "\n".join(lines)
        super().__init__(message_pt, failure_count=len(failures))
        self.failures: list[FailureRow] = failures


class OutputPathError(EleitorumError):
    """VAL-08, OUT-11, OUT-12: output path equals input or already exists."""

    def __init__(
        self,
        path: pathlib.Path,
        reason: Literal["same_as_input", "already_exists"],
    ) -> None:
        if reason == "same_as_input":
            message_pt = (
                f"O ficheiro de saída '{path}' é o mesmo que o ficheiro de entrada. "
                "Escolha um nome diferente para o ficheiro de saída."
            )
        else:
            message_pt = (
                f"O ficheiro de destino '{path}' já existe. "
                "Confirme a substituição ou escolha um nome diferente."
            )
        super().__init__(message_pt, path=str(path), reason=reason)


class ColumnDetectionError(EleitorumError):
    """DET-02 fallthrough: required column could not be detected.

    Used by pipeline.py to surface the manual-mapping signal.
    """

    def __init__(self, missing: Literal["mecanografico", "name"]) -> None:
        if missing == "mecanografico":
            message_pt = (
                "Não foi possível detetar automaticamente a coluna do número "
                "mecanográfico. Por favor, selecione a coluna correspondente."
            )
        else:
            message_pt = (
                "Não foi possível detetar automaticamente a coluna do nome. "
                "Por favor, selecione a coluna correspondente."
            )
        super().__init__(message_pt, missing=missing)


# ---------------------------------------------------------------------------
# Module-level helper
# ---------------------------------------------------------------------------


def format_error_message(err: EleitorumError) -> str:
    """Format any EleitorumError as a multi-line PT-PT message.

    Suitable for writing to the _ERRORS_ log file (LOG-06). Never includes
    Python traceback, file paths from the call stack, or exception class names.
    """
    # Re-emit only the PT-PT message — never call traceback.format_exc() or
    # any frame-introspection. This is the V7 ASVS mitigation (no stack-trace
    # leakage).
    return err.message_pt
