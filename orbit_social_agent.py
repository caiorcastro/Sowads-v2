import os
import re
import json
import glob
import csv
import argparse
from datetime import datetime

import pandas as pd
import requests
import google.generativeai as genai


CSV_DIR = "output_csv_batches_v2"
OUTPUT_DIR = "output_social_copies"
REPORTS_DIR = "relatorios"
CTA_HISTORY_FILE = os.path.join(OUTPUT_DIR, "_cta_history.json")
DEFAULT_WP_URL = "https://sowads.com.br"
MODEL_NAME = "gemini-2.5-flash"
ENV_FILE = ".env"

NETWORKS = {
    "linkedin": {
        "label": "LinkedIn",
        "tone": "consultivo, analitico, B2B, com autoridade e clareza",
        "audience": "gestores, liderancas, decisores e profissionais de marketing",
        "length": "700 a 1300 caracteres",
        "hashtags": "3 a 5 hashtags",
    },
    "instagram": {
        "label": "Instagram",
        "tone": "direto, leve, escaneavel, visual e energico — linhas curtas, bullets com emojis, muito espaco em branco",
        "audience": "profissionais e empresas consumindo conteudo rapido e visual",
        "length": "400 a 900 caracteres",
        "hashtags": "5 a 8 hashtags",
    },
    "facebook": {
        "label": "Facebook",
        "tone": "conversacional, acessivel, simples e informativo — pode usar alguns bullets com emojis para escaneabilidade",
        "audience": "publico amplo, comunidades e donos de negocio",
        "length": "300 a 700 caracteres",
        "hashtags": "2 a 4 hashtags",
    },
}


class Colors:
    HEADER = "\033[95m"
    OKBLUE = "\033[94m"
    OKCYAN = "\033[96m"
    OKGREEN = "\033[92m"
    WARNING = "\033[93m"
    FAIL = "\033[91m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"


def log(color, label, message):
    print(f"{color}{Colors.BOLD}[{label}]{Colors.ENDC} {message}")


def load_env_file(path=ENV_FILE):
    if not os.path.exists(path):
        return
    try:
        with open(path, "r", encoding="utf-8") as handle:
            for raw_line in handle:
                line = raw_line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, value = line.split("=", 1)
                key = key.strip()
                value = value.strip().strip('"').strip("'")
                if key and key not in os.environ:
                    os.environ[key] = value
    except Exception:
        return


def load_api_key(cli_key=None):
    load_env_file()
    api_key = cli_key or os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("Forneca --api_key ou defina GEMINI_API_KEY.")
    return api_key


def slugify(text, max_len=60):
    text = str(text).lower()
    for src, dst in [
        ("áàãâä", "a"),
        ("éèêë", "e"),
        ("íìîï", "i"),
        ("óòõôö", "o"),
        ("úùûü", "u"),
        ("ç", "c"),
    ]:
        for ch in src:
            text = text.replace(ch, dst)
    text = re.sub(r"[^a-z0-9\s-]", "", text)
    text = re.sub(r"[\s_]+", "-", text).strip("-")
    return text[:max_len]


def normalize_wp_post_id(value):
    if pd.isna(value):
        return ""
    text = str(value).strip()
    if re.fullmatch(r"\d+\.0+", text):
        return text.split(".", 1)[0]
    return text


def strip_html(html):
    text = re.sub(r"<script[\s\S]*?</script>", " ", str(html), flags=re.IGNORECASE)
    text = re.sub(r"<style[\s\S]*?</style>", " ", text, flags=re.IGNORECASE)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def summarize_text(text, max_chars=1400):
    clean = re.sub(r"\s+", " ", str(text)).strip()
    if len(clean) <= max_chars:
        return clean
    cutoff = clean[:max_chars]
    last_period = max(cutoff.rfind(". "), cutoff.rfind("! "), cutoff.rfind("? "))
    if last_period > 300:
        return cutoff[: last_period + 1].strip()
    return cutoff.strip() + "..."


def ensure_dirs():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs(REPORTS_DIR, exist_ok=True)
    for network in NETWORKS:
        os.makedirs(os.path.join(OUTPUT_DIR, network), exist_ok=True)


