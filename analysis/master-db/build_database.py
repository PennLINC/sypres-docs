#!/usr/bin/env python3
"""Build the SYPRES psychedelic-RCT master database from Covidence exports.

This script merges two kinds of Covidence CSV exports into a single JSON file
that powers the interactive dashboard at /docs/datasets/master-db/:

  1. A *bibliographic* export of the INCLUDED studies (title, authors,
     abstract, journal, DOI, PMID, registry). Filename contains "included".
  2. The *extraction* export, which carries the data-extraction template
     fields (drug, arms, comparator, population, outcomes, ...). Identified
     by the presence of a "Reviewer Name" column.

The two are joined on the Covidence number. Studies that are included but not
yet extracted are kept and flagged `extracted: false` so the dashboard can show
extraction progress.

Re-run after every new Covidence export:

    python3 analysis/master-db/build_database.py

Output: _data/master_db.json  (consumed by the dashboard via site.data)

No third-party dependencies (Python 3 stdlib only).
"""
from __future__ import annotations

import csv
import datetime as _dt
import glob
import json
import os
import re
import sys

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
DATA_DIR = os.path.join(HERE, "data")
OUT_PATH = os.path.join(REPO, "_data", "master_db.json")
# Optional manual PRISMA numbers not present in the Covidence stage exports.
MANUAL_PATH = os.path.join(HERE, "prisma_manual.json")

# ---------------------------------------------------------------------------
# Controlled vocabularies for light auto-derivation (drug + indication).
# These power the dashboard facets for studies that are not yet extracted.
# Order matters: first match wins. Extracted values always take precedence.
# ---------------------------------------------------------------------------
DRUG_PATTERNS = [
    ("MDMA", r"mdma|methylenedioxymethamphetamine|ecstasy|midomafetamine"),
    ("Psilocybin", r"psilocybin|psilocin|psilocyb"),
    ("LSD", r"\blsd\b|lysergic|lysergide"),
    ("DMT", r"\bdmt\b|dimethyltryptamine|ayahuasca"),
    ("5-MeO-DMT", r"5-meo"),
    ("Mescaline", r"mescaline"),
    ("Ketamine", r"ketamine|esketamine"),
]

INDICATION_PATTERNS = [
    ("PTSD", r"ptsd|post[- ]?traumatic|posttraumatic"),
    ("Depression", r"depress|\bmdd\b"),
    ("Anxiety", r"anxiety|anxiolytic"),
    ("Alcohol use", r"alcohol"),
    ("OCD", r"obsessive|\bocd\b"),
    ("Pain", r"\bpain\b|analgesic|nocicep"),
    ("Tinnitus", r"tinnitus"),
    ("Substance use", r"addiction|substance use|smoking|nicotine|cocaine"),
]


def _clean(s: str | None) -> str:
    return (s or "").strip()


def _classify(path: str, header: list[str]) -> str | None:
    """Return 'extraction', 'included', or None for a CSV given its header."""
    cols = set(header)
    if "Reviewer Name" in cols and "Study type" in cols:
        return "extraction"
    if "Abstract" in cols and "included" in os.path.basename(path).lower():
        return "included"
    return None


def _latest(paths: list[str]) -> str | None:
    """Pick the most recently *named* export (Covidence stamps filenames)."""
    return sorted(paths)[-1] if paths else None


def _norm_covidence(raw: str) -> int | None:
    m = re.search(r"\d+", raw or "")
    return int(m.group()) if m else None


def _split_list(raw: str, sep: str = ";") -> list[str]:
    return [p.strip() for p in (raw or "").split(sep) if p.strip()]


def _parse_pages(raw: str) -> tuple[str, str]:
    """'2152-2162' -> ('2152','2162'); 'S105-S105' -> ('S105','S105')."""
    raw = _clean(raw)
    if not raw:
        return "", ""
    m = re.match(r"^\s*([A-Za-z]?\d+)\s*[-–]\s*([A-Za-z]?\d+)\s*$", raw)
    if m:
        return m.group(1), m.group(2)
    return raw, ""  # single page or article number


