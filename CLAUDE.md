# CLAUDE.md — BolãoCalc CAIXA

## Visão Geral
PWA (Progressive Web App) para calcular cotas de bolões de loteria da CAIXA. O usuário tira foto do comprovante da lotérica, o app faz OCR via Gemini Vision para extrair os jogos e calcula automaticamente o valor de cada cota.

**URL produção:** https://marcelo888888.github.io/bolaocalc

---

## Stack
- **Frontend:** HTML5 + Vanilla JS + CSS3 (tudo em `index.html`, single-file app)
- **OCR:** Gemini Vision (único motor ativo — OCR.space e Tesseract são legados desativados)
- **PWA:** Service Worker + manifest.json (funciona offline após primeira visita)
- **Sem backend:** 100% client-side, roda no browser

---

## Estrutura de Arquivos
```
index.html           # App inteiro (HTML + CSS + JS inline)
service-worker.js    # Cache offline (versão atual: bolaocalc-v35)
manifest.json        # Metadados PWA
icon-192.png         # Ícone PWA 192x192
icon-512.png         # Ícone PWA 512x512
apple-touch-icon.png # Ícone iOS
qrcode.png           # QR do link p/ gerar a chave Gemini (aistudio.google.com/apikey) — usado DENTRO do
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
- Gate de documento errado (não documentado até 2026-07-20): `mostrarDocErrado(tipo)` — se o Gemini
  identificar que a foto não é o Resumo de Bolão (ex.: Listagem PIX), mostra aviso específico e volta pra
  câmera sem montar tabela nem contar como tentativa falha.

### 2. OCR com Gemini Vision
- Modelo primário: `gemini-3.5-flash`
- Fallbacks: `gemini-2.5-flash`, `gemini-3.1-flash-lite`
- 2 tentativas por modelo (prompt detalhado + simplificado)
- Validação interna: compara soma dos jogos vs totais declarados (≤5% = consistente)
- Chave API armazenada em `localStorage('gemini_key')`
- `maxOutputTokens: 8192` — necessário para comprovantes com 15+ jogos

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

## Configurações (localStorage)
| Chave | Valor | Descrição |
|-------|-------|-----------|
| `gemini_key` | String | API key do Google AI Studio para Gemini Vision. **Isolado por origem** (github.io ≠ IP local) — ver v4 na seção 6 sobre como a chave atravessa a troca de origem nos redirects do próprio app. |
| `lca_server` | String | IP/host do PC (LCA) salvo no ⚙️ — usado por `getLcaUrl()` fora do GitHub Pages, e como base do link "local" no GitHub Pages. Faltava nesta tabela até 2026-07-20 (corrigido). |
| `lca_operador` | Number (id) | Operador selecionado no ⚙️ — vai no payload de `POST /scan/boloes`. Faltava nesta tabela até 2026-07-20 (corrigido). |

---

## Padrões e Regras

### Prompt do Gemini
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

### Modelos Gemini (ordem de tentativa)
1. `gemini-3.5-flash` — primário, melhor qualidade
2. `gemini-2.5-flash` — fallback estável/maduro
3. `gemini-3.1-flash-lite` — fallback econômico/rápido

**Atenção:** `gemini-2.0-flash` e `gemini-1.5-flash` foram descontinuados/removidos da API.
`responseMimeType: "application/json"` causa HTTP 400 com gemini-2.5-flash — não usar.

---

## Erros Conhecidos e Tratamento
| Erro | Causa | Tratamento |
|------|-------|-----------|
| HTTP 429 | Quota free tier esgotada | Mensagem: gerar nova chave |
| HTTP 400 expired | Chave expirada | Mensagem: configurar nova chave no ⚙️ |
| HTTP 404 | Modelo descontinuado | Tenta próximo modelo da lista |
| JSON truncado | maxOutputTokens insuficiente | Aumentar limite (hoje: 8192) |
| Documento errado (ex.: Listagem PIX) | Foto não é o Resumo de Bolão | `mostrarDocErrado(tipo)` avisa e volta pra câmera, sem contar tentativa |

---

## Deploy
- GitHub Pages: branch `main`, raiz `/`
- Service worker atualizado a cada deploy (incrementar versão `bolaocalc-vN`)
- Para forçar atualização no browser: F12 → Application → Service Workers → Unregister → Ctrl+Shift+R

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
