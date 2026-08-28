# CLAUDE.md — BolãoCalc CAIXA

## Visão Geral
PWA (Progressive Web App) para calcular cotas de bolões de loteria da CAIXA. O usuário tira foto do comprovante da lotérica, o app faz OCR por um modelo de visão para extrair os jogos e calcula automaticamente o valor de cada cota.

**URL produção:** https://marcelo888888.github.io/bolaocalc

---

## Stack
- **Frontend:** HTML5 + Vanilla JS + CSS3 (tudo em `index.html`, single-file app)
- **OCR:** modelo de visão (único motor — o código morto de OCR.space e Tesseract foi removido na v37)
- **PWA:** Service Worker + manifest.json (funciona offline após primeira visita)
- **Sem backend:** 100% client-side, roda no browser

---

## Estrutura de Arquivos
```
index.html           # App inteiro (HTML + CSS + JS inline)
service-worker.js    # Cache offline (versão atual: bolaocalc-v39)
manifest.json        # Metadados PWA
icon-192.png         # Ícone PWA 192x192
icon-512.png         # Ícone PWA 512x512
apple-touch-icon.png # Ícone iOS
qrcode.png           # QR do link p/ gerar a chave de acesso (aistudio.google.com/apikey) — usado DENTRO do
                      # app, no modal ⚙️ Configurações. NÃO abre o app — corrigido em 2026-07-20 depois
                      # do README/topo apontar pra ele por engano (ver qrcode_app.png abaixo).
qrcode_app.png        # QR do link do app (https://marcelo888888.github.io/bolaocalc) — usado no topo
                      # do README.md. Gerado em 2026-07-20 (antes disso o README usava qrcode.png por
                      # engano, que na real aponta pra outro lugar — ver acima).
```

> Existe um TERCEIRO QR, gerado em tempo real (não é arquivo estático aqui) — o da aba **Scan** do LCA
> principal (`js/scan.js`, `scanRenderQrBox()`), que aponta pro endereço da rede local
> (`http://<ip-do-pc>:8000/bolaocalc/`). Esse é o recomendado pra abrir/usar o app na loja (sem bloqueio
> de conteúdo misto), mas **não é instalável como PWA completo** — HTTP não-localhost não é "contexto
> seguro", então o service worker não registra e o banner de instalar não aparece ali. Pra instalar de
> verdade (ícone próprio, offline), o caminho é a URL do GitHub Pages (HTTPS).

---

## Funcionalidades

### 1. Captura de Comprovante
- Foto pela câmera (capture="environment") via `iniciarFoto()` — ver nota de 2026-07-20 na seção 6
  sobre a pergunta "uso manual?" antes de abrir a câmera.
- Upload da galeria
- ~~Entrada manual (fallback)~~ — **removida** (commit "Fases 3-5 ... remove digitacao manual", SW v31,
  antes de qualquer trabalho de 2026-07-20). `retakePhoto()` só reabre a câmera; não existe mais botão
  "✏️ Digitar Manualmente" no HTML nem no README. Se essa doc dizia o contrário até 2026-07-20, estava
  desatualizada — corrigido.
- Gate de documento errado (não documentado até 2026-07-20): `mostrarDocErrado(tipo)` — se o motor
  identificar que a foto não é o Resumo de Bolão (ex.: Listagem PIX), mostra aviso específico e volta pra
  câmera sem montar tabela nem contar como tentativa falha.

### 2. OCR por visão computacional
- Modelo primário: `gemini-3.1-flash-lite` (o mais barato)
- Fallbacks: `gemini-3.6-flash`, `gemini-3.5-flash` — nessa ordem, do mais barato ao mais caro
- 2 tentativas por modelo (prompt detalhado + simplificado)
- Validação interna: compara soma dos jogos vs totais declarados (≤5% = consistente)
- Chave API armazenada em `localStorage('app_access_key')` (migra sozinha da antiga `gemini_key`)
- `maxOutputTokens: 16384` + `thinkingLevel: 'minimal'` — necessário para comprovantes com 15+ jogos

