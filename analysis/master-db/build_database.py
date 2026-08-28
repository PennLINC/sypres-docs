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
    ("Bretisilocin", r"bretisilocin|\bgm-?2505\b"),
    ("LSD", r"\blsd\b|lysergic|lysergide"),
    ("Ayahuasca", r"ayahuasca"),
    # 5-MeO must precede the bare DMT pattern or it is swallowed by it
    ("5-MeO-DMT", r"5-meo"),
    ("DMT", r"\bdmt\b|dimethyltryptamine"),
    ("Mescaline", r"mescaline"),
    ("2C-B", r"2c-b|bromo-2,5-dimethoxyphenethylamine"),
    ("Methylone", r"methylone"),
    ("Salvinorin A", r"salvinorin|salvia divinorum"),
    ("Ibogaine", r"iboga|ibogaine|noribogaine"),
    ("Ketamine", r"ketamine|esketamine"),
]

INDICATION_PATTERNS = [
    ("PTSD", r"ptsd|post[- ]?traumatic|posttraumatic"),
    ("Depression", r"depress|\bmdd\b"),
    ("Anxiety", r"anxiety|anxiolytic"),
    ("Cancer", r"cancer|oncolog|palliative"),
    ("Alcohol use", r"alcohol"),
    ("Opioid use", r"opioid|heroin"),
    ("Cocaine use", r"cocaine"),
    ("Methamphetamine use", r"methamphetamine"),
    ("Tobacco/nicotine use", r"tobacco|nicotine|smoking"),
    ("Eating disorder", r"eating disorder|anorexia|bulimia|binge"),
    ("OCD", r"obsessive|\bocd\b"),
    ("Burnout", r"burnout"),
    ("Migraine", r"migraine|cluster headache"),
    ("Neurological", r"neurological|stroke|\btbi\b|traumatic brain"),
    ("Pain", r"\bpain\b|fibromyalgia|analgesic|nocicep"),
    ("Tinnitus", r"tinnitus"),
    ("Substance use", r"addiction|substance use"),
]

# Blinding is recorded as WHO was masked, not a single/double/triple level: the
# registry stores a party count plus the roles, and the two come apart (a
# "Double" trial may be participant+investigator or participant+care-provider,
# and a "Single" one may mask only the outcomes assessor, leaving the
# participant unblinded). The level is derivable by counting named roles; the
# roles are not derivable from the level. `not-specified` records "a level was
# stated but the roles were not named" — never inferred.
BLINDING_ROLES = ["participant", "care provider", "investigator", "outcomes assessor"]
BLINDING_OTHER = ["not-specified", "open-label", "not reported"]

# Design values the template offers. Deliberately no "single-group": in a
# database restricted to randomised trials it should not exist, and our one
# registry instance was a mislabelled crossover (see `_registry_qc`).
DESIGN_VALUES = ["parallel", "crossover", "factorial", "not reported"]

# ClinicalTrials.gov interventionModel -> the template's design vocabulary, so
# registry-sourced and extracted designs land in the same facet.
DESIGN_FROM_REGISTRY = {
    "Parallel": "parallel", "Crossover": "crossover", "Factorial": "factorial",
    "Sequential": "other", "Single Group": "other",
}

# Comparator cells are ";"-separated; each item is classified independently, so a
# study is often several of these at once — Goodwin 2022 (1/10/25 mg psilocybin)
# is BOTH a low-dose control and a dose-ranging comparison, and a 2x2
# co-administration trial is placebo + both component-alone arms. Any figure over
# these must count "studies using X", never a share of studies.
#
# ORDER IS LOAD-BEARING: first match wins per item, and the final entry matches
# anything, so every specific pattern must precede it.
COMPARATOR_PATTERNS = [
    ("Placebo", r"placebo"),
    # dose is the variable under study — distinct from a single designated
    # low-dose control, and the cheapest available marker of the dose-ranging
    # literature now that dose values themselves are out of scope
    ("Dose-ranging", r"dose[- ]rang|dose[- ]response|other dose levels"),
    # the two halves of a co-administration factorial. Registered as CROSSOVER on
    # CT.gov (allocation structure), which hides the factorial treatment
    # structure — these ticks are what recover it.
    ("Intervention alone", r"intervention component alone"),
    ("Co-administered alone", r"co-?administered component alone"),
    # a designated low/near-inert dose serving as the control. NOT called
    # "active": 1 mg psilocybin is deliberately sub-perceptual.
    ("Low-dose control", r"low[- ]dose"),
    ("Waitlist / care as usual", r"waitlist|care as usual"),
    ("Psychotherapy", r"psychotherapy|hypnosis"),
    ("Active drug", r"."),  # catch-all: any other named drug — must stay last
]


