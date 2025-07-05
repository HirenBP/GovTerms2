import json
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import time
import pandas as pd
import re
import random
import os

SKIP_WORDS = {
    "acronym",
    "meaning",
    "term, acronym or abbreviation",
    "description or complete term",
    "copy link",
    "glossary",
    "Term", 
    "Description",
    "term",
    "description",
    "definition"
}

def format_glossary_line(line: str) -> str:
    line = line.replace('\xa0', ' ')
    new_line = re.sub(r'\s{2,}', ': ', line, count=1)
    if new_line == line:
        parts = line.split(' ', 1)
        if len(parts) == 2:
            new_line = f"{parts[0]}: {parts[1]}"
    return new_line

def glossary_in_list(list_tag) -> dict:
    glossary_dict = {}
    for li in list_tag.find_all("li"):
        text = li.get_text(" ", strip=True)
        text = text.replace('\xa0', ' ')
        if len(text) == 1 or text.lower() in SKIP_WORDS:
            continue
        # Try splitting by colon or dash first
        if ':' in text:
            parts = text.split(':', 1)
        elif ' - ' in text:
            parts = text.split(' - ', 1)
        else:
            # Split on 3 or more whitespace (including tabs, spaces, etc.)
            parts = re.split(r'[ \t\u00A0]{3,}', text, maxsplit=1)
        if len(parts) == 2:
            term, definition = parts[0].strip(), parts[1].strip()
            if term.lower() in SKIP_WORDS or definition.lower() in SKIP_WORDS:
                continue
            glossary_dict[term] = definition
    return glossary_dict

def glossary_in_table(table) -> dict:
    glossary_dict = {}
    for row in table.find_all("tr"):
        cells = row.find_all(["td", "th"])
        cell_texts = [cell.get_text(" ", strip=True).replace('\xa0', ' ') for cell in cells]
        if any(cell.lower() in SKIP_WORDS for cell in cell_texts):
            continue
        if len(cell_texts) >= 2:
            term, definition = cell_texts[0], cell_texts[1]
            if len(term) == 1 or term.lower() in SKIP_WORDS or definition.lower() in SKIP_WORDS:
                continue
            glossary_dict[term] = definition
        elif len(cell_texts) == 1:
            line = format_glossary_line(cell_texts[0])
            parts = line.split(':', 1)
            if len(parts) == 2:
                term, definition = parts[0].strip(), parts[1].strip()
                if len(term) == 1 or term.lower() in SKIP_WORDS or definition.lower() in SKIP_WORDS:
                    continue
                glossary_dict[term] = definition
    return glossary_dict

def glossary_in_paragraph(paragraphs) -> dict:
    glossary_dict = {}
    i = 0
    while i < len(paragraphs):
        p = paragraphs[i]
        strong = p.find("strong") or p.find("b")
        text = p.get_text(" ", strip=True).replace('\xa0', ' ')
        if len(text) == 1 or text.lower() in SKIP_WORDS:
            i += 1
            continue
        # Check for <p><strong>Term</strong></p><p>Definition</p> structure
        if strong:
            abbr = strong.get_text(" ", strip=True)
            rest = text.replace(abbr, "", 1).strip()
            # If this <p> is just the term, and next <p> is definition
            if not rest and (i + 1) < len(paragraphs):
                next_p = paragraphs[i + 1]
                next_text = next_p.get_text(" ", strip=True).replace('\xa0', ' ')
                next_strong = next_p.find("strong") or next_p.find("b")
                # Only treat as definition if next <p> is not just a term
                if next_text and not next_strong and next_text.lower() not in SKIP_WORDS:
                    # Remove leading colon(s) and whitespace from definition
                    definition = re.sub(r'^\s*:+\s*', '', next_text)
                    definition = re.sub(r'^:+', ':', definition)
                    if abbr.lower() not in SKIP_WORDS and len(abbr) > 1:
                        glossary_dict[abbr] = definition
                    i += 2
                    continue
            # Otherwise, handle <p><strong>ADF<br>Australian Defence Force.</strong></p>
            if abbr.lower() not in SKIP_WORDS and len(abbr) > 1:
                # Remove leading colon(s) and whitespace from rest
                rest = re.sub(r'^\s*:+\s*', '', rest)
                rest = re.sub(r'^:+', ':', rest)
                glossary_dict[abbr] = rest
        else:
            parts = re.split(r'\s{3,}', text, maxsplit=1)
            if len(parts) == 2:
                term, definition = parts[0].strip(), parts[1].strip()
                if term.lower() in SKIP_WORDS or definition.lower() in SKIP_WORDS or len(term) == 1:
                    i += 1
                    continue
                definition = re.sub(r'^\s*:+\s*', '', definition)
                definition = re.sub(r'^:+', ':', definition)
                glossary_dict[term] = definition
            else:
                parts = text.split(':', 1)
                if len(parts) == 2:
                    term, definition = parts[0].strip(), parts[1].strip()
                    if term.lower() in SKIP_WORDS or definition.lower() in SKIP_WORDS or len(term) == 1:
                        i += 1
                        continue
                    definition = re.sub(r'^\s*:+\s*', '', definition)
                    definition = re.sub(r'^:+', ':', definition)
                    glossary_dict[term] = definition
        i += 1
    return glossary_dict

