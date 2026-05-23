# Phase 3: Integration, End-to-End Testing + Fixtures - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-05-23
**Phase:** 3-Integration, End-to-End Testing + Fixtures
**Areas discussed:** Worker QThread end-to-end, Cobertura de código (TST-09), Elegíveis byte-exact assertions, WizardController full flow

---

## Worker QThread End-to-End

| Opção | Descrição | Seleccionada |
|-------|-----------|--------------|
| Sim, 2 testes (happy-path + rejection) | Worker com ficheiro real, qtbot.waitSignal, sem mocking do pipeline | ✓ |
| Sim, e adicionar cancelável também | Terceiro teste: worker cancelado a meio com ficheiro real | |
| Não, unit tests do worker são suficientes | Os sinais e cancel já cobertos pelos testes existentes | |

**Escolha do utilizador:** 2 testes (happy-path + rejection)
**Notas:** O teste de cancel com ficheiro real foi explicitamente decidido não fazer — o teste unit existente `test_worker_run_emits_cancelled_when_cancelled` já cobre esse caminho com 200 rows sintéticas.

---

## Cobertura de Código (TST-09)

| Opção | Descrição | Seleccionada |
|-------|-----------|--------------|
| Medir primeiro e preencher só se necessário | Eficiente: não adicionar testes redundantes | ✓ |
| Medir e atingir 95%+ se possível | Ambicioso: maximizar cobertura acima do mínimo | |
| Pular — confiar no relatório da Phase 1 | Assumir 91.26% mantido | |

**Escolha do utilizador:** Measure-first
**Notas:** Phase 1 reportou 91.26% no momento da implementação. Medir com `pytest --cov=src/eleitorum/core --cov-report=term-missing` e só adicionar testes se algum módulo estiver abaixo de 90%.

---

## Elegíveis Byte-Exact Assertions

| Opção | Descrição | Seleccionada |
|-------|-----------|--------------|
| Expandir o teste existente | Editar test_happy_path_elegiveis_csv: índice 0-based, ordenação NFKD, formato linhas | ✓ |
| Expandir + adicionar teste de diacríticos | Adicionar teste dedicado com ã, é, ç para verificar ordenação NFKD | |

**Escolha do utilizador:** Expandir o teste existente
**Notas:** Gap identificado: o teste actual verifica BOM, CRLF e cabeçalho, mas não verifica o conteúdo das linhas de dados (índice, ordenação, formato).

---

## WizardController Full Flow

| Opção | Descrição | Seleccionada |
|-------|-----------|--------------|
| Não adicionar (recomendado) | Três caminhos já testados isoladamente; full-flow frágil e lento | ✓ |
| Adicionar um teste de fluxo completo | Exercitar o caminho completo de UI até ficheiro de saída | |

**Escolha do utilizador:** Não adicionar
**Notas:** Consenso claro: pipeline testada em test_full_pipeline.py, worker com pipeline real no novo test_worker_integration.py, wizard navigation em test_wizard.py. Um teste end-to-end adicional seria frágil sem valor proporcional.

---

## Claude's Discretion

- Timeout dos qtbot.waitSignal: 10000ms (alinhado com budget PERF-01)
- Fixture para happy-path worker test: `generators.make_simple_caderno` (simples, sem edge cases)
- Localização: `tests/integration/test_worker_integration.py` (não tests/unit/ui/)

## Deferred Ideas

- Teste de cancel com ficheiro real — decidido não fazer (unit test existente já cobre)
- WizardController full-flow test — decidido não fazer (frágil, lento)
