# Paper & figure outline — the psychedelic RCT evidence map

**Status:** planning document. Written 2026-08-26, then **revised twice after Parker's review**
the same day (scope decisions, then comment follow-ups). Scored against the pilot database (95 included papers; 45 with ≥1 reviewer extraction; 16
with a consensus-equivalent row). Every number quoted is **provisional** — they show which
figures the schema can support, not results.

Companion documents: [`CLAUDE.md`](CLAUDE.md) for the pipeline, data dictionary, and the
extraction-template gap list; [`figures/`](figures/) for runnable preview scripts — one per
viable figure, regenerated with `python3 analysis/master-db/figures/make_figures.py` after each
rebuild.

> **Scope decisions from review (2026-08-26).** Dose, psychotherapy, per-arm N, route,
> primary-outcome designation, race/ethnicity, and risk-of-bias were all judged **out of scope**
> for extraction. This revision reflects those decisions rather than re-arguing them: figures that
> depended on those fields are cut or reduced, and the gap list is now four items, not eight.

---

## 1. What we are striving toward

A **living systematic map** (evidence-and-gap map) of *every randomized controlled trial that has
administered a psychedelic drug* — any drug, any population, healthy volunteers included — paired
with an open, exportable, citable database.

This is deliberately **not** a meta-analysis. Its contribution is *structural*: it describes the
shape of an entire literature that has so far only been reviewed drug-by-drug and
indication-by-indication. The paper is the argument, the database is the instrument, and each new
Covidence export updates both.

### Why this is publishable

1. **Nobody has mapped the whole field.** Existing systematic reviews are drug × indication
   slices. Healthy-volunteer pharmacology — which the pilot suggests is the *majority* of the
   corpus (38 of 45 extracted studies) — is systematically excluded from them, and it is where
   most of the dosing, safety, and mechanism evidence actually lives.
2. **Papers are not trials, and the gap is large.** In the pilot, 40 linked papers reduce to 32
   distinct trials, with one trial contributing three papers. Every count in this literature
   quoted "per study" is inflated by an unknown factor. We can quantify it — including for
   *unregistered* trials, via source-paper DOIs, which is the piece other maps cannot do.
3. **No two trials measure the same set of things.** Among the 16 verified-complete extractions
   there are **15 distinct domain combinations, 14 of which are used by exactly one study**. This
   is the empirical case for a core outcome set. *(See the note under Figure 5 on what level of
   granularity this claim is — and is not — making. Earlier drafts quoted 26 combinations across
   29 studies; that used every reviewer row, including in-progress ones, and has been restated on
   the verified denominator.)*
4. **The field's registration and reporting record is measurable, and mixed.** In the pilot,
   extracted studies from the 2000s are almost entirely unregistered; from the 2020s, almost
   entirely registered. Of 18 registry-enriched trials, 3 were registered *retrospectively* and
   only 6 have posted results.

### Candidate venues

| Venue | Fit |
|---|---|
| **BMJ Open** / **Systematic Reviews** | Natural home for a systematic map + open database; permissive on length and figures. |
| **JAMA Network Open** | Higher profile; would want the registration/reporting-quality angle foregrounded. |
| **Nature Mental Health** / **Neuropsychopharmacology** | Best fit if the core-outcome-set argument leads. |
| **Lancet Psychiatry** (Review/Health Policy) | Aspirational; needs a sharp policy hook. |

A companion **data descriptor** (*Scientific Data*, *Data in Brief*) is worth considering for the
database artefact itself, citable separately from the map.

---

## 2. Figure plan

✅ possible now · ⚠️ partly possible · ⛔ out of scope after review.
Figure 11 was added after review; Figure 9 and panel 10D were cut.

