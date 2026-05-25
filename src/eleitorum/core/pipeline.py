"""Pipeline orchestrator for EleitorUM core processing.

This module is the ONLY public API Phase 2 (Qt UI) should call.
Everything else in ``eleitorum.core`` is an implementation detail.

Qt-free contract: this module imports ONLY stdlib, eleitorum.core sub-modules,
and dataclasses. It NEVER imports Qt or any UI toolkit.

Security notes:
- T-1-05-01: All EleitorumError subclasses are caught and translated to
  PipelineResult(success=False). No Python traceback ever reaches the caller.
- T-1-05-02: The output CSV is written ONLY after validate_rows returns
  passed=True (OUT-10 enforced — never partially written).
- T-1-05-03: validate_output_path is called before any write attempt.
- T-1-05-04: readers.py uses openpyxl streaming mode (PERF-03); pipeline.py
  never imports openpyxl directly.
- T-1-05-05: progress_cb is opaque — called once per 100 rows + final.
- T-1-05-06: log files written only to intended_output_path.parent (LOG-07).
"""

from __future__ import annotations

import dataclasses
import pathlib
import re
from collections.abc import Callable
from typing import Any, Literal

from eleitorum.core import detection, output, readers, validate
from eleitorum.core import logging as elt_logging
from eleitorum.core.errors import (
    ColumnDetectionError,
    EleitorumError,
    FailureRow,
    MecanograficoError,
    format_error_message,
)
from eleitorum.core.transform import (
    ChangeRecord,
    normalize_mecanografico_case,
    transform_mecanografico,
    transform_name,
)

# ---------------------------------------------------------------------------
# Public dataclasses
# ---------------------------------------------------------------------------

_RAW_PREFIX_RE: re.Pattern[str] = re.compile(r"^\s*([A-Za-z]{1,2})")


@dataclasses.dataclass
class PipelineSource:
    """How to interpret the input. Most fields are optional and only used for
    Excel multi-sheet inputs or pre-resolved manual column mappings."""

    path: pathlib.Path
    sheet_name: str | None = None  # for multi-sheet Excel; None = first sheet
    manual_mec_col: int | None = None  # override DET-03 auto-detection; None = auto-detect
    manual_name_col: int | None = None  # override DET-04 auto-detection
    # override CSV delimiter; None = auto (';' for .csv, '\t' for .tsv)
    csv_delimiter: str | None = None
    encoding: str | None = None  # override INP-07 detection (rare; for testing)
    # When manual columns are given, use this header row index instead of 0.
    # Set by WizardController from its pre-scan result so the pipeline and the
    # wizard agree on which row is the header.
    manual_header_row_index: int | None = None


@dataclasses.dataclass
class PipelineResult:
    """Single return type for both success and failure."""

    success: bool
    output_path: pathlib.Path | None  # set on success
    log_path: pathlib.Path | None  # set on success
    error_log_path: pathlib.Path | None  # set on failure (instead of output + log)
    rows_processed: int
    transformations_applied: int
    # keys: encoding, header_row_index, mec_col_index, name_col_index, detection_method
    detection: dict[str, Any]
    failures: list[FailureRow]  # populated on failure
    log_entries: list[str]  # the log lines built during the run
    # Populated during dry-run (output_path=None) only — first 50 output rows as
    # string-converted cell values, used by StepPreview table. Empty on write-phase
    # runs. Additive field with default [] — Phase 1 tests are NOT affected.
    preview_rows: list[list[str]] = dataclasses.field(default_factory=list)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _normalize_source(
    source: PipelineSource | pathlib.Path | str,
) -> PipelineSource:
    """Coerce any input type to PipelineSource."""
    if isinstance(source, PipelineSource):
        return source
    if isinstance(source, (str, pathlib.Path)):
        return PipelineSource(path=pathlib.Path(source))
    raise TypeError(f"source must be a path or PipelineSource, got {type(source).__name__!r}")