class SmartGlossaryExtractor:
    """
    Enhanced extractor that tries multiple techniques to identify and extract glossary data from a page.
    """
    def __init__(self):
        pass

    def setup_driver(self) -> webdriver.Chrome:
        options = webdriver.ChromeOptions()
        options.add_argument("--headless")
        return webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    def extract_from_url(self, url: str) -> dict:
        driver = self.setup_driver()
        try:
            driver.get(url)
            # Wait for the main glossary div to be present
            WebDriverWait(driver, 30).until(
                EC.presence_of_element_located((
                    By.CSS_SELECTOR,
                    "div.AnnualReportArticle_articleContent__eheNu"
                ))
            )
            # Now wait until the main div contains at least one table, p, or strong child
            def glossary_div_has_content(driver):
                try:
                    div = driver.find_element(By.CSS_SELECTOR, "div.AnnualReportArticle_articleContent__eheNu")
                    # Check for at least one table, p, or strong child
                    return (
                        div.find_elements(By.TAG_NAME, "table") or
                        div.find_elements(By.TAG_NAME, "p") or
                        div.find_elements(By.TAG_NAME, "strong")
                    )
                except Exception:
                    return False
            WebDriverWait(driver, 30).until(glossary_div_has_content)
            
            # soup = BeautifulSoup(driver.find_element)
            # soup = BeautifulSoup(driver.page_source, "html.parser")
            # main_div = soup.find("div", class_="AnnualReportArticle_articleContent__eheNu")
            element = driver.find_element(By.CLASS_NAME, "AnnualReportArticle_articleContent__eheNu")
            main_div = element.get_attribute('outerHTML')
            soup = BeautifulSoup(main_div, "html.parser")
            main_div = soup.find("div", class_="AnnualReportArticle_articleContent__eheNu")
            if main_div:
                pass
            else:
                print("    [ERROR] Main content div 'AnnualReportArticle_articleContent__eheNu' not found on page.")
            return self.smart_extract_glossary(soup)
        except Exception as e:
            print(f"    [ERROR] Error occurred: {e}")
            return {}
        finally:
            driver.quit()

    def smart_extract_glossary(self, soup) -> dict:
        # Priority: table > list > paragraph
        glossary_data = {}
        extraction_sources = {}
        # 1. Try all tables
        tables = soup.find_all("table")
        if tables:
            for table in tables:
                extracted = glossary_in_table(table)
                if extracted:
                    for k in extracted:
                        extraction_sources[k] = 'table'
                    glossary_data.update(extracted)
            return {"glossary": glossary_data, "sources": extraction_sources}
        # 2. Try all lists
        lists = soup.find_all(["ul", "ol"])
        if lists:
            for ul in lists:
                extracted = glossary_in_list(ul)
                if extracted:
                    for k in extracted:
                        extraction_sources[k] = 'list'
                    glossary_data.update(extracted)
            return {"glossary": glossary_data, "sources": extraction_sources}
        # 3. Try all paragraphs
        paragraphs = soup.find_all("p")
        if paragraphs:
            extracted = glossary_in_paragraph(paragraphs)
            if extracted:
                for k in extracted:
                    extraction_sources[k] = 'paragraph'
                glossary_data.update(extracted)
        return {"glossary": glossary_data, "sources": extraction_sources}

