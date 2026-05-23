# Phase 2: UI Scaffold + Wizard Steps - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-05-23
**Phase:** 02-UI Scaffold + Wizard Steps
**Areas discussed:** Comportamento do Cancelar, Ecrã de boas-vindas, "Ver detalhes" no pré-visualização, Ícone da aplicação na Fase 2, SessionModel, Tema claro/escuro, Processamento em background

---

## Comportamento do Cancelar (WIZ-11)

| Opção | Descrição | Seleccionada |
|-------|-----------|--------------|
| Parar e voltar ao passo 3 | Thread para via threading.Event; assistente volta ao passo de mapeamento de colunas | |
| Deixar terminar e descartar | Thread termina em background, resultado ignorado, volta ao passo 1 | |
| Pedir confirmação primeiro + voltar ao passo 3 | Diálogo de confirmação; se confirmar, thread para e volta ao passo 3 | ✓ |

**User's choice:** Opção 3 — confirmação antes de cancelar, depois segue o comportamento da opção 1 (parar thread + voltar ao passo 3).
**Notes:** O utilizador combinou opções 1 e 3 explicitamente — confirmação primeiro para evitar cancelamentos acidentais, mas retorno ao passo 3 (não passo 1) para não obrigar a recarregar o ficheiro.

---

## Ecrã de Boas-Vindas (APP-16)

| Opção | Descrição | Seleccionada |
|-------|-----------|--------------|
| QDialog modal antes do assistente | Aparece sobre a janela principal; "Começar" fecha; não afecta QStackedWidget | ✓ |
| Passo 0 no QStackedWidget | Primeiro widget no stack antes do passo 1; "Começar" avança para passo 1 | |
| Janela separada | Janela separada antes da janela principal | |

**User's choice:** QDialog modal antes do assistente.
**Notes:** Quando reaberto via menu Ajuda → o mesmo QDialog é usado (comportamento idêntico ao primeiro arranque).

---

## "Ver Detalhes" no Pré-visualização (WIZ-05)

| Opção | Descrição | Seleccionada |
|-------|-----------|--------------|
| Secção recolhível inline | QTextEdit abaixo do painel de sumário; toggle com o link | ✓ |
| Diálogo separado | QDialog com registo completo; utilizador fecha e volta ao passo 4 | |
| Painel lateral deslizante | Painel da direita com o registo | |

**User's choice:** Secção recolhível inline.
**Notes:** Altura ~150px, scroll completo sem truncagem, toggle com o mesmo link.

---

## Ícone da Aplicação na Fase 2 (BRAND-02)

| Opção | Descrição | Seleccionada |
|-------|-----------|--------------|
| Criar SVG agora, gerar ICO na Fase 4 | icon.svg criado na Fase 2; QIcon carrega SVG; ICO/PNG na Fase 4 | ✓ |
| Placeholder provisório | Sem QIcon definido na Fase 2; ícone criado inteiramente na Fase 4 | |

**User's choice:** Criar o SVG agora.
**Notes:** A janela fica com marca visual correcta desde a Fase 2; sem dependência de bloqueio na Fase 4.

---

## SessionModel (Arquitectura)

| Opção | Descrição | Seleccionada |
|-------|-----------|--------------|
| Python dataclass partilhado | @dataclass com type hints; passado por construtor a cada step | ✓ |
| Tu decides (agente) | Delegação ao agente | |

**User's choice:** Python dataclass partilhado.
**Notes:** Sem dependências Qt nos dados; testável sem QApplication.

---

## Tema Claro/Escuro (APP-07 a APP-12)

| Opção | Descrição | Seleccionada |
|-------|-----------|--------------|
| QSS global (stylesheet) | theme.py gera QSS; QApplication.setStyleSheet(); troca instantânea | ✓ |
| QPalette nativa Qt | QPalette sem suporte directo ao accent #a21a1c | |
| Tu decides | Delegação ao agente | |

**User's choice:** QSS global.
**Notes (pergunta de seguimento):** Se a deteção do tema do sistema falhar → fallback para tema claro.

---

## Processamento em Background (WIZ-11)

| Opção | Descrição | Seleccionada |
|-------|-----------|--------------|
| Ecrã de progresso entre passos | Widget intermédio no QStackedWidget; auto-avança para passo 4 no sucesso | ✓ |
| Passo 4 com indicador de carregamento | Passo 4 aparece imediatamente com tabela vazia e barra de progresso | |

**User's choice:** Ecrã de progresso entre passos.
**Notes:** Área extra identificada pelo agente como crítica para a navegação do QStackedWidget. Widget dedicado (passo 3.5) com barra indeterminada → determinada.

---

## Claude's Discretion

- Arquitectura do QThread: `PipelineWorker(QThread)` com sinais `progress(int, int)`, `finished(result)`, `error(str)`
- Layout da NavBar: footer com QHBoxLayout; texto do Próximo sobreposto no passo 4
- Indicador de passo: QLabel "Passo N de 5/6"; contador dinâmico conforme presença do passo 2.5
- Organização dos QSettings: `EleitorUM/EleitorUM` (empresa/app)
- Carregamento da fonte Inter via QFontDatabase
- Verificação de contraste WCAG AA: manual durante implementação

## Deferred Ideas

Nenhuma — a discussão manteve-se dentro do âmbito da fase.
