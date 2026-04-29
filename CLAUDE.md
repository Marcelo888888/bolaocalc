# CLAUDE.md — BolãoCalc CAIXA

## Visão Geral
PWA (Progressive Web App) para calcular cotas de bolões de loteria da CAIXA. O usuário tira foto do comprovante da lotérica, o app faz OCR via Gemini Vision para extrair os jogos e calcula automaticamente o valor de cada cota.

---

## Stack
- **Frontend:** HTML5 + Vanilla JS + CSS3 (tudo em `index.html`, single-file app)
- **OCR:** Gemini Vision API (único motor ativo no fluxo principal)
- **PWA:** Service Worker + manifest.json (funciona offline)
- **Sem backend:** 100% client-side, roda no browser

---

## Estrutura de Arquivos
```
index.html           # App inteiro (HTML + CSS + JS inline)
service-worker.js    # Cache offline (versão atual: bolaocalc-v5)
manifest.json        # Metadados PWA
icon-192.png         # Ícone PWA 192x192
icon-512.png         # Ícone PWA 512x512
apple-touch-icon.png # Ícone iOS
qrcode.png           # QR code para compartilhar
```

---

## Estado Global (JavaScript)
| Variável | Tipo | Descrição |
|----------|------|-----------|
| `attempts` | Array | Histórico de tentativas (não usado ativamente) |
| `currentAttempt` | Number | Contagem de tentativas da sessão atual |
| `maxAttempts` | Number | Limite de 3 tentativas antes de redirecionar para entrada manual |
| `currentJogos` | Array | Array de objetos de jogo usados na tela atual |
| `currentTotalComprovante` | Number | Total lido do comprovante para validação |
| `deferredPrompt` | Event | Evento de instalação PWA guardado |

---

## Funcionalidades

### 1. Captura de Comprovante
- Foto pela câmera (capture="environment")
- Upload da galeria (segundo input sem `capture`, para compatibilidade iOS)
- Entrada manual (fallback sempre disponível)

### 2. Pipeline de OCR — Gemini Vision (único motor ativo)

O app tenta os modelos Gemini em sequência até obter um resultado consistente:

```javascript
const GEMINI_MODELS = ['gemini-2.5-flash', 'gemini-2.0-flash', 'gemini-2.0-flash-lite'];
```

Para cada modelo, tenta dois prompts:
1. **`GEMINI_PROMPT_PRIMARY`** — prompt detalhado descrevendo o layout físico do comprovante CAIXA
2. **`GEMINI_PROMPT_RETRY`** — prompt simplificado, disparado se o primeiro resultado for inconsistente

Se um modelo retorna 404, o app pula para o próximo modelo. Se todos falharem, mostra mensagem de erro específica.

**Chave API:** armazenada em `localStorage('gemini_key')`, configurável via modal ⚙️.

**Quando Gemini falha**, o app mostra erro específico por código HTTP — **não há fallback automático para OCR.space ou Tesseract**:
- `429` / `quota`: instrui a gerar nova chave em aistudio.google.com
- `400` / `invalid`: instrui a reconfigurar a chave
- `404`: modelo indisponível, sugere tentar novamente

### 3. Funções OCR Legadas (definidas mas não invocadas no fluxo principal)
`ocrWithOcrSpace()`, `ocrWithTesseract()`, `extractJogos()`, `extractTotal()`, `detectarModalidade()`, `parseNumOCR()`, `extrairNumerosLinha()` — mantidas no código mas não chamadas de `processarArquivo()`.

### 4. Pré-processamento de Imagem
- **`removePenMarks(file)`**: remove pixels azuis (hue 180–270) e vermelhos (hue 0–30/330–360) da imagem, substituindo por branco. Definida mas não chamada no fluxo atual.
- **`preprocessImage(file)`**: escala + grayscale + binarização para Tesseract. Definida mas não chamada no fluxo atual.
- **Para Gemini**: a imagem é enviada em base64 sem pré-processamento (raw).

### 5. Validação de Resultado
Após OCR com Gemini, `_validateGeminiResult(result)` verifica:
- `result.jogos` é array não-vazio
- Cada jogo tem `modalidade`, `qt > 0`, `vBolao > 0`
- Consistência interna: `|soma_jogos − totais_declarados| / totais_declarados ≤ 5%` → `consistent: true`

Resultados com `consistent: false` são guardados como `bestResult` e usados se nenhum modelo atingir consistência.

### 6. Correção Automática de Tarifa
Após o OCR, se `pctTar > 0` e a tarifa lida divergir >R$0,02 da calculada (`vBolao × pctTar / 100`), a tarifa calculada substitui a lida. Células com tarifa estimada/corrigida são marcadas com `*` amarelo na tabela de detalhes.

