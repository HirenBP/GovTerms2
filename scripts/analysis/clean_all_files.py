#!/usr/bin/env python3
"""
Script to remove the longest incorrect term from both flattened files and update them.
"""

import json
import shutil

def clean_both_files():
    """Clean both the flattened and simplified files by removing the longest incorrect term."""
    
    # File paths
    flattened_file = r"c:\Users\hiren\PycharmProjects\GovTerms2\data\output\glossary_output_flattened.json"
    simplified_file = r"c:\Users\hiren\PycharmProjects\GovTerms2\data\output\glossary_output_simplified.json"
    
    # Backup original files
    shutil.copy2(flattened_file, flattened_file + ".backup")
    shutil.copy2(simplified_file, simplified_file + ".backup")
    print("Created backup files")
    
    # Clean flattened file
    with open(flattened_file, 'r', encoding='utf-8') as f:
        flattened_data = json.load(f)
    
    # Find and remove the longest term
    longest_record = max(flattened_data, key=lambda record: len(record['term']))
    longest_term = longest_record['term']
    
    cleaned_flattened = [record for record in flattened_data if record['term'] != longest_term]
    
    # Update flattened file
    with open(flattened_file, 'w', encoding='utf-8') as f:
        json.dump(cleaned_flattened, f, indent=2, ensure_ascii=False)
    
    print(f"Updated {flattened_file}: {len(flattened_data)} -> {len(cleaned_flattened)} terms")
    
    # Clean simplified file
    with open(simplified_file, 'r', encoding='utf-8') as f:
        simplified_data = json.load(f)
    
    cleaned_simplified = [record for record in simplified_data if record['term'] != longest_term]
    
    # Update simplified file
    with open(simplified_file, 'w', encoding='utf-8') as f:
        json.dump(cleaned_simplified, f, indent=2, ensure_ascii=False)
    
    print(f"Updated {simplified_file}: {len(simplified_data)} -> {len(cleaned_simplified)} terms")
    
    print(f"\nRemoved term: {longest_term[:100]}...")
    print(f"From entity: {longest_record['entity']}")

if __name__ == "__main__":
    clean_both_files()