**2026-08-28 (v41) — a chave é identificada, nunca exibida.** O ⚙️ despejava a chave
inteira dentro do campo de senha e o diálogo do "🔗 Abrir local" mostrava a URL com
`#gk=<chave completa>` — visível na tela e em qualquer captura. Agora:

- o campo do ⚙️ abre **vazio** (preencher = trocar; em branco = manter) e acima dele
  aparece `🔑 Chave em uso: ••••ONMg · salva em 28/08/2026`. Só os **4 últimos
  caracteres**, que é o que basta para saber se o aparelho está com a chave nova ou com
  a que já esgotou — o fluxo do dono é apagar a chave esgotada e gerar outra;
- o diálogo do "Abrir local" mostra o endereço **sem** o `#gk=`; a navegação continua
  levando a chave.
- **Limite:** a chave ainda passa pelo hash e aparece na barra de endereço por um
  instante até `sincronizarChaveDoHash()` limpar com `history.replaceState`. Eliminar
  isso exigiria outro mecanismo de transporte.

**2026-08-28 (v40) — a chave é gravada em DOIS nomes de propósito.** A v39 renomeou a
chave de `gemini_key` para `app_access_key` **e apagava a antiga**. Como o app tem duas
instalações (seção própria abaixo) e a do PC estava na v36 — que lê o nome antigo —, quem
configurasse numa precisava digitar de novo na outra. `gravarAccessKey()` grava nos dois.
**Remover a escrita duplicada quando todas as cópias estiverem >= v40**, inclusive as
mídias de instalação do local B.

**2026-08-28 (v37→v39) — troca de geração dos motores, marca branca e rede de segurança.**
O app tinha parado de ser confiável porque a cascata apontava para modelos mortos:
o primário estava em fim de vida (o provedor já o derrubou uma vez antes da data
anunciada) e o terceiro não existia mais — ou seja, toda foto gastava requests em
404 antes de chegar num motor vivo. O que mudou:

- Cascata trocada pelos modelos atuais, **ordenada por preço** (ver "Ordem da lista fixa").
  Numa primeira versão (v37) a ordem saiu errada — `3.5-flash` na frente do `3.6-flash`,
  sendo o 3.5 o dobro do preço. Corrigido na v38.
- `thinkingLevel: 'minimal'` + `maxOutputTokens: 16384`. O modo de raciocínio da
  geração 3 vem **ligado por padrão** e divide o orçamento de saída com o JSON —
  era a causa real do "JSON truncado" que esta doc registrava como falta de limite.
  O código tinha `thinkingBudget: 0`, que resolve o mesmo, mas é o parâmetro legado
  e a doc oficial diz para não combinar com o novo.
- `temperature: 0` removido: virou desaconselhado na geração 3 (risco de loop).
- Removidos `ocrWithOcrSpace()` e `ocrWithTesseract()` — **nenhum dos dois tinha
  chamador** — junto com o `<script>` do tesseract.js (CDN externa que o service
  worker nem cacheava, então offline falhava de qualquer jeito) e uma **chave de
  API do OCR.space que estava hardcoded** no fonte de um repositório público.
- Marca branca (seção própria abaixo) e descoberta automática de motores (idem).
- Como o app é usado em **duas máquinas (A e B)**, cada uma dessas mudanças só
  chega depois do ⚙️ → "Forçar atualização" nas duas — ver Deploy.

> Armadilha de processo desta sessão: o trabalho começou sobre uma cópia local
> atrasada (v22) enquanto o repositório já estava na v36, e o `git push` foi
> rejeitado no fim. **Antes de mexer, `git pull`** — as duas máquinas commitam aqui.

### 3. Validação
- Compara `soma(vBolao + vTarifa)` vs `totalComprovante` (bolão+tarifa do comprovante)
- Diferença calculada corretamente incluindo tarifa nos dois lados
- Exibe: jogos encontrados, soma bolão+tarifa, total no comprovante, diferença %

### 4. Tela de Detalhes (Linha a Linha)
- Tabela com todas as linhas: MOD-CONC, Qt, V.Bolão, V.Tarifa, Cota
- Tarifa estimada (calculada via %TAR) marcada em amarelo com asterisco

