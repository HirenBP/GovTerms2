import json
from collections import Counter

COMBINED_FILE = r"data/output/combined_glossary.json"

with open(COMBINED_FILE, "r", encoding="utf-8") as f:
    terms = json.load(f)

# Total number of terms
total_terms = len(terms)
print(f"Total number of terms: {total_terms}")

# Terms by type of body
body_type_counts = Counter(term["BodyType"] for term in terms if "BodyType" in term)
print("\nTerms by Body Type:")
for body_type, count in body_type_counts.most_common():
    print(f"  {body_type}: {count}")

# Most common terms (top 10)
term_counter = Counter(term["Term"].strip().lower() for term in terms if "Term" in term)
print("\nTop 10 Most Common Terms:")
for term, count in term_counter.most_common(10):
    print(f"  {term}: {count}")


# Count of terms where the term is longer than its definition
longer_term_count = sum(
    1 for t in terms
    if "Term" in t and "Definition" in t and len(t["Term"]) > len(t["Definition"])
)

print(f"\nNumber of terms where the term is longer than its definition: {longer_term_count}")
print("\nTerms where the term is longer than its definition:")
for t in terms:
    if "Term" in t and "Definition" in t and len(t["Term"]) > len(t["Definition"]):
        print(f"  {t['Term']}:\n {t['Definition']}")

# The longest term
longest_term = max(terms, key=lambda t: len(t["Term"]))
print("\nLongest Term:")
print(f"  {longest_term['Term']} (Length: {len(longest_term['Term'])})")
print(f"  Definition: {longest_term['Definition']}")
print(f"  Entity: {longest_term['Entity']}")
print(f"  BodyType: {longest_term['BodyType']}")
print(f"  Portfolio: {longest_term['Portfolio']}")
print(f"  Url: {longest_term['Url']}")
