---
layout: single
title: "Meta-analysis on Psilocybin for Depression"
output:
  md_document:
    variant: markdown_github
    preserve_yaml: true
---

This document outlines the steps taken to perform a meta-analysis
investigating the efficacy of psilocybin for treating depression, using
data collated for the SYPRES project. Full source code is available
[here](https://github.com/pennlinc/sypres-docs/blob/main/analysis/psilodep/psilodep-meta-analysis.Rmd).

### Load Packages

Next, we load the necessary R packages for data manipulation,
meta-analysis, and visualization. Key packages include: - `readr` and
`tidyverse` for data loading and manipulation. - `meta` and `metafor`
for conducting the meta-analysis calculations. - `esc` for effect size
calculation utilities. - `metapsyTools` for specialized functions
designed for psychiatric meta-analyses, particularly handling data
formats and running pre-defined analysis pipelines. - `dmetar` for
additional meta-analysis functions and tools.

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

### Data Loading and Preparation

The raw data is loaded from a CSV file. This dataset contains
information extracted from multiple studies.

Some studies report change scores from baseline rather than endpoint
scores. To pool these studies with those reporting endpoint means and
standard deviations (SDs), we need endpoint SDs for the change score
studies. Where these are missing, we impute them.

Specifically, for the MADRS (Montgomery–Åsberg Depression Rating Scale)
outcome: 1. We identify studies reporting change scores
(`outcome_type == "change"`). 2. For Rosenblat et al. (2024) and Goodwin
et al. (2022), endpoint SDs are imputed using the average endpoint SD
from the Raison et al. (2023) study arms. We calculate the endpoint mean
by adding the mean change to the baseline mean. These rows are marked
with `outcome_type = "imsd"` (imputed mean/SD). 3. For Raison et
al. (2023) itself, we use the reported endpoint SDs directly and
calculate the endpoint means from the change scores and baseline means.
These rows retain `outcome_type = "msd"`.

The original dataset is then combined with these new rows containing the
calculated/imputed endpoint data.

Finally, we use functions from the `metapsyTools` package
(`checkDataFormat` and `checkConflicts`) to ensure the combined data
conforms to the expected structure and to identify potential
inconsistencies (e.g., differing control group data reported for the
same study).

``` r
# Load data
data <- read_csv("/Users/sps253/Documents/GIT/data-depression-psiloctr/data.csv")
#data <- read_csv("/Users/bsevchik/Documents/GitHub/metapsy_psilodep/data.csv")
# after release we will replace this with metapsyData load function

# Check data format with checkDataFormat
checkDataFormat(data)

# Check conflicts with checkConflicts
checkConflicts(data)
```

### Filter Data and Calculate Effect Sizes

Before running the main analysis, we prepare the data further:

1.  **Calculate Effect Sizes:** We use `calculateEffectSizes()` (from
    `metapsyTools`) to compute Hedges’ g (a standardized mean
    difference, SMD) and its standard error for each study comparison
    based on the endpoint means, SDs, and sample sizes.
2.  **Filter Data:** We select the specific data points to be included
    in the primary meta-analysis:
    -   Exclude specific low-dose arms (10 mg psilocybin) if present in
        multi-arm studies.
    -   Exclude the Krempien (2023) study.
    -   Use `filterPoolingData()` (from `metapsyTools`) to select only
        rows marked as the primary instrument
        (`primary_instrument == "1"`) and primary timepoint
        (`primary_timepoint == "1"`) for each study.
    -   Include only the endpoint data (`outcome_type == "msd"` or
        `"imsd"`), excluding the original change score data.

The resulting `data_main` dataframe contains the filtered data ready for
our main meta-analysis.

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

### Run Primary Meta-Analysis

We now perform the main meta-analysis using the `runMetaAnalysis`
function from `metapsyTools`. This function simplifies running standard
meta-analytic models.

We specify: - `which.run = "overall"`: Conducts a random-effects
meta-analysis pooling all studies in `data_main`. - `es.measure = "g"`:
Uses the pre-calculated Hedges’ g effect sizes. - `method.tau = "REML"`:
Employs the Restricted Maximum Likelihood estimator for the
between-study variance (τ²). - `hakn = TRUE`: Applies the Knapp-Hartung
adjustment for significance tests, which is recommended for
meta-analyses with a small number of studies. - Various `*.var`
arguments map the columns in `data_main` to the required inputs for the
analysis (study labels, arm conditions, sample sizes, etc.).

The results, including the pooled effect size, confidence intervals,
heterogeneity statistics, and the meta-analysis model object, are stored
in `main_results`.

Finally, a basic forest plot is generated using `meta::forest` to
visualize the individual study effect sizes and the overall pooled
result. The studies are sorted by year.

``` r
main_results <- runMetaAnalysis(data_main, # using pre-filtered data for now

  # specify models to run
  which.run = c("overall", "outliers"),
  which.influence = "overall",
  which.outliers = "overall",

  # specify statistical parameters
  es.measure = "g", # uses .g column in data_es and .g_se (Hedges' g/bias-corrected SMD)
  method.tau = "REML", # default, but still including for clarity
  method.tau.ci = "Q-Profile", # not sure if this will work!
  hakn = TRUE, # Knapp-Hartung effect size significance tests be used

  # specify variables in data_es
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
    ## Prediction interval               [-1.6139; -0.2270]              
    ## 
    ## Quantifying heterogeneity:
    ##  tau^2 = 0.0674 [0.0000; 1.2489]; tau = 0.2596 [0.0000; 1.1175]
    ##  I^2 = 51.5% [0.0%; 77.3%]; H = 1.44 [1.00; 2.10]
    ## 
    ## Test of heterogeneity:
    ##      Q d.f. p-value
    ##  16.50    8  0.0358
    ## 
    ## Details on meta-analytical method:
    ## - Inverse variance method
    ## - Restricted maximum-likelihood estimator for tau^2
    ## - Q-Profile method for confidence interval of tau^2 and tau
    ## - Hartung-Knapp adjustment for random effects model (df = 8)
    ## - Prediction interval based on t-distribution (df = 7)

``` r
meta::forest(
  main_results$model.overall,
  sortvar = main_results$model.overall$data$year,
  layout = "JAMA"
)
```

![](/analysis/psilodep/knitfigs/primary-meta-analysis-1.png)

# Funnel Plot & Egger’s Test

``` r
eggers.test(main_results$model.overall)
```

    ## Warning in eggers.test(main_results$model.overall): Your meta-analysis contains k = 9 studies. Egger's test may lack
    ## the statistical power to detect bias when the number of studies is small (i.e., k<10).

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
       #ylim = 
       xlab = "Standardized Mean Difference (SMD)",
       ylab = "Standard Error (SE)",
       main = "Funnel Plot of Main Model Continuous Outcomes",
       las = 1
       )
dev.off()
```

![](/analysis/psilodep/paperfigs/SI_Fig_01.png)

# three-level CHE

``` r
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

time_results <- runMetaAnalysis(data_time, # using pre-filtered data for now
  
  which.run = "threelevel.che",
  # specify statistical parameters
  es.measure = "g", # uses .g column in data and .g_se (Hedges' g/bias-corrected SMD)
  method.tau = "REML", # default, but still including for clarity
  method.tau.ci = "Q-Profile", # not sure if this will work!
  hakn = TRUE, # Knapp-Hartung effect size significance tests be used

  # specify variables in data
  study.var = "study",
  arm.var.1 = "condition_arm1",
  arm.var.2 = "condition_arm2",
  measure.var = "instrument",
  w1.var = "n_arm1",
  w2.var = "n_arm2",
  time.var = "time_days",
  round.digits = 2 # can change to change number of digits to round the presented results to
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

![](/analysis/psilodep/paperfigs/SI_Fig_02.png)

### Subgroup & sensitivity analyses!

Subgroups analyses can be easily filtered. We can run them all at once
with metapsyTools by mutating the the `multi_arm2` variable to be a
dummy variable designating our subgroups.

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

  # specify statistical parameters
  which.run = "overall", # inverse variance random effects
  es.measure = "g", # uses .g column in data_es and .g_se (Hedges' g/bias-corrected SMD)
  method.tau = "REML", # default, but still including for clarity
  method.tau.ci = "Q-Profile", # not sure if this will work!
  hakn = TRUE, # Knapp-Hartung effect size significance tests be used

  # specify variables in data_es
  study.var = "study",
  arm.var.1 = "condition_arm1",
  arm.var.2 = "condition_arm2",
  measure.var = "instrument",
  w1.var = "n_arm1",
  w2.var = "n_arm2",
  time.var = "time_weeks",
  round.digits = 2 # can change to change number of digits to round the presented results to
)

# use metapsyTools replacement and rerun functions for quickly repeating the same analysis with the same parameters

dep <- main # copy the model to a new name
data(dep) <- data_dep # replace the dataframe in the new model
rerun(dep) # re-run the model
```

    ## Model results ------------------------------------------------ 
    ## Model       k     g g.ci           p        i2 i2.ci         prediction.ci   nnt
    ##  -1 [-1.62; -0.39] 0.009  60.4 [2.88; 83.84] [-2.18; 0.18]  2.75

``` r
excwl <- main
data(excwl) <- data_excwl
rerun(excwl)
```

    ## Model results ------------------------------------------------ 
    ## Model       k     g g.ci          p         i2 i2.ci      prediction.ci    nnt
    ## .84 [-1.1; -0.58] <0.001  12.6 [0; 74.49] [-1.13; -0.55]  3.35

``` r
rob <- main
data(rob) <- data_rob
rerun(rob)
```

    ## Model results ------------------------------------------------ 
    ## Model       k     g g.ci           p        i2 i2.ci      prediction.ci    nnt
    ## .94 [-1.44; -0.43] 0.004  56.3 [0; 81.21] [-1.86; -0.02]  2.96

``` r
parallel <- main
data(parallel) <- data_parallel
rerun(parallel)
```

    ## Model results ------------------------------------------------ 
    ## Model       k     g g.ci           p        i2 i2.ci      prediction.ci    nnt
    ## .79 [-1.11; -0.46] 0.003  14.3 [0; 82.17] [-1.13; -0.44]   3.6

``` r
crossover <- main
data(crossover) <- data_crossover
rerun(crossover)
```

    ## Model results ------------------------------------------------ 
    ## Model       k     g g.ci         p        i2 i2.ci          prediction.ci   nnt
    ## .19 [-2.5; 0.12] 0.062  69.3 [11.47; 89.36] [-4.5; 2.11]   2.28

``` r
### SENSITIVITY

expanded <- main
data(expanded) <- data_expanded
rerun(expanded)
```

    ## Model results ------------------------------------------------ 
    ## Model       k     g g.ci           p         i2 i2.ci         prediction.ci    nnt
    ## .89 [-1.24; -0.55] <0.001  53.7 [10.99; 75.9] [-1.65; -0.14]  3.12

``` r
outliers <- main
data(outliers) <- data_outliers
rerun(outliers)
```

    ## Model results ------------------------------------------------ 
    ## Model       k     g g.ci           p         i2 i2.ci      prediction.ci    nnt
    ## .81 [-1.05; -0.58] <0.001   8.6 [0; 70.37] [-1.05; -0.58]  3.46

``` r
fixed <- main
method.tau(fixed) <- "FE" # for this sensitivity analysis, we keep data the same but change parameters
hakn(fixed) <- FALSE
rerun(fixed)
```

    ## Model results ------------------------------------------------ 
    ## Model       k     g g.ci           p         i2 i2.ci      prediction.ci    nnt
    ## .86 [-1.05; -0.68] <0.001  51.5 [0; 77.28] [-1.61; -0.23]  3.25

``` r
g10 <- main
data(g10) <- data_g10
rerun(g10)
```

    ## Model results ------------------------------------------------ 
    ## Model       k     g g.ci           p        i2 i2.ci          prediction.ci   nnt
    ## .89 [-1.36; -0.42] 0.003  72.2 [45.47; 85.87] [-2.09; 0.31]  3.13

``` r
clinician <- main
data(clinician) <- data_clinician
rerun(clinician)
```

    ## Model results ------------------------------------------------ 
    ## Model       k     g g.ci           p        i2 i2.ci         prediction.ci   nnt
    ## .02 [-1.51; -0.54] 0.002  57.6 [1.73; 81.67] [-1.95; -0.1]  2.69

``` r
selfreport <- main
data(selfreport) <- data_selfreport
rerun(selfreport)
```

    ## Model results ------------------------------------------------ 
    ## Model       k     g g.ci          p        i2 i2.ci          prediction.ci   nnt
    ## .11 [-2.58; 0.35] 0.102  78.1 [47.31; 90.87] [-4.7; 2.47]   2.45

Here’s our summary figure! ![](/analysis/psilodep/paperfigs/Fig_03.png)

### Run Meta-Analyses on Dichotomous Data

filter for response and remission data

``` r
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
```

run meta-analysis on response data

``` r
response_results <- runMetaAnalysis(data_response,
  which.run = "overall",
  es.measure = "RR", # risk ratio
  es.type = "raw",
  method.tau = "PM",
  method.tau.ci = "Q-Profile",
  method.random.ci = "HK",
  hakn = TRUE, # Knapp-Hartung adjustement

  # specify variables in data_dichotomous
  study.var = "study",
  arm.var.1 = "condition_arm1",
  arm.var.2 = "condition_arm2",
  measure.var = "instrument",
  w1.var = "n_arm1",
  w2.var = "n_arm2",
  time.var = "time_weeks",
  round.digits = 2
)

meta::forest(
  response_results$model.overall,
  sortvar = response_results$model.overall$data$year,
  xlab = "Log RR (95% CI)",
  leftlabs = c("Study", "Log RR"),
  layout = "JAMA")
```

![](/analysis/psilodep/knitfigs/response%20model-1.png)

run meta-analysis for remission data

``` r
remission_results <- runMetaAnalysis(data_remission,
  which.run = "overall",
  es.measure = "RR", # risk ratio
  es.type = "raw",
  method.tau = "PM",
  method.tau.ci = "Q-Profile",
  method.random.ci = "HK",
  hakn = TRUE, # Knapp-Hartung adjustement

  # specify variables in data_dichotomous
  study.var = "study",
  arm.var.1 = "condition_arm1",
  arm.var.2 = "condition_arm2",
  measure.var = "instrument",
  w1.var = "n_arm1",
  w2.var = "n_arm2",
  time.var = "time_weeks",
  round.digits = 2
)

meta::forest(
  remission_results$model.overall,
  sortvar=remission_results$model.overall$data$year,
  xlab = "Log RR (95% CI)",
  leftlabs = c("Study", "Log RR"),
  layout = "JAMA")
```

![](/analysis/psilodep/knitfigs/remission%20model-1.png)