### ✅ Figure 1 — Study flow (PRISMA 2020)
Rendered from the `prisma` block. **Upstream counts are now entered** and reconcile exactly:
14,502 identified − 6,951 duplicates − 2,781 auto-marked ineligible − 2,584 excluded at
title/abstract = 2,186 records in review. Following PRISMA 2020, automation removals are counted
as *removed before screening*, so records screened = 4,770. The build now checks this arithmetic
and warns if a hand-entered number drifts out of sync with the stage exports.

### ✅ Figure 2 — Growth and composition of the evidence base
Stacked area or bar, papers per 5-year window, 1960 → present, coloured by drug. Shows the two
distinct eras (a 1960s wave, a near-total gap through the 1980s–90s, the post-2000 renaissance)
and the compositional shift from LSD toward MDMA and psilocybin.
*Needs:* year + drug only — **available for all 95 papers without extraction.**
*Watch:* annotate or truncate the final partial window so the apparent 2025+ decline is not read
as real.

### ✅ Figure 3 — Evidence-and-gap matrix: drug × population
The signature figure of a systematic map. Bubble grid, drug on one axis, indication on the other;
bubble area = number of *trials* (not papers), fill = cumulative participants. Empty cells are the
point — they are the research-gap map.
*Needs:* drug, indication, N, trial key — **all present.**

### ✅ Figure 4 — Papers, trials, and fragmentation
- **4A** Distribution of papers per trial (pilot: 25 trials × 1 paper, 6 × 2, 1 × 3).
- **4B** Timeline: each trial a row, its papers as points, ordered by first publication.
- **4C** Registration status by publication year.
*Needs:* `trial_key`, `registration_status`, year — **all present**, and the parent-DOI linkage is
what makes 4A honest for unregistered trials. *The most novel figure in the set.*

### ✅ Figure 5 — The outcome landscape (the core-outcome-set argument)
- **5A** Heatmap: outcome domain × drug (or × indication), cell = % of trials assessing it.
- **5B** Co-occurrence / UpSet plot of domain combinations.
- **5C** Distinct sub-category measures within each domain (pilot range: 1–8 per domain).

> **What this figure claims, precisely.** We extract **outcome domains** and a controlled
> sub-category within each (e.g. `Psychiatric: depression`) — **not instruments**. So the claim is
> *not* "trials use a scattered set of scales"; that would need instrument-level extraction, which
> is out of scope. The claim is that **trials do not agree on which domains to measure at all**:
> 15 distinct domain combinations across 16 studies, 14 of them unique to a single study.
> This is the right level anyway — COMET-style core-outcome-set development explicitly establishes
> *core domains* first and selects instruments as a separate second stage. The figure supports
> stage one, and says nothing about stage two.

### ⚠️ Figure 6 — Statistical scale of the field
Distribution of N by decade, by phase, and by healthy-volunteer vs patient population. Pilot:
median 24, IQR 15–32, range 6–176. *Needs:* `n_randomized` — **present.**

*Attrition panel — contingent.* Only 10 of 45 extracted rows carry both N randomized and N
analyzed; **N randomized alone is missing on 18%**. The older unregistered studies often report
**a single N** with no statement about dropouts, so a blank is ambiguous between *"no dropouts"*
and *"not reported"* — and that ambiguity, not reviewer effort, is the real obstacle. The
"not reported" option is therefore needed on **both** fields, not just `N analyzed`: either one
being blank makes attrition undeterminable. With it, *"attrition was undeterminable in X% of
trials"* becomes a publishable finding rather than a hole.

