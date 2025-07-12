import json
import pandas as pd
from extractor import GlossaryExtractor
import time

def process_row(row):
    extractor = GlossaryExtractor()
    url = row["Url"]
    entity = row["Entity"]
    bodytype = row["BodyType"]
    try:
        data = extractor.extract_from_url(url)
        glossary = data.get("glossary", {})
        sources = data.get("sources", {})
        extraction_sources = set(sources.values())
        extraction_source_str = ", ".join(sorted(extraction_sources)) if extraction_sources else "unknown"
        num_terms = len(glossary)
        return {
            "entity": entity,
            "extraction_source": extraction_source_str,
            "num_terms": num_terms,
            "url": url,
            "glossary": glossary
        }
    except Exception as e:
        return {
            "entity": entity,
            "extraction_source": "error",
            "num_terms": 0,
            "url": url,
            "glossary": {},
            "error": str(e)
        }

def main():
    start_time = time.time()
    log_lines = []
    print("[DEBUG] About to read CSV", flush=True)
    df = pd.read_csv(r"data/output/FINAL_GLOSSARY_URLS.csv")
    print(f"[DEBUG] Read {len(df)} rows from CSV", flush=True)
    rows = df.to_dict(orient="records")
    log_lines.append(f"[INFO] Extraction started. Processing {len(rows)} URLs.")

    from concurrent.futures import ThreadPoolExecutor, as_completed
    results = []
    with ThreadPoolExecutor(max_workers=16) as executor:
        futures = [executor.submit(process_row, row) for row in rows]
        for future in as_completed(futures):
            res = future.result()
            results.append(res)
            if "error" in res:
                log_lines.append(f"[ERROR] Failed: {res['entity']} | {res['url']} | {res.get('error','')}")
            else:
                log_lines.append(f"[SUCCESS] {res['entity']} | {res['url']} | {res['num_terms']} terms")

    with open(r"data/output/test_glossary16.txt", "w", encoding="utf-8") as file:
        for res in results:
            file.write(f"Entity: {res['entity']} |")
            file.write(f"Extraction Source: {res['extraction_source']} |")
            file.write(f"Number of Terms: {res['num_terms']}\n")
            file.write(f"Url : {res['url']}\n")
            for term, definition in res["glossary"].items():
                file.write(f"{term}: {definition}\n")
            if "error" in res:
                file.write(f"Error: {res['error']}\n")
            file.write("\n")
    end_time = time.time()
    elapsed = end_time - start_time
    log_lines.append(f"[INFO] Extraction finished. Elapsed time: {elapsed:.2f} seconds ({elapsed/60:.2f} minutes)")

    with open(r"data/output/extraction_log16.txt", "w", encoding="utf-8") as logfile:
        for line in log_lines:
            logfile.write(line + "\n")
    print(f"Extraction complete. Elapsed time: {elapsed:.2f} seconds. See data/output/extraction_log.txt for details.")

if __name__ == "__main__":
    print("[DEBUG] In __main__ block", flush=True)
    main()