def _build_failure_result(
    builder: elt_logging.LogBuilder,
    failures: list[FailureRow],
    error_log_path: pathlib.Path,
) -> PipelineResult:
    """Build a failure PipelineResult after writing the error log."""
    return PipelineResult(
        success=False,
        output_path=None,
        log_path=None,
        error_log_path=error_log_path,
        rows_processed=0,
        transformations_applied=0,
        detection={},
        failures=failures,
        log_entries=builder.entries,
    )


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------


def run_pipeline(
    source: PipelineSource | pathlib.Path | str,
    output_type: Literal["caderno", "elegiveis"],
    output_path: pathlib.Path | None = None,
    *,
    progress_cb: Callable[[int, int], None] | None = None,
    overwrite_allowed: bool = False,
) -> PipelineResult:
    """Main pipeline entry point. Qt-free.

    Args:
        source: file path or PipelineSource with options.
        output_type: 'caderno' or 'elegiveis'.
        output_path: destination CSV. If None, dry-run (validate only, no write).
        progress_cb: called as progress_cb(current_row, total_rows). D-04 contract.
        overwrite_allowed: pass True only after explicit user consent.

    Returns:
        PipelineResult — never raises EleitorumError subclasses; instead returns
        success=False with error_log_path populated.
        Genuinely unexpected exceptions (ImportError, MemoryError) DO propagate.
    """
    src = _normalize_source(source)
    builder = elt_logging.LogBuilder()
    builder.add("INICIO", f"Tipo de output: {output_type}")
    builder.add("INPUT", f"Ficheiro: {src.path}")

    # Determine the error log target used in the catch block
    intended_error_target = output_path if output_path else src.path.with_suffix(".csv")

    try:
        return _execute_pipeline(
            src=src,
            output_type=output_type,
            output_path=output_path,
            progress_cb=progress_cb,
            overwrite_allowed=overwrite_allowed,
            builder=builder,
            intended_error_target=intended_error_target,
        )
    except EleitorumError as e:
        builder.add("ERRO", format_error_message(e))
        error_log_path = elt_logging.write_error_log_file(
            builder, intended_output_path=intended_error_target
        )
        return _build_failure_result(builder, [], error_log_path)


