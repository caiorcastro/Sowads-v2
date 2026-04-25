# Sowads Orbit AI — Documento Mestre
> Consolidação de toda a memória do projeto, regras operacionais, histórico de decisões e instruções de sistema.
> Gerado em: 2026-04-23

---

## Índice

1. [O que é este projeto](#1-o-que-é-este-projeto)
2. [Provedor de IA — regra fixa](#2-provedor-de-ia--regra-fixa)
3. [Scripts — o que cada um faz](#3-scripts--o-que-cada-um-faz)
4. [Estrutura de arquivos e diretórios](#4-estrutura-de-arquivos-e-diretórios)
5. [Variáveis de ambiente (.env)](#5-variáveis-de-ambiente-env)
6. [Pipeline completo — passo a passo](#6-pipeline-completo--passo-a-passo)
7. [Sistema de Briefings](#7-sistema-de-briefings)
8. [Sistema de Imagens](#8-sistema-de-imagens)
9. [Formato dos CSVs](#9-formato-dos-csvs)
10. [Events CSV — backend Sowads](#10-events-csv--backend-sowads)
11. [Regras editoriais](#11-regras-editoriais)
12. [QA Score — thresholds e penalidades](#12-qa-score--thresholds-e-penalidades)
13. [Mapeamento de categorias](#13-mapeamento-de-categorias)
14. [Invariantes — nunca quebrar](#14-invariantes--nunca-quebrar)
15. [Verticais implementadas e planejadas](#15-verticais-implementadas-e-planejadas)
16. [Histórico de erros e lições aprendidas](#16-histórico-de-erros-e-lições-aprendidas)
17. [Regras de comportamento para o assistente de IA](#17-regras-de-comportamento-para-o-assistente-de-ia)
18. [Troubleshooting](#18-troubleshooting)
19. [Comandos úteis](#19-comandos-úteis)

---

## 1. O que é este projeto

**Sowads Orbit AI** é um motor de conteúdo SEO/AIO para escalar autoridade digital da Sowads Agência. Gera artigos HTML otimizados para WordPress em escala, copies sociais por rede (LinkedIn, Instagram, Facebook, TikTok), e exporta eventos para o backend Sowads com imagens da biblioteca WP já existente.

**Versão atual:** v3

### O que é a Sowads

Agência de marketing digital especializada em SEO, AIO e gestão estratégica de mídia paga. Meta Tech Provider.

Dois produtos internos, **completamente independentes entre si**:
- **Orbit AI** — conteúdo orgânico SEO/AIO (este projeto)
- **Automação Meta Ads** — tráfego pago

**Regra de compliance crítica:** nenhum artigo pode sugerir causalidade entre os dois produtos. Anúncios pagos não melhoram ranqueamento orgânico — nunca afirmar isso.

### Repositório

```
Local : /Users/caio.castro/Library/CloudStorage/GoogleDrive-.../VAIO/Python-Projetos/Sowads-v2-local/
GitHub: caiorcastro/Sowads-v2
```

---

## 2. Provedor de IA — regra fixa

**Sempre OpenRouter. Nunca Gemini direto. Nunca outra API sem aprovação explícita do Caio.**

```
Endpoint : https://openrouter.ai/api/v1/chat/completions
Modelo   : google/gemini-2.5-flash
Fallback : --fallback_model moonshotai/kimi-k2.6
Chave    : OPENROUTER_API_KEY no .env
Headers  : HTTP-Referer: https://sowads.com.br
           X-Title: Sowads Orbit AI Content Engine
```

**Por quê?** O Caio estabeleceu isso explicitamente: *"use o openrouter com o modelo que estamos usando nas gerações ao invés do gemini... não devemos mais usar o gemini diretamente."* Qualquer script que faz chamada de IA deve usar OpenRouter — incluindo o `orbit_social_agent.py` que antes usava `google.generativeai`.

---

## 3. Scripts — o que cada um faz

| Script | Input | Output | Observações |
|--------|-------|--------|-------------|
| `run_lotes.sh` | — | CSVs em `output_csv_batches_v2/` | **NÃO publica** — só gera |
| `orbit_content_engine.py` | CSV de temas | CSV de artigos com métricas | Motor principal: OpenRouter + briefings + QA + self-healing |
| `orbit_qa_validator.py` | HTML | score 0-100 + lista de issues | Usado internamente pelo engine |
| `orbit_media_indexer.py` | — | `relatorios/media_index.json` | Indexa biblioteca WP, matching por Jaccard + penalidade |
| `orbit_monitor.py` | log file | terminal em tempo real | ETA, scores, imagens por artigo |
| `orbit_publisher.py` | CSV de artigos | posts no WP | Sempre `--test_one` antes de `--all` |
| `orbit_social_agent.py` | CSVs de artigos | TXTs por rede + events CSV | Usa OpenRouter; aceita draft e published |
| `orbit_topic_creator.py` | tema livre | CSV de temas | Brainstorm de pautas |
| `orbit_optimizer.py / _v2 / _parallel` | CSV | CSV otimizado | Otimização AIO em lote |
| `bing_index_now.py` | URLs | push IndexNow | Indexação forçada Bing |
| `check_models*.py / get_models_list.py` | — | lista de modelos | Utilitários |

---

## 4. Estrutura de arquivos e diretórios

```
Sowads-v2-local/
├── CLAUDE.md                              ← Instruções para IA — leia antes de agir
├── README.md                              ← Documentação pública do projeto
├── SOWADS_ORBIT_MASTER.md                 ← Este arquivo
├── run_lotes.sh                           ← Pipeline: gera todos os lotes (nunca publica)
│
├── orbit_content_engine.py               ← Motor de artigos
├── orbit_qa_validator.py                 ← Score QA
├── orbit_media_indexer.py                ← Matching de imagens WP
├── orbit_monitor.py                      ← Monitor em tempo real
├── orbit_publisher.py                    ← Publicação WP via XML-RPC
├── orbit_social_agent.py                 ← Copies por rede + events CSV
├── orbit_topic_creator.py                ← Brainstorm de temas
├── orbit_optimizer.py / _v2 / _parallel  ← Otimização AIO em lote
├── bing_index_now.py                     ← Indexação forçada Bing
├── check_models*.py / get_models_list.py ← Utilitários
│
├── briefings/
│   ├── turismo.md                        ← Pesquisa: turismo 2026, OTAs, AI Overviews
│   └── auto.md                           ← Pesquisa: EVs Brasil, montadoras chinesas
│
├── regras_geracao/
│   └── schema_orbit_ai_v1.json           ← Brand, compliance, regras SEO/AIO
│
├── output_csv_batches_v2/                ← Artigos gerados (1 CSV por lote)
│   ├── lote_auto_temas.csv
│   ├── lote_turismo_temas.csv
│   ├── lote_auto_batch1_artigos_1_a_20.csv
│   └── lote_turismo_batch1_artigos_1_a_20.csv
│
├── output_social_copies/                 ← TXTs de copies por rede social
│   ├── linkedin/
│   ├── instagram/
│   └── facebook/
│
├── output_sowads_events/                 ← CSVs de eventos para o backend Sowads
│   └── orbitai_events_{org}_{ts}.csv
│
└── relatorios/                           ← Relatórios Markdown + media_index.json
    ├── media_index.json
    └── report_social_*.md
```

---

## 5. Variáveis de ambiente (.env)

O `.env` **nunca é commitado** (está no `.gitignore`). Deve conter:

```env
# IA — sempre OpenRouter
OPENROUTER_API_KEY=sk-or-v1-...

# WordPress
WORDPRESS_URL=https://sowads.com.br
WORDPRESS_USER=caio
WORDPRESS_PASSWORD=...       # app password do WP, não a senha real

# Bing
BING_INDEXNOW_KEY=

# Backend Sowads / contas sociais
# Substituir pelos IDs reais antes de produção
SOWADS_ORG_ID=0-DUMMY-0
IG_ACCOUNT_ID=DUMMY-IG-00000000000
FB_PAGE_ID=DUMMY-FB-00000000000
LI_ACCOUNT_ID=DUMMY-LI-00000000000
TT_ACCOUNT_ID=DUMMY-TT-00000000000
```

---

## 6. Pipeline completo — passo a passo

```
Temas CSV
    │
    ▼
orbit_content_engine.py ──► output_csv_batches_v2/
    │  (artigos HTML + QA score + URLs de imagens)
    │
    ├──► orbit_social_agent.py ──► output_social_copies/{rede}/
    │         │                    output_sowads_events/*.csv  ◄── backend Sowads
    │         │
    ▼         ▼
orbit_publisher.py ──► WordPress (draft → revisão → publish)
    │
    ▼
bing_index_now.py ──► Bing IndexNow
```

### Passo 1 — Gerar artigos

```bash
./run_lotes.sh
# Ou um lote específico:
python3 orbit_content_engine.py \
  --model "google/gemini-2.5-flash" \
  --wp_url "https://sowads.com.br" \
  --wp_user "caio" \
  --wp_pass "..." \
  --csv_input "output_csv_batches_v2/lote_auto_temas.csv"
```

Salva CSVs em `output_csv_batches_v2/`. **Nunca publica automaticamente.**

### Passo 2 — Gerar copies sociais + events CSV

```bash
python3 orbit_social_agent.py --count 40
# Para artigo específico:
python3 orbit_social_agent.py --wp_post_id 32277
```

Aceita artigos em `draft` e `published`. Gera automaticamente:
- `output_social_copies/{rede}/{unique_id}__wp{id}__{rede}.txt`
- `output_sowads_events/orbitai_events_{org}_{ts}.csv`

### Passo 3 — Validar 1 artigo ANTES de publicar o lote

```bash
python3 orbit_publisher.py \
  --wp_url https://sowads.com.br \
  --wp_user caio \
  --wp_pass "..." \
  --input_dir output_csv_batches_v2 \
  --test_one
```

**Verificar manualmente no painel WP:**
1. Imagem destacada aparece?
2. Conteúdo sem código JSON-LD no final?
3. Word count razoável?
4. Sem asteriscos `**` no texto?

### Passo 4 — Publicar lote completo (só após validar)

```bash
python3 orbit_publisher.py \
  --wp_url https://sowads.com.br \
  --wp_user caio \
  --wp_pass "..." \
  --input_dir output_csv_batches_v2 \
  --all
```

O publisher seta a imagem destacada automaticamente. Terminal mostra `🖼️` (ok) ou `⚠️ sem imagem` (falhou).

### Passo 5 — Indexar no Bing (opcional)

```bash
python3 bing_index_now.py
```

### Monitorar progresso

```bash
python3 orbit_monitor.py --log relatorios/run_pipeline.log
```

---

## 7. Sistema de Briefings

Pasta `briefings/` contém arquivos `.md` com dados de pesquisa que vão além do corte da IA — números reais, tendências de mercado, players do setor, dados de 2026.

### Como funciona

O engine detecta automaticamente palavras-chave do tema do artigo e, se houver match com a linha de keywords do briefing, injeta os primeiros 800 chars do arquivo no prompt. **Zero código necessário** — só criar o arquivo.

### Formato obrigatório

```markdown
# Palavras-chave para detecção: palavra1, palavra2, palavra3

## Contexto de mercado
[dados reais, números, tendências 2026...]

## Dados relevantes
...
```

**A primeira linha é obrigatória e deve ter exatamente esse formato.**

### Briefings existentes

| Arquivo | Verticais cobertas | Palavras-chave principais |
|---------|-------------------|--------------------------|
| `turismo.md` | turismo, viagens, OTAs | turismo, viagem, hotel, destino, CVC, SGE |
| `auto.md` | automotivo, EVs | auto, carro, elétrico, montadora, EV, concessionária |

### Criar novo briefing

1. Pesquise o mercado (dados reais, players, números 2026)
2. Crie `briefings/<vertical>.md` com a linha de keywords
3. Pronto — zero código

---

## 8. Sistema de Imagens

Reutiliza imagens **já existentes** na biblioteca do WordPress (~850 itens, ~62 grupos). **Nunca gera imagens novas. Nunca sobe para a biblioteca WP.**

### Scoring de matching

| Critério | Peso |
|----------|------|
| Similaridade Jaccard (palavras do tema vs. nome do arquivo WP) | 80% |
| Completude do grupo (tem blog + linkedin + ig + fb?) | 20% |
| Penalidade por repetição (`use_count`) | desconto progressivo |

**Penalidade por repetição:**
- `use_count = 0` → multiplicador 1.0
- `use_count = 1` → multiplicador 0.5
- `use_count = 2` → multiplicador 0.25
- `use_count = 3+` → multiplicador 0.10

### Persistência

`relatorios/media_index.json` — guarda `use_count` e `assigned_to` entre runs. Regenerar com:

```bash
python3 orbit_media_indexer.py
```

### Padrão de nomes dos arquivos WP

`{Prefix}_{N}_{type}_{topic-slug}_{hash}.jpg`

| Tipo | Canal |
|------|-------|
| `wp` ou `blog` | Post do blog |
| `li` | LinkedIn |
| `ig` | Instagram |
| `fb` | Facebook |
| `tt` | TikTok |
| `meta` | Formato 4:5 Meta |

### Colunas de imagem no CSV de artigos

`img_blog`, `img_linkedin`, `img_instagram`, `img_facebook`, `img_tiktok` — contêm URLs completas da biblioteca WP.

---

## 9. Formato dos CSVs

### CSV de temas (input do content engine)

```csv
topic_pt,vertical,category
"AIO para Lançamentos Automotivos","automotivo","SEO & AIO"
"GEO e a Jornada do Test-Drive","automotivo","SEO & AIO"
"Mídia Paga e Autoridade Orgânica","automotivo","Mídia Paga"
```

| Coluna | Obrigatória | Descrição |
|--------|-------------|-----------|
| `topic_pt` | Sim | Tema do artigo em português |
| `vertical` | Não | Usado para matching de briefing e imagens |
| `category` | Sim | Categoria WP — deve estar no mapeamento de categorias |

### CSV de artigos (output do content engine)

Nome do arquivo: `{input_stem}_batch{n}_artigos_{start}_a_{end}.csv`

Exemplo: `lote_auto_batch1_artigos_1_a_20.csv`

| Coluna | Descrição |
|--------|-----------|
| `unique_import_id` | ID único do artigo (ex: `Orbit_1`) |
| `post_title` | Título completo |
| `post_content` | HTML completo (`<article lang="pt-BR">…</article>`) |
| `meta_title` | Meta title SEO (≤ 60 chars) |
| `meta_description` | Meta description (≤ 160 chars) |
| `original_theme` | Tema original do CSV de temas |
| `suggested_category` | Categoria preservada do CSV de temas |
| `qa_score` | Score QA 0-100 |
| `heal_retries` | Tentativas de self-healing usadas |
| `img_blog` | URL completa da imagem de blog |
| `img_linkedin` | URL completa da imagem LinkedIn |
| `img_instagram` | URL completa da imagem Instagram |
| `img_facebook` | URL completa da imagem Facebook |
| `img_tiktok` | URL completa da imagem TikTok |
| `wp_post_id` | ID do post WP após publicação |
| `published_at` | Timestamp da publicação |
| `post_status` | `draft` ou `published` |
| `post_date` | Data agendada ou de criação |
| `language` | `pt-BR` |

---

## 10. Events CSV — backend Sowads

Gerado automaticamente pelo `orbit_social_agent.py` após cada run.

### Localização

```
output_sowads_events/orbitai_events_{SOWADS_ORG_ID}_{unix_timestamp}.csv
```

### Colunas

| Coluna | Descrição | Exemplo |
|--------|-----------|---------|
| `org_id` | ID da org Sowads | `0-DUMMY-0` |
| `source_event_id` | ID único do evento | `orbitAI_Orbit_1_ig_a3f2b1c9` |
| `event_source` | Sempre `orbit_ai` | `orbit_ai` |
| `event_type` | Sempre `create_organic_post` | `create_organic_post` |
| `event_version` | Sempre `v1` | `v1` |
| `event_request_timestamp` | Unix timestamp | `1776964623` |
| `payload` | JSON completo do post | ver abaixo |
| `status` | Sempre `pending` | `pending` |

### Estrutura do payload (por rede)

**Instagram / Facebook (Meta):**
```json
{
  "social_network": "meta",
  "channel": "instagram",
  "account_id": "DUMMY-IG-00000000000",
  "platform_spec": {
    "meta": {
      "page_id": "DUMMY-FB-00000000000",
      "instagram_actor_id": "DUMMY-IG-00000000000"
    }
  },
  "content": {
    "format": "PHOTO",
    "primary_text": "hook\n\ncopy\n\ncta\n\n#hashtag1 #hashtag2",
    "link": "https://sowads.com.br/blog/...",
    "media": { "url": "[BIBLIOTECA]Orbit_1_ig_tema-do-artigo_abc123.jpg", "type": "IMAGE" }
  }
}
```

**LinkedIn:**
```json
{
  "social_network": "linkedin",
  "account_id": "DUMMY-LI-00000000000",
  "platform_spec": { "linkedin": { "organization_id": "DUMMY-LI-00000000000" } },
  "content": {
    "format": "IMAGE",
    "primary_text": "hook\n\ncopy\n\ncta\n\n#hashtag1",
    "link": "https://sowads.com.br/blog/...",
    "media": { "url": "[BIBLIOTECA]Orbit_1_li_tema-do-artigo_abc123.jpg", "type": "IMAGE" }
  }
}
```

**TikTok** — mesmo formato que LinkedIn mas sem `link`.

### Proporção

**1 artigo = 4 linhas** no events CSV (ig, fb, li, tt).

---

## 11. Regras editoriais

### Word count

- **Alvo no prompt:** 700–1.400 palavras
- **Realidade:** modelo tende a overshoot, chegando a 1.500–1.900 palavras
- **Estratégia de compressão:** converter parágrafos corridos em `<ul><li>` — nunca cortar frases
- **QA penaliza progressivamente** (ver seção 12)

### FAQ

- HTML puro com `<section class="faq-section" style="...">` + `<h2>` + `<h3>` + `<p>`
- **Sem JSON-LD, sem `<script>`** — stripped via código em `parse_response()` E proibido no prompt
- Mínimo 5 perguntas

### H1

- **Não incluído no conteúdo** — WordPress renderiza o título do post como H1 automaticamente
- QA penaliza presença de H1 no conteúdo (-10 pts)

### Asteriscos

- Modelo às vezes gera `**texto**` (markdown bold) dentro do HTML — comportamento indesejado
- **Solução via código** em `parse_response()`: `re.sub(r'\*\*(.+?)\*\*', r'\1', text, flags=re.DOTALL)`
- Aplicado em: `post_content`, `meta_title`, `meta_description`

### Estrutura HTML obrigatória

```html
<article lang="pt-BR">
  <!-- SEM <h1> — WordPress usa o título do post -->
  <h2>Seção principal</h2>
  <p>Parágrafo...</p>
  <ul><li>Item de lista</li></ul>
  <h3>Subseção</h3>

  <section class="faq-section" style="...">
    <h2>Perguntas Frequentes</h2>
    <h3>Pergunta 1?</h3>
    <p>Resposta...</p>
    <!-- mínimo 5 perguntas -->
  </section>
</article>
```

### Compliance — temas de Mídia Paga

Quando o artigo aborda temas de mídia paga/anúncios:
- Tratar canais orgânico e pago como **paralelos e independentes**
- **Nunca afirmar** que anúncios melhoram ranqueamento orgânico
- **Nunca afirmar** que SEO aumenta ROAS ou performance de anúncios

### Proibido no conteúdo

- Hyperlinks (`<a href>`)
- Imagens (`<img>`, `<figure>`)
- URLs externas
- JSON-LD (`<script type="application/ld+json">`)
- Qualquer `<script>` tag

---

## 12. QA Score — thresholds e penalidades

| Verificação | Penalidade |
|-------------|-----------|
| FAQ ausente (`faq-section`) | -20 |
| H2/H3 hierárquicos ausentes | -10 |
| H1 presente no conteúdo | -10 |
| Tabelas ou listas ausentes | -5 |
| Referências numéricas ausentes | -5 |
| Word count < 700 | -15 |
| Word count > 1.500 | -5 |
| Word count > 1.800 | -12 |
| Word count > 2.000 | **-25 → dispara self-heal** |

**Self-healing:** até 2 tentativas com prompt de correção focado nos issues detectados. Se score ≥ 80 após retry, publica normalmente. Se não atingir 80 após 2 tentativas, o artigo é marcado como falha no CSV.

**Mínimo para publicação:** 80/100.

---

## 13. Mapeamento de categorias

A categoria **sempre vem do CSV de temas** (coluna `category`). O publisher converte para o nome real no WordPress:

```python
CATEGORY_CSV_TO_WP = {
    "SEO & AIO":               "SEO e AI-SEO",
    "Conteúdo":                "Conteúdo em Escala",
    "Estratégia e Performance": "Estratégia e Performance",
    "Mídia Paga":              "Mídia Paga",
    "Data e Analytics":        "Dados e Analytics",
}
```

**Nunca inferir categoria por keyword.** Isso causou um incidente onde 40 artigos foram publicados todos como "Mídia Paga" — foi necessário corrigir via XML-RPC um por um.

---

## 14. Invariantes — nunca quebrar

| # | Regra | Garantida por |
|---|-------|---------------|
| 1 | **OpenRouter sempre** — nunca Gemini direto | `.env` + código |
| 2 | **Compliance Orbit AI ↔ Meta Ads** — zero causalidade | prompt + revisão manual |
| 3 | **Zero hyperlinks, `<img>`, `<figure>` ou JSON-LD** no conteúdo | `parse_response()` strip |
| 4 | **FAQ HTML puro** — `faq-section`, sem `<script>` | prompt + `parse_response()` |
| 5 | **Sem H1 no conteúdo** — WP usa o título como H1 | `parse_response()` strip |
| 6 | **Score QA ≥ 80/100** | self-healing automático |
| 7 | **Publicação manual** — `--test_one` antes de `--all` | processo humano |
| 8 | **Imagens da biblioteca WP** — nunca gerar, nunca subir nova | `orbit_media_indexer.py` |
| 9 | **Sem `**asteriscos**`** no conteúdo | `parse_response()` strip |
| 10 | **Categorias do CSV de temas** — nunca inferir | `CATEGORY_CSV_TO_WP` |
| 11 | **CSVs nomeados com stem do input** — nunca sobrescrever | convenção de nomeação |

---

## 15. Verticais implementadas e planejadas

### Implementadas

| Vertical | CSV de temas | Briefing |
|----------|-------------|---------|
| Automotivo | `lote_auto_temas.csv` | `briefings/auto.md` |
| Turismo | `lote_turismo_temas.csv` | `briefings/turismo.md` |

### Artigos publicados até agora

- **Lote auto** (IDs 32277–32315): 20 artigos, QA médio 95/100, word count ~1.550
- **Lote turismo** (IDs 32317–32355): 20 artigos, QA médio 94/100, word count ~1.730
- Status atual no WP: **draft** (aguardando revisão manual do Caio)

### Próximas verticais sugeridas (prospects Sowads)

| Vertical | Observações |
|----------|-------------|
| Saúde / clínicas | Alta demanda de SEO local, E-E-A-T crítico |
| Imóveis / construtoras | Long-tail geográfico forte |
| Educação / cursos | AI Overviews frequente no setor |
| Financeiro / fintechs | Compliance rigoroso necessário |
| Varejo / e-commerce | Ranqueamento de produtos, GEO |
| Advocacia / jurídico | E-E-A-T altíssimo, regulado |
| Franquias | Multi-unidade, SEO local |
| Agro | Nicho com baixa competição digital |

### Como adicionar nova vertical

1. Pesquise o mercado → crie `briefings/<vertical>.md` com linha de keywords
2. Crie `output_csv_batches_v2/lote_<vertical>_temas.csv` com colunas `topic_pt, vertical, category`
3. Adicione lote no `run_lotes.sh` seguindo o padrão existente
4. **Zero mudança de código necessária**

---

## 16. Histórico de erros e lições aprendidas

Esta seção documenta incidentes reais desta sessão de trabalho para não repetir.

### 1. CSV sobrescrito — artigos perdidos

**O que aconteceu:** Ambos os lotes (auto e turismo) geravam `lote_1_artigos_1_a_20.csv`. O lote turismo sobrescreveu o lote auto — 20 artigos perdidos.

**Causa:** O nome do arquivo de saída não incluía o stem do arquivo de input.

**Solução:** Nomeação agora usa `{input_stem}_batch{n}_artigos_{start}_a_{end}.csv`. Ex: `lote_auto_batch1_artigos_1_a_20.csv`.

**Lição:** Nunca sobrescrever CSVs existentes. O nome do arquivo de saída deve sempre incluir a identidade do lote de entrada.

---

### 2. Publicação automática — artigos ruins no ar

**O que aconteceu:** `run_lotes.sh` rodava `orbit_publisher.py --all` no final. Publicou artigos sem imagem destacada, com JSON-LD visível no conteúdo, com 2.596 palavras e compliance violado.

**Causa:** Publicação automática sem validação manual.

**Solução:** Removida completamente do `run_lotes.sh`. Publicação é sempre manual com `--test_one` primeiro.

**Lição:** *"antes de sair publicando lotes, teste, verifique, valide e depois poste."*

---

### 3. JSON-LD aparecendo no conteúdo mesmo com instrução no prompt

**O que aconteceu:** Artigos publicados tinham `<script type="application/ld+json">` visível no final do conteúdo. O prompt dizia para não incluir JSON-LD — modelo ignorou.

**Causa:** Instrução no prompt não é suficiente para comportamentos estruturais.

**Solução:** Strip via código em `parse_response()`:
```python
post_content = re.sub(r'<script\b[^>]*>[\s\S]*?</script>', '', post_content)
```

**Lição:** Invariantes críticos devem ser garantidos via código além do prompt.

---

### 4. Imagens sem featured image no WordPress

**O que aconteceu:** Posts foram publicados sem imagem destacada. O monitor mostrava 0 matches de imagem.

**Causa:** `orbit_publisher.py` não tinha código para setar a imagem destacada — apenas incluía a URL no conteúdo.

**Solução:** Adicionado `get_media_id_by_url()` (busca o attachment ID via REST API pelo nome do arquivo) + `set_featured_image()` (XML-RPC `wp.editPost` com `post_thumbnail`).

---

### 5. Todas as categorias publicadas como "Mídia Paga"

**O que aconteceu:** 40 artigos publicados, todos com categoria "Mídia Paga" — mas a maioria era SEO/AIO.

**Causa:** `orbit_publisher.py` usava detecção por keyword para inferir categoria. Artigos de SEO/AIO mencionavam "tráfego" e "anúncios" no contexto, sendo classificados erroneamente.

**Solução:**
1. `orbit_content_engine.py` agora preserva a coluna `category` do CSV de temas até a saída como `suggested_category`
2. `orbit_publisher.py` usa `CATEGORY_CSV_TO_WP` dict para mapear — nunca infere por keyword
3. Todos os 40 posts foram corrigidos via XML-RPC `wp.editPost` cross-referenciando CSV original com `wp_post_id`

---

### 6. Asteriscos `**texto**` no conteúdo publicado

**O que aconteceu:** 6 artigos publicados tinham `**texto em negrito**` (markdown) em vez de `<strong>texto</strong>` (HTML).

**Causa:** Modelo gerava markdown bold dentro do HTML — comportamento de contaminação de formato.

**Solução:** Strip via código em `parse_response()`:
```python
post_content = re.sub(r'\*\*(.+?)\*\*', r'\1', post_content, flags=re.DOTALL)
meta_title = re.sub(r'\*\*(.+?)\*\*', r'\1', meta_title)
meta_desc = re.sub(r'\*\*(.+?)\*\*', r'\1', meta_desc)
```

Os 6 posts foram corrigidos via XML-RPC sem regenerar nenhum artigo.

**IDs afetados:** 32307, 32319, 32321, 32327, 32343, 32345

---

### 7. Social agent usando Gemini direto em vez de OpenRouter

**O que aconteceu:** `orbit_social_agent.py` usava `google.generativeai` com `GEMINI_API_KEY`. O Caio pediu para usar OpenRouter.

**Solução:** Script migrado para OpenRouter — mesma API, mesmo modelo `google/gemini-2.5-flash`, sem `google.generativeai`.

---

### 8. Status real no WP diferente do CSV

**O que aconteceu:** CSVs tinham coluna `post_status: published`, mas no WP os posts estavam como `draft`. Claude reportou status errado.

**Causa:** CSV reflete o momento da geração/publicação, não o estado atual do WP.

**Solução:** Sempre verificar status real via `server.wp.getPosts()` antes de reportar ou agir.

**Lição:** *"porra mano nao..... os ultimos 40 que estao bons estao como rascunho..... nao tao como publicados, puta merda."* — nunca assumir estado do WP com base no CSV.

---

### 9. 41 rascunhos de lixo + 50 rascunhos antigos no WP

**O que aconteceu:** Após múltiplas tentativas de geração/publicação com bugs, o WP acumulou 91 posts em rascunho desnecessários além dos 40 bons.

**Solução:** Auditoria via XML-RPC identificou 3 grupos:
- **41 rascunhos de lixo** (IDs 32195–32275) → deletados
- **50 rascunhos antigos** (IDs ≤ 32163) → deletados a pedido do Caio
- **40 bons** (IDs 32277–32355) → mantidos como draft para revisão

**Lição:** Sempre auditar o WP antes de qualquer limpeza. Nunca deletar sem confirmação explícita do Caio.

---

## 17. Regras de comportamento para o assistente de IA

Estas regras foram estabelecidas explicitamente pelo Caio ao longo das sessões.

### Antes de agir

- **Ler os arquivos reais** — nunca inventar estado do projeto
- **`git status`** antes de qualquer edição de pipeline
- **Verificar WP via XML-RPC** quando o estado real dos posts importa — nunca confiar nos CSVs
- **Report primeiro** quando o Caio pede auditoria — nunca executar e reportar ao mesmo tempo

### Durante a execução

- **Nunca sobrescrever CSVs** sem confirmação
- **Nunca publicar automaticamente** mesmo que o Caio peça "publique tudo" — sempre `--test_one` primeiro com confirmação explícita
- **Invariantes via código**, não só via prompt — strip de JSON-LD, H1, asteriscos, hyperlinks
- **Categorias do CSV** — nunca inferir por keyword

### Ao corrigir posts já publicados

- Usar XML-RPC `wp.editPost` com regex — nunca regenerar o artigo
- Atualizar o CSV local após a correção

### Ao final de cada sessão de mudanças

- Atualizar `CLAUDE.md`
- Atualizar `README.md`
- Atualizar a memória do projeto (`project_sowads_orbit.md` + `feedback_orbit_pipeline.md`)
- Commit + push
- **Fazer isso proativamente**, sem precisar ser solicitado

### Sobre o Caio

- Founder / responsável técnico e estratégico do projeto
- Estilo de trabalho: direto, cobra resultados, não tolera erros repetidos
- Prefere report → confirmação → execução, especialmente em ações destrutivas

---

## 18. Troubleshooting

| Problema | Causa provável | Solução |
|----------|---------------|---------|
| JSON-LD aparece no artigo | `parse_response()` sem strip | Verificar `re.sub(r'<script\b...')` em `parse_response()` |
| `**asteriscos**` no conteúdo | `parse_response()` sem strip | Verificar `re.sub(r'\*\*...')` em `parse_response()` |
| Imagem não aparece no WP | `get_media_id_by_url` falhou | Verificar nome do arquivo na biblioteca WP via painel |
| CSV sobrescrito entre lotes | Nome sem stem do input | Verificar nomeação: `{input_stem}_batch{n}_artigos_{a}_a_{b}.csv` |
| Categoria errada no WP | Inferência por keyword ativa | Verificar `CATEGORY_CSV_TO_WP` no publisher e coluna `suggested_category` no CSV |
| Events CSV vazio | `_payload` não salvo | Verificar `article["_payload"] = payload` no loop do social agent |
| Social agent falha com JSON | Model retornou texto extra | Retry automático — rodar `--wp_post_id` para o artigo específico |
| Posts com status errado no WP | CSV desatualizado | Sempre verificar via `server.wp.getPosts()` |
| Word count muito alto | Model ignora prompt | QA penaliza >2.000 (self-heal) — verificar thresholds em `orbit_qa_validator.py` |
| FAQ regex não detecta | Model adiciona `style="..."` | Regex deve ser `r'<section[^>]+class=["\']faq-section["\']'` (não literal) |

---

## 19. Comandos úteis

### Desenvolvimento

```bash
# Listar modelos disponíveis no OpenRouter
python3 get_models_list.py

# Regenerar index de imagens da biblioteca WP
python3 orbit_media_indexer.py

# Ver log de geração em tempo real
python3 orbit_monitor.py --log relatorios/run_pipeline.log
```

### Correção de posts publicados (sem regenerar)

```bash
# Remover asteriscos de posts específicos
python3 - <<'EOF'
import xmlrpc.client, re, csv
server = xmlrpc.client.ServerProxy("https://sowads.com.br/xmlrpc.php")
user, pw = "caio", "SENHA_APP"
post_ids = [32307, 32319]  # substituir pelos IDs

for pid in post_ids:
    post = server.wp.getPost(1, user, pw, pid, ["post_content", "post_title"])
    content = re.sub(r'\*\*(.+?)\*\*', r'\1', post["post_content"], flags=re.DOTALL)
    server.wp.editPost(1, user, pw, pid, {"post_content": content})
    print(f"✅ {pid} corrigido")
EOF

# Mover posts para rascunho (sem deletar)
python3 - <<'EOF'
import xmlrpc.client
server = xmlrpc.client.ServerProxy("https://sowads.com.br/xmlrpc.php")
user, pw = "caio", "SENHA_APP"
for pid in [32195, 32197, 32199]:  # lista de IDs
    server.wp.editPost(1, user, pw, pid, {"post_status": "draft"})
    print(f"  draft: {pid}")
EOF

# Listar todos os rascunhos no WP com status atual
python3 - <<'EOF'
import xmlrpc.client
server = xmlrpc.client.ServerProxy("https://sowads.com.br/xmlrpc.php")
drafts = server.wp.getPosts(1, "caio", "SENHA_APP", {
    "post_status": "draft", "number": 200,
    "orderby": "ID", "order": "DESC",
    "fields": ["post_id", "post_title", "post_date"]
})
print(f"Total rascunhos: {len(drafts)}")
for p in drafts:
    print(f"  ID {p['post_id']} | {p['post_date']} | {p['post_title'][:60]}")
EOF
```

### Git

```bash
# Ver histórico de commits
git log --oneline -10

# Status atual
git status

# Push após alterações
git add -A && git commit -m "descrição" && git push
```
