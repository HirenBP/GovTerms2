import requests
import pandas as pd
import os
from dotenv import load_dotenv

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
keywords = ["glossary", "acronym", "abbreviation"]
matching_entries = []

# Track which agencies have glossary, acronym/abbreviation, both, or none
agency_glossary_types = {agency: set() for agency in all_agencies}

# Filter + construct URLs
for r in all_results:
    if r.get("ReportingYear") == "2023-24":
        slug = r.get("UrlSlug", "").lower()
        title = r.get("Title", "").lower()
        entity = (r.get("Entity") or "").strip()
        section_title = r.get("SectionTitle")
        article_title = r.get("Title")
        found_types = set()
        if any(k in slug for k in ["glossary"] ) or any(k in title for k in ["glossary"] ):
            found_types.add("glossary")
        if any(k in slug for k in ["acronym", "abbreviation"]) or any(k in title for k in ["acronym", "abbreviation"]):
            found_types.add("acronym_or_abbreviation")
        # Include if (SectionTitle is not None) OR (SectionTitle is None AND Title is not None)
        if found_types and entity in agency_glossary_types and (section_title or (section_title is None and article_title)):
            agency_glossary_types[entity].update(found_types)
            portfolio = r.get("PortfolioUrlSlug")
            entity_slug = r.get("EntityUrlSlug")
            tail = r.get("UrlSlug")
            if portfolio and entity_slug and tail:
                url = f"{BASE_URL}/{portfolio}/{entity_slug}/{tail}".replace("//", "/")
                url = url.replace("https:/", "https://")
                matching_entries.append([r.get("Portfolio"), r.get("Entity"), r.get("BodyType"), url])
df = pd.DataFrame(matching_entries, columns=["Portfolio","Entity","BodyType","Url"])
print(f'{len(matching_entries)} number of glossary urls extracted and saved')

# --- Summary Section ---
only_glossary = [agency for agency, types in agency_glossary_types.items() if types == {"glossary"}]
only_acronym = [agency for agency, types in agency_glossary_types.items() if types == {"acronym_or_abbreviation"}]
both = [agency for agency, types in agency_glossary_types.items() if types == {"glossary", "acronym_or_abbreviation"}]
no_details = [agency for agency, types in agency_glossary_types.items() if not types]

print(f"\nSummary out of {len(all_agencies)} agencies:")
print(f"- {len(only_glossary)} have only glossary details")
print(f"- {len(only_acronym)} have only acronym/abbreviation details")
print(f"- {len(both)} have both glossary and acronym/abbreviation details")
print(f"- {len(no_details)} have no glossary or acronym/abbreviation details")

# Optionally, save the lists to CSV for further analysis
summary_df = pd.DataFrame({
    'Agency': list(all_agencies),
    'GlossaryType': [', '.join(sorted(agency_glossary_types[agency])) if agency_glossary_types[agency] else 'none' for agency in all_agencies]
})
summary_df.to_csv('data/output/glossary_coverage_summary.csv', index=False)

def get_glossary_type_and_urls(entity, matching_entries):
    # Find all glossary URLs for this entity
    urls = [(row[3], row[2]) for row in matching_entries if (row[1] or '').strip() == entity]
    # row[3] = url, row[2] = BodyType
    if not urls:
        return 'none', '', ''
    if len(urls) == 1:
        return 'one', urls[0][0], ''
    # If there are two or more, try to distinguish types
    # If both glossary and acronym/abbreviation exist, return both
    glossary_urls = [u for u, bodytype in urls if any(k in u for k in ['glossary'])]
    acronym_urls = [u for u, bodytype in urls if any(k in u for k in ['acronym', 'abbreviation'])]
    if glossary_urls and acronym_urls:
        return 'both', glossary_urls[0], acronym_urls[0]
    # If all are of one type, just return the first two
    return 'one', urls[0][0], urls[1][0] if len(urls) > 1 else ''

# Read the annual report details file
annual_df = pd.read_csv('data/output/annual_reports_details2.csv')

# Add columns for glossary type and URLs
annual_df['glossary_type'] = ''
annual_df['glossary_url1'] = ''
annual_df['glossary_url2'] = ''

for idx, row in annual_df.iterrows():
    entity = (row['Entity'] or '').strip()
    gtype, url1, url2 = get_glossary_type_and_urls(entity, matching_entries)
    annual_df.at[idx, 'glossary_type'] = gtype
    annual_df.at[idx, 'glossary_url1'] = url1
    annual_df.at[idx, 'glossary_url2'] = url2


annual_df.to_csv('data/output/all_data.csv', index=False)
print('Combined file with glossary types and URLs written to data/output/all_data3.csv')
print(annual_df.head(10))
