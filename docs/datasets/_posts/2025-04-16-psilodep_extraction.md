---
title: "Psilodep Covidence SOP"
excerpt: "Psilodep Covidence SOP"
layout: single

---

*SOP for full Covidence workflow on PSILODEP_Review*

# **Title and Abstract Screening Stage**
+ List of reasons to exclude studies during initial title/abstract screening:
  + Studies the wrong psychedelic drug
  + Review articles or meta-analyses
  + Animal studies (non-human research)
  + Protocols
  + Comment/Perspective
  + Non-RCTs
  + Studies in healthy participants
  + Open-label studies: These are generally excluded. However, a randomized open-label study with waitlist-control should be included. If it cannot be determined with certainty whether an open-label study has a randomization and control component, it is best practice to advance it to full-text screening for confirmation.
+ Tags are not required at this screening stage, nor are notes necessary. Any study meeting the exclusion criteria listed above should be excluded and not advanced to full-text review.

+ List of reasons to advance studies into full-text review (these studies might be excluded later):
   + Re-analyses/mechanistic papers (e.g., neuroimaging papers, mediation analyses, reports on additional outcomes, follow-ups)
   + Papers that compare the target psychedelic drug with another treatment (e.g., SSRIs/escitalopram)
   + Corrections to articles that have already been advanced or will be advanced to full-text review; these can later be merged with the studies they correct during the extraction stage.
   + RCTs that investigate the target psychedelic drug's effect on any specific outcome (e.g., alcohol use disorder, cancer); during full-text review, determine if any secondary outcome measures assess mood or depression.

  + Otherwise, include the studies for full-text review. Use the notes section to document any unusual cases not accounted for above.

# **Full Text Review**
+ During full-text review, select a reason for each study excluded. This is the current list of exclusion reasons, which can be updated here as needed:

  + Re-analysis/Secondary report
    + Choose this reason only if it is the *sole* reason for exclusion. For example, if the study compares a psychedelic drug to escitalopram, choose 'Wrong comparator' instead of 'Re-analysis/Secondary report.' Any of the subsequent reasons supersede the 'Re-analysis/secondary report' reason.
  + Conference abstract - full text already included
    + Some conference abstracts might be excluded for a different reason (in which case, the full text would not already be included). In such instances, the other reason (e.g., not an RCT) supersedes this conference abstract reason.
    + If the full text is not already included, but there is no other reason to exclude the conference abstract, leave it in full-text review for now and potentially follow-up with study authors.
    + Only advance conference abstracts at this stage if they report new information. If the full text is already included with the same results as the conference abstract, exclude the conference abstract.
  + Wrong patient population (e.g., healthy, pediatric)
  + Wrong outcomes/no mood outcomes
  + Wrong intervention/drug
  + Wrong comparator (e.g., SSRIs)
    + Studies comparing the target psychedelic drug with SSRIs/escitalopram fall into this category.
  + Not an RCT
    + Single-arm, non-randomized open-label studies fall into this category.
  + Protocol/incomplete study
  + Non-English language
+ The selected reason must agree between both reviewers, or conflicts will need to be resolved later.


# **Data Extraction**

*The sections below correspond to different tabs in Covidence's Data Extraction Tool. Read through the entire document before completing data extraction, and ensure a copy of the SOP is readily available during the process.*

| General Formatting: |
|:----------------------------------------------------|
|Our coding sheet parses multiple inputs via a semi-colon.<br>Group or time-point descriptions are used in several places to link information across the coding sheet.<br>Maintain consistency and do not create custom abbreviations for timepoints or arms (e.g., use '6 weeks' instead of '6 wks', or 'High-dose-1st' instead of 'HD1'). The simplest practice for consistency is to use the identical names reported in the study.|

| General Overview of Data Extraction Process for Reviewer 1 vs. Reviewer 2: |
|:----------------------------------------------------|
|1. Both reviewers complete the full identification, methods, and population sections. The process does not differ between reviewers for these tabs.<br>2. For the **interventions** section, *Reviewer 1* sets up the interventions table as described below, defining the number of intervention/control arms and entering the group names. *Reviewer 2* does not set up the table but fills out the required information within it.<br>3. For the **outcomes** section, *Reviewer 1* sets up the entire outcomes table. *Reviewer 2* does not perform any actions in the outcomes tab and can ignore the corresponding section of this SOP.<br>4. For the **results** table, *Reviewer 1* changes the format and sets up the results table as specified in the SOP. *Reviewer 2* cannot change the table format but fills it out with the appropriate values from the paper.|


