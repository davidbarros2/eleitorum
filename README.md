**EleitorUM** is a Windows desktop utility that normalises electoral roll and eligibility list files. It accepts Excel and text formats (XLSX, XLS, ODS, CSV, TSV), validates and transforms the data according to strict rules, and produces a byte-exact CSV output with no manual fixing required.

---

# EleitorUM

> Utilitário Windows para normalizar cadernos eleitorais e listas de elegíveis.

[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue)](https://www.python.org/downloads/)
[![Licença: MIT](https://img.shields.io/badge/licen%C3%A7a-MIT-green)](LICENSE)
[![Plataforma: Windows](https://img.shields.io/badge/plataforma-Windows%2010%2F11-0078D4?logo=windows)](https://www.microsoft.com/windows)
[![Estado: v1.0.0](https://img.shields.io/badge/estado-v1.0.0-brightgreen)]()

O **EleitorUM** automatiza a preparação de cadernos eleitorais e listas de elegíveis — uma tarefa hoje feita manualmente no Excel e no Notepad. Aceita qualquer ficheiro Excel ou texto (XLSX, XLS, ODS, CSV, TSV), valida e normaliza os dados segundo regras precisas, e produz um CSV byte-exact acompanhado de um log detalhado de todas as alterações.

**Valor central:** um ficheiro de entrada arbitrário entra, o ficheiro correcto sai — sem correcções manuais.

---

## Funcionalidades

**Entrada**
- Formatos suportados: XLSX, XLSM, XLS, ODS, CSV, TSV
- Detecção automática de codificação (UTF-8, UTF-8 BOM, CP1252, ISO-8859-1, …)
- Detecção automática da linha de cabeçalho (tolerante a títulos e linhas em branco)
- Detecção automática das colunas mecanográfico e nome (correspondência flexível por sinónimos)

**Normalização**
- Número mecanográfico: prefixos válidos (A, PG, ID, F, D, B, Q, EX), sem zeros à esquerda, case por maioria (minúsculas em caso de empate)
- Nomes: espaços múltiplos e exóticos (incluindo ZWSP U+200B), vírgulas, anotações parentéticas, caracteres ilegíveis (U+FFFD), mojibake UTF-8-lido-como-Latin-1
- Floats do Excel (`14891.0` → `14891`)

**Validação**
- Prefixo inválido, número não-positivo, duplicados, colisões de namespace F/D/B
- Filosofia fail-fast: nenhum ficheiro de saída é escrito se existirem erros

**Saída**
- Caderno eleitoral: `numero_mecanografico;nome;` (categoria sempre vazia)
- Lista de elegíveis: `indice;designacao` (índice 0-based, ordem NFKD alfabética)
- Formato exacto: UTF-8 com BOM, ponto-e-vírgula, CRLF, sem quoting, newline final

**Logs**
- Sucesso: ficheiro `_LOG_` com cada alteração identificada por linha, campo e valor
- Falha: ficheiro `_ERRORS_` com cada erro por linha, campo, valor e mensagem em PT-PT

**Performance**
- 150.000 linhas em 3,5 s (orçamento 10 s), leitura em modo streaming

---

## Estado do Projecto

| Fase | Descrição | Estado |
|------|-----------|--------|
| 1 — Core Pipeline | Leitura, detecção, transformação, validação, output, logging — Qt-free | ✅ Concluída |
| 2 — Interface Gráfica | Wizard PySide6, pré-visualização, temas claro/escuro | ✅ Concluída |
| 3 — Testes de Integração | Cobertura ponta-a-ponta, fixtures sintéticos | ✅ Concluída |
| 4 — Build e Distribuição | PyInstaller `.exe`, CI/CD, v1.0.0 | ✅ Concluída |

---

## Instalação

Descarregue `EleitorUM-1.0.0-win64.zip` da [página de lançamentos](https://github.com/davidbarros2/eleitorum/releases/tag/v1.0.0), extraia o ZIP e execute `EleitorUM.exe`. Não é necessário instalar Python.

### Verificação de integridade (opcional)

```powershell
# Verificar SHA-256
(Get-FileHash EleitorUM-1.0.0-win64.zip -Algorithm SHA256).Hash.ToLower()
```
Compare com o conteúdo de `EleitorUM-1.0.0-win64.zip.sha256`.

### Aviso de segurança

O Windows pode apresentar um aviso SmartScreen na primeira execução (o executável não tem assinatura de código). Clique em "Mais informações" → "Executar assim mesmo" para prosseguir.

---

## Desenvolvimento

### Pré-requisitos

- Python 3.11 ([python.org](https://www.python.org/downloads/) ou `pyenv-win`)
- `pip` actualizado (`python -m pip install --upgrade pip`)

### Instalação

```bash
git clone https://github.com/davidbarros2/eleitorum.git
cd eleitorum
pip install -e ".[dev]"
```

### Lançar a aplicação

```bash
python -m eleitorum
```

### Executar os testes

```bash
# Suite completa
pytest

# Excluir o benchmark de 150k linhas
pytest -m "not performance"

# Com relatório de cobertura
pytest --cov --cov-report=term-missing
```

### Lint e type checking

```bash
ruff check .
ruff format .
mypy src/
```

---

## Estrutura do Projecto

```
src/eleitorum/
├── core/
│   ├── pipeline.py       # ponto de entrada público (sem Qt)
│   ├── readers.py        # leitura XLSX/XLS/ODS/CSV/TSV
│   ├── detection.py      # detecção de codificação, cabeçalho e colunas
│   ├── transform.py      # normalização de mecanográfico e nome
│   ├── validate.py       # validação de linhas e caminho de saída
│   ├── output.py         # escrita CSV byte-exact
│   ├── logging.py        # construção e escrita de logs
│   └── errors.py         # hierarquia de excepções em PT-PT
├── ui/
│   ├── app.py            # QApplication factory (Fusion + tema + fonte)
│   ├── main_window.py    # QMainWindow, menu bar, QSettings
│   ├── wizard.py         # WizardController, navegação, dry-run/write
│   ├── dialogs.py        # WelcomeDialog + AboutDialog
│   ├── session.py        # SessionModel @dataclass (sem Qt)
│   ├── worker.py         # PipelineWorker QThread
│   ├── theme.py          # QSS claro/escuro, detecção do sistema
│   ├── strings.py        # todas as strings PT-PT
│   ├── widgets/          # NavBar, OptionCard, DropZone
│   └── steps/            # StepType, StepUpload, StepSheet, StepColumns,
│                         # StepProcessing, StepPreview, StepDone
├── resources/
│   ├── icon.svg
│   └── fonts/Inter/      # Inter (download manual — ver README)
├── config.py             # constantes globais (APP_NAME, …)
└── __main__.py           # python -m eleitorum

tests/
├── unit/                 # testes unitários por módulo (core + ui)
├── integration/          # pipeline ponta-a-ponta + benchmark
└── fixtures/             # geradores de dados sintéticos
```

---

## Stack Tecnológico

| Componente | Biblioteca | Versão | Licença |
|------------|------------|--------|---------|
| Interface gráfica | PySide6 | 6.11.1 | LGPL |
| Leitura XLSX | openpyxl | 3.1.5 | MIT |
| Leitura XLS | xlrd | 2.0.2 | BSD |
| Leitura ODS | odfpy | 1.4.1 | GPL/LGPL |
| Normalização | pandas | 3.0.x | BSD |
| Detecção de codificação | charset-normalizer | 3.4.7 | MIT |
| Empacotamento | PyInstaller | 6.20.0 | GPL + bootloader exception |
| Testes | pytest + pytest-qt | 9.0.3 / 4.5.0 | MIT |
| Lint e formatação | ruff | 0.15.x | MIT |
| Type checking | mypy | 2.1.0 | MIT |

---

## Licença

Distribuído sob a licença [MIT](LICENSE).
