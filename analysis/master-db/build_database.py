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
# Consensus row selection
#
# The extraction export carries ONE ROW PER REVIEWER PER STUDY (Covidence emits
# every reviewer's independent extraction). Consensus has not been run yet, so
# for the pilot a single reviewer's rows stand in for consensus. All other rows
# are still counted (meta.extraction_coverage) so the dashboard can report
# dual-extraction progress, but they do not populate study records.
#
# Set to None once Covidence consensus rows are available — then every row in
# the export is used and duplicates are resolved by "last row wins".
# ---------------------------------------------------------------------------
CONSENSUS_REVIEWER = "Parker Singleton"

# ---------------------------------------------------------------------------
# Outcome taxonomy
#
# The revised template replaced the single free-form `Outcomes` cell with 15
# outcome-CATEGORY columns, each holding a ";"-separated list of the specific
# measures assessed within that category. That gives two levels of granularity:
#   outcome_domains[]  -> the category names populated for a study (clean facet)
#   outcome_measures[] -> "Domain: measure" strings (detail view / export)
# ---------------------------------------------------------------------------
OUTCOME_DOMAINS = [
    "Cognitive",
    "Drug experience questionnaires",
    "Molecular",
    "Neuroimaging",
    "Physiological/Autonomic",
    "PK/PD",
    "Psychiatric",
    "Functioning and well-being",
    "Psychological process",
    "Safety & tolerability",
    "Sensorimotor & perception",
    "Somatic health",
    "Therapy process",
    "Trial integrity",
    "Other outcomes",
]

# ---------------------------------------------------------------------------
# Controlled vocabularies for normalization + light auto-derivation.
#
# Used two ways: (1) to normalize the extracted drug/population cells into
# consistent facet labels, and (2) to auto-derive facets from title/abstract for
# studies that are not yet extracted. Extracted values always take precedence.
# `_derive_all` returns EVERY match (studies routinely administer >1 drug).
# ---------------------------------------------------------------------------
DRUG_PATTERNS = [
    ("MDMA", r"mdma|methylenedioxymethamphetamine|ecstasy|midomafetamine"),
    ("MDA", r"\bmda\b|methylenedioxyamphetamine"),
    ("Psilocybin", r"psilocybin|psilocin|psilocyb"),
    ("LSD", r"\blsd\b|lysergic|lysergide"),
    ("Ayahuasca", r"ayahuasca"),
    ("5-MeO-DMT", r"5-meo"),
    ("DMT", r"\bdmt\b|dimethyltryptamine"),
    ("Mescaline", r"mescaline"),
    ("2C-B", r"2c-b|bromo-2,5-dimethoxyphenethylamine"),
    ("Salvinorin A", r"salvinorin|salvia divinorum"),
    ("Ibogaine", r"ibogaine|noribogaine"),
    ("Ketamine", r"ketamine|esketamine"),
]

INDICATION_PATTERNS = [
    ("PTSD", r"ptsd|post[- ]?traumatic|posttraumatic"),
    ("Depression", r"depress|\bmdd\b"),
    ("Anxiety", r"anxiety|anxiolytic"),
    ("Alcohol use", r"alcohol"),
    ("Opioid use", r"opioid|heroin"),
    ("OCD", r"obsessive|\bocd\b"),
    ("Pain", r"\bpain\b|analgesic|nocicep"),
    ("Tinnitus", r"tinnitus"),
    ("Substance use", r"addiction|substance use|smoking|nicotine|cocaine"),
]

# Comparator cells are ";"-separated; each item is classified independently so a
# study can be both placebo- and active-controlled.
COMPARATOR_PATTERNS = [
    ("Placebo", r"placebo"),
    ("Low-dose active", r"low[- ]dose"),
    ("Waitlist / care as usual", r"waitlist|care as usual"),
    ("Psychotherapy", r"psychotherapy|hypnosis"),
    ("Active drug", r"."),  # catch-all: any other named drug
]


def _clean(s: str | None) -> str:
    return (s or "").strip()


