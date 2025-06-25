import json

with open(r'C:\Users\hiren\PycharmProjects\GovTerms2\data\individual_results.json', encoding="utf-8") as f:
    data = json.load(f)

print(f"Number of object in the file: {len(data)}")
# Build a dictionary: term -> dict of definition -> set of entities
term_defs = {}
for item in data:
    term = item['term']
    definition = item['definition']
    entity = item['entity']
    term_defs.setdefault(term, {})
    term_defs[term].setdefault(definition, set()).add(entity)

print(f"Total terms with duplicate definition: {len(term_defs)}")

with open("terms_with_multiple_definitions.txt", "w", encoding="utf-8") as out_f:
    for term, defs in term_defs.items():
        if len(defs) > 1:
            print(f'Term "{term}" has multiple definitions:')
            out_f.write(f'Term "{term}" has multiple definitions:\n')
            for d, entities in defs.items():
                entity_list = ", ".join(sorted(entities))
                print(f"  - {d}  [Entities: {entity_list}]")
                out_f.write(f"  - {d}  [Entities: {entity_list}]\n")