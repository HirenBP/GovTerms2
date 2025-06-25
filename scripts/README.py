#!/usr/bin/env python3
"""
GovTerms2 - Refactored Project Structure

This project has been reorganized for clarity and maintainability.

Directory Structure:
===================

scripts/
├── extraction/
│   └── selenium_json.py          # Main web scraping and extraction logic
├── crawling/
│   ├── fetch_annual_report_urls_api.py   # Fetch annual report URLs
│   └── fetch_glossary_urls_api.py        # Fetch glossary URLs
└── analysis/
    ├── analyze_flattened.py      # Analyze flattened glossary data
    ├── analyze_simplified.py     # Analyze simplified data
    ├── flatten_glossary.py       # Convert nested to flat JSON
    ├── clean_all_files.py        # Data cleaning utilities
    ├── show_longest.py           # Show longest terms
    ├── remove_longest_term.py    # Remove incorrect terms
    └── jason_counter.py          # Count and analyze term duplicates

archive/
├── website_scraping.py           # Legacy web scraping approach
├── selenium_test.py              # Selenium testing script
└── refactor.py                   # Old refactoring script

data/
├── input/                        # Source data files
└── output/                       # Processed data
    ├── glossary_output_simplified.json   # Clean 3-field format (term, definition, entity)
    ├── glossary_output_flattened.json    # Complete flat format with all metadata
    └── glossary_output_grouped.json      # Original nested format by department

infrastructure/
├── azure_config.json            # Azure configuration
└── cosmosdb_schema.json          # Database schema

Key Files:
==========
- requirements.txt               # Python dependencies
- README.md                     # Project documentation
- found_glossary_urls.txt       # Found URLs during crawling
- terms_with_multiple_definitions.txt  # Analysis of duplicate terms

Removed in Refactoring:
======================
- Empty src/ directory structure (30+ empty files)
- Empty tests/ directory
- Unused frontend assets (static/, templates/)
- Backup files and duplicate outputs
- Empty infrastructure files

The two essential data files are:
1. glossary_output_simplified.json - For most use cases (term, definition, entity)
2. glossary_output_flattened.json - For complete analysis with all metadata
"""

print(__doc__)
