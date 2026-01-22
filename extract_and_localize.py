import csv
import json
import re

# Load priority topics from JSON
priority_topics = []
try:
    with open('regras_geracao/schema_conteudo_latam_v9.json', 'r') as f:
        data = json.load(f)
        priority_topics.extend(data.get('priority_topics', {}).get('US', []))
        priority_topics.extend(data.get('priority_topics', {}).get('UAE', []))
        priority_topics.extend(data.get('priority_topics', {}).get('real_estate', []))
except Exception as e:
    print(f"Error reading JSON: {e}")

# Load existing topics from CSV
existing_topics = []
try:
    with open('2025_12_13_20_21_batch.csv', 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get('post_title'):
                existing_topics.append(row['post_title'])
except Exception as e:
    print(f"Error reading CSV: {e}")

# Localization function
def localize_title(title):
    title = title.replace("Brasileiros", "Latinos")
    title = title.replace("brasileiros", "latinos")
    title = title.replace("Brasil", "América Latina")
    title = title.replace("EUA", "EE. UU.")
    title = title.replace("Estados Unidos", "EE. UU.")
    # Add more rules as needed based on observation
    return title

# Prepare output data
output_rows = []
seen_titles = set()

# Process existing
for title in existing_topics:
    localized = localize_title(title)
    if localized not in seen_titles:
        output_rows.append({"Origin": "Existing Batch", "Original_PT": title, "Localized_ES_Draft": localized})
        seen_titles.add(localized)

# Process priority (assuming they are already in ES or need minor tweaks? JSON says they are ready for ES-419)
for title in priority_topics:
    # These are already in ES per the JSON content
    if title not in seen_titles:
        output_rows.append({"Origin": "JSON Priority", "Original_PT": "N/A", "Localized_ES_Draft": title})
        seen_titles.add(title)

# Write to new CSV
with open('relatorios/planejamento_temas_latam.csv', 'w', newline='') as f:
    fieldnames = ['Origin', 'Original_PT', 'Localized_ES_Draft']
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(output_rows)

print(f"Generated {len(output_rows)} topics in relatorios/planejamento_temas_latam.csv")
