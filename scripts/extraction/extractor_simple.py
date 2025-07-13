from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
DEFAULT_SKIP_WORDS = {
    "acronym", "meaning", "term", "acronym or abbreviation", "description or complete term", "copy link", "glossary",
    "term", "Description", "term", "description", "definition", "abbreviation", "explanation", "expansion/meaning",
    "specialist term", "acronym/specialist term", "expansion", "explanation/meaning", "term acronym",
    "description / definition", "abbreviation: explanation", "acronym/specialist term: expansion/meaning",
    "term acronym: description / definition","shortened form", "expanded term", "word or phrase", "explanation", "abbreviation / acronym",
    "acronym or abbreviation", "term in full", "acronym/abbreviation", "abbreviation/acronym", "full name", "acronym/ initialism", "acronym/abbreviation",
    "description or term", "abbreviation / acronym", "full form", "item", "term, acronym or abbreviation", "abbreviation or acronym"
}
class SimpleHTMLViewer:
    def __init__(self):
        self.driver = None

    def setup_driver(self):
        options = Options()
        options.add_argument("--headless")
        options.add_argument("--disable-gpu")
        self.driver = webdriver.Chrome(options=options)

    def extract_clean_tag_structure(self, url: str) -> str:
        self.setup_driver()
        try:
            self.driver.get(url)

            WebDriverWait(self.driver, 60).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div.AnnualReportArticle_articleContent__eheNu"))
            )

            def has_content(driver):
                try:
                    div = driver.find_element(By.CSS_SELECTOR, "div.AnnualReportArticle_articleContent__eheNu")
                    return any((
                        div.find_elements(By.TAG_NAME, "table"),
                        div.find_elements(By.TAG_NAME, "td"),
                        div.find_elements(By.TAG_NAME, "th"),
                        div.find_elements(By.TAG_NAME, "p"),
                        div.find_elements(By.TAG_NAME, "span"),
                        div.find_elements(By.TAG_NAME, "ul"),
                        div.find_elements(By.TAG_NAME, "ol"),
                        div.find_elements(By.TAG_NAME, "li"),
                        div.find_elements(By.TAG_NAME, "strong")
                    ))
                except:
                    return False

            WebDriverWait(self.driver, 60).until(has_content)

            element = self.driver.find_element(By.CLASS_NAME, "AnnualReportArticle_articleContent__eheNu")
            raw_html = element.get_attribute("outerHTML")
            soup = BeautifulSoup(raw_html, "html.parser")

            result = []
            # Only pull top-level <td> and <th> text
            # This avoids nested extraction and only grabs the outer text once
            tags = soup.find_all(["td", "th"])
            # Only skip single-letter entries in the first 5 pairs (10 cells)
            for idx, tag in enumerate(tags):
                text = tag.get_text(" ", strip=True)
                # Exact match skip word logic (case-insensitive, stripped)
                text_lower = text.strip().lower()
                is_skip_word = any(text_lower == skip_word.strip().lower() for skip_word in DEFAULT_SKIP_WORDS)
                if not is_skip_word:
                    result.append(text)
            return "\n".join(result)

        finally:
            self.driver.quit()