def load_published_articles(csv_dir):
    files = sorted(glob.glob(os.path.join(csv_dir, "*.csv")))
    if not files:
        raise FileNotFoundError(f"Nenhum CSV encontrado em {csv_dir}/")

    articles = []
    for file_path in files:
        try:
            df = pd.read_csv(file_path)
        except Exception as exc:
            log(Colors.WARNING, "CSV", f"Falha lendo {file_path}: {exc}")
            continue

        for idx, row in df.iterrows():
            status = str(row.get("post_status", "")).strip().lower()
            wp_post_id = normalize_wp_post_id(row.get("wp_post_id"))
            content = str(row.get("post_content", ""))
            if status != "published":
                continue
            if not wp_post_id:
                continue
            if len(content) < 100 or "ERRO" in content:
                continue

            published_at = str(row.get("published_at", "")).strip()
            sort_value = published_at or str(row.get("post_date", "")).strip()
            articles.append(
                {
                    "file": file_path,
                    "file_idx": idx,
                    "unique_import_id": str(row.get("unique_import_id", "")).strip() or f"row_{idx}",
                    "wp_post_id": wp_post_id,
                    "post_title": str(row.get("post_title", "")).strip(),
                    "meta_title": str(row.get("meta_title", "")).strip(),
                    "meta_description": str(row.get("meta_description", "")).strip(),
                    "post_content": content,
                    "suggested_category": str(row.get("suggested_category", "")).strip(),
                    "qa_score": str(row.get("qa_score", "")).strip(),
                    "published_at": published_at,
                    "sort_value": sort_value,
                }
            )

    articles.sort(key=lambda item: item["sort_value"])
    return articles


def fetch_post_url(wp_url, wp_post_id):
    try:
        response = requests.get(
            f"{wp_url.rstrip('/')}/wp-json/wp/v2/posts/{wp_post_id}",
            timeout=15,
        )
        if response.status_code == 200:
            data = response.json()
            link = data.get("link", "")
            if link:
                return link
    except Exception:
        pass
    return f"{wp_url.rstrip('/')}/?p={wp_post_id}"


def load_cta_history():
    if not os.path.exists(CTA_HISTORY_FILE):
        return {network: [] for network in NETWORKS}
    try:
        with open(CTA_HISTORY_FILE, "r", encoding="utf-8") as handle:
            data = json.load(handle)
        for network in NETWORKS:
            data.setdefault(network, [])
        return data
    except Exception:
        return {network: [] for network in NETWORKS}


def save_cta_history(history):
    with open(CTA_HISTORY_FILE, "w", encoding="utf-8") as handle:
        json.dump(history, handle, ensure_ascii=False, indent=2)


def get_recent_ctas(history, network, limit=8):
    values = history.get(network, [])
    return values[-limit:]


def is_obviously_repeated(candidate, recent_values):
    normalized = normalize_phrase(candidate)
    if not normalized:
        return True
    for recent in recent_values:
        other = normalize_phrase(recent)
        if normalized == other:
            return True
        if normalized in other or other in normalized:
            return True
    return False


def normalize_phrase(text):
    text = str(text).lower()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def build_prompt(article, recent_ctas):
    article_title = article["post_title"]
    category = article["suggested_category"] or "Sem categoria"
    description = article["meta_description"] or ""
    excerpt = summarize_text(strip_html(article["post_content"]), max_chars=1800)

    network_briefs = []
    for network, config in NETWORKS.items():
        blocked = recent_ctas.get(network, [])
        blocked_text = "\n".join(f"- {item}" for item in blocked) if blocked else "- nenhum ainda"
        network_briefs.append(
            f"""
REDE: {network}
- Rotulo: {config['label']}
- Tom: {config['tone']}
- Publico: {config['audience']}
- Tamanho alvo: {config['length']}
- Hashtags: {config['hashtags']}
- CTAs bloqueados por repeticao recente:
{blocked_text}
"""
        )

    return f"""
ROLE: Social Media Copywriter senior da Sowads.
TASK: Criar copies derivados de UM artigo de blog ja publicado.

ARTIGO:
- Titulo: {article_title}
- Categoria: {category}
- Meta description: {description}
- URL: {article['url']}
- QA score: {article['qa_score']}
- Resumo base:
{excerpt}

REGRAS GERAIS:
- Responder em pt-BR.
- Nao inventar fatos nao presentes no resumo.
- Cada rede deve ter linguagem propria, sem parecer o mesmo texto reciclado.
- Usar emojis de forma estrategica: no hook para chamar atencao, nos bullets para escaneabilidade, e no CTA para energia. Nao exagerar — maximo 1-2 emojis por linha.
- O campo "copy" do Instagram e Facebook DEVE ter estrutura visual: linhas curtas, bullets com emojis (ex: ✅ ✨ 💡 📊 🎯 👉), espacos em branco entre blocos, muito escaneavel. Seguir o padrao: abertura de impacto, lista de beneficios/pontos, fechamento com CTA.
- O campo "copy" do LinkedIn pode ter paragrafos mais longos mas ainda usar emojis pontuais no inicio de blocos importantes.
- CTA de cada rede deve soar natural e sem repeticao obvia.
- Nao usar CTAs genericos repetitivos como "Leia o artigo completo" para todas as redes.
- Hashtags devem vir como lista de strings sem # duplicado no texto principal.

BRIEFS POR REDE:
{''.join(network_briefs)}

FORMATO DE SAIDA: JSON puro com este schema:
{{
  "linkedin": {{
    "hook": "...",
    "copy": "...",
    "cta": "...",
    "hashtags": ["#tag1", "#tag2"]
  }},
  "instagram": {{
    "hook": "...",
    "copy": "...",
    "cta": "...",
    "hashtags": ["#tag1", "#tag2"]
  }},
  "facebook": {{
    "hook": "...",
    "copy": "...",
    "cta": "...",
    "hashtags": ["#tag1", "#tag2"]
  }}
}}
"""


