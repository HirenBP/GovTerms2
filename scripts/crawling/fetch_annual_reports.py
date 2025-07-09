from fetch_results_from_api import API_Extractor
import pandas as pd
extractor = API_Extractor()
results = extractor.extract()
URLS_with_details = []
# Get annual reports and construct urls.
for r in results:
    if r.get("ReportingYear") == "2023-24" and r.get("ContentType") == "annual_report": # Filter for 2023-24 annual reports
        portfolio = r.get("PortfolioUrlSlug") # Extract the portfolio slug
        entity = r.get("EntityUrlSlug") # Extract the entity slug
        slug = r.get("UrlSlug")  # Extract the URL slug (identifer)
        # Construct the full URL for the annual report
        url = f"https://www.transparency.gov.au/publications/{portfolio}/{entity}/{slug}"
        # Append the report details and URL to the list
        URLS_with_details.append([r.get("Portfolio"),r.get("Entity"), r.get("Title"), r.get("BodyType"), url])

#Create a DataFrame from the URLs list and save it as a CSV file.
df2 = pd.DataFrame(URLS_with_details, columns=["Portfolio", "Entity", "Title","BodyType", "URL"])

# df.to_csv("data/output/annual_reports_2023-242.csv", index=False) # Save the DataFrame to a CSV file.
df2.to_csv("data/output/ANNUAL_REPORTS.csv", index=False) # Save the DataFrame to a CSV file. 

print(f'✅ Total URLs fetched: {len(URLS_with_details)}') # Log the total number of URLS fetched.      