def _classify(path: str, header: list[str]) -> str | None:
    """Return 'extraction', 'included', or None for a CSV given its header.

    The extraction export is identified by `Reviewer Name` + `Covidence #` only.
    It deliberately does NOT key on template-specific columns: the template is
    still being revised, and an earlier version of this check required a
    `Study type` column that a template change later deleted — which silently
    dropped the entire extraction export (n_extracted fell to 0 with no error).
    `build()` now also fails loudly on any unclassified reviewer CSV.
    """
    cols = set(header)
    if "Reviewer Name" in cols and "Covidence #" in cols:
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
    """Split a ";"-separated Covidence cell, ignoring separators inside ().

    Several controlled-vocabulary labels contain the separator character inside
    a parenthetical — e.g. "Persisting (PEQ; not HPPD)" — so a naive split
    shreds them into two bogus categories.
    """
    parts, buf, depth = [], [], 0
    for ch in raw or "":
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth = max(0, depth - 1)
        if ch == sep and depth == 0:
            parts.append("".join(buf))
            buf = []
        else:
            buf.append(ch)
    parts.append("".join(buf))
    return [p.strip() for p in parts if p.strip()]


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


def _derive(patterns, *texts) -> str | None:
    blob = " ".join(t.lower() for t in texts if t)
    for label, pat in patterns:
        if re.search(pat, blob):
            return label
    return None


def _derive_all(patterns, *texts) -> list[str]:
    """Every matching label, in vocabulary order (studies often use >1 drug)."""
    blob = " ".join(t.lower() for t in texts if t)
    return [label for label, pat in patterns if re.search(pat, blob)]


def _strip_other(item: str) -> str:
    """'Other: prazosin' -> 'prazosin'."""
    return re.sub(r"(?i)^\s*other\s*:\s*", "", item or "").strip()


def _norm_drugs(raw: str) -> list[str]:
    """Normalize the ";"-separated intervention-drug cell to facet labels.

    Each item is mapped through DRUG_PATTERNS so casing/synonyms collapse
    ("salvinorin A" -> "Salvinorin A"); anything outside the vocabulary is kept
    verbatim (minus an "Other:" prefix) so nothing is silently dropped.
    """
    out: list[str] = []
    for item in _split_list(raw):
        item = _strip_other(item)
        if not item:
            continue
        hits = _derive_all(DRUG_PATTERNS, item)
        for h in (hits or [item[:1].upper() + item[1:]]):
            if h not in out:
                out.append(h)
    return out


def _indication_from(raw: str) -> str:
    """Collapse the ";"-separated Target Population cell to one facet label.

    A named clinical indication always wins over "healthy volunteers" (e.g.
    "depression; Other: frontline clinicians" is a depression trial).
    """
    items = _split_list(raw)
    for item in items:
        hit = _derive(INDICATION_PATTERNS, _strip_other(item))
        if hit:
            return hit
    if any("healthy" in i.lower() for i in items):
        return "Healthy volunteers"
    return _strip_other(items[0]) if items else ""


def _is_healthy(raw: str) -> bool:
    """True when the sample is healthy volunteers rather than a patient group."""
    items = _split_list(raw)
    if not items:
        return False
    if any(_derive(INDICATION_PATTERNS, _strip_other(i)) for i in items):
        return False
    return any("healthy" in i.lower() for i in items)


def _phase(raw_or_enum: str) -> str:
    """Normalize a trial-phase value from either the template or CT.gov.

    ClinicalTrials.gov enums are SCREAMING_SNAKE ('PHASE2', 'NA'); the template
    stores bare digits ('1') plus two NON-phase sentinels, 'Unregistered' and
    'Not Applicable' (see `_registration_status`).
    """
    p = _clean(raw_or_enum).upper()
    if not p or p == "UNREGISTERED":
        return ""
    if p in ("NA", "N/A", "NOT APPLICABLE"):
        return "N/A"
    m = re.fullmatch(r"(?:EARLY[_ ]?PHASE\s*1|EARLY PHASE 1)", p)
    if m:
        return "Early Phase 1"
    m = re.search(r"(\d)", p)
    return f"Phase {m.group(1)}" if m else p.replace("PHASE", "Phase ").strip()


def _registration_status(phase_raw: str, registry_norm: str) -> str:
    """'registered' | 'unregistered' | 'unknown'.

    The template's `Trial Phase` column does double duty: it holds a phase for
    registered trials but the sentinel 'Unregistered' for studies with no trial
    record. A recognized registry id is the stronger signal and wins.
    """
    if registry_norm:
        return "registered"
    if _clean(phase_raw).lower().startswith("unregistered"):
        return "unregistered"
    return "unknown"