## Summary
> **Tips for this section:**
> 1. The summary page contains the 'Complete' button (top right corner), which is used once data extraction is finished. This button does not appear in other sections.
> 2. Reviewing the supplement/protocol/appendix is useful. Supplemental information often contains details about randomization, recruitment, inclusion/exclusion criteria, and data for additional timepoints not reported in the main paper.
{: .notice--info}

## Identification
> **Tips for this section:**
> 1. Search for the study title on PubMed.
> 2. From the PubMed page, copy the PMID, trial registry number, and DOI.
> 3. Search the trial registry number in the corresponding database (e.g., ClinicalTrials.gov).
{: .notice--info}


SPONSORSHIP SOURCE
+ Enter the funding/sponsorship source for the study (e.g., the institution name).

COUNTRY
+ For the United States, enter "USA".
+ For the United Kingdom, enter "UK".
+ For the Czech Republic, enter "the Czech Republic".
+ For Denmark, enter "Denmark".
+ For Germany, enter "Germany".
+ For Ireland, enter "Ireland".
+ For the Netherlands, enter "the Netherlands".
+ For Portugal, enter "Portugal".
+ For Spain, enter "Spain".
+ For Canada, enter "Canada".
+ If there are multiple countries/study sites, separate them with semi-colons.

SETTING
+ Refers to the institution/study site. Specify if it is a multi-site study. Covidence defines this as "The setting where the study was conducted... important for understanding potential contextual factors."
+ Information to include if provided:
  + Indicate 'single-site' or 'multi-site'.
  + If dosing occurs in an institutional setting (typical), enter 'institutional setting'. Otherwise, enter 'other'.
+ Example format: 'multi-site; institutional setting'

COMMENTS
+ List any unusual details or information that did not fit into other fields.

AUTHOR'S CONTACT DETAILS
+ This field is often automatically filled by Covidence; verify its accuracy.

START DATE & END DATE
+ Format as "Month Year" (e.g., "October 2007").
+ If a day is provided, format as "Month Day, Year" (e.g., "October 5, 2007").
+ Use the start/end dates listed in the paper or protocol. If unavailable, search the trial registry number in the relevant database (e.g., ClinicalTrials.gov) and use the dates found there.
+ If both end of assessment and end of data analysis dates are provided, use the end of assessment date.

DOI, TRIAL REGISTRY ID, & PMID
+ Enter only the number itself (do not include prefixes like "DOI:" or "PMID:").
+ For merged studies, separate multiple DOIs with semi-colons, listing the primary study's DOI first. Only the DOI field needs to contain information from all merged sources.

MERGED STUDY?
+ Enter 'yes' if the study entry in Covidence combines information from multiple papers. Enter 'no' if it represents a single paper.
+ If only a correction/update is merged, still answer 'yes', although no new data will be extracted.
+ Merged study tips:
  1. The primary outcome listed in the Methods section should correspond to the primary outcome of the *primary* paper (often the first published; should match the pre-registered primary outcome).

WHAT DO ADDITIONAL PAPER(S) ADD?
+ Use this section ONLY if 'yes' was selected for 'MERGED STUDY?'. Otherwise, leave blank.
+ *If only a correction is merged, enter 'Correction'.*
  + If a correction is added alongside a secondary paper, append '; Correction' after the description of the secondary paper's contribution (following the format below).
+ *If only a conference abstract adding new information is merged, enter 'Conference abstract - [description of new results]'*.
  + If a conference abstract is added alongside a secondary paper, include this information after the secondary paper description, separated by a semi-colon.