### 5. Tela de Resumo Final
- **Resumo por modalidade** (acima): modalidade, nº de jogos/cotas, cota calculada
- **Detalhamento por cota** (abaixo): valor da cota, quantidade total de cotas
- Totais gerais: total de cotas e valor total (bolão + tarifa)

### 6. Transmitir para o PC
- Botão "📡 Transmitir para o PC" (tela de Resumo) faz `POST /scan/boloes` pro LCA.
- No GitHub Pages (HTTPS), fetch pro PC em HTTP é bloqueado por conteúdo misto mesmo com IP configurado —
  o indicador do cabeçalho mostra "🔗 Abrir local" nesse caso.
- **2026-07-20 (v1):** clicar em "Transmitir para o PC" com a conexão não confirmada passou a abrir
  direto a versão local em vez de deixar o fetch falhar. Só que isso é navegação de página inteira (troca
  de origem) → `currentJogos` se perde → obrigava a repetir a foto. Feedback do Marcelo: inaceitável.
- **2026-07-20 (v2) — a pergunta migrou pra ANTES da foto:** `iniciarFoto()` (botão "📸 Tirar Foto") checa
  a mesma condição (GitHub Pages + PC configurado + conexão não confirmada) e redireciona pra
  `http://<ip>:8000/bolaocalc/?autofoto=1` **antes** de tirar a foto (se for o caso). Na página local, a
  IIFE `autoFotoAoAbrirLocal()` detecta `?autofoto=1`, limpa o parâmetro da URL (`history.replaceState`,
  evita reabrir em F5) e tenta `fileInput.click()` sozinha; como alguns navegadores bloqueiam abrir o
  seletor de arquivo fora de um gesto do usuário, o botão `#btnTirarFoto` também ganha destaque visual
  (`.pulse-destaque`) e `scrollIntoView` como reforço — pior caso, é só 1 toque, não repete o fluxo todo.
  Resultado: nenhum jogo é perdido, porque a troca de origem acontece antes do OCR rodar.
- **2026-07-20 (v3, atual) — modal próprio em vez de `confirm()`:** o `confirm()` nativo só permite
  botões genéricos "OK"/"Cancelar", que exigiam uma frase explicativa longa pra não confundir qual era
  qual. Trocado por `#fotoIntentModal` (mesmo padrão visual do `#configModal`) com dois botões diretos:
  **"📡 Transmitir PC"** (chama `fotoIntentTransmitir()` → salva `_fotoIntentIpHost` e redireciona pra
  `?autofoto=1`) e **"🧮 Só Calc Manual"** (chama `fotoIntentManual()` → fecha o modal e abre a câmera ali
  mesmo). `iniciarFoto()` só abre o modal quando a condição (GitHub Pages + IP configurado + não
  confirmado) é verdadeira; fora isso vai direto pra `fileInput.click()`.
- O redirect antigo dentro de `transmitirParaPC()` (v1) **ficou como rede de segurança** — cobre o caso
  de alguém responder "uso manual" na foto e mudar de ideia já na tela de Resumo; nesse caso específico
  ainda perde os jogos lidos (é exceção, não o caminho normal).
- **2026-07-20 (v4) — chave Gemini atravessa a troca de origem:** `localStorage` é isolado por origem
  (github.io e IP local são origens diferentes) — sem isso, cada vez que a versão local abria pela
  primeira vez, faltava a chave e o OCR falhava com "Leitura não configurada", obrigando reconfigurar
  na mão. Todo redirect pra versão local (`fotoIntentTransmitir()`, o fallback em `transmitirParaPC()`,
  o de `salvarConfig()` e o do indicador "🔗 Abrir local") agora usa `localUrlComChave(ipHost, caminho)`,
  que anexa a chave no **hash** da URL (`#gk=...` — nunca em query string, hash não vai pro servidor/log).
  `sincronizarChaveDoHash()` na página local lê o hash, grava em `localStorage` **só se ainda não
  houver chave local** (não sobrescreve uma já configurada) e limpa o hash da barra de endereço.
  **Limite:** só sincroniza nos redirects feitos pelo próprio app; abrir a versão local direto (ex.: QR
  da aba Scan do LCA, sem passar por nenhum desses botões) ainda exige configurar a chave uma vez nessa
  origem, manualmente.