def _comparator_types(raw: str) -> list[str]:
    """Classify each ";"-separated comparator item (a study can be both
    placebo- and active-controlled). Order follows COMPARATOR_PATTERNS."""
    out: list[str] = []
    for item in _split_list(raw):
        item = _strip_other(item)
        if not item:
            continue
        for label, pat in COMPARATOR_PATTERNS:
            if re.search(pat, item.lower()):
                if label not in out:
                    out.append(label)
                break
    return out


def _outcomes(ext: dict) -> tuple[list[str], list[str]]:
    """(domains, measures) from the 15 outcome-category columns.

    domains  = category names with at least one measure recorded
    measures = "Domain: measure" for every specific measure
    """
    domains: list[str] = []
    measures: list[str] = []
    for dom in OUTCOME_DOMAINS:
        vals = _split_list(ext.get(dom, ""))
        if not vals:
            continue
        domains.append(dom)
        measures.extend(f"{dom}: {v}" for v in vals)
    return domains, measures


# Deterministic public URLs per registry. Only ClinicalTrials.gov has an API we
# consume (see enrichment), but every recognized id can at least be LINKED — and
# anything we can't link directly falls back to the WHO ICTRP search portal,
# which resolves an id from any of its member registries.
# All patterns below were verified to resolve to the right trial record.
ICTRP_SEARCH = "https://trialsearch.who.int/?TrialID={}"


def _registry_url(reg: str) -> str:
    """Best public URL for a raw registry cell (which may list several ids).

    Prefers the id that actually resolves: a Dutch record, for example, is often
    recorded as "NL70508.068.1; NL-OMON55178" — the ABR/CCMO number comes first
    but only the OMON number resolves on onderzoekmetmensen.nl.
    """
    reg = reg or ""
    m = re.search(r"NCT\d+", reg)
    if m:
        return f"https://clinicaltrials.gov/study/{m.group()}"
    m = re.search(r"ISRCTN\s*(\d+)", reg, re.I)
    if m:
        return f"https://www.isrctn.com/ISRCTN{m.group(1)}"
    m = re.search(r"ACTRN\s*(\d+)", reg, re.I)
    if m:                                    # short form redirects to the record
        return f"https://www.anzctr.org.au/ACTRN{m.group(1)}.aspx"
    m = re.search(r"(?:NL-)?OMON\s*(\d+)", reg, re.I)
    if m:
        return f"https://onderzoekmetmensen.nl/en/trial/{m.group(1)}"
    m = re.search(r"DRKS\s*(\d+)", reg, re.I)
    if m:
        return f"https://drks.de/search/en/trial/DRKS{m.group(1)}"
    # Everything else recognizable → the WHO portal, which federates 20+ registries.
    norm = _norm_registry(reg)
    return ICTRP_SEARCH.format(norm) if norm else ""


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


def _norm_doi(raw: str) -> str:
    """Canonical lowercase DOI for matching ('https://doi.org/10.X/Y ' -> '10.x/y')."""
    d = _clean(raw).lower()
    d = re.sub(r"^https?://(dx\.)?doi\.org/", "", d)
    d = re.sub(r"^doi:\s*", "", d)
    return d.strip().rstrip(".")


