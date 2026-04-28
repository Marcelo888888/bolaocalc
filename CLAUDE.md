# CLAUDE.md — BolãoCalc CAIXA

## Visão Geral
PWA (Progressive Web App) para calcular cotas de bolões de loteria da CAIXA. O usuário tira foto do comprovante da lotérica, o app faz OCR para extrair os jogos e calcula automaticamente o valor de cada cota.

---

## Stack
- **Frontend:** HTML5 + Vanilla JS + CSS3 (tudo em `index.html`, single-file app)
- **OCR Pipeline:** Gemini Vision (primário) → OCR.space (fallback) → Tesseract.js (último recurso)
- **PWA:** Service Worker + manifest.json (funciona offline)
- **Sem backend:** 100% client-side, roda no browser

---

## Estrutura de Arquivos
```
index.html           # App inteiro (HTML + CSS + JS inline)
service-worker.js    # Cache offline (versão: bolaocalc-v2)
manifest.json        # Metadados PWA
icon-192.png         # Ícone PWA 192x192
icon-512.png         # Ícone PWA 512x512
apple-touch-icon.png # Ícone iOS
qrcode.png           # QR code para compartilhar
```

---

## Funcionalidades

### 1. Captura de Comprovante
- Foto pela câmera (capture="environment")
- Upload da galeria
- Entrada manual (fallback)

### 2. Pipeline de OCR (3 camadas com retry inteligente)
1. **Gemini 3 Flash** (primário): Envia imagem raw em base64. Usa 2 prompts:
   - Prompt detalhado (descreve layout físico do comprovante CAIXA)
   - Prompt simplificado (retry automático se 1ª tentativa for inconsistente)
   - Validação interna: compara soma dos jogos vs totais declarados (≤5% = consistente)
   - Chave API armazenada em `localStorage('gemini_key')`.
2. **OCR.space** (fallback): API key hardcoded `K82269935`. Usa Engine 2, idioma português.
3. **Tesseract.js** (último recurso): Processamento local com pré-processamento de imagem (grayscale + binarização).

### 3. Validação
- Compara soma dos bolões lidos vs. total no comprovante
- Diferença ≤ 10% → aprovado automaticamente
- Diferença 10-25% → aviso, permite prosseguir
- Diferença > 25% → bloqueado, sugere nova foto
- Até 3 tentativas de foto; após 3, oferece correção manual

### 4. Cálculo de Cotas
- `cota = (vBolao + vTarifa) / qt`
- Agrupa por valor de cota para tabela final
- Exibe totais de cotas e valor total

### 5. Compartilhamento
- Botão "Compartilhar no WhatsApp" gera texto formatado com tabela de cotas

---

## Configurações (localStorage)
| Chave | Valor | Descrição |
|-------|-------|-----------|
| `gemini_key` | String | API key do Google AI Studio para Gemini Vision |

---

## Padrões e Regras

### Prompt do Gemini
O prompt pede JSON puro com `responseMimeType: "application/json"` e `temperature: 0`. Estrutura esperada:
```json
{
  "jogos": [{"modalidade":"MEGA","qt":3,"vBolao":30.00,"vTarifa":10.50}],
  "totalBolao": 594.00,
  "totalTarifa": 207.85
}
```

### Pré-processamento de Imagem (apenas Tesseract)
- Escala para mínimo 2000px no maior lado
- Limite máximo 3000px
- Grayscale + contraste 180% + brilho 115%
- Binarização com threshold 150

### Modalidades Reconhecidas
MEGA, QUINA, LOTOFÁCIL, LOTOMANIA, TIMEMANIA, DUPLA SENA, DIA DE SORTE

---

## Deploy
- Hospedado como site estático (GitHub Pages ou similar)
- Funciona offline após primeira visita (Service Worker)
- Sem servidor necessário

---

## Relação com Outros Projetos
- **INDEPENDENTE** do projeto PDV Gráfica (`pdv-grafica/`)
- Compartilham apenas o diretório pai (`Antigravity_Testes/`)
- Stacks diferentes, repositórios Git separados
