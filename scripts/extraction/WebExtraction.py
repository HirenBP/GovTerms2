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



def main():
    extractor = GlossaryExtractor()
    url1 = r'https://www.pmc.gov.au/resources/abbreviations-and-acronyms-groups-or-topics'
    resuls = {}
    
    soup = extractor.extract_from_url(url1)
    terms = soup.find_all('dt')
    definitions = soup.find_all('dd')
    if terms and definitions:
        for term, definition in zip(terms, definitions):
            resuls[term.get_text(strip=True)] = definition.get_text(strip=True)
    else:
        print('Unable to fetch any terms')
    print(len(resuls))

if __name__ == "__main__":
    main()