# ---------------------------------------------------------------------------
# Extraction-template column map
#
# Covidence exports each field's LABEL as the column header, and labels get
# reworded between template revisions. Every field is therefore looked up by a
# list of candidate names (newest first), and `_check_template` reports any
# expected column that is missing plus any column in the export we don't read —
# so a rename is caught loudly instead of silently zeroing out a field, which is
# exactly how a `Study type` rename once dropped the whole extraction export.
# ---------------------------------------------------------------------------
TEMPLATE_COLUMNS = {
    "covidence":   ["Covidence #"],
    "reviewer":    ["Reviewer Name"],
    "study_id":    ["Study ID"],
    "title":       ["Title"],
    "doi":         ["DOI"],
    "registry":    ["Trial Registry Number"],
    "reg_not_reported": ["Registration not reported in the paper (found by search)"],
    "pooled":      ["Pooled study?"],
    "parent_doi":  ["Parent study DOI", "Parent Study DOI"],
    "parent_not_cited": ["Parent study not cited in the paper (found by search)"],
    "country":     ["Country / countries where the trial was conducted",
                    "Country/countries where the trial was conducted", "Country"],
    "phase":       ["Trial Phase"],
    "design":      ["Design"],
    "blinding":    ["Blinding"],
    "n_rand":      ["N randomized"],
    "n_anal":      ["N analyzed", "N analyzed (if applicable)"],
    "age_metric":  ["Age metric"],
    "age_value":   ["Age value"],
    "pct_female":  ["%Female", "% Female", "%female"],
    "population":  ["Target Population"],
    "microdosing": ["Microdosing study?"],
    "drugs":       ["Psychedelic/Intervention Drug(s)"],
    "coadmin":     ["Co-administration/Pre-treatment Drug(s)"],
    "comparator":  ["Comparator Drug"],
    "qualitative": ["What is the qualitative outcome?"],
    "notes":       ["Notes"],
}
# Columns retired by the 2026-08 revision. Present in older exports; reading them
# is harmless, but they must not be reported as "unrecognised".
RETIRED_COLUMNS = {"Study type", "Number of conditions/arms", "Derivative?",
                   "Microdosing study?", "Outcomes", "Sex-specific population?"}


def _clean(s: str | None) -> str:
    return (s or "").strip()


def _norm_key(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "").strip().lower())


def _get(row: dict, field: str) -> str:
    """Read a template field by any of its candidate column names."""
    names = TEMPLATE_COLUMNS[field]
    for n in names:
        if n in row:
            v = _clean(row[n])
            if v:
                return v
    norm = {_norm_key(k): v for k, v in row.items()}
    for n in names:
        v = _clean(norm.get(_norm_key(n)))
        if v:
            return v
    return ""


def _check_template(header: list[str]) -> list[str]:
    """Warn about template columns we expect but can't find, and vice versa."""
    out, present = [], {_norm_key(h) for h in header}
    missing = [names[0] for names in TEMPLATE_COLUMNS.values()
               if not any(_norm_key(n) in present for n in names)]
    if missing:
        out.append("extraction export is missing expected column(s): "
                   + ", ".join(repr(m) for m in missing)
                   + " — a template rename silently empties the field it feeds.")
    known = {_norm_key(n) for names in TEMPLATE_COLUMNS.values() for n in names}
    known |= {_norm_key(d) for d in OUTCOME_DOMAINS} | {_norm_key(r) for r in RETIRED_COLUMNS}
    unread = [h for h in header if _norm_key(h) not in known]
    if unread:
        out.append("extraction export has column(s) the build does not read: "
                   + ", ".join(repr(u) for u in unread)
                   + " — add them to TEMPLATE_COLUMNS or OUTCOME_DOMAINS.")
    return out


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


