import pandas as pd
import os
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import WebDriverException, TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from pathlib import Path

def check_url(driver, url):
    try:
        driver.get(url)
        # Wait for page to load (wait for body or error message)
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        page_source = driver.page_source.lower()
        # Common error indicators
        if (
            "page not found" in page_source or
            "404" in page_source or
            "not found" in page_source or
            "error 404" in page_source or
            "the page you requested could not be found" in page_source
        ):
            return "Not Found"
        return "OK"
    except (TimeoutException, WebDriverException) as e:
        return f"Error: {str(e).splitlines()[0]}"
    except Exception as e:
        return f"Error: {str(e).splitlines()[0]}"

def main():
    root = Path(__file__).resolve().parents[2]
    all_data_path = root / 'data' / 'output' / 'all_data.csv'
    log_path = root / 'data' / 'output' / 'glossary_url_check_log.csv'
    df = pd.read_csv(all_data_path)
    results = []
    # Setup Selenium driver
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--disable-gpu')
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    try:
        for idx, row in df.iterrows():
            agency = row['Entity']
            portfolio = row['Portfolio']
            for url_col in ['glossary_url1', 'glossary_url2']:
                url = str(row.get(url_col, '')).strip()
                if url:
                    status = check_url(driver, url)
                    print(f"{agency} | {portfolio} | {url_col} | {url} | {status}")
                    results.append({
                        'Agency': agency,
                        'Portfolio': portfolio,
                        'URL Col': url_col,
                        'URL': url,
                        'Status': status
                    })
                    time.sleep(1)
    finally:
        driver.quit()
    # Save log
    pd.DataFrame(results).to_csv(log_path, index=False)
    print(f"\nResults saved to {log_path}")

if __name__ == "__main__":
    main()
