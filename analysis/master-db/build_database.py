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
import time
import urllib.error
import urllib.request

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
DATA_DIR = os.path.join(HERE, "data")
OUT_PATH = os.path.join(REPO, "_data", "master_db.json")
# Optional manual PRISMA numbers not present in the Covidence stage exports.
MANUAL_PATH = os.path.join(HERE, "prisma_manual.json")
# Local cache of fetched registry responses (gitignored; parsed details live in
# the committed _data/master_db.json so the *site* build never needs the network).
CACHE_DIR = os.path.join(HERE, ".registry_cache")
CTGOV_API = "https://clinicaltrials.gov/api/v2/studies/{}"
CACHE_TTL_DAYS = 30

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


# Recognized trial-registry id formats (used as the trial-grouping key). Anything
# not matching — e.g. a Web of Science accession (WOS:...) — is treated as "no
# registry" so it doesn't masquerade as a trial id.
_REGISTRY_RE = re.compile(
    r"(NCT\d+|ISRCTN\d+|EudraCT[\s:-]*[\d-]+|ACTRN\d+|DRKS\d+|ChiCTR[\w-]+|NTR\d+"
    r"|NL[-\w.]+|JPRN[-\w]+|UMIN\d+|PACTR\d+|IRCT[\w-]+)",
    re.IGNORECASE,
)


def _norm_registry(registry: str) -> str:
    """Canonical trial id from a registry/accession string, or '' if not a registry.

    Prefers an NCT id (most common); falls back to other known registry formats.
    """
    if not registry:
        return ""
    nct = re.search(r"NCT\d+", registry)
    if nct:
        return nct.group()
    m = _REGISTRY_RE.search(registry)
    return m.group(1).strip() if m else ""


def _link_trials(studies: list) -> dict:
    """Group studies into trials so the dashboard can show papers sharing a trial.

    A trial is keyed by its normalized registry id. A secondary-analysis paper with
    no registry of its own is attached to its parent's trial via `Parent Study DOI`.
    Mutates each study (adds `registry_norm`, `trial_key`, `connected_ids`) and
    returns {trial_key: [covidence_id, ...]} for trials that have a registry.
    """
    from collections import defaultdict

    for s in studies:
        s["registry_norm"] = _norm_registry(s.get("registry", ""))
        s["trial_key"] = s["registry_norm"] or None

    # Attach registry-less secondary analyses to their parent study's trial.
    by_doi = {s["doi"].lower(): s for s in studies if s.get("doi")}
    for s in studies:
        if s["trial_key"]:
            continue
        parent_doi = re.sub(r"^https?://doi\.org/", "", (s.get("parent_study_doi") or "").lower())
        parent = by_doi.get(parent_doi)
        if parent and parent.get("trial_key"):
            s["trial_key"] = parent["trial_key"]

    by_key: dict = defaultdict(list)
    for s in studies:
        if s["trial_key"]:
            by_key[s["trial_key"]].append(s["covidence_id"])

    for s in studies:
        ids = by_key.get(s["trial_key"], []) if s["trial_key"] else []
        s["connected_ids"] = [cid for cid in ids if cid != s["covidence_id"]]

    return dict(by_key)


# ---------------------------------------------------------------------------
# Trial-registry enrichment (ClinicalTrials.gov API v2; NCT ids only)
#
# Failure modes are first-class: see fetch_status values below. The build never
# raises on a registry problem — it records the status and emits null details, so
# a missing/renamed/non-NCT registry can't break the database.
#   ok                   – fetched (or cached) and parsed
#   not_found            – API returned 404 (withdrawn / typo'd NCT)
#   error                – network/API/parse failure (falls back to stale cache)
#   unsupported_registry – not an NCT id (e.g. the Dutch NL/OMON registry); the
#                          CT.gov API can't resolve it. Handle upstream (manual /
#                          a per-registry adapter) — details stay null.
#   not_fetched          – fetching disabled (--no-fetch) and nothing cached yet
# ---------------------------------------------------------------------------
def _enum(s: str) -> str:
    """ClinicalTrials.gov enums are SCREAMING_SNAKE → 'Title Case'."""
    return (s or "").replace("_", " ").title()


def _phase(p: str) -> str:
    p = (p or "").upper()
    return {"NA": "N/A", "EARLY_PHASE1": "Early Phase 1"}.get(p, p.replace("PHASE", "Phase ").strip())