def _split_multi(raw: str) -> list[str]:
    """A template multi-select cell -> the list of values chosen.

    Checked options are ";"-separated. Several free-text values inside a single
    "Other:" entry are "+"-separated, because the Covidence other-box rejects
    semicolons — so "Other: prazosin + oxytocin" is two values, not one.
    """
    out: list[str] = []
    for item in _split_list(raw):
        m = re.match(r"(?i)^other\s*:\s*(.*)$", item)
        if not m:
            out.append(item)
            continue
        for part in m.group(1).split("+"):
            part = part.strip()
            if part:
                out.append("Other: " + part)
    return out


# A blank numeric box means "not extracted yet"; "not reported" is always an
# explicit NR. Keeping them distinct is the whole point — a blank could always be
# an oversight, so it can never carry the meaning "the paper doesn't say".
_NR_RE = re.compile(r"(?i)^\s*(n\.?\s*r\.?|not\s*reported)\s*$")


def _num_or_nr(raw: str, cast=int) -> tuple[object, str]:
    """(value, status) for a numeric box that also accepts NR.

    status: "value" | "not_reported" | "blank" | "unparsed".
    """
    v = _clean(raw)
    if not v:
        return None, "blank"
    if _NR_RE.match(v):
        return None, "not_reported"
    m = re.search(r"-?\d+(?:\.\d+)?", v.replace(",", ""))
    if not m:
        return None, "unparsed"
    try:
        return cast(float(m.group())), "value"
    except (TypeError, ValueError):
        return None, "unparsed"


def _age(metric_raw: str, value_raw: str) -> dict:
    """The Age metric + Age value pair -> a structured age record.

    A *range* fills low/high and leaves `value` None: a range carries no point
    estimate, and inventing a midpoint would fabricate precision the paper never
    reported. Only `mean` (and optionally `median`) contribute a point estimate.
    """
    metric = _clean(metric_raw)
    key = _norm_key(_strip_other(metric))
    v = _clean(value_raw)
    out = {"age_metric": key or "", "age_metric_raw": metric,
           "age": None, "age_low": None, "age_high": None}
    if not v or key in ("not reported", ""):
        return out
    if key == "range":
        m = re.match(r"^\s*(\d+(?:\.\d+)?)\s*(?:[-\u2010-\u2015]|to)\s*(\d+(?:\.\d+)?)\s*$", v)
        if m:
            out["age_low"], out["age_high"] = float(m.group(1)), float(m.group(2))
        return out
    num, status = _num_or_nr(v, cast=float)
    if status == "value":
        out["age"] = num
    return out


def _yes(raw: str) -> bool:
    """A single-checkbox field: ticked (any value) means yes, blank means no."""
    return bool(_clean(raw)) and not _NR_RE.match(_clean(raw))


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
    for item in _split_multi(raw):
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
    items = _split_multi(raw)
    for item in items:
        hit = _derive(INDICATION_PATTERNS, _strip_other(item))
        if hit:
            return hit
    if any("healthy" in i.lower() for i in items):
        return "Healthy volunteers"
    return _strip_other(items[0]) if items else ""


def _is_healthy(raw: str) -> bool:
    """True when the sample is healthy volunteers rather than a patient group."""
    items = _split_multi(raw)
    if not items:
        return False
    if any(_derive(INDICATION_PATTERNS, _strip_other(i)) for i in items):
        return False
    return any("healthy" in i.lower() for i in items)


def _phase(raw_or_enum: str) -> str:
    """Normalize a trial-phase value from either the template or CT.gov.

    ClinicalTrials.gov enums are SCREAMING_SNAKE ('PHASE2', 'NA'); the template
    stores bare digits ('1'), 'Not Applicable', and 'Not Reported'.

    'Unregistered' and 'Pooled' are LEGACY sentinels from the pre-2026-08
    template, where this column doubled as a registration-status field. They are
    not phases and map to "" here; `_check_legacy_phase` warns when an export
    still contains them.
    """
    p = _clean(raw_or_enum).upper()
    if not p or p in ("UNREGISTERED", "POOLED"):
        return ""
    if p in ("NOT REPORTED", "NR", "NOT_REPORTED"):
        return "Not reported"
    if p in ("NA", "N/A", "NOT APPLICABLE"):
        return "N/A"
    m = re.fullmatch(r"(?:EARLY[_ ]?PHASE\s*1|EARLY PHASE 1)", p)
    if m:
        return "Early Phase 1"
    m = re.search(r"(\d)", p)
    return f"Phase {m.group(1)}" if m else p.replace("PHASE", "Phase ").strip()


