---
layout: single
title: "Meta-analysis on Psilocybin for Depression"
output:
  md_document:
    variant: markdown_github
    preserve_yaml: true
---

This document provides a comprehensive walk-through of the meta-analysis
investigating the efficacy of psilocybin for treating depression
symptoms, using data extracted for the SYPRES project. The analysis
includes both continuous (depression symptom severity scores) and
dichotomous (response/remission rates) outcomes, along with extensive
subgroup and sensitivity analyses.

Full source code is available
[here](https://github.com/pennlinc/sypres-docs/blob/main/analysis/psilodep/psilodep-meta-analysis.Rmd).

## Overview

This meta-analysis synthesizes evidence from randomized controlled
trials examining the efficacy of psilocybin for treating depression. The
analysis employs meta-analytic methods to provide robust estimates of
treatment effects while accounting for study heterogeneity and potential
biases.

### Key Features of This Analysis

-   **Comprehensive outcome assessment**: Both continuous (depression
    symptom severity) and dichotomous (response/remission) outcomes
-   **Time course analysis**: Three-level hierarchical models to examine
    treatment effects over time
-   **Robustness testing**: Extensive sensitivity and subgroup analyses
-   **Publication bias assessment**: Multiple methods to evaluate
    potential bias
-   **Transparent reporting**: Complete code and methodology
    documentation

## Methods

### Statistical Approach for Primary Meta-Analysis

For our primary meta-analysis, we employ random-effects meta-analysis
using the Restricted Maximum Likelihood (REML) estimator for
between-study variance. For continuous outcomes, we calculate Hedges’ g
(standardized mean difference) as the effect size measure. For
dichotomous outcomes, we use log risk ratios (RR).

**Key statistical specifications:** - **Effect size**: Hedges’ g for
continuous outcomes, log RR for dichotomous outcomes - **Heterogeneity
estimator**: REML for random-effects models - **Confidence intervals**:
Q-Profile method for heterogeneity, Knapp-Hartung adjustment for effect
sizes - **Significance testing**: Knapp-Hartung adjustment for small
sample sizes

### Quality Assessment

We conduct sensitivity analyses excluding studies with high risk of bias
evaluated using the Cochrane Risk of Bias tool Publication bias is
evaluated using funnel plots and Egger’s test.

### Load Required Packages

We begin by loading the necessary R packages for data manipulation,
meta-analysis, and visualization:

-   **Data manipulation**: `readr` and `tidyverse` for data loading and
    manipulation
-   **Meta-analysis**: `meta` and `metafor` for conducting meta-analytic
    calculations
-   **Effect sizes**: `esc` for effect size calculation utilities
-   **Specialized tools**: `metapsyTools` for specific meta-analysis
    functions and `dmetar` for additional meta-analysis tools

``` r
library(readr)
library(tidyverse)
library(meta)
library(metafor)
library(esc)
library(metapsyTools)
library(dmetar)
library(gt)
```

### Data Loading and Quality Checks

The raw data is loaded from a CSV file containing information extracted
from multiple studies. Before proceeding with the analysis, we perform
quality checks to ensure data integrity and identify potential issues.

``` r
# Load data
#data <- read_csv("/Users/sps253/Documents/GIT/data-depression-psiloctr/data.csv")
data <- read_csv("/Users/bsevchik/Documents/GitHub/metapsy_psilodep/data.csv")
# after release we will replace this with metapsyData load function

# Check data format with checkDataFormat
checkDataFormat(data)

# Check conflicts with checkConflicts
checkConflicts(data)
```

### Data Preparation and Filtering

We prepare the data for analysis by applying several filters to create
our primary analysis dataset:

1.  **Primary outcomes**: Select only the primary instrument and
    timepoint for each study
2.  **Study design**: Exclude post-crossover data to avoid
    double-counting
3.  **Outcome type**: Include only endpoint data (mean/SD or imputed
    mean/SD)
4.  **Dosing**: Exclude medium-dose arm (10 mg psilocybin) from
    multi-arm study (Goodwin 2022)
5.  **Study exclusions**: Remove specific studies (Krempien 2023,
    Carhart-Harris 2021) based on predefined criteria

The resulting `data_main` dataframe contains the filtered data ready for
our primary meta-analysis.

``` r
data_main <- data %>%
  filterPoolingData(
    primary_instrument == "1",
    primary_timepoint == "1",
    is.na(post_crossover) | !Detect(post_crossover,"1"),
    outcome_type == "msd" | outcome_type == "imsd",
    !(Detect(study, "Goodwin 2022") & (!is.na(multi_arm1)) & Detect(multi_arm1, "10 mg")),
    !(Detect(study, "Goodwin 2022") & (!is.na(multi_arm2)) & Detect(multi_arm2, "10 mg")),
    !Detect(study, "Krempien 2023"),
    !Detect(study, "Carhart-Harris 2021")
  )
```

## Results

### Primary Meta-Analysis

We conduct the main meta-analysis using the `runMetaAnalysis` function
from `metapsyTools`. This analysis pools all studies in our filtered
dataset to estimate the overall effect of psilocybin on depression
severity.

**Key specifications:** - **Effect size**: Hedges’ g (standardized mean
difference) - **Model**: Random-effects meta-analysis using REML
estimator - **Adjustments**: Knapp-Hartung adjustment for significance
tests - **Additional analyses**: Outlier detection and influence
analysis

The results include the pooled effect size, confidence intervals,
heterogeneity statistics, and the meta-analysis model object.

``` r
main_results <- runMetaAnalysis(data_main,

  # Specify models to run
  which.run = c("overall", "outliers"),
  which.influence = "overall",
  which.outliers = "overall",

  # Specify statistical parameters
  es.measure = "g", # uses .g column in data_es and .g_se (Hedges' g/bias-corrected SMD)
  method.tau = "REML", # default, but still including for clarity
  method.tau.ci = "Q-Profile", # not sure if this will work!
  hakn = TRUE, # Knapp-Hartung effect size significance tests be used

  # Specify variables
  study.var = "study",
  arm.var.1 = "condition_arm1",
  arm.var.2 = "condition_arm2",
  measure.var = "instrument",
  w1.var = "n_arm1",
  w2.var = "n_arm2",
  time.var = "time_weeks",
  round.digits = 2 # can change to change number of digits to round the presented results to
)

summary(main_results$model.overall)
```

    ##                      g             95%-CI %W(random)
    ## Back 2024      -1.4215 [-2.2271; -0.6160]        7.9
    ## Davis 2021     -2.4807 [-3.5637; -1.3976]        5.0
    ## Goodwin 2022   -0.6875 [-1.0085; -0.3665]       19.8
    ## Griffiths 2016 -1.2731 [-1.8827; -0.6635]       11.4
    ## Raison 2023    -0.8700 [-1.2941; -0.4459]       16.3
    ## Rieser 2025    -0.3806 [-1.0314;  0.2701]       10.5
    ## Rosenblat 2024 -0.4932 [-1.2218;  0.2355]        9.1
    ## Ross 2016      -0.7940 [-1.5967;  0.0086]        7.9
    ## vonRotz 2023   -0.9384 [-1.5120; -0.3648]       12.2
    ## 
    ## Number of studies: k = 9
    ## 
    ##                                 g             95%-CI     t p-value
    ## Random effects model (HK) -0.9205 [-1.2987; -0.5423] -5.61  0.0005
    ## Prediction interval               [-1.5967; -0.2442]              
    ## 
    ## Quantifying heterogeneity (with 95%-CIs):
    ##  tau^2 = 0.0674 [0.0000; 1.2489]; tau = 0.2596 [0.0000; 1.1175]
    ##  I^2 = 51.5% [0.0%; 77.3%]; H = 1.44 [1.00; 2.10]
    ## 
    ## Test of heterogeneity:
    ##      Q d.f. p-value
    ##  16.50    8  0.0358
    ## 
    ## Details of meta-analysis methods:
    ## - Inverse variance method
    ## - Restricted maximum-likelihood estimator for tau^2
    ## - Q-Profile method for confidence interval of tau^2 and tau
    ## - Calculation of I^2 based on Q
    ## - Hartung-Knapp adjustment for random effects model (df = 8)
    ## - Prediction interval based on t-distribution (df = 8)

``` r
# Create simple forest plot of results

meta::forest(
  main_results$model.overall,
  sortvar = main_results$model.overall$data$year,
  layout = "JAMA"
)
```

![](/analysis/psilodep/knitfigs/primary-meta-analysis-1.png)

The primary meta-analysis on continuous outcomes in the 9 studies
included in the main model showed a statistically significant reduction
in depression scores with psilocybin treatment as compared to control
conditions, with small to moderate between-study heterogeneity.

### Publication Bias Assessment

We assess potential publication bias using both visual (funnel plot) and
statistical (Egger’s test) methods.

``` r
# Run Egger's test

eggers.test(main_results$model.overall)
```

    ## Warning in eggers.test(main_results$model.overall): Your meta-analysis contains k = 9 studies. Egger's test
    ## may lack the statistical power to detect bias when the number of studies is small (i.e., k<10).

    ## Eggers' test of the intercept 
    ## ============================= 
    ## 
    ##  intercept       95% CI     t         p
    ##     -2.024 -4.46 - 0.41 -1.63 0.1472072
    ## 
    ## Eggers' test does not indicate the presence of funnel plot asymmetry.

``` r
png(filename = file.path(basedir,"analysis/psilodep/paperfigs/SI_Fig_01.png"), res=315, width=2500, height=1500)
funnel(main_results$model.overall,
       studlab = TRUE, #can also use vector with study labels
       cex.studlab = 0.7, #adjust size of study labels
       cex = 0.7,         #axis tick labels and point size
       cex.axis = 0.7,    #axis number label size
       cex.lab = 0.7,     #axis title (xlab, ylab) size
       cex.main = 0.95,    #main title size
       xlim = c(-3,0.2),
       col = "steelblue",
       pch = 19, #bold solid circle
       bg = "white",
       xlab = "Standardized Mean Difference (SMD)",
       ylab = "Standard Error (SE)",
       main = "Funnel Plot of Main Model Continuous Outcomes",
       las = 1
       )
dev.off()
```

![](/analysis/psilodep/paperfigs/SI_Fig_01.png) Visual inspection of the
funnel plot reveals limited asymmetry, and the Egger’s test did not find
small study effects, implying minimal evidence of publication bias.

### Three-level hierarchical effects (CHE) meta-analysis

We conduct a three-level correlated and hierarchical effects (CHE)
meta-analysis to examine how the effect of psilocybin changes over time.
This approach accounts for the hierarchical structure of the data
(multiple timepoints within studies) and potential correlations between
timepoints.

``` r
# Select data for the CHE meta-analysis

data_time <- data %>%
  calculateEffectSizes() %>%
  filter(
    is.na(multi_arm1) | !str_detect(multi_arm1, "10 mg"),
    is.na(multi_arm2) | !str_detect(multi_arm2, "10 mg"),
    !str_detect(study, "Krempien 2023"),
    !str_detect(study, "Carhart-Harris 2021")
  ) %>%
  filterPoolingData(
    primary_instrument == "1",
    time_days > 0,
    post_crossover == 0 | is.na(post_crossover),
    outcome_type == "msd" | outcome_type == "imsd"
  )

# Run meta-analysis

time_results <- runMetaAnalysis(data_time,

  which.run = "threelevel.che",
  # Specify statistical parameters
  es.measure = "g", # uses .g column in data and .g_se, referring to Hedges' g
  method.tau = "REML", 
  method.tau.ci = "Q-Profile", 
  hakn = TRUE, # Knapp-Hartung effect size significance tests used

  # Specify variables
  study.var = "study",
  arm.var.1 = "condition_arm1",
  arm.var.2 = "condition_arm2",
  measure.var = "instrument",
  w1.var = "n_arm1",
  w2.var = "n_arm2",
  time.var = "time_days",
  round.digits = 2 
)

time_results$model.threelevel.che
```

    ## 
    ## Multivariate Meta-Analysis Model (k = 30; method: REML)
    ## 
    ## Variance Components:
    ## 
    ##             estim    sqrt  nlvls  fixed       factor 
    ## sigma^2.1  0.1399  0.3740      9     no        study 
    ## sigma^2.2  0.0378  0.1944     30     no  study/es.id 
    ## 
    ## Test for Heterogeneity:
    ## Q(df = 29) = 78.0275, p-val < .0001
    ## 
    ## Model Results:
    ## 
    ## estimate      se     tval  df    pval    ci.lb    ci.ub      
    ##  -0.8993  0.1630  -5.5168  29  <.0001  -1.2327  -0.5659  *** 
    ## 
    ## ---
    ## Signif. codes:  0 '***' 0.001 '**' 0.01 '*' 0.05 '.' 0.1 ' ' 1

The three-level CHE model reveals an overall significant decrease in
depression scores under psilocybin compared to control conditions.

#### Meta-Regression

We perform meta-regression to examine the relationship between time
since final dose and treatment effect.

``` r
reg <- metaRegression(time_results$model.threelevel.che, ~ time_days)
reg
```

    ## 
    ## Multivariate Meta-Analysis Model (k = 30; method: REML)
    ## 
    ## Variance Components:
    ## 
    ##             estim    sqrt  nlvls  fixed       factor 
    ## sigma^2.1  0.1327  0.3642      9     no        study 
    ## sigma^2.2  0.0399  0.1997     30     no  study/es.id 
    ## 
    ## Test for Residual Heterogeneity:
    ## QE(df = 28) = 76.5481, p-val < .0001
    ## 
    ## Test of Moderators (coefficient 2):
    ## F(df1 = 1, df2 = 28) = 0.2603, p-val = 0.6139
    ## 
    ## Model Results:
    ## 
    ##            estimate      se     tval  df    pval    ci.lb    ci.ub      
    ## intrcpt     -0.9173  0.1660  -5.5266  28  <.0001  -1.2574  -0.5773  *** 
    ## time_days    0.0008  0.0015   0.5102  28  0.6139  -0.0023   0.0039      
    ## 
    ## ---
    ## Signif. codes:  0 '***' 0.001 '**' 0.01 '*' 0.05 '.' 0.1 ' ' 1

``` r
png(filename = file.path(basedir,"analysis/psilodep/paperfigs/SI_Fig_02.png"), res=315, width=3000, height=2200)
regplot(reg, mod="time_days", xlab="Time since final dose (days)")
dev.off()
```

![](/analysis/psilodep/paperfigs/SI_Fig_02.png) Adding time since final
dose as a continouus predictor to our model reveals a large and
significant effect-size favoring psilocybin immediately following dosing
that was stable over time.

### Subgroup and Sensitivity Analyses

We conduct comprehensive subgroup and sensitivity analyses to examine
the robustness of our findings and explore potential moderators of
treatment effects.

These analyses include:

**Subgroup Analyses:** - Depression as primary diagnosis - Study design
(parallel vs. crossover) - Exclusion of open-label studies - Exclusion
of high risk-of-bias studies

**Sensitivity Analyses:** - In multi-arm study (Goodwin 2022) replace
high-dose intervention (25 mg) with medium-dose intervention (10 mg) -
Expanded inclusion criteria - Clinician-rated vs. self-report outcomes -
Exclusion of outlier studies - Fixed-effects model

``` r
# Build a dataframe that has each subgroup and sensitivity analysis in it

data_main <- data %>%
  filterPoolingData(
    primary_instrument == "1",
    primary_timepoint == "1",
    is.na(post_crossover) | !Detect(post_crossover,"1"),
    outcome_type == "msd" | outcome_type == "imsd",
    !(Detect(study, "Goodwin 2022") & (!is.na(multi_arm1)) & Detect(multi_arm1, "10 mg")),
    !(Detect(study, "Goodwin 2022") & (!is.na(multi_arm2)) & Detect(multi_arm2, "10 mg")),
    !Detect(study, "Krempien 2023"),
    !Detect(study, "Carhart-Harris 2021")
    ) %>%
    mutate(multi_arm2 = "main")

data_dep <- data %>%
  filterPoolingData(
    primary_instrument == "1",
    primary_timepoint == "1",
    is.na(post_crossover) | !Detect(post_crossover,"1"),
    outcome_type == "msd" | outcome_type == "imsd",
    !(Detect(study, "Goodwin 2022") & (!is.na(multi_arm1)) & Detect(multi_arm1, "10 mg")),
    !(Detect(study, "Goodwin 2022") & (!is.na(multi_arm2)) & Detect(multi_arm2, "10 mg")),
    !Detect(study, "Krempien 2023"),
    !Detect(study, "Carhart-Harris 2021"),
    diagnosis == "dep" | diagnosis == "trd"
    ) %>%
    mutate(multi_arm2 = "dep")

data_excwl <- data %>%
  filterPoolingData(
    primary_instrument == "1",
    primary_timepoint == "1",
    is.na(post_crossover) | !Detect(post_crossover,"1"),
    outcome_type == "msd" | outcome_type == "imsd",
    !(Detect(study, "Goodwin 2022") & (!is.na(multi_arm1)) & Detect(multi_arm1, "10 mg")),
    !(Detect(study, "Goodwin 2022") & (!is.na(multi_arm2)) & Detect(multi_arm2, "10 mg")),
    !Detect(study, "Krempien 2023"),
    !Detect(study, "Carhart-Harris 2021"),
    outcome_type == "msd" | outcome_type == "imsd",
    !Detect(condition_arm2, "wl"),
  ) %>%
  mutate(multi_arm2 = "excwl")

data_rob <- data %>%
  filterPoolingData(
    primary_instrument == "1",
    primary_timepoint == "1",
    is.na(post_crossover) | !Detect(post_crossover,"1"),
    outcome_type == "msd" | outcome_type == "imsd",
    !(Detect(study, "Goodwin 2022") & (!is.na(multi_arm1)) & Detect(multi_arm1, "10 mg")),
    !(Detect(study, "Goodwin 2022") & (!is.na(multi_arm2)) & Detect(multi_arm2, "10 mg")),
    !Detect(study, "Krempien 2023"),
    !Detect(study, "Carhart-Harris 2021"),
    outcome_type == "msd" | outcome_type == "imsd",
    !Detect(rob, "High"),
  ) %>%
  mutate(multi_arm2 = "rob")

data_parallel <- data %>%
  filterPoolingData(
    primary_instrument == "1",
    primary_timepoint == "1",
    outcome_type == "msd" | outcome_type == "imsd",
    is.na(post_crossover) | !Detect(post_crossover,"1"),
    outcome_type == "msd" | outcome_type == "imsd",
    !(Detect(study, "Goodwin 2022") & (!is.na(multi_arm1)) & Detect(multi_arm1, "10 mg")),
    !(Detect(study, "Goodwin 2022") & (!is.na(multi_arm2)) & Detect(multi_arm2, "10 mg")),
    !Detect(study, "Krempien 2023"),
    !Detect(study, "Carhart-Harris 2021"),
    design == "parallel"
  ) %>%
  mutate(multi_arm2 = "parallel")

data_crossover <- data %>%
  filterPoolingData(
    primary_instrument == "1",
    primary_timepoint == "1",
    outcome_type == "msd" | outcome_type == "imsd",
    is.na(post_crossover) | !Detect(post_crossover,"1"),
    outcome_type == "msd" | outcome_type == "imsd",
    !(Detect(study, "Goodwin 2022") & (!is.na(multi_arm1)) & Detect(multi_arm1, "10 mg")),
    !(Detect(study, "Goodwin 2022") & (!is.na(multi_arm2)) & Detect(multi_arm2, "10 mg")),
    !Detect(study, "Krempien 2023"),
    !Detect(study, "Carhart-Harris 2021"),
    design == "crossover"
  ) %>%
  mutate(multi_arm2 = "crossover")

data_expanded <- data %>%
  filterPoolingData(
    primary_instrument == "1",
    primary_timepoint == "1",
    outcome_type == "msd" | outcome_type == "imsd",
    !(Detect(study, "Goodwin 2022") & (!is.na(multi_arm1)) & Detect(multi_arm1, "10 mg")),
    !(Detect(study, "Goodwin 2022") & (!is.na(multi_arm2)) & Detect(multi_arm2, "10 mg")),
    !(Detect(study, "Krempien 2023") & (!is.na(multi_arm1)) & Detect(multi_arm1, "12 mg")),
    !(Detect(study, "Krempien 2023") & (!is.na(multi_arm2)) & Detect(multi_arm2, "12 mg"))
    ) %>%
    mutate(multi_arm2 = "expanded")

data_outliers <- data_main %>%
  filterPoolingData(
    !Detect(study, "Davis 2021")
    ) %>%
    mutate(multi_arm2 = "outliers")

data_fixed <- data_main %>%
    mutate(multi_arm2 = "fixed")

data_g10 <- data %>%
  filterPoolingData(
    primary_instrument == "1",
    primary_timepoint == "1",
    is.na(post_crossover) | !Detect(post_crossover,"1"),
    outcome_type == "msd" | outcome_type == "imsd",
    !(Detect(study, "Goodwin 2022") & (!is.na(multi_arm1)) & Detect(multi_arm1, "25 mg")),
    !(Detect(study, "Goodwin 2022") & (!is.na(multi_arm2)) & Detect(multi_arm2, "25 mg")),
    !Detect(study, "Krempien 2023"),
    !Detect(study, "Carhart-Harris 2021")
    )  %>%
    mutate(multi_arm2 = "g10")

data_clinician <- data %>%
  filterPoolingData(
    primary_timepoint == "1",
    is.na(post_crossover) | !Detect(post_crossover,"1"),
    !(Detect(study, "Goodwin 2022") & (!is.na(multi_arm1)) & Detect(multi_arm1, "10 mg")),
    !(Detect(study, "Goodwin 2022") & (!is.na(multi_arm2)) & Detect(multi_arm2, "10 mg")),
    !Detect(study, "Krempien 2023"),
    !Detect(study, "Carhart-Harris 2021"),
    rating == "clinician",
    Detect(instrument_symptom, "depression"),
    outcome_type != "response",
    outcome_type != "remission",
    outcome_type != "change"
  ) %>%
  mutate(multi_arm2 = "clincian") %>%
  filterPriorityRule(instrument = c("madrs", "grid-ham-d"))

data_selfreport <- data %>%
  filterPoolingData(
    primary_timepoint == "1",
    is.na(post_crossover) | !Detect(post_crossover,"1"),
    !(Detect(study, "Goodwin 2022") & (!is.na(multi_arm1)) & Detect(multi_arm1, "10 mg")),
    !(Detect(study, "Goodwin 2022") & (!is.na(multi_arm2)) & Detect(multi_arm2, "10 mg")),
    !Detect(study, "Krempien 2023"),
    !Detect(study, "Carhart-Harris 2021"),
    rating == "self-report",
    Detect(instrument_symptom, "depression"),
    outcome_type != "response",
    outcome_type != "remission",
    outcome_type != "change" & outcome_type != "unknown"
  ) %>%
  mutate(multi_arm2 = "self-report") %>%
  filterPriorityRule(instrument = c("bdi", "qids-sr", "hads-d", "smdds", "hads"))
```

``` r
main <- runMetaAnalysis(data_main,

  # Specify statistical parameters
  which.run = "overall", # inverse variance random effects
  es.measure = "g", # uses .g column in data_es and .g_se, referring to Hedges' g
  method.tau = "REML", 
  method.tau.ci = "Q-Profile", 
  hakn = TRUE, # Knapp-Hartung adjustment

  # Specify variables in data_es
  study.var = "study",
  arm.var.1 = "condition_arm1",
  arm.var.2 = "condition_arm2",
  measure.var = "instrument",
  w1.var = "n_arm1",
  w2.var = "n_arm2",
  time.var = "time_weeks",
  round.digits = 2 
)

# Use metapsyTools replacement and rerun functions for quickly repeating the same analysis with the same parameters

dep <- main # copy the model to a new name
data(dep) <- data_dep # replace the dataframe in the new model
rerun(dep) # re-run the model
```

    ## Model results ------------------------------------------------ 
    ## Model       k     g g.ci           p        i2 i2.ci         prediction.ci   nnt
    ##  -1 [-1.62; -0.39] 0.009  60.4 [2.88; 83.84] [-2.09; 0.09]  2.75

``` r
excwl <- main
data(excwl) <- data_excwl
rerun(excwl)
```

    ## Model results ------------------------------------------------ 
    ## Model       k     g g.ci          p         i2 i2.ci      prediction.ci    nnt
    ## .84 [-1.1; -0.58] <0.001  12.6 [0; 74.49] [-1.11; -0.57]  3.35

``` r
rob <- main
data(rob) <- data_rob
rerun(rob)
```

    ## Model results ------------------------------------------------ 
    ## Model       k     g g.ci           p        i2 i2.ci      prediction.ci    nnt
    ## .94 [-1.44; -0.43] 0.004  56.3 [0; 81.21] [-1.81; -0.06]  2.96

``` r
parallel <- main
data(parallel) <- data_parallel
rerun(parallel)
```

    ## Model results ------------------------------------------------ 
    ## Model       k     g g.ci           p        i2 i2.ci      prediction.ci    nnt
    ## .79 [-1.11; -0.46] 0.003  14.3 [0; 82.17] [-1.09; -0.49]   3.6

``` r
crossover <- main
data(crossover) <- data_crossover
rerun(crossover)
```

    ## Model results ------------------------------------------------ 
    ## Model       k     g g.ci         p        i2 i2.ci          prediction.ci   nnt
    ## .19 [-2.5; 0.12] 0.062  69.3 [11.47; 89.36] [-3.64; 1.25]  2.28

``` r
### SENSITIVITY

expanded <- main
data(expanded) <- data_expanded
rerun(expanded)
```

    ## Model results ------------------------------------------------ 
    ## Model       k     g g.ci           p         i2 i2.ci         prediction.ci    nnt
    ## .89 [-1.24; -0.55] <0.001  53.7 [10.99; 75.9] [-1.64; -0.15]  3.12

``` r
outliers <- main
data(outliers) <- data_outliers
rerun(outliers)
```

    ## Model results ------------------------------------------------ 
    ## Model       k     g g.ci           p         i2 i2.ci      prediction.ci    nnt
    ## .81 [-1.05; -0.58] <0.001   8.6 [0; 70.37] [-1.04; -0.59]  3.46

``` r
fixed <- main
method.tau(fixed) <- "FE" # for this sensitivity analysis, we keep data the same but change parameters
hakn(fixed) <- FALSE
rerun(fixed)
```

    ## Model results ------------------------------------------------ 
    ## Model       k     g g.ci           p         i2 i2.ci      prediction.ci   nnt
    ## .86 [-1.05; -0.68] <0.001  51.5 [0; 77.28] [-1.6; -0.24]  3.25

``` r
g10 <- main
data(g10) <- data_g10
rerun(g10)
```

    ## Model results ------------------------------------------------ 
    ## Model       k     g g.ci           p        i2 i2.ci          prediction.ci   nnt
    ## .89 [-1.36; -0.42] 0.003  72.2 [45.47; 85.87] [-2.06; 0.28]  3.13

``` r
clinician <- main
data(clinician) <- data_clinician
rerun(clinician)
```

    ## Model results ------------------------------------------------ 
    ## Model       k     g g.ci           p        i2 i2.ci         prediction.ci   nnt
    ## .02 [-1.51; -0.54] 0.002  57.6 [1.73; 81.67] [-1.9; -0.14]  2.69

``` r
selfreport <- main
data(selfreport) <- data_selfreport
rerun(selfreport)
```

    ## Model results ------------------------------------------------ 
    ## Model       k     g g.ci          p        i2 i2.ci          prediction.ci   nnt
    ## .11 [-2.58; 0.35] 0.102  78.1 [47.31; 90.87] [-4.24; 2.01]  2.45

Here’s our summary figure! ![](/analysis/psilodep/paperfigs/Fig_03.png)
Our series of subgroup and sensitivity analyses produced results largely
in line with our main model results. Hedges’ g values did not differ
greatly from the main model, and 10/12 of the subgroup and sensitivity
analyses produced significant results. Heterogeneity changes
substantially when excluding open-label studies, excluding crossover
studies, analyzing crossover studies on their own, and looking
exclusively at self-report outcomes.

### Dichotomous Outcomes Analysis

In addition to continuous depression severity scores, we also analyze
dichotomous outcomes including response and remission rates. These
analyses provide complementary information about the clinical
significance of psilocybin treatment.

#### Response Rate Analysis

We first analyze response rates, defined as the proportion of
participants achieving a clinically meaningful reduction in depression
symptoms.

``` r
# Get response data

data_response <- data %>%
  filterPoolingData(
    primary_instrument == "1",
    primary_timepoint == "1",
    outcome_type == "response",
    !(Detect(study, "Goodwin 2022") & (!is.na(multi_arm1)) & Detect(multi_arm1, "10 mg")),
    !(Detect(study, "Goodwin 2022") & (!is.na(multi_arm2)) & Detect(multi_arm2, "10 mg")),
    !Detect(study, "Krempien 2023")
  )
data_response <- data_response[order(data_response$year), ]

# Run meta-analysis

response_results <- runMetaAnalysis(data_response,
  which.run = "overall",
  es.measure = "RR", # risk ratio
  es.type = "raw",
  method.tau = "PM",
  method.tau.ci = "Q-Profile",
  method.random.ci = "HK",
  hakn = TRUE, # Knapp-Hartung adjustement

  # Specify variables
  study.var = "study",
  arm.var.1 = "condition_arm1",
  arm.var.2 = "condition_arm2",
  measure.var = "instrument",
  w1.var = "n_arm1",
  w2.var = "n_arm2",
  time.var = "time_weeks",
  round.digits = 2
)

# Create simple forest plot of response results

meta::forest(
  response_results$model.overall,
  sortvar = response_results$model.overall$data$year,
  xlab = "Log RR (95% CI)",
  leftlabs = c("Study", "Log RR"),
  layout = "JAMA")
```

![](/analysis/psilodep/knitfigs/response%20model-1.png)

Our meta-analysis shows statistically significant greater treatment
response with psilocybin compared to control conditions.

#### Remission Rate Analysis

We also analyze remission rates, defined as the proportion of
participants achieving full remission of depressive symptoms.

``` r
# Get remission data

data_remission <- data %>%
  filterPoolingData(
    primary_instrument == "1",
    primary_timepoint == "1",
    outcome_type == "remission",
    !(Detect(study, "Goodwin 2022") & (!is.na(multi_arm1)) & Detect(multi_arm1, "10 mg")),
    !(Detect(study, "Goodwin 2022") & (!is.na(multi_arm2)) & Detect(multi_arm2, "10 mg")),
    !Detect(study, "Krempien 2023")
  )
data_remission <- data_remission[order(data_remission$year), ]

# Run meta-analysis

remission_results <- runMetaAnalysis(data_remission,
  which.run = "overall",
  es.measure = "RR", # risk ratio
  es.type = "raw",
  method.tau = "PM",
  method.tau.ci = "Q-Profile",
  method.random.ci = "HK",
  hakn = TRUE, # Knapp-Hartung adjustement

  # Specify variables
  study.var = "study",
  arm.var.1 = "condition_arm1",
  arm.var.2 = "condition_arm2",
  measure.var = "instrument",
  w1.var = "n_arm1",
  w2.var = "n_arm2",
  time.var = "time_weeks",
  round.digits = 2
)

# Create simple forest plot of remission results

meta::forest(
  remission_results$model.overall,
  sortvar=remission_results$model.overall$data$year,
  xlab = "Log RR (95% CI)",
  leftlabs = c("Study", "Log RR"),
  layout = "JAMA")
```

![](/analysis/psilodep/knitfigs/remission%20model-1.png)

Our meta-analysis shows statistically significant higher remission rates
with psilocybin compared to control conditions.

As a sensitivity analysis, we also run a fixed-effects meta-analysis on
the response and remission results.

``` r
# Run fixed meta-analysis

fixed_response_results <- runMetaAnalysis(data_response,
  which.run = "overall",
  es.measure = "RR", # risk ratio
  es.type = "raw",
  method.tau = "FE",
  method.tau.ci = "Q-Profile",
  method.random.ci = "HK",
  hakn = FALSE, # Knapp-Hartung adjustement

  # Specify variables
  study.var = "study",
  arm.var.1 = "condition_arm1",
  arm.var.2 = "condition_arm2",
  measure.var = "instrument",
  w1.var = "n_arm1",
  w2.var = "n_arm2",
  time.var = "study_time_point",
  round.digits = 2
)
fixed_response_results
```

    ## Model results ------------------------------------------------ 
    ## Model       k    rr rr.ci        p         i2 i2.ci     prediction.ci   nnt
    ## 2.8 [2.05; 3.83] <0.001     0 [0; 79.2] [1.78; 4.3]    2.81

Using a fixed-effects model to run a meta-analysis on response outcomes
yielded results that were in line with the main model, showing
statistically significant greater treatment response with psilocybin
compared to control conditions.

``` r
#Run fixed meta-analysis

fixed_remission_results <- runMetaAnalysis(data_remission,
  which.run = "overall",
  es.measure = "RR", # risk ratio
  es.type = "raw",
  method.tau = "FE",
  method.tau.ci = "Q-Profile",
  method.random.ci = "HK",
  hakn = FALSE, # Knapp-Hartung adjustement

  # Specify variables
  study.var = "study",
  arm.var.1 = "condition_arm1",
  arm.var.2 = "condition_arm2",
  measure.var = "instrument",
  w1.var = "n_arm1",
  w2.var = "n_arm2",
  time.var = "study_time_point",
  round.digits = 2
)
fixed_remission_results
```

    ## Model results ------------------------------------------------ 
    ## Model       k    rr rr.ci        p         i2 i2.ci     prediction.ci   nnt
    ## .13 [2.66; 6.42] <0.001     0 [0; 79.2] [2.22; 7.71]      3

Using a fixed-effects model to run a meta-analysis on remission outcomes
yielded results that were in line with the main model, showing
statistically significant higher remission rate with psilocybin compared
to control conditions.

### Summary and Conclusions

This comprehensive meta-analysis provides promising evidence regarding
the efficacy of psilocybin for treating depression, but should be
interpreted with caution.

The analysis includes:

1.  **Primary analysis** of continuous depression severity outcomes
    using standardized mean differences
2.  **Time course analysis** examining how treatment effects evolve over
    time
3.  **Publication bias assessment** using multiple methods
4.  **Extensive subgroup and sensitivity analyses** to examine
    robustness and moderators
5.  **Dichotomous outcomes analysis** of response and remission rates

The results demonstrate consistent evidence for the efficacy of
psilocybin in reducing depression severity, with effects persisting over
time and showing robustness across various sensitivity analyses.
However, given the small number of studies eligible to include in our
meta-analysis and limitations such as the potential for functional
unblinding and expectancy effects, results should be interpreted with
caution.
