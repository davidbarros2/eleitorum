"""All PT-PT user-facing string constants for the EleitorUM UI (APP-20).

No string literals may appear in widget code. All user-facing copy is defined
here. Format strings use .format(key=value) syntax for parameterization.

Mirrors Phase 1's errors.py pattern: centralized, typed, PT-PT only.
All copy sourced from 02-UI-SPEC.md Copywriting Contract, Error States, and
Empty States sections. The UMINHO_DISCLAIMER is verbatim from Eleitorum.md §3.5.
"""
from __future__ import annotations


# ---------------------------------------------------------------------------
# Window / app title
# ---------------------------------------------------------------------------

# Note: widget code reads APP_NAME from eleitorum.config, not this constant.
# This is retained only as a reference anchor.
WINDOW_TITLE: str = "EleitorUM"


# ---------------------------------------------------------------------------
# Step titles
# ---------------------------------------------------------------------------

STEP_1_TITLE: str = "Tipo de ficheiro de saída"
STEP_2_TITLE: str = "Carregar ficheiro"
STEP_25_TITLE: str = "Escolher folha"
STEP_3_TITLE: str = "Mapeamento de colunas"
STEP_4_TITLE: str = "Pré-visualização"
STEP_DONE_SUCCESS_TITLE: str = "Concluído"
STEP_DONE_ERROR_TITLE: str = "Erro no processamento"
STEP_PROCESSING_TITLE: str = "A processar…"


# ---------------------------------------------------------------------------
# Step indicator
# ---------------------------------------------------------------------------

# Usage: STEP_INDICATOR.format(n=current_step, total=total_steps)
STEP_INDICATOR: str = "Passo {n} de {total}"


# ---------------------------------------------------------------------------
# NavBar buttons
# ---------------------------------------------------------------------------

BTN_ANTERIOR: str = "Anterior"
BTN_PROXIMO: str = "Próximo"
BTN_CANCELAR: str = "Cancelar"
BTN_GRAVAR: str = "Escolher destino e gravar"  # overrides BTN_PROXIMO on step 4
BTN_COMECAR: str = "Começar"  # welcome dialog primary action
BTN_SAIR: str = "Sair"  # step 6 success secondary action
BTN_PROCESSAR_OUTRO: str = "Processar outro ficheiro"  # step 6 primary action
BTN_ABRIR_PASTA: str = "Abrir pasta"  # step 6 open output folder
BTN_ALTERAR: str = "Alterar"  # step 3 column mapping inline link
BTN_VER_DETALHES_ABRIR: str = "Ver detalhes"  # step 4 expand log
BTN_VER_DETALHES_FECHAR: str = "Fechar detalhes"  # step 4 collapse log
BTN_ESCOLHER_FICHEIRO: str = "ou escolher ficheiro…"  # step 2 file picker button
BTN_CONFIRM_CANCEL: str = "Sim, cancelar"  # D-01 confirmation dialog
BTN_CONTINUE: str = "Não, continuar"  # D-01 decline cancel


# ---------------------------------------------------------------------------
# Processing screen
# ---------------------------------------------------------------------------

PROCESSING_LOADING: str = "A carregar ficheiro…"
# Usage: PROCESSING_PROGRESS.format(current=current_row, total=total_rows)
PROCESSING_PROGRESS: str = "A validar linha {current} de {total}…"


# ---------------------------------------------------------------------------
# Confirmation dialogs
# ---------------------------------------------------------------------------

CONFIRM_CANCEL: str = (
    "Tem a certeza que quer cancelar? O processamento será interrompido."
)


# ---------------------------------------------------------------------------
# Empty states / drop zone
# ---------------------------------------------------------------------------

DROP_ZONE_PLACEHOLDER: str = "Arraste o ficheiro para aqui"


# ---------------------------------------------------------------------------
# Error messages
# ---------------------------------------------------------------------------

# Usage: ERR_UNSUPPORTED_EXT.format(ext=".docx")
ERR_UNSUPPORTED_EXT: str = (
    "O formato '{ext}' não é suportado. Formatos aceites: XLSX, XLSM, XLS, ODS, CSV, TSV."
)
ERR_FILE_OPEN: str = (
    "Não foi possível ler o ficheiro. Feche-o noutro programa e tente novamente."
)
ERR_OUTPUT_SAME_AS_INPUT: str = (
    "O destino não pode ser o mesmo ficheiro que o original. Escolha outro local."
)
ERR_OUTPUT_OPEN: str = (
    "Não foi possível gravar o ficheiro. Feche-o no Excel e tente novamente."
)
ERR_OUTPUT_EXISTS_PROMPT: str = "Já existe um ficheiro com esse nome. Substituir?"
ERR_NO_DETECTION_HEADING: str = (
    "Não foi possível detetar as colunas automaticamente."
)
ERR_NO_DETECTION_BODY: str = "Por favor, escolha quais usar:"