def main():
    import os
    import re
    filename = input("What do you want to name the output file ? ").strip()
    # Sanitize filename to remove illegal characters
    filename = re.sub(r'[\\/:*?"<>|]', '', filename)
    output_dir = os.path.join('C:', 'Users', 'hiren', 'PycharmProjects', 'GovTerms2', 'data', 'output')
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)
    file_path = os.path.join(output_dir, f"{filename}.txt")
    visited_csv = r'C:\Users\hiren\PycharmProjects\GovTerms2\data\output\visited_agencies.csv'
    # Read visited agencies if file exists
    if os.path.exists(visited_csv):
        visited_agencies = set(pd.read_csv(visited_csv, header=None)[0].tolist())
    else:
        visited_agencies = set()
    # Read all_data.csv with glossary_type, glossary_url1, glossary_url2
    df = pd.read_csv(r'C:\Users\hiren\PycharmProjects\GovTerms2\data\output\all_data.csv')
    # Only keep rows where glossary_type is 'one' or 'both' and not already visited
    df = df[df['glossary_type'].isin(['one', 'both'])].reset_index(drop=True)
    df = df[~df['Entity'].isin(visited_agencies)].reset_index(drop=True)
    # Randomly sample 5 agencies
    if len(df) > 5:
        df = df.sample(5, random_state=42).reset_index(drop=True)
    extractor = SmartGlossaryExtractor()
    used_ids = set()
    visited = []  # Track visited agencies and URLs
    tested_agencies = set()
    def generate_id() -> str:
        while True:
            term_id = str(random.randint(10000, 99999))
            if term_id not in used_ids:
                used_ids.add(term_id)
                return term_id
    output_lines = []
    for idx, row in df.iterrows():
        entity = row['Entity']
        portfolio = row['Portfolio']
        glossary_type = str(row.get('glossary_type', 'none')).strip().lower()
        url1 = str(row.get('glossary_url1', '')).strip()
        url2 = str(row.get('glossary_url2', '')).strip()
        all_terms = {}
        all_sources = {}
        # Helper to try extraction, and if no terms, try with cleaned url
        def try_extract(url):
            glossary_details = extractor.extract_from_url(url)
            glossary = glossary_details.get("glossary", {})
            sources = glossary_details.get("sources", {})
            if not glossary and '--' in url:
                cleaned_url = re.sub(r'-{2,}', '-', url)
                if cleaned_url != url:
                    glossary_details = extractor.extract_from_url(cleaned_url)
                    glossary = glossary_details.get("glossary", {})
                    sources = glossary_details.get("sources", {})
                    return glossary, sources, cleaned_url
            return glossary, sources, url
        if glossary_type == 'both':
            for url in [url1, url2]:
                if url:
                    glossary, sources, used_url = try_extract(url)
                    all_terms.update(glossary)
                    all_sources.update(sources)
                    visited.append((entity, used_url))
                    time.sleep(2)
        elif glossary_type == 'one':
            if url1:
                glossary, sources, used_url = try_extract(url1)
                all_terms.update(glossary)
                all_sources.update(sources)
                visited.append((entity, used_url))
                time.sleep(2)
        # Print extracted terms for this agency
        if all_terms:
            output_lines.append(f"Agency: {entity} | Portfolio: {portfolio}\n")
            for term, definition in all_terms.items():
                method = all_sources.get(term, 'unknown')
                output_lines.append(f"  [{method}] {term}: {definition}\n")
            output_lines.append("\n")
        else:
            output_lines.append(f"Agency: {entity} | Portfolio: {portfolio}\n  No terms extracted.\n\n")
        tested_agencies.add(entity)
    # Print only the final log
    print(f"[LOG] Extracted terms written to {file_path}")
    # Write output_lines to a text file
    with open(file_path, 'w', encoding='utf-8') as f:
        f.writelines(output_lines)
    # Update visited agencies CSV
    if tested_agencies:
        all_visited = visited_agencies.union(tested_agencies)
        pd.Series(list(all_visited)).to_csv(visited_csv, index=False, header=False)
        print(f"[LOG] Updated visited agencies CSV: {visited_csv}")
    # Add a final log: 
    print(f"Visited below agencies: ")
    print("{:<40} | {:<10} | {:<4} | {:<5} | {}".format('Agency', 'Type', 'Terms', 'Meth', 'Portfolio'))
    print("-"*160)
    for idx, row in df.iterrows():
        entity = row['Entity']
        portfolio = row['Portfolio']
        glossary_type = str(row.get('glossary_type', 'none')).strip().lower()
        url1 = str(row.get('glossary_url1', '')).strip()
        url2 = str(row.get('glossary_url2', '')).strip()
        # Find output for this agency
        agency_block = [l for l in output_lines if l.startswith(f"Agency: {entity}")]
        if agency_block:
            start_idx = output_lines.index(agency_block[0])
            end_idx = start_idx + 1
            while end_idx < len(output_lines) and not output_lines[end_idx].startswith('Agency:'):
                end_idx += 1
            block_lines = output_lines[start_idx:end_idx]
            term_lines = [l for l in block_lines if l.strip().startswith('[')]
            num_terms = len(term_lines)
            methods = set()
            for l in term_lines:
                m = re.match(r'\s*\[(\w+)\]', l)
                if m:
                    methods.add(m.group(1))
            methods_str = ','.join(sorted(methods)) if methods else '-'
        else:
            num_terms = 0
            methods_str = '-'
        # Compose URLs (full, not truncated)
        if glossary_type == 'both':
            url_str = f"{url1} | {url2}" if url2 else url1
        else:
            url_str = url1
        print("{:<40} | {:<10} | {:<4} | {:<5} | {}".format(
            entity[:40], glossary_type, num_terms, methods_str, portfolio[:30]))
        print(f"    Glossary URL(s): {url_str}")

if __name__ == "__main__":
    main()