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
    "top": 1000,  # Number of results to fetch per batch
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

URLs = [] # List to store the final URLs
print(all_results[0])
for r in all_results:
    if "glossary" in r:
        print("The raw data contains the word glossary")
    if r.get("ReportingYear") == "2023-24" and r.get("ContentType") == "annual_report": # Filter for 2023-24 annual reports
        portfolio = r.get("PortfolioUrlSlug") # Extract the portfolio slug
        entity = r.get("EntityUrlSlug") # Extract the entity slug
        slug = r.get("UrlSlug")  # Extract the URL slug (identifer)

        # Construct the full URL for the annual report
        url = f"https://www.transparency.gov.au/publications/{portfolio}/{entity}/{slug}"
        print(f'{r.get("Entity")} \n {url}')

        # Append the report details and URL to the list
        URLs.append([r.get("Title"), r.get("Portfolio"), r.get("Entity"), url])
        NUMBER_OF_URLS += 1 # Increment the URL counter

# # Ensure the directory exists
# output_dir = "data/output"
# os.makedirs(output_dir, exist_ok=True)  # Create the directory if it doesn't exist

#Create a DataFrame from the URLs list and save it as a CSV file.
df = pd.DataFrame(URLs, columns=["Title", "Portfolio", "Entity", "URL"]) # Create a DataFrame with specified columns.
df.to_csv("data/output/annual_reports_2023-242.csv", index=False) # Save the DataFrame to a CSV file.

print(f'✅ Total URLs fetched: {NUMBER_OF_URLS}') # Log the total number of URLS fetched.
