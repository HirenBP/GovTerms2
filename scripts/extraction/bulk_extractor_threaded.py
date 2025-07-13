import pandas as pd
from extractor_simple import SimpleHTMLViewer
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
OUTPUT_FILE = "data/output/GLOSSARY_TABLE_FINAL.txt"
LOG_FILE = "data/output/GLOSSARY_LOG_FINAL.txt"
LOG_FILE_FAILED = "data/output/GLOSSARY_LOG_FAILED.txt"
def filter_glossary_lines(lines):
    """
    Filters out header single uppercase letters from glossary lines based on heuristic:
    - If repeated single uppercase letters exist: assume headers + valid terms; remove first occurrence of each letter (headers)
    - Else if many unique single uppercase letters (>=13) and enough lines (>=20): assume only headers; remove all single uppercase letters
    - Else: assume no headers; keep all lines
    
    Args:
        lines (list of str): raw lines from glossary extraction
    
    Returns:
        filtered list of lines
    """

    # Strip lines and remove empty lines
    lines = [line.strip() for line in lines if line.strip() != ""]

    # Extract all single uppercase letter lines
    single_caps = [line for line in lines if len(line) == 1 and line.isalpha() and line.isupper()]
    unique_caps = set(single_caps)
    total_lines = len(lines)
    num_unique_caps = len(unique_caps)

    # Detect if any single uppercase letter repeats (case 2)
    has_repeats = any(single_caps.count(c) > 1 for c in unique_caps)

    if has_repeats:
        # Case 2: Headers + valid single-letter terms
        seen = set()
        filtered = []
        for line in lines:
            if len(line) == 1 and line.isalpha() and line.isupper():
                if line not in seen:
                    seen.add(line)
                    # Skip first occurrence (header)
                    continue
            filtered.append(line)
        return filtered

    if num_unique_caps >= 10 and total_lines >= 20:
        # Case 1: Only headers, remove all single-letter lines
        return [line for line in lines if not (len(line) == 1 and line.isalpha() and line.isupper())]

    # Case 3: No headers, keep all lines
    return lines

def extract_and_format(row):
    entity = row["Entity"]
    body_type = row["BodyType"]
    url = row["Url"]
    extractor = SimpleHTMLViewer()
    
    try:
        html_structure = extractor.extract_clean_tag_structure(url)
        if html_structure:
            lines = [line.strip() for line in html_structure.splitlines() if line.strip()]
            # Filter glossary lines using the new heuristic
            filtered_lines = filter_glossary_lines(lines)
            terms = []
            pairs = zip(filtered_lines[::2], filtered_lines[1::2])
            for term, definition in pairs:
                terms.append(f"{term}: {definition}")
            block = f"Entity: {entity} | Body Type: {body_type} | Number of terms:{len(terms)} | URL: {url}\n" + "\n".join(terms) + "\n\n"
            print(f"[✅] {entity} – extracted {len(terms)} terms.")
            return block, (entity, url, len(terms))
        else:
            print(f"[⚠️] {entity} – No glossary content extracted.")
            return None, (entity, url, 0)
    except Exception as e:
        print(f"[❌] {entity} – Failed. Reason: {e}")
        return None, (entity, url, 0)

def main():
    start_time = time.time()
    df = pd.read_csv("data/output/FINAL_GLOSSARY_URLS.csv")
    results = []
    log_entries = []
    failed_entries = []
    with ThreadPoolExecutor(max_workers=12) as executor:
        futures = [executor.submit(extract_and_format, row) for _, row in df.iterrows()]
        for future in as_completed(futures):
            block, log_info = future.result()
            entity, url, num_terms = log_info
            log_entries.append(f"Entity: {entity} | Number of terms: {num_terms} ")
            if num_terms <= 0:
                # Log failed entries separately
                failed_entries.append(f"Entity: {entity} | URL: {url} | Number of terms: {num_terms} ")
            if block:
                results.append(block)
    total_time = time.time() - start_time
    results.sort()
    # Write to output file
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        for block in results:
            f.write(block)
        f.write(f"\n[⏱️] Total extraction time: {total_time:.2f} seconds\n")

    # Write log file
    with open(LOG_FILE, "w", encoding="utf-8") as logf:
        logf.write(f"Total URLs processed: {len(df)}\n")
        logf.write(f"Total extraction time: {total_time:.2f} seconds\n")
        logf.write("\n")
        for entry in log_entries:
            logf.write(entry + "\n")
    # Write failed entries log file
    with open(LOG_FILE_FAILED, "w", encoding="utf-8") as failed_log:
        failed_log.write(f"Total failed entries: {len(failed_entries)}\n")
        failed_log.write("\n")
        for entry in failed_entries:
            failed_log.write(entry + "\n")    

    print(f"\n[📁] All results written to: {OUTPUT_FILE}")
    print(f"[📝] Log written to: {LOG_FILE}")

if __name__ == "__main__":

    main()
