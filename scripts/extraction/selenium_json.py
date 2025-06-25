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
import traceback
import re

SKIP_WORDS = {
    "acronym",
    "meaning",
    "term, acronym or abbreviation",
    "description or complete term",
    "copy link",
    "glossary"
}

def format_glossary_line(line):
    """
    Formats a glossary line by replacing multiple spaces or non-breaking spaces with a colon.
    """
    line = line.replace('\xa0', ' ')
    new_line = re.sub(r'\s{2,}', ': ', line, count=1)
    if new_line == line:
        parts = line.split(' ', 1)
        if len(parts) == 2:
            new_line = f"{parts[0]}: {parts[1]}"
    return new_line

def glossary_in_list(list_tag):
    glossary_dict = {}
    for li in list_tag.find_all("li"):
        text = li.get_text(" ", strip=True)
        text = text.replace('\xa0', ' ')
        if len(text) == 1 or text.lower() in SKIP_WORDS:
            continue
        # Try splitting by colon, dash, or multiple spaces
        if ':' in text:
            parts = text.split(':', 1)
        elif ' - ' in text:
            parts = text.split(' - ', 1)
        else:
            parts = re.split(r'\s{3,}', text, maxsplit=1)
        if len(parts) == 2:
            term, definition = parts[0].strip(), parts[1].strip()
            if term.lower() in SKIP_WORDS or definition.lower() in SKIP_WORDS:
                continue
            glossary_dict[term] = definition
    return glossary_dict

def glossary_in_table(table):
    glossary_dict = {}
    for row in table.find_all("tr"):
        cells = row.find_all(["td", "th"])
        cell_texts = [cell.get_text(" ", strip=True).replace('\xa0', ' ') for cell in cells]
        # Skip header or unwanted rows
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

def glossary_in_paragraph(paragraphs):
    glossary_dict = {}
    for p in paragraphs:
        # Handle <strong> tags
        strong = p.find("strong")
        text = p.get_text(" ", strip=True).replace('\xa0', ' ')
        if len(text) == 1 or text.lower() in SKIP_WORDS:
            continue
        if strong:
            abbr = strong.get_text(" ", strip=True)
            rest = text.replace(abbr, "", 1).strip()
            if not rest:
                if abbr.lower() not in SKIP_WORDS and len(abbr) > 1:
                    glossary_dict[abbr] = ""
            else:
                if abbr.lower() not in SKIP_WORDS and rest.lower() not in SKIP_WORDS and len(abbr) > 1:
                    glossary_dict[abbr] = rest
        else:
            # Try splitting by multiple spaces or colon
            parts = re.split(r'\s{3,}', text, maxsplit=1)
            if len(parts) == 2:
                term, definition = parts[0].strip(), parts[1].strip()
                if term.lower() in SKIP_WORDS or definition.lower() in SKIP_WORDS or len(term) == 1:
                    continue
                glossary_dict[term] = definition
            else:
                # Try splitting by colon
                parts = text.split(':', 1)
                if len(parts) == 2:
                    term, definition = parts[0].strip(), parts[1].strip()
                    if term.lower() in SKIP_WORDS or definition.lower() in SKIP_WORDS or len(term) == 1:
                        continue
                    glossary_dict[term] = definition
    return glossary_dict


def prepare_urls(csv_path):
    df = pd.read_csv(csv_path)
    filtered_df = df[df['Type of Glossary'].notnull()]
    urls = {}
    for _, row in filtered_df.iterrows():
        portfolio = row['Portfolio']
        entity = row['Entity']
        entity_website = row.get('Entity Website', '')
        glossary_url = row['Glossary Url']
        if isinstance(glossary_url, str):
            glossary_url = glossary_url.replace('https:/', 'https://')
        urls[(portfolio, entity)] = {
            "Entity Website": entity_website,
            "Glossary Url": glossary_url
        }
    return urls

class GlossaryExtractor:
    def __init__(self):
        pass

    def setup_driver(self):
        options = webdriver.ChromeOptions()
        options.add_argument("--headless")
        return webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    def extract_from_url(self, url):
        driver = self.setup_driver()
        try:
            driver.get(url)
            WebDriverWait(driver, 30).until(
                EC.presence_of_element_located((
                    By.CSS_SELECTOR, 
                    "div.AnnualReportArticle_articleContent__eheNu table, "
                    "div.AnnualReportArticle_articleContent__eheNu p, "
                    "div.AnnualReportArticle_articleContent__eheNu strong"
                ))
            )
            soup = BeautifulSoup(driver.page_source, "html.parser")
            glossary_div = soup.find("div", class_="AnnualReportArticle_articleContent__eheNu")
            return self.extract_glossary_lines(glossary_div)
        except Exception as e:
            print(f"Error occurred: {e}")
            return {}
        finally:
            driver.quit()

    def extract_glossary_lines(self, glossary_div):
        if not glossary_div:
            return {}
        table = glossary_div.find("table")
        if table:
            return {"glossary": glossary_in_table(table)}
        paragraphs = glossary_div.find_all("p")
        if paragraphs:
            return {"glossary": glossary_in_paragraph(paragraphs)}
        list_tag = glossary_div.find(["ul", "ol"])
        if list_tag:
            return {"glossary": glossary_in_list(list_tag)}
        return {}
import random

def main():
    output_json = r'C:\Users\hiren\PycharmProjects\GovTerms2\data\individual_results.json'
    urls = prepare_urls(r'C:\Users\hiren\PycharmProjects\GovTerms2\data\output\combined_for_scrapping.csv')
    extractor = GlossaryExtractor()
    output_data = []

    used_ids = set()

    def generate_id():
        while True:
            term_id = str(random.randint(10000, 99999))
            if term_id not in used_ids:
                used_ids.add(term_id)
                return term_id

    for (portfolio, entity), meta in urls.items():
        print(f"Processing: {portfolio} - {entity}")
        glossary_details = extractor.extract_from_url(meta["Glossary Url"])
        glossary = glossary_details.get("glossary", {})
        for term, definition in glossary.items():
            output_data.append({
                "term_id": generate_id(),
                "term": term,
                "definition": definition,
                "entity": entity,
                "source_url": meta["Glossary Url"]
            })
        time.sleep(2)

    with open(output_json, "w", encoding="utf-8") as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    main()