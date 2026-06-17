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

## ⚠ TODO next session — sidebar fix over-corrected (layout regression)

The site-wide rule added to `assets/css/custom.css` to fix the off-center gutter went too far.
It forces **every** sidebar-less page to full-width + left-aligned:

```css
#main:not(:has(.sidebar)) > .page,
#main:not(:has(.sidebar)) > .archive { float: none; width: 100%; }
```

**Regressions reported (desktop width):**
- **Home / landing** (`index.md`, `layout: home` → `.archive`) — was centered, now **left-shifted**.
- **News** (`/docs/blog/index`, `layout: blog` → `.archive`) — was centered, now **left-shifted**.
- **Team** (`/docs/team`, `layout: archive` → `.archive`) — was right-shifted, now left-shifted; **wants centered**.
  (Team's content is a fixed `width: 1000px` `<table>` — centering the column alone won't center it;
  the table likely also needs `margin: 0 auto`.)

**Looks correct and should stay as-is:** the RCT database, Methods, Overview, Publications.

**Why:** the database *wants* full width (`classes: wide` + a wide dashboard/table); the landing/
list pages want a **centered, constrained column**. One blanket rule can't serve both.

**Candidate fix (don't blanket full-width):**
- Keep `float: none; width: 100%` **only** for `.wide` sidebar-less pages (the database).
- For non-wide sidebar-less pages, **center** the existing column instead of widening it, e.g.
  `#main:not(:has(.sidebar)) > .page, … > .archive { float: none; margin-left: auto; margin-right: auto; }`
  (keep the theme's `width: calc(100% - sidebar)`; possibly also zero the leftover `padding-right`
  for symmetry). Then add `margin: 0 auto` to the Team table.
- Mechanics: `.page` rules in `_sass/minimal-mistakes/_page.scss`, `.archive` in `_archive.scss`;
  `.wide` (which only zeroes right padding) in both.

**Test matrix (≥ ~1024px, where the float applies):** Home `/`, News `/docs/blog/index`,
Team `/docs/team`, Methods `/docs/methods`, Overview `/docs/datasets`, Publications
`/docs/community/publications`, database `/docs/datasets/master-db`, and a **sidebar** page
(`/docs/datasets/PSILODEP`) to confirm no regression there. Each uses a different layout, so
check them all.

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
   python3 analysis/master-db/build_database.py
   python3 -m unittest discover -s analysis/master-db/tests
   ```
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

`meta` block: `generated, review_id, n_included, n_extracted, drugs[], indications[],
outcomes[], year_min, year_max, source_included, source_extraction`.
`meta.outcomes[]` is the sorted union of all extracted outcome domains — it populates the
dashboard's **Outcome** facet.

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
- **Export buttons export exactly the filtered rows.** CSV = full field set; RIS = importable
  into Zotero/EndNote/Mendeley/Covidence/Rayyan.
- Pure client-side; data is embedded at build time (no fetch / no CORS issues). Fine for
  hundreds of rows. If the included set grows into the thousands, add pagination/virtualized
  rendering and consider fetching the JSON from `assets/` instead of embedding.

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