def _link_trials(studies: list) -> dict:
    """Group papers into trials so the dashboard can show reports of one trial.

    Two identifiers make a trial, in priority order:

    1. **Registry id** (`registry_norm`) — the canonical case.
    2. **Parent-paper DOI** — for UNREGISTERED trials the template records the
       source paper's DOI, so several reports of the same unregistered trial
       share a key of the form ``doi:10.xxxx/yyy``. A paper that is itself named
       as a parent by another paper adopts its *own* DOI as that key, so the
       source paper joins the group. If the named parent is in the database and
       *is* registered, the child inherits the parent's registry id instead —
       a secondary analysis whose own registry field was left blank.

    Mutates each study (adds `registry_norm`, `parent_doi_norm`, `trial_key`,
    `trial_key_source`, `connected_ids`) and returns {trial_key: [covidence_id]}.
    """
    from collections import defaultdict

    for s in studies:
        s["registry_norm"] = _norm_registry(s.get("registry", ""))
        s["parent_doi_norm"] = _norm_doi(s.get("parent_study_doi", ""))
        s["trial_key"] = s["registry_norm"] or None
        s["trial_key_source"] = "registry" if s["registry_norm"] else ""

    by_doi = {_norm_doi(s["doi"]): s for s in studies if s.get("doi")}
    # DOIs cited as a parent by at least one paper — these identify the trial.
    parent_dois = {s["parent_doi_norm"] for s in studies if s["parent_doi_norm"]}

    for s in studies:
        if s["trial_key"]:
            # A registered paper that is also cited as a parent keeps its
            # registry id; children resolving through it land on the same key.
            continue
        parent = by_doi.get(s["parent_doi_norm"])
        if parent and parent.get("registry_norm"):
            s["trial_key"] = parent["registry_norm"]        # inherit registry
            s["trial_key_source"] = "parent-registry"
        elif s["parent_doi_norm"]:
            s["trial_key"] = "doi:" + s["parent_doi_norm"]  # unregistered trial
            s["trial_key_source"] = "parent-doi"
        elif _norm_doi(s.get("doi", "")) in parent_dois:
            s["trial_key"] = "doi:" + _norm_doi(s["doi"])   # this IS the source paper
            s["trial_key_source"] = "source-paper"

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


def _ym(date: str) -> str:
    """'2009-01-15' / '2009-01' -> '2009-01' (CT.gov date granularity varies)."""
    m = re.match(r"(\d{4})-(\d{2})", _clean(date))
    return f"{m.group(1)}-{m.group(2)}" if m else ""


def _prospective(registered: str, start: str) -> bool | None:
    """Was the trial registered before it started enrolling?

    Compared at month granularity because CT.gov start dates are often
    month-only; registration in the same month as the start counts as
    prospective, the conventional (lenient) reading. None when either date is
    missing, so 'unknown' never masquerades as 'retrospective'.
    """
    r, s = _ym(registered), _ym(start)
    return (r <= s) if (r and s) else None


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
    start = (stt.get("startDateStruct", {}) or {}).get("date", "")
    # first public posting is the registration date of record
    registered = _clean(stt.get("studyFirstSubmitDate")) or \
        (stt.get("studyFirstPostDateStruct", {}) or {}).get("date", "")

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
        # raw signals for the design-mislabel check (see _registry_qc)
        "n_arm_groups": len(ai.get("armGroups") or []),
        "max_interventions_per_arm": max(
            [len(a.get("interventionNames") or []) for a in (ai.get("armGroups") or [])] or [0]),
        "sponsor": lead.get("name", ""),
        "industry": lead.get("class") == "INDUSTRY",
        "start": start,
        "completion": completion,
        "registered": registered,
        # True = registered on/before the enrolment start month; None = unknown
        "prospective": _prospective(registered, start),
        "countries": countries,
        "primary_outcomes": [
            (o.get("measure", "") + (" — " + o["timeFrame"] if o.get("timeFrame") else ""))
            for o in (om.get("primaryOutcomes") or []) if o.get("measure")
        ],
        "results_posted": bool(raw.get("hasResults")) or bool(stt.get("resultsFirstPostDateStruct")),
    }


def build_trials(studies: list, fetch: bool = False, refresh: bool = False) -> list:
    """One entry per identified trial: registry details (enriched) + linked papers.

    Covers registered trials (registry id) and unregistered trials identified by
    their source-paper DOI (`doi:` keys). Papers with neither identifier have no
    `trial_key` and stay paper-only.
    """
    groups: dict = {}
    order: list = []
    raw_registry: dict = {}     # trial_key -> a paper's raw registry cell, for linking
    for s in studies:
        k = s.get("trial_key")
        if k:
            if k not in groups:
                groups[k] = []
                order.append(k)
            groups[k].append(s["covidence_id"])
            if s.get("registry") and k not in raw_registry:
                raw_registry[k] = s["registry"]

    trials = []
    for k in order:
        nct = k if re.fullmatch(r"NCT\d+", k) else None
        if k.startswith("doi:"):
            # Unregistered trial, identified by the DOI of its source paper.
            doi = k[4:]
            trials.append({
                "trial_key": k, "registry": "", "registry_url": f"https://doi.org/{doi}",
                "source": "source-paper", "fetched": None,
                "fetch_status": "unregistered", "details": None,
                "paper_ids": groups[k], "source_doi": doi,
            })
        elif nct:
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
            # No API adapter for this registry, but the record is still reachable:
            # link the registry directly where the id resolves, else WHO ICTRP.
            url = _registry_url(raw_registry.get(k, k))
            trials.append({
                "trial_key": k, "registry": k,
                "registry_url": url,
                "registry_link_is_ictrp": url.startswith("https://trialsearch.who.int"),
                "source": "other", "fetched": None,
                "fetch_status": "unsupported_registry", "details": None,
                "paper_ids": groups[k],
            })
    # most papers first, registered trials ahead of unregistered, then by id
    trials.sort(key=lambda t: (-len(t["paper_ids"]),
                               t["trial_key"].startswith("doi:"),
                               t["trial_key"]))
    return trials