def _registry_raw(nct: str, fetch: bool, refresh: bool):
    """Return (raw_json|None, status, fetched_date|None). Cache-first; never raises."""
    path = os.path.join(CACHE_DIR, nct + ".json")
    if os.path.exists(path) and not refresh:
        try:
            c = json.load(open(path, encoding="utf-8"))
            age = (_dt.date.today() - _dt.date.fromisoformat(c.get("fetched", "1900-01-01"))).days
            # use cache if fresh, or whenever we're not allowed to fetch
            if c.get("status") == "ok" and c.get("raw") and (age < CACHE_TTL_DAYS or not fetch):
                return c["raw"], "ok", c.get("fetched")
        except Exception:
            pass
    if not fetch:
        return None, "not_fetched", None
    try:
        req = urllib.request.Request(
            CTGOV_API.format(nct),
            headers={"User-Agent": "SYPRES-master-db/1.0 (+https://sypres.io)"},
        )
        with urllib.request.urlopen(req, timeout=20) as resp:
            raw = json.loads(resp.read().decode("utf-8"))
        fetched = _dt.date.today().isoformat()
        os.makedirs(CACHE_DIR, exist_ok=True)
        with open(path, "w", encoding="utf-8") as fh:
            json.dump({"fetched": fetched, "status": "ok", "raw": raw}, fh, ensure_ascii=False)
        time.sleep(0.34)  # be polite to the API
        return raw, "ok", fetched
    except urllib.error.HTTPError as e:
        status = "not_found" if e.code == 404 else "error"
    except Exception:
        status = "error"
    # fetch failed: fall back to a stale cached copy if we have one
    if os.path.exists(path):
        try:
            c = json.load(open(path, encoding="utf-8"))
            if c.get("raw"):
                return c["raw"], "ok", c.get("fetched")
        except Exception:
            pass
    return None, status, None


def _parse_ctgov(raw: dict) -> dict | None:
    """Pull the trial-card fields out of a CT.gov v2 study record (defensively)."""
    if not isinstance(raw, dict):
        return None
    ps = raw.get("protocolSection")
    if not ps:
        return None
    ident = ps.get("identificationModule", {}) or {}
    stt = ps.get("statusModule", {}) or {}
    dz = ps.get("designModule", {}) or {}
    sp = ps.get("sponsorCollaboratorsModule", {}) or {}
    ai = ps.get("armsInterventionsModule", {}) or {}
    om = ps.get("outcomesModule", {}) or {}
    cl = ps.get("contactsLocationsModule", {}) or {}
    cm = ps.get("conditionsModule", {}) or {}
    di = dz.get("designInfo", {}) or {}
    mi = di.get("maskingInfo", {}) or {}
    lead = sp.get("leadSponsor", {}) or {}
    en = dz.get("enrollmentInfo", {}) or {}

    masking = _enum(mi.get("masking"))
    who = mi.get("whoMasked") or []
    if masking and who:
        masking += " (" + ", ".join(_enum(w).lower() for w in who) + ")"

    countries = []
    for loc in (cl.get("locations") or []):
        c = loc.get("country")
        if c and c not in countries:
            countries.append(c)

    completion = (stt.get("completionDateStruct", {}) or {}).get("date") or \
        (stt.get("primaryCompletionDateStruct", {}) or {}).get("date") or ""

    return {
        "title": ident.get("officialTitle") or ident.get("briefTitle") or "",
        "status": _enum(stt.get("overallStatus")),
        "study_type": _enum(dz.get("studyType")),
        "phase": ", ".join(_phase(p) for p in (dz.get("phases") or [])),
        "allocation": _enum(di.get("allocation")),
        "model": _enum(di.get("interventionModel")),
        "masking": masking,
        "enrollment": (en.get("count") if isinstance(en.get("count"), int) else None),
        "enrollment_type": _enum(en.get("type")),
        "conditions": cm.get("conditions") or [],
        "arms": [a.get("label", "") + (" — " + _enum(a.get("type")) if a.get("type") else "")
                 for a in (ai.get("armGroups") or []) if a.get("label")],
        "sponsor": lead.get("name", ""),
        "industry": lead.get("class") == "INDUSTRY",
        "start": (stt.get("startDateStruct", {}) or {}).get("date", ""),
        "completion": completion,
        "countries": countries,
        "primary_outcomes": [
            (o.get("measure", "") + (" — " + o["timeFrame"] if o.get("timeFrame") else ""))
            for o in (om.get("primaryOutcomes") or []) if o.get("measure")
        ],
        "results_posted": bool(raw.get("hasResults")) or bool(stt.get("resultsFirstPostDateStruct")),
    }