def _execute_pipeline(
    *,
    src: PipelineSource,
    output_type: Literal["caderno", "elegiveis"],
    output_path: pathlib.Path | None,
    progress_cb: Callable[[int, int], None] | None,
    overwrite_allowed: bool,
    builder: elt_logging.LogBuilder,
    intended_error_target: pathlib.Path,
) -> PipelineResult:
    """Inner pipeline logic — all EleitorumError exceptions propagate to run_pipeline."""

    # ------------------------------------------------------------------
    # Step 5: Read input
    # ------------------------------------------------------------------
    # For CSV/TSV: determine the delimiter to use.
    # PipelineSource.csv_delimiter overrides auto-detection.
    # Default: ';' for .csv (EleitorUM output format), '\t' for .tsv.
    # Note: readers.read_input uses ',' as CSV delimiter; for EleitorUM
    # files we must override with ';'. We call read_csv_like directly
    # when a custom delimiter is needed.
    ext = src.path.suffix.lower()
    if ext in {".csv", ".tsv"} and src.csv_delimiter is not None:
        # Explicit override — bypass read_input dispatch
        read_result = readers.read_csv_like(
            src.path, delimiter=src.csv_delimiter, encoding=src.encoding or "utf-8-sig"
        )
    elif ext == ".csv":
        # EleitorUM default: semicolon CSV
        read_result = readers.read_csv_like(src.path, delimiter=";")
    elif ext == ".tsv":
        # TSV: readers.read_input already uses '\t', so delegate
        read_result = readers.read_input(src.path, sheet_name=src.sheet_name)
    else:
        read_result = readers.read_input(src.path, sheet_name=src.sheet_name)

    if read_result.sheet_name:
        builder.add("INPUT", f"Folha selecionada: {read_result.sheet_name}")
    if read_result.skipped_trailing_empty > 0:
        builder.add(
            "INPUT",
            f"Linhas vazias finais ignoradas: {read_result.skipped_trailing_empty}",
        )

    # ------------------------------------------------------------------
    # Step 8: CSV/TSV encoding detection + optional re-read
    # ------------------------------------------------------------------
    encoding_used: str | None = None
    if read_result.raw_bytes_sample is not None:
        if src.encoding:
            # Manual override: trust the caller; no detection needed
            encoding_used = src.encoding
        else:
            enc = detection.detect_encoding(read_result.raw_bytes_sample)
            builder.add(
                "INPUT",
                f"Codificação detetada: {enc.encoding} "
                f"(confiança {enc.confidence:.2f}, BOM={enc.via_bom})",
            )
            encoding_used = enc.encoding

            # If detected encoding differs from utf-8-sig and is a Western European
            # encoding, re-read with the correct encoding to handle mojibake cases
            # where the file was opened with the wrong codec.
            # NOTE: For Phase 1 v1 this path handles cp1252/iso-8859-1 CSV files.
            # Phase 2 may add a UI prompt for manual encoding confirmation.
            if encoding_used.lower() not in ("utf-8-sig", "utf-8", "utf_8_sig", "utf_8"):
                ext = src.path.suffix.lower()
                if ext in {".csv", ".tsv"}:
                    delimiter = (
                        src.csv_delimiter if src.csv_delimiter else ("\t" if ext == ".tsv" else ";")
                    )
                    read_result = readers.read_csv_like(
                        src.path, delimiter=delimiter, encoding=encoding_used
                    )

    # ------------------------------------------------------------------
    # Step 9: collect all rows
    # ------------------------------------------------------------------
    all_rows = read_result.rows

    # ------------------------------------------------------------------
    # Step 10: header detection
    # ------------------------------------------------------------------
    # For caderno: both columns must be specified to use manual mapping.
    # For elegiveis: mec column is always None (DET-07), so name column alone suffices.
    manual_mapping = (
        src.manual_name_col is not None
        and (output_type == "elegiveis" or src.manual_mec_col is not None)
    )

    header_row_index: int
    if manual_mapping:
        # Use the wizard-provided header row index when available; fall back to 0.
        header_row_index = src.manual_header_row_index if src.manual_header_row_index is not None else 0
    else:
        _detected_index = detection.detect_header_row(all_rows)
        if _detected_index is None:
            raise ColumnDetectionError(missing="mecanografico")
        header_row_index = _detected_index

    # ------------------------------------------------------------------
    # Step 11: extract header and data rows
    # ------------------------------------------------------------------
    header_row = all_rows[header_row_index]
    data_rows = all_rows[header_row_index + 1 :]

    # ------------------------------------------------------------------
    # Step 12: column detection or manual mapping
    # ------------------------------------------------------------------
    col_mapping: _ManualColumnMapping | detection.ColumnMapping
    if manual_mapping:
        # Build a minimal ColumnMapping-like namespace for the rest of the pipeline
        col_mapping = _ManualColumnMapping(
            mec_col_index=src.manual_mec_col,
            name_col_index=src.manual_name_col,
            mec_col_label="(manual)",
            name_col_label="(manual)",
            detection_method="manual",
        )
    else:
        col_mapping = detection.detect_columns(header_row, data_rows, output_type)

    # ------------------------------------------------------------------
    # Step 13/14: validate column indices
    # ------------------------------------------------------------------
    if output_type == "caderno" and col_mapping.mec_col_index is None:
        raise ColumnDetectionError(missing="mecanografico")
    if col_mapping.name_col_index is None:
        raise ColumnDetectionError(missing="name")

    # ------------------------------------------------------------------
    # Step 15/16: log column choices
    # ------------------------------------------------------------------
    if output_type == "caderno":
        builder.add(
            "COLUNA",
            f"Coluna mec: '{col_mapping.mec_col_label}' (metodo: {col_mapping.detection_method})",
        )
    builder.add("COLUNA", f"Coluna nome: '{col_mapping.name_col_label}'")

    # ------------------------------------------------------------------
    # Step 17: transform loop
    # ------------------------------------------------------------------
    transformed: list[tuple[int, str, int, str]] = []  # (row_idx, prefix, number, name)
    raw_prefix_strings: list[str] = []
    change_records: list[ChangeRecord] = []
    failures: list[FailureRow] = []
    total = len(data_rows)

    for i, raw_row in enumerate(data_rows):
        row_idx = header_row_index + 2 + i  # 1-based, includes header

        # Extract cell values safely
        mec_raw = (
            raw_row[col_mapping.mec_col_index]
            if col_mapping.mec_col_index is not None and col_mapping.mec_col_index < len(raw_row)
            else None
        )
        name_raw = (
            raw_row[col_mapping.name_col_index]
            if col_mapping.name_col_index is not None and col_mapping.name_col_index < len(raw_row)
            else None
        )

        # Caderno: transform mecanográfico
        prefix = ""
        number = 0
        if output_type == "caderno":
            try:
                prefix, number, mec_changes = transform_mecanografico(mec_raw, row_idx)
                change_records.extend(mec_changes)

                # Capture raw prefix string for batch case normalization (TRF-04)
                raw_mec_str = str(mec_raw) if mec_raw is not None else ""
                m = _RAW_PREFIX_RE.match(raw_mec_str)
                if m:
                    raw_prefix_strings.append(m.group(1))

            except MecanograficoError as me:
                failures.append(
                    FailureRow(
                        row_index=row_idx,
                        column_name="numero mecanografico",
                        value=str(mec_raw) if mec_raw is not None else "(vazio)",
                        message_pt=me.message_pt,
                    )
                )
                # Continue to next row — D-07 aggregation; do NOT stop here
                # Still attempt to transform the name for logging purposes
                _, name_changes = transform_name(name_raw, row_idx)
                change_records.extend(name_changes)
                continue

        # Transform name
        name, name_changes = transform_name(name_raw, row_idx)
        change_records.extend(name_changes)

        transformed.append((row_idx, prefix, number, name))

        # D-04 progress callback — every 100 rows and on final row
        if progress_cb is not None and (i % 100 == 0 or i == total - 1):
            progress_cb(i + 1, total)

    # ------------------------------------------------------------------
    # Step 18: batch case normalization (caderno only)
    # ------------------------------------------------------------------
    chosen_case: Literal["lower", "upper"] = "lower"
    if output_type == "caderno" and transformed:
        # normalize_mecanografico_case takes list[TransformResult] as first arg
        # but only uses raw_prefix_strings; pass empty list for transforms
        chosen_case, _low, _upp, case_record = normalize_mecanografico_case([], raw_prefix_strings)
        change_records.append(case_record)

    # ------------------------------------------------------------------
    # Step 19: add change records to log
    # ------------------------------------------------------------------
    for cr in change_records:
        builder.add_change(cr.row_index, cr)

    # ------------------------------------------------------------------
    # Step 20: validate rows + merge failures
    # ------------------------------------------------------------------
    outcome = validate.validate_rows(transformed, output_type)
    failures.extend(outcome.failures)

    if failures:
        # Add ERRO lines for each failure
        for f in failures:
            builder.add(
                "ERRO",
                f"Linha {f.row_index}: {f.column_name} = '{f.value}' — {f.message_pt}",
            )
        builder.add("FIM", f"Processamento interrompido. {len(failures)} erros.")
        error_log_path = elt_logging.write_error_log_file(
            builder, intended_output_path=output_path or src.path.with_suffix(".csv")
        )
        return _build_failure_result(builder, failures, error_log_path)

    # ------------------------------------------------------------------
    # Step 21: dry-run guard
    # ------------------------------------------------------------------
    if output_path is None:
        # Build preview_rows snapshot — first 50 output rows as string lists.
        # This is a deep copy of string-converted cell values; no live references
        # into pipeline internal state. Only populated on dry-run (output_path=None)
        # so that StepPreview can render a table without needing a written CSV.
        _preview: list[list[str]] = []
        if output_type == "caderno":
            for _row_idx, prefix, number, name in transformed[:50]:
                if chosen_case == "lower":
                    _mec_str = f"{prefix.lower()}{number}"
                else:
                    _mec_str = f"{prefix.upper()}{number}"
                _preview.append([_mec_str, name, ""])  # category always empty
        else:
            # elegiveis: index + designation (index assigned during output phase;
            # for preview use 0-based position as placeholder string)
            _sorted_names = sorted(
                [name for (_row_idx, _prefix, _number, name) in transformed],
                key=lambda s: s.casefold(),
            )
            for _i, _name in enumerate(_sorted_names[:50]):
                _preview.append([str(_i), _name])

        return PipelineResult(
            success=True,
            output_path=None,
            log_path=None,
            error_log_path=None,
            rows_processed=len(transformed),
            transformations_applied=len(change_records),
            detection={
                "encoding": encoding_used,
                "header_row_index": header_row_index,
                "mec_col_index": col_mapping.mec_col_index,
                "name_col_index": col_mapping.name_col_index,
                "detection_method": col_mapping.detection_method,
            },
            failures=[],
            log_entries=builder.entries,
            preview_rows=_preview,
        )

    # ------------------------------------------------------------------
    # Step 22: validate output path
    # ------------------------------------------------------------------
    validate.validate_output_path(src.path, output_path, overwrite_allowed=overwrite_allowed)

    # ------------------------------------------------------------------
    # Steps 23-24: build output rows and write
    # ------------------------------------------------------------------
    if output_type == "caderno":
        output_rows: list[tuple[str, str]] = []
        for _row_idx, prefix, number, name in transformed:
            if chosen_case == "lower":
                mec_str = f"{prefix.lower()}{number}"
            else:
                mec_str = f"{prefix.upper()}{number}"
            output_rows.append((mec_str, name))
        output.write_caderno(
            output_path,
            output_rows,
            input_path=src.path,
            overwrite_allowed=overwrite_allowed,
        )
    else:
        designations = [name for (_row_idx, _prefix, _number, name) in transformed]
        output.write_elegiveis(
            output_path,
            designations,
            input_path=src.path,
            overwrite_allowed=overwrite_allowed,
        )

    # ------------------------------------------------------------------
    # Steps 25-27: finalize log
    # ------------------------------------------------------------------
    builder.add("SAIDA", f"Ficheiro gerado: {output_path} ({len(transformed)} linhas)")
    builder.add(
        "FIM",
        f"Processamento concluido com sucesso. {len(change_records)} alteracoes.",
    )
    log_path = elt_logging.write_log_file(builder, output_path)

    # ------------------------------------------------------------------
    # Step 28: return success result
    # ------------------------------------------------------------------
    return PipelineResult(
        success=True,
        output_path=output_path,
        log_path=log_path,
        error_log_path=None,
        rows_processed=len(transformed),
        transformations_applied=len(change_records),
        detection={
            "encoding": encoding_used,
            "header_row_index": header_row_index,
            "mec_col_index": col_mapping.mec_col_index,
            "name_col_index": col_mapping.name_col_index,
            "detection_method": col_mapping.detection_method,
        },
        failures=[],
        log_entries=builder.entries,
    )


# ---------------------------------------------------------------------------
# Internal: minimal ColumnMapping-like object for manual mapping mode
# ---------------------------------------------------------------------------


@dataclasses.dataclass
class _ManualColumnMapping:
    """Minimal stand-in for detection.ColumnMapping when manual columns are given.

    This avoids importing detection.ColumnMapping just to create a manual-mode
    object; the pipeline only uses these five attributes.
    """

    mec_col_index: int | None
    name_col_index: int | None
    mec_col_label: str | None
    name_col_label: str | None
    detection_method: Literal["synonym", "format_fallback", "manual"]
