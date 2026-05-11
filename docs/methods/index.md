---
title: "Meta-Analytic Models: A Practical Explainer"
excerpt: "Brief explanations of each argument used in the SYPRES meta-analytic models."
layout: single
toc: true
toc_sticky: true
---

This page is a short, practical reference for the meta-analytic models we run in
the SYPRES living reviews. For each model type, we show the example code block
used in our analyses (see [`analysis/`](https://github.com/PennLINC/sypres-docs/tree/main/analysis))
and walk through every argument and the reasoning behind it.

Most models are fit with the
[`runMetaAnalysis()`](https://tools.metapsy.org/articles/metapsytools.html#runmetaanalysis)
wrapper from [`metapsyTools`](https://tools.metapsy.org/), which is itself a
convenience layer on top of [`{meta}`](https://cran.r-project.org/package=meta)
and [`{metafor}`](https://www.metafor-project.org/). For the broader theory and
worked examples behind these choices, we recommend
[*Doing Meta-Analysis with R*](https://doing-meta.guide) (Harrer, Cuijpers,
Furukawa & Ebert).

---

## 1. Continuous outcomes (random-effects)

The primary efficacy model. Used to pool standardized mean differences (e.g.,
psilocybin vs. control on a depression rating scale) across studies.

```r
main_results <- runMetaAnalysis(data_main,

  # Specify models to run
  which.run       = c("overall", "outliers"),
  which.influence = "overall",
  which.outliers  = "overall",

  # Specify statistical parameters
  es.measure    = "g",         # Hedges' g
  method.tau    = "REML",
  method.tau.ci = "Q-Profile",
  hakn          = TRUE,        # Knapp-Hartung adjustment

  # Specify variables
  study.var   = "study",
  arm.var.1   = "condition_arm1",
  arm.var.2   = "condition_arm2",
  measure.var = "instrument",
  w1.var      = "n_arm1",
  w2.var      = "n_arm2",
  time.var    = "time_weeks",
  round.digits = 2
)
```

**Argument-by-argument:**

- `which.run = c("overall", "outliers")` — fits the main random-effects model
  *and* a sensitivity model with statistical outliers removed. `which.influence`
  / `which.outliers` tell `metapsyTools` which fitted model to base influence
  diagnostics and outlier detection on.
- `es.measure = "g"` — **Hedges' *g***, a standardized mean difference with
  a small-sample bias correction. Standard choice when studies use different
  rating scales. See
  [Doing Meta-Analysis ch. 3.4.1 (Effect Sizes - Small Sample Bias)](https://doing-meta.guide/effects).
- `method.tau = "REML"` — restricted maximum likelihood for the
  between-study variance τ². REML is the default estimator for between-study variance in metaPsyTools;
  it gives less biased and more reliable estimates of τ² in a wide range of conditions, and
  is performs well with a small amount of studies, especially when combined with the Knapp-Hartung Sidik-Jonkman adjustment
  for inference described below.
  For more information, see [here](https://doing-meta.guide/pooling-es), [here](https://doi.org/10.1002/jrsm.1316), and [here](https://doi.org/10.1002/jrsm.1164).
- `method.tau.ci = "Q-Profile"` — Q-profile method for the confidence
  interval around τ²/I². This method also holds up well when there are only few trials in a meta-analysis and when heterogeneity is moderate to large, since it does not rely on large-sample normal approximations.
  This is the default and recommended method in [metapsyTools](https://tools.metapsy.org/reference/runmetaanalysis).
  See also ["Confidence intervals for the amount of heterogeneity in meta-analysis"](https://doi.org/10.1002/sim.2514).
- `hakn = TRUE` — Knapp–Hartung–Sidik–Jonkman adjustment to the
  standard error of the pooled effect. Produces wider, more conservative
  confidence intervals that are better calibrated when *k* is small; most robust to changes
  in the heterogeneity variance estimate.
  See [Doing Meta-Analysis ch. 4.1.2.2 (Pooling Effect Sizes - Knapp-Hartung Adjustments)](https://doing-meta.guide/pooling-es).
- `study.var`, `arm.var.1`, `arm.var.2`, `measure.var`, `w1.var`, `w2.var`,
  `time.var` — column names that point `runMetaAnalysis()` at study labels,
  the two arms being contrasted, the outcome instrument, the per-arm sample
  sizes, and the timepoint variable. These follow the
  [Metapsy data standard](https://docs.metapsy.org/data-preparation/format/).
- `round.digits = 2` — display rounding only.

> **Why these defaults?** In addition to the justifications provided above,
> Hedges' *g* + REML + Knapp–Hartung is the
> recommended combination in the [`metapsyTools` documentation](https://tools.metapsy.org/articles/metapsytools.html), and is also reflected in the current peer-reviewed literature, e.g. [here](https://onlinelibrary.wiley.com/doi/full/10.1002/jrsm.1356), [here](https://onlinelibrary.wiley.com/doi/full/10.1002/sim.7411), and [here](https://link.springer.com/article/10.1186/1471-2288-14-25?report=reader).

---

## 2. Dichotomous outcomes (response/remission)

Used for binary clinical outcomes such as **response** (defined per study as a threshold (i.e.,≥50%) in symptom reduction)
or **remission** (score below a clinical threshold to meet diagnostic criteria).

```r
response_results <- runMetaAnalysis(data_response,
  which.run     = "overall",
  es.measure    = "RR",        # risk ratio
  es.type       = "raw",
  method.tau    = "PM",
  method.tau.ci = "Q-Profile",
  hakn          = TRUE,        # Knapp-Hartung adjustment

  # Specify variables
  study.var   = "study",
  arm.var.1   = "condition_arm1",
  arm.var.2   = "condition_arm2",
  measure.var = "instrument",
  w1.var      = "n_arm1",
  w2.var      = "n_arm2",
  time.var    = "time_weeks",
  round.digits = 2
)
```

**What changes vs. the continuous model:**

- `es.measure = "RR"` — **risk ratio** (intervention events ÷ control events).
  RR is more easily interpretable than odds ratios, and odds ratios are sometimes mistakenly interpreted as RRs, so RRs are
  generally preferable in clinical meta-analyses.
  See [Doing Meta-Analysis ch. 3.3.2.1 (Effect Sizes - Risk Ratio)](https://doing-meta.guide/effects).
- `es.type = "raw"` — tells `metapsyTools` the input columns are raw event
  counts (`event_arm1`, `totaln_arm1`, …) rather than precomputed effect sizes.
- `method.tau = "PM"` — **Paule–Mandel** estimator for τ². Recommended for
  binary outcomes (Veroniki et al. 2016) where REML can be biased.
  For more information, see [here](https://doing-meta.guide/pooling-es), [here](https://doi.org/10.1002/jrsm.1316), and [here](https://doi.org/10.1002/jrsm.1164), [here](https://doi.org/10.1002/jrsm.1316), and [here](https://doi.org/10.1002/jrsm.1164).
- `method.tau.ci`, `hakn` — same rationale as the continuous model.
- The variable mapping is identical to the continuous case; `runMetaAnalysis()`
  picks up the event/total columns automatically based on `es.type = "raw"`.

---

## 3. Three-level (CHE) models

Used when a study contributes **multiple effect sizes** — typically several
post-treatment timepoints from the same trial. A standard random-effects
model assumes effect sizes are independent; ignoring within-study dependence
underestimates standard errors. The **correlated and hierarchical effects
(CHE)** model of Pustejovsky & Tipton (2021) handles both sources of
non-independence.

```r
time_results <- runMetaAnalysis(data_time,
  which.run     = "threelevel.che",

  # Specify statistical parameters
  es.measure    = "g",
  method.tau    = "REML",
  method.tau.ci = "Q-Profile",   # N/A for three-level models
  hakn          = TRUE,

  # Specify variables
  study.var   = "study",
  arm.var.1   = "condition_arm1",
  arm.var.2   = "condition_arm2",
  measure.var = "instrument",
  w1.var      = "n_arm1",
  w2.var      = "n_arm2",
  time.var    = "time_days",
  round.digits = 2
)
```

**What's different here:**

- `which.run = "threelevel.che"` — fits the three-level CHE model via
  `{metafor}`'s `rma.mv()` with cluster-robust ("RVE") inference. Effect sizes
  are nested within studies, with two heterogeneity components: within-study
  (level 2) and between-study (level 3). See
  [Doing Meta-Analysis ch. 10 ("Multilevel" Meta-Analysis)](https://doing-meta.guide/multilevel-ma).
- `time.var = "time_days"` — the variable that distinguishes effect sizes
  *within* the same study. Each timepoint becomes a separate row in the
  long-format input.
- `method.tau.ci = "Q-Profile"` is **ignored** for multilevel models (we
  leave it for symmetry with other calls; the inline comment flags this).
  Heterogeneity CIs for three-level models require parametric bootstrapping
  (`i2.ci.boot = TRUE`), which we run separately when needed.
- `hakn = TRUE` — when combined with `rma.mv()`, this triggers the
  small-sample (Tipton-Pustejovsky) adjustment to the cluster-robust standard
  errors.
- An additional argument `rho.within.study` (default `0.6`) sets the
  assumed correlation between effect sizes within a study. Because the true
  ρ is rarely known, we **sweep it from 0 → 1** as a sensitivity check; see
  the rho-sweep block in the analysis Rmd files.

> **When to use this instead of the standard model:** any time you have more
> than one effect size per study (multiple timepoints, multiple outcomes,
> multi-arm trials with shared controls). Don't average them away — let the
> three-level model use all the data.

---

## 4. Meta-regression

Adds a **moderator** to a fitted meta-analytic model to test whether the
pooled effect varies as a function of a study- or effect-level covariate
(e.g., time since dosing, cumulative dose, % female).

```r
reg <- metaRegression(time_results$model.threelevel.che, ~time_days)
reg
```

**Argument-by-argument:**

- First argument — a **fitted model object** from `runMetaAnalysis()`. We
  almost always regress on top of the three-level CHE model so that
  within-study dependence is correctly handled.
- `~time_days` — a one-sided R formula listing the moderator(s). Use `+` to
  add multiple moderators (`~time_days + diagnosis`) or `*` for interactions.
  Categorical moderators are dummy-coded automatically.

`metaRegression()` is a thin wrapper around `metafor::rma.mv()`'s `mods=`
argument that preserves the parent model's τ² estimator, RVE settings, and
Knapp–Hartung adjustment, so the moderator test inherits the same inference
machinery as the parent model. See
[Doing Meta-Analysis ch. 8 (Meta-Regression)](https://doing-meta.guide/metareg) and
the [`metafor` meta-regression docs](https://cran.r-project.org/web/packages/metafor/metafor.pdf).

**Tips:**

- Don't run a separate meta-regression on top of an `overall` model when you
  have multiple effect sizes per study — fit it on the three-level model
  instead.
- Plot the result with `regplot(reg, mod = "time_days")` to visualize the
  moderator slope and study-weighted points.
- For categorical moderators, the omnibus test (`QM`) tells you whether the
  moderator explains a significant share of heterogeneity overall; individual
  coefficients give you the contrast against the reference level.

---

## Where to go next

- [`metapsyTools` reference manual](https://tools.metapsy.org/) — function-by-function docs for every argument used above.
- [*Doing Meta-Analysis with R*](https://doing-meta.guide) — the textbook the SYPRES models are built around.
- [Metapsy data format](https://docs.metapsy.org/data-preparation/format/) — what `study.var`, `arm.var.*`, etc. expect to find in your input data.
- [`metafor` project site](https://www.metafor-project.org/) — for the underlying estimators (`rma`, `rma.mv`) and diagnostic tools.
- Worked examples in this repo corresponding to our meta-analytic studies:
  [Psilocybin for Depression Rmd](https://github.com/PennLINC/sypres-docs/blob/main/analysis/psilodep/psilodep-meta-analysis.Rmd)
  · [MDMA for PTSD Rmd](https://github.com/PennLINC/sypres-docs/blob/main/analysis/mdmaptsd/mdmaptsd-meta-analysis.Rmd).