def _registration_status(registry_norm: str, extracted: bool) -> str:
    """'registered' | 'unregistered' | 'unknown'.

    Derived from the registry cell, not from a phase sentinel: the 2026-08
    template removed 'Unregistered' as a phase value, so an empty registry box on
    an EXTRACTED row is the reviewer's positive statement that no registration
    exists. On an un-extracted row nobody has looked yet, so it stays unknown.
    """
    if registry_norm:
        return "registered"
    return "unregistered" if extracted else "unknown"


def _blinding(raw: str) -> tuple[list[str], list[str]]:
    """(roles, flags) from the Blinding multi-select.

    roles = the named masked parties; flags = not-specified / open-label /
    not reported. Split because a masking LEVEL may only be derived by counting
    named roles — a "participant + not-specified" record states a level was given
    without naming who, and must not be counted as single-blind.
    """
    roles, flags = [], []
    for item in _split_multi(raw):
        k = _norm_key(_strip_other(item))
        if k in BLINDING_ROLES:
            roles.append(k)
        elif k in (_norm_key(f) for f in BLINDING_OTHER):
            flags.append(k)
        elif k:
            flags.append(k)
    return roles, flags


def _masking_level(roles: list[str], flags: list[str]) -> str:
    """Classic label, derived by counting named roles — never assumed."""
    if "open-label" in flags:
        return "Open label"
    if not roles:
        return "" if not flags else "Not specified"
    if "not-specified" in flags:
        return "Stated, roles not named"
    return {1: "Single", 2: "Double", 3: "Triple", 4: "Quadruple"}.get(len(roles), "")


def _comparator_types(raw: str) -> list[str]:
    """Classify each ";"-separated comparator item (a study can be both
    placebo- and active-controlled). Order follows COMPARATOR_PATTERNS."""
    out: list[str] = []
    for item in _split_multi(raw):
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
        vals = _split_multi(ext.get(dom, ""))
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


def _norm_registry_all(registry: str) -> list[str]:
    """Every recognised trial id in the cell, de-duplicated, order preserved.

    A pooled study lists one id per pooled trial (";"-separated). A single trial
    cross-registered on two registries also yields several ids — which is why
    "more than one id" is NOT used to infer pooling; the Pooled checkbox is.
    """
    out: list[str] = []
    for part in _split_list(registry):
        n = _norm_registry(part)
        if n and n not in out:
            out.append(n)
    if not out:                       # whole-cell fallback (unsplit / odd separators)
        n = _norm_registry(registry)
        if n:
            out = [n]
    # NCT first: it is the only id we can enrich, so it is the canonical key
    out.sort(key=lambda k: not k.upper().startswith("NCT"))
    return out


def _norm_doi(raw: str) -> str:
    """Canonical lowercase DOI for matching ('https://doi.org/10.X/Y ' -> '10.x/y')."""
    d = _clean(raw).lower()
    d = re.sub(r"^https?://(dx\.)?doi\.org/", "", d)
    d = re.sub(r"^doi:\s*", "", d)
    return d.strip().rstrip(".")


