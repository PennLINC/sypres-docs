# sypres.io
:triangular_ruler: Website for the [SYPRES](https://sypres.io) Project

## Website Overview

The site is organized into four main sections, accessible from the top navigation bar:

| Section | URL | Description |
|---------|-----|-------------|
| **Studies** | `/docs/datasets` | Overview of SYPRES and living evidence, with individual study pages (e.g. Psilocybin for Depression) |
| **Team** | `/docs/team` | Current SYPRES team members |
| **Publications** | `/docs/community/publications` | Published papers and citations |
| **News** | `/docs/blog` | Project updates, conference appearances, and announcements |

Additional pages linked from within the Studies section include search terms, extraction SOPs, effect sizes, and reproducibility guides for each dataset.

## Analysis & Project Setup

For setting up the R environments used in SYPRES analyses, see the [analysis README](analysis/README.md).

## Scripts

Python scripts in `scripts/` handle reference formatting and enrichment. They require Python 3.10+ and a few packages:

```
pip install pybtex requests
```

### format_pubs.py — Project publication formatting

Converts SYPRES's own project publication BibTeX files (under `_data/publications/*.bib`) into HTML citation lists (under `_includes/publications/`). These are the publications *by* the SYPRES team, not the trial reference lists.

```
python scripts/format_pubs.py
```

Reads from and writes to:
- `_data/publications/core_publications.bib` → `_includes/publications/core_publications.html`
- `_data/publications/psilodep.bib` → `_includes/publications/psilodep.html`
- `_data/publications/mdmaptsd.bib` → `_includes/publications/mdmaptsd.html`

### parse_references.py — Trial reference lists (with Blossom enrichment)

Generates numbered HTML reference lists for each living review dataset. If Blossom API enrichment data exists (see below), it merges per-study summaries and abstracts as expandable `<details>` blocks under each citation.

```
python scripts/parse_references.py
```

Reads from and writes to:
- `docs/_data/psilodep_refs.json` + `_data/publications/psilodep_blossom.json` → `_includes/publications/psilodep_refs.html`
- `docs/_data/mdmaptsd_refs.json` + `_data/publications/mdmaptsd_blossom.json` → `_includes/publications/mdmaptsd_refs.html`

If no `*_blossom.json` file exists for a dataset, the script still works — it just renders plain citations without expanders.

### fetch_blossom_metadata.py — Blossom API enrichment

Fetches per-study metadata (paragraph summaries, abstracts, study characteristics) from the [Blossom API](https://www.moreblossom.com/developers) and writes enrichment JSON files that `parse_references.py` consumes.

**Setup:** Export your Blossom API key as an environment variable (never commit it):
```
export BLOSSOM_API_KEY=ak_your_key_here
```

**Usage:**
```bash
# Fetch all datasets:
python scripts/fetch_blossom_metadata.py --all

# Fetch a single dataset:
python scripts/fetch_blossom_metadata.py --dataset psilodep

# Dry-run a single study (prints raw API response, writes nothing):
python scripts/fetch_blossom_metadata.py --dataset psilodep --only "Davis, 2021" --dry-run

# Force re-fetch (ignore 30-day cache):
python scripts/fetch_blossom_metadata.py --dataset psilodep --force
```

The script caches responses locally in `scripts/.blossom_cache/` (gitignored) with a 30-day TTL. Re-runs are fast and idempotent.

### Full regeneration workflow

When references or enrichment data change, regenerate everything with:

```bash
export BLOSSOM_API_KEY=ak_...
python scripts/fetch_blossom_metadata.py --all
python scripts/parse_references.py
python scripts/format_pubs.py
```

## Development

### Building and serving locally

If you haven't installed ruby:

```
brew install rbenv ruby-build
rbenv install 3.1.4 # current version of ruby the website uses
eval "$(rbenv init -)"
```

You only need to run this command once:
```
bundle install
```

Then you can serve locally anytime using:
```
bundle exec jekyll serve
```

If your terminal session is restarted, you may need to re-run the eval command when you come back.
Then you can run `bundle exec jekyll serve` again and it should work.
If you're having trouble, check that the version is correct: `ruby -v`.