import requests
import os
from dotenv import load_dotenv

load_dotenv()
# Usage:
# extractor = API_Extractor()
# results = extractor.extract()
class API_Extractor:
    def __init__(self):
        self.api_url = os.getenv("API_URL")
        self.api_key = os.getenv("API_KEY")
        self.headers = {
            "Content-Type": "application/json",
            "api-key": self.api_key,
            "Accept": "application/json"
        }
        self.payload_template = {
            "search": "*",
            "highlight": "Content",
            "searchMode": "all",
            "orderby": "ReportingYear desc,ContentType,Entity",
            "top": 1000,
            "skip": 0,
            "count": True,
            "queryType": "simple"
        }

    def extract(self):
        all_results = []
        response = requests.post(self.api_url, headers=self.headers, json=self.payload_template)
        json_data = response.json()
        total_count = json_data.get('@odata.count', 0)
        all_results.extend(json_data.get('value', []))

        batch_size = self.payload_template["top"]
        for skip in range(batch_size, total_count, batch_size):
            self.payload_template["skip"] = skip
            response = requests.post(self.api_url, headers=self.headers, json=self.payload_template)
            if response.status_code == 200:
                all_results.extend(response.json().get('value', []))
            else:
                print(f"⚠️ Failed to fetch batch at skip={skip}")
            print(f"🔄 Fetched {len(all_results)} records so far...")
        return all_results