def _to_int(raw: str) -> int | None:
    m = re.search(r"\d+", raw or "")
    return int(m.group()) if m else None


def _yes_no(raw: str) -> str:
    v = _clean(raw).lower()
    if v in ("yes", "y", "true"):
        return "yes"
    if v in ("no", "n", "false"):
        return "no"
    return "unknown"


def _derive(patterns, *texts) -> str | None:
    blob = " ".join(t.lower() for t in texts if t)
    for label, pat in patterns:
        if re.search(pat, blob):
            return label
    return None


def _registry_url(reg: str) -> str:
    nct = re.search(r"NCT\d+", reg or "")
    if nct:
        return f"https://clinicaltrials.gov/study/{nct.group()}"
    return ""


def _study_url(doi: str, pmid: str) -> str:
    if doi:
        doi = re.sub(r"^https?://doi\.org/", "", doi.strip())
        return f"https://doi.org/{doi}"
    if pmid:
        return f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"
    return ""


# ---------------------------------------------------------------------------
# PRISMA study-flow
#
# The four bibliographic Covidence exports are snapshots of each study's
# CURRENT stage and are mutually exclusive (a study sits in exactly one of
# screen / select / included / excluded). The funnel below is derived with set
# algebra so it stays correct even if a future export happens to overlap.
# Database-identification and duplicate-removal counts are NOT in these exports
# (they live in the Covidence dashboard).
# ---------------------------------------------------------------------------
STAGE_KEYS = ("screen", "select", "included", "excluded")


def _stage_path(key: str) -> str | None:
    """Latest data CSV whose filename contains `key` (e.g. 'excluded').

    Plain substring match is safe: none of screen/select/included/excluded is a
    substring of another ('included' is not contained in 'excluded').
    """
    hits = [p for p in glob.glob(os.path.join(DATA_DIR, "*.csv"))
            if key in os.path.basename(p).lower()]
    return _latest(hits)


def _stage_ids(path: str | None) -> set:
    ids = set()
    if path:
        with open(path, newline="", encoding="utf-8-sig") as fh:
            for row in csv.DictReader(fh):
                cid = _norm_covidence(row.get("Covidence #", ""))
                if cid is not None:
                    ids.add(cid)
    return ids


def _exclusion_reasons(path: str | None) -> dict:
    """Tally full-text exclusion reasons from the excluded export's `Notes`
    (format: 'Exclusion reason: <reason>; '). Sorted most-common first."""
    reasons: dict = {}
    if path:
        with open(path, newline="", encoding="utf-8-sig") as fh:
            for row in csv.DictReader(fh):
                note = re.sub(r"(?i)exclusion reason:", "", row.get("Notes", "") or "")
                for part in note.split(";"):
                    part = part.strip()
                    if part:
                        reasons[part] = reasons.get(part, 0) + 1
    return dict(sorted(reasons.items(), key=lambda kv: (-kv[1], kv[0])))


def _load_manual() -> dict:
    """Load optional hand-entered PRISMA numbers from prisma_manual.json.

    Covidence stage exports omit 'records identified', 'duplicates removed' and
    'excluded at title/abstract screening', so the snapshot funnel starts
    mid-stream. These let the diagram show the full top of the funnel once known.
    """
    keys = ("records_identified", "duplicates_removed", "excluded_title_abstract")
    manual = {k: None for k in keys}
    if os.path.exists(MANUAL_PATH):
        with open(MANUAL_PATH, encoding="utf-8") as fh:
            raw = json.load(fh)
        for k in keys:
            manual[k] = raw[k] if isinstance(raw.get(k), int) else None
    return manual


