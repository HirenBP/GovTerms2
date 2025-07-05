import pandas as pd
import time
from pathlib import Path

from scripts.extraction.base_extractor import SmartGlossaryExtractor


def main():
    root = Path(__file__).resolve().parents[2]
    output_dir = root / 'data' / 'output'
    output_dir.mkdir(parents=True, exist_ok=True)
    visited_csv = output_dir / 'visited_agencies.csv'

    if visited_csv.exists():
        visited_agencies = set(pd.read_csv(visited_csv, header=None)[0].dropna().astype(str).tolist())
    else:
        visited_agencies = set()

    df = pd.read_csv(root / 'data' / 'output' / 'all_data.csv')
    df = df[df['glossary_type'].isin(['one', 'both'])].reset_index(drop=True)
    df = df[~df['Entity'].isin(visited_agencies)].reset_index(drop=True)

    extractor = SmartGlossaryExtractor()
    output_lines = []
    tested_agencies = set()

    for _, row in df.iterrows():
        entity = row['Entity']
        portfolio = row['Portfolio']
        glossary_type = str(row.get('glossary_type', 'none')).strip().lower()
        url1 = str(row.get('glossary_url1', '')).strip()
        url2 = str(row.get('glossary_url2', '')).strip()

        urls = []
        if glossary_type == 'both':
            urls = [u for u in [url1, url2] if u]
        elif glossary_type == 'one' and url1:
            urls = [url1]

        all_terms = {}
        all_sources = {}
        for url in urls:
            details = extractor.extract_with_fallback(url)
            all_terms.update(details.get('glossary', {}))
            all_sources.update(details.get('sources', {}))
            time.sleep(2)

        if all_terms:
            output_lines.append(f"Agency: {entity} | Portfolio: {portfolio}\n")
            for term, definition in all_terms.items():
                method = all_sources.get(term, 'unknown')
                output_lines.append(f"  [{method}] {term}: {definition}\n")
            output_lines.append("\n")
        else:
            output_lines.append(f"Agency: {entity} | Portfolio: {portfolio}\n  No terms extracted.\n\n")
        tested_agencies.add(entity)

    part = 1
    batch_lines = []
    entities_per_file = 5
    for line in output_lines:
        batch_lines.append(line)
        if line.startswith('Agency') and len(batch_lines) > 1:
            if len(batch_lines) > entities_per_file:
                part_file = output_dir / f"glossaries_part{part}.txt"
                with open(part_file, 'w', encoding='utf-8') as f:
                    f.writelines(batch_lines[:-1])
                print(f"[LOG] Written {len(batch_lines)-1} lines to {part_file}")
                batch_lines = [batch_lines[-1]]
                part += 1
    if batch_lines:
        part_file = output_dir / f"glossaries_part{part}.txt"
        with open(part_file, 'w', encoding='utf-8') as f:
            f.writelines(batch_lines)
        print(f"[LOG] Written {len(batch_lines)} lines to {part_file}")

    log_csv_path = output_dir / 'extraction_log.csv'
    pd.Series(tested_agencies).to_csv(log_csv_path, index=False, header=False)
    print(f"[LOG] Comprehensive extraction log written to {log_csv_path}")

    if tested_agencies:
        all_visited = visited_agencies.union(tested_agencies)
        pd.Series(list(all_visited)).to_csv(visited_csv, index=False, header=False)
        print(f"[LOG] Updated visited agencies CSV: {visited_csv}")


if __name__ == '__main__':
    main()
