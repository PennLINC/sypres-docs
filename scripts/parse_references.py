#!/usr/bin/env python3
"""
Parse References from JSON and generate enriched HTML includes.

Reads per-dataset reference JSON files (docs/_data/<dataset>_refs.json) and,
if available, Blossom API enrichment data (_data/publications/<dataset>_blossom.json).
Outputs numbered HTML reference lists with optional <details> expanders showing
per-study summaries and abstracts from Blossom.

Usage:
    python scripts/parse_references.py
"""

import json
import re
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

REFS_STYLE = """\
<style>
.ref-details summary {
  cursor: pointer;
  color: #494e52;
  font-size: 0.85em;
  margin-top: 0.3em;
}
.ref-details summary:hover {
  color: #0077b6;
}
.ref-details__body {
  margin: 0.5em 0 0.5em 1em;
  font-size: 0.9em;
  line-height: 1.6;
}
.ref-details__body p {
  margin: 0 0 0.5em;
}
.ref-details__abstract summary {
  font-size: 0.85em;
}
.ref-details__source {
  font-size: 0.8em;
  color: #6c757d;
  margin-top: 0.5em;
}
@media print {
  .ref-details { display: block; }
  .ref-details[open] > summary { display: none; }
}
</style>
"""


def key_to_id(key: str) -> str:
    """Convert 'Davis, 2021' to 'ref-davis-2021'."""
    slug = key.lower().replace(",", "").replace(" ", "-")
    slug = re.sub(r"[^a-z0-9\-]", "", slug)
    return f"ref-{slug}"


def extract_year(key: str) -> int:
    match = re.search(r"(\d{4})", key)
    return int(match.group(1)) if match else 9999


def load_refs(dataset: str) -> dict[str, str]:
    """Load the refs JSON. Returns {author_year_key: citation_string}."""
    path = ROOT / "docs" / "_data" / f"{dataset}_refs.json"
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def load_blossom(dataset: str) -> dict[str, dict]:
    """Load Blossom enrichment data. Returns {author_year_key: record} or {}."""
    path = ROOT / "_data" / "publications" / f"{dataset}_blossom.json"
    if not path.exists():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    return data.get("records", {})


def render_details_block(record: dict) -> str:
    """Render a <details> block for a single enriched study."""
    if record.get("status") != "ok":
        return ""

    summary = record.get("paragraph_summary", "").strip()
    abstract = record.get("abstract", "").strip()
    blossom_url = record.get("blossom_url", "")

    if not summary and not abstract:
        return ""

    parts = []
    parts.append('  <details class="ref-details">')
    parts.append("    <summary>Study summary via Blossom</summary>")
    parts.append('    <div class="ref-details__body">')

    if summary:
        parts.append(f"      <p>{escape(summary)}</p>")

    if abstract:
        parts.append('      <details class="ref-details__abstract">')
        parts.append("        <summary>Abstract</summary>")
        # Split abstract into paragraphs
        for para in abstract.split("\n\n"):
            para = para.strip()
            if para:
                parts.append(f"        <p>{escape(para)}</p>")
        parts.append("      </details>")

    if blossom_url:
        parts.append(
            f'      <p class="ref-details__source">'
            f'Enriched metadata from <a href="{escape(blossom_url)}" '
            f'rel="noopener" target="_blank">Blossom</a>.</p>'
        )

    parts.append("    </div>")
    parts.append("  </details>")
    return "\n".join(parts)


def render_refs_html(refs: dict[str, str], blossom: dict[str, dict]) -> str:
    """Render the full references HTML include."""
    # Sort by year
    sorted_keys = sorted(refs.keys(), key=extract_year)

    has_blossom = any(
        blossom.get(k, {}).get("status") == "ok" for k in sorted_keys
    )

    parts = []
    if has_blossom:
        parts.append(REFS_STYLE)

    parts.append("<ol>")
    for key in sorted_keys:
        citation = refs[key]
        ref_id = key_to_id(key)
        details = render_details_block(blossom.get(key, {}))

        if details:
            parts.append(f'<li id="{ref_id}">')
            parts.append(f"  {escape(citation)}")
            parts.append(details)
            parts.append("</li>")
        else:
            parts.append(f'<li id="{ref_id}">{escape(citation)}</li>')

    parts.append("</ol>")
    return "\n".join(parts)


def process_dataset(dataset: str) -> None:
    """Process a single dataset: load refs + blossom, write HTML include."""
    refs = load_refs(dataset)
    if not refs:
        print(f"  No refs found for {dataset}, skipping.")
        return

    blossom = load_blossom(dataset)
    enriched = sum(1 for k in refs if blossom.get(k, {}).get("status") == "ok")

    html = render_refs_html(refs, blossom)

    output_path = ROOT / "_includes" / "publications" / f"{dataset}_refs.html"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(html, encoding="utf-8")

    print(
        f"  Wrote {output_path.relative_to(ROOT)} "
        f"({len(refs)} refs, {enriched} enriched)"
    )


def main():
    input_dir = ROOT / "docs" / "_data"
    json_files = sorted(input_dir.glob("*_refs.json"))

    if not json_files:
        print(f"No *_refs.json files found in {input_dir}")
        return

    for json_file in json_files:
        dataset = json_file.stem.replace("_refs", "")
        print(f"Processing {dataset}:")
        process_dataset(dataset)


if __name__ == "__main__":
    main()
