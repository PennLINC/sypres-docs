#!/usr/bin/env python3
"""
Fetch per-study metadata from the Blossom API and write enrichment JSON.

Usage:
    # Dry-run a single study (prints raw JSON, writes nothing):
    python scripts/fetch_blossom_metadata.py --dataset psilodep --only "Davis, 2021" --dry-run

    # Fetch all studies for a dataset:
    python scripts/fetch_blossom_metadata.py --dataset psilodep

    # Fetch all datasets:
    python scripts/fetch_blossom_metadata.py --all

    # Force re-fetch (ignore cache):
    python scripts/fetch_blossom_metadata.py --dataset psilodep --force

Requires BLOSSOM_API_KEY environment variable.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

ROOT = Path(__file__).resolve().parent.parent
DATASETS = ["psilodep", "mdmaptsd"]
API_BASE = "https://www.moreblossom.com/api/v1"
CACHE_DIR = Path(__file__).resolve().parent / ".blossom_cache"
CACHE_TTL_DAYS = 30

DOI_PATTERN = re.compile(r"10\.\d{4,9}/[^\s,;\"'>\]]+", re.IGNORECASE)


def flatten_portable_text(blocks: list[dict]) -> str:
    """Flatten Sanity CMS portable text blocks into plain text paragraphs."""
    paragraphs = []
    for block in blocks:
        if not isinstance(block, dict) or block.get("_type") != "block":
            continue
        children = block.get("children", [])
        text = "".join(child.get("text", "") for child in children)
        if text.strip():
            paragraphs.append(text.strip())
    return "\n\n".join(paragraphs)


def unwrap_response(resp_json: dict) -> dict | list:
    """Unwrap Blossom API {data: ..., meta: ...} envelope."""
    if isinstance(resp_json, dict) and "data" in resp_json:
        return resp_json["data"]
    return resp_json


def get_api_key() -> str:
    key = os.environ.get("BLOSSOM_API_KEY", "").strip()
    if not key:
        print("ERROR: BLOSSOM_API_KEY environment variable is not set.", file=sys.stderr)
        print("Export it in your shell: export BLOSSOM_API_KEY=ak_...", file=sys.stderr)
        sys.exit(1)
    print(f"Using API key: {key[:6]}...")
    return key


def build_session() -> requests.Session:
    session = requests.Session()
    retry = Retry(
        total=3,
        backoff_factor=1.5,
        status_forcelist=[429, 500, 502, 503, 504],
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session


def extract_doi(citation: str) -> str | None:
    """Extract a DOI from a citation string, stripping trailing punctuation."""
    match = DOI_PATTERN.search(citation)
    if not match:
        return None
    doi = match.group(0).rstrip(".,;:)")
    return doi


def cache_path(doi: str) -> Path:
    """Return the cache file path for a given DOI."""
    h = hashlib.sha1(doi.encode()).hexdigest()
    return CACHE_DIR / f"{h}.json"


def read_cache(doi: str, force: bool) -> dict | None:
    """Read a cached response if it exists and is fresh."""
    if force:
        return None
    path = cache_path(doi)
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        cached_at = datetime.fromisoformat(data.get("_cached_at", "2000-01-01"))
        age_days = (datetime.now(timezone.utc) - cached_at).days
        if age_days > CACHE_TTL_DAYS:
            return None
        return data
    except (json.JSONDecodeError, ValueError):
        return None


def write_cache(doi: str, data: dict) -> None:
    """Write a response to the cache."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    data["_cached_at"] = datetime.now(timezone.utc).isoformat()
    cache_path(doi).write_text(
        json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8"
    )


def fetch_paper_by_doi(
    session: requests.Session, api_key: str, doi: str
) -> dict:
    """
    Two-step lookup:
    1. GET /papers?doi=<doi> → get slug
    2. GET /papers/:slug → full detail
    """
    # Step 1: DOI lookup
    resp = session.get(
        f"{API_BASE}/papers",
        params={"doi": doi},
        headers={"Authorization": f"Bearer {api_key}"},
        timeout=30,
    )
    resp.raise_for_status()
    doi_result = unwrap_response(resp.json())

    # Normalize to a list of papers
    if isinstance(doi_result, dict):
        papers = [doi_result]
    elif isinstance(doi_result, list):
        papers = doi_result
    else:
        papers = []

    if not papers:
        return {"_step": "doi_lookup", "_status": "no_results", "doi": doi}

    # Take the first match
    paper = papers[0]
    slug = paper.get("slug")

    if not slug:
        # DOI lookup returned data but no slug — return what we have
        return {"_step": "doi_lookup", "_status": "no_slug", "doi": doi, "doi_response": paper}

    time.sleep(0.65)

    # Step 2: full detail by slug
    resp2 = session.get(
        f"{API_BASE}/papers/{slug}",
        headers={"Authorization": f"Bearer {api_key}"},
        timeout=30,
    )
    resp2.raise_for_status()
    detail = unwrap_response(resp2.json())
    if not isinstance(detail, dict):
        detail = {}
    detail["_step"] = "full_detail"
    detail["_status"] = "ok"
    detail["_doi_queried"] = doi
    detail["_slug"] = slug
    return detail


