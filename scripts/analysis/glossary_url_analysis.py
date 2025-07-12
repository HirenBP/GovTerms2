import json
from collections import Counter
from pathlib import Path

# Load the JSON file
json_path = Path(r"data/output/glossary.json")
with open(json_path, "r", encoding="utf-8") as f:
    data = json.load(f)

# Filter out entries that have both 'term' and 'definition'
entries = [d for d in data if "term" in d and "definition" in d and d["term"] and d["definition"]]

# Number of entities
entities = set(d.get("entity", "") for d in entries if d.get("entity"))
num_entities = len(entities)

# Number of terms (total)
num_terms = len(entries)

# Number of unique terms
unique_terms = set(d["term"] for d in entries)
num_unique_terms = len(unique_terms)

# 10 longest terms
longest_terms = sorted(unique_terms, key=len, reverse=True)[:10]

# 10 longest definitions
definitions = [d["definition"] for d in entries]
longest_definitions = sorted(definitions, key=len, reverse=True)[:10]

# Prepare report
report_lines = [
    f"Number of entities: {num_entities}",
    f"Number of terms (total): {num_terms}",
    f"Number of unique terms: {num_unique_terms}",
    "10 longest terms:",
    *[f"  {t}" for t in longest_terms],
    "10 longest definitions:",
    *[f"  {d[:120]}..." if len(d) > 120 else f"  {d}" for d in longest_definitions],
]

report = "\n".join(report_lines)

# Print to console
print(report)

# Save to text file
output_txt = json_path.parent / "glossary_analysis.txt"
with open(output_txt, "w", encoding="utf-8") as f:
    f.write(report)