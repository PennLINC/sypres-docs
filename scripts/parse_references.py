#!/usr/bin/env python3
"""
Parse References from JSON

This script parses JSON reference files and converts them to HTML format with numbered lists.
"""

import json
import re
import sys
from pathlib import Path


def parse_json_references(json_file_path):
    """Parse JSON file containing references in key-value format."""
    with open(json_file_path, "r", encoding="utf-8") as f:
        references = json.load(f)

    # Convert to list of citations, sorted by key (which typically contains year)
    citations = []
    for key, citation in references.items():
        citations.append(citation)

    # Sort by year extracted from the key (e.g., 'Griffiths, 2016' -> 2016)
    def extract_year(key):
        year_match = re.search(r"(\d{4})", key)
        return int(year_match.group(1)) if year_match else 9999

    citations.sort(
        key=lambda x: extract_year(next(k for k, v in references.items() if v == x)),
        reverse=False,
    )

    return citations


def render_citations_to_html(citations):
    """Convert list of citations to HTML format with numbered list."""
    html = "<ol>\n"
    for citation in citations:
        html += f"<li>{citation}</li>\n"
    html += "</ol>"
    return html


def process_single_file(input_json_file, output_html_file):
    """Process a single JSON file and generate HTML output."""
    try:
        # Parse the JSON file
        citations = parse_json_references(input_json_file)
        print(f"Parsed {len(citations)} citations from {input_json_file}")

        # Convert to HTML
        citations_html = render_citations_to_html(citations)

        # Write to HTML file
        with open(output_html_file, "w", encoding="utf-8") as f:
            f.write(citations_html)

        print(f"HTML file written to: {output_html_file}")
        return True

    except Exception as e:
        print(f"Error processing {input_json_file}: {e}")
        return False


def main():
    # Default configuration for psilodep_refs.json
    input_json_file = "../docs/_data/psilodep_refs.json"
    output_html_file = "../_includes/publications/psilodep_refs.html"

    if Path(input_json_file).exists():
        process_single_file(input_json_file, output_html_file)
    else:
        print("Default file not found. Please check the file path.")
        print(f"Looking for: {input_json_file}")


if __name__ == "__main__":
    main()
