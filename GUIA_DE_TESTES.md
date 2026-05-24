# Guia de Testes — EleitorUM v1.0.0

Este guia descreve como instalar e testar o EleitorUM do princípio ao fim. Não são necessários conhecimentos técnicos de informática além dos normais para seguir este guia.

---

## Índice

1. [Requisitos](#1-requisitos)
2. [Instalação](#2-instalação)
3. [Criar os ficheiros de teste](#3-criar-os-ficheiros-de-teste)
4. [Testes de interface (A–H)](#4-testes-de-interface-ah)
5. [Testes funcionais (I–L)](#5-testes-funcionais-il)
6. [Teste de linha de comandos (M)](#6-teste-de-linha-de-comandos-m)
7. [Verificação do lançamento no GitHub (N)](#7-verificação-do-lançamento-no-github-n)
8. [Folha de resultados](#8-folha-de-resultados)

---

## 1. Requisitos

- Computador com **Windows 10** ou **Windows 11**
- Ligação à internet (apenas para o descarregamento inicial)
- Uma pasta no Ambiente de Trabalho para guardar os ficheiros de teste

---

## 2. Instalação

### 2.1 Descarregar

1. Abra o browser (Chrome, Edge, Firefox, etc.) e aceda a:  
   **https://github.com/davidbarros2/eleitorum/releases/tag/v1.0.0**

2. Na secção **"Assets"**, clique em **`EleitorUM-1.0.0-win64.zip`** para iniciar o descarregamento.

3. Quando terminar, o ficheiro ZIP encontra-se na pasta `Transferências` (ou no local que o browser usa por predefinição).

### 2.2 Extrair o ficheiro ZIP

1. Localize o ficheiro `EleitorUM-1.0.0-win64.zip`.
2. Clique com o botão **direito** sobre ele.
3. Escolha **"Extrair tudo…"**
4. Na janela que aparece, escolha o **Ambiente de Trabalho** como destino e clique em **"Extrair"**.
5. Será criada uma pasta `EleitorUM-1.0.0-win64` no Ambiente de Trabalho. Dentro encontra a pasta `EleitorUM` com o executável.

### 2.3 Executar pela primeira vez

1. Abra a pasta `EleitorUM` e faça **duplo clique** em **`EleitorUM.exe`**.

2. **Aviso SmartScreen (Windows):** o Windows pode apresentar um ecrã de aviso azul com o título "O Windows protegeu o seu PC". Isto acontece porque o executável não tem assinatura de código comercial — é normal.
   - Clique em **"Mais informações"** (texto a azul no meio do ecrã)
   - Clique em **"Executar assim mesmo"** (botão que aparece na parte inferior)
   - Este aviso só surge na **primeira execução**

3. A aplicação deve abrir-se. Continue para a [Secção 3](#3-criar-os-ficheiros-de-teste).

---

## 3. Criar os ficheiros de teste

Antes dos testes funcionais, é necessário preparar quatro ficheiros de teste. Siga as instruções abaixo.

### Ficheiro 1 — `caderno_valido.csv` (caderno eleitoral com transformações)

1. Prima `Win + R`, escreva `notepad` e prima **Enter**.
2. Copie e cole **exactamente** o seguinte conteúdo:

```
Numero Mecanografico;Nome
f1;João Silva  (docente)
f2;Maria Santos
f3;Pedro  Costa
f4;Ana Ferreira
pg101;Rui Oliveira (investigador)
```

3. Clique em **Ficheiro → Guardar como…**
4. Na janela de guardar:
   - Navegue até ao **Ambiente de Trabalho**
   - Em **"Tipo"**, escolha **"Todos os Ficheiros (\*.\*)"** (importante — evita guardar como `.txt`)
   - No campo **"Nome do ficheiro"** escreva: `caderno_valido.csv`
   - Clique em **Guardar**

### Ficheiro 2 — `elegiveis_validos.csv` (lista de elegíveis)

1. Abra um novo Bloco de Notas (Ficheiro → Novo).
2. Cole o seguinte conteúdo:

```
Nome
João Silva
Maria Santos
Pedro Costa
Ana Ferreira
Rui Oliveira
```

3. Guarde como `elegiveis_validos.csv` no Ambiente de Trabalho (mesmo processo descrito acima — tipo "Todos os Ficheiros").

### Ficheiro 3 — `caderno_erros.csv` (caderno com erros propositados)

1. Abra um novo Bloco de Notas.
2. Cole o seguinte conteúdo:

```
Numero Mecanografico;Nome
f1;João Silva
ZZZ1;Maria Santos
f2;Pedro Costa
f1;Ana Ferreira
```

> Este ficheiro contém dois erros propositados: prefixo inválido `ZZZ1` e número mecanográfico `f1` repetido duas vezes.

3. Guarde como `caderno_erros.csv` no Ambiente de Trabalho.

### Ficheiro 4 — `teste.xlsx` (ficheiro Excel — necessário apenas para o Teste K)

**Se tiver o Excel instalado:**

1. Abra o Excel e crie uma nova folha de cálculo vazia.
2. Na célula **A1** escreva `Nº Mecanográfico`; na célula **B1** escreva `Nome`.
3. Nas 20 linhas seguintes introduza dados (A2=`f1`, B2=`Sintético Teste 1`; A3=`f2`, B3=`Sintético Teste 2`; etc., até A21=`f20`, B21=`Sintético Teste 20`).
4. **Adicione uma segunda folha:** clique com o botão direito no separador da folha no fundo e escolha "Inserir folha" (ou prima o `+` ao lado do nome da folha). Deixe-a vazia ou com apenas um cabeçalho.
5. Guarde como `teste.xlsx` no Ambiente de Trabalho (Ficheiro → Guardar como → Formato Excel, extensão `.xlsx`).

**Se não tiver o Excel:** salte o Teste K ou use o LibreOffice Calc com o mesmo processo. O Teste K é opcional.

---

## 4. Testes de interface (A–H)

### Pré-requisito — limpar definições guardadas

Para garantir que a aplicação inicia como se fosse a primeira vez, execute os seguintes passos **uma única vez** antes de começar os testes:

1. Prima `Win + R`, escreva `powershell`, prima **Enter**.
2. Na janela do PowerShell que se abriu, escreva o seguinte e prima Enter:
   ```
   reg delete "HKCU\Software\EleitorUM" /f
   ```
3. Se aparecer a mensagem "Erro: não foi possível encontrar…", ignore — significa que as definições ainda não existiam. Se aparecer "A operação foi concluída com êxito", as definições foram apagadas.
4. Feche o PowerShell.

---

### Teste A — Primeiro lançamento (diálogo de boas-vindas)

**O que testa:** o diálogo de boas-vindas aparece automaticamente na primeira utilização.

**Passos:**
1. Faça duplo clique em `EleitorUM.exe`.

**O que deve ver:**
- Uma janela de diálogo com o título **"Bem-vindo ao EleitorUM"**
- Texto a explicar os 4 passos do assistente (seleccionar tipo, carregar ficheiro, mapear colunas, rever e gravar)
- Um botão **"Começar"**

**Verifique:**
- [ ] O diálogo de boas-vindas apareceu automaticamente
- [ ] O texto descreve os passos do assistente
- [ ] O botão "Começar" existe e funciona

**Após verificar:** clique em **Começar**.

**O que deve ver a seguir:**
- A janela principal com dois cartões: **"Caderno Eleitoral"** e **"Lista de Elegíveis"**
- Um indicador de passo no canto superior (ex: "Passo 1 de 5")
- O botão **"Anterior"** desactivado (aparência esbatida)

**Verifique:**
- [ ] A janela principal abriu após clicar "Começar"
- [ ] Os dois cartões de tipo de ficheiro estão visíveis
- [ ] O botão "Anterior" está desactivado

---

### Teste B — Alternância de tema (claro/escuro)

**O que testa:** o tema escuro funciona e é memorizado entre sessões.

**Passos:**
1. Na barra de menus, clique em **Ver → Tema Escuro**.

**O que deve ver:**
- A interface muda imediatamente para fundo escuro
- Todo o texto continua legível
- A opção no menu passa a ser **"Tema Claro"**

**Verifique:**
- [ ] A interface mudou para tema escuro imediatamente
- [ ] Todo o texto é legível no tema escuro
- [ ] A opção do menu passou de "Tema Escuro" para "Tema Claro"

**Passos:**
2. Feche a aplicação: **Ficheiro → Sair** (ou prima `Alt + F4`).
3. Abra novamente `EleitorUM.exe`.

**O que deve ver:**
- A aplicação abre em **tema escuro** (sem mostrar o diálogo de boas-vindas desta vez)

**Verifique:**
- [ ] A aplicação reabriu em tema escuro

4. Volte ao tema claro: **Ver → Tema Claro**.

---

### Teste C — Processamento completo: Caderno Eleitoral

**O que testa:** o fluxo completo do assistente para um caderno eleitoral válido.

**Passos:**
1. No ecrã principal (Passo 1), clique no cartão **"Caderno Eleitoral"** — deve ficar realçado com uma borda colorida.
2. Clique em **Próximo**.

**O que deve ver:** ecrã **"Carregar ficheiro"** com uma zona de largada de ficheiros.

3. Clique em **"ou escolher ficheiro…"** e na janela de abertura de ficheiro, navegue até ao Ambiente de Trabalho e seleccione `caderno_valido.csv`. (Alternativa: arraste o ficheiro directamente para a zona de largada.)
4. O nome do ficheiro deve aparecer na zona de largada e o botão **Próximo** fica activo.
5. Clique em **Próximo**.

**O que deve ver:** ecrã **"Mapeamento de colunas"** com as colunas detectadas automaticamente.

**Verifique:**
- [ ] A coluna "Numero Mecanografico" foi mapeada para Nº Mecanográfico (detectada automaticamente)
- [ ] A coluna "Nome" foi mapeada para Nome (detectada automaticamente)

6. Clique em **Próximo**.

**O que deve ver:** o ecrã de processamento **"A processar…"** aparece brevemente (pode ser muito rápido), seguido do ecrã **"Pré-visualização"**.

**O que deve ver no ecrã de Pré-visualização:**
- Uma tabela com as 5 linhas processadas (mec, nome, categoria)
- Número total de linhas e número de alterações aplicadas — o número de alterações deve ser **maior que zero** (existem espaços duplos e anotações entre parênteses para normalizar)
- Um botão **"Ver detalhes"**

**Verifique:**
- [ ] A tabela de pré-visualização mostra as 5 linhas
- [ ] O número de alterações aplicadas é maior que 0
- [ ] As anotações entre parênteses já não aparecem nas colunas de nome (ex: "(docente)" foi removido)

7. Clique em **"Ver detalhes"** para expandir o log de alterações — deve mostrar uma lista com as alterações efectuadas linha a linha.
8. Clique em **"Fechar detalhes"** para recolher o log.
9. Clique em **"Escolher destino e gravar"**.

**O que deve ver:** uma janela de guardar ficheiro.

10. Navegue até ao **Ambiente de Trabalho**. No campo "Nome do ficheiro" escreva `resultado_caderno` e clique em **Guardar**.

**O que deve ver:** um breve ecrã de processamento, depois o ecrã final **"Concluído"**.

**O que deve ver no ecrã "Concluído":**
- O texto **"Pronto!"**
- "X linhas processadas, Y alterações aplicadas."
- Três botões: **"Processar outro ficheiro"**, **"Abrir pasta"**, **"Sair"**

**Verifique:**
- [ ] O ecrã "Concluído" apareceu com o texto "Pronto!"
- [ ] O número de linhas processadas é 5
- [ ] O número de alterações é maior que 0
- [ ] Os três botões estão presentes

11. Clique em **"Abrir pasta"**.

**O que deve ver:** a pasta do Ambiente de Trabalho abre-se no Explorador de Ficheiros com dois novos ficheiros:
- `resultado_caderno.csv` — o ficheiro de saída
- `resultado_caderno_LOG_…csv` — o log de transformações (nome contém `_LOG_`)

**Verifique:**
- [ ] O ficheiro `resultado_caderno.csv` foi criado
- [ ] O ficheiro de log `_LOG_` foi criado

12. Abra `resultado_caderno.csv` com o **Bloco de Notas** (botão direito → Abrir com → Bloco de Notas).

**O que deve ver:**
```
f1;João Silva;
f2;Maria Santos;
f3;Pedro Costa;
f4;Ana Ferreira;
pg101;Rui Oliveira;
```
_(as anotações entre parênteses foram removidas; os espaços duplos normalizados; separador é ponto-e-vírgula; cada linha tem três campos terminados em `;`)_

**Verifique:**
- [ ] O separador é ponto-e-vírgula (`;`), não vírgula nem tabulação
- [ ] As anotações "(docente)" e "(investigador)" foram removidas
- [ ] Cada linha tem três campos (mec`;`nome`;`vazio)
- [ ] Existem exactamente 5 linhas de dados

---

### Teste D — Processamento completo: Lista de Elegíveis

**O que testa:** o fluxo do assistente para uma lista de elegíveis e a ordenação alfabética da saída.

**Passos:**
1. No ecrã "Concluído" do Teste C, clique em **"Processar outro ficheiro"**.
2. No Passo 1, clique no cartão **"Lista de Elegíveis"** e clique em **Próximo**.
3. Carregue `elegiveis_validos.csv` e clique em **Próximo**.
4. No ecrã de mapeamento, verifique que "Nome" foi detectado como coluna de nome. Clique em **Próximo**.
5. No ecrã de pré-visualização, clique em **"Escolher destino e gravar"**.
6. Guarde como `resultado_elegiveis` no Ambiente de Trabalho.

7. Abra `resultado_elegiveis.csv` com o Bloco de Notas.

**O que deve ver:**
```
0;Ana Ferreira
1;João Silva
2;Maria Santos
3;Pedro Costa
4;Rui Oliveira
```
_(ordenação alfabética NFKD; índice 0-based; sem terceiro campo vazio ao contrário do caderno)_

**Verifique:**
- [ ] O formato é `índice;nome` (dois campos, sem campo vazio final)
- [ ] Os nomes estão ordenados **alfabeticamente** (Ana, João, Maria, Pedro, Rui)
- [ ] O índice começa em **0** (não em 1)
- [ ] Existem exactamente 5 linhas

---

### Teste E — Rejeição de destino igual ao original

**O que testa:** a aplicação recusa gravar o ficheiro de saída sobre o ficheiro de entrada.

**Passos:**
1. Inicie um novo processamento: **Ficheiro → Reiniciar**.
2. Seleccione **"Caderno Eleitoral"** → Próximo.
3. Carregue `caderno_valido.csv` → Próximo.
4. No mapeamento de colunas → Próximo.
5. No ecrã de pré-visualização, clique em **"Escolher destino e gravar"**.
6. Na janela de guardar, navegue ao Ambiente de Trabalho e seleccione o ficheiro `caderno_valido.csv` (o mesmo ficheiro de entrada!).
7. Clique em **Guardar**.

**O que deve ver:**
- Uma mensagem de aviso: _"O destino não pode ser o mesmo ficheiro que o original. Escolha outro local."_
- A janela de guardar volta a aparecer para escolher outro destino

**Verifique:**
- [ ] A mensagem de aviso apareceu
- [ ] O ficheiro original não foi alterado
- [ ] A janela de guardar voltou a abrir

8. Desta vez, escolha um nome diferente (ex: `resultado_caderno2`) e clique em Guardar para confirmar que a gravação funciona com um nome diferente.

---

### Teste F — Menu Reiniciar

**O que testa:** o menu Reiniciar volta imediatamente ao Passo 1 sem pedir confirmação.

**Passos:**
1. Inicie um novo processamento: seleccione um tipo de ficheiro e avance até ao Passo 3 (Mapeamento de colunas) ou qualquer passo a meio.
2. No menu, clique em **Ficheiro → Reiniciar**.

**O que deve ver:**
- A interface volta imediatamente ao Passo 1 (selecção de tipo)
- Não aparece nenhum diálogo de confirmação
- Nenhum cartão está seleccionado

**Verifique:**
- [ ] A interface voltou ao Passo 1 imediatamente
- [ ] Não apareceu nenhum diálogo de confirmação
- [ ] Os cartões de tipo estão sem selecção

---

### Teste G — Diálogo "Sobre"

**O que testa:** o conteúdo e os elementos do diálogo de informação sobre a aplicação.

**Passos:**
1. No menu, clique em **Ajuda → Sobre…**

**O que deve ver:**
- Título da janela: **"EleitorUM — Sobre"**
- Cabeçalho: **"EleitorUM 1.0.0"**
- Descrição breve em português ("Utilitário para normalização de ficheiros eleitorais.")
- Nota de licença: **"Distribuído sob a licença MIT."**
- Uma hiperligação: **"Repositório no GitHub"**
- Um botão **"Fechar"**

**Verifique:**
- [ ] O título da janela é "EleitorUM — Sobre"
- [ ] O cabeçalho mostra **"EleitorUM 1.0.0"** (versão correcta)
- [ ] A nota de licença MIT está presente
- [ ] A hiperligação "Repositório no GitHub" existe
- [ ] **NÃO existe** nenhuma referência à Universidade do Minho ou "UMinho"

2. Clique na hiperligação **"Repositório no GitHub"**.

**O que deve ver:** o browser abre-se na página **`https://github.com/davidbarros2/eleitorum`**

**Verifique:**
- [ ] O browser abriu no endereço correcto do repositório

3. Feche o diálogo com o botão **"Fechar"**.

---

### Teste H — Persistência da geometria da janela

**O que testa:** o tamanho e a posição da janela são memorizados entre sessões.

**Passos:**
1. Com a janela principal aberta, arraste-a para uma posição diferente no ecrã (ex: canto superior direito).
2. Redimensione a janela arrastando um canto.
3. Feche a aplicação: **Ficheiro → Sair**.
4. Abra novamente `EleitorUM.exe`.

**O que deve ver:**
- A janela abre exactamente com o **mesmo tamanho** e na **mesma posição** que tinha antes de fechar

**Verifique:**
- [ ] A janela reabriu com o mesmo tamanho
- [ ] A janela reabriu na mesma posição no ecrã

---

## 5. Testes funcionais (I–L)

### Teste I — Formato de ficheiro não suportado

**O que testa:** a aplicação recusa ficheiros em formatos não suportados e mostra uma mensagem clara.

**Preparação:** crie um ficheiro de qualquer tipo com extensão não suportada. Por exemplo, abra o Bloco de Notas, escreva qualquer coisa, e guarde-o como `teste.docx` (escolha "Todos os ficheiros" no tipo e escreva o nome com `.docx`).

**Passos:**
1. Inicie um novo processamento: seleccione "Caderno Eleitoral" → Próximo.
2. Tente carregar `teste.docx` (ou qualquer ficheiro com extensão `.docx`, `.pdf`, `.txt`, etc.).

**O que deve ver:**
- Uma mensagem de erro visível na interface: _"O formato '.docx' não é suportado. Formatos aceites: XLSX, XLSM, XLS, ODS, CSV, TSV."_
- A zona de largada fica disponível para tentar outro ficheiro

**Verifique:**
- [ ] A mensagem de erro de formato não suportado apareceu com o nome do formato incorrecto
- [ ] A aplicação não bloqueou — continua a aceitar ficheiros

---

### Teste J — Ficheiro com erros de validação

**O que testa:** a aplicação detecta erros nos dados, não cria o ficheiro de saída, e cria um ficheiro de erros.

**Passos:**
1. Inicie um novo processamento: **Ficheiro → Reiniciar**.
2. Seleccione **"Caderno Eleitoral"** → Próximo.
3. Carregue `caderno_erros.csv` → Próximo.
4. No mapeamento de colunas, clique em Próximo (as colunas devem ser detectadas automaticamente).

**O que deve ver:** o ecrã final mostra **"Erro no processamento"** com a mensagem "Foram encontrados erros que impedem a criação do ficheiro."

**Verifique:**
- [ ] O ecrã de erro apareceu (e não o ecrã "Concluído")
- [ ] A mensagem informa que devem consultar o ficheiro de erros

5. Abra a pasta do Ambiente de Trabalho. Deve existir um ficheiro com `_ERRORS_` no nome (ex: `caderno_erros_ERRORS_….csv`). Não deve existir um ficheiro de saída.

**Verifique:**
- [ ] O ficheiro `_ERRORS_` foi criado
- [ ] **Não foi criado** nenhum ficheiro `resultado_caderno.csv` ou similar

6. Abra o ficheiro `_ERRORS_` com o Bloco de Notas.

**O que deve ver no ficheiro de erros:**
- Uma linha de erro referindo o prefixo inválido `ZZZ1`
- Uma linha de erro referindo o número mecanográfico duplicado `f1`

**Verifique:**
- [ ] O ficheiro de erros menciona o prefixo inválido
- [ ] O ficheiro de erros menciona o duplicado

---

### Teste K — Ficheiro Excel com múltiplas folhas (ecrã de selecção de folha)

_Este teste só é possível se criou o ficheiro `teste.xlsx` com duas folhas (ver Secção 3.4). Se não criou, assinale como "N/A"._

**Passos:**
1. Inicie um novo processamento: seleccione "Caderno Eleitoral" → Próximo.
2. Carregue `teste.xlsx` (o ficheiro Excel com duas folhas) → Próximo.

**O que deve ver:** um novo ecrã **"Escolher folha"** que não aparece para ficheiros CSV.

**O que deve ver neste ecrã:**
- Uma lista com o nome de cada folha
- Cada folha mostra o número de linhas entre parênteses
- Folhas sem dados têm a indicação "— folha vazia"

**Verifique:**
- [ ] O ecrã "Escolher folha" apareceu (aparece apenas para Excel com múltiplas folhas)
- [ ] As folhas do ficheiro estão listadas com o número de linhas

3. Seleccione a folha com dados e clique em **Próximo** para continuar o processamento normalmente.

---

### Teste L — Verificação detalhada do formato do ficheiro de saída

**O que testa:** o ficheiro CSV de saída tem exactamente o formato correcto para a plataforma eleitoral.

**Passos:**
1. Abra `resultado_caderno.csv` do Teste C com o **Bloco de Notas**.
2. Examine o conteúdo linha a linha.

**Verifique (caderno eleitoral):**
- [ ] O separador é **ponto-e-vírgula** (`;`), não vírgula (`,`) nem tabulação
- [ ] Cada linha de dados tem **três campos**: `mecanografico;nome;` (o terceiro campo, categoria, está sempre vazio)
- [ ] Não há aspas `"` em redor dos valores
- [ ] O ficheiro termina com uma **linha em branco** após a última linha de dados (ou seja, há um Enter depois da última linha)

3. Abra `resultado_elegiveis.csv` do Teste D com o Bloco de Notas.

**Verifique (lista de elegíveis):**
- [ ] O separador é ponto-e-vírgula
- [ ] Cada linha tem **dois campos**: `índice;nome` (sem terceiro campo)
- [ ] Não há aspas em redor dos valores
- [ ] O índice é numérico e começa em 0

**Nota sobre o BOM UTF-8:** os ficheiros de saída começam com uma marca invisível (BOM) que indica a codificação UTF-8. O Bloco de Notas pode mostrar caracteres estranhos no início — isso é **normal e esperado**. O Excel e a maioria das aplicações reconhece esta marca automaticamente.

---

## 6. Teste de linha de comandos (M)

### Teste M — Flag `--version`

**O que testa:** o executável reporta a versão correcta quando chamado com `--version`, sem abrir a janela gráfica.

**Passos:**
1. Prima `Win + R`, escreva `powershell`, prima **Enter**.
2. Na janela do PowerShell, navegue até à pasta do executável com o seguinte comando (ajuste o caminho se extraiu para outro local):
   ```powershell
   cd "$env:USERPROFILE\Desktop\EleitorUM-1.0.0-win64\EleitorUM"
   ```
3. Execute:
   ```powershell
   .\EleitorUM.exe --version
   ```

**O que deve ver:**
```
EleitorUM 1.0.0
```
_Apenas esta linha, sem mais texto, sem janela gráfica._

**Verifique:**
- [ ] O output é exactamente `EleitorUM 1.0.0`
- [ ] Nenhuma janela gráfica se abriu
- [ ] O PowerShell ficou disponível para o próximo comando (sem mensagens de erro)

---

## 7. Verificação do lançamento no GitHub (N)

_Este teste é observacional. Não requer instalar nada — apenas aceder ao GitHub no browser._

### Teste N — Pipeline de CI/CD e release automático

**Passos:**
1. Aceda a **https://github.com/davidbarros2/eleitorum/actions**
2. Procure a execução do workflow **"Release"** associada à tag v1.0.0.

**Verifique:**
- [ ] O workflow "Release" executou sem erros (ícone verde ✓)
- [ ] Os passos "Build Windows artifact", "Smoke test — --version" e "Publish GitHub Release" estão todos concluídos

3. Aceda a **https://github.com/davidbarros2/eleitorum/releases/tag/v1.0.0**

**Verifique:**
- [ ] A release v1.0.0 existe e está publicada (não é rascunho)
- [ ] O ficheiro `EleitorUM-1.0.0-win64.zip` está disponível
- [ ] O ficheiro `EleitorUM-1.0.0-win64.zip.sha256` está disponível

4. Aceda a **https://github.com/davidbarros2/eleitorum/actions** e procure o workflow **"CI"**.

**Verifique:**
- [ ] O CI passou nos jobs "test" (Python 3.11 e 3.12) e "audit"

---

## 8. Folha de resultados

Preencha esta tabela com os resultados de cada teste e devolva-a com as suas notas.

| Teste | Descrição | Resultado | Notas |
|-------|-----------|:---------:|-------|
| **A** | Diálogo de boas-vindas no primeiro lançamento | ✅ / ❌ / ? | |
| **B** | Tema escuro/claro com persistência | ✅ / ❌ / ? | |
| **C** | Caderno Eleitoral — ficheiro válido (fluxo completo) | ✅ / ❌ / ? | |
| **D** | Lista de Elegíveis — ordenação e formato | ✅ / ❌ / ? | |
| **E** | Rejeição de destino igual ao original | ✅ / ❌ / ? | |
| **F** | Menu Reiniciar volta ao Passo 1 sem confirmação | ✅ / ❌ / ? | |
| **G** | Diálogo Sobre — versão, licença, link, sem UMinho | ✅ / ❌ / ? | |
| **H** | Persistência de tamanho e posição da janela | ✅ / ❌ / ? | |
| **I** | Mensagem de erro para formato não suportado | ✅ / ❌ / ? | |
| **J** | Erros de validação: sem ficheiro de saída, log de erros criado | ✅ / ❌ / ? | |
| **K** | Ecrã de selecção de folha para Excel multi-folha | ✅ / ❌ / N/A | |
| **L** | Formato exacto do ficheiro CSV de saída | ✅ / ❌ / ? | |
| **M** | Flag `--version` sem janela gráfica | ✅ / ❌ / ? | |
| **N** | Pipeline GitHub Actions e release automático | ✅ / ❌ / ? | |

**Legenda:**
- **✅ Passou** — comportamento exactamente como esperado
- **❌ Falhou** — comportamento diferente do esperado (descreva na coluna Notas)
- **?** — não testado ou situação inesperada
- **N/A** — não aplicável (ex: Teste K sem Excel)

---

_Guia elaborado para EleitorUM v1.0.0 · Maio de 2026_
