# Master DB — Psychedelic RCT Database (pilot)

A project to screen and extract metadata on **all RCTs that administer a psychedelic
drug** (any drug, any condition, including healthy-volunteer studies). The deliverable
is two things from one pipeline:

1. A **published, exportable database** others can use to seed their own systematic reviews.
2. An **interactive dashboard** on sypres.io where users search, filter, inspect metadata,
   and export filtered results as CSV or RIS.

This is distinct from the SYPRES *living reviews* (PSILODEP, MDMAPTSD), which are focused
meta-analyses. The master DB is a broad, structured catalogue of the evidence base.

> **Status:** Pilot. 19 studies included; 4 fully extracted against the pilot template.
> The extraction template is still being refined — see "Recommended metadata additions".

## Site layout note — sidebar-less page centering (resolved)

Minimal Mistakes reserves a left gutter on `.page`/`.archive` (`float: right;
width: calc(100% - 250px)`) for a sidebar that our `_includes/sidebar.html` only emits on
dataset pages. On pages without it, content was shifted off-center. The fix lives in
`assets/css/custom.css` (verified across Home/News/Team/Methods/Overview/Publications/database
+ a sidebar page at ≥1024px):

- **Drop the float** on sidebar-less `.page`/`.archive` so the column isn't pushed into the
  empty gutter; also **reclaim the right TOC padding** — except where a TOC actually renders
  (`single` + `toc`, e.g. Methods, keeps `.sidebar__right` room via `:not(:has(.sidebar__right))`).
  Without reclaiming the padding, centered/fixed-width content centers inside a left-offset box.
- **Home & News** (`body.layout--home` / `body.layout--blog`) are constrained to a centered
  `max-width: 40rem` column (note: root font is **22px** at large breakpoints, so `40rem ≈ 880px`;
  don't reason about `rem` here as 16px).
- **Team's** fixed `width: 1000px` tables get `margin: 0 auto` (centering the column alone won't
  center a fixed-width child) — set inline in `docs/team/index.html`.
- Pages **with** a sidebar (PSILODEP, MDMAPTSD) are untouched (`#main:has(.sidebar)` short-circuits).

## Data flow

```
Covidence exports (analysis/master-db/data/*.csv)
        │   included export    → bibliographic record for every INCLUDED study
        │   extraction export   → data-extraction template fields (subset of studies)
        │   screen/select/      → per-stage record counts → PRISMA study-flow
        │   included/excluded
        ▼
analysis/master-db/build_database.py   (stdlib only — no deps)
        │   build(): merge on Covidence #, normalize, auto-derive facets,
        │            compute PRISMA funnel + outcome list
        ▼
_data/master_db.json                   ({meta, prisma, studies}; committed)
        ▼
docs/datasets/master-db/index.html     (dashboard; embeds the JSON via {{ site.data }};
        │                                PRISMA box rendered server-side via Liquid)
        ▼
/docs/datasets/master-db/              (live page, linked from Studies nav)
```

## Files

