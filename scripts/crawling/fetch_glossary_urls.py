from fetch_results_from_api import API_Extractor
from collections import defaultdict
import csv

extractor = API_Extractor()
results = extractor.extract()
URLS_with_details = []
BASE_URL = "https://www.transparency.gov.au/publications"
keywords = [
    "glossary", "glossaries", "acronym", "acronyms",
    "abbreviation", "abbreviations", "shortened","definitions","glossary-and-indexes", "shortened-terms"]

filtered_results = []
for r in results:
    urlslug = r.get("UrlSlug", "").lower()
    # Loosen year pattern and add more keywords
    if (
        (
            ("2023-24" in urlslug or "2023-2024" in urlslug)
            and "annual-report" in urlslug
        )
        and any(k in urlslug for k in keywords)
    ):
        filtered_results.append(r)

for r in filtered_results:
    portfolio = r.get("PortfolioUrlSlug")
    entity_slug = r.get("EntityUrlSlug")
    tail = r.get("UrlSlug")
    if portfolio and entity_slug and tail:
        url = f"{BASE_URL}/{portfolio}/{entity_slug}/{tail}".replace("//", "/")
        url = url.replace("https:/", "https://")
        URLS_with_details.append([
            r.get("Portfolio"),
            r.get("Entity"),
            r.get("BodyType"),
            url
        ])

# Group by entity
entity_to_urls = defaultdict(list)
for entry in URLS_with_details:
    entity = entry[1]
    entity_to_urls[entity].append(entry)

final_entries = []
for entity, entries in entity_to_urls.items():
    # Count number of "/" in each url
    entries_with_slash_count = [(entry, entry[3].count("/")) for entry in entries]
    entries_sorted = sorted(entries_with_slash_count, key=lambda x: x[1], reverse=True)
    if len(entries_sorted) == 1:
        # Only one URL, keep it
        final_entries.append(entries_sorted[0][0])
    elif len(entries_sorted) == 2:
        # Two URLs, keep both if same slash count, else keep the one with more slashes
        if entries_sorted[0][1] == entries_sorted[1][1]:
            final_entries.append(entries_sorted[0][0])
            final_entries.append(entries_sorted[1][0])
        else:
            final_entries.append(entries_sorted[0][0])
    else:
        # More than two URLs, keep all with the maximum number of slashes
        max_slash = entries_sorted[0][1]
        for entry, count in entries_sorted:
            if count == max_slash:
                final_entries.append(entry)

output_path = r"data/output/FINAL_GLOSSARY_URLS.csv"
output_path2 = r"data/output/GLOSSARY_ENTITIES.txt"
unique_entities = set()

with open(output_path, "w", encoding="utf-8", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["Portfolio", "Entity", "BodyType", "Url"])
    for entry in final_entries:
        unique_entities.add(entry[1])
        writer.writerow(entry)

with open(output_path2, "w", encoding="utf-8") as f:
    for entry in sorted(unique_entities):
        url_count = len(entity_to_urls[entry])
        f.write(f"{entry} ({url_count} urls)\n")

print(f"Results written to {output_path}")
print(f"Number of urls extracted: {len(final_entries)}")
print(f"Unique entities extracted:{len(unique_entities)}")