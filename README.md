# 🚀 D4U Unified Content Engine (AI-Powered)

> **A Revolução na Escala de Conteúdo Global da D4U Immigration.**

Este projeto não é apenas um script; é uma **infraestrutura completa de Engenharia de Prompt e Automação** projetada para dominar a produção de conteúdo multilíngue com precisão cirúrgica.

## 🌟 O Que Este Projeto Faz?
Transformamos o processo manual e lento de redação em uma **linha de montagem inteligente** capaz de gerar centenas de artigos técnicos, persuasivos e 100% compliant em minutos.

### 🔥 Principais Diferenciais:
*   **Compliance Jurídico Automático:** O sistema integra regras rígidas (ex: "taxa de sucesso >91%", "não somos assessoria jurídica") diretamente no "DNA" de cada artigo. Risco de erro humano: **ZERO**.
*   **Localização Nativa (Latam-First):** Não é tradução, é **adaptação cultural**. O motor entende que "fisioterapeutas no Brasil" viram "batalhadores latinos" e ajusta contextos, moedas e dores para o público ES-419 (Espanhol Latino-Americano).
*   **Escalabilidade Infinita:** De 1 a 1.000 artigos. O sistema opera em lotes inteligentes (Batch Processing), gerando arquivos CSV prontos para importação direta no WordPress.
*   **SEO Técnico Embutido:** Cada artigo já nasce com Meta Titles otimizados, Meta Descriptions persuasivas e estrutura HTML semântica (`<article>`, `<h2>`, JSON-LD FAQ Schema).

---

## 🛠️ Arquitetura Técnica
Construído sobre a API **Google Gemini Pro/Flash**, o motor utiliza uma arquitetura de *Chain-of-Density* para maximizar a riqueza do conteúdo sem alucinações.

### Estrutura de Pastas
*   📂 `regras_geracao/`: O "Cérebro" do sistema. Contém o JSON Schema com todas as diretrizes de marca, tom de voz e regras legais.
*   📂 `modelos/`: Inteligência de seleção de modelos de IA.
*   📂 `d4u_content_engine.py`: O coração da automação. Script CLI robusto com retry-logic, fallback de modelos e formatação de saída.
*   📂 `output_csv_batches/`: A "Esteira de Saída". Onde os lotes de conteúdo prontos são depositados.

---

## 🚀 Como Usar
Para gerar novos lotes de conteúdo com o **Gemini 2.5 Flash** (rápido e preciso):

```bash
# Exemplo: Gerar do lote 2 em diante
python3 d4u_content_engine.py --api_key "SUA_CHAVE_AQUI" --model "gemini-2.5-flash" --start_batch 2
```

## 📊 Impacto de Negócio
*   **Tempo de Produção:** Reduzido de dias para segundos.
*   **Consistência da Marca:** Garantida em 100% dos assets.
*   **Custo:** Fração irrelevante comparado a agências de conteúdo tradicionais.

---
*Desenvolvido para D4U Immigration - Expansão Global.*
