# GovTerms2: Government Jargon Decoder Chatbot

**GovTerms2** is a Python-based chatbot that helps users understand and decode glossary terms, acronyms## 🚀 Features

- 🔍 **Automated Discovery**: Crawl 2023–24 annual report pages from transparency.gov.au
- 🧠 **Smart Extraction**: Extract glossary and acronym definitions from varied page formats using Selenium
- 📊 **Data Analysis**: Comprehensive analysis tools for understanding and cleaning glossary data
- 📚 **Structured Storage**: Normalized JSON data with agency metadata and source tracking
- 🔧 **Modular Scripts**: Organized scripts for crawling, extraction, and analysis workflows
- ☁️ **Deployment Ready**: Azure infrastructure configuration for cloud deployment
- 📈 **Scalable Architecture**: Designed for integration with SharePoint/Teams via Power Appsbreviations found in Australian Government reports published on [transparency.gov.au](https://www.transparency.gov.au).

---

## 🎯 Project Goals

- ✅ Automatically crawl and extract glossary/acronym definitions from 2023–24 Commonwealth agency annual reports
- ✅ Structure the data for fast, flexible searching and chatbot responses
- ✅ Deploy a publicly accessible web chatbot interface
- ✅ Enable future integration with SharePoint and Microsoft Teams via Power Apps

---

## 🔧 Project Structure

```
GovTerms2/
├── data/                    # Raw and processed data files
│   ├── input/              # Source data files (PDFs, CSV, Excel)
│   ├── output/             # Processed output files
│   ├── glossary_output.json # Main glossary data
│   └── individual_results.json # Individual extraction results
├── documents/              # HTML snapshots and API documentation
│   ├── agency_html_snapshots/ # Scraped HTML content
│   ├── glossary_samples/   # Sample glossary pages
│   └── Transparency_API_fields.json # API field documentation
├── scripts/                # Standalone processing scripts
│   ├── analysis/          # Data analysis and processing scripts
│   ├── crawling/          # URL discovery and crawling scripts
│   ├── extraction/        # Content extraction scripts
│   └── README.py          # Script documentation
├── infrastructure/         # Deployment and configuration
│   ├── azure_config.json  # Azure deployment settings
│   ├── cosmosdb_schema.json # Database schema
│   └── deploy_webapp.bicep # Infrastructure as Code
├── requirements.txt       # Python dependencies
├── GovTerms2.code-workspace # VS Code workspace configuration
└── README.md             # This file
```

---

## 📝 Key Scripts and Modules

### Analysis Scripts (`scripts/analysis/`)
- `analyze_flattened.py` - Analyzes flattened glossary data structure
- `analyze_simplified.py` - Performs simplified data analysis
- `clean_all_files.py` - Cleans and normalizes data files
- `flatten_glossary.py` - Flattens nested glossary structures
- `jason_counter.py` - Counts and analyzes JSON data elements
- `show_longest.py` - Displays longest terms in dataset

### Crawling Scripts (`scripts/crawling/`)
- `fetch_annual_report_urls_api.py` - Discovers annual report URLs via API
- `fetch_glossary_urls_api.py` - Finds glossary pages within reports

### Extraction Scripts (`scripts/extraction/`)
- `selenium_json.py` - Extracts glossary content using Selenium WebDriver

---

## ⚙️ Setup Instructions

### 1. Clone the repository
```bash
git clone https://github.com/your-username/govterms2.git
cd GovTerms2
```

### 2. Create and activate a virtual environment
```bash
# Create virtual environment
python -m venv .venv

# Activate virtual environment
# Windows (PowerShell)
.venv\Scripts\Activate.ps1

# Windows (Command Prompt)
.venv\Scripts\activate.bat

# macOS/Linux
source .venv/bin/activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Run data extraction (optional - data already included)
```bash
# Fetch annual report URLs
python scripts/crawling/fetch_annual_report_urls_api.py

# Extract glossary URLs  
python scripts/crawling/fetch_glossary_urls_api.py

# Extract glossary content
python scripts/extraction/selenium_json.py
```

### 5. Run analysis scripts (optional)
```bash
# Analyze and clean data
python scripts/analysis/flatten_glossary.py
python scripts/analysis/clean_all_files.py
```

### 6. Explore the data
```bash
# View main glossary data
python -c "import json; data=json.load(open('data/glossary_output.json')); print(f'Found {len(data)} glossary entries')"

# List available scripts
ls scripts/*/*.py
```

### 7. Open in VS Code (recommended)
```bash
# Open the project workspace
code GovTerms2.code-workspace
```

The workspace file includes optimized settings for Python development and debugging.

---

## � Data Files

The project includes several key data files:

### Input Data (`data/input/`)
- `Bodies list 1 April 2025 - FINAL.pdf` - Official list of government bodies
- `Commonwealth_Websites.xlsx` - Commonwealth website inventory
- `df_cleaned_tabs.csv` - Cleaned tabular data
- `Flipchart 1 April 2025 - FINAL.pdf` - Visual reference materials

### Output Data (`data/output/`)
- `annual_reports_2023-24.csv` - Annual report URLs and metadata
- `combined_for_scrapping.csv` - Combined data for web scraping
- `glossary_output_grouped.json` - Grouped glossary definitions
- `glossary_urls.csv` - Discovered glossary page URLs
- `result.csv` - Final extraction results

### Main Data Files (`data/`)
- `glossary_output.json` - Primary glossary data with definitions and sources
- `individual_results.json` - Individual extraction results per agency

---

## �🚀 Features

- 🔍 Crawl all 2023–24 annual report pages from transparency.gov.au
- 🧠 Extract glossary and acronym definitions from varied page formats
- 📚 Normalize, cross-link, and store terms and abbreviations with agency metadata
- 💬 Provide a fast, searchable chatbot interface via web API
- ☁️ Deploy to Azure App Service with public access
- 🔁 Migration-ready for SharePoint/Teams integration via Power Apps

---

## 🧪 Sample Bot Interaction

**User:** What is PBO?  
**Bot:**  
```
PBO stands for Portfolio Budget Office  
Defined by:  
- Department of Finance → [Link]  
- Parliamentary Budget Office → [Link]  
Definition: An independent body that provides budget and economic analysis to Parliament.
```

---

## 💻 Usage

### Running Analysis Scripts
```bash
# Count glossary terms
python scripts/analysis/jason_counter.py

# Show longest terms in dataset  
python scripts/analysis/show_longest.py

# Clean and normalize data
python scripts/analysis/clean_all_files.py
```

### Data Processing Workflow
1. **Discovery**: Use crawling scripts to find annual reports and glossary pages
2. **Extraction**: Use Selenium script to extract glossary content from web pages
3. **Analysis**: Use analysis scripts to clean, normalize and understand the data
4. **Testing**: Run test suite to validate functionality

### Key Data Locations
- Raw glossary data: `data/glossary_output.json`
- Processed results: `data/output/`
- HTML snapshots: `documents/agency_html_snapshots/`

---

## 🌐 Deployment Plan

- Hosted on Azure App Service (Flask or FastAPI backend)
- Azure CosmosDB or SQL for data storage
- Static frontend for public access
- Power Platform migration planned for enterprise rollout

---


## 👤 Author

**Hiren Kishor Bhavsar**<br>
**Department of Social Services**
[![LinkedIn](https://img.shields.io/badge/-LinkedIn-blue?style=flat&logo=linkedin)]
(https://www.linkedin.com/in/hirenbhavsar43796265722057697a/)
  
Developed as part of a public sector AI innovation competition.

---

## 📄 License

[MIT License](LICENSE) – Open-source for academic and non-commercial use.

---

## 📊 Current Status

This project has successfully:
✅ **Extracted glossary data** from 100+ Australian Government agency annual reports  
✅ **Processed and cleaned** thousands of terms and definitions  
✅ **Organized data** into structured JSON format with source attribution  
✅ **Created analysis tools** for data exploration and quality assurance  
✅ **Prepared infrastructure** for Azure cloud deployment  

**Next Steps**: Deploy chatbot interface and integrate with SharePoint/Teams