def _registry_qc(trials: list) -> list:
    """Registry self-contradictions worth a human look.

    The one that matters in practice: some registrants put *every* intervention
    into a single arm group. When they do, `interventionModel` stops being
    trustworthy — a study where one arm receives both drug and placebo is a
    crossover however it is labelled. NCT00823407 (Baggott 2010) is registered
    SINGLE_GROUP + RANDOMIZED with one arm containing "Drug: MDA" and
    "Drug: Placebo"; NCT01951508 has the same one-arm-many-drugs shape but is
    correctly labelled CROSSOVER. A single group has nothing to randomise
    between, so SINGLE_GROUP + RANDOMIZED is a contradiction on its face.
    """
    out = []
    for t in trials:
        d = t.get("details")
        if not d:
            continue
        one_arm_many_drugs = d.get("n_arm_groups") == 1 and d.get("max_interventions_per_arm", 0) > 1
        if d.get("model") == "Single Group" and d.get("allocation") == "Randomized":
            out.append(
                f"{t['trial_key']}: registered as Single Group *and* Randomized — a single group "
                f"has nothing to randomise between"
                + (", and its one arm lists several interventions, so this is very likely a "
                   "mislabelled crossover" if one_arm_many_drugs else "")
                + ". Do not trust its design model."
            )
        elif one_arm_many_drugs and d.get("model") not in ("Crossover", "Factorial"):
            out.append(
                f"{t['trial_key']}: one arm group lists several interventions but the design "
                f"model is {d.get('model') or 'unset'!r} — check whether it is a crossover."
            )
        if d.get("model") and not d.get("allocation"):
            out.append(f"{t['trial_key']}: no allocation recorded in the registry.")
    return out


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


# Upstream PRISMA counts that live on the Covidence dashboard, not in any stage
# export. `auto_marked_ineligible` is Covidence's automated screening: in PRISMA
# 2020 those records are "removed before screening", alongside duplicates — NOT
# counted as screened — which is why `records_screened` excludes them.
MANUAL_KEYS = ("records_identified", "duplicates_removed",
               "auto_marked_ineligible", "excluded_title_abstract")