# ---------------------------------------------------------------------------
# Option card copy (step 1)
# ---------------------------------------------------------------------------

OPTION_CADERNO_HEADING: str = "Caderno Eleitoral"
OPTION_CADERNO_DESC: str = "Lista de votantes elegíveis a participar numa eleição"
OPTION_ELEGIVEIS_HEADING: str = "Lista de Elegíveis"
OPTION_ELEGIVEIS_DESC: str = (
    "Lista de candidatos ou opções disponíveis numa eleição"
)


# ---------------------------------------------------------------------------
# File dialog labels
# ---------------------------------------------------------------------------

OPEN_DIALOG_TITLE: str = "Escolher ficheiro de entrada"
OPEN_DIALOG_FILTER: str = (
    "Ficheiros suportados (*.xlsx *.xlsm *.xls *.ods *.csv *.tsv);;"
    "Todos os ficheiros (*.*)"
)
SAVE_DIALOG_TITLE: str = "Gravar ficheiro de saída"
SAVE_DIALOG_FILTER: str = "Ficheiro CSV (*.csv);;Todos os ficheiros (*.*)"


# ---------------------------------------------------------------------------
# Sheet picker (step 2.5)
# ---------------------------------------------------------------------------

SHEET_PICKER_EMPTY_SUFFIX: str = " — folha vazia"
# Usage: SHEET_PICKER_ROWS_TEMPLATE.format(rows=row_count)
SHEET_PICKER_ROWS_TEMPLATE: str = "({rows} linhas)"


# ---------------------------------------------------------------------------
# Menu bar (APP-14)
# ---------------------------------------------------------------------------

MENU_FILE: str = "Ficheiro"
MENU_VIEW: str = "Ver"
MENU_HELP: str = "Ajuda"
MENU_REINICIAR: str = "Reiniciar"
MENU_SAIR: str = "Sair"
MENU_TEMA_CLARO: str = "Tema Claro"
MENU_TEMA_ESCURO: str = "Tema Escuro"
MENU_BOAS_VINDAS: str = "Boas-vindas…"
MENU_SOBRE: str = "Sobre…"


# ---------------------------------------------------------------------------
# About dialog (APP-15)
# ---------------------------------------------------------------------------

ABOUT_DESCRIPTION: str = (
    "Utilitário para normalização de ficheiros eleitorais da Universidade do Minho."
)
ABOUT_LICENSE: str = "Distribuído sob a licença MIT."
ABOUT_REPO_LINK_LABEL: str = "Repositório no GitHub"

# Verbatim from Eleitorum.md §3.5 — do not paraphrase.
UMINHO_DISCLAIMER: str = (
    "O EleitorUM é uma ferramenta independente de código aberto. Não é oficialmente "
    "afiliada nem endossada pela Universidade do Minho. As cores e referências "
    "gráficas inspiram-se nas normas da UMinho mas o projeto não tem qualquer "
    "ligação institucional com a universidade."
)


# ---------------------------------------------------------------------------
# Welcome dialog (APP-16)
# ---------------------------------------------------------------------------

WELCOME_HEADING: str = "Bem-vindo ao EleitorUM"
WELCOME_BODY: str = (
    "O EleitorUM guia-o passo a passo na transformação dos seus ficheiros "
    "eleitorais para o formato exigido pela plataforma da Universidade do Minho.\n\n"
    "1. Selecione o tipo de ficheiro de saída\n"
    "2. Carregue o ficheiro de entrada\n"
    "3. Mapeie as colunas\n"
    "4. Reveja a pré-visualização e grave o resultado"
)


# ---------------------------------------------------------------------------
# Step done — success and error screens (step 6)
# ---------------------------------------------------------------------------

DONE_PRONTO: str = "Pronto!"
# Usage: DONE_SUCCESS_SUMMARY.format(rows=rows_processed, changes=transformations_applied)
DONE_SUCCESS_SUMMARY: str = "{rows} linhas processadas, {changes} alterações aplicadas."
DONE_ERROR_HEADING: str = "Foram encontrados erros que impedem a criação do ficheiro."
DONE_ERROR_BODY: str = (
    "Consulte o ficheiro de erros para obter a lista completa dos problemas encontrados."
)


# ---------------------------------------------------------------------------
# Column mapping (step 3)
# ---------------------------------------------------------------------------

COL_MAPPING_HIGH: str = "A coluna {name} será usada como {role}."
COL_MAPPING_LOW: str = "A coluna {name} foi selecionada. Pode alterar."


# ---------------------------------------------------------------------------
# Preview (step 4)
# ---------------------------------------------------------------------------

PREVIEW_TOTAL_ROWS: str = "Total de linhas: {n}"
PREVIEW_TRANSFORMATIONS: str = "Alterações aplicadas: {m}"
PREVIEW_WARNINGS: str = "Atenção: {k} linhas com avisos"
