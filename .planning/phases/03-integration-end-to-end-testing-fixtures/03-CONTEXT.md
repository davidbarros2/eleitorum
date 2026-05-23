# Phase 3: Integration, End-to-End Testing + Fixtures - Context

**Gathered:** 2026-05-23
**Status:** Ready for planning

<domain>
## Phase Boundary

Fechar a lacuna entre a pipeline core e o worker Qt. A maior parte dos testes de Phase 1 e Phase 2 já existe (381 testes passando). Phase 3 adiciona o que genuinamente falta: testes de integração QThread com ficheiros reais, expansão das asserções byte-exact para elegíveis, medição e garantia de cobertura ≥90%, e formalização dos requisitos TST-01–09 como completos.

**In scope:** TST-01, TST-02, TST-03, TST-04, TST-05, TST-06, TST-07, TST-08, TST-09

**Out of scope:** novos testes de wizard flow completo (frágil, desnecessário dado que os três caminhos já são testados isoladamente); qualquer alteração ao código de produção

**Estado inicial conhecido:**
- 381 testes passando, 1 skipped
- All 15 fixture generators em `tests/fixtures/generators.py` ✓
- 18 integration tests cobrindo todos os 5 user journeys + edge cases ✓
- Asserções byte-exact caderno: BOM, CRLF, sem aspas ✓ (elegíveis: incompleto)
- Worker unit tests (sinais, cancel) ✓ — worker com ficheiro real: ❌ (a fazer)
- pytest-qt smoke tests para todos os 7 wizard steps ✓

</domain>

<decisions>
## Implementation Decisions

### Worker QThread Integration Tests
- **D-01:** Criar `tests/integration/test_worker_integration.py` com exactamente 2 novos testes:
  1. Happy-path: `PipelineWorker` com ficheiro sintético caderno real → `qtbot.waitSignal(worker.finished, timeout=10000)`, verificar `result.success=True` e ficheiro de saída criado no disco.
  2. Rejection: `PipelineWorker` com ficheiro que tem duplicados (via `generators.make_duplicate_within_prefix`) → `qtbot.waitSignal(worker.error, timeout=10000)`, verificar que nenhum ficheiro de saída é escrito.
  - Rationale: fecha o gap "wire pipeline to UI" do objectivo da Fase 3; o worker unit test existente testa sinais e cancel mas não a pipeline real end-to-end.
  - **NÃO adicionar** um terceiro teste de cancel com ficheiro real — o teste unit `test_worker_run_emits_cancelled_when_cancelled` já cobre esse caminho.

### Elegíveis Byte-Exact Assertions
- **D-02:** Expandir `test_happy_path_elegiveis_csv` (em `tests/integration/test_full_pipeline.py`) para verificar:
  - (a) Primeira linha de dados começa com `0;` (índice 0-based)
  - (b) Designações estão em ordem alfabética NFKD (verificar pelo menos as primeiras 3 linhas)
  - (c) Formato das linhas: `{int};{designação}` sem campo extra vazio (elegíveis não têm `;` final, ao contrário do caderno)
  - Rationale: o teste actual verifica BOM, CRLF, cabeçalho — mas não o conteúdo correcto das linhas de dados.

### Cobertura de Código (TST-09)
- **D-03:** Estratégia measure-first:
  1. Medir cobertura actual: `pytest --cov=src/eleitorum/core --cov-report=term-missing`
  2. Se todos os módulos core (transform.py, validate.py, detection.py, output.py, readers.py, logging.py, pipeline.py) estiverem ≥90% → marcar TST-09 como completo sem adicionar testes.
  3. Se algum módulo estiver abaixo de 90% → adicionar testes unitários específicos para as linhas descobertas.
  4. TST-09 exige "transformation and validation logic" — o limiar aplica-se especialmente a `transform.py` e `validate.py`.
  - Rationale: eficiente — Phase 1 já reportou 91.26%; não adicionar testes redundantes se o limiar se mantém.

### WizardController Full Flow
- **D-04:** NÃO adicionar testes de fluxo completo wizard→worker→pipeline→UI.
  - Os três caminhos já são testados separadamente:
    - Pipeline: `tests/integration/test_full_pipeline.py`
    - Worker + pipeline: `tests/integration/test_worker_integration.py` (D-01 acima)
    - Wizard navigation: `tests/unit/ui/test_wizard.py`
  - Um teste de fluxo completo seria frágil (timing de QThread), lento, e sem valor proporcional ao custo de manutenção.

