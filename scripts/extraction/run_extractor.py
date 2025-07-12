import json
import pandas as pd
from extractor import GlossaryExtractor

def main() -> None:
    # Read the CSV file
    df = pd.read_csv(r"data/output/FINAL_GLOSSARY_URLS.csv")
    extractor = GlossaryExtractor()
    results = []

    for _, row in df.iterrows():
        url = row["Url"]
        entity = row["Entity"]
        bodytype = row["BodyType"]
        data = extractor.extract_from_url(url)
        glossary = data.get("glossary", {})
        for term, definition in glossary.items():
            results.append({
                "term": term,
                "definition": definition,
                "entity": entity,
                "bodytype": bodytype,
                "source_url": url
            })

    output = r"data/output/glossary.json"
    with open(output, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

if __name__ == "__main__":
    main()