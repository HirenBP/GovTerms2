"""Utility module for extracting glossary terms from transparency.gov.au."""
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
from bs4.element import Tag
import re
from typing import Dict, List, Set, Pattern, Optional, Tuple
import os
import logging
import sys

DEFAULT_SKIP_WORDS = {
    "acronym", "meaning", "term, acronym or abbreviation", "description or complete term", "copy link", "glossary",
    "Term", "Description", "term", "description", "definition", "abbreviation", "explanation", "expansion/meaning",
    "specialist term", "acronym/specialist term", "expansion", "explanation/meaning", "term acronym",
    "description / definition", "abbreviation: explanation", "acronym/specialist term: expansion/meaning",
    "term acronym: description / definition",
}

DEFAULT_HEADER_PATTERNS = [
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

# # --- Start of redirection ---
# # Save the original stdout and stderr
# original_stdout = sys.stdout
# original_stderr = sys.stderr

# # Open /dev/null (or equivalent on Windows) for writing
# # 'w' mode is important for creating the file if it doesn't exist (though /dev/null always exists)
# devnull = open(os.devnull, 'w')

# # Redirect stdout and stderr
# sys.stdout = devnull
# sys.stderr = devnull
# # --- End of redirection ---

def get_silent_chrome_driver():
    # 1. Suppress Selenium Python Client Logs
    # This sets the logging level for the selenium library itself
    logging.getLogger('selenium').setLevel(logging.WARNING) # Or logging.ERROR, logging.CRITICAL

    # 2. Configure Chrome Options for Browser-level logs
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")  # Recommended for headless on some systems
    options.add_argument("--no-sandbox")   # Required for running as root in some environments (e.g., Docker)
    options.add_argument("--disable-dev-shm-usage") # Overcomes limited resource problems
    options.add_argument("--log-level=3")  # Suppress Chrome's internal logging (INFO, WARNING, ERROR messages)
    options.add_experimental_option("excludeSwitches", ["enable-logging"]) # Disable default logging to console

    # 3. Configure ChromeDriver Service for ChromeDriver logs
    # Redirect ChromeDriver's stdout and stderr to os.devnull
    service = Service(log_path=os.devnull)

    # You can also try setting an environment variable for ChromeDriver
    # os.environ['WDM_LOG_LEVEL'] = '0' # For webdriver-manager logs, if you're using it

    try:
        driver = webdriver.Chrome(service=service, options=options)
        return driver
    except Exception as e:
        print(f"Error initializing WebDriver: {e}")
        # Potentially log the error to a file if you want to debug without terminal output
        return None


def is_header_row(term: str, definition: str, SKIP_WORDS: set, HEADER_PATTERNS: list) -> bool:
    t = term.strip().lower()
    d = definition.strip().lower()
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

def glossary_in_list(list_tag: Tag, SKIP_WORDS: Set[str], HEADER_PATTERNS: List[Pattern]) -> Dict[str, str]:
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
            if is_header_row(term, definition, SKIP_WORDS, HEADER_PATTERNS):
                continue
            glossary_dict[term] = definition
    return glossary_dict

def glossary_in_table(table: Tag, SKIP_WORDS: Set[str], HEADER_PATTERNS: List[Pattern]) -> Dict[str, str]:
    glossary_dict = {}

    for row in table.find_all("tr"):
        cells = row.find_all(["td", "th"])

        # Use smarter nested tag parsing per cell
        cell_texts = []
        for cell in cells:
            parts = cell.find_all(["p", "span"])
            if parts:
                combined = " ".join(part.get_text(" ", strip=True) for part in parts if part.get_text(strip=True))
            else:
                combined = cell.get_text(" ", strip=True)
            cell_texts.append(combined.replace('\xa0', ' ').strip())

        # Handle rows with even number of cells (e.g., 2, 4, 6...)
        if len(cell_texts) >= 2 and len(cell_texts) % 2 == 0:
            for i in range(0, len(cell_texts), 2):
                term, definition = cell_texts[i], cell_texts[i + 1]
                if len(term) == 1 or is_header_row(term, definition, SKIP_WORDS, HEADER_PATTERNS):
                    continue
                glossary_dict[term] = definition

        # Fallback: 1-cell rows like 'Term: Definition'
        elif len(cell_texts) == 1:
            line = format_glossary_line(cell_texts[0])
            parts = line.split(':', 1)
            if len(parts) == 2:
                term, definition = parts[0].strip(), parts[1].strip()
                if len(term) == 1 or is_header_row(term, definition, SKIP_WORDS, HEADER_PATTERNS):
                    continue
                glossary_dict[term] = definition

    return glossary_dict


def extract_term_definition_from_strong_paragraph(paragraphs, i, SKIP_WORDS):
    """
    Helper to extract a (term, definition) pair from a <p> with <strong> or <b> tag, possibly using the next <p> as the definition.
    Returns (term, definition, new_index) or (None, None, i+1) if not found.
    """
    p = paragraphs[i]
    strong = p.find("strong") or p.find("b")
    text = p.get_text(" ", strip=True).replace('\xa0', ' ')
    abbr = strong.get_text(" ", strip=True)
    rest = text.replace(abbr, "", 1).strip()
    # Handle <p><strong>TERM</strong> – definition</p> and <p><strong>TERM</strong>: definition</p>
    if rest:
        # Remove leading dash, en dash, colon, or whitespace
        rest = re.sub(r'^[\s\-–:]+', '', rest)
        if abbr.lower() not in SKIP_WORDS and len(abbr) > 1:
            return abbr, rest, i + 1
    # If this <p> is just the term, and next <p> is definition
    if not rest and (i + 1) < len(paragraphs):
        next_p = paragraphs[i + 1]
        next_text = next_p.get_text(" ", strip=True).replace('\xa0', ' ')
        next_strong = next_p.find("strong") or next_p.find("b")
        if next_text and not next_strong and next_text.lower() not in SKIP_WORDS:
            definition = re.sub(r'^\s*:+\s*', '', next_text)
            definition = re.sub(r'^:+', ':', definition)
            return abbr, definition, i + 2
    return None, None, i + 1

def extract_term_definition_from_plain_paragraph(text, SKIP_WORDS):
    """
    Helper to extract a (term, definition) pair from a plain <p> tag using various splitting strategies.
    Returns (term, definition) or (None, None) if not found.
    """
    # Try splitting by 3+ spaces first
    parts = re.split(r'\s{3,}', text, maxsplit=1)
    if len(parts) == 2:
        return parts[0].strip(), parts[1].strip()
    # Try splitting by colon
    parts = text.split(':', 1)
    if len(parts) == 2:
        return parts[0].strip(), parts[1].strip()
    # Try splitting by en dash (–) only if surrounded by spaces
    parts = re.split(r'\s+–\s+', text, maxsplit=1)
    if len(parts) == 2:
        return parts[0].strip(), parts[1].strip()
    # Try splitting by single space (for <p>TERM DEFINITION</p> with no punctuation)
    parts = text.split(' ', 1)
    if len(parts) == 2 and len(parts[0]) > 1 and len(parts[1]) > 1:
        return parts[0].strip(), parts[1].strip()
    return None, None

def glossary_in_paragraph(
    paragraphs: List[Tag], SKIP_WORDS: Set[str], HEADER_PATTERNS: List[Pattern]
) -> Dict[str, str]:
    """
    Extract glossary terms and definitions from a list of <p> tags.
    Handles paragraphs with <strong>/<b> tags as terms, and various splitting strategies for plain paragraphs.
    Returns a dictionary of term: definition pairs.
    """
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
            # Try to extract from <strong>/<b> paragraph
            term, definition, new_i = extract_term_definition_from_strong_paragraph(paragraphs, i, SKIP_WORDS)
            if term and definition and not is_header_row(term, definition, SKIP_WORDS, HEADER_PATTERNS):
                glossary_dict[term] = definition
                i = new_i
                continue
            # If <p><strong>TERM</strong></p> and next <p> is definition
            if not definition and (i + 1) < len(paragraphs):
                next_p = paragraphs[i + 1]
                next_text = next_p.get_text(" ", strip=True).replace('\xa0', ' ')
                next_strong = next_p.find("strong") or next_p.find("b")
                if next_text and not next_strong and next_text.lower() not in SKIP_WORDS:
                    if not is_header_row(term, next_text, SKIP_WORDS, HEADER_PATTERNS):
                        glossary_dict[term] = next_text
                        i += 2
                        continue
        else:
            # Try to extract from plain paragraph
            term, definition = extract_term_definition_from_plain_paragraph(text, SKIP_WORDS)
            if term and definition and not is_header_row(term, definition, SKIP_WORDS, HEADER_PATTERNS) and len(term) > 1:
                definition = re.sub(r'^\s*:+\s*', '', definition)
                definition = re.sub(r'^:+', ':', definition)
                glossary_dict[term] = definition
                i += 1
                continue
        i += 1
    return glossary_dict

class GlossaryExtractor:
    """
    Extracts glossary terms and definitions from transparency.gov.au annual report pages.
    Uses Selenium to load the page and BeautifulSoup to parse the content.
    Provides methods to extract from tables, lists, and paragraphs.
    """
    def __init__(
        self,
        skip_words: Optional[Set[str]] = None,
        header_patterns: Optional[List[Pattern]] = None
    ):
        """
        Initializes the GlossaryExtractor.
        Args:
            skip_words (Optional[Set[str]]): Custom set of words to skip. If None, uses default.
            header_patterns (Optional[List[Pattern]]): Custom header patterns. If None, uses default.
        """
        self.SKIP_WORDS = skip_words if skip_words is not None else DEFAULT_SKIP_WORDS
        self.HEADER_PATTERNS = header_patterns if header_patterns is not None else DEFAULT_HEADER_PATTERNS

    def setup_driver(self) -> webdriver.Chrome:
        driver = get_silent_chrome_driver()
        return driver
    def extract_from_url(self, url: str) -> dict:
        """
        Loads the given URL, waits for the main content div, and extracts glossary data.
        Args:
            url (str): The URL to extract from.
        Returns:
            dict: A dictionary with 'glossary' and 'sources' keys.
        """
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

    def smart_extract_glossary(self, soup: BeautifulSoup) -> dict:
        """
        Attempts to extract glossary data from the parsed HTML using tables, lists, then paragraphs.
        Args:
            soup (BeautifulSoup): Parsed HTML soup.
        Returns:
            dict: A dictionary with 'glossary' and 'sources' keys.
        """
        glossary_data: Dict[str, str] = {}
        extraction_sources: Dict[str, str] = {}
        tables = soup.find_all("table")
        if tables:
            for table in tables:
                extracted = glossary_in_table(table, self.SKIP_WORDS, self.HEADER_PATTERNS)
                if extracted:
                    for k in extracted:
                        extraction_sources[k] = 'table'
                    glossary_data.update(extracted)
            return {"glossary": glossary_data, "sources": extraction_sources}
        lists = soup.find_all(["ul", "ol"])
        if lists:
            for ul in lists:
                extracted = glossary_in_list(ul, self.SKIP_WORDS, self.HEADER_PATTERNS)
                if extracted:
                    for k in extracted:
                        extraction_sources[k] = 'list'
                    glossary_data.update(extracted)
            return {"glossary": glossary_data, "sources": extraction_sources}
        paragraphs = soup.find_all("p")
        if paragraphs:
            extracted = glossary_in_paragraph(paragraphs, self.SKIP_WORDS, self.HEADER_PATTERNS)
            if extracted:
                for k in extracted:
                    extraction_sources[k] = 'paragraph'
                glossary_data.update(extracted)
        return {"glossary": glossary_data, "sources": extraction_sources}

    def _extract_table_pairs(self, table):
        """Extracts glossary pairs from a two-column table where each cell contains multiple terms/definitions."""
        results = []
        for row in table.find_all("tr"):
            tds = row.find_all("td")
            if len(tds) == 2:
                terms = self._extract_texts_from_td(tds[0])
                definitions = self._extract_texts_from_td(tds[1])
                # Only pair up to the shortest list to avoid IndexError
                for term, definition in zip(terms, definitions):
                    results.append((term, definition))
        return results

    def _extract_texts_from_td(self, td):
        """Helper to extract all terms/definitions from a <td>, splitting on <br> and <p>."""
        texts = []
        for p in td.find_all("p"):
            for part in p.decode_contents().split("<br>"):
                clean = BeautifulSoup(part, "html.parser").get_text(strip=True)
                if clean:
                    texts.append(clean)
        return texts

    def extract_standard_glossary(self, soup):
        """
        Attempts to extract glossary terms and definitions from common HTML patterns:
        - <dt>/<dd> pairs
        - <tr><td>term</td><td>definition</td></tr>
        Returns a dict of {term: definition} if found, else returns an empty dict.
        """
        glossary_dict = {}
        # 1. Try <dt>/<dd> pairs
        dts = soup.find_all("dt")
        dds = soup.find_all("dd")
        if dts and dds and len(dts) == len(dds):
            for dt, dd in zip(dts, dds):
                term = dt.get_text(" ", strip=True)
                definition = dd.get_text(" ", strip=True)
                if term and definition and not is_header_row(term, definition, self.SKIP_WORDS, self.HEADER_PATTERNS):
                    glossary_dict[term] = definition
            if glossary_dict:
                return glossary_dict
        # 2. Try <tr><td>term</td><td>definition</td></tr> (but not special two-column tables)
        for table in soup.find_all("table"):
            for row in table.find_all("tr"):
                cells = row.find_all(["td", "th"])
                if len(cells) == 2:
                    term = cells[0].get_text(" ", strip=True)
                    definition = cells[1].get_text(" ", strip=True)
                    if term and definition and not is_header_row(term, definition, self.SKIP_WORDS, self.HEADER_PATTERNS):
                        glossary_dict[term] = definition
        return glossary_dict