| Path | Role |
|------|------|
| `data/*.csv` | Raw Covidence exports. Drop new ones here. Filenames are timestamped by Covidence. |
| `build_database.py` | `build()` returns the dict; `main()` writes `_data/master_db.json`. Re-run after every new export. |
| `tests/test_build_database.py` | Stdlib `unittest` suite for the build pipeline. See [Tests](#tests). |
| `.registry_cache/` | Gitignored cache of fetched ClinicalTrials.gov responses (parsed details are committed in `_data/master_db.json`). |
| `CLAUDE.md` | This file. |
| `../../_data/master_db.json` | Generated data consumed by the site. **Do not hand-edit** — regenerate. |
| `../../docs/datasets/master-db/index.html` | The dashboard page (HTML + scoped CSS + vanilla JS). |
| `../../_data/navigation.yml` | Studies submenu — contains the dashboard link. |

## How to update the database

1. Export the relevant stages from Covidence (see [stage exports](#covidence-stage-exports--prisma)).
   At minimum the **included** and **extraction** CSVs; include **screen/select/excluded** to keep
   the PRISMA flow current.
2. Drop them into `analysis/master-db/data/` (old exports can stay — newest of each is used).
3. Rebuild + test:
   ```bash
   python3 analysis/master-db/build_database.py      # fetches NCT registry details (network)
   #   --no-fetch  cache-only / offline      --refresh  re-fetch, ignore the 30-day cache TTL
   python3 -m unittest discover -s analysis/master-db/tests
   ```
   The fetch only touches new/stale NCT ids and is resilient (see
   [enrichment failure modes](#failure-modes-the-build-never-crashes-on-a-registry-problem)).
4. Rebuild/serve the site. Locale must be UTF-8 (a vendored Sass file is UTF-8):
   ```bash
   LANG=en_US.UTF-8 LC_ALL=en_US.UTF-8 bundle exec jekyll serve --no-watch
   ```
   Then open `/docs/datasets/master-db/`.

The build auto-detects the included export (header has `Abstract` + `included` in the filename)
and the extraction export (header has `Reviewer Name`), picking the most recent of each.

## Covidence stage exports & PRISMA

Covidence exports are **snapshots of each study's current stage** and are *mutually exclusive*
(a study appears in exactly one — verified: the four bibliographic exports share zero Covidence
IDs). Map of filename keyword → stage:

| Filename contains | Stage | Current n |
|---|---|---|
| `screen`   | In title/abstract screening (not yet adjudicated) | 4,426 |
| `select`   | Passed title/abstract; in full-text review | 116 |
| `included` | Passed full-text review (→ the database) | 19 |
| `excluded` | Excluded at full-text (reason in `Notes`) | 2 |
| *(none of the above, has `Reviewer Name`)* | Extraction template | 4 |

`build_prisma()` derives the funnel with set algebra (robust even if a future export overlaps):
records in review = ∪ of all stages; advanced-to-full-text = select ∪ included ∪ excluded;
still-in-screening = the remainder. Full-text **exclusion reasons** are tallied from the excluded
export's `Notes` (`"Exclusion reason: <reason>;"`).

### ⚠ What the stage exports do NOT contain (`prisma_manual.json`)

The stage exports **omit the top of the PRISMA funnel**: *records identified per database*,
*duplicates removed*, and **records excluded at title/abstract screening**. (The `screen` export
is only studies *still in* screening, not those already rejected.) So "records in the review"
(`records_in_review`) is **not** the total screened — it starts mid-funnel.

These three numbers live on the Covidence dashboard and must be entered by hand in
[`prisma_manual.json`](prisma_manual.json):

```json
{ "records_identified": null, "duplicates_removed": null, "excluded_title_abstract": null }
```

`build_prisma()` reads them into `prisma.manual` (with derived `records_screened` and a
`complete` flag) and re-run the build. While any are null, the dashboard PRISMA box shows an
amber **"upstream counts not yet entered"** reminder; once all three are filled it renders the
full Identification → Screening → Eligibility → Included flow. **Remember to update these from
Covidence before publishing** — until then the funnel undercounts total screening.

## Join key & sources

- Studies are joined on the **Covidence #** (`#28318` in the bibliographic export, `28318`
  in the extraction export — the script strips the `#`).
- Bibliographic fields come from the *included* export. `Ref` column = **PMID**.
- Extraction fields come from the *extraction* export. Studies present in *included* but not
  in *extraction* are kept and flagged `extracted: false`.

### Fields that appear in both exports (de-duplication)

The extraction export re-lists `Title`, `Study ID`, `DOI`, and `Trial Registry Number`, which
also exist in the bibliographic export. They split into two groups:

- **Pure duplicates — sourced from bibliographic, ignore the extraction copy:** `Title` and
  `Study ID` (= bibliographic `Study`) are always populated by the Covidence import (0/19
  blank), so the extraction copies add nothing. Safe to drop from the data-entry template.
- **Fill-if-missing — coalesced (bibliographic first, then extraction):** `DOI` and the
  registry are *not* always present on import (2/19 included studies have no DOI; the
  bibliographic `Accession Number` is blank for ~3/4 registered trials). So a reviewer can
  add the missing value at extraction and the build coalesces it in
  (`doi = included.DOI or extraction.DOI`; registry = `Trial Registry Number or Accession`).
  **Keep these in the template** — treat them as "verify / fill if the import lacks one."

## Data dictionary (`_data/master_db.json` → `studies[]`)

Bibliographic (all studies):
`covidence_id, study_id, title, authors[], authors_str, abstract, year, month, journal,
volume, issue, pages, page_start, page_end, pmid, doi, url, registry, registry_url, tags[]`

Derived facets (all studies — used for filtering):
- `drug` + `drug_source` (`extracted` | `auto` | `unknown`)
- `indication` + `indication_source` (`extracted` | `auto` | `unknown`)

> `auto` values are keyword-derived from title/abstract for studies not yet extracted, and
> are surfaced in the UI with an "auto" marker. Extracted values always win. The keyword
> vocabularies live at the top of `build_database.py` (`DRUG_PATTERNS`, `INDICATION_PATTERNS`).

Extraction template (only populated when `extracted: true`):
`reviewer, study_type, parent_study_doi, n_arms, n_arms_raw, drugs_raw, derivative,
microdosing, comparator, population, outcomes[], qualitative_outcome, extraction_notes`

Trial linkage (all studies):
- `registry_norm` — canonical trial id (NCT preferred; other registries recognized;
  non-registry accessions like `WOS:…` normalize to `""`). See `_norm_registry()`.
- `trial_key` — the grouping key: `registry_norm`, or (for a registry-less secondary
  analysis) the parent study's `trial_key` resolved via `parent_study_doi`; else `null`.
- `connected_ids[]` — Covidence #s of **other papers in the DB sharing this trial**.

`trials[]` (one per **registered** trial; powers the Trials tab):
`trial_key, registry, registry_url, source, fetched, fetch_status, details{…}|null, paper_ids[]`.
`details` (when `fetch_status == "ok"`): `title, status, study_type, phase, allocation, model,
masking, enrollment, enrollment_type, conditions[], arms[], sponsor, industry, start,
completion, countries[], primary_outcomes[], results_posted`. See
[enrichment](#trial-registry-enrichment--trial-cards) for `fetch_status` values.

`meta` block: `generated, review_id, n_included, n_extracted, drugs[], indications[],
outcomes[], registries[], n_trials, n_registered_trials, n_trials_enriched,
n_multi_paper_trials, year_min, year_max, source_included, source_extraction`.
`meta.outcomes[]` populates the **Outcome** facet. (`registries[]` is retained for tests /
future use — the trial-registry *filter* was removed.)

`prisma` block: `records_in_review, in_screening, advanced_to_fulltext, fulltext_in_review,
fulltext_excluded, fulltext_excluded_reasons{reason: count}, included, extracted, source_files,
manual{records_identified, duplicates_removed, excluded_title_abstract, records_screened, complete}`
(see the [screening-exclusion caveat](#-what-the-stage-exports-do-not-contain-prisma_manualjson)).

## Dashboard behavior

- Full-text search (title/authors/abstract/journal/year) + facet filters (drug, condition,
  **outcome domain**, microdosing, extraction status, year range) + sortable columns. Click a
  row to expand the full record (abstract + all extraction fields + DOI/PMID/registry links).
  The **Outcome** facet matches studies whose `outcomes[]` contains the selected domain, so it
  only surfaces extracted studies (pending records have no outcomes yet).
- A collapsible **PRISMA study-flow** box (top of page) is rendered server-side from the
  `prisma` block via Liquid, so it needs no JS and stays in sync with the data.
- **Papers / Trials tabs.** A tab bar switches between the **Papers** view (default — the
  search/table; trials never appear here) and the **Trials** view (a supplement). Trials are
  registered trials only (registered papers grouped by `registry_norm`, + `parent_study_doi`
  for registry-less secondary analyses); unregistered papers are paper-only.
- **Trial cards** (Trials tab) show the registry details auto-pulled from ClinicalTrials.gov
  (see [enrichment](#trial-registry-enrichment--trial-cards)) plus *Papers in this database
  from this trial*. **Cross-navigation:** a paper card's *"View trial details →"* opens the
  trial card; a trial card's paper chips open the paper (flipping tabs as needed). Each paper
  card also still shows a *Connected papers* line for siblings sharing its trial.
  (A trial-registry *filter* was prototyped and removed — not useful.)
- **Export buttons export exactly the filtered rows.** CSV = full field set; RIS = importable
  into Zotero/EndNote/Mendeley/Covidence/Rayyan.
- Pure client-side; data is embedded at build time (no fetch / no CORS issues). Fine for
  hundreds of rows. If the included set grows into the thousands, add pagination/virtualized
  rendering and consider fetching the JSON from `assets/` instead of embedding.
- **Feedback links** open a pre-filled GitHub issue via URL params
  (`issues/new?title=…&body=…&labels=…`), so they work without merged templates. The repo
  comes from `{{ site.repository }}` (rendered onto `#mdb-data[data-repo]`, read by `issueUrl()`):
  - *"Report a missing study"* (top of page, Liquid-built) → label `missing-study`.
  - *"Report inaccurate or incomplete data"* (per study, in the expanded card) → label
    `data-correction`, body pre-filled with that study's id / Covidence # / DOI / record URL.
  - Optional: create the `missing-study` and `data-correction` labels in the repo (unknown
    labels are silently dropped, so the links still work without them).

## Trial-registry enrichment & trial cards

`build_trials()` groups registered papers into trials and, for **ClinicalTrials.gov (NCT)** ids,
fetches structured details from the free API v2 (`https://clinicaltrials.gov/api/v2/studies/<NCT>`),
parses them with `_parse_ctgov()`, and
stores them in `trials[].details`. Stdlib only (`urllib`); responses are cached under
`analysis/master-db/.registry_cache/<NCT>.json` (gitignored). The **parsed details are committed
inside `_data/master_db.json`**, so the *site* build never needs the network — only
`build_database.py` does, and only for NCTs missing/stale in the cache.

Run flags (see [How to update](#how-to-update-the-database)):
- default `python3 build_database.py` → fetches missing/stale (TTL 30 days) NCTs.
- `--no-fetch` → cache-only (offline / CI); uncached NCTs get `fetch_status: not_fetched`.
- `--refresh` → ignore TTL and re-fetch everything.

### Failure modes (the build never crashes on a registry problem)

| `fetch_status` | When | Card shows |
|---|---|---|
| `ok` | fetched or cached + parsed | full registry details |
| `unsupported_registry` | **not an NCT** — e.g. Cavarra's Dutch `NL70508.068.1`, ISRCTN, EudraCT | registry id only + "automated details aren't available for this registry" |
| `not_found` | API 404 (withdrawn / embargoed / **mistyped NCT** — doubles as QC) | registry link + "could not be found" note |
| `error` | network down / rate-limited / parse failure → **falls back to stale cache** if present | last good details, or the error note |
| `not_fetched` | `--no-fetch` and nothing cached | "details haven't been fetched yet" note |

**Gotchas / how to handle:**
- **Non-NCT registries** (the big one): the CT.gov API can't resolve them. The Dutch CCMO/OMON
  has no clean public API → stays manual. Others have their own APIs (ISRCTN, EU-CTIS, ANZCTR)
  — add a per-registry adapter in `_registry_raw`/`build_trials` keyed off the id prefix if/when
  needed. Until then they render gracefully as `unsupported_registry`.
- **Registry ≠ paper.** Details are the *planned protocol* (e.g. *planned* vs *actual*
  enrollment, status, results-posted) and can differ from the published paper — the card labels
  them "from ClinicalTrials.gov." Do **not** overwrite extracted fields with registry values.
- **Staleness.** Each cache entry has a `fetched` date; details drift over time (status, results
  posted). Re-run with `--refresh` periodically, or delete `.registry_cache/`.
- **API versioning.** v1 is retired; this pins v2 and isolates field paths in `_parse_ctgov()`
  (defensive `.get()` throughout) so a schema change is a one-function fix and partial data
  still renders.
- **Offline/CI builds.** Use `--no-fetch`; the committed JSON already carries the details, so
  the published site is unaffected.

## Tests

Stdlib `unittest`, no dependencies. From the repo root:

```bash
python3 -m unittest discover -s analysis/master-db/tests        # or: -v
python3 analysis/master-db/tests/test_build_database.py
```

Covers (a) the pure helpers — Covidence-# / page / int parsing, yes-no, drug & indication
derivation, registry & study URLs, CSV classification, stage-file disambiguation; and
(b) `build()` against the real exports — split into **invariants** (PRISMA reconciliation,
required keys, DOI/URL coalescing, sort order, `meta.outcomes` superset) and **current-fixture
counts** (`n_included`, PRISMA numbers). When you add exports and the counts legitimately
change, update `test_current_counts` — the invariant tests should keep passing untouched.

## Repository layout & publishing (single source of truth)

- The **only** tracked copy of the raw exports is `analysis/master-db/data/`. Keep them there.
- `_site/` is Jekyll's **generated build output** — it is in `.gitignore` and rebuilt on every
  `jekyll build`. Files you may see under `_site/analysis/...` are throwaway copies, not a second
  version to maintain.
- `analysis/master-db/` is **excluded from the Jekyll build** (`_config.yml` → `exclude:`), so the
  raw CSVs, build script, tests, and this file are **not published** to the live site. The data
  still reaches the site through the committed `_data/master_db.json`. (The `psilodep`/`mdmaptsd`
  analysis folders are *not* excluded because their dataset pages embed figures from them.)
- If you ever want to publish a clean database file for download, generate a curated CSV into
  `assets/` deliberately rather than exposing the raw Covidence exports.

## RIS export — feasible today

RIS is generated entirely from the bibliographic fields, no extra data required:
`TY, AU (one per author), TI, PY, JO/JF, VL, IS, SP, EP, DO, AB, AN(PMID), UR, KW(drug,
condition), C1(registry), ER`. Pages like `2152-2162` are split into SP/EP; article numbers
become SP only. Caveats (not blockers):
- Author names arrive as `Lastname II` (initials, no comma). Export reformats to
  `Lastname, II`, which all major managers parse. Full given names would make citations
  cleaner but are optional.
- A few records lack a DOI and/or pages (e.g. the conference abstract Yazar-Klosinski 2021).
  RIS is still valid, just sparser.

## Recommended metadata additions (template still in pilot)

The current extraction template captures study identity, drug, arms, comparator, population,
and outcome *domains*. For the database to be genuinely useful for downstream systematic
reviews / meta-analyses, the highest-value additions are:

**Tier 1 — essential (currently absent):**
1. **Sample size** — N randomized (total), N analyzed, and **N per arm**. Nothing downstream
   (meta-analysis, weighting) works without this.
2. **Dose** — dose per arm (mg / µg / mg/kg), **number of dosing sessions**, and
   cumulative/total dose. Central for psychedelics; `Microdosing? yes/no` is too coarse.
3. **Blinding** — open-label vs single/double/triple-blind, and who was blinded. Key
   risk-of-bias driver and a known psychedelic issue (functional unblinding).
4. **Design** — parallel-group vs **crossover** vs within-subject. Many of these pharmacology
   trials are crossover; `Number of arms` doesn't capture it and it changes the analysis.
5. **Psychotherapy / psychological support** — present/absent, model, total hours, # therapists.
   Distinguishes "drug" from "drug-assisted therapy" — a defining design axis.

**Tier 2 — important for filtering/synthesis:**
6. Structured **condition/indication** (even for healthy-volunteer studies, the study domain).
7. **Route of administration** (oral, IV, sublingual…).
8. **Primary outcome instrument(s)** (CAPS-5, MADRS, QIDS, YBOCS…) + **primary endpoint timepoint**.
9. **Age** (mean/SD or range) and **sex** distribution.
10. **Country/region** and **setting** (single- vs multi-center, # sites).
11. **Funding/sponsor** + **industry vs non-industry** flag (RoB / COI).
12. **Risk-of-bias** judgment (Cochrane RoB 2 domains + overall) — already planned for SYPRES.

**Tier 3 — psychedelics-specific / nice to have:**
13. Participants' **prior psychedelic experience** (expectancy).
14. **Follow-up duration** / longest timepoint; open-label extension present?
15. **Publication status** (peer-reviewed / preprint / conference abstract).
16. Link to extractable **effect-size data** (parallels the existing `*-effect-sizes` datasets).

**Data-quality / structural:**
- `Number of conditions/arms` contains `Other: 10`, `Other: 2` — make it a plain integer.
- `Outcomes` packs domains + `Other: X` into one cell — consider a controlled multi-select
  plus a free-text "other" so faceting stays clean.
- Some records lack a DOI (conference abstracts, older trials); keep PMID/registry as backup
  stable identifiers.