+ Secondary papers merged in Covidence typically either report on the same outcomes but at later timepoints (long-term follow-up) or include additional outcomes at the same timepoints. This field MUST include: a) a brief general description of the added content, and b) a list of the additional outcomes (abbreviations acceptable) and/or additional timepoints. Replace italicized text in examples below with study-specific information:
  + Example (additional outcomes):<br>
      '*Goodwin 2023* expands upon *Goodwin 2022* by *adding additional self-report measures*. The additional outcome measures are: *GAD-7*, *QIDS-SR-16*, *PANAS*, *SDS*, *WSAS*, *EQ-5D-3L*, and *DSST*.'
  + Example (additional timepoints):<br>
      '*Goodwin 2023* expands upon *Goodwin 2022* by adding additional follow-up timepoints. The additional timepoints are: *6-months following the second dose*, and *12 months following the second dose*.'
  + Example (both):<br>
      '*Goodwin 2023* expands upon *Goodwin 2022* by adding both additional outcome measures and additional follow-up timepoints. The additional outcome measures are: *GAD-7*, *QIDS-SR-16*, *PANAS*, and *SDS*. The additional timepoints are: *6-months following the second dose*, and *12 months following the second dose*.'

## Methods
DESIGN
+ For this review, always select Randomized Controlled Trial.
+ Select the appropriate radio button for parallel group or crossover design.

METHOD OF RANDOMIZATION
+ Include details like cluster randomization if applicable. Some studies specify how randomization was generated; include this if available.

METHOD OF RECRUITMENT
+ Specify method (e.g., Online, Mail, Word of mouth).

BLINDING
+ Enter brief description (e.g., "double-blind," "single-blind," "open-label").

WHO WAS BLINDED?
+ Enter brief description. For double-blind studies, typically includes participants & study staff/clinicians administering the drug.

TYPE OF THERAPY
+ Enter 'Other' unless a standardized therapy (CBT, DBT, ERP, etc.) is specified. List non-traditional or drug-specific protocols (e.g., "set and setting protocol," MAPS protocol) if used.

FREQUENCY OF THERAPY SESSIONS
+ Provide a general sense of therapy frequency and timing per participant, noting if standardized between arms. Not required to be overly detailed.
  + Example (single-dose): 3 weekly sessions before dosing; 3 weekly sessions post-dosing.
  + Example (multi-dose): 3 weekly sessions before dosing; 3 weekly sessions between doses; 3 weekly sessions after final dose.

WHO PERFORMED CLINICAL ASSESSMENTS?

+ The most common scenarios are:

| Answer                       | Explanation                                                                 |
|:-----------------------------|:----------------------------------------------------------------------------|
| 3rd-party independent raters  | Common in industry-sponsored studies; aims to mitigate bias.               |
| Unspecified                  | Common in academic studies; generally presumed to be study staff.          |
| Independent study staff       | Study staff not involved in therapy administration.                         |
| Non-independent study staff   | Study staff involved in therapy administration.                             |


+ NOTE: This question concerns who administered the assessment (asked questions or provided questionnaires), not whether instruments were clinician-administered or self-report.
+ For older or academic studies, this may not be clearly reported. Check the 'assessments' section of the study protocol if available.

