# Master-DB figures

Preview figures for the systematic-map paper. One script per figure, plus a
runner. See [`../PAPER_OUTLINE.md`](../PAPER_OUTLINE.md) for what each figure is
arguing and [`../CLAUDE.md`](../CLAUDE.md) for the data dictionary.

```bash
python3 analysis/master-db/build_database.py        # refresh the data first
python3 analysis/master-db/figures/make_figures.py  # regenerate everything
python3 analysis/master-db/figures/make_figures.py fig05 fig11   # a subset
MDB_FIG_DARK=1 python3 analysis/master-db/figures/make_figures.py  # dark steps
```

Output lands in `output/` as **PNG (200 dpi) and PDF** — the PDF is vector, so it
is the one to hand a journal.

**Dependencies:** matplotlib + numpy. (`build_database.py` itself stays
stdlib-only; only the figures need these.)

**Data source:** the committed `_data/master_db.json`. The scripts never read the
raw Covidence CSVs, so a figure can never disagree with the dashboard — but it
also means you must re-run `build_database.py` after dropping in a new export.

## The figures

| Script | Figure | Denominator | Status |
|---|---|---|---|
| `fig01_prisma.py` | Study flow (PRISMA 2020) | whole review | ✅ complete |
| `fig02_growth.py` | Growth and composition by drug | **all 95 papers** | ✅ at full scale already |
| `fig03_gap_matrix.py` | Evidence-and-gap matrix, drug × population | all papers → trials | ✅ |
| `fig04_papers_trials.py` | Papers vs trials, publication tail | all papers | ✅ |
| `fig05_outcomes.py` | Outcome landscape (the core-outcome-set case) | verified extractions | ✅ |
| `fig06_scale.py` | Sample size, by era and population | verified extractions | ✅ (+ honest attrition panel) |
| `fig07_design.py` | Comparator, design model, who was masked | verified + registry | ⚠ B/C registered trials only |
| `fig08_who_where.py` | Geography and population composition | verified + registry | ⚠ no demographics by scope decision |
| `fig10_registration.py` | Registration status, prospective, results posted | verified + registry | ✅ |
| `fig11_integrity_safety.py` | What is never checked | verified extractions | ✅ |

Figure 9 (dose landscape) is **not implemented** — dose is out of scope, so there
is nothing to plot. Figure 10D (outcome switching) was cut for the same reason it
was cut from the plan. Registration-status-over-time lives only in Figure 10; it
would have duplicated a Figure 4 panel.

## Two rules the scripts follow

1. **Verified rows only** for anything extraction-derived. `_common.verified()`
   returns studies whose extraction is complete (the consensus reviewer's rows).
   In-progress rows have blank outcome columns and would drag every rate down,
   which reads as a reviewer effect when it is really missing data.
2. **The denominator is stamped on every figure.** At this stage n is part of the
   finding — several panels rest on 16 studies and must not be read as results.

## Palette

One validated categorical order (`_common.SERIES`), assigned in fixed order and
never cycled; a sequential blue ramp for magnitude; the reserved status palette
for good/warning/critical states only. Three light-mode slots sit below 3:1
contrast, so every figure using them ships direct value labels — that is
deliberate, not decoration. `MDB_FIG_DARK=1` swaps in the dark steps (for web
embedding; journal figures stay light).

## Publishing to the site

`analysis/master-db/` is **excluded from the Jekyll build**, so nothing in
`output/` reaches sypres.io as-is. To put a figure on the dataset page, copy the
PNG into a directory Jekyll does build (e.g. `assets/`) as a deliberate step —
the `psilodep`/`mdmaptsd` folders are included precisely because their dataset
pages embed figures from them.
