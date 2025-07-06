import json
import csv

# Load Entity URLs from CSV
entity_url_map = {}
with open("data/output/ANUAL_REPORTS_FINAL.csv", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    for row in reader:
        name = row["Entity"].strip()
        url = row["URL"].strip()
        entity_url_map[name] = url

# Parse glossary file
json_data = []
current_entity = None
current_portfolio = None

with open("data/output/all_glossaries.txt", encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        if line.startswith("Entity:") and "|" in line:
            entity_part, portfolio_part = line.split("|", 1)
            current_entity = entity_part.replace("Entity:", "").strip()
            current_portfolio = portfolio_part.replace("Portfolio:", "").strip()
        elif ":" in line and current_entity:
            try:
                term, definition = line.split(":", 1)
                entity_url = entity_url_map.get(current_entity, "")
                json_data.append({
                    "str": f"{term.strip()}: {definition.strip()}",
                    "Term": term.strip(),
                    "Definition": definition.strip(),
                    "Entity": current_entity,
                    "Portfolio": current_portfolio,
                    "Entity Url": entity_url
                })
            except ValueError:
                print(f"⚠️ Could not parse line: {line}")
                continue

# Save output JSON
with open("data/output/All_glossaries.json", "w", encoding="utf-8") as out:
    json.dump(json_data, out, indent=4, ensure_ascii=False)

print(f"✅ {len(json_data)} Glossary terms exported successfully.")