CHOSEN PRIMARY OUTCOME MEASURE
+ Use the abbreviation for the primary outcome measure, matching its name in the outcomes table.
+ If multiple primary outcome measures exist, list them in 'All primary outcome measures' and select one based on the following hierarchy:
  + Choose the measure most closely related to the review's focus (e.g., for depression, prioritize a depression outcome over an anxiety outcome).
  + Select the measure most commonly used in other studies, prioritizing clinician-administered over self-report, and independently administered over unspecified or study staff administration.
  + This selection should involve discussion among team members, with the decision and reasoning documented (e.g., on the study's Notion page).

SAFETY AND PHYSIOLOGY MEASURES
+ List all collected safety and physiology-related measures, separated by semi-colons.
+ Use the exact name of the measure or survey instrument if provided.
+ If sub-outcomes exist, listing them can provide helpful detail (or the more detailed response can be chosen during consensus).
+ Acute drug effects (ASC, MEQ) and longer-term emotional/spiritual/personality scales can be included here. However, explicit mood scales (depression, anxiety, etc.) should be listed under 'All other mood & secondary outcome measures'.

ALL OTHER MOOD & SECONDARY OUTCOME MEASURES
+ List all remaining outcome measures not categorized as primary or safety/physiology.
+ Use abbreviations, separated by semi-colons (e.g., MADRS; BDI; STAI).
  + For STAI, list 'STAI' here; specific forms (STAI-Trait, STAI-State, STAI-Total) can be reported in the results.
+ Many outcomes listed here might not be reported in detail in the study results but should be noted for reference.
+ Response & remission are often listed as secondary outcomes but do not need separate entries here, as they are derived from scales already included.

STUDY TIMEPOINTS
+ Do not calculate or convert timepoints; record them exactly as written in the study. Separate entries with semi-colons.
+ Other information to potentially include:
  + Timing of unblinding
  + Timing of crossover
  + Timing of dose administration
+ Information not needed here: timing of therapy sessions (covered in 'Frequency of therapy sessions').
+ The goal is to track the timing of doses and assessment administrations, similar to graphical timelines provided in some studies. This field serves as a reference to contextualize timepoints in the outcomes/results tabs.
+ Example generic format:
  'Study Timepoint (Covidence timepoint): Description;' OR 'Study Timepoint: Description;'*
    + *The Covidence timepoint in parentheses is only applicable for timepoints where outcomes are reported (dose administration timepoints typically lack a corresponding Covidence timepoint).*
+ Example format (Griffiths 2016):
  Day 0: Baseline; Month 1: Dose 1; 5 weeks after session 1 (Post-first dose 1): data assessment; 5 weeks after session 1: Dose 2; 5 weeks after session 1: Crossover; 5 weeks after session 2 (Post-second dose 1): data assessment; 6 months (Follow-up 1): Follow-up assessment
+ Example format (Goodwin 2022/2023):
  Day -1: Baseline; Day 1: Dose 1; Day 2 (Post-first dose 1): Follow-up at clinic assessment; Week 1 (Post-first dose 2): Follow-up at clinic assessment; Week 2: Follow-up at clinic assessment; Week 3 (Post-first dose 3): Follow-up at clinic assessment; Week 6 (Post-first dose 4): Follow-up remote assessment; Week 9 (Post-first dose 5): Follow-up remote assessment; Week 12 (Post-first dose 6): Follow-up at clinic assessment

OTHER
+ Include any other methodological information not covered in pre-specified fields.

NAME OF EACH ARM
+ Enter the names used by the paper authors to refer to each group (should match 'group name' in the Interventions section).
  + Example: Intervention group = "psilocybin group"; Control group = "niacin group".
+ Use these exact group names consistently throughout the data extraction template.

STATISTICAL ANALYSES
+ Copy and paste relevant statistical analysis methods descriptions from the paper.
+ Include the paragraphs describing modeling methods for baseline adjustments, missing data imputation, and significance testing (typically 1-3 paragraphs).

SUPPLEMENTAL ANALYSES
+ Include descriptions of additional analyses (often found in supplements) that may be of interest for later analysis but are not reported in the main Covidence results. Examples include subgroup analyses (by antidepressant use, prior psychedelic use, baseline severity) or Per Protocol (PP) analyses.

MISCELLANEOUS DETAILS
+ Add any notable method or design details not covered above. This field may sometimes be blank. Use this field for miscellaneous details identified for extraction later.
+ Generally, use this 'Miscellaneous details' field rather than the generic 'Notes' section for such information.

ADJUSTED VALUE USED
+ Use this field only if the paper reports primary results as adjusted values. While the 'Notes' box in the Outcomes section indicates if a value is adjusted/unadjusted, provide specifics here.
+ Example: If the QIDS-SR score uses the least squares mean, enter "QIDS-SR: least-squares mean".
+ Separate entries for different outcome measures with a semi-colon (e.g., "QIDS-SR: least-squares mean; MADRS: least-squares mean").

IS PRIMARY ANALYSIS ON INTENT-TO-TREAT (ITT) OR PER-PROTOCOL (PP) POPULATION?
  + Enter 'ITT' if analysis is on the intent-to-treat population. Enter 'PP' if on the per-protocol population.
  + If unclear, enter 'unspecified'.

CHOSEN PRIMARY ENDPOINT
+ The primary endpoint should match a time-point description in the outcomes table (see Outcomes -> Overall Process) and align with the paper's description. It should be the primary endpoint of the *main paper*.
+ If not explicitly stated, review pre-registered information (check clinical trial registry if possible) and choose the timepoint closest to the average primary endpoint timepoint across similar studies.
+ This selection should involve team discussion, with the decision and rationale documented (e.g., on Notion).
+ If a specific timepoint is chosen according to the above, list all primary endpoints mentioned in the paper/pre-registration in the 'All primary endpoints' field below.

ADJUSTED OUTCOMES
+ List all outcomes reported as adjusted values. Separate abbreviations with semi-colons.
+ Do not list response/remission outcomes here.

UNADJUSTED OUTCOMES
+ List all outcomes reported as unadjusted values. Separate abbreviations with semi-colons.
+ Do not list response/remission outcomes here.

CHANGE FROM BASELINE OUTCOMES
+ List all outcomes reported as change from baseline (not endpoint values). Separate abbreviations with semi-colons.
+ Change-from-baseline values represent the difference from the baseline measure (e.g., negative scores for depression scales after effective intervention).
+ Do not include response/remission outcomes here.

ENDPOINT OUTCOMES
+ List all outcomes reported as endpoint values (raw scores at the timepoint, not change from baseline). Separate abbreviations with semi-colons.
+ Do not include response/remission outcomes here.

HOW IS RESPONSE DEFINED?
+ Note how response is defined in the study and its corresponding outcome name in the outcomes/results section.
  + Example: 'Response 1: 50% or greater reduction in BDI at a particular assessment point relative to baseline'
+ If multiple response definitions exist, indicate the corresponding outcome name for each and separate definitions with semi-colons.
  + Example format: 'Response 1: 50% or greater reduction in BDI...; Response 2: 50% or greater reduction in HADS-D...'
+ If response is not an outcome, enter 'n/a'.

HOW IS REMISSION DEFINED?
+ Note how remission is defined and its corresponding outcome name.
  + Example: 'Remission 1: 50% or greater reduction in depressive symptoms plus HADS D ⩽7'
+ If multiple remission definitions exist, use the same format as for response, separating with semi-colons.
+ If remission is not an outcome, enter 'n/a'.

DATA FROM WEBPLOTDIGITIZER
+ List data recorded in results obtained via WebPlotDigitizer.
+ Include outcomes, timepoints, and statistics if relevant: 'Outcome1: Timepoint1 (stat1, stat2), Timepoint2 (stat1); Outcome2: Timepoint1 (stat1, stat2), Timepoint2 (stat1, stat2), Timepoint3 (stat1, stat2)'
  + Example format: "MADRS: Day 2 (mean, SD), Day 14 (mean, SD); BDI: Day -1 (mean, SD), Day 14 (mean, SD), Day 21 (mean, SD)"

DATA FROM CONTACTING AUTHORS
+ List data recorded in results obtained via author contact.
+ Use the same format as for 'Data from WebPlotDigitizer'.

ALL PRIMARY ENDPOINTS
+ List all primary endpoints as pre-registered/listed in the paper.
+ May be identical to 'Chosen primary endpoint' if only one exists.

ALL PRIMARY OUTCOME MEASURES
+ List all primary outcome measures as pre-registered/listed in the paper.
+ May be identical to 'Chosen primary outcome measure' if only one exists.

ADVERSE EVENTS
+ Briefly describe adverse events as listed in the study. Separate details with semi-colons. Potential information:
  + Number or percentage of AEs (specify by arm and total if available).
    + Example format: 'Number of AEs: intervention = 13, control = 5, total = 18'
  + Number or percentage of serious AEs (SAEs).
  + List of AEs (e.g., 'AEs included headache, nausea, dizziness').
  + Number of SAEs per arm (use same format as for AEs).
  + List of SAEs.


## Population
INCLUSION/EXCLUSION CRITERIA
+ Copy directly from protocol/paper. Delete bullet points. Separate criteria lines by adding a semicolon to the end of each line.

GROUP DIFFERENCES
+ Enter 'n/a' for most studies. Note any reported group differences (due to criteria or randomization).

TOTAL SAMPLE SIZE
+ Enter the number of participants randomized.

NUMBER OF WITHDRAWALS
+ Provide the total number per arm throughout the study. Name arms according to the Interventions table group names.
+ Total withdrawals = number excluded from per-protocol analyses.
+ For crossover studies, specify if withdrawals occurred before or after crossover.
  + Example (non-crossover): "High-dose-1st: 4; Low-dose-1st: 6"
  + Example (crossover): "immediate treatment group: 2 total (1 pre-crossover, 1 post-crossover); delayed treatment group: 1 total (0 pre-crossover, 1 post-crossover)"
    + Include total withdrawals per group, followed by breakdown (pre/post-crossover counts separated by comma). Separate group entries with a semi-colon.

PRISMA WITHDRAWAL DETAILS
+ Transcribe information as described/displayed in the study's flow diagram, maintaining the original phrasing; include arm, n, and reason.
+ Example format (Goodwin 2022):
  + 25-mg group: 79 randomized, 5 discontinued (2 adverse event, 1 lost to follow-up, 2 withdrew); 10-mg group: 75 randomized, 9 discontinued (1 lack of efficacy, 2 adverse event, 6 withdrew); 1-mg group: 79 randomized, 10 discontinued (1 lack of efficacy, 1 withdrawn by physician, 2 lost to follow-up, 6 withdrew)
  + Note: Format varies by study; prioritize accuracy relative to the PRISMA diagram. If participants withdrew before the first dose, include this detail.

PRIMARY PATIENT DIAGNOSIS
+ E.g., MDD, TRD, life-threatening cancer with DSM-IV diagnosis for mood/anxiety/adjustment disorder.

OTHER
+ Include recorded past drug use not covered under psychedelic use (e.g., cannabis) in notes.
  + Example format: 'Recent use of cannabis or dronabiol: 42% intervention, 52% control, 47% all participants'
  + Separate multiple items in 'Other' with semi-colons.
+ Include notable SAEs or other significant information (e.g., death by suicide/cancer) in notes.

EXCLUSION CRITERIA BOXES
+ The following fields capture binary responses to common exclusion criteria. Enter 'yes' or 'no' based on the full exclusion criteria. If information is unavailable, enter 'missing'; if unclear, enter 'unclear'.
  + Were participants excluded for currently taking SSRIs?
    + 'Yes' indicates participants on SSRIs at intake were automatically ineligible (no taper option).
  + If participants were taking a psychiatric medication, did they have to taper off before participating?
    + 'Yes' indicates participants could be on medication at screening but required tapering before intervention.
    + If the answer to the first question is 'yes', enter 'n/a' here.
  + Were participants excluded for a personal history of psychosis/psychotic disorder/schizophrenia?
  + Were participants excluded for a family history of psychosis/psychotic disorder/schizophrenia?
    + Enter 'yes' if *any* exclusion based on family history exists, regardless of degree of relation.
  + Were participants excluded for **any** previous psychedelic use?
    + Enter 'yes' only if **all** participants were psychedelic-naive.
    + If exclusion was based on specific parameters (e.g., lifetime use limits), enter 'no', as some prior exposure might be permitted.
    + If *any* history or experience was allowed, enter 'no'.
  + Were participants excluded for a **current** alcohol/substance use disorder?

ANY NOTABLE POPULATION CHARACTERISTICS NOT CAPTURED ABOVE
+ Capture relevant participant details not covered elsewhere (e.g., co-morbidities).

BASELINE CHARACTERISTICS
+ *Many fields under baseline characteristics may need to be left blank, as reporting varies across studies.*
  + *Options exist for standard deviation or standard error; typically, only one is reported with the mean. Leave the unreported field blank.*

Psychiatric medication discontinuation/use:
+ Specify the type of medication (e.g., SSRIs) in the NOTES section if detailed in the paper.



## Interventions
*Overall Process*
+ Select the checkboxes next to both 'Intervention' and 'Control'.
+ For 'Group name' under each arm, enter the name used by the paper authors (should match 'Name of each arm' in Methods).
  + Example: "psilocybin group", "niacin group".
  + Also useful for crossover studies: "high dose 1st group", "low dose 1st group".
+ Hover over the intervention or control column to add additional arms if needed (e.g., for studies with multiple active doses).
  + This highlights the importance of accurately entering the 'Group name' for each arm.


NUMBER OF PARTICIPANTS ALLOCATED
+ Enter the number randomized into each group.

DRUG
+ May be the same (e.g., low dose as placebo) or different between intervention and control arms.

DOSE
+ Typically reported in mg or mg/kg.

NUMBER OF DOSES
+ Include only doses administered BEFORE the primary endpoint. (E.g., if an optional second dose occurs after the primary endpoint, enter '1').
+ For crossover studies, enter the number of doses received BEFORE crossover.

FREQUENCY
+ Enter the interval (days/weeks) between doses if multiple doses are administered.
+ Leave blank if only one dose.

MODE/ROUTE OF ADMINISTRATION
+ Use brief, standardized terms (e.g., "oral", "IV").

DURATION OF FOLLOW-UP/LAST REPORTED ENDPOINT
+ Specify in terms of days, weeks, or months.

SOURCE OF PSILOCYBIN/FORMULA
+ Enter the source/formulation used (e.g., 'synthetic psilocybin/Usona Institute', 'synthetic psilocybin/David Nichols', 'COMP360/Compass Pathways').

OTHER
+ Enter any other intervention/drug details not captured above.

## Outcomes
*Overall Process - Timepoints*
+ Note for Reviewer 2: Timepoints and outcomes tables will be pre-configured by Reviewer 1.
+ Select checkboxes only for outcomes intended for later analysis.
+ For outcomes not pre-listed, check an appropriate 'Additional Outcome' box (continuous or dichotomous).
+ In the "Describe outcomes" section (under 'Add reported name...'), enter the scale acronym used in the study.
  + *Exception: If using a pre-selected outcome where the reported name is identical to the desired entry (e.g., 'BDI'), and no further version specification is needed, enter '[acronym]_null' (e.g., 'BDI_null').*
  + The acronym should match an entry in the Methods fields "Change from baseline outcomes" or "Endpoint outcomes".
  + For response/remission, clearly specify the scale used for definition here.
  + If using an 'Additional Outcome', specify the outcome measure name here.
+ For each outcome, delete unused timepoints (likely most). Retain only timepoints where that specific outcome was measured in the study.
  + Different outcomes may have different measurement schedules. Specify timepoints per outcome scale.
  + Note: Include DOSE timepoints only if data were collected *on* the dosing day. Otherwise, dosing timing is captured in Methods -> Study Timepoints. (Consider keeping DOSE timepoints temporarily while entering reported times for timeline clarity, then delete before moving to results).
+ For remaining timepoints, click the edit icon and enter the actual timepoint (day, week, etc.) as reported in the paper under 'Add reported time'.
   + Maintain the exact format used in the paper; do not convert units (e.g., weeks to days) at this stage.
+ Account for 'sustained response' outcomes within a 'response' timepoint entry.
  + Use a 'follow-up' timepoint. In the timepoint description, use the format: "Weeks #-# Sustained Response". Specify the range as sustained response definitions often span multiple weeks.
+ Multiple response/remission outcome options exist (Response 1, Response 2, etc.) for studies with multiple definitions (e.g., anxiety vs. depression remission).
  + Specify the scale used in 'Add reported name' for each (e.g., "HAM-A Response"). Ensure the definition method is detailed in the corresponding Methods field.
  + Adjusted response/remission options (Adjusted Response 1, etc.) are available for reporting adjusted data (e.g., adjusted odds ratios). Use these when applicable, adding '(adjusted)' to the reported name (e.g., 'HAM-A Response (adjusted)'). Edit the results table format later as needed.

SCALE
+ Use the "Scale" field in results to enter the reference cited in the paper for the scale (e.g., Beck 1998).

RANGE
+ Enter the range of possible total scores for the outcome measure.

UNITS
+ Leave blank for most depression/anxiety survey outcomes.

DIRECTION
+ "Lower is better" indicates lower scores represent improvement (e.g., less depression).

DATA VALUE
+ Select 'Change from baseline' if applicable; this can also be configured when editing the results table.

NOTES
+ Use the "Notes" field at the bottom of the results table to specify if the entered number is adjusted or unadjusted.
  + Results are often unadjusted. Adjusted values (e.g., least squares mean) should be noted here.

*BASELINE OUTCOMES*
+ The "Baseline Outcomes" selection provides a workaround for baseline data reported in a different format than subsequent timepoints (e.g., endpoint vs. change from baseline). Reporting is idiosyncratic:
+ Each 'timepoint' (Baseline 1-20) represents a field for baseline data of a different outcome measure. Select the required number of baseline timepoints and label each with the corresponding outcome measure name (e.g., 'GRID-HAM-D'). This label appears in parentheses in the results table.
+ The results table will then allow entry of baseline data for each selected outcome measure in the format reported in the paper.

*COLLAPSED OUTCOMES*
+ For studies (especially waitlist-controlled) reporting results collapsed across groups (e.g., immediate vs. delayed treatment), use the "Collapsed Outcomes" section, as standard results tables separate intervention/control data.
+ Select the required number of "Collapsed Outcomes" options (1-12). Under 'as reported' for each, enter the outcome measure name for the collapsed data.
  + Use the format "[*Outcome Name*] Collapsed" (e.g., "QIDS-SR Collapsed") as Covidence requires unique outcome descriptors.
+ Select timepoints as usual (those where collapsed data are reported).
+ Repeat for all outcomes with collapsed data.
+ In the results section, edit the table format to 'effect estimate (arm vs. reference arm)' to allow a single entry per timepoint (ignore intervention/control row headers). Add a custom "Reported As" field matching how collapsed results are reported.

## Results data
*Overall Process*
+ Click the edit icon for each results table to configure format. Specify:
  + REPORTED AGAINST: Choose 'arm' or 'reference arm (effect estimate)'.
  + REPORTED AS: **Crucial field.** Attempt to use "Standard" options first. Custom options can be created if necessary and will reappear in the list. Reviewer 2 reports data according to the format set by Reviewer 1.
  + (Outcome Group & Outcome Reporting can be left blank).
  + DATA VALUE: Specify 'Change from baseline' or 'Endpoint'; can also be set in the outcomes table configuration.
+ If results for a timepoint are missing (not reported in text/tables, or unextractable from graphs), click the 'missing data' tag button. This distinguishes unreported data from incomplete extraction.
+ If data are reported in multiple formats, prioritize the format closer to raw data.
  + If both mean and mean difference are reported, enter the mean.
  + If both effect estimates and number/percentage of participants (esp. for response/remission) are reported, enter the number/percentage.
+ Covidence results fields accept only numbers. If reporting requires characters (e.g., p < 0.001), enter the numerical part ('0.001') and add a note in the results Notes section specifying the exact reported value ('p < 0.001').

## Completing extraction
+ When finished, navigate to the "Summary" tab and click "Complete".
  + Do not click Complete until the *entire* data extraction is finished and ready for comparison during the Consensus stage.



# **Consensus Stage**
*Overall Tips/Process*
+ Covidence automatically flags identical responses. Manually review and select the final response for non-identical or near-identical entries where automatic flagging fails.
+ To finalize a response, either click the desired reviewer's box or edit/combine responses directly in the 'Consensus' box.
+ After resolving straightforward discrepancies, dedicate time for both reviewers to discuss challenging or ambiguous aspects of the extraction. Reviewers should maintain a system for noting questions/confusions during individual extraction for discussion during consensus.
+ If consensus cannot be reached between Reviewer 1 and Reviewer 2, involve a third reviewer/supervisor.

*Style Review*
+ After content consensus, perform a formal "style review" to ensure syntax and format strictly adhere to this SOP.


# **WebPlotDigitizer Extraction & Consensus**

For papers presenting data solely or partially in figures, use WebPlotDigitizer.
+ Reviewer 1 completes data extraction from figures using [WebPlotDigitizer](https://automeris.io). Instructions [here](https://automeris.io/docs/digitize/). Process involves calibrating axes and manually clicking data points.
  + Note: WebPlotDigitizer outputs coordinates based on clicking order; click points sequentially along the x-axis.
  + Reviewer 1 obtains x/y coordinates for effect size data points (typically means), updates the Notion database, and adjusts x-coordinates based on study timepoints using judgment based on the study context. R1 also acquires coordinates for error bar endpoints and manually calculates SE or SD (by subtracting lower bar value from mean, or mean from upper bar value).
  + R1 must verify from the figure caption whether error bars represent SD or SE and note this in the Notion database.
+ Reviewer 2 reviews the adjusted coordinates (mean and error bar endpoint) by visually assessing reasonableness. If a point seems unreasonable, R2 performs a full replication for that data point using WebPlotDigitizer.
+ Reviewer 2 also reviews the SD/SE calculation by re-calculating it from the mean and error bar values.
+ Once R1 and R2 agree on the data points listed in Notion and record progress, both reviewers enter the values into Covidence results. They then check the Covidence consensus page to ensure agreement and resolve discrepancies.