def generate_social_payload(model, article, recent_ctas, max_retries=5):
    import time
    prompt = build_prompt(article, recent_ctas)
    for attempt in range(max_retries):
        try:
            response = model.generate_content(
                prompt,
                generation_config={"response_mime_type": "application/json"},
            )
            payload = json.loads(response.text)
            return payload
        except Exception as exc:
            msg = str(exc)
            if "429" in msg or "quota" in msg.lower() or "rate" in msg.lower():
                wait = 30 * (attempt + 1)
                log(Colors.WARNING, "RATE-LIMIT", f"Tentativa {attempt+1}/{max_retries} — aguardando {wait}s...")
                time.sleep(wait)
            else:
                raise
    raise RuntimeError(f"Falhou apos {max_retries} tentativas por rate limit.")


def validate_model_access(model):
    model.generate_content("Responda apenas com OK.")


def validate_payload(payload, recent_ctas):
    for network in NETWORKS:
        if network not in payload:
            raise ValueError(f"Rede ausente no payload: {network}")

        item = payload[network]
        for field in ("hook", "copy", "cta", "hashtags"):
            if field not in item:
                raise ValueError(f"Campo ausente em {network}: {field}")

        if len(str(item["copy"]).strip()) < 120:
            raise ValueError(f"Copy muito curta para {network}")

        if is_obviously_repeated(item["cta"], recent_ctas.get(network, [])):
            raise ValueError(f"CTA repetido ou muito parecido em {network}: {item['cta']}")

        hashtags = item["hashtags"]
        if not isinstance(hashtags, list) or not hashtags:
            raise ValueError(f"Hashtags invalidas em {network}")


def build_txt_content(article, network, item, filename):
    hashtags_text = " ".join(item["hashtags"])
    unique_id = f"{article['unique_import_id']}__wp{article['wp_post_id']}"
    return (
        f"ID_UNICO: {unique_id}\n"
        f"ARQUIVO: {filename}\n"
        f"REDE: {network}\n"
        f"POST_ID_WORDPRESS: {article['wp_post_id']}\n"
        f"TITULO_ARTIGO: {article['post_title']}\n"
        f"URL: {article['url']}\n"
        f"CATEGORIA: {article['suggested_category'] or 'Sem categoria'}\n\n"
        f"HOOK:\n{item['hook'].strip()}\n\n"
        f"COPY:\n{item['copy'].strip()}\n\n"
        f"CTA:\n{item['cta'].strip()}\n\n"
        f"HASHTAGS:\n{hashtags_text}\n"
    )


def save_network_files(article, payload):
    saved = []
    unique_id = f"{article['unique_import_id']}__wp{article['wp_post_id']}"
    for network in NETWORKS:
        filename = f"{unique_id}__{network}.txt"
        dest_path = os.path.join(OUTPUT_DIR, network, filename)
        content = build_txt_content(article, network, payload[network], filename)
        with open(dest_path, "w", encoding="utf-8") as handle:
            handle.write(content)
        saved.append({"network": network, "path": dest_path, "filename": filename})
    return saved


