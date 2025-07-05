import pandas as pd
import time
from pathlib import Path

from scripts.extraction.base_extractor import SmartGlossaryExtractor


def main():
    root = Path(__file__).resolve().parents[2]
    output_dir = root / 'data' / 'output'
    output_dir.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(root / 'data' / 'output' / 'glossary_sectiontitle_keyword_urls_agg.csv')
    url_columns = [col for col in df.columns if col.startswith('url')]
    extractor = SmartGlossaryExtractor()
    output_lines = []
    log_lines = []

    for _, row in df.iterrows():
        entity = row['Entity']
        portfolio = row.get('Portfolio', '')
        urls = [str(row[col]).strip() for col in url_columns if pd.notna(row[col]) and str(row[col]).strip()]
        all_terms = {}
        all_sources = {}
        url_used_for_log = None
        for url in urls:
            details = extractor.extract_with_fallback(url)
            glossary = details.get('glossary', {})
            sources = details.get('sources', {})
            if glossary and not url_used_for_log:
                url_used_for_log = details.get('used_url', url)
            all_terms.update(glossary)
            all_sources.update(sources)
            time.sleep(2)
        output_lines.append(f"Entity: {entity} | Portfolio: {portfolio}\n")
        if all_terms:
            for term, definition in all_terms.items():
                method = all_sources.get(term, 'unknown')
                output_lines.append(f"  [{method}] {term}: {definition}\n")
            output_lines.append("\n")
        else:
            output_lines.append("  No terms extracted.\n\n")
        num_terms = len(all_terms)
        if num_terms < 5:
            log_lines.append(f"{entity}\t{num_terms}\t{url_used_for_log or ''}\n")
        else:
            log_lines.append(f"{entity}\t{num_terms}\n")

    all_output_path = output_dir / 'all_glossaries.txt'
    with open(all_output_path, 'w', encoding='utf-8') as f:
        f.writelines(output_lines)
    print(f"[LOG] All glossary extractions written to {all_output_path}")

    log_output_path = output_dir / 'extraction_log.txt'
    with open(log_output_path, 'w', encoding='utf-8') as f:
        f.writelines(log_lines)
    print(f"[LOG] Extraction log written to {log_output_path}")


if __name__ == '__main__':
    main()
