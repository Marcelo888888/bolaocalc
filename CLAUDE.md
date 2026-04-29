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
service-worker.js    # Cache offline (versão atual: bolaocalc-v10)
manifest.json        # Metadados PWA
icon-192.png         # Ícone PWA 192x192
icon-512.png         # Ícone PWA 512x512
apple-touch-icon.png # Ícone iOS
qrcode.png           # QR code para acesso rápido
```

---

## Funcionalidades

### 1. Captura de Comprovante
- Foto pela câmera (capture="environment")
- Upload da galeria
- Entrada manual (fallback)

### 2. OCR com Gemini Vision
- Modelo primário: `gemini-2.5-flash`
- Fallbacks: `gemini-2.0-flash-lite`, `gemini-flash-latest`
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

### 6. Compartilhamento
- Botão "Compartilhar no WhatsApp" gera texto formatado com resumo por modalidade + tabela de cotas
- Usa `navigator.share` (mobile) ou copia para clipboard (desktop)

---

## Configurações (localStorage)
| Chave | Valor | Descrição |
|-------|-------|-----------|
| `gemini_key` | String | API key do Google AI Studio para Gemini Vision |

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
1. `gemini-2.5-flash` — primário, melhor qualidade
2. `gemini-2.0-flash-lite` — fallback econômico
3. `gemini-flash-latest` — fallback genérico

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
| `validationCard` null | Elemento removido do HTML | Removida referência no JS |

---

## Deploy
- GitHub Pages: branch `main`, raiz `/`
- Service worker atualizado a cada deploy (incrementar versão `bolaocalc-vN`)
- Para forçar atualização no browser: F12 → Application → Service Workers → Unregister → Ctrl+Shift+R

---

## Relação com Outros Projetos
- **INDEPENDENTE** do projeto PDV Gráfica (`pdv-grafica/`)
- Compartilham apenas o diretório pai (`Antigravity_Testes/`)