def _load_manual() -> dict:
    """Load optional hand-entered PRISMA numbers from prisma_manual.json.

    Covidence stage exports omit 'records identified', 'duplicates removed',
    'records auto-marked ineligible' and 'excluded at title/abstract screening',
    so the snapshot funnel starts mid-stream. These let the diagram show the full
    top of the funnel once known.

    Keys are accepted in either snake_case or hyphenated form, so a hand-edited
    file using `auto-marked-ineligible` works without being reformatted.
    """
    manual = {k: None for k in MANUAL_KEYS}
    if os.path.exists(MANUAL_PATH):
        with open(MANUAL_PATH, encoding="utf-8") as fh:
            raw = json.load(fh)
        for k in MANUAL_KEYS:
            v = raw.get(k, raw.get(k.replace("_", "-")))
            manual[k] = v if isinstance(v, int) else None
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
    # PRISMA 2020: records screened = identified − (duplicates + automation removals).
    # Equivalently records still in review + those excluded at title/abstract, which
    # is what we can always compute; the two agree when the numbers reconcile.
    manual["records_screened"] = (records_in_review + ex_ta) if isinstance(ex_ta, int) else None
    manual["removed_before_screening"] = (
        manual["duplicates_removed"] + manual["auto_marked_ineligible"]
        if isinstance(manual["duplicates_removed"], int)
        and isinstance(manual["auto_marked_ineligible"], int) else None
    )
    manual["complete"] = all(manual[k] is not None for k in MANUAL_KEYS)

    # Reconciliation: identified − removed-before-screening − excluded at
    # title/abstract must equal the records the stage exports still account for.
    # A mismatch means a hand-entered number is stale or a stage export is out of
    # sync — surfaced rather than silently drawn as a wrong diagram.
    manual["reconciles"] = None
    manual["reconcile_delta"] = None
    if manual["complete"]:
        expected = (manual["records_identified"] - manual["removed_before_screening"] - ex_ta)
        manual["reconcile_delta"] = expected - records_in_review
        manual["reconciles"] = manual["reconcile_delta"] == 0

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
        elif "Reviewer Name" in header:
            # A reviewer export we failed to recognize would silently zero out
            # the extraction data (this happened once when a template revision
            # deleted a column the classifier keyed on). Never fail quietly.
            sys.exit(f"ERROR: {os.path.relpath(path, REPO)} has a 'Reviewer Name' column but "
                     "could not be classified as an extraction export (no 'Covidence #').")

    inc_path = _latest(included_files)
    ext_path = _latest(extraction_files)
    if not inc_path:
        sys.exit("ERROR: no '*included*.csv' bibliographic export found in data/")

    warnings: list[str] = []

    # ---- read extraction rows, keeping only the consensus reviewer ----
    # Covidence emits one row per reviewer per study. Every row is tallied for
    # coverage stats, but only CONSENSUS_REVIEWER's rows populate the database
    # (see the note on CONSENSUS_REVIEWER).
    extraction: dict[int, dict] = {}
    reviewers: dict[str, int] = {}
    rows_by_study: dict[int, set] = {}
    # Rows with core fields filled but every outcome column still blank. These are
    # NOT errors — extraction is in progress, and only the consensus reviewer's rows
    # are verified complete. Tracked as progress (and as the reason outcome-domain
    # figures must be computed over verified rows only), never warned about.
    missing_outcomes: dict[str, int] = {}
    n_extraction_rows = 0
    if ext_path:
        with open(ext_path, newline="", encoding="utf-8-sig") as fh:
            for row in csv.DictReader(fh):
                cid = _norm_covidence(row.get("Covidence #", ""))
                if cid is None:
                    continue
                who = _clean(row.get("Reviewer Name"))
                n_extraction_rows += 1
                reviewers[who] = reviewers.get(who, 0) + 1
                rows_by_study.setdefault(cid, set()).add(who)
                worked = any(_clean(row.get(f)) for f in
                             ("N randomized", "Psychedelic/Intervention Drug(s)",
                              "Target Population", "Comparator Drug"))
                if worked and not any(_clean(row.get(d)) for d in OUTCOME_DOMAINS):
                    missing_outcomes[who] = missing_outcomes.get(who, 0) + 1
                if CONSENSUS_REVIEWER and who != CONSENSUS_REVIEWER:
                    continue
                extraction[cid] = row
    if CONSENSUS_REVIEWER and not extraction:
        warnings.append(
            f"no extraction rows matched CONSENSUS_REVIEWER={CONSENSUS_REVIEWER!r} "
            f"(reviewers present: {', '.join(sorted(reviewers)) or 'none'})"
        )

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
            # `drugs` keeps every agent administered (many studies compare 2-3);
            # `drug` is the first, used for the table badge and legacy sorting.
            drug_ext = _clean(ext.get("Psychedelic/Intervention Drug(s)"))
            if drug_ext:
                drugs = _norm_drugs(drug_ext)
                drug_source = "extracted"
            else:
                drugs = _derive_all(DRUG_PATTERNS, row.get("Title", ""), row.get("Abstract", ""))
                drug_source = "auto" if drugs else "unknown"
            drug = drugs[0] if drugs else "Unclear"

            # Indication: extracted target population wins; else derive.
            pop_ext = _clean(ext.get("Target Population"))
            if pop_ext:
                indication = _indication_from(pop_ext) or "Unclear"
                indication_source = "extracted"
                healthy = _is_healthy(pop_ext)
            else:
                indication = _derive(
                    INDICATION_PATTERNS, row.get("Title", ""), row.get("Abstract", ""),
                    _clean(row.get("Tags")),
                )
                healthy = not indication and bool(re.search(
                    r"healthy", (row.get("Title", "") + row.get("Abstract", "")).lower()
                ))
                if healthy:
                    indication = "Healthy volunteers"
                indication_source = "auto" if indication else "unknown"
                indication = indication or "Unclear"

            # ---- revised-template fields ----
            phase_raw = _clean(ext.get("Trial Phase"))
            registry_norm = _norm_registry(registry)
            phase = _phase(phase_raw)
            reg_status = _registration_status(phase_raw, registry_norm)
            outcome_domains, outcome_measures = _outcomes(ext) if is_ext else ([], [])
            n_rand = _to_int(ext.get("N randomized"))
            n_anal = _to_int(ext.get("N analyzed (if applicable)"))
            sex = _clean(ext.get("Sex-specific population?")).lower()

            # QC: a phase implies a registered trial. Flag the contradiction
            # rather than silently trusting either field.
            if is_ext and phase and phase != "N/A" and reg_status != "registered":
                warnings.append(
                    f"#{cid} {_clean(row.get('Study'))}: '{phase_raw}' recorded in Trial Phase "
                    f"but no trial registry id — registration status is 'unknown'."
                )
            if is_ext and n_rand and n_anal and n_anal > n_rand:
                warnings.append(
                    f"#{cid} {_clean(row.get('Study'))}: N analyzed ({n_anal}) > N randomized ({n_rand})."
                )

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
                    "drugs": drugs,
                    "drug_source": drug_source,
                    "indication": indication,
                    "indication_source": indication_source,
                    "healthy_volunteers": healthy,
                    # ---- extraction template fields ----
                    "extracted": is_ext,
                    "reviewer": _clean(ext.get("Reviewer Name")),
                    "parent_study_doi": _clean(ext.get("Parent study DOI")),
                    "phase": phase,
                    "phase_raw": phase_raw,
                    "registration_status": reg_status,
                    "n_randomized": n_rand,
                    "n_analyzed": n_anal,
                    # best available sample size, for sorting/plotting
                    "n": n_rand if n_rand is not None else n_anal,
                    "n_source": ("randomized" if n_rand is not None
                                 else "analyzed" if n_anal is not None else ""),
                    "drugs_raw": drug_ext,
                    "coadmin": _clean(ext.get("Co-administration/Pre-treatment Drug(s)")),
                    "comparator": _clean(ext.get("Comparator Drug")),
                    "comparator_types": _comparator_types(ext.get("Comparator Drug", "")),
                    "population": pop_ext,
                    "sex_specific": sex if sex in ("male", "female") else "",
                    "outcome_domains": outcome_domains,
                    "outcome_measures": outcome_measures,
                    "qualitative_outcome": _clean(ext.get("What is the qualitative outcome?")),
                    "extraction_notes": _clean(ext.get("Notes")),
                    # how many reviewers have extracted this study so far
                    "n_extractions": len(rows_by_study.get(cid, ())),
                }
            )

    # sort newest first, then alphabetically by study id
    studies.sort(key=lambda s: (-(s["year"] or 0), s["study_id"].lower()))

    # group papers into trials (by registry, + parent-DOI for secondary analyses)
    by_key = _link_trials(studies)
    n_trials = len(by_key) + sum(1 for s in studies if not s["trial_key"])
    trials = build_trials(studies, fetch=fetch, refresh=refresh)

    n_extracted = sum(1 for s in studies if s["extracted"])

    warnings.extend(_registry_qc(trials))

    prisma = build_prisma(n_extracted)
    if prisma["manual"]["reconciles"] is False:
        d = prisma["manual"]["reconcile_delta"]
        warnings.append(
            f"PRISMA numbers do not reconcile by {d:+d}: identified − duplicates − "
            f"auto-marked-ineligible − excluded at title/abstract should equal the "
            f"{prisma['records_in_review']} records the stage exports account for. "
            f"Check prisma_manual.json against the Covidence dashboard."
        )

    out = {
        "meta": {
            "generated": _dt.date.today().isoformat(),
            "review_id": re.search(r"\d+", os.path.basename(inc_path)).group(),
            "n_included": len(studies),
            "n_extracted": n_extracted,
            "drugs": sorted({d for s in studies for d in s["drugs"]}),
            "indications": sorted({s["indication"] for s in studies if s["indication"] != "Unclear"}),
            # facet vocabularies, restricted to values actually present
            "outcome_domains": [d for d in OUTCOME_DOMAINS
                                if any(d in s["outcome_domains"] for s in studies)],
            "outcome_measures": sorted({m for s in studies for m in s["outcome_measures"]}),
            "phases": sorted({s["phase"] for s in studies if s["phase"]}),
            "comparator_types": [c for c, _ in COMPARATOR_PATTERNS
                                 if any(c in s["comparator_types"] for s in studies)],
            "registries": sorted({s["registry_norm"] for s in studies if s["registry_norm"]}),
            "n_trials": n_trials,
            "n_registered_trials": sum(1 for t in trials if not t["trial_key"].startswith("doi:")),
            "n_unregistered_trials": sum(1 for t in trials if t["trial_key"].startswith("doi:")),
            "n_trials_enriched": sum(1 for t in trials if t["fetch_status"] == "ok"),
            "n_multi_paper_trials": sum(1 for ids in by_key.values() if len(ids) > 1),
            "year_min": min((s["year"] for s in studies if s["year"]), default=None),
            "year_max": max((s["year"] for s in studies if s["year"]), default=None),
            # extraction provenance: which rows became the database, and how far
            # dual extraction has progressed across the whole export
            "consensus_reviewer": CONSENSUS_REVIEWER,
            "extraction_coverage": {
                "rows": n_extraction_rows,
                "studies_with_any_extraction": len(rows_by_study),
                "studies_with_consensus_row": n_extracted,
                "studies_dual_extracted": sum(1 for v in rows_by_study.values() if len(v) > 1),
                "reviewers": dict(sorted(reviewers.items(), key=lambda kv: (-kv[1], kv[0]))),
                "rows_missing_outcomes": dict(sorted(missing_outcomes.items(),
                                                     key=lambda kv: (-kv[1], kv[0]))),
            },
            "warnings": warnings,
            "source_included": os.path.relpath(inc_path, REPO),
            "source_extraction": os.path.relpath(ext_path, REPO) if ext_path else None,
        },
        "prisma": prisma,
        "trials": trials,
        "studies": studies,
    }
    return out


