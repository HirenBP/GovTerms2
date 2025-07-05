from bs4 import BeautifulSoup
import re

SKIP_WORDS = {
    "acronym",
    "meaning",
    "term, acronym or abbreviation",
    "description or complete term",
    "copy link",
    "glossary",
    "term",
    "description",
    "definition",
    "Term",
    "Description",
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

def is_header_row(term: str, definition: str) -> bool:
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

def glossary_in_list(list_tag: BeautifulSoup) -> dict:
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

def glossary_in_table(table: BeautifulSoup) -> dict:
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
