
import os
import csv
import json
import argparse
import glob
import requests
import pandas as pd
from datetime import datetime
from requests.auth import HTTPBasicAuth

# --- Configuration ---
OUTPUT_DIR = "output_csv_batches_v2"
REPORTS_DIR = "relatorios"

class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'


def list_draft_articles(input_dir):
    """List all draft articles from CSV files."""
    csv_files = sorted(glob.glob(f"{input_dir}/*.csv"))
    all_drafts = []

    for file_path in csv_files:
        try:
            df = pd.read_csv(file_path)
            for idx, row in df.iterrows():
                status = str(row.get('post_status', '')).strip().lower()
                if status in ['draft', 'rascunho']:
                    content = str(row.get('post_content', ''))
                    if len(content) > 100 and 'ERRO' not in content:
                        all_drafts.append({
                            'file': file_path,
                            'file_idx': idx,
                            'title': str(row.get('post_title', 'Sem titulo')),
                            'meta_title': str(row.get('meta_title', '')),
                            'meta_desc': str(row.get('meta_description', '')),
                            'content': content,
                            'qa_score': row.get('qa_score', 'N/A'),
                            'date': str(row.get('post_date', ''))
                        })
        except Exception as e:
            print(f"{Colors.WARNING}Erro lendo {file_path}: {e}{Colors.ENDC}")

    return all_drafts


def publish_to_wordpress(wp_url, wp_user, wp_pass, article, publish_status='draft'):
    """Publish article to WordPress via REST API."""
    api_url = f"{wp_url}/wp-json/wp/v2/posts"

    # Separate article content from JSON-LD
    content = article['content']

    # Build post data
    post_data = {
        'title': article['meta_title'] if article['meta_title'] else article['title'],
        'content': content,
        'status': publish_status,  # 'draft' or 'publish'
        'format': 'standard',
    }

    # Add Yoast/RankMath SEO meta if available
    meta = {}
    if article.get('meta_title'):
        meta['_yoast_wpseo_title'] = article['meta_title']
        meta['rank_math_title'] = article['meta_title']
    if article.get('meta_desc'):
        meta['_yoast_wpseo_metadesc'] = article['meta_desc']
        meta['rank_math_description'] = article['meta_desc']

    if meta:
        post_data['meta'] = meta

    try:
        response = requests.post(
            api_url,
            json=post_data,
            auth=HTTPBasicAuth(wp_user, wp_pass),
            headers={'Content-Type': 'application/json'},
            timeout=30
        )

        if response.status_code == 201:
            data = response.json()
            return {
                'success': True,
                'post_id': data.get('id'),
                'link': data.get('link'),
                'status': data.get('status')
            }
        else:
            return {
                'success': False,
                'error': f"HTTP {response.status_code}: {response.text[:200]}"
            }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }


def mark_as_published(file_path, file_idx, post_id):
    """Update CSV to mark article as published."""
    try:
        df = pd.read_csv(file_path)
        df.loc[file_idx, 'post_status'] = 'published'
        df.loc[file_idx, 'wp_post_id'] = post_id
        df.loc[file_idx, 'published_at'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        df.to_csv(file_path, index=False, quoting=csv.QUOTE_ALL)
    except Exception as e:
        print(f"{Colors.WARNING}Erro atualizando CSV: {e}{Colors.ENDC}")


def generate_publish_report(results, timestamp):
    """Generate publish report."""
    os.makedirs(REPORTS_DIR, exist_ok=True)
    report_path = os.path.join(REPORTS_DIR, f"report_publicacao_{timestamp}.md")

    lines = []
    lines.append("# Orbit AI -- Relatorio de Publicacao\n")
    lines.append(f"**Data:** {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")

    success = sum(1 for r in results if r['success'])
    failed = sum(1 for r in results if not r['success'])

    lines.append("## Resumo\n")
    lines.append(f"| Metrica | Valor |")
    lines.append(f"|---|---|")
    lines.append(f"| Total publicados | {success} |")
    lines.append(f"| Falhas | {failed} |")
    lines.append("")

    lines.append("## Detalhamento\n")
    lines.append("| # | Titulo | Score QA | Status | Post ID | Link |")
    lines.append("|---|---|---|---|---|---|")
    for i, r in enumerate(results):
        if r['success']:
            lines.append(f"| {i+1} | {r['title'][:45]} | {r.get('qa_score', 'N/A')} | Publicado | {r.get('post_id', '')} | {r.get('link', '')} |")
        else:
            lines.append(f"| {i+1} | {r['title'][:45]} | {r.get('qa_score', 'N/A')} | ERRO | - | {r.get('error', '')[:50]} |")

    with open(report_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))

    return report_path


