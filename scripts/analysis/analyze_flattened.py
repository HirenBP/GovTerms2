#!/usr/bin/env python3
"""
Script to analyze the flattened glossary file and show statistics.
"""

import json
from collections import Counter

def analyze_flattened_glossary(file_path):
    """
    Analyze the flattened glossary file and show statistics.
    
    Args:
        file_path (str): Path to the flattened JSON file
    """
    
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print(f"Total glossary terms: {len(data)}")
    print()
    
    # Count by department
    departments = Counter(record['department'] for record in data)
    print("Terms by Department:")
    for dept, count in departments.most_common():
        print(f"  {dept}: {count} terms")
    print()
    
    # Count by entity (top 10)
    entities = Counter(record['entity'] for record in data)
    print("Top 10 Entities by term count:")
    for entity, count in entities.most_common(10):
        print(f"  {entity}: {count} terms")
    print()
    
    # Show a few sample records from different departments
    sample_departments = list(departments.keys())[:3]
    print("Sample records from different departments:")
    for dept in sample_departments:
        sample_record = next(record for record in data if record['department'] == dept)
        print(f"\n  {dept} - {sample_record['entity']}:")
        print(f"    Term: {sample_record['term']}")
        print(f"    Definition: {sample_record['definition']}")
    
    # Count top ten longest terms. 
    print("Top 10 longest terms:")
    longest_terms = sorted(data, key=lambda record: len(record['term']), reverse=True)[:10]
    for i, record in enumerate(longest_terms, 1):
        print(f"  {i}. {record['term']} ({len(record['term'])} chars) - {record['entity']}")
    print()

if __name__ == "__main__":
    file_path = r"c:\Users\hiren\PycharmProjects\GovTerms2\data\output\glossary_output_flattened.json"
    analyze_flattened_glossary(file_path)
