import pandas as pd
import time
from pathlib import Path

from scripts.extraction.base_extractor import SmartGlossaryExtractor


def main():
    root = Path(__file__).resolve().parents[2]
    output_dir = root / 'data' / 'output'
    output_dir.mkdir(parents=True, exist_ok=True)

    retry_entities = {
        "Australian Security Intelligence Organisation",
        "Australian Submarine Agency",
        "Coal Mining Industry (Long Service Leave Funding) Corporation",
        "Fisheries Research and Development Corporation",
        "Future Fund Management Agency",
        "Independent Health and Aged Care Pricing Authority",
        "National Emergency Management Agency",
        "National Film and Sound Archive of Australia",
        "National Gallery of Australia",
        "National Intermodal Corporation Limited",
        "Parliamentary Workplace Support Service",
        "Tiwi Land Council",
    }

    df = pd.read_csv(root / 'data' / 'output' / 'glossary_sectiontitle_keyword_urls_agg.csv')
    url_columns = [col for col in df.columns if col.startswith('url')]
    extractor = SmartGlossaryExtractor()

    for _, row in df.iterrows():
        entity = row['Entity']
        if entity not in retry_entities:
            continue
        portfolio = row.get('Portfolio', '')
        urls = [str(row[col]).strip() for col in url_columns if pd.notna(row[col]) and str(row[col]).strip()]
        all_terms = {}
        all_sources = {}
        for url in urls:
            print(f"[INFO] Extracting for {entity} from {url}")
            details = extractor.extract_with_fallback(url)
            all_terms.update(details.get('glossary', {}))
            all_sources.update(details.get('sources', {}))
            time.sleep(2)
        print(f"Entity: {entity} | Portfolio: {portfolio}")
        if all_terms:
            for term, definition in all_terms.items():
                method = all_sources.get(term, 'unknown')
                print(f"  [{method}] {term}: {definition}")
            print()
        else:
            print("  No terms extracted.\n")
        num_terms = len(all_terms)
        print(f"[RESULT] {entity}: {num_terms} terms extracted\n")


if __name__ == '__main__':
    main()