> Removido em 2026-07-20: botão/função "Compartilhar no WhatsApp" (`compartilhar()`, baseada em
> `navigator.share`/`navigator.clipboard` — quebrava justamente no cenário acima, contexto HTTP inseguro).
> Considerado desnecessário; eliminado do HTML e do JS.

---

## ⚠️ Marca branca — o fornecedor de OCR não aparece na interface

O app vai ser distribuído e o dono não quer expor qual tecnologia de IA usa.
Regras ao mexer no código:

- **Nenhum texto visível ao usuário** pode citar o fornecedor ou o ID do modelo —
  isso inclui `setOcrStatus`, mensagens de erro, o modal do ⚙️ e os comentários do
  fonte (o `index.html` é servido inteiro, comentário também é visível).
- Erros crus da API passam por **`sanitizarErro()`** antes de ir para a tela: troca
  `models/<id>`, o nome do fornecedor e o host por termos neutros.
- Identificadores internos são neutros: `OCR_ENGINES`, `_callEngine`, `ocrWithEngine`,
  `getAccessKey`, `showErroLeitura`, `accessKeyInput`.
- **Limite conhecido e aceito:** os IDs em `OCR_ENGINES` e o host da API vão na URL
  da requisição — quem abrir o DevTools descobre. Esconder de verdade exigiria um
  backend intermediando as chamadas. Este `CLAUDE.md` também é público (o repo é
  público por causa do GitHub Pages) — decisão consciente de 2026-08-28.

## Configurações (localStorage)
| Chave | Valor | Descrição |
|-------|-------|-----------|
| `ocr_engines_cache` | JSON `{ts, valor:[...]}` | Motores descobertos no servidor, validade de 7 dias. Some sozinho; pode apagar sem medo. |
| `ocr_engine_preferido` | JSON `{ts, valor:"..."}` | Último motor descoberto que funcionou; tentado antes da lista fixa. |
| `app_access_key` | String | API key do provedor de visão (migrada de `gemini_key`, usada até a v36). **Isolado por origem** (github.io ≠ IP local) — ver v4 na seção 6 sobre como a chave atravessa a troca de origem nos redirects do próprio app. |
| `lca_server` | String | IP/host do PC (LCA) salvo no ⚙️ — usado por `getLcaUrl()` fora do GitHub Pages, e como base do link "local" no GitHub Pages. Faltava nesta tabela até 2026-07-20 (corrigido). |
| `lca_operador` | Number (id) | Operador selecionado no ⚙️ — vai no payload de `POST /scan/boloes`. Faltava nesta tabela até 2026-07-20 (corrigido). |

---

## Padrões e Regras

### Prompt do motor de leitura
Dois prompts por tentativa:
- **Primary**: descreve layout do comprovante CAIXA (MOD-CONC, C.T/C.V, seções COM/SEM TARIFA)
- **Retry**: versão simplificada com as mesmas regras

Estrutura JSON esperada:
```json
{
  "jogos": [{"modalidade":"MEGA","concurso":"2995","qt":3,"vBolao":30.00,"pctTar":35,"vTarifa":10.50}],
  "totalBolao": 594.00,
  "totalTarifa": 207.85
}
```

### Cálculo de Cota
`cota = (vBolao + vTarifa) / qt`

### Correção Automática de Tarifa
Se `vTarifa` lido difere em >R$0,02 do calculado (`vBolao × pctTar / 100`), usa o calculado e marca como estimada.

## Motores de leitura

### Descoberta automática (v39)

Se **todos** os motores da lista fixa responderem 404 — o provedor aposentou os
IDs escritos no código — o app chama `GET {API_BASE}/models` e passa a usar o que
existe hoje, sem precisar de deploy nas máquinas. Detalhes que importam:

- **Só dispara depois de 404 em todos os fixos.** No caminho normal não há request
  extra nenhum.