def reviewers_done(cov: dict, who: str) -> str:
    """'3/12 done' for a reviewer's outcome-column progress."""
    total = cov["reviewers"].get(who, 0)
    return f"{total - cov['rows_missing_outcomes'][who]}/{total} done"


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
    cov = m["extraction_coverage"]
    print(f"Wrote {os.path.relpath(OUT_PATH, REPO)}")
    print(f"  included : {m['n_included']}  extracted: {m['n_extracted']}")
    print(f"  drugs    : {', '.join(m['drugs'])}")
    print(f"  outcomes : {len(m['outcome_domains'])} domains, "
          f"{len(m['outcome_measures'])} distinct measures")
    print(f"  extract. : {cov['rows']} rows by {len(cov['reviewers'])} reviewers over "
          f"{cov['studies_with_any_extraction']} studies "
          f"({cov['studies_dual_extracted']} dual-extracted); "
          f"consensus source = {m['consensus_reviewer'] or 'all rows'}")
    if cov["rows_missing_outcomes"]:
        prog = ", ".join(f"{w} {reviewers_done(cov, w)}"
                         for w in cov["rows_missing_outcomes"])
        print(f"  progress : outcome columns still blank on "
              f"{sum(cov['rows_missing_outcomes'].values())} in-progress row(s) — {prog}")
    print(f"  prisma   : {p['records_in_review']} in review -> "
          f"{p['advanced_to_fulltext']} full-text -> {p['included']} included "
          f"-> {p['extracted']} extracted")
    print(f"  trials   : {m['n_registered_trials']} registered, "
          f"{m['n_trials_enriched']} enriched  ({dict(statuses)})")
    if m["warnings"]:
        print(f"\n  {len(m['warnings'])} data-quality warning(s):")
        for w in m["warnings"]:
            print(f"    ! {w}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
