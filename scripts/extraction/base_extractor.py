import re
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

from .extractors import glossary_in_table, glossary_in_list, glossary_in_paragraph

class SmartGlossaryExtractor:
    def setup_driver(self) -> webdriver.Chrome:
        options = webdriver.ChromeOptions()
        options.add_argument("--headless")
        return webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    def extract_from_url(self, url: str) -> dict:
        driver = self.setup_driver()
        try:
            driver.get(url)
            WebDriverWait(driver, 30).until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, "div.AnnualReportArticle_articleContent__eheNu")
                )
            )
            element = driver.find_element(By.CLASS_NAME, "AnnualReportArticle_articleContent__eheNu")
            soup = BeautifulSoup(element.get_attribute("outerHTML"), "html.parser")
            return self.smart_extract_glossary(soup)
        except Exception as e:
            print(f"[ERROR] Error occurred: {e}")
            return {}
        finally:
            driver.quit()

    def smart_extract_glossary(self, soup) -> dict:
        glossary_data = {}
        sources = {}
        for table in soup.find_all("table"):
            extracted = glossary_in_table(table)
            if extracted:
                for k in extracted:
                    sources[k] = "table"
                glossary_data.update(extracted)
        if glossary_data:
            return {"glossary": glossary_data, "sources": sources}

        for ul in soup.find_all(["ul", "ol"]):
            extracted = glossary_in_list(ul)
            if extracted:
                for k in extracted:
                    sources[k] = "list"
                glossary_data.update(extracted)
        if glossary_data:
            return {"glossary": glossary_data, "sources": sources}

        paragraphs = soup.find_all("p")
        if paragraphs:
            extracted = glossary_in_paragraph(paragraphs)
            if extracted:
                for k in extracted:
                    sources[k] = "paragraph"
                glossary_data.update(extracted)
        return {"glossary": glossary_data, "sources": sources}

    def extract_with_fallback(self, url: str) -> dict:
        result = self.extract_from_url(url)
        if result.get("glossary"):
            result["used_url"] = url
            result["fallback"] = False
            return result
        cleaned_url = re.sub(r"-{2,}", "-", url)
        if cleaned_url != url:
            fallback_result = self.extract_from_url(cleaned_url)
            if fallback_result.get("glossary"):
                fallback_result["used_url"] = cleaned_url
                fallback_result["fallback"] = True
                return fallback_result
        result["used_url"] = url
        result["fallback"] = False
        return result