### 7. Validação de Totais (tela de detalhes)
`validateData(jogos, totalComprovante)` compara a soma dos bolões com o total do comprovante e exibe:
- Diferença ≤ 10% → `ok` (verde)
- Diferença 10–25% → aviso (sem cor de erro)
- Diferença > 25% → `error` (vermelho)

> **Bug conhecido:** `validateData` chama `document.getElementById('validationCard')` que **não existe no HTML** (o elemento foi removido). A chamada `.classList.add('show')` lança `TypeError`, que é capturado pelo `catch (errGemini)` e exibe mensagem de erro mesmo com OCR bem-sucedido. A solução é remover ou comentar essa linha.

### 8. Cálculo de Cotas
- `cota = (vBolao + vTarifa) / qt`
- Tabela de detalhes mostra cada linha com modalidade-concurso, qt, vBolão, vTarifa, cota
- Tela de resumo agrupa por valor de cota e exibe totais

### 9. Entrada Manual
Formulário com dropdown de modalidade + campos numéricos (qt, bolão, tarifa). Adiciona linhas dinamicamente. Modalidades no dropdown: MEGA, QUINA, LFACIL, LOTO, LOTOMANIA, TIMEMANIA.

### 10. Compartilhamento
Botão "Compartilhar no WhatsApp" usa `navigator.share()` se disponível, cai para `navigator.clipboard` e por último abre `wa.me/?text=...`.

---

## Configurações (localStorage)
| Chave | Valor | Descrição |
|-------|-------|-----------|
| `gemini_key` | String | API key do Google AI Studio para Gemini Vision |

---

## Padrões e Regras

### Chamada Gemini (`_callGemini`)
```javascript
generationConfig: { temperature: 0, maxOutputTokens: 4096 }
```
Sem `responseMimeType` — o JSON é extraído por regex do texto livre retornado (`texto.match(/\{[\s\S]*\}/)`).

### Estrutura JSON esperada do Gemini
```json
{
  "jogos": [
    {
      "modalidade": "MEGA",
      "concurso": "2995",
      "qt": 3,
      "vBolao": 30.00,
      "pctTar": 35,
      "vTarifa": 10.50
    }
  ],
  "totalBolao": 594.00,
  "totalTarifa": 207.85
}
```

### Lógica do Prompt
**Seção COM TARIFA:** colunas `MOD-CONC | C.T/C.V | V.BOLAO | %TAR | V.TARIFA`
- `MOD-CONC` ex `MEGA-2995` → `modalidade="MEGA"`, `concurso="2995"`
- `C.T/C.V` ex `3/0` → `qt = número ANTES da barra`
- Se `vTarifa` ilegível: `vBolao × pctTar / 100`

**Seção SEM TARIFA:** colunas `MODALIDADE | QTDADE | VLR.BOLAO` → `vTarifa=0`, `pctTar=0`

### Modalidades Reconhecidas
`MEGA`, `QUINA`, `LOTOFÁCIL`, `LOTOMANIA`, `TIMEMANIA`, `DUPLA SENA`, `DIA DE SORTE`

---

## Fluxo de Telas (UI)

```
cameraSection (início)
    ↓ foto/galeria → processarArquivo()
ocrLoading (spinner)
    ↓ sucesso → validateData() → showDetails()
detailCard (tabela linha a linha)
    ↓ "Ver Resumo" → showResult()
resultCard (agrupado por cota)
    ↓ "Novo Bolão" → resetAll()

cameraSection → "Digitar Manualmente"
    ↓
manualCard → calculateManual() → showDetails()

Após 3 tentativas sem sucesso → showManualEdit()
```

---

## Service Worker
- **Versão atual:** `bolaocalc-v5`
- Estratégia: cache-first, fallback para rede
- Ao ativar: remove todos os caches com nome diferente de `bolaocalc-v5`
- **Importante:** ao incrementar versão do cache, alterar `CACHE_NAME` em `service-worker.js`

---

## Deploy
- Site estático (GitHub Pages ou similar)
- Funciona offline após primeira visita
- Sem servidor, sem build step — editar `index.html` diretamente

---

## Convenções de Desenvolvimento
- **Single-file:** todo código vive em `index.html` (HTML + `<style>` + `<script>`)
- **Sem frameworks, sem bundler, sem npm**
- Testar mudanças abrindo `index.html` direto no browser ou via servidor estático local
- Ao mudar arquivos cacheados pelo SW, incrementar `CACHE_NAME` em `service-worker.js`
- Valores monetários: sempre usar `.toFixed(2)` e substituir `.` por `,` para exibição em pt-BR

---

## Relação com Outros Projetos
- **INDEPENDENTE** do projeto PDV Gráfica (`pdv-grafica/`)
- Compartilham apenas o diretório pai (`Antigravity_Testes/`)
- Stacks diferentes, repositórios Git separados
