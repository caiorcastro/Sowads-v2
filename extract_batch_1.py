import pandas as pd
import os
import re

# Read Batch 1
df = pd.read_csv('output_csv_batches/lote_1_artigos_1_a_10.csv')
output_folder = 'html_review'

if not os.path.exists(output_folder):
    os.makedirs(output_folder)

print(f"Extracting {len(df)} articles to {output_folder}...")

for index, row in df.iterrows():
    title = row.get('post_title', f"Article_{index+1}")
    content = row.get('post_content', "")
    
    # Sanitize filename
    safe_title = re.sub(r'[^a-zA-Z0-9]', '_', title)[:50]
    filename = f"{index+1:02d}_{safe_title}.html"
    path = os.path.join(output_folder, filename)
    
    with open(path, 'w', encoding='utf-8') as f:
        # Wrap in simple HTML boilerplate for browser viewing
        f.write(f"<!DOCTYPE html><html lang='es'><head><meta charset='UTF-8'><title>{title}</title><style>body{{font-family:sans-serif;max-width:800px;margin:2rem auto;line-height:1.6}}</style></head><body>")
        f.write(f"<h1>Preview: {title}</h1>")
        f.write("<hr>")
        f.write(content)
        f.write("</body></html>")
        
    print(f" -> Saved: {filename}")

print("Done.")