def build_prisma(n_extracted: int) -> dict:
    """Return the PRISMA-style funnel counts from the stage snapshots."""
    paths = {k: _stage_path(k) for k in STAGE_KEYS}
    S, L, I, E = (_stage_ids(paths[k]) for k in STAGE_KEYS)
    advanced = L | I | E
    records_in_review = len(S | L | I | E)

    # Merge optional manual upstream counts (identification / screening exclusions).
    manual = _load_manual()
    ex_ta = manual["excluded_title_abstract"]
    manual["records_screened"] = (records_in_review + ex_ta) if isinstance(ex_ta, int) else None
    manual["complete"] = all(
        manual[k] is not None
        for k in ("records_identified", "duplicates_removed", "excluded_title_abstract")
    )

    return {
        "records_in_review": records_in_review,
        "in_screening": len(S - advanced),
        "advanced_to_fulltext": len(advanced),
        "fulltext_in_review": len(L - I - E),
        "fulltext_excluded": len(E - I),
        "fulltext_excluded_reasons": _exclusion_reasons(paths["excluded"]),
        "included": len(I),
        "extracted": n_extracted,
        # Upstream counts NOT in the stage exports — supply via prisma_manual.json.
        "manual": manual,
        "source_files": {k: (os.path.relpath(p, REPO) if p else None)
                         for k, p in paths.items()},
    }


