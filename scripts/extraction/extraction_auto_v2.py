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
import csv
import pandas.errors

# Expanded SKIP_WORDS and header patterns
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
    "definition",
    "abbreviation",
    "explanation",
    "expansion/meaning",
    "specialist term",
    "acronym/specialist term",
    "expansion",
    "explanation/meaning",
    "term acronym",
    "description / definition",
    "abbreviation: explanation",
    "acronym/specialist term: expansion/meaning",
    "term acronym: description / definition",
}

HEADER_PATTERNS = [
    re.compile(r"^term.*acronym.*description.*definition$", re.I),
    re.compile(r"^abbreviation.*explanation$", re.I),
    re.compile(r"^acronym/specialist term.*expansion/meaning$", re.I),
    re.compile(r"^acronym.*expansion$", re.I),
    re.compile(r"^term.*definition$", re.I),
    re.compile(r"^expansion/meaning$", re.I),
    re.compile(r"^expansion$", re.I),
    re.compile(r"^explanation$", re.I),
    re.compile(r"^description / definition$", re.I),
]

def is_header_row(term, definition):
    t = term.strip().lower()
    d = definition.strip().lower()
    if t in SKIP_WORDS or d in SKIP_WORDS:
        return True
    for pat in HEADER_PATTERNS:
        if pat.match(term.strip()) or pat.match(definition.strip()):
            return True
    # Also skip if both are short and contain only words like 'term', 'definition', etc.
    if len(t) < 25 and len(d) < 25 and (t in d or d in t):
        return True
    return False

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
            if is_header_row(term, definition):
                continue
            glossary_dict[term] = definition
    return glossary_dict

def glossary_in_table(table) -> dict:
    glossary_dict = {}
    for row in table.find_all("tr"):
        cells = row.find_all(["td", "th"])
        cell_texts = [cell.get_text(" ", strip=True).replace('\xa0', ' ') for cell in cells]
        if len(cell_texts) >= 2:
            term, definition = cell_texts[0], cell_texts[1]
            if len(term) == 1 or is_header_row(term, definition):
                continue
            glossary_dict[term] = definition
        elif len(cell_texts) == 1:
            line = format_glossary_line(cell_texts[0])
            parts = line.split(':', 1)
            if len(parts) == 2:
                term, definition = parts[0].strip(), parts[1].strip()
                if len(term) == 1 or is_header_row(term, definition):
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
                    if abbr.lower() not in SKIP_WORDS and len(abbr) > 1 and not is_header_row(abbr, definition):
                        glossary_dict[abbr] = definition
                    i += 2
                    continue
            # Otherwise, handle <p><strong>ADF<br>Australian Defence Force.</strong></p>
            if abbr.lower() not in SKIP_WORDS and len(abbr) > 1 and not is_header_row(abbr, rest):
                # Remove leading colon(s) and whitespace from rest
                rest = re.sub(r'^\s*:+\s*', '', rest)
                rest = re.sub(r'^:+', ':', rest)
                glossary_dict[abbr] = rest
        else:
            # Try splitting by 3+ spaces first
            parts = re.split(r'\s{3,}', text, maxsplit=1)
            if len(parts) == 2:
                term, definition = parts[0].strip(), parts[1].strip()
                if is_header_row(term, definition) or len(term) == 1:
                    i += 1
                    continue
                definition = re.sub(r'^\s*:+\s*', '', definition)
                definition = re.sub(r'^:+', ':', definition)
                glossary_dict[term] = definition
            else:
                # Try splitting by colon
                parts = text.split(':', 1)
                if len(parts) == 2:
                    term, definition = parts[0].strip(), parts[1].strip()
                    if is_header_row(term, definition) or len(term) == 1:
                        i += 1
                        continue
                    definition = re.sub(r'^\s*:+\s*', '', definition)
                    definition = re.sub(r'^:+', ':', definition)
                    glossary_dict[term] = definition
                else:
                    # Try splitting by en dash (–) only if surrounded by spaces
                    parts = re.split(r'\s+–\s+', text, maxsplit=1)
                    if len(parts) == 2:
                        term, definition = parts[0].strip(), parts[1].strip()
                        if is_header_row(term, definition) or len(term) == 1:
                            i += 1
                            continue
                        definition = re.sub(r'^\s*:+\s*', '', definition)
                        definition = re.sub(r'^:+', ':', definition)
                        glossary_dict[term] = definition
        i += 1
    return glossary_dict

class SmartGlossaryExtractor:
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
            WebDriverWait(driver, 30).until(
                EC.presence_of_element_located((
                    By.CSS_SELECTOR,
                    "div.AnnualReportArticle_articleContent__eheNu"
                ))
            )
            def glossary_div_has_content(driver):
                try:
                    div = driver.find_element(By.CSS_SELECTOR, "div.AnnualReportArticle_articleContent__eheNu")
                    return (
                        div.find_elements(By.TAG_NAME, "table") or
                        div.find_elements(By.TAG_NAME, "p") or
                        div.find_elements(By.TAG_NAME, "strong")
                    )
                except Exception:
                    return False
            WebDriverWait(driver, 30).until(glossary_div_has_content)
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
        glossary_data = {}
        extraction_sources = {}
        tables = soup.find_all("table")
        if tables:
            for table in tables:
                extracted = glossary_in_table(table)
                if extracted:
                    for k in extracted:
                        extraction_sources[k] = 'table'
                    glossary_data.update(extracted)
            return {"glossary": glossary_data, "sources": extraction_sources}
        lists = soup.find_all(["ul", "ol"])
        if lists:
            for ul in lists:
                extracted = glossary_in_list(ul)
                if extracted:
                    for k in extracted:
                        extraction_sources[k] = 'list'
                    glossary_data.update(extracted)
            return {"glossary": glossary_data, "sources": extraction_sources}
        paragraphs = soup.find_all("p")
        if paragraphs:
            extracted = glossary_in_paragraph(paragraphs)
            if extracted:
                for k in extracted:
                    extraction_sources[k] = 'paragraph'
                glossary_data.update(extracted)
        return {"glossary": glossary_data, "sources": extraction_sources}

def main():
    output_dir = os.path.join('C:', 'Users', 'hiren', 'PycharmProjects', 'GovTerms2', 'data', 'output')
    os.makedirs(output_dir, exist_ok=True)
    df = pd.read_csv(r'C:\Users\hiren\PycharmProjects\GovTerms2\data\output\glossary_sectiontitle_keyword_urls_agg.csv')
    url_columns = [col for col in df.columns if col.startswith('url')]
    extractor = SmartGlossaryExtractor()
    used_ids = set()
    output_lines = []
    log_lines = []
    for idx, row in df.iterrows():
        entity = row['Entity']
        portfolio = row.get('Portfolio', '')
        urls = [str(row[col]).strip() for col in url_columns if pd.notna(row[col]) and str(row[col]).strip()]
        all_terms = {}
        all_sources = {}
        url_used_for_log = None
        for url in urls:
            glossary_details = extractor.extract_from_url(url)
            glossary = glossary_details.get("glossary", {})
            sources = glossary_details.get("sources", {})
            all_terms.update(glossary)
            all_sources.update(sources)
            if url_used_for_log is None:
                url_used_for_log = url
            time.sleep(2)
        output_lines.append(f"Entity: {entity} | Portfolio: {portfolio}\n")
        if all_terms:
            for term, definition in all_terms.items():
                method = all_sources.get(term, 'unknown')
                output_lines.append(f"  [{method}] {term}: {definition}\n")
            output_lines.append("\n")
        else:
            output_lines.append(f"  No terms extracted.\n\n")
        num_terms = len(all_terms)
        if num_terms < 5:
            log_lines.append(f"{entity}\t{num_terms}\t{url_used_for_log if url_used_for_log else ''}\n")
        else:
            log_lines.append(f"{entity}\t{num_terms}\n")
    # Write all output to one text file
    all_output_path = os.path.join(output_dir, "all_glossaries.txt")
    with open(all_output_path, 'w', encoding='utf-8') as f:
        f.writelines(output_lines)
    print(f"[LOG] All glossary extractions written to {all_output_path}")
    # Write log file
    log_output_path = os.path.join(output_dir, "extraction_log.txt")
    with open(log_output_path, 'w', encoding='utf-8') as f:
        f.writelines(log_lines)
    print(f"[LOG] Extraction log written to {log_output_path}")

if __name__ == "__main__":
    main()
