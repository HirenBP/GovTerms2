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

# Pagination: Fetch additional batches of results if total_count exceeds batch_size
for skip in range(batch_size, total_count, batch_size):
    payload_template["skip"] = skip  # Update the `skip` parameter for pagination
    response = requests.post(API_URL, headers=HEADERS, json=payload_template)  # Send POST request for the next batch
    if response.status_code == 200:  # Check if the request was successful
        all_results.extend(response.json().get('value', []))  # Add the fetched results to the list
    else:
        print(f"⚠️ Failed to fetch batch at skip={skip}")  # Log an error if the request fails
    print(f"🔄 Fetched {len(all_results)} records so far...")  # Log the progress

BASE_URL = "https://www.transparency.gov.au/publications"
keywords = ["glossary", "acronym", "abbreviation"]
matching_entries = []

# Filter + construct URLs
for r in all_results:
    if r.get("ReportingYear") == "2023-24":
        slug = r.get("UrlSlug", "").lower()
        title = r.get("Title", "").lower()

        if any(k in slug for k in keywords) or any(k in title for k in keywords):
            portfolio = r.get("PortfolioUrlSlug")
            entity = r.get("EntityUrlSlug")
            tail = r.get("UrlSlug")

            if portfolio and entity and tail:
                url = f"{BASE_URL}/{portfolio}/{entity}/{tail}".replace("//", "/")
                url.replace("https:/", "https://")
                matching_entries.append([r.get("Portfolio"),r.get("Entity"),r.get("BodyType"),url])
df = pd.DataFrame(matching_entries, columns=["Portfolio","Entity","BodyType","Url"])
print(f'{len(matching_entries)} number of glossary urls extracted and saved')
df.to_csv(r"C:\Users\hiren\PycharmProjects\GovTerms2\data\output\glossary_urls.csv",columns=["Portfolio","Entity", "BodyType", "Url"] ,index=False)