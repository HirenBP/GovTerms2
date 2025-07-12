import json
import pandas as pd
from extractor import GlossaryExtractor

def main() -> None:
    # Read the CSV file
    df = pd.read_csv(r"data/output/FINAL_GLOSSARY_URLS.csv")
    extractor = GlossaryExtractor()
    with open(r"data/output/test_glossary.txt", "w", encoding="utf-8") as file:
        for _, row in df.head(5).iterrows():
            url = row["Url"]
            entity = row["Entity"]
            bodytype = row["BodyType"]
            data = extractor.extract_from_url(url)
            glossary = data.get("glossary", {})
            sources = data.get("sources", {})
            # Determine extraction source(s) used for this entity
            extraction_sources = set(sources.values())
            extraction_source_str = ", ".join(sorted(extraction_sources)) if extraction_sources else "unknown"
            num_terms = len(glossary)
            file.write(f"Entity: {entity} |")
            file.write(f"Extraction Source: {extraction_source_str} |")
            file.write(f"Number of Terms: {num_terms}\n")
            file.write(f"Url : {url}\n" )
            for term, definition in glossary.items():
                file.write(f"{term}: {definition}\n")
            file.write("\n")
        
        
if __name__ == "__main__":
    main()