### ⚠️ Figure 7 — Design and methodological rigour
Comparator type, parallel vs crossover, blinding level, and whether blinding integrity was
*assessed*. Comparator type is extracted; design model and masking come **free from
ClinicalTrials.gov** for registered trials (pilot: 10 parallel / 7 crossover / 1 single-group;
masking recorded for all 18). Blinding-integrity assessment comes from the `Trial integrity`
outcome domain.
⛔ *Blocked for unregistered trials* — roughly half the corpus, and the older half. The one
remaining extraction ask (gap #3) closes this.

### ⚠️ Figure 8 — Who is studied, and where
Trial geography from the registry (pilot: heavily United States and Switzerland), plus the
healthy-vs-patient split and single-sex studies.
Reduced after review: **race/ethnicity is not being extracted**, so the representativeness panel is
out. If age and % female are added (gap #4, optional), a demographic panel becomes possible;
otherwise this figure is geography + population composition only, and the paper should state
plainly that demographic representativeness was **outside the scope of this map** rather than
implying the data were unavailable.

### ⛔ Figure 9 — The dose landscape · out of scope
Cut after review. Dose extraction was judged not worth the burden: it is heterogeneously reported
(mg vs mg/kg), varies by route, and is especially awkward for PK dose-response designs.

**The data corroborate that judgement.** Even ClinicalTrials.gov carries dose inconsistently — of
18 enriched trials, only 4 state an explicit mg/µg dose in their arm labels and 3 more give an
ordinal level ("low dose", "high-dose psilocybin"); the other 11 give none. There is no free
registry-side substitute.

**What survives:** restoring the **microdosing flag** (gap #1) recovers a microdose vs full-dose
stratification. That is a coarse binary rather than a dose landscape — no dose-response — but
microdosing trials are a distinct literature with distinct effects, and being unable to separate
them at all would distort Figures 3, 5 and 6, where a 15 µg LSD study and a 200 µg LSD study
currently sit in the same cell.

### ⚠️ Figure 10 — Registration and reporting integrity
- **10A** Registered vs unregistered by year. ✅
- **10B** Prospective vs retrospective registration ✅ — from CT.gov registration and start dates
  (pilot: 15 prospective, 3 retrospective).
- **10C** Results posted to the registry ✅ (pilot: 6 of 18).
- **10D** ~~Outcome switching~~ — **cut.** Parker's objection is correct and decisive: in a
  database that deliberately includes secondary reports, a paper reporting a secondary outcome is
  the normal case, not evidence of switching. Detecting switching would require flagging *the
  primary report of each trial*, which we do not have and are not adding. A second problem
  confirms the cut: registered primary outcomes are free-text prose ("Percentage Change of the
  BOLD Signal", "area under the concentration time curve in oxytocin level") that will not map
  cleanly onto 15 coarse domains, so mismatches would mostly be parsing failures masquerading as
  findings.

### ✅ Figure 11 — Trial integrity and safety reporting *(added after review)*

A **negative-space figure**: the finding is not what these trials do, but what they never check.
Fully supported by the current schema — no new columns needed.

> All numbers below are computed over the **16 verified-complete rows only**. Other reviewers'
> rows are legitimately mid-extraction, and including them biases every rate downward. n = 16 is
> far too small to publish; it demonstrates the figure is computable, nothing more.

- **11A — Claimed blinding vs verified blinding.** Cross-tabulate the masking level the registry
  claims against whether the paper actually *assessed* blinding integrity (`Trial integrity`
  domain). Pilot: **3 of 6** enriched trials with a complete extracted paper verified their blind
  — the two that didn't and are triple/double-masked are the interesting cells. Across the
  verified rows, **81% show no blinding-integrity check at all**. In a field where functional
  unblinding is *the* central methodological criticism, that contrast is the whole argument.
- **11B — Safety reporting completeness**, by population and era: any safety outcome, structured
  AE collection, cardiovascular monitoring, longer-term safety. Pilot: **81% record no safety
  domain at all**; structured AE collection appears in 3 of 16.
- **11C — What safety means when it is reported.** Structured AE collection (3), cardiovascular /
  QTc (1). Abuse potential and HPPD — the psychedelic-specific harms — appear **zero times** in
  the verified rows (once each across all rows). That absence is the most pointed thing here.
- **11D — Expectancy.** `expectancy` is already an option in the template and **has not been
  recorded for a single study**. A zero is a legitimate and striking result for a figure about
  trial integrity: the field's most-discussed confound, available to record, never recorded.
  Worth confirming it is truly zero rather than not-yet-reached as extraction completes.

> **A caveat about this whole gap analysis.** I inferred the extraction template from the *values
> present in the export*, so **options that exist but have never been used are invisible to me** —
> which is exactly how I wrongly called expectancy a missing field. Other items flagged as gaps
> may likewise already exist in the template. Worth checking this list against the actual Covidence
> codebook before acting on any of it.

### Supplementary

**S1 — Reliability of the review process.** ✅ Per-reviewer rows can be exported from Covidence
*after* consensus as well as before, so nothing here is time-limited: the database uses the
consensus export, and the independent extractions are pulled separately for agreement. That also
means the supplement need not stop at extraction — **agreement is measurable at all three stages
of the review**, which turns a defensive methods note into a genuine contribution. Very few
reviews report reliability at more than one stage, and almost none do so for a *living* review
that will repeat the process as new reviewers join.

- **S1a — title/abstract screening.** Two independent include/exclude decisions per record across
  the ~4,770 screened. Report Cohen's κ **with raw percentage agreement**: screening is heavily
  prevalence-imbalanced (most records are excluded) and κ is deflated by exactly that imbalance,
  so κ alone understates agreement. PABAK or a prevalence-adjusted figure alongside it is the
  honest presentation.
- **S1b — full-text review.** κ on the include/exclude decision, plus a second and more
  informative statistic: agreement on the **exclusion reason** among records both reviewers
  excluded. Two reviewers can agree to exclude for different reasons, and a decision-only κ hides
  that entirely.
- **S1c — extraction.** Per field, because the fields are different kinds of measurement: κ for
  categorical fields (phase, population, comparator), set overlap (Jaccard) for the multi-select
  outcome domains, exact agreement or ICC for the numeric fields.

*What still has to be pulled:* **none of the five exports currently in `data/` carries screening
decisions.** `screen`, `select`, `included` and `excluded` are bibliographic record lists with no
reviewer column at all; only the extraction export has `Reviewer Name`. S1a and S1b therefore need
an additional Covidence export type — per-reviewer screening decisions — not a re-parse of what we
already hold.

*Compute on a frozen snapshot:* agreement measured mid-extraction is meaningless, since a
"disagreement" is usually one reviewer not having reached a field the other has. Restrict each
statistic to records both reviewers have actually completed.

**S2 — Registry vs publication discrepancies.** Richer than "the registry disagrees with the
paper" — the pilot's five mismatches have **three distinct causes**, and none of them is an error:

| Trial | Registry | Paper | What it actually is |
|---|---|---|---|
| NCT03790358 | 80 enrolled; arms are **MDMA** dose levels | Bershad 2019 & 2020, **LSD** microdoses, n=20 each | **Umbrella registration.** One NCT covering a programme of serotonin-agonist studies; the registry record describes a different substudy's intervention entirely. Not a subgroup analysis. |
| NCT04648137 | 30 enrolled; arms are *patients with central diabetes insipidus* / *healthy volunteers* | Atila 2025, n=15 analysed | **Genuine subgroup** — a secondary analysis reporting the healthy-volunteer half. |
| NCT04865653 | 20 "actual" | Arikci 2025: 24 randomised, 20 analysed | Registry's *actual enrolment* equals the paper's **analysed** count. |
| NCT04558294 | 24 "actual" | Becker 2023: 26 randomised, 24 analysed | Same pattern. |

Across the four trials where we hold both numbers, registry "actual enrolment" matched N analysed
three times and N randomised twice (one matched both). So the registry figure is **not reliably
either quantity** — which is the reportable finding: an enrolment discrepancy is not evidence of
error until you establish which quantity each source is reporting.

> **This also qualifies Figure 4.** Grouping papers by registration treats an umbrella
> registration as a single trial even when it covers several distinct experiments — Bershad 2019
> (four-session dose-ranging) and Bershad 2020 (two-session fMRI) are different experiments under
> one NCT. So the papers-per-trial ratio *over*-merges in umbrella cases while unregistered
> reports without a parent DOI stay *under*-merged. Report it as "papers per registration", not
> "papers per experiment", and note both directions of error.

---

## 3. Tables

| Table | Content | Feasible |
|---|---|---|
| **T1** | Characteristics of included trials: drug, population, N, phase, comparator, country, registration | ⚠️ (country/design registry-only) |
| **T2** | Outcome domains and the sub-categories recorded within each | ✅ |
| **T3** | Evidence gaps: drug × indication cells with zero or one trial | ✅ |
| **S-T1** | Full study list with identifiers (the exported database) | ✅ |

---

## 4. Analyses beyond the figures

1. **Trial-level vs paper-level counts** for every headline statistic, reported as a pair. The gap
   between the two *is* a result.
2. **Concentration analysis — by senior-author group, not by centre.** The original framing needed
   institutional affiliations, which the Covidence export does not carry; country comes only from
   the registry and only for registered trials, so it cannot carry this. **Author names, however,
   are present for all 95 papers.** Last-author concentration is computable today: 56 distinct
   last authors, with the top five accounting for **29% of all papers** (Liechti 6, Vollenweider
   6, Nutt 6, Borgwardt 5, de Wit 5). Registry lead sponsors add an organisational view for
   enriched trials (University Hospital Basel alone sponsors 6 of 18).
   *Caveat to state in the methods:* last author is a proxy for research group, and it will
   mis-handle name collisions and shared senior authorship. Report it as a bibliometric
   description, not a precise count of laboratories.
3. **Unpublished trials — feasible, but it is a separate piece of work.** Parker is right that our
   registry ids come *from* papers, so this cannot be answered from the database alone. It needs a
   query in the other direction: search ClinicalTrials.gov directly for completed interventional
   trials with a psychedelic intervention, then subtract the NCT ids that appear in our database.
   The remainder are candidate unpublished trials, and no extraction work is involved.
   *Real caveats:* while screening is incomplete a "missing" trial may simply be unscreened, so
   this must wait until the review is closed; trials in non-CT.gov registries are invisible to it;
   and a trial may be published somewhere we have not indexed. It would be a genuinely new number
   for the field — but it is an added task, not a free one.
4. ~~Outcome-domain coverage vs regulatory expectation~~ — **cut.** It was under-specified: it
   needs a normative standard for what a phase 3 programme must establish, which we would be
   asserting rather than measuring. A purely descriptive version (outcome domains cross-tabulated
   by phase) is computable, but the pilot's phase distribution is 23 phase 1 to 1 phase 2 and 2
   phase 3, and phase is recorded only for registered trials — too thin to carry a figure. Worth
   revisiting only if phase coverage improves substantially.

---

## 4a. Gap 3, specified — the design and blinding options

Derived from what ClinicalTrials.gov actually encodes across our 18 enriched trials, so extracted
values stay directly comparable with the registry for trials that have one.

### Design — nearly right, and one thing *not* to add

Parallel vs crossover covers 17 of 18 (10 parallel, 7 crossover), and crossover being that common
is itself worth capturing. Factorial is worth having given how many psychedelic studies add a
pre-treatment or co-administered drug.

**Do not offer "single-group".** Our one single-group trial turned out to be a registration error
(below), and in a database restricted to randomised trials a genuine single-group design should
not exist. A reviewer reaching for it is really asking whether the study belongs in the review —
a screening decision, not an extraction option.

**Proposed:** `parallel` · `crossover` (incl. within-subject) · `factorial` · `quasi-randomised` ·
`other` · `not reported`.

#### The one "single-group" trial is a mislabelled crossover

[NCT00823407](https://clinicaltrials.gov/study/NCT00823407) — *Clinical Pharmacology of MDA*
(Baggott 2010, n=12) — registers `allocation: RANDOMIZED` together with
`interventionModel: SINGLE_GROUP`, which contradicts itself: a single group has nothing to
randomise between. The giveaway is in the arms. There is **one** arm group, labelled "MDA", and it
lists **two** interventions — `Drug: MDA` and `Drug: Placebo` — both double-masked to participant
and care provider. Every participant receives both. That is a crossover.

The cause is a registration habit rather than a typo: some registrants put every intervention
inside a single arm group. [NCT01951508](https://clinicaltrials.gov/study/NCT01951508) has exactly
the same shape — one arm holding methylphenidate, modafinil, MDMA and placebo — but is correctly
labelled `CROSSOVER`. Same structure, two different labels.

So the reliable signal is **structural, not the label: one arm group containing several drug
interventions is a crossover**, whatever the model field says. `_registry_qc()` now checks for
this and warns; it also caught NCT01951508's missing `allocation` field.

### Blinding — the three-option list has a real problem

"Single / double / open-label" is the classic vocabulary, but it is **not** what CT.gov records,
and the mismatch is not cosmetic. The registry counts **how many parties are masked** and
separately records **which**. Those come apart in our own data:

| Registry level | Who was actually masked | Trials |
|---|---|---|
| Double | participant, investigator | 3 |
| Double | participant, *care provider* | 1 |
| Triple | participant, care provider, investigator | 5 |
| Triple | participant, investigator, outcomes assessor | 3 |
| Triple | participant, care provider, outcomes assessor | 1 |
| Quadruple | all four roles | 3 |
| Single | participant only | 1 |
| Single | *outcomes assessor only* | 1 |

Read the last two rows together. Both are "single-blind", but in one the participant does not know
what they took and in the other **they do** — only the rater is masked. For a psychedelic trial
that is close to the most important distinction available, and the classic label erases it.
"Double-blind" is no better: participant + investigator three times out of four here, participant
+ care provider the fourth.

**Proposed: record *who* was masked, and derive the level.** A multi-select —
`participant` · `care provider (therapist / session monitor)` · `investigator` ·
`outcomes assessor` — plus two mutually exclusive values, `nobody (open-label)` and
`not reported`.

It costs the same to fill as three radio buttons, it is what a methods section actually states, it
is identical to the registry's own vocabulary so registered and unregistered trials stay
comparable, and single/double/triple/quadruple can still be **derived by counting** — the classic
label without the information loss.

The **care provider** role earns its place specifically: in psychedelic-assisted therapy the
session monitor is the person least likely to be genuinely blind whatever the protocol claims, and
the registry records them as masked in 10 of our 18 trials. Capturing the role explicitly is what
lets Figure 11A ask whether that claim was ever tested.

**Allocation is not worth a field.** 17 of 18 are registered randomised and the database is RCTs
by definition. The one value worth having is `quasi-randomised` (alternation, day of week), which
does appear in mid-century trials — fold it into the design list rather than adding a column.

---

## 4b. Registered but not on ClinicalTrials.gov — what can be done

Only ClinicalTrials.gov has an adapter today; everything else renders as
`unsupported_registry`. Tested against the registries that actually appear in the corpus:

| Registry | Programmatic access | Verdict |
|---|---|---|
| **ClinicalTrials.gov** (NCT) | API v2 | Already implemented; 18 trials enriched |
| **ISRCTN** | ✅ **Public XML API works**, including `?format=who` — returns the full WHO Trial Registration Data Set (68 fields: `study_design`, `phase`, `primary_sponsor`, `countries`, `target_size`, `results_actual_enrolment`, `date_registration`, `date_enrolment`, outcomes, status) | **The one worth building.** See below. |
| **ANZCTR** (ACTRN) | ❌ HTTP 403 to scripted requests (bot protection) | Link only |
| **Dutch CCMO / OMON** | ❌ no API; HTML record resolves | Link only |
| **NTR** (old Dutch) | ❌ trialregister.nl is dead — retired 2022, records migrated | Link via ICTRP |
| **EU CTIS** | ❌ public API requires an auth token | Link only |
| **EU CTR** (EudraCT) | ❌ HTML search only | Link only |
| **WHO ICTRP** | ⚠️ no REST API (`GetTrialByID` 404); weekly bulk XML by request form | Universal *link* target; bulk XML is the long-term generic path |

**Done now — every registry id is at least linked.** Previously a non-NCT trial rendered with *no
link at all*, which was the worst outcome: a dead end rather than a one-click lookup.
`_registry_url()` now builds verified URLs for ISRCTN, ANZCTR, Dutch OMON, and DRKS, and falls
back to the WHO ICTRP search portal (`trialsearch.who.int/?TrialID=…`) for any other recognized
id. All patterns were checked against live records. One subtlety handled: Dutch cells list the
ABR/CCMO number first (`NL70508.068.1; NL-OMON55178`) but only the **OMON** id resolves.

**The one adapter worth writing, when it earns its place.** ISRCTN's `format=who` returns the
*WHO* dataset, not an ISRCTN-specific schema — so a `_parse_who()` written once would also read
ICTRP bulk XML and any other registry exposing that format. It maps onto most of our `details`
schema, including prospective-vs-retrospective registration (`date_registration` vs
`date_enrolment`) and planned-vs-actual enrolment (`target_size` vs `results_actual_enrolment`).
Two differences from CT.gov to handle: `study_design` is semi-structured text
(`"Allocation: Randomized controlled trial; Masking: Blinded (masking used); …"`) rather than
enums, and dates are `DD/MM/YYYY`.
*Not built yet, deliberately:* **the corpus currently contains zero ISRCTN trials.** Worth doing
when one appears, or once the corpus is complete enough to know how many non-NCT trials there
really are — a few hours' work, not a research project.

---

## 5. What is still blocked, after review

Four items, none of which is a new extraction column. Everything else was judged out of scope and
the figures above have been adjusted accordingly. **Expectancy was removed from this list** — it
is already a template option, simply never used (see Figure 11D).

| # | Field | Unblocks | Cost | Status |
|---|---|---|---|---|
| 1 | **Microdosing flag** (restore the removed yes/no) | The microdose vs full-dose split in Figures 3, 5, 6, and what remains of 9 | Very low | Parker open to it |
| 2 | **A "not reported" option on *both* `N randomized` and `N analyzed`** | Figure 6's attrition panel. Either field being blank makes attrition undeterminable, and N randomized is already missing on 18% of rows — so one option on one field isn't enough | Very low | Proposed |
| 3 | **Design + blinding, asked only when `Trial Phase = Unregistered`** — vocabulary specified below | Figure 7 for the ~half of the corpus the registry cannot describe | Low | Vocabulary drafted |
| 4 | **Age (mean/range) and % female** | A demographic panel in Figure 8 | Low | Optional — "could be persuaded" |

**The structural insight that still stands.** ClinicalTrials.gov already supplies design, masking,
allocation, sponsor and industry status, country, planned enrolment, primary outcomes,
registration date, and results-posted — at 100% field coverage for enriched trials. Extraction
effort should never be spent re-collecting these for registered trials. Gap #3 follows directly
from this: ask the design questions *only* of unregistered studies, where the registry cannot
answer them.

---

## 6. Sequencing

1. **Now** — `prisma_manual.json` is filled and reconciles. Decide on gaps #1–#2 (both very low
   cost) and add them to the Covidence template *before* the bulk of extraction runs, so they
   never require a retrospective pass over hundreds of studies.
2. **During extraction** — run consensus, then flip `CONSENSUS_REVIEWER` to `None`; build Figures
   2, 3, 4, 5 on the growing set as a running check that the schema holds up.
3. **At completion** — freeze a versioned database release (Zenodo DOI, see *Future directions* in
   `CLAUDE.md`), then write against the frozen version so every number in the paper is reproducible
   from a citable artefact.