def _link_trials(studies: list) -> dict:
    """Group papers into trials so the dashboard can show reports of one trial.

    A paper may report SEVERAL trials — a pooled study reports one per pooled
    cohort — so the general field is `trial_keys[]`. `trial_key` stays as the
    single-trial convenience (None when a paper spans several), which is what the
    dashboard's trial navigation and the papers-per-trial figure use.

    Keys come from, in priority order:

    1. **Registry ids** (`registry_ids`) — the canonical case.
    2. **Parent-paper DOI** — for UNREGISTERED trials the template records the
       source paper's DOI, so several reports of one unregistered trial share a
       key of the form ``doi:10.xxxx/yyy``. A paper itself named as a parent
       adopts its own DOI as that key, so the source paper joins the group. If
       the named parent is in the database and *is* registered, the child
       inherits the parent's registry id instead.

    Mutates each study (adds `registry_norm`, `registry_ids`, `parent_doi_norm`,
    `trial_keys`, `trial_key`, `trial_key_source`, `connected_ids`) and returns
    {trial_key: [covidence_id, ...]}.
    """
    from collections import defaultdict

    for s in studies:
        ids = _norm_registry_all(s.get("registry", ""))
        s["registry_ids"] = ids
        s["registry_norm"] = ids[0] if ids else ""
        s["parent_doi_norm"] = [d for d in
                                (_norm_doi(x) for x in _split_list(s.get("parent_study_doi", "")))
                                if d]
        # Several ids mean several TRIALS only for a pooled study. Otherwise it
        # is one trial cross-registered on two registries (e.g. a Dutch study
        # carrying both its ABR and OMON numbers) — grouping those as separate
        # trials would double-count the trial. The Pooled checkbox is the signal,
        # never the id count.
        s["trial_keys"] = list(ids) if (s.get("pooled") and len(ids) > 1) else ids[:1]
        s["trial_key_source"] = "registry" if ids else ""

    by_doi = {_norm_doi(s["doi"]): s for s in studies if s.get("doi")}
    parent_dois = {d for s in studies for d in s["parent_doi_norm"]}

    for s in studies:
        if s["trial_keys"]:
            continue
        for pd in s["parent_doi_norm"]:
            parent = by_doi.get(pd)
            if parent and parent["registry_ids"]:
                s["trial_keys"].extend(k for k in parent["registry_ids"]
                                       if k not in s["trial_keys"])
                s["trial_key_source"] = "parent-registry"
            else:
                key = "doi:" + pd
                if key not in s["trial_keys"]:
                    s["trial_keys"].append(key)
                s["trial_key_source"] = "parent-doi"
        if not s["trial_keys"] and _norm_doi(s.get("doi", "")) in parent_dois:
            s["trial_keys"] = ["doi:" + _norm_doi(s["doi"])]      # this IS the source paper
            s["trial_key_source"] = "source-paper"

    for s in studies:
        s["trial_key"] = s["trial_keys"][0] if len(s["trial_keys"]) == 1 else None

    by_key: dict = defaultdict(list)
    for s in studies:
        for k in s["trial_keys"]:
            by_key[k].append(s["covidence_id"])

    # connected = shares AT LEAST ONE trial with this paper (symmetric by
    # construction, and correct for pooled papers that span several trials)
    for s in studies:
        seen: list = []
        for k in s["trial_keys"]:
            for cid in by_key.get(k, []):
                if cid != s["covidence_id"] and cid not in seen:
                    seen.append(cid)
        s["connected_ids"] = seen

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
    # roles in the template's own vocabulary, so registry-sourced and extracted
    # blinding land in the same facet ("CARE_PROVIDER" -> "care provider")
    masked_roles = [r for r in (_enum(w).lower() for w in who) if r in BLINDING_ROLES]
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
        "masking_level": _enum(mi.get("masking")),
        "masked_roles": masked_roles,
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
        # every trial the paper reports — a pooled study appears under each of
        # its constituent trials rather than collapsing them into one
        for k in (s.get("trial_keys") or ([s["trial_key"]] if s.get("trial_key") else [])):
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
    legacy_phase = 0
    legacy_export = False
    if ext_path:
        with open(ext_path, newline="", encoding="utf-8-sig") as fh:
            reader = csv.DictReader(fh)
            warnings.extend(_check_template(reader.fieldnames or []))
            # An export predating the 2026-08 revision has none of the
            # conditional-block columns; its rows cannot violate rules the
            # template did not yet have, so those QC checks are skipped.
            present = {_norm_key(h) for h in (reader.fieldnames or [])}
            legacy_export = not any(_norm_key(n) in present
                                    for n in ("Design", "Blinding", "Pooled study?"))
            for row in reader:
                cid = _norm_covidence(_get(row, "covidence"))
                if cid is None:
                    continue
                who = _get(row, "reviewer")
                n_extraction_rows += 1
                reviewers[who] = reviewers.get(who, 0) + 1
                rows_by_study.setdefault(cid, set()).add(who)
                if _clean(_get(row, "phase")).upper() in ("UNREGISTERED", "POOLED"):
                    legacy_phase += 1
                worked = any(_get(row, f) for f in
                             ("n_rand", "drugs", "population", "comparator"))
                if worked and not any(_clean(row.get(d)) for d in OUTCOME_DOMAINS):
                    missing_outcomes[who] = missing_outcomes.get(who, 0) + 1
                if CONSENSUS_REVIEWER and who != CONSENSUS_REVIEWER:
                    continue
                extraction[cid] = row
    if legacy_phase:
        warnings.append(
            f"{legacy_phase} extraction row(s) still use the pre-2026-08 Trial Phase "
            f"sentinels ('Unregistered'/'Pooled'). Those are not phases — registration "
            f"status now derives from the Trial Registry Number cell, and pooling from "
            f"the Pooled checkbox. Re-export after the template update."
        )
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
            drug_ext = _get(ext, "drugs")
            if drug_ext:
                drugs = _norm_drugs(drug_ext)
                drug_source = "extracted"
            else:
                drugs = _derive_all(DRUG_PATTERNS, row.get("Title", ""), row.get("Abstract", ""))
                drug_source = "auto" if drugs else "unknown"
            drug = drugs[0] if drugs else "Unclear"

            # Indication: extracted target population wins; else derive.
            pop_ext = _get(ext, "population")
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
            sid = _clean(row.get("Study"))
            registry_ids = _norm_registry_all(registry)
            registry_norm = registry_ids[0] if registry_ids else ""
            has_nct = any(k.startswith("NCT") for k in registry_ids)
            pooled = _yes(_get(ext, "pooled")) if is_ext else False
            reg_status = _registration_status(registry_norm, is_ext)

            # Registration/parent DISCLOSURE — a reporting-integrity axis distinct
            # from prospective-vs-retrospective. The checkbox is ticked only when
            # the id was found by search and NOT reported in the paper (a CONSORT
            # item 23 / ICMJE violation). Tri-state: True = present AND reported,
            # False = present but not reported, None = nothing to disclose.
            has_parent = bool(_get(ext, "parent_doi"))
            reg_not_reported = _yes(_get(ext, "reg_not_reported")) if is_ext else False
            parent_not_cited = _yes(_get(ext, "parent_not_cited")) if is_ext else False
            registration_disclosed = (not reg_not_reported) if registry_ids else None
            parent_disclosed = (not parent_not_cited) if has_parent else None

            phase_raw = _get(ext, "phase")
            phase = _phase(phase_raw)
            design_raw = _get(ext, "design")
            design_txt = _norm_key(_strip_other(design_raw))
            # an "Other:" design is free text — keep it, but facet it as "other"
            # so arbitrary strings never become facet values
            design = design_txt if design_txt in DESIGN_VALUES else (
                "other" if design_txt else "")
            blind_roles, blind_flags = _blinding(_get(ext, "blinding"))
            countries = [_strip_other(c) for c in _split_multi(_get(ext, "country"))]
            src_tag = "extracted"

            outcome_domains, outcome_measures = _outcomes(ext) if is_ext else ([], [])
            n_rand, n_rand_status = _num_or_nr(_get(ext, "n_rand"))
            n_anal, n_anal_status = _num_or_nr(_get(ext, "n_anal"))
            pct_female, pct_female_status = _num_or_nr(_get(ext, "pct_female"), cast=float)
            age = _age(_get(ext, "age_metric"), _get(ext, "age_value"))

            # ---- QC on the conditional block ----
            # It is filled ONLY when the study has no NCT and is not pooled; a
            # value where one shouldn't be means the reviewer filled a section
            # they should have skipped, and a registry value will silently
            # override it below.
            if is_ext and not legacy_export and has_nct and (
                    phase or design or blind_roles or blind_flags):
                warnings.append(
                    f"#{cid} {sid}: has an NCT ({registry_norm}) but the no-NCT block "
                    f"(phase/design/blinding) was filled — registry values take precedence."
                )
            # The block is gated on "no NCT", NOT "unregistered": a study on
            # ANZCTR/ISRCTN/Dutch is registered but is NOT auto-enriched, so it
            # still needs these by hand. This is the likeliest misreading.
            if is_ext and not legacy_export and registry_ids and not has_nct and not pooled \
                    and not (phase or design or blind_roles or blind_flags):
                warnings.append(
                    f"#{cid} {sid}: registered on a non-NCT registry ({registry_norm}) so "
                    f"nothing is auto-enriched, but phase/design/blinding are all empty — "
                    f"the no-NCT block applies here and appears to have been skipped."
                )
            if is_ext and reg_not_reported and not registry_ids:
                warnings.append(f"#{cid} {sid}: 'registration not reported (found by search)' is "
                                f"ticked but the Trial Registry Number is empty — enter the id you "
                                f"found, or untick the box.")
            if is_ext and parent_not_cited and not has_parent:
                warnings.append(f"#{cid} {sid}: 'parent study not cited (found by search)' is ticked "
                                f"but Parent study DOI is empty.")
            if is_ext and n_rand is not None and n_anal is not None and n_anal > n_rand:
                warnings.append(f"#{cid} {sid}: N analyzed ({n_anal}) > N randomized ({n_rand}).")
            if is_ext and pct_female is not None and not (0 <= pct_female <= 100):
                warnings.append(f"#{cid} {sid}: %Female is {pct_female}, outside 0-100.")
            for label, status in (("N randomized", n_rand_status), ("N analyzed", n_anal_status),
                                  ("%Female", pct_female_status)):
                if is_ext and status == "unparsed":
                    warnings.append(f"#{cid} {sid}: {label} value could not be read as a "
                                    f"number or NR.")

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
                    "reviewer": _get(ext, "reviewer"),
                    "parent_study_doi": _get(ext, "parent_doi"),
                    "pooled": pooled,
                    "has_nct": has_nct,
                    "registration_status": reg_status,
                    # reporting-integrity: registered? · disclosed? · prospective?
                    # disclosed/parent_disclosed are True/False/None (None = N/A)
                    "registration_disclosed": registration_disclosed,
                    "parent_disclosed": parent_disclosed,
                    # phase / design / blinding / country: extracted here, then
                    # overwritten from the registry for NCT studies (see below)
                    "phase": phase,
                    "phase_raw": phase_raw,
                    "phase_source": src_tag if phase else "",
                    "design": design,
                    "design_other": design_txt if design == "other" else "",
                    "design_source": src_tag if design else "",
                    "blinding_roles": blind_roles,
                    "blinding_flags": blind_flags,
                    "masking_level": _masking_level(blind_roles, blind_flags),
                    "blinding_source": src_tag if (blind_roles or blind_flags) else "",
                    "countries": countries,
                    "countries_source": src_tag if countries else "",
                    # sample size — a blank is "not extracted", NR is "the paper
                    # does not say"; only two integers make attrition computable
                    "n_randomized": n_rand,
                    "n_randomized_status": n_rand_status,
                    "n_analyzed": n_anal,
                    "n_analyzed_status": n_anal_status,
                    "n": n_rand if n_rand is not None else n_anal,
                    "n_source": ("randomized" if n_rand is not None
                                 else "analyzed" if n_anal is not None else ""),
                    "attrition": (n_rand - n_anal
                                  if n_rand is not None and n_anal is not None else None),
                    "attrition_determinable": n_rand is not None and n_anal is not None,
                    # demographics
                    "age": age["age"],
                    "age_metric": age["age_metric"],
                    "age_low": age["age_low"],
                    "age_high": age["age_high"],
                    "pct_female": pct_female,
                    "pct_female_status": pct_female_status,
                    # single-sex is now DERIVED from %female rather than asked
                    "sex_specific": ("female" if pct_female == 100 else
                                     "male" if pct_female == 0 else ""),
                    "microdosing": _yes(_get(ext, "microdosing")) if is_ext else False,
                    "drugs_raw": drug_ext,
                    "coadmin": _get(ext, "coadmin"),
                    "comparator": _get(ext, "comparator"),
                    "comparator_types": _comparator_types(_get(ext, "comparator")),
                    "population": pop_ext,
                    "outcome_domains": outcome_domains,
                    "outcome_measures": outcome_measures,
                    "qualitative_outcome": _get(ext, "qualitative"),
                    "extraction_notes": _get(ext, "notes"),
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

    # ---- fill phase / design / blinding / country from the registry ----
    # For an NCT study the template deliberately skips those questions, so the
    # registry is the source. Registry values WIN where both exist (the reviewer
    # was meant to skip), and are labelled so no figure mistakes a planned
    # protocol value for something read off the paper.
    details_by_key = {t["trial_key"]: t.get("details") for t in trials if t.get("details")}
    for s in studies:
        ds = [details_by_key[k] for k in s["trial_keys"] if details_by_key.get(k)]
        if not ds:
            continue
        if len(ds) > 1:
            # pooled across several registered trials: adopt a registry value
            # only where every cohort agrees, mirroring the template's own rule
            def agreed(key, conv=lambda v: v):
                vals = {json.dumps(conv(x.get(key)), sort_keys=True, default=str) for x in ds}
                return conv(ds[0].get(key)) if len(vals) == 1 else None
            d = {k: agreed(k) for k in ("phase", "model", "masking_level",
                                        "masked_roles", "countries")}
        else:
            d = ds[0]
        if not d:
            continue
        if d.get("phase"):
            s["phase"], s["phase_source"] = _phase(d["phase"].split(",")[0]), "registry"
        model = DESIGN_FROM_REGISTRY.get(d.get("model") or "")
        if model:
            s["design"], s["design_source"] = model, "registry"
        if d.get("masked_roles") or d.get("masking_level"):
            s["blinding_roles"] = list(d.get("masked_roles") or [])
            s["blinding_flags"] = [] if d.get("masked_roles") else ["not-specified"]
            s["masking_level"] = d.get("masking_level") or _masking_level(
                s["blinding_roles"], s["blinding_flags"])
            s["blinding_source"] = "registry"
        if d.get("countries"):
            s["countries"], s["countries_source"] = list(d["countries"]), "registry"

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
            "designs": [d for d in DESIGN_VALUES + ["other"]
                        if any(s["design"] == d for s in studies)],
            "blinding_roles": [r for r in BLINDING_ROLES
                               if any(r in s["blinding_roles"] for s in studies)],
            "masking_levels": sorted({s["masking_level"] for s in studies if s["masking_level"]}),
            "countries": sorted({c for s in studies for c in s["countries"]}),
            "comparator_types": [c for c, _ in COMPARATOR_PATTERNS
                                 if any(c in s["comparator_types"] for s in studies)],
            "registries": sorted({s["registry_norm"] for s in studies if s["registry_norm"]}),
            "n_trials": n_trials,
            "n_registered_trials": sum(1 for t in trials if not t["trial_key"].startswith("doi:")),
            "n_unregistered_trials": sum(1 for t in trials if t["trial_key"].startswith("doi:")),
            "n_trials_enriched": sum(1 for t in trials if t["fetch_status"] == "ok"),
            "n_multi_paper_trials": sum(1 for ids in by_key.values() if len(ids) > 1),
            "n_pooled": sum(1 for s in studies if s.get("pooled")),
            "n_microdosing": sum(1 for s in studies if s.get("microdosing")),
            # how much of the corpus each source actually covers
            "field_sources": {
                f: dict(sorted(
                    __import__("collections").Counter(
                        s[f + "_source"] for s in studies if s.get(f + "_source")).items()))
                for f in ("phase", "design", "blinding", "countries")
            },
            "attrition_determinable": sum(1 for s in studies
                                          if s.get("attrition_determinable")),
            # registration-disclosure integrity (a lower bound — only trials whose
            # registration/parent was actually found can be judged non-disclosed)
            "disclosure": {
                "registration_disclosed":
                    sum(1 for s in studies if s.get("registration_disclosed") is True),
                "registration_not_disclosed":
                    sum(1 for s in studies if s.get("registration_disclosed") is False),
                "parent_disclosed":
                    sum(1 for s in studies if s.get("parent_disclosed") is True),
                "parent_not_disclosed":
                    sum(1 for s in studies if s.get("parent_disclosed") is False),
            },
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
    fs = m["field_sources"]
    print("  sources  : " + " | ".join(
        f"{f} {'+'.join(f'{k[:3]}:{v}' for k, v in fs[f].items()) or '—'}"
        for f in ("phase", "design", "blinding", "countries")))
    n_ext = m["n_extracted"]
    print(f"  attrition: determinable for {m['attrition_determinable']}/{n_ext} extracted"
          f" · pooled {m['n_pooled']} · microdosing {m['n_microdosing']}")
    d = m["disclosure"]
    reg_known = d["registration_disclosed"] + d["registration_not_disclosed"]
    print(f"  disclose : registration undisclosed {d['registration_not_disclosed']}/{reg_known} "
          f"found · parent uncited {d['parent_not_disclosed']}/"
          f"{d['parent_disclosed'] + d['parent_not_disclosed']} found")
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
