#!/usr/bin/env python3
"""
Quick script to show just the longest terms after cleanup.
"""

import json

def show_longest_terms():
    """Show the top 10 longest terms after cleanup."""
    
    file_path = r"c:\Users\hiren\PycharmProjects\GovTerms2\data\output\glossary_output_flattened.json"
    
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print(f"Total terms: {len(data)}")
    print("\nTop 10 longest terms after cleanup:")
    
    longest_terms = sorted(data, key=lambda record: len(record['term']), reverse=True)[:10]
    for i, record in enumerate(longest_terms, 1):
        print(f"  {i}. {record['term']} ({len(record['term'])} chars) - {record['entity']}")

if __name__ == "__main__":
    show_longest_terms()
