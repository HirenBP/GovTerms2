import requests
import pandas as pd
import os
from dotenv import load_dotenv
from collections import defaultdict
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

# -------------------------------------------------------------------
# The following API is used by transparency.gov.au to power its search.
# We discovered it by inspecting the browser's network activity:
# - Open the publications page in Chrome
# - Use DevTools > Network > XHR
# - Look for a POST request to `search.windows.net`
# - Right-click > Copy as cURL
# - Extract `api-key` and request body from the cURL command
#
# This is an Azure Cognitive Search endpoint used to fetch structured
# report metadata like titles, years, and slugs (used to build URLs).
# -------------------------------------------------------------------

def fetch_api_batch(api_url, headers, payload):
    try:
        response = requests.post(api_url, headers=headers, json=payload)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logging.warning(f"Failed to fetch batch at skip={payload.get('skip', 0)}: {e}")
        return None

def main():
    # Set env variables
    load_dotenv()
    API_URL = os.getenv("API_URL")
    API_KEY = os.getenv("API_KEY")
    NUMBER_OF_URLS = 0
    if not API_URL or not API_KEY:
        raise ValueError("API_URL or API_KEY environment variable is not set or loaded.")
    HEADERS = {
        "Content-Type": "application/json",
        "api-key": API_KEY,
        "Accept": "application/json"
    }
    payload_template = {
        "search": "*",
        "highlight": "Content",
        "searchMode": "all",
        "orderby": "ReportingYear desc,ContentType,Entity",
        "top": 1000,
        "skip": 0,
        "count": True,
        "queryType": "simple"
    }
    all_results = []
    batch_size = 1000
    # Initial API request
    json_data = fetch_api_batch(API_URL, HEADERS, payload_template)
    if not json_data:
        logging.error("Failed to fetch initial batch. Exiting.")
        return
    total_count = json_data.get('@odata.count', 0)
    all_results.extend(json_data.get('value', []))
    # Pagination
    for skip in range(batch_size, total_count, batch_size):
        payload_template["skip"] = skip
        batch_data = fetch_api_batch(API_URL, HEADERS, payload_template)
        if batch_data:
            all_results.extend(batch_data.get('value', []))
        logging.info(f"Fetched {len(all_results)} records so far...")
    # Read the list of all agencies from the annual reports CSV
    all_agencies_df = pd.read_csv(r'data\output\ANUAL_REPORTS_FINAL.csv', dtype=str)
    all_agencies = set(all_agencies_df['Entity'].str.strip())
    BASE_URL = "https://www.transparency.gov.au/publications"
    keywords = ["glossary", "acronym", "abbreviation", "shortened terms", "shorterned"]
    matching_entries = []
    def safe_url_join(*parts):
        url = "/".join(part.strip("/") for part in parts if part)
        url = url.replace("https:/", "https://")
        return url
    for r in all_results:
        if r.get("ReportingYear") == "2023-24":
            section_title = (r.get("SectionTitle") or "").lower()
            if any(k in section_title for k in keywords):
                portfolio = r.get("PortfolioUrlSlug")
                entity_slug = r.get("EntityUrlSlug")
                tail = r.get("UrlSlug")
                if portfolio and entity_slug and tail:
                    url = safe_url_join(BASE_URL, portfolio, entity_slug, tail)
                    matching_entries.append([r.get("Portfolio"), r.get("Entity"), r.get("BodyType"), url])
    df = pd.DataFrame(matching_entries, columns=["Portfolio","Entity","BodyType","Url"])
    logging.info(f'{len(matching_entries)} number of glossary urls extracted and saved')
    # Aggregate URLs per Entity
    entity_url_map = defaultdict(list)
    entity_portfolio = {}
    entity_bodytype = {}
    for entry in matching_entries:
        portfolio, entity, bodytype, url = entry
        key = entity.strip() if entity else ''
        if key:
            entity_url_map[key].append(url)
            entity_portfolio[key] = portfolio
            entity_bodytype[key] = bodytype
    max_urls = max((len(urls) for urls in entity_url_map.values()), default=1)
    columns = ["Portfolio", "Entity", "BodyType"] + [f"url{i+1}" for i in range(max_urls)]
    rows = []
    for entity, urls in entity_url_map.items():
        row = [entity_portfolio[entity], entity, entity_bodytype[entity]] + urls
        row += [''] * (max_urls - len(urls))
        rows.append(row)
    os.makedirs(os.path.dirname(r'data/output/GLOSSARY_FINAL.csv'), exist_ok=True)
    agg_df = pd.DataFrame(rows, columns=columns)
    output_path = r'data/output/GLOSSARY_FINAL.csv'
    agg_df.to_csv(output_path, index=False)
    logging.info(f'Aggregated glossary/acronym URLs written to {output_path}')
    agencies_with_keyword = set([entry[1].strip() for entry in matching_entries if entry[1]])
    agencies_without_keyword = all_agencies - agencies_with_keyword
    logging.info(f"\nSummary out of {len(all_agencies)} agencies:")
    logging.info(f"- {len(agencies_with_keyword)} have at least one SectionTitle keyword match (glossary/acronym/abbreviation)")
    logging.info(f"- {len(agencies_without_keyword)} have no SectionTitle keyword match")
    output_path = r'data/output/GLOSSARY_FINAL2.csv'
    df.to_csv(output_path, index=False)
    logging.info(f'Filtered glossary/acronym URLs written to {output_path}')

if __name__ == "__main__":
    main()