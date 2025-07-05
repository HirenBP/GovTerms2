import requests
import pandas as pd
import os
from dotenv import load_dotenv
from collections import defaultdict

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

# Set env variables
load_dotenv()

API_URL = os.getenv("API_URL")
API_KEY = os.getenv("API_KEY")
NUMBER_OF_URLS = 0 # Counter to keep track of the URLs constructed.

# HTTP header required for the API request.
HEADERS = {
    "Content-Type": "application/json",
    "api-key": API_KEY,
    "Accept": "application/json"
}

# Template for the API request payload
payload_template = {
    "search": "*",  # Search query (wildcard to fetch all results)
    "highlight": "Content",  # Field to highlight in the search results
    "searchMode": "all",  # Search mode (all terms must match)
    "orderby": "ReportingYear desc,ContentType,Entity",  # Sorting order
    "top": 10000,  # Number of results to fetch per batch
    "skip": 0,  # Number of results to skip (used for pagination)
    "count": True,  # Include the total count of results
    "queryType": "simple"  # Query type (simple query syntax)
}

all_results = [] # List to store all fetched results.
batch_size = 1000 # Number of records to fetch per batch.

# Initial API request to fetch the first batch of results.
response = requests.post(API_URL, headers=HEADERS, json=payload_template) # Send POST request to the API.
json_data = response.json() # Parse JSON response
total_count = json_data.get('@odata.count', 0) # Get the total number of results.
all_results.extend(json_data.get('value', [])) # Add the fetched results to the list.
if not API_URL or not API_KEY:
    raise ValueError("API_URL or API_KEY environment variable is not set or loaded.")
# Pagination: Fetch additional batches of results if total_count exceeds batch_size
for skip in range(batch_size, total_count, batch_size):
    payload_template["skip"] = skip  # Update the `skip` parameter for pagination
    response = requests.post(API_URL, headers=HEADERS, json=payload_template)  # Send POST request for the next batch
    if response.status_code == 200:  # Check if the request was successful
        all_results.extend(response.json().get('value', []))  # Add the fetched results to the list
    else:
        print(f"⚠️ Failed to fetch batch at skip={skip}")  # Log an error if the request fails
    print(f"🔄 Fetched {len(all_results)} records so far...")  # Log the progress

# Read the list of all agencies from the annual reports CSV
all_agencies_df = pd.read_csv('data/output/annual_reports_2023-24.csv')
all_agencies = set(all_agencies_df['Entity'].str.strip())

BASE_URL = "https://www.transparency.gov.au/publications"
keywords = ["glossary", "acronym", "abbreviation", "shortened terms", "shorterned"]
matching_entries = []

# Filter + construct URLs
for r in all_results:
    if r.get("ReportingYear") == "2023-24":
        section_title = (r.get("SectionTitle") or "").lower()
        if any(k in section_title for k in keywords):
            portfolio = r.get("PortfolioUrlSlug")
            entity_slug = r.get("EntityUrlSlug")
            tail = r.get("UrlSlug")
            if portfolio and entity_slug and tail:
                url = f"{BASE_URL}/{portfolio}/{entity_slug}/{tail}".replace("//", "/")
                url = url.replace("https:/", "https://")
                matching_entries.append([r.get("Portfolio"), r.get("Entity"), r.get("BodyType"), url])
df = pd.DataFrame(matching_entries, columns=["Portfolio","Entity","BodyType","Url"])
print(f'{len(matching_entries)} number of glossary urls extracted and saved')

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

# Prepare rows for CSV: one row per Entity, with url1, url2, ...
max_urls = max((len(urls) for urls in entity_url_map.values()), default=1)
columns = ["Portfolio", "Entity", "BodyType"] + [f"url{i+1}" for i in range(max_urls)]
rows = []
for entity, urls in entity_url_map.items():
    row = [entity_portfolio[entity], entity, entity_bodytype[entity]] + urls
    # Pad with empty strings if fewer than max_urls
    row += [''] * (max_urls - len(urls))
    rows.append(row)

agg_df = pd.DataFrame(rows, columns=columns)
output_path = 'data/output/glossary_sectiontitle_keyword_urls_agg.csv'
agg_df.to_csv(output_path, index=False)
print(f'Aggregated glossary/acronym URLs written to {output_path}')

# --- Updated Summary Section ---
# Agencies with at least one SectionTitle keyword match
agencies_with_keyword = set([entry[1].strip() for entry in matching_entries if entry[1]])
agencies_without_keyword = all_agencies - agencies_with_keyword

print(f"\nSummary out of {len(all_agencies)} agencies:")
print(f"- {len(agencies_with_keyword)} have at least one SectionTitle keyword match (glossary/acronym/abbreviation)")
print(f"- {len(agencies_without_keyword)} have no SectionTitle keyword match")

# Optionally, print lists for inspection
#print(f"Agencies with keyword match: {sorted(agencies_with_keyword)}")
#print(f"Agencies without keyword match: {sorted(agencies_without_keyword)}")

# Save the filtered results
output_path = 'data/output/glossary_sectiontitle_keyword_urls2.csv'
df.to_csv(output_path, index=False)
print(f'Filtered glossary/acronym URLs written to {output_path}')