def load_refs(dataset: str) -> dict[str, str]:
    """Load the refs JSON for a dataset. Returns {author_year_key: citation_string}."""
    refs_path = ROOT / "docs" / "_data" / f"{dataset}_refs.json"
    if not refs_path.exists():
        print(f"ERROR: {refs_path} not found.", file=sys.stderr)
        sys.exit(1)
    return json.loads(refs_path.read_text(encoding="utf-8"))


def fetch_dataset(
    dataset: str,
    session: requests.Session,
    api_key: str,
    only: str | None = None,
    dry_run: bool = False,
    force: bool = False,
) -> dict:
    """Fetch Blossom metadata for all studies in a dataset."""
    refs = load_refs(dataset)
    records: dict[str, dict] = {}
    errors = 0
    total = 0

    for key, citation in refs.items():
        if only and key != only:
            continue
        total += 1
        doi = extract_doi(citation)

        if not doi:
            print(f"  [{key}] No DOI found — skipping")
            records[key] = {"status": "not_found", "reason": "no DOI; gray literature"}
            continue

        # Check cache
        cached = read_cache(doi, force)
        if cached and not dry_run:
            print(f"  [{key}] Cached (DOI: {doi})")
            records[key] = build_record(key, doi, cached)
            continue

        print(f"  [{key}] Fetching DOI: {doi} ...")
        try:
            raw = fetch_paper_by_doi(session, api_key, doi)

            if dry_run:
                print(json.dumps(raw, indent=2, ensure_ascii=False))
                print(f"\n--- End of dry-run for {key} ---\n")
                continue

            write_cache(doi, raw)
            records[key] = build_record(key, doi, raw)
            print(f"  [{key}] OK")
            time.sleep(0.65)

        except requests.RequestException as e:
            print(f"  [{key}] ERROR: {e}", file=sys.stderr)
            records[key] = {"status": "error", "doi": doi, "error": str(e)}
            errors += 1
            time.sleep(0.65)

    if dry_run:
        return {}

    # Fail if >20% errors
    if total > 0 and errors / total > 0.2:
        print(
            f"ERROR: {errors}/{total} studies failed (>{20}% threshold).",
            file=sys.stderr,
        )
        sys.exit(1)

    return {
        "dataset": dataset,
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "blossom_api_version": "v1",
        "records": records,
    }


def build_record(key: str, doi: str, raw: dict) -> dict:
    """Normalize a raw API response into our output record schema."""
    if raw.get("_status") != "ok":
        return {
            "status": raw.get("_status", "unknown"),
            "doi": doi,
            "reason": f"API returned status: {raw.get('_status')}",
            "raw": raw,
        }

    slug = raw.get("_slug", raw.get("slug", ""))
    blossom_url = f"https://www.moreblossom.com/papers/{slug}" if slug else ""

    # Abstract is Sanity portable text — flatten to plain text
    abstract_raw = raw.get("abstract", "")
    if isinstance(abstract_raw, list):
        abstract = flatten_portable_text(abstract_raw)
    else:
        abstract = str(abstract_raw) if abstract_raw else ""

    return {
        "status": "ok",
        "doi": doi,
        "blossom_slug": slug,
        "blossom_url": blossom_url,
        "title": raw.get("title", ""),
        "paragraph_summary": raw.get("paragraphSummary", ""),
        "abstract": abstract,
        "pmid": raw.get("pmid"),
        "publication_date": raw.get("publicationDate", ""),
        "citation_count": raw.get("citationCount"),
        "study_characteristics": raw.get("studyCharacteristics", []),
        "compounds": [c.get("title", "") for c in raw.get("compounds", [])],
        "topics": [t.get("title", "") for t in raw.get("topics", [])],
        "journal": raw.get("journal", {}).get("name", ""),
        "raw": {k: v for k, v in raw.items() if not k.startswith("_")},
    }


def write_output(dataset: str, data: dict) -> Path:
    """Write the enrichment JSON to _data/publications/."""
    out_dir = ROOT / "_data" / "publications"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{dataset}_blossom.json"
    out_path.write_text(
        json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    return out_path


def main():
    parser = argparse.ArgumentParser(
        description="Fetch per-study metadata from the Blossom API."
    )
    parser.add_argument(
        "--dataset",
        choices=DATASETS,
        help="Dataset to fetch (e.g., psilodep, mdmaptsd).",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        dest="all_datasets",
        help="Fetch all known datasets.",
    )
    parser.add_argument(
        "--only",
        help='Fetch only this study key (e.g., "Davis, 2021").',
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print raw API response to stdout; write nothing to disk.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Ignore cache and re-fetch all studies.",
    )
    args = parser.parse_args()

    if not args.dataset and not args.all_datasets:
        parser.error("Specify --dataset <name> or --all.")

    api_key = get_api_key()
    session = build_session()

    datasets = DATASETS if args.all_datasets else [args.dataset]

    for ds in datasets:
        print(f"\n=== {ds} ===")
        result = fetch_dataset(
            ds, session, api_key, only=args.only, dry_run=args.dry_run, force=args.force
        )
        if args.dry_run:
            print("(dry-run — nothing written to disk)")
            continue

        out_path = write_output(ds, result)
        ok = sum(1 for r in result["records"].values() if r.get("status") == "ok")
        total = len(result["records"])
        print(f"Wrote {out_path.relative_to(ROOT)} ({ok}/{total} studies enriched)")


if __name__ == "__main__":
    main()
