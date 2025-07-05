import requests
import os
from dotenv import load_dotenv
import json

# Load environment variables
load_dotenv()

API_URL = os.getenv("API_URL")
API_KEY = os.getenv("API_KEY")

HEADERS = {
    "Content-Type": "application/json",
    "api-key": API_KEY,
    "Accept": "application/json"
}

payload = {
    "search": "*",
    "highlight": "Content",
    "searchMode": "all",
    "orderby": "ReportingYear desc,ContentType,Entity",
    "top": 1000,  # Fetch in batches of 1000
    "skip": 0,
    "count": True,
    "queryType": "simple"
}

if not API_URL or not API_KEY:
    raise ValueError("API_URL or API_KEY environment variable is not set or loaded.")

all_results = []
batch_size = 1000

# Initial request
response = requests.post(API_URL, headers=HEADERS, json=payload)
if response.status_code != 200:
    print(f"API request failed with status code {response.status_code}")
    print(response.text)
    exit(1)

data = response.json()
total_count = data.get('@odata.count', 0)
all_results.extend(data.get('value', []))

# Pagination
for skip in range(batch_size, total_count, batch_size):
    payload["skip"] = skip
    response = requests.post(API_URL, headers=HEADERS, json=payload)
    if response.status_code == 200:
        all_results.extend(response.json().get('value', []))
        print(f"Fetched {len(all_results)} records so far...")
    else:
        print(f"Failed to fetch batch at skip={skip}")
        print(response.text)
        break

# Filter for 2023-24 records (do not restrict to annual_report)
filtered = [r for r in all_results if r.get("ReportingYear") == "2023-24"]


print("\nFiltered records with SectionTitle containing glossary/acronym/abbreviation/shortened term:")
keywords = ["glossary", "acronym", "abbreviation", "shortened term"]
for record in filtered:
    section = (record.get('SectionTitle') or '').lower()
    if any(k in section for k in keywords):
        print(json.dumps(record, ensure_ascii=False, indent=2))

# Save all records where ReportingYear is 2023-24 and SectionTitle contains a keyword
output_records = []
keywords = ["glossary", "acronym", "abbreviation", "shortened term"]
for record in all_results:
    if record.get("ReportingYear") == "2023-24":
        section = (record.get('SectionTitle') or '').lower()
        if any(k in section for k in keywords):
            output_records.append(record)

with open(r"C:\Users\hiren\PycharmProjects\GovTerms2\data\output\sectiontitle_keyword_records.txt", "w", encoding="utf-8") as file:
    for record in output_records:
        file.write(json.dumps(record, ensure_ascii=False) + "\n")