def main():
    parser = argparse.ArgumentParser(description="Orbit AI WordPress Publisher")
    parser.add_argument("--wp_url", default="https://sowads.com.br", help="WordPress site URL")
    parser.add_argument("--wp_user", default=None, help="WordPress username (or set WP_USER env var)")
    parser.add_argument("--wp_pass", default=None, help="WordPress app password (or set WP_PASS env var)")
    parser.add_argument("--input_dir", default=OUTPUT_DIR, help="Directory with CSV files")
    parser.add_argument("--publish", action='store_true', help="Publish as 'publish' instead of 'draft'")
    parser.add_argument("--all", action='store_true', help="Publish all drafts without asking")
    parser.add_argument("--list", action='store_true', help="Only list drafts, don't publish")
    args = parser.parse_args()

    # Get credentials from args or env vars
    wp_user = args.wp_user or os.environ.get('WP_USER')
    wp_pass = args.wp_pass or os.environ.get('WP_PASS')

    print(f"{Colors.HEADER}=== ORBIT AI WORDPRESS PUBLISHER ==={Colors.ENDC}")
    print(f"Site: {args.wp_url}")
    print(f"Input: {args.input_dir}")

    # List all draft articles
    drafts = list_draft_articles(args.input_dir)

    if not drafts:
        print(f"\n{Colors.WARNING}Nenhum artigo em rascunho encontrado em {args.input_dir}/{Colors.ENDC}")
        return

    # Display drafts
    print(f"\n{Colors.OKCYAN}Encontrados {len(drafts)} artigos em rascunho:{Colors.ENDC}\n")
    print(f"{'#':<4} {'Score':<8} {'Arquivo':<35} {'Titulo'}")
    print("-" * 100)
    for i, d in enumerate(drafts):
        score = d.get('qa_score', 'N/A')
        fname = os.path.basename(d['file'])[:33]
        title = d['title'][:55]
        print(f"{i+1:<4} {str(score):<8} {fname:<35} {title}")

    if args.list:
        print(f"\n{Colors.OKCYAN}Modo lista. Use --all ou selecione artigos para publicar.{Colors.ENDC}")
        return

    if not wp_user or not wp_pass:
        print(f"\n{Colors.FAIL}Credenciais nao fornecidas. Use --wp_user/--wp_pass ou defina WP_USER/WP_PASS.{Colors.ENDC}")
        return

    # Selection
    if not args.all:
        print(f"\n{Colors.BOLD}Quais artigos publicar? (ex: 1,3,5 ou 'all' para todos){Colors.ENDC}")
        selection = input("> ").strip()
        if selection.lower() == 'all':
            selected = list(range(len(drafts)))
        else:
            try:
                selected = [int(x.strip()) - 1 for x in selection.split(',')]
            except ValueError:
                print(f"{Colors.FAIL}Selecao invalida.{Colors.ENDC}")
                return
    else:
        selected = list(range(len(drafts)))

    # Publish
    publish_status = 'publish' if args.publish else 'draft'
    print(f"\n{Colors.HEADER}Publicando {len(selected)} artigos como '{publish_status}'...{Colors.ENDC}\n")

    results = []
    for idx in selected:
        if idx < 0 or idx >= len(drafts):
            continue

        article = drafts[idx]
        print(f"  [{idx+1}/{len(selected)}] {article['title'][:50]}...", end=" ")

        result = publish_to_wordpress(args.wp_url, wp_user, wp_pass, article, publish_status)
        result['title'] = article['title']
        result['qa_score'] = article.get('qa_score', 'N/A')

        if result['success']:
            print(f"{Colors.OKGREEN}OK (ID: {result['post_id']}){Colors.ENDC}")
            mark_as_published(article['file'], article['file_idx'], result['post_id'])
        else:
            print(f"{Colors.FAIL}ERRO: {result['error'][:60]}{Colors.ENDC}")

        results.append(result)

    # Report
    if results:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M")
        report_path = generate_publish_report(results, timestamp)
        print(f"\n{Colors.OKGREEN}[REPORT] Relatorio de publicacao: {report_path}{Colors.ENDC}")

    success_count = sum(1 for r in results if r['success'])
    print(f"\n{Colors.HEADER}=== PUBLICACAO COMPLETA: {success_count}/{len(results)} ==={Colors.ENDC}")


if __name__ == "__main__":
    main()
