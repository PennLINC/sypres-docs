# Master DB — Psychedelic RCT Database (pilot)

A project to screen and extract metadata on **all RCTs that administer a psychedelic
drug** (any drug, any condition, including healthy-volunteer studies). The deliverable
is two things from one pipeline:

1. A **published, exportable database** others can use to seed their own systematic reviews.
2. An **interactive dashboard** on sypres.io where users search, filter, inspect metadata,
   and export filtered results as CSV or RIS.

This is distinct from the SYPRES *living reviews* (PSILODEP, MDMAPTSD), which are focused
meta-analyses. The master DB is a broad, structured catalogue of the evidence base.

> **Status:** Pilot. 95 papers included; 45 have at least one reviewer extraction, of which
> **16 carry a consensus-equivalent row** (see [Consensus rows](#consensus-rows--one-row-per-reviewer)).
> The extraction template was revised on 2026-08-27 — see
> [Template revisions](#template-revisions--what-changed-and-what-broke).
> It is still being refined; see [Extraction-template gaps](#extraction-template-gaps-post-review-2026-08-26).

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
        │   extraction export   → data-extraction template fields, ONE ROW PER
        │                         REVIEWER PER STUDY (filtered to consensus rows)
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

## Consensus rows — one row per reviewer

Covidence emits the extraction export with **one row per reviewer per study**, so a
dual-extracted study appears two or more times. Consensus adjudication has not been run
yet, so `build_database.py` filters to a single reviewer's rows as a stand-in:

```python
CONSENSUS_REVIEWER = "Parker Singleton"   # set to None once real consensus rows exist
```

Non-consensus rows are **counted, not discarded** — `meta.extraction_coverage` reports
`{rows, studies_with_any_extraction, studies_with_consensus_row, studies_dual_extracted,
reviewers{}}` so the dashboard can show dual-extraction progress. Setting
`CONSENSUS_REVIEWER = None` uses every row (last row per study wins) — that is the switch
to flip when Covidence consensus rows become available.

> **Extraction is in progress — incomplete rows are normal, not errors.** Only the consensus
> reviewer's rows are verified complete; 21 other rows fill the core fields but have every outcome
> column still blank (`extraction_coverage.rows_missing_outcomes`; reported by `main()` as
> *progress*, deliberately **not** as a data-quality warning). Two consequences:
>
> 1. **Compute outcome-domain figures over verified rows only.** Including in-progress rows drags
>    every rate downward and looks like a reviewer effect.
> 2. **No inter-rater statistic is computable from a mid-extraction export** — a "disagreement" is
>    usually one reviewer not having reached a field yet. (An earlier note here quoted a Jaccard
>    figure from this export; it was not a valid IRR and has been removed.)
>
> **Per-reviewer rows survive consensus.** Covidence can export them *after* consensus as well as
> before, so the database can use the consensus export while agreement statistics are computed
> from a separate per-reviewer export. Nothing about this is time-limited.
>
> **Agreement is measurable at all three review stages**, not just extraction — but only the
> extraction export currently carries a reviewer column. `screen`, `select`, `included` and
> `excluded` are bibliographic record lists with **no reviewer field at all**, so title/abstract
> and full-text agreement need an *additional* Covidence export (per-reviewer screening
> decisions), not a re-parse of `data/`. Note when reporting screening κ that the stage is heavily
> prevalence-imbalanced, which deflates κ — pair it with raw agreement or PABAK.

> ⚠ Because these are single-reviewer extractions, **published values can still change**.
> The dashboard says so in the pilot banner. Reviewers do disagree in the current export
> (e.g. #29156 Addy 2012: `N randomized` 32 vs 30; #30126 Baggott 2016: phase `1` vs
> `Unregistered`), which is exactly what consensus is for — and what makes an
> inter-rater-agreement figure worth producing (see the analysis plan).

## Template revisions — what changed, and what broke

The extraction template was revised between the 2026-06-18 and 2026-08-27 exports:

| | Old template (17 cols) | Revised template (32 cols) |
|---|---|---|
| **Removed** | `Study type`, `Number of conditions/arms`, `Derivative?`, `Microdosing study?`, `Outcomes` | — |
| **Renamed** | `Parent Study DOI` | `Parent study DOI` (lower-case *s*) |
| **Added** | — | `Trial Phase`, `N randomized`, `N analyzed (if applicable)`, `Sex-specific population?`, `Co-administration/Pre-treatment Drug(s)` |
| **Restructured** | one free-text `Outcomes` cell | **15 outcome-category columns** (`Cognitive` … `Other outcomes`), each a `;`-separated list of specific measures |

**The failure this caused (worth remembering).** `_classify()` identified the extraction
export by requiring both `Reviewer Name` *and* `Study type`. When the revision deleted
`Study type`, the export stopped being recognized — and because a missing extraction file
was a legitimate state, the build **succeeded** with `n_extracted: 0`. Nothing errored.
Two guards now exist:

1. `_classify()` keys only on `Reviewer Name` + `Covidence #` — columns a template
   revision will not remove.
2. `build()` **exits with an error** if any CSV has a `Reviewer Name` column that it
   could not classify.

**Rule of thumb:** never key file detection, or any control flow, on a template column
that a reviewer could delete. Read new columns defensively with `.get()` and let missing
values be empty.

### Gotchas in the revised template

- **`Trial Phase` does double duty.** It holds a phase (`1`, `2`, `3`) for registered
  trials but also the sentinels `Unregistered` and `Not Applicable`. The build splits
  these into two clean fields: `phase` (`Phase 1` / `N/A` / `""`) and
  `registration_status` (`registered` / `unregistered` / `unknown`), where a recognized
  registry id always wins. A phase recorded with **no** registry is a contradiction and
  raises a build warning (it also catches typo'd registry ids — e.g. `CT03019822,`
  missing its `N`, which `_norm_registry` correctly refuses to treat as a registry).
- **A controlled-vocabulary label contains the `;` separator**: `Persisting (PEQ; not
  HPPD)`. `_split_list()` is parenthesis-aware so this is not shredded into two bogus
  categories. Any future label with a `;` inside `()` is handled; one outside is not.
- **`vison` is misspelled in the Covidence option list** for *Sensorimotor & perception*
  (4 rows). Fix it in the Covidence template — the build passes vocabulary values through
  verbatim by design, so correcting it here would mask the source error.
- **Multi-drug studies are common.** `Psychedelic/Intervention Drug(s)` is `;`-separated
  (e.g. `2C-B; MDMA; psilocybin`); the build normalizes it to `drugs[]` and the dashboard
  facet matches on *any* member. `drug` (first listed) is kept for the table badge.
- **`Microdosing study?` was removed** with no replacement. Microdose trials are no longer
  identifiable from the template. With dose ruled out of scope, restoring the flag is the
  only way to separate microdose trials — see
  [Extraction-template gaps](#extraction-template-gaps-post-review-2026-08-26).

## Files

| Path | Role |
|------|------|
| `data/*.csv` | Raw Covidence exports. Drop new ones here. Filenames are timestamped by Covidence. |
| `build_database.py` | `build()` returns the dict; `main()` writes `_data/master_db.json`. Re-run after every new export. |
| `tests/test_build_database.py` | Stdlib `unittest` suite for the build pipeline. See [Tests](#tests). |
| `PAPER_OUTLINE.md` | Planning doc: the systematic-map paper, its figure plan, and which figures the current schema can and cannot support. |
| `figures/` | Preview figure scripts (matplotlib + numpy), one per viable figure, plus `make_figures.py`. Reads the committed `_data/master_db.json`, never the raw CSVs. See `figures/README.md`. |
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
| `screen`   | In title/abstract screening (not yet adjudicated) | 1,270 |
| `select`   | Passed title/abstract; in full-text review | 810 |
| `included` | Passed full-text review (→ the database) | 95 |
| `excluded` | Excluded at full-text (reason in `Notes`) | 11 |
| *(none of the above, has `Reviewer Name`)* | Extraction template | 45 studies / 61 rows |

`build_prisma()` derives the funnel with set algebra (robust even if a future export overlaps):
records in review = ∪ of all stages; advanced-to-full-text = select ∪ included ∪ excluded;
still-in-screening = the remainder. Full-text **exclusion reasons** are tallied from the excluded
export's `Notes` (`"Exclusion reason: <reason>;"`).

### ⚠ What the stage exports do NOT contain (`prisma_manual.json`)

The stage exports **omit the top of the PRISMA funnel**: *records identified per database*,
*duplicates removed*, and **records excluded at title/abstract screening**. (The `screen` export
is only studies *still in* screening, not those already rejected.) So "records in the review"
(`records_in_review`) is **not** the total screened — it starts mid-funnel.

These numbers live on the Covidence dashboard and are entered by hand in
[`prisma_manual.json`](prisma_manual.json) — **now filled**:

```json
{ "records_identified": 14502, "duplicates_removed": 6951,
  "auto-marked-ineligible": 2781, "excluded_title_abstract": 2584 }
```

`auto-marked-ineligible` is Covidence's automated screening. **PRISMA 2020 counts those records as
"removed before screening"**, alongside duplicates — *not* as screened — so:

```
14,502 identified − (6,951 duplicates + 2,781 automation) = 4,770 screened
4,770 screened − 2,584 excluded at title/abstract        = 2,186 records in review ✓
```

which reconciles exactly with the stage exports. `build_prisma()` reads the file into
`prisma.manual`, deriving `records_screened`, `removed_before_screening`, `complete`, and
`reconciles`/`reconcile_delta`. **A mismatch raises a build warning and an amber box on the
dashboard** rather than silently drawing a wrong diagram — so a stale hand-entered number cannot
pass unnoticed after a new export. Keys are accepted in snake_case *or* hyphenated form, so
`auto-marked-ineligible` works without reformatting the file.

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

Derived facets, continued:
- `drugs[]` — every agent administered (multi-drug studies); `drug` = first listed
- `healthy_volunteers` — true only when the sample is healthy volunteers *and* no clinical
  indication was identified (a record whose population is simply unknown is neither
  healthy nor patient — the dashboard's Population facet respects that)

Extraction template (only populated when `extracted: true`):
`reviewer, n_extractions, parent_study_doi, phase, phase_raw, registration_status,
n_randomized, n_analyzed, n, n_source, drugs_raw, coadmin, comparator, comparator_types[],
population, sex_specific, outcome_domains[], outcome_measures[], qualitative_outcome,
extraction_notes`

- `phase` — `Phase 1|2|3` / `N/A` / `""`; `phase_raw` keeps the template cell verbatim.
- `registration_status` — `registered` (a recognized registry id exists) / `unregistered`
  (`Trial Phase` said so) / `unknown`.
- `n` / `n_source` — best available sample size: `n_randomized` if present, else
  `n_analyzed`, with `n_source` naming which (`"randomized"` | `"analyzed"` | `""`).
- `outcome_domains[]` — which of the 15 template categories were assessed (the facet).
- `outcome_measures[]` — `"Domain: measure"` for every specific measure (detail + export).
- `comparator_types[]` — `Placebo` / `Low-dose active` / `Active drug` /
  `Waitlist / care as usual` / `Psychotherapy`; a study can be several at once.
- `n_extractions` — how many reviewers have extracted this study (dual-extraction progress).

Trial linkage (all studies):
- `registry_norm` — canonical trial id (NCT preferred; other registries recognized;
  non-registry accessions like `WOS:…` normalize to `""`). See `_norm_registry()`.
- `parent_doi_norm` — normalized `Parent study DOI` (lower-cased, `doi.org/` stripped).
- `trial_key` — the grouping key, in priority order (see `_link_trials()`):
  1. `registry_norm` — the canonical case;
  2. the **parent's registry id**, if the named parent paper is in the DB and registered
     (a secondary analysis whose own registry cell was left blank);
  3. `"doi:<parent_doi_norm>"` — an **unregistered trial identified by its source paper**.
     A paper that is itself named as a parent by another paper adopts its *own* DOI as
     this key, so the source paper joins the group;
  4. `null` — no registration and no linked source paper.
- `trial_key_source` — which rule fired: `registry` | `parent-registry` | `parent-doi` |
  `source-paper`.
- `connected_ids[]` — Covidence #s of **other papers in the DB sharing this trial**.

> **Why rule 3 matters.** The earlier implementation only linked a child to its parent if
> the parent paper was *itself in the database*, so a report of an unregistered trial whose
> source paper had not been included stayed orphaned — which defeated the purpose of
> extracting parent DOIs. Keying on the DOI itself means several reports of one
> unregistered trial group correctly regardless of whether the source paper is included
> (verified: Addy 2015 ↔ Addy 2012, Cami 2000 ↔ delaTorre 2000, Borissova 2021 ↔
> Carhart-Harris 2015).

`trials[]` (one per **identified** trial — registered *or* DOI-identified; powers the Trials tab):
`trial_key, registry, registry_url, source, fetched, fetch_status, details{…}|null, paper_ids[]`
(+ `source_doi` on `doi:` keys).
`details` (when `fetch_status == "ok"`): `title, status, study_type, phase, allocation, model,
masking, enrollment, enrollment_type, conditions[], arms[], sponsor, industry, start,
completion, countries[], primary_outcomes[], results_posted`. See
[enrichment](#trial-registry-enrichment--trial-cards) for `fetch_status` values.

`meta` block: `generated, review_id, n_included, n_extracted, drugs[], indications[],
outcome_domains[], outcome_measures[], phases[], comparator_types[], registries[],
n_trials, n_registered_trials, n_unregistered_trials, n_trials_enriched,
n_multi_paper_trials, year_min, year_max, consensus_reviewer, extraction_coverage{…},
warnings[], source_included, source_extraction`.

- `outcome_domains[]` populates the **Outcome domain** facet and keeps *template order*,
  not alphabetical order (the categories have a meaningful reading order).
- `phases[]`, `drugs[]`, `indications[]` populate their facets; `registries[]` is retained
  for tests / future use (the trial-registry *filter* was removed).
- `warnings[]` — data-quality contradictions found during the build (printed by `main()`;
  see [Gotchas](#gotchas-in-the-revised-template)). Currently: a phase recorded without a
  registry id; N analyzed exceeding N randomized; PRISMA numbers that fail to reconcile; and
  **extraction rows whose core fields are filled but whose 15 outcome columns are all blank**
  (`extraction_coverage.rows_missing_outcomes`).

`prisma` block: `records_in_review, in_screening, advanced_to_fulltext, fulltext_in_review,
fulltext_excluded, fulltext_excluded_reasons{reason: count}, included, extracted, source_files,
manual{records_identified, duplicates_removed, auto_marked_ineligible, excluded_title_abstract,
records_screened, removed_before_screening, complete, reconciles, reconcile_delta}`
(see the [screening-exclusion caveat](#-what-the-stage-exports-do-not-contain-prisma_manualjson)).

## Dashboard behavior

- Full-text search (title/authors/abstract/journal/year) + facet filters (**drug**,
  **condition**, **outcome domain**, **population**, **phase**, **registration**, extraction
  status, year range) + sortable columns (study, year, drug, condition, **N**, **phase**).
  Click a row to expand the full record (abstract + all extraction fields + outcomes grouped
  by domain + DOI/PMID/registry links).
  - The **Drug** facet matches any member of `drugs[]`, so a three-arm comparison of 2C-B /
    MDMA / psilocybin appears under all three.
  - The **Outcome domain**, **Phase**, and **N** facets only surface extracted studies
    (pending records have no extraction fields yet).
  - **Population** is `Healthy volunteers` vs `Patient population`; a record whose population
    is unknown matches neither, deliberately.
- A collapsible **PRISMA study-flow** box (top of page) is rendered server-side from the
  `prisma` block via Liquid, so it needs no JS and stays in sync with the data.
- **Papers / Trials tabs.** A tab bar switches between the **Papers** view (default — the
  search/table; trials never appear here) and the **Trials** view (a supplement). Trials
  cover both registered trials (grouped by `registry_norm`) **and unregistered trials
  identified by a source-paper DOI**; only papers with neither identifier are paper-only.
- **Trial cards** (Trials tab) show the registry details auto-pulled from ClinicalTrials.gov
  (see [enrichment](#trial-registry-enrichment--trial-cards)) plus *Papers in this database
  from this trial*. An unregistered trial's card is titled *"Unregistered trial"* and links
  the source-paper DOI instead of a registry. Card DOM ids are slugified
  (`doi:10.1038/npp.2014.12` → `trial-doi-10-1038-npp-2014-12`) so `/` and `.` don't break
  `getElementById`. **Cross-navigation:** a paper card's *"View trial details →"* opens the
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
- **Non-NCT registries** (the big one): the CT.gov API can't resolve them. Tested 2026-08-26:

  | Registry | Programmatic access |
  |---|---|
  | **ISRCTN** | ✅ public XML API, incl. `?format=who` → the full **WHO Trial Registration Data Set** (68 fields) |
  | **ANZCTR** | ❌ HTTP 403 to scripted requests (bot protection) |
  | **Dutch CCMO / OMON** | ❌ no API (HTML record only) |
  | **NTR** (old Dutch) | ❌ trialregister.nl retired 2022 |
  | **EU CTIS** | ❌ public API requires an auth token |
  | **EU CTR** (EudraCT) | ❌ HTML search only |
  | **WHO ICTRP** | ⚠️ no REST API; weekly bulk XML by request form |

  **Every recognized id is nonetheless linked** — `_registry_url()` builds verified URLs for
  NCT, ISRCTN, ANZCTR, Dutch OMON and DRKS, and falls back to the WHO ICTRP search portal
  (`trialsearch.who.int/?TrialID=…`) for anything else recognized. Trials still render as
  `unsupported_registry` (no structured details) but are never a dead end.
  *Dutch subtlety:* cells read `NL70508.068.1; NL-OMON55178` — `_norm_registry` keys the trial on
  the ABR number, but only the **OMON** id resolves, so `_registry_url()` prefers it.

  **If a second adapter is ever wanted, write `_parse_who()`, not `_parse_isrctn()`.** ISRCTN's
  `format=who` returns the WHO dataset, so one parser would also read ICTRP bulk XML and any
  other registry exposing that format. Differences from CT.gov: `study_design` is semi-structured
  text (`"Allocation: …; Masking: …"`) not enums, and dates are `DD/MM/YYYY`. Not built — the
  corpus contains zero ISRCTN trials today.
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

Covers (a) the pure helpers — Covidence-# / page / int parsing, parenthesis-aware list
splitting, multi-drug normalization, indication & healthy-volunteer derivation, phase &
registration-status splitting, comparator classification, outcome-column parsing, DOI &
registry normalization, CSV classification, stage-file disambiguation, trial grouping
(registry, parent-registry, parent-DOI, source-paper), CT.gov parsing; and (b) `build()`
against the real exports — split into **invariants** (PRISMA reconciliation, required keys,
consensus-row uniqueness, pending records carrying no extraction fields, sample-size
coalescing, DOI/URL coalescing, sort order, facet-vocabulary/study agreement, symmetric
trial linkage) and **current-fixture counts** (`n_included`, `n_extracted`, extraction
coverage, PRISMA numbers). When you add exports and the counts legitimately change, update
`test_current_counts` — the invariant tests should keep passing untouched.

Two regression tests are worth keeping forever:
`test_classify_survives_template_revisions` (the silent-zero failure above, plus a check
that the *real* export on disk is recognized) and
`test_link_trials_groups_unregistered_reports_by_parent_doi`.

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

## Extraction-template gaps (post-review, 2026-08-26)

The 2026-08 revision closed several gaps: **sample size**, **trial phase**, **registration
status**, **structured outcome domains**, **co-administered drugs**, and **trial linkage**
(registry + parent DOI).

A review on 2026-08-26 then ruled the following **out of scope for extraction**, with reasons
worth recording so they are not re-litigated:

| Ruled out | Reason given |
|---|---|
| **Dose** (per arm, sessions, cumulative) | Significant reviewer burden; heterogeneously reported (mg vs mg/kg); varies by route; especially awkward for PK dose-response designs |
| **Psychotherapy / psychological support** | Not being extracted |
| **N per arm** | Many of these are crossover trials, where per-arm N is just total N |
| **Route of administration** | Not worth the lift |
| **Primary-outcome designation** | Many early-phase and healthy-volunteer studies have no clear primary outcome |
| **Race / ethnicity** | Not wanted |
| **Risk of bias (RoB 2)** | Out of scope entirely |

Corroborating the dose decision: even ClinicalTrials.gov reports dose inconsistently — of 18
enriched trials only 4 give an explicit mg/µg dose in their arm labels and 3 more give an ordinal
level; the other 11 give none. There is no free registry-side substitute, so the burden argument
holds on the registry side too.

> ⚠ **This gap list was inferred from the values present in the export**, so template options that
> exist but have never been used are invisible to it — that is how `expectancy` was wrongly listed
> as missing when it is in fact an available option that no study has yet recorded. **Check this
> list against the actual Covidence codebook before acting on it.**

### What remains on the list

1. **Restore the microdosing flag.** The revision removed `Microdosing study?` with no
   replacement, so microdose trials are currently unidentifiable. With dose out of scope this is
   the *only* way to separate them, and without it a 15 µg and a 200 µg LSD study sit in the same
   cell of every drug-level figure. Very low cost; reviewer is open to it.
2. **Give *both* `N randomized` and `N analyzed` an explicit "not reported" option.** Older
   unregistered studies often report a single N and never mention dropouts, so a blank means
   either "no dropouts" or "not reported". Either field being blank makes attrition
   undeterminable, and `N randomized` is already missing on 18% of extracted rows — so one option
   on one field is not enough. Very low cost.
3. **Design + blinding, asked only when `Trial Phase = Unregistered`.** See the registry note
   below — the one place where extracting design data is *not* duplicated effort. Vocabulary,
   derived from what CT.gov encodes so the two sources stay comparable:
   - **Design:** `parallel` · `crossover` (incl. within-subject) · `factorial` ·
     `quasi-randomised` · `other` · `not reported`. **Deliberately no `single-group`** — in a
     database of randomised trials it should not exist, and our one instance was a registration
     error (see the registry-QC note below). A reviewer reaching for it is really raising a
     screening question.
   - **Blinding: record *who* was masked, not a single/double/open label.** CT.gov stores a
     *count* of masked parties plus the roles, and the two come apart — among our trials
     "Double" is participant+investigator 3× but participant+care-provider once, and the two
     "Single" trials are participant-only and **outcomes-assessor-only**, i.e. in one the
     participant is blind and in the other they are not. Collapsing to the classic label destroys
     exactly the distinction that matters for a psychedelic trial. Use a multi-select —
     `participant` · `care provider (therapist/session monitor)` · `investigator` ·
     `outcomes assessor` — plus exclusive `nobody (open-label)` and `not reported`;
     single/double/triple/quadruple is then *derived* by counting.
   - **Allocation needs no field** (17/18 randomised, and the database is RCTs by definition).
4. **Age (mean/range) and % female** — optional; reviewer "could be persuaded".
**Not a gap after all:** `expectancy` is already a template option. It has been recorded for
**zero** studies, which is a finding rather than a missing field.

### ⚑ Don't extract what the registry already gives you

For enriched trials, CT.gov supplies at 100% field coverage: `allocation`, **design model**
(10 parallel / 7 crossover / 1 single-group), **masking** (4 double / 9 triple / 3 quadruple /
2 single), planned `enrollment`, `sponsor` + **industry flag** (5 industry / 13 non-industry),
**countries**, **primary outcomes**, **registration date** (→ prospective vs retrospective:
15 vs 3), start/completion dates, and **results-posted** (6 of 18).

- **Never re-collect these for registered trials.** Take them from the registry and label them as
  registry-sourced (they describe the *planned protocol*; never overwrite an extracted value).
- **Registry enrollment ≠ paper N**, and the difference is informative rather than an error:
  Bershad 2019/2020 report 20 participants from an 80-participant registered trial.
- The registry is also a **QC channel**: `NCT00823407` (Baggott 2010) is registered as
  `Single Group` in a database of *randomized* trials, and `NCT01951508` has no allocation
  recorded.
- **Design labels can be wrong, and the arm structure is the reliable signal.** `NCT00823407`
  (Baggott 2010) registers `allocation: RANDOMIZED` with `interventionModel: SINGLE_GROUP` — a
  contradiction — and its single arm "MDA" lists *two* interventions, `Drug: MDA` and
  `Drug: Placebo`, double-masked. Every participant gets both: it is a crossover. The cause is a
  registration habit, not a typo — `NCT01951508` has the same one-arm-many-drugs shape and *is*
  labelled `CROSSOVER`. So trust the structure over the label: **one arm group holding several drug
  interventions is a crossover.** `_registry_qc()` implements this check and warns.
- **Umbrella registrations exist and they break the "one NCT = one trial" assumption.**
  `NCT03790358` ("Mood Effects of Serotonin Agonists", 80 enrolled) lists **MDMA** dose arms, but
  both papers under it (Bershad 2019, Bershad 2020) report **LSD** microdosing with n=20 each —
  different substudies sharing one registration, not subgroup analyses. So `trial_key` grouping
  counts papers per *registration*, which over-merges umbrella cases; unregistered reports with no
  parent DOI under-merge in the other direction. State both when reporting papers-per-trial.
- **Registry "actual enrolment" is not reliably N randomized or N analyzed.** In the four trials
  where the database holds both, it matched N analyzed 3× and N randomized 2× (one matched both).
  Treat an enrolment discrepancy as a question, not an error.

### Data-quality / structural

- `Trial Phase` mixes phase with registration status (`Unregistered`, `Not Applicable`). The build
  splits it, but two columns would be cleaner and would stop reviewers recording a phase for a
  trial they also believe is unregistered (8 rows do this today).
- **`vison`** is misspelled in the *Sensorimotor & perception* option list.
- `Persisting (PEQ; not HPPD)` contains the `;` list separator inside its label. The parser
  handles it, but avoid `;` in new option labels.
- Free-text `Other: …` values are common in the drug and comparator columns. Promote recurring
  ones to first-class options so faceting stays clean.
- **Reviewer disagreement is real** and currently invisible in the published data (16 of 45
  studies are dual-extracted). Run consensus, then flip `CONSENSUS_REVIEWER` to `None`.
- Some records lack a DOI (conference abstracts, older trials); keep PMID/registry as backup
  stable identifiers.

## Future directions — download tracking

**Why it doesn't work today:** the CSV/RIS buttons build the file **client-side** (a `Blob`
from data already on the page → synthetic `<a download>`). On a static site that makes **no
network request**, so nothing — GitHub, Zenodo, a CDN, a server log — can count it. This is
unlike the metapsy datasets, whose counts come from the data living on GitHub + Zenodo (see
`scripts/clone-tracking/fetch.py` + `fetch_zenodo.py` → `_data/download_totals.yml`).
NB: linking to a raw file in `assets/` on GitHub Pages is **also** uncountable (Pages exposes no
download logs) — it must be a real release/deposit or an analytics/beacon hook.

**Plan (do both — they answer different questions):**

1. **Canonical, citable artifact = authoritative counts (primary).** Have `build_database.py`
   also emit a full-database `psychedelic-rcts.csv`, and publish it as a **Zenodo** deposit
   (mint a DOI; per-version + concept-level download counts — great for "others export to start
   their own reviews") and/or a **GitHub data repo / Release** like `metapsy-project/data-*`.
   Then **reuse the existing pipeline**: add the repo to `scripts/clone-tracking/fetch.py` and
   the Zenodo concept recid to `fetch_zenodo.py`; the total flows into `_data/download_totals.yml`
   and can render on the page exactly like the metapsy sidebar (`site.data.download_totals`).
   Add a **"Download the full database (citable) →"** button pointing at that artifact (the
   counted, canonical download); keep the client-side filtered CSV/RIS as an untracked
   convenience. Fits the living/versioned model — each rebuild = a new Zenodo version.

2. **Analytics events = usage of the interactive/filtered exports (complement).** Site analytics
   is **already configured** (`_config.yml` → `analytics.provider: google-gtag`, `G-YTGXSZFJ08`),
   so this is nearly free: fire `gtag('event', 'file_download', { format: 'csv'|'ris', rows: <n
   filtered>, filters: <state> })` from the CSV/RIS click handlers in
   `docs/datasets/master-db/index.html`. Captures what the artifact can't (which formats, how
   many rows, which filters people actually export). *Caveats:* ad-blockers undercount and these
   are click events, not authoritative downloads — hence pairing with #1. (A privacy-friendly
   alt like Plausible/GoatCounter, or a `navigator.sendBeacon` to a small counter/Cloudflare
   Worker, would work the same way if GA is ever dropped.)

**Bottom line:** Zenodo/GitHub artifact for the citable, authoritative number (consistent with
the other SYPRES datasets); gtag events layered in for interactive-export usage.