def build_trials(studies: list, fetch: bool = False, refresh: bool = False) -> list:
    """One entry per *registered* trial: registry details (enriched) + linked papers.

    Unregistered papers (no `trial_key`) are paper-only and never become trials.
    """
    groups: dict = {}
    order: list = []
    for s in studies:
        k = s.get("trial_key")
        if k:
            if k not in groups:
                groups[k] = []
                order.append(k)
            groups[k].append(s["covidence_id"])

    trials = []
    for k in order:
        nct = k if re.fullmatch(r"NCT\d+", k) else None
        if nct:
            raw, status, fetched = _registry_raw(nct, fetch, refresh)
            details = _parse_ctgov(raw)
            if status == "ok" and details is None:
                status = "error"  # had data but couldn't parse it
            trials.append({
                "trial_key": k, "registry": k,
                "registry_url": f"https://clinicaltrials.gov/study/{nct}",
                "source": "clinicaltrials.gov", "fetched": fetched,
                "fetch_status": status, "details": details, "paper_ids": groups[k],
            })
        else:
            trials.append({
                "trial_key": k, "registry": k, "registry_url": "",
                "source": "other", "fetched": None,
                "fetch_status": "unsupported_registry", "details": None,
                "paper_ids": groups[k],
            })
    # most papers first, then by registry id
    trials.sort(key=lambda t: (-len(t["paper_ids"]), t["trial_key"]))
    return trials


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


def build(fetch: bool = False, refresh: bool = False) -> dict:
    """Read the Covidence exports and return the full database dict
    (`{meta, prisma, trials, studies}`).

    `fetch` controls registry enrichment (network). It defaults to False so tests
    and offline builds stay hermetic; `main()` turns it on. `refresh` ignores cache
    TTL and re-fetches. The *site* build never needs the network — it reads the
    committed _data/master_db.json, which already contains the parsed details."""
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

    # group papers into trials (by registry, + parent-DOI for secondary analyses)
    by_key = _link_trials(studies)
    n_trials = len(by_key) + sum(1 for s in studies if not s["trial_key"])
    trials = build_trials(studies, fetch=fetch, refresh=refresh)

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
            "registries": sorted({s["registry_norm"] for s in studies if s["registry_norm"]}),
            "n_trials": n_trials,
            "n_registered_trials": len(trials),
            "n_trials_enriched": sum(1 for t in trials if t["fetch_status"] == "ok"),
            "n_multi_paper_trials": sum(1 for ids in by_key.values() if len(ids) > 1),
            "year_min": min((s["year"] for s in studies if s["year"]), default=None),
            "year_max": max((s["year"] for s in studies if s["year"]), default=None),
            "source_included": os.path.relpath(inc_path, REPO),
            "source_extraction": os.path.relpath(ext_path, REPO) if ext_path else None,
        },
        "prisma": build_prisma(n_extracted),
        "trials": trials,
        "studies": studies,
    }
    return out


def main() -> int:
    argv = sys.argv[1:]
    fetch = "--no-fetch" not in argv          # fetch registry details by default
    refresh = "--refresh" in argv             # ignore cache TTL, re-fetch
    out = build(fetch=fetch, refresh=refresh)
    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as fh:
        json.dump(out, fh, ensure_ascii=False, indent=2)

    m, p = out["meta"], out["prisma"]
    from collections import Counter
    statuses = Counter(t["fetch_status"] for t in out["trials"])
    print(f"Wrote {os.path.relpath(OUT_PATH, REPO)}")
    print(f"  included : {m['n_included']}  extracted: {m['n_extracted']}")
    print(f"  drugs    : {', '.join(m['drugs'])}")
    print(f"  outcomes : {len(m['outcomes'])} domains")
    print(f"  prisma   : {p['records_in_review']} in review -> "
          f"{p['advanced_to_fulltext']} full-text -> {p['included']} included "
          f"-> {p['extracted']} extracted")
    print(f"  trials   : {m['n_registered_trials']} registered, "
          f"{m['n_trials_enriched']} enriched  ({dict(statuses)})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
