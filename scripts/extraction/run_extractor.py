"""Example script showing how to use :class:`GlossaryExtractor`."""

import json
from pathlib import Path
from extractor import GlossaryExtractor


def main() -> None:
    urls = [
        "https://www.transparency.gov.au/publications/finance/asc-pty-ltd/annual-report-2024/glossary",
    ]
    extractor = GlossaryExtractor()
    results = []
    for url in urls:
        data = extractor.extract_from_url(url)
        glossary = data.get("glossary", {})
        for term, definition in glossary.items():
            results.append({"term": term, "definition": definition, "source_url": url})

    output = Path("data") / "glossary_output.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)


if __name__ == "__main__":
    main()

