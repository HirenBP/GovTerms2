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
import os
import pandas.errors

# Expanded SKIP_WORDS and header patterns
SKIP_WORDS = {
    "acronym", "meaning", "term, acronym or abbreviation", "description or complete term", "copy link", "glossary",
    "Term", "Description", "term", "description", "definition", "abbreviation", "explanation", "expansion/meaning",
    "specialist term", "acronym/specialist term", "expansion", "explanation/meaning", "term acronym",
    "description / definition", "abbreviation: explanation", "acronym/specialist term: expansion/meaning",
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
        if ':' in text:
            parts = text.split(':', 1)
        elif ' - ' in text:
            parts = text.split(' - ', 1)
        else:
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
        if strong:
            abbr = strong.get_text(" ", strip=True)
            rest = text.replace(abbr, "", 1).strip()
            if not rest and (i + 1) < len(paragraphs):
                next_p = paragraphs[i + 1]
                next_text = next_p.get_text(" ", strip=True).replace('\xa0', ' ')
                next_strong = next_p.find("strong") or next_p.find("b")
                if next_text and not next_strong and next_text.lower() not in SKIP_WORDS:
                    definition = re.sub(r'^\s*:+\s*', '', next_text)
                    definition = re.sub(r'^:+', ':', definition)
                    if abbr.lower() not in SKIP_WORDS and len(abbr) > 1 and not is_header_row(abbr, definition):
                        glossary_dict[abbr] = definition
                    i += 2
                    continue
            if abbr.lower() not in SKIP_WORDS and len(abbr) > 1 and not is_header_row(abbr, rest):
                rest = re.sub(r'^\s*:+\s*', '', rest)
                rest = re.sub(r'^:+', ':', rest)
                glossary_dict[abbr] = rest
        else:
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
                parts = text.split(':', 1)
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
            if not main_div:
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
    df = pd.read_csv(r'C:\Users\hiren\PycharmProjects\GovTerms2\data\output\all_data_copy.csv')
    agency_name = input("Enter the agency name (case-insensitive, partial match allowed): ").strip().lower()
    matches = df[df['Entity'].str.lower().str.contains(agency_name)]
    if matches.empty:
        print(f"No agency found matching '{agency_name}'.")
        return
    print(f"Found {len(matches)} matching agency(ies):")
    for idx, row in matches.iterrows():
        print(f"  {row['Entity']} (Portfolio: {row['Portfolio']})")
    if len(matches) > 1:
        agency_full = input("Enter the exact agency name from above: ").strip()
        match_row = matches[matches['Entity'] == agency_full]
        if match_row.empty:
            print(f"No exact match for '{agency_full}'. Exiting.")
            return
        row = match_row.iloc[0]
    else:
        row = matches.iloc[0]
    entity = row['Entity']
    portfolio = row['Portfolio']
    glossary_type = str(row.get('glossary_type', 'none')).strip().lower()
    url1 = str(row.get('glossary_url1', '')).strip()
    url2 = str(row.get('glossary_url2', '')).strip()
    extractor = SmartGlossaryExtractor()
    all_terms = {}
    all_sources = {}
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
                time.sleep(2)
    elif glossary_type == 'one':
        if url1:
            glossary, sources, used_url = try_extract(url1)
            all_terms.update(glossary)
            all_sources.update(sources)
            time.sleep(2)
    print(f"\nAgency: {entity} | Portfolio: {portfolio}")
    if all_terms:
        print(f"Extracted {len(all_terms)} terms:")
        for term, definition in all_terms.items():
            method = all_sources.get(term, 'unknown')
            print(f"  [{method}] {term}: {definition}")
    else:
        print("  No terms extracted.")
    print("\nExtraction log:")
    methods = set(all_sources.values())
    methods_str = ','.join(sorted(methods)) if methods else '-'
    url_str = f"{url1} | {url2}" if glossary_type == 'both' else url1
    print(f"  Agency: {entity}")
    print(f"  Portfolio: {portfolio}")
    print(f"  Glossary Type: {glossary_type}")
    print(f"  Num Terms: {len(all_terms)}")
    print(f"  Methods: {methods_str}")
    print(f"  Glossary URLs: {url_str}")

if __name__ == "__main__":
    main()
