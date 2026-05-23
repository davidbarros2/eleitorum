"""Custom exception hierarchy for EleitorUM.

Every exception class here:
- Subclasses EleitorumError (which subclasses Exception)
- Carries an idiomatic PT-PT message in `message_pt`
- Never includes Python stack traces or English technical terms in user-visible output

Security note (ASVS V7 / T-1-02-01): format_error_message() re-emits only
``message_pt`` and never calls traceback.format_exc() or any frame-introspection.
"""

from __future__ import annotations

import dataclasses
import pathlib
from typing import Any, Literal

# ---------------------------------------------------------------------------
# Module-level ordering constant (shared with readers.py SUPPORTED_EXTENSIONS)
# ---------------------------------------------------------------------------

_ACCEPTED_EXTS_TEXT: str = ".xlsx, .xlsm, .xls, .ods, .csv, .tsv"


# ---------------------------------------------------------------------------
# FailureRow — immutable record for aggregated validation failures
# ---------------------------------------------------------------------------


@dataclasses.dataclass(frozen=True)
class FailureRow:
    """A single row-level validation failure, used by ValidationError.

    All indices are 1-based (as presented to the user in the error log).
    """

    row_index: int  # 1-based source row index for user display
    column_name: str  # column name as seen in source header
    value: str  # offending raw value (stringified)
    message_pt: str  # one-line PT-PT description

    def __post_init__(self) -> None:
        if self.row_index < 1:
            raise ValueError(
                f"row_index deve ser >= 1 (1-based); recebido: {self.row_index}"
            )


# ---------------------------------------------------------------------------
# Base exception
# ---------------------------------------------------------------------------


class EleitorumError(Exception):
    """Base class for all EleitorUM custom exceptions.

    Subclasses never raise EleitorumError directly; they each provide a
    typed ``__init__`` that constructs an idiomatic PT-PT ``message_pt``.

    Attributes
    ----------
    message_pt:
        Idiomatic European Portuguese (PT-PT) message suitable for display to
        the end user. Never contains Python tracebacks or English technical terms.
    details:
        Optional keyword arguments forwarded from the subclass ``__init__`` for
        programmatic inspection (e.g. ``row_index``, ``extension``).
    """

    def __init__(self, message_pt: str, **details: Any) -> None:
        super().__init__(message_pt)
        self.message_pt: str = message_pt
        self.details: dict[str, Any] = details

    def __str__(self) -> str:
        return self.message_pt


# ---------------------------------------------------------------------------
# Subclasses — one per failure domain
# ---------------------------------------------------------------------------


class UnsupportedFormatError(EleitorumError):
    """INP-06: File extension not in SUPPORTED_EXTENSIONS.

    The PT-PT message lists all accepted formats so the user knows exactly
    what to convert to.
    """

    def __init__(self, extension: str) -> None:
        message_pt = (
            f"O tipo de ficheiro '{extension}' não é suportado. "
            f"Formatos aceites: {_ACCEPTED_EXTS_TEXT}."
        )
        super().__init__(message_pt, extension=extension)


class FileAccessError(EleitorumError):
    """INP-13 / VAL-09: PermissionError on read or write.

    The ``mode`` argument selects between two distinct PT-PT messages:
    - ``"read"``  → instructs the user to close the file in another application.
    - ``"write"`` → instructs the user to close the destination in another
                    application.
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
    """INP-08: Encoding could not be determined by charset-normalizer.

    The PT-PT message includes a verbatim actionable instruction from
    Eleitorum.md Section 4.2: re-save as UTF-8.
    """

    def __init__(self, path: pathlib.Path) -> None:
        message_pt = (
            f"Não foi possível identificar a codificação do ficheiro '{path}'. "
            "Tente abri-lo e guardá-lo novamente em UTF-8."
        )
        super().__init__(message_pt, path=str(path))


class MecanograficoError(EleitorumError):
    """VAL-01, VAL-02: Invalid mecanográfico — bad prefix or non-positive number.

    Carries the 1-based ``row_index`` and the offending raw ``value`` in
    ``details`` so the error log can reference them precisely.
    """

    def __init__(self, row_index: int, value: str, reason: str) -> None:
        message_pt = (
            f"Linha {row_index}: o número mecanográfico '{value}' é inválido — "
            f"{reason}. Corrija o ficheiro de origem e tente novamente."
        )
        super().__init__(message_pt, row_index=row_index, value=value, reason=reason)


class ValidationError(EleitorumError):
    """VAL-03, VAL-04, VAL-06, VAL-07: Aggregated validation failures.

    ``summary_pt`` is a one-line PT-PT summary (e.g. "Encontradas N linhas
    inválidas."). The full message appends each failure as an indented line.
    ``failures`` is also accessible directly for programmatic inspection by
    pipeline.py and the logging module.
    """

    def __init__(self, failures: list[FailureRow], summary_pt: str) -> None:
        lines = [summary_pt]
        for f in failures:
            lines.append(f"  - Linha {f.row_index}: {f.value} ({f.message_pt})")
        message_pt = "\n".join(lines)
        super().__init__(message_pt, failure_count=len(failures))
        self.failures: list[FailureRow] = failures


class OutputPathError(EleitorumError):
    """VAL-08, OUT-11, OUT-12: Output path collision.

    Two distinct instantiations:
    - ``"same_as_input"``   → the output path equals the input path (VAL-08).
    - ``"already_exists"``  → destination exists; user has not consented (OUT-12).
    """

    def __init__(
        self,
        path: pathlib.Path,
        reason: Literal["same_as_input", "already_exists"],
    ) -> None:
        if reason == "same_as_input":
            message_pt = (
                f"O ficheiro de saída '{path}' é o mesmo que o ficheiro de entrada. "
                "Escolha um caminho diferente para não sobrescrever o original."
            )
        else:
            message_pt = (
                f"O ficheiro '{path}' já existe. "
                "Confirme a substituição ou escolha um nome diferente para o ficheiro de saída."
            )
        super().__init__(message_pt, path=str(path), reason=reason)


class ColumnDetectionError(EleitorumError):
    """DET-02 fallthrough: required column could not be auto-detected.

    ``missing`` identifies which column type failed detection. Used by
    pipeline.py to surface the manual-mapping signal to the UI layer.
    """

    def __init__(self, missing: Literal["mecanografico", "name"]) -> None:
        if missing == "mecanografico":
            column_label = "do número mecanográfico"
            hint = "mec., mecanográfico ou número de pessoal"
        else:
            column_label = "do nome / designação"
            hint = "nome, designação ou name"
        message_pt = (
            f"Não foi possível detetar automaticamente a coluna {column_label}. "
            f"Procure uma coluna com um cabeçalho semelhante a: {hint}. "
            "Se nenhuma corresponder, utilize o mapeamento manual."
        )
        super().__init__(message_pt, missing=missing)


# ---------------------------------------------------------------------------
# Module-level helper
# ---------------------------------------------------------------------------


def format_error_message(err: EleitorumError) -> str:
    """Format any EleitorumError as a PT-PT message for writing to the error log.

    Security invariant (T-1-02-01 / ASVS V7): this function MUST NOT call
    ``traceback.format_exc()``, ``inspect`` frames, or any introspection that
    would expose Python internals. It re-emits only ``err.message_pt``.

    For ValidationError the message is already multi-line (summary + per-row
    details). For all other subclasses, the message is a single PT-PT sentence.
    """
    return err.message_pt