def build() -> dict:
    """Read the Covidence exports and return the full database dict
    (`{meta, prisma, studies}`). Pure — does not touch the filesystem to write."""
    csvs = glob.glob(os.path.join(DATA_DIR, "*.csv"))
    included_files, extraction_files = [], []
    for path in csvs:
        with open(path, newline="", encoding="utf-8-sig") as fh:
            header = next(csv.reader(fh))
        kind = _classify(path, header)
        if kind == "included":
            included_files.append(path)
        elif kind == "extraction":
            extraction_files.append(path)

    inc_path = _latest(included_files)
    ext_path = _latest(extraction_files)
    if not inc_path:
        sys.exit("ERROR: no '*included*.csv' bibliographic export found in data/")

    # ---- read extraction rows keyed by covidence id ----
    extraction: dict[int, dict] = {}
    if ext_path:
        with open(ext_path, newline="", encoding="utf-8-sig") as fh:
            for row in csv.DictReader(fh):
                cid = _norm_covidence(row.get("Covidence #", ""))
                if cid is not None:
                    extraction[cid] = row

    # ---- read included rows and merge ----
    studies: list[dict] = []
    with open(inc_path, newline="", encoding="utf-8-sig") as fh:
        for row in csv.DictReader(fh):
            cid = _norm_covidence(row.get("Covidence #", ""))
            ext = extraction.get(cid, {})
            is_ext = bool(ext)

            # DOI: the bibliographic import is canonical, but ~10% of records
            # (older trials, conference abstracts) have no DOI on import, so fall
            # back to a DOI the reviewer supplied during extraction.
            doi = _clean(row.get("DOI")) or _clean(ext.get("DOI"))
            pmid = _clean(row.get("Ref"))
            page_start, page_end = _parse_pages(row.get("Pages"))

            # Registry: prefer extraction's trial registry field, else the
            # bibliographic accession number (e.g. "ClinicalTrials.gov/NCT...").
            registry = _clean(ext.get("Trial Registry Number")) or _clean(
                row.get("Accession Number")
            )

            # Drug: extracted value wins; otherwise scan title + abstract.
            drug_ext = _clean(ext.get("Psychedelic/Intervention Drug(s)"))
            if drug_ext:
                drug = drug_ext.split(";")[0].strip().upper() if len(
                    drug_ext
                ) <= 5 else drug_ext.split(";")[0].strip()
                drug = _derive(DRUG_PATTERNS, drug_ext) or drug_ext.split(";")[0].strip()
                drug_source = "extracted"
            else:
                drug = _derive(DRUG_PATTERNS, row.get("Title", ""), row.get("Abstract", ""))
                drug_source = "auto" if drug else "unknown"
                drug = drug or "Unclear"

            # Indication: extracted target population wins; else derive.
            pop_ext = _clean(ext.get("Target Population"))
            if pop_ext:
                indication = _derive(INDICATION_PATTERNS, pop_ext) or (
                    "Healthy volunteers" if "healthy" in pop_ext.lower() else pop_ext
                )
                indication_source = "extracted"
            else:
                indication = _derive(
                    INDICATION_PATTERNS, row.get("Title", ""), row.get("Abstract", ""),
                    _clean(row.get("Tags")),
                )
                if not indication and re.search(
                    r"healthy", (row.get("Title", "") + row.get("Abstract", "")).lower()
                ):
                    indication = "Healthy volunteers"
                indication_source = "auto" if indication else "unknown"
                indication = indication or "Unclear"

            studies.append(
                {
                    "covidence_id": cid,
                    "study_id": _clean(row.get("Study")),
                    "title": _clean(row.get("Title")),
                    "authors": _split_list(row.get("Authors")),
                    "authors_str": _clean(row.get("Authors")),
                    "abstract": _clean(row.get("Abstract")),
                    "year": _to_int(row.get("Published Year")),
                    "month": _clean(row.get("Published Month")),
                    "journal": _clean(row.get("Journal")),
                    "volume": _clean(row.get("Volume")),
                    "issue": _clean(row.get("Issue")),
                    "pages": _clean(row.get("Pages")),
                    "page_start": page_start,
                    "page_end": page_end,
                    "pmid": pmid,
                    "doi": doi,
                    "url": _study_url(doi, pmid),
                    "registry": registry,
                    "registry_url": _registry_url(registry),
                    "tags": _split_list(row.get("Tags")),
                    # ---- derived facets ----
                    "drug": drug,
                    "drug_source": drug_source,
                    "indication": indication,
                    "indication_source": indication_source,
                    # ---- extraction template fields ----
                    "extracted": is_ext,
                    "reviewer": _clean(ext.get("Reviewer Name")),
                    "study_type": _clean(ext.get("Study type")),
                    "parent_study_doi": _clean(ext.get("Parent Study DOI")),
                    "n_arms": _to_int(ext.get("Number of conditions/arms")),
                    "n_arms_raw": _clean(ext.get("Number of conditions/arms")),
                    "drugs_raw": drug_ext,
                    "derivative": _yes_no(ext.get("Derivative?")) if is_ext else "unknown",
                    "microdosing": _yes_no(ext.get("Microdosing study?")) if is_ext else "unknown",
                    "comparator": _clean(ext.get("Comparator Drug")),
                    "population": pop_ext,
                    "outcomes": _split_list(ext.get("Outcomes")),
                    "qualitative_outcome": _clean(ext.get("What is the qualitative outcome?")),
                    "extraction_notes": _clean(ext.get("Notes")),
                }
            )

    # sort newest first, then alphabetically by study id
    studies.sort(key=lambda s: (-(s["year"] or 0), s["study_id"].lower()))

    n_extracted = sum(1 for s in studies if s["extracted"])
    out = {
        "meta": {
            "generated": _dt.date.today().isoformat(),
            "review_id": re.search(r"\d+", os.path.basename(inc_path)).group(),
            "n_included": len(studies),
            "n_extracted": n_extracted,
            "drugs": sorted({s["drug"] for s in studies if s["drug"] != "Unclear"}),
            "indications": sorted({s["indication"] for s in studies if s["indication"] != "Unclear"}),
            "outcomes": sorted({o for s in studies for o in s["outcomes"]}),
            "year_min": min((s["year"] for s in studies if s["year"]), default=None),
            "year_max": max((s["year"] for s in studies if s["year"]), default=None),
            "source_included": os.path.relpath(inc_path, REPO),
            "source_extraction": os.path.relpath(ext_path, REPO) if ext_path else None,
        },
        "prisma": build_prisma(n_extracted),
        "studies": studies,
    }
    return out


def main() -> int:
    out = build()
    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as fh:
        json.dump(out, fh, ensure_ascii=False, indent=2)

    m, p = out["meta"], out["prisma"]
    print(f"Wrote {os.path.relpath(OUT_PATH, REPO)}")
    print(f"  included : {m['n_included']}  extracted: {m['n_extracted']}")
    print(f"  drugs    : {', '.join(m['drugs'])}")
    print(f"  outcomes : {len(m['outcomes'])} domains")
    print(f"  prisma   : {p['records_in_review']} in review -> "
          f"{p['advanced_to_fulltext']} full-text -> {p['included']} included "
          f"-> {p['extracted']} extracted")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