- Filtra por `generateContent` + nome com `flash`, descartando o que não serve para
  OCR (`image`, `tts`, `live`, `transcribe`, `embedding`, `audio`, `video`, `gemma`,
  `omni`) via `MOTOR_INCOMPATIVEL`.
- Ordena por custo em `_ordenarPorCusto`: `lite` primeiro, depois versão mais nova,
  `preview`/`exp` por último. É heurística por nome — quando os preços mudarem de
  forma relevante, revisar aqui.
- Tenta no máximo `MAX_MOTORES_DESCOBERTOS` (3).
- **Cache:** a lista fica em `localStorage.ocr_engines_cache` e o motor que
  funcionou em `ocr_engine_preferido`, ambos com validade de 7 dias
  (`CACHE_TTL_MS`). O preferido é tentado **antes** da lista fixa, para não
  desperdiçar 404 a cada foto enquanto o deploy não acontece. Ele é descartado
  assim que voltar a dar 404.
- Se a própria listagem falhar (403, rede), o erro original da leitura é o que
  aparece na tela — a descoberta nunca piora a mensagem.

**Isso não substitui atualizar a lista fixa.** É rede de segurança: quando cair
nesse caminho, o certo é olhar o console (`Motores descobertos: ...`) e promover o
modelo bom para `OCR_ENGINES`, escolhendo pelo preço real e não pela heurística.

### Ordem da lista fixa

A ordem é **econômica**, não por qualidade — `_validateResult` só aceita o resultado
se a soma dos jogos fechar com os totais do comprovante (≤5%), então um erro do
modelo barato faz a cascata subir sozinha para o próximo. O pior caso é uma
chamada extra.

1. `gemini-3.1-flash-lite` — primário, $0.25/$1.50 por milhão de tokens
2. `gemini-3.6-flash` — $0.75/$3.75 (vira $1.50/$7.50 em 01/01/2027)
3. `gemini-3.5-flash` — último recurso, $1.50/$9.00

A ordem continua válida depois do reajuste de 2027: o 3.6 fica com o mesmo
preço de entrada do 3.5 e ainda mais barato na saída.

**Atenção — armadilhas do Gemini 3:**
- O *thinking* vem **ligado por padrão** e seus tokens são descontados do
  `maxOutputTokens`. Sem limitá-lo o JSON volta vazio ou truncado em comprovante
  grande. Usar `thinkingConfig: { thinkingLevel: 'minimal' }` — `thinkingBudget`
  é o parâmetro legado e não deve ser combinado com o novo.
- `temperature: 0` passou a ser **desaconselhado** (risco de loop). Deixar no default.
- Usar IDs **explícitos**, nunca o alias `gemini-flash-latest`: o alias troca de
  modelo sem aviso.
- `gemini-2.5-flash`, `gemini-2.0-flash*` e `gemini-1.5-flash` estão descontinuados
  ou em fim de vida — não voltar para eles.
- `responseMimeType: "application/json"` causava HTTP 400 no 2.5-flash; não foi
  reavaliado no 3.x. O parsing por regex em `_callEngine` é o que está em uso.

---

## Erros Conhecidos e Tratamento
| Erro | Causa | Tratamento |
|------|-------|-----------|
| HTTP 429 | Limite de requisições atingido — **a chave é da conta paga do Marcelo**, não é quota de free tier; provavelmente rate limit (req/min), não falta de crédito | Mensagem ao usuário: "❌ Limite de leitura atingido" (código não sugere gerar nova chave — isso não resolve rate limit numa chave paga do mesmo projeto) |
| HTTP 400 expired | Chave expirada | Mensagem: configurar nova chave no ⚙️ |
| HTTP 404 | Motor aposentado pelo provedor | Tenta o próximo da lista; se **todos** derem 404, cai na descoberta automática (ver seção Motores de leitura) |
| JSON truncado / resposta vazia | thinking consumindo o `maxOutputTokens` | `thinkingLevel: 'minimal'` + limite 16384 |
| Documento errado (ex.: Listagem PIX) | Foto não é o Resumo de Bolão | `mostrarDocErrado(tipo)` avisa e volta pra câmera, sem contar tentativa |

