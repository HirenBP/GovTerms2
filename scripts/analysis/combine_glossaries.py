import json
import pandas as pd

GLOSSARIES_FILE = r"data/output/GLOSSARY_TABLE_FINAL.txt"
FAILED_GLOSSARIES_FILE = r"data/output/failed_glossary_retry_results.txt"
GLOSSARY_URLS_FILE = r"data/output/FINAL_GLOSSARY_URLS.csv"
WEB_GLOSSARY_FILE = r"data\output\WEB_GLOSSARY.txt"
OUTPUT_FILE = r"data/output/combined_glossary.json"

# Read the glossary URLs file to get portfolio and entity information
df_urls = pd.read_csv(GLOSSARY_URLS_FILE)

# Read the glossary file and extract terms
terms = []
number_of_terms = 0
with open(GLOSSARIES_FILE, "r", encoding="utf-8") as f:
    lines = f.readlines()
    for line in lines:
        # Skip empty lines
        if line.strip() and line.startswith("Entity:"):
            parts = line.split("|")
            entity = parts[0].split(":")[1].strip()
            body_type = parts[1].split(":")[1].strip()
            number_of_terms = int(parts[2].split(":")[1].strip())
            # Extract URL from the line
            url = parts[3].split(":", 1)[1].strip()
        elif line.strip() and ":" in line and number_of_terms > 1:
            defs = line.split(":", 1)
            term = defs[0].strip()
            definition = defs[1].strip()
            terms.append({
                "Term": term,
                "Definition": definition,
                "Entity": entity,
                "BodyType": body_type,
                "Portfolio": df_urls[df_urls["Entity"] == entity]["Portfolio"].values[0],
                "Url": url
            })

# Read the failed glossary file and extract terms
failed_terms = []
with open(FAILED_GLOSSARIES_FILE, "r", encoding="utf-8") as f:
    lines = f.readlines()
    entity = None
    url = None
    number_of_terms = 0
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if line.startswith("Entity:"):
            parts = line.split("|")
            entity = parts[0].split(":")[1].strip()
            number_of_terms = int(parts[1].split(":")[1].strip())
            # Next non-empty line is URL
            i += 1
            while i < len(lines) and not lines[i].strip():
                i += 1
            url = lines[i].split(":", 1)[1].strip() if i < len(lines) and lines[i].startswith("Url:") else None
        elif line and ":" in line and not line.startswith("Url:") and entity and url and number_of_terms > 1:
            term, definition = line.split(":", 1)
            failed_terms.append({
                "Term": term.strip(),
                "Definition": definition.strip(),
                "Entity": entity,
                "Portfolio": df_urls[df_urls["Entity"] == entity]["Portfolio"].values[0],
                "Url": url
            })
        i += 1
# Read Web Glossary file and extract terms, portflio, body type and url
web_terms = []
with open(WEB_GLOSSARY_FILE, "r", encoding="utf-8") as f:
    lines = f.readlines()
    portfolio = entity = body_type = url = None
    for i, line in enumerate(lines):
        line = line.strip()
        if not line:
            continue
        if line.startswith("Portfolio:"):
            # Parse header line
            parts = line.split("|")
            portfolio = parts[0].split(":",1)[1].strip()
            entity = parts[1].split(":",1)[1].strip()
            body_type = parts[2].split(":",1)[1].strip()
            # Number of Terms is parts[3], but not needed here
            # Next non-empty line is URL
            j = i + 1
            while j < len(lines) and not lines[j].strip():
                j += 1
            if j < len(lines) and lines[j].startswith("Url:"):
                url = lines[j].split(":",1)[1].strip()
        elif ":" in line and not line.startswith("Url:") and portfolio and entity and body_type and url:
            term, definition = line.split(":", 1)
            web_terms.append({
                "Term": term.strip(),
                "Definition": definition.strip(),
                "Entity": entity,
                "BodyType": body_type,
                "Portfolio": portfolio,
                "Url": url
            })
# Combine terms and failed terms and web terms
combined_terms = terms + failed_terms + web_terms

# Write combined terms to JSON file with ensure_ascii=False to preserve special characters
with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump(combined_terms, f, indent=4, ensure_ascii=False)
print(f"Combined glossary terms written to {OUTPUT_FILE}")
print(f"Total terms extracted: {len(terms) + len(failed_terms) + len(web_terms)}")