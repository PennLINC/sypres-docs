#!/usr/bin/env python3
"""
Convert project publication BibTeX files into HTML includes.

This script mirrors the logic in `scripts/format_pubs.ipynb`, but loops over the
project's publication BibTeX files instead of handling a single hard-coded file.
"""

from __future__ import annotations

import re
from pathlib import Path

from pybtex import database


ROOT = Path(__file__).resolve().parent.parent
PUBLICATION_JOBS = (
    (
        ROOT / "_data/publications/core_publications.bib",
        ROOT / "_includes/publications/core_publications.html",
        "2025",
    ),
    (
        ROOT / "_data/publications/psilodep.bib",
        ROOT / "_includes/publications/psilodep.html",
        "2025",
    ),
    (
        ROOT / "_data/publications/mdmaptsd.bib",
        ROOT / "_includes/publications/mdmaptsd.html",
        "2025",
    ),
)


def pybtex_entry_to_dict(entry_tuple):
    key, entry = entry_tuple
    entry_dict = {
        "type": entry.type,
        "fields": dict(entry.fields),
        "persons": {
            role: [str(person) for person in persons]
            for role, persons in entry.persons.items()
        },
    }
    return {key: entry_dict}


def parse_bib_to_dict(bib_entries):
    bibliography_dict = {}
    for entry_tuple in bib_entries:
        entry_dict = pybtex_entry_to_dict(entry_tuple)
        bibliography_dict.update(entry_dict)
    return bibliography_dict


def remove_non_letters(text):
    return re.sub(r"[^a-zA-Z\-]", "", text)


def remove_curly_braces(text):
    return text.replace("{", "").replace("}", "")


def remove_alternate_commas(input_string):
    output_string = ""
    comma_count = 1

    for char in input_string:
        if char == ",":
            comma_count += 1
            if comma_count % 2 != 0:
                output_string += char
        else:
            output_string += char

    return output_string


def format_author_names(authors):
    formatted_authors = []
    for author in authors:
        parts = author.split(",")
        clean_parts = []
        for part in parts:
            part = part.replace(" ", "-")
            part = remove_non_letters(part)
            if part != "others" and part != "":
                clean_parts.append(part)
        if len(clean_parts) >= 2:
            last_name = clean_parts[0].strip()
            first_middle_names = parts[1].strip().split()
            initials = "".join([name[0].upper() for name in first_middle_names])
            formatted_authors.append(f"{last_name}, {initials}")
    final_authors = ", ".join(formatted_authors)
    char_to_replace = ", "
    replacement_char = ", & "
    last_index = final_authors.rfind(char_to_replace)
    second_last_index = final_authors[:last_index].rfind(char_to_replace)
    final_authors = (
        final_authors[:second_last_index]
        + replacement_char
        + final_authors[second_last_index + 1 :]
    )
    final_authors = remove_alternate_commas(final_authors)
    return final_authors


def dict_to_nlm_citation(entry_dict):
    authors = entry_dict.get("author", "")[0]
    title = entry_dict.get("title", "")
    if title.endswith("."):
        title = title.rstrip(".")
    journal = entry_dict.get("journal", "")
    volume = entry_dict.get("volume", "")
    pages = entry_dict.get("pages", "")
    year = entry_dict.get("year", "")
    authors_formatted = format_author_names(authors)
    citation = f"{authors_formatted}. {title}. {journal}. {year};{volume}:{pages}."
    citation = remove_curly_braces(citation)
    return citation


def dict_to_software_citation(entry_dict):
    authors = entry_dict.get("author", "")[0]
    title = entry_dict.get("title", "")
    if title.endswith("."):
        title = title.rstrip(".")
    publisher = entry_dict.get("publisher", "")
    year = entry_dict.get("year", "")
    version = entry_dict.get("version", "")
    doi = entry_dict.get("doi", "")
    url = entry_dict.get("url", "")
    authors_formatted = format_author_names(authors)

    parts = [f"{authors_formatted}.", f"{title}."]
    if publisher:
        parts.append(f"{publisher}.")
    if year:
        parts.append(f"{year}.")
    if version and version not in title:
        parts.append(f"Version {version}.")
    if doi:
        parts.append(f"DOI: {doi}.")
    if url:
        parts.append(f"URL: {url}.")

    citation = " ".join(parts)
    citation = remove_curly_braces(citation)
    return citation


def render_citations_to_html(citations):
    html = "<ul>\n"
    for citation in citations:
        html += "<li>"
        parts = citation.split(".")
        if ";" in citation and len(parts) >= 4:
            authors = parts[0].strip()
            title = parts[1].strip()
            journal = parts[2].strip()
            year = parts[3][1:5]
            volume_info = parts[3][6:]
            volume_info = volume_info.replace("--", "-")
            if volume_info != ":":
                html += f"{authors}. {title}. {journal}. {year}. {volume_info}"
            else:
                html += f"{authors}. {title}. {journal}. {year}."
        else:
            html += citation
        html += "</li>\n"
    html += "</ul>"
    return html


def generate_html_for_bib(bibfile, default_year):
    bib_data = database.parse_file(str(bibfile))
    sorted_entries = sorted(
        bib_data.entries.items(),
        key=lambda x: x[1].fields.get("year", default_year),
        reverse=False,
    )
    bibliography_dict = parse_bib_to_dict(sorted_entries)
    citations = []
    for item in bibliography_dict.values():
        item["fields"]["author"] = list(item["persons"].values())
        if item["type"] == "software":
            citations.append(dict_to_software_citation(item["fields"]))
        else:
            citations.append(dict_to_nlm_citation(item["fields"]))
    return render_citations_to_html(citations)


def main():
    for bibfile, output_file, default_year in PUBLICATION_JOBS:
        citations_html = generate_html_for_bib(bibfile, default_year)
        output_file.write_text(citations_html, encoding="utf-8")
        print(f"Wrote {output_file.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
