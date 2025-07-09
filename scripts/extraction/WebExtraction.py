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
        #options.add_argument("--headless")
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

def extract_from_dl(soup):
    # Extracts from <dl> <dt>term</dt><dd>definition</dd> ...
    resuls = {}
    terms = soup.find_all('dt')
    definitions = soup.find_all('dd')
    if terms and definitions:
        for term, definition in zip(terms, definitions):
            resuls[term.get_text(strip=True)] = definition.get_text(strip=True)
    return resuls

def extract_from_ul_li(soup):
    # Extracts from <ul> <li><a>term</a> – definition</li> ...
    resuls = {}
    for ul in soup.find_all('ul'):
        for li in ul.find_all('li'):
            a = li.find('a', class_='glossary-term')
            if a:
                term = a.get_text(strip=True)
                # Remove the <a> tag from li, get the rest as definition
                definition = li.get_text(separator=' ', strip=True)
                # Remove the term from the start and any dash/colon
                definition = definition[len(term):].lstrip(' –:').strip()
                if term and definition:
                    resuls[term] = definition
    return resuls

def main():
    extractor = GlossaryExtractor()
    urls = [
        r'https://www.pmc.gov.au/resources/abbreviations-and-acronyms-groups-or-topics',
        r'https://www.rba.gov.au/glossary/',
        # Add more URLs as needed
    ]
    all_results = {}
    for url in urls:
        print(f"Extracting from: {url}")
        soup = extractor.extract_from_url(url)
        # Try <dl> first
        dl_results = extract_from_dl(soup)
        for term, definition in dl_results.items():
            all_results[(url, term)] = definition
        # Try <ul><li><a>...</a> – def</li>
        ul_results = extract_from_ul_li(soup)
        for term, definition in ul_results.items():
            all_results[(url, term)] = definition
    # Output to text file
    with open(r'data/output/GlossaryFromWeb.txt', 'w', encoding='utf-8') as f:
        for (url, term), definition in all_results.items():
            f.write(f"[{url}] : {term}: {definition}\n")
    print(f"Extracted {len(all_results)} terms. Output written to GlossaryFromWeb.txt")

if __name__ == "__main__":
    main()