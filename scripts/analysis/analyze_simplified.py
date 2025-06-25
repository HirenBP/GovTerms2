#!/usr/bin/env python3
"""
Quick analysis of the simplified glossary file.
"""

import json
from collections import Counter

def analyze_simplified_glossary():
    """Show statistics for the simplified glossary file."""
    
    file_path = r"c:\Users\hiren\PycharmProjects\GovTerms2\data\output\glossary_output_simplified.json"
    
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print(f"Total glossary terms: {len(data)}")
    print()
    
    # Show structure
    print("Record structure:")
    if data:
        first_record = data[0]
        for key, value in first_record.items():
            print(f"  {key}: {type(value).__name__}")
        print()
        
        print("Sample record:")
        print(f"  Term: {first_record['term']}")
        print(f"  Definition: {first_record['definition']}")
        print(f"  Entity: {first_record['entity']}")
        print()
    
    # Count by entity (top 10)
    entities = Counter(record['entity'] for record in data)
    print("Top 10 Entities by term count:")
    for entity, count in entities.most_common(10):
        print(f"  {entity}: {count} terms")
    print()
    
    # Show entities with different names
    unique_entities = len(entities)
    print(f"Total unique entities: {unique_entities}")

if __name__ == "__main__":
    analyze_simplified_glossary()
