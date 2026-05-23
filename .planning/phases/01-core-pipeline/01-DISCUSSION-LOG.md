# Phase 1: Core Pipeline - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-05-23
**Phase:** 1-Core Pipeline
**Areas discussed:** Nomes das colunas de entrada, Lista de prefixos, Ordenação dos elegíveis, Validações em aberto (BOM + F/D/B)

---

## Nomes das colunas de entrada

| Option | Description | Selected |
|--------|-------------|----------|
| "Mecanográfico" (nome exacto) | Ferramenta procura primeiro por nome exacto | |
| "N.º Mecanográfico" ou variantes com número | Ex: Nº Mec., N.Mec, Número Mecanográfico | |
| Nome diferente (outro) | A coluna tem nome variado nos ficheiros reais | ✓ |

**User's choice:** Não há nome standard — há 10–50+ variantes diferentes nos ficheiros da UMinho. O produto owner sugeriu deteção por formato do número (prefixo + número, sem espaços) como alternativa mais robusta.

**Notes:** Esta foi a descoberta mais importante da discussão. O product owner revelou que a deteção por nome de coluna seria insuficiente. Adicionalmente, o product owner indicou que o documento `.planning/eleitorum.md` existia e continha as respostas a estas questões — razão pela qual a pergunta sobre nomes de colunas pareceu redundante do seu ponto de vista.

---

## Documento de especificação canónica

| Option | Description | Selected |
|--------|-------------|----------|
| Sim, tenho o ficheiro — posso partilhá-lo | Documento completo existe | ✓ |
| Está no .planning/ | Guardado na pasta de planeamento | |
| Não, o REQUIREMENTS.md é tudo o que existe | Sem documento separado | |

**User's choice:** "Acabei de o transferir para a pasta .planning/. O ficheiro chama-se eleitorum.md"

**Notes:** O ficheiro `.planning/eleitorum.md` é a especificação canónica completa com 18 secções. Responde a todas as questões em aberto do STATE.md excepto o BOM. Este ficheiro deve ser a primeira referência para todos os agentes de planeamento e execução.

---

## Lista de prefixos mecanográficos

(Respondida pelo documento de especificação — sem questão direta ao utilizador)

**Spec confirms:** A, PG, ID, F, D, B, Q, EX — lista completa e exaustiva (Section 6.1). Qualquer outro prefixo → erro imediato.

---

## Ordenação dos elegíveis

(Decisão técnica tomada pelo assistente — sem questão direta ao utilizador)

**Decision:** Sort key Unicode-normalizado, sem diacríticos, sem distinção maiúsculas/minúsculas: `unicodedata.normalize('NFKD', s.casefold()).encode('ascii', 'ignore').decode('ascii')`. Trata ã=a, é=e, ç=c — consistente com convenção alfabética portuguesa.

---

## Validações em aberto — BOM

| Option | Description | Selected |
|--------|-------------|----------|
| Sim, testei — plataforma aceita com BOM | Decisão definitiva | |
| Sim, testei — plataforma rejeita com BOM | Implementar sem BOM | |
| Ainda não testei | Implementar com BOM, testar mais tarde | ✓ |

**User's choice:** Ainda não testado.

**Notes:** Implementação prossegue com BOM (utf-8-sig) conforme especificação Section 5.1. Mantido como constante `USE_BOM = True` em output.py para alteração trivial quando o teste for realizado.

---

## Claude's Discretion

- **Algoritmo de deteção de mojibake:** scan por padrão `Ã` + byte 0x80–0xBF; tentativa `encode('latin-1').decode('utf-8')`; aceitar apenas se resultado é limpo.
- **Hierarquia de exceções:** estrutura interna (nomes de classes, etc.) delegada ao assistente, desde que as mensagens PT-PT correspondam aos exemplos da spec.
- **Threshold de confiança de codificação:** 0.85 (REQUIREMENTS.md) em vez de 0.80 (spec Section 4.2) — valor mais conservador.
- **Estrutura de testes:** organização interna dos testes unitários, nomes de fixtures, conftest.py.

## Deferred Ideas

Nenhuma — a discussão manteve-se dentro do âmbito da Fase 1.
