"""
This script extracts glossary details from the site pages and gets output them as json

"""
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
import requests

class GlossaryExtractor():
    def __init__(self):
        pass
        
    def setup_driver(self):
        options = webdriver.ChromeOptions()
        options.add_argument("--disable-gpu")
        options.add_argument("--nosandbox")
        options.add_argument('--start-maximized')

        return webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    def extract_from_url(self, url):
        driver = self.setup_driver()
        try:
            driver.get(url)
            time.sleep(10)

            soup = BeautifulSoup(driver.page_source,'html.parser')
            return soup
        except Exception as e:
            print(f'Error occurred: {e}')
        finally:
            driver.quit()
def extract_terms_and_definitions(soup):
    results = {}

    # 1. Handle <dt>/<dd> pairs
    terms = soup.find_all('dt')
    definitions = soup.find_all('dd')
    if terms and definitions and len(terms) == len(definitions):
        for term, definition in zip(terms, definitions):
            results[term.get_text(strip=True)] = definition.get_text(strip=True)

    # 2. Handle <li> with <a> as term
    for li in soup.find_all('li'):
        a = li.find('a')
        if a:
            term = a.get_text(strip=True)
            a.extract()
            definition = li.get_text(" ", strip=True)
            # Remove leading en dash (–) and whitespace only
            definition = re.sub(r'^\s*–\s*', '', definition)
            if term and definition:
                results[term] = definition

    return results

def main():
    extractor = GlossaryExtractor()
    urls = [
    {"Entity": "Department of the Prime Minister and Cabinet",
    "Url": r'https://www.pmc.gov.au/resources/abbreviations-and-acronyms-groups-or-topics',
    "Portfolio": "Prime Minister and Cabinet",
    "BodyType": "Non-Corporate Commonwealth Entity"},
    {
    "Entity": "Reserve Bank of Australia",
    "Url": r'https://www.rba.gov.au/glossary/',
    "Portfolio": "Treasury",
    "BodyType": "Corporate Commonwealth Entity"
    }
    ]
    output_lines = []
    for info in urls:
        soup = extractor.extract_from_url(info["Url"])
        results = extract_terms_and_definitions(soup)
        num_terms = len(results)
        output_lines.append(f"Portfolio: {info.get('Portfolio','')} | Entity: {info['Entity']} | BodyType: {info.get('BodyType','')} | Number of Terms: {num_terms}")
        output_lines.append(f"Url: {info['Url']}")
        for term, definition in results.items():
            output_lines.append(f"{term}: {definition}")
        output_lines.append("")
    with open("glossary_output.txt", "w", encoding="utf-8") as f:
        for line in output_lines:
            f.write(line + "\n")
    print(f"Glossaries written to glossary_output.txt")

if __name__ == "__main__":
    main()