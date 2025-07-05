import pandas as pd
import os
from pathlib import Path

def normalize_urls(urls):
    # Split by |, strip whitespace, ignore empty
    return set(u.strip() for u in str(urls).split('|') if u.strip())

def main():
    root = Path(__file__).resolve().parents[2]
    log_path = root / 'data' / 'output' / 'extraction_log.csv'
    all_data_path = root / 'data' / 'output' / 'all_data.csv'
    output_path = root / 'data' / 'output' / 'url_comparison_log.csv'

    log_df = pd.read_csv(log_path)
    all_data_df = pd.read_csv(all_data_path)

    results = []
    for idx, row in log_df.iterrows():
        num_terms = row.get('Num Terms', 0)
        try:
            num_terms = int(num_terms)
        except Exception:
            continue
        if num_terms not in [0, 1]:
            continue
        agency = row['Agency']
        portfolio = row['Portfolio']
        glossary_type = row['Glossary Type']
        log_urls = row['Glossary URLs']
        # Find matching entity in all_data.csv
        match = all_data_df[all_data_df['Entity'] == agency]
        if match.empty:
            all_data_urls = ''
        else:
            # Use both glossary_url1 and glossary_url2 if present
            url1 = str(match.iloc[0].get('glossary_url1', '')).strip()
            url2 = str(match.iloc[0].get('glossary_url2', '')).strip()
            all_data_urls = url1
            if url2:
                all_data_urls += ' | ' + url2
        set_log = normalize_urls(log_urls)
        set_all = normalize_urls(all_data_urls)
        same = set_log == set_all
        print(f"{agency} | {portfolio} | {glossary_type} | {num_terms} | SAME: {same}")
        print(f"  All Data URLs: {all_data_urls}")
        print(f"  Glossary URLs: {log_urls}\n")
        results.append({
            'Agency': agency,
            'Portfolio': portfolio,
            'Glossary Type': glossary_type,
            'Num Terms': num_terms,
            'All Data URLs': all_data_urls,
            'Glossary URLs': log_urls,
            'Same': 'same' if same else 'different'
        })
    # Save results
    pd.DataFrame(results).to_csv(output_path, index=False)
    print(f"Comparison saved to {output_path}")

if __name__ == "__main__":
    main()