### Claude's Discretion
- Timeout dos `qtbot.waitSignal` nos testes de integração worker: usar 10000ms (10s) — alinhado com o budget de PERF-01 para 150k rows; ficheiros sintéticos pequenos terminam muito antes.
- Localização do novo ficheiro de testes worker: `tests/integration/test_worker_integration.py` (não `tests/unit/ui/`) porque exercita a pipeline real sem mocking.
- Fixture a usar para o happy-path worker test: `generators.make_simple_caderno` — clean, simples, sem edge cases que possam complicar o timeout.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Phase Scope and Requirements
- `.planning/ROADMAP.md` §"Phase 3: Integration, End-to-End Testing + Fixtures" — 4 success criteria que definem "done" para esta fase
- `.planning/REQUIREMENTS.md` — requirement IDs TST-01–09 com descrições exactas dos critérios de aceitação

### Existing Test Infrastructure (state to preserve)
- `tests/integration/test_full_pipeline.py` — 18 integration tests existentes; editar `test_happy_path_elegiveis_csv` para D-02; NÃO remover testes existentes
- `tests/fixtures/generators.py` — todos os 15 generators sintéticos (importável sem QApplication); NÃO modificar generators existentes
- `tests/unit/ui/test_worker.py` — 5 worker unit tests existentes; NÃO duplicar estes testes

### Worker API (integration contract)
- `.planning/phases/02-ui-scaffold-wizard-steps/02-CONTEXT.md` §D-07 — fluxo do processing widget e sinais do worker
- `src/eleitorum/ui/worker.py` — `PipelineWorker(source, output_type, output_path)`, sinais: `progress(int,int)`, `finished(PipelineResult)`, `error(str)`, `cancelled()`
- `src/eleitorum/core/pipeline.py` — `run_pipeline(source, output_type, output_path, progress_cb=None)` — assinatura fixa, não modificar

### Coverage Measurement
- `pyproject.toml` — configuração do pytest-cov e pytest; confirmar que `[tool.pytest.ini_options]` tem `qt_api = "pyside6"`

### Primary Specification
- `.planning/Eleitorum.md` — Sections 10 (user journeys), 14 (testing strategy), 14.3 (fixture function list)

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `tests/fixtures/generators.py` — todos os 15 generators; `make_simple_caderno`, `make_duplicate_within_prefix` são os mais relevantes para D-01
- `tests/integration/test_full_pipeline.py` — padrão estabelecido: `generators.make_*()` → `run_pipeline()` → `assert raw bytes`; D-02 segue este padrão
- `tests/unit/ui/conftest.py` — `qtbot` fixture disponível; confirmar que os tests de integração worker também acedem a `qtbot`

### Established Patterns
- Dados sintéticos: nomes com "Teste", "Exemplo", ou "Sintetica" em todos os fixtures (privacidade invariante)
- `qtbot.waitSignal(signal, timeout=N)` — padrão para testes QThread em pytest-qt
- `workers` do tipo `PipelineWorker` devem usar `worker.start()` (não `.run()`) para lançar o QThread

### Integration Points
- `tests/integration/` — localização correcta para `test_worker_integration.py`; os testes de integração não têm dependência de QApplication explícita mas precisam de `qtbot` fixture
- `test_happy_path_elegiveis_csv` — expandir inline (não criar novo teste) para D-02

</code_context>

<specifics>
## Specific Ideas

- Para D-02 (elegíveis assertions): o teste já usa `content.split("\r\n")` para extrair linhas — continuar com este padrão em vez de importar csv. As linhas de dados têm formato `{int};{designação}`, verificar com `int(lines[1].split(";")[0]) == 0`.

- Para D-01 (worker integration): o `PipelineWorker` recebe `output_path=None` no dry-run e um path real no write-run. Para o happy-path integration test, passar `output_path=tmp_path / "out.csv"` (write-run directo, sem dry-run).

</specifics>

<deferred>
## Deferred Ideas

- Teste de cancel com ficheiro real (worker + QThread + ficheiro sintético >100 rows, cancel antes de start) — decidido NÃO fazer em Phase 3: o teste unit existente `test_worker_run_emits_cancelled_when_cancelled` já cobre este caminho com ficheiro sintético de 200 rows.

- WizardController full-flow test — decidido NÃO fazer: frágil, lento, valor proporcional insuficiente.

</deferred>

---

*Phase: 3-Integration, End-to-End Testing + Fixtures*
*Context gathered: 2026-05-23*