def update_csv_status(article):
    try:
        df = pd.read_csv(article["file"])
        df.loc[article["file_idx"], "social_copy_status"] = "generated"
        df.loc[article["file_idx"], "social_copy_generated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        df.to_csv(article["file"], index=False, quoting=csv.QUOTE_ALL)
    except Exception as exc:
        log(Colors.WARNING, "CSV", f"Falha ao atualizar status social em {article['file']}: {exc}")


def generate_report(results, timestamp):
    os.makedirs(REPORTS_DIR, exist_ok=True)
    path = os.path.join(REPORTS_DIR, f"report_social_{timestamp}.md")
    lines = [
        "# Relatorio de Social Copies",
        "",
        f"**Data:** {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        f"**Total de artigos:** {len(results)}",
        "",
        "| # | ID | Titulo | Redes | Status |",
        "|---|---|---|---|---|",
    ]
    for index, result in enumerate(results, start=1):
        status = "OK" if result["success"] else "ERRO"
        lines.append(
            f"| {index} | {result['unique_id']} | {result['title'][:60]} | "
            f"{', '.join(result.get('networks', [])) or '-'} | {status} |"
        )
        if not result["success"]:
            lines.append(f"|  |  | Erro: {result['error'][:120]} |  |  |")

    with open(path, "w", encoding="utf-8") as handle:
        handle.write("\n".join(lines))
    return path


def select_articles(articles, count=5, article_id=None, wp_post_id=None):
    selected = articles
    if article_id:
        selected = [item for item in selected if item["unique_import_id"] == article_id]
    if wp_post_id:
        selected = [item for item in selected if item["wp_post_id"] == str(wp_post_id)]
    if not article_id and not wp_post_id:
        selected = selected[-count:]
    return selected


def run(api_key, wp_url=DEFAULT_WP_URL, count=5, article_id=None, wp_post_id=None, dry_run=False, delay=4):
    ensure_dirs()
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(MODEL_NAME)
    if not article_id and not wp_post_id:
        validate_model_access(model)

    articles = load_published_articles(CSV_DIR)
    selected = select_articles(articles, count=count, article_id=article_id, wp_post_id=wp_post_id)
    if not selected:
        raise ValueError("Nenhum artigo publicado encontrado para processar.")

    for article in selected:
        article["url"] = fetch_post_url(wp_url, article["wp_post_id"])

    log(Colors.HEADER, "SOCIAL", f"Gerando copies para {len(selected)} artigo(s).")
    for article in selected:
        log(
            Colors.OKCYAN,
            "POST",
            f"[{article['unique_import_id']}] wp={article['wp_post_id']} | {article['post_title']}",
        )

    if dry_run:
        log(Colors.WARNING, "DRY-RUN", "Nenhuma chamada ao modelo sera feita.")
        return

    history = load_cta_history()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    results = []

    for idx, article in enumerate(selected):
        if idx > 0 and delay > 0:
            import time
            time.sleep(delay)
        unique_id = f"{article['unique_import_id']}__wp{article['wp_post_id']}"
        recent_ctas = {network: get_recent_ctas(history, network) for network in NETWORKS}
        try:
            payload = generate_social_payload(model, article, recent_ctas)
            validate_payload(payload, recent_ctas)
            saved_files = save_network_files(article, payload)

            for network in NETWORKS:
                history.setdefault(network, []).append(payload[network]["cta"].strip())
                history[network] = history[network][-20:]

            update_csv_status(article)
            save_cta_history(history)

            log(Colors.OKGREEN, "OK", f"Copies salvos para {unique_id}")
            results.append(
                {
                    "success": True,
                    "unique_id": unique_id,
                    "title": article["post_title"],
                    "networks": [item["network"] for item in saved_files],
                }
            )
        except Exception as exc:
            log(Colors.FAIL, "ERRO", f"{unique_id}: {exc}")
            results.append(
                {
                    "success": False,
                    "unique_id": unique_id,
                    "title": article["post_title"],
                    "networks": [],
                    "error": str(exc),
                }
            )

    report_path = generate_report(results, timestamp)
    log(Colors.OKGREEN, "REPORT", f"Relatorio salvo em {report_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Orbit Social Agent - gera copies para LinkedIn, Instagram e Facebook."
    )
    parser.add_argument("--api_key", help="Gemini API Key. Se omitido, usa GEMINI_API_KEY.")
    parser.add_argument("--wp_url", default=DEFAULT_WP_URL, help="Base URL do WordPress.")
    parser.add_argument("--count", type=int, default=5, help="Quantidade de artigos recentes. Padrao: 5")
    parser.add_argument("--article_id", help="Filtra por unique_import_id, ex: Orbit_27")
    parser.add_argument("--wp_post_id", help="Filtra por wp_post_id")
    parser.add_argument("--dry_run", action="store_true", help="Lista os artigos sem gerar copies.")
    args = parser.parse_args()

    api_key = load_api_key(args.api_key)
    run(
        api_key=api_key,
        wp_url=args.wp_url,
        count=args.count,
        article_id=args.article_id,
        wp_post_id=args.wp_post_id,
        dry_run=args.dry_run,
    )


if __name__ == "__main__":
    main()