---

## ⚠️ O app tem DUAS instalações — atualizar as duas

Descoberto em 2026-08-28, depois de a máquina A abrir a v39 e a aba Scan do LCA
continuar mostrando v36. Os dois números estavam certos: são instalações diferentes.

| Instalação | Onde | Quem usa |
|---|---|---|
| **GitHub Pages** | `https://marcelo888888.github.io/bolaocalc` — este repositório | celular via HTTPS |
| **Cópia no SistLCA** | `C:\dev\Sist_Lca\bolaocalc\` — servida pelo PC em `http://<ip>:8000/bolaocalc/` | QR da aba Scan do LCA, rede local |

A cópia do SistLCA é **vendorizada, não é submódulo**: são os mesmos arquivos copiados
à mão. `js/scan.js` do SistLCA lê o `service-worker.js` dessa cópia e mostra "Versão no
PC: vN" — é o número dela, não o do GitHub Pages.

**Ao publicar aqui, copiar `index.html` e `service-worker.js` para lá também** e commitar
no SistLCA **por caminho explícito** (naquele repo `git add -A` é proibido; ver o
`CLAUDE.md`/`AGENTS.md` de lá, que exige registrar a tarefa no `docs/ai/STATE.json` e
escrever no `docs/ai/HANDOFF.md`).

Ainda existem cópias de instalação do **local B** — `_pendriveB/codigo/bolaocalc/` (não
versionada), `C:\dev\_LCA_INSTALL_LOCAL_B\` e `C:\dev\LCA_INSTALL_copia_pendrive\`.
Em 2026-08-28 as três estavam na v36.

**Consequência prática:** enquanto as instalações estiverem em versões diferentes, elas
precisam concordar no nome da chave no `localStorage` — por isso a v40 grava em
`app_access_key` **e** `gemini_key`. Ver a nota da v40 na seção de OCR.

---

## Deploy
- GitHub Pages: branch `main`, raiz `/`
- **`git pull` antes de começar** — o app é usado em duas máquinas (A e B) e as duas
  commitam neste repo. Já houve push rejeitado por trabalhar sobre cópia atrasada.
- A cada deploy, incrementar **os dois** juntos: `CACHE_NAME` em `service-worker.js`
  e o badge `id="appVersion"` no topo do `index.html`. Eles saíram de sincronia uma
  vez (badge v31 com SW v36) e o badge é justamente como se confere, no celular, se
  a máquina já pegou a versão nova.
- Publicação no Pages leva ~1 min depois do push. Conferir com:
  `curl -s https://marcelo888888.github.io/bolaocalc/service-worker.js | head -1`
- **Em cada máquina/celular:** ⚙️ → "Forçar atualização" (`forcarAtualizacao()`, que
  desregistra o service worker e limpa os caches) → conferir o badge no topo. Sem
  isso o service worker antigo continua servindo a versão velha do cache.
- Alternativa no desktop: F12 → Application → Service Workers → Unregister → Ctrl+Shift+R

---

## Relação com Outros Projetos
> Corrigido em 2026-07-20 — a versão anterior citava uma pasta (`Antigravity_Testes/`) que não existe
> mais no ambiente atual; ficou desatualizada numa reorganização de pastas não registrada aqui.

- Vive em disco dentro do repo do LCA (`C:\dev\Sist_Lca\bolaocalc\`), mas é um **git independente**
  (remoto próprio `github.com/Marcelo888888/bolaocalc.git`, branch `main`) — commits e push aqui NÃO
  passam pelo git do `Sist_Lca` (remoto `github.com/Marcelo888888/Sist_Lca.git`). É preciso `git push`
  dentro da própria pasta `bolaocalc/` pra publicar no GitHub Pages; editar o arquivo local não basta
  (isso já causou confusão em 2026-07-20 — ver `memory` do Cowork, "iPhone versão antiga").
- **INDEPENDENTE** do projeto PDV Gráfica — não encontrado em `C:\dev` no ambiente atual; se existir,
  é em outro lugar/máquina, sem relação de código com este app.
