#!/usr/bin/env python3
"""
Script to flatten the grouped glossary JSON structure.
Converts nested structure to a flat array of term records.
"""

import json
import os

def flatten_glossary(input_file, output_file):
    """
    Flatten the nested glossary structure into a flat array.
    
    Args:
        input_file (str): Path to the input grouped JSON file
        output_file (str): Path to save the flattened JSON file
    """
    
    # Read the input file
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    flattened_records = []
    
    # Iterate through each department/portfolio
    for department, entities in data.items():
        for entity_info in entities:
            entity_name = entity_info.get("Entity", "")
            entity_website = entity_info.get("Entity Website", "")
            glossary_url = entity_info.get("Glossary Url", "")
            
            # Get the glossary terms
            glossary_details = entity_info.get("Glossary Details", {})
            glossary_terms = glossary_details.get("glossary", {})
            
            # Create a record for each term
            for term, definition in glossary_terms.items():
                record = {
                    "term": term,
                    "definition": definition,
                    "entity": entity_name
                }
                flattened_records.append(record)
    
    # Write the flattened data to output file
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(flattened_records, f, indent=2, ensure_ascii=False)
    
    print(f"Successfully flattened {len(flattened_records)} glossary terms")
    print(f"Output saved to: {output_file}")

if __name__ == "__main__":
    input_file = r"c:\Users\hiren\PycharmProjects\GovTerms2\data\output\glossary_output_grouped.json"
    output_file = r"c:\Users\hiren\PycharmProjects\GovTerms2\data\output\glossary_output_simplified.json"
    
    # Check if input file exists
    if not os.path.exists(input_file):
        print(f"Error: Input file not found: {input_file}")
        exit(1)
    
    flatten_glossary(input_file, output_file)
