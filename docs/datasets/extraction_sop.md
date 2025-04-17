# **SOP Document**

*SOP for full Covidence workflow on PSILODEP_Review*

# **Title and Abstract Screening Stage**
+ List of reasons that we want to exclude studies in initial title/abstract screening:
  + Studies the wrong psychedelic drug
  + Review articles or meta-analyses
  + Animal studies (non-human research)
  + Protocols
  + Comment/Perspective
  + Non-RCTs
  + Studies in healthy participants
  + Open-label studies - these are generally excluded. However, a randomized open-label study with waitlist-control DOES get included. If you cannot determine with certainty whether or not an open-label study has a randomization and control component then its best practice to push it to full-text screening to confirm.
+ You don't need to use tags at this screening stage or add any notes; anything included in the reasons above is grounds for excluding the study and not sending it to full text review.

 + List of reasons we want to push studies into full text review, but might be excluded later:
   + Re-analyses/mechanistic papers (i.e., neuroimaging papers, mediation analyses, reports on additional outcomes, follow-ups)
   + Papers that compare psychedelic drug with another treatment (e.g., SSRIs/escitalopram)
   + Corrections to articles that we have already or want to push into full text review; these can later be merged with the studies that they correct in the extraction stage.
   + RCTs that investigate the correct psychedelic drug's effect on any specific outcome (like alcohol use disorder, cancer, etc.); in full text review, we can then see if any of their secondary outcome measures assess mood or depression.
  
  + Otherwise, include the studies for full text review. You can use the notes section to note any odd edge cases not accounted for above.

# **Full Text Review**
+ As you do full text review, you must select a reason for each study you exclude. This is the current list of reasons to exclude a study, which can be updated here as needed:

  + Re-analysis/Secondary report
    + Re-analysis/secondary report should always be chosen only if this is the *only* reason that the study should be excluded. For example, if the study compares a psychedelic drug to escitalopram, you should choose 'Wrong comparator' instead of 'Re-analysis/Secondary report.' In essence, any of the below reasons supersede this re-analysis/secondary report reason.
  + Conference abstract - full text already included
    + There might be conference abstracts that would be excluded anyways for a different reason (and in this case, the full text would not already be included). In this case, the other reason (for example, if it was not an RCT) would supersede this conference abstract reason.
    + If the full text is not already included, but there is not another reason to exclude the conference abstract, leave in full text review for now and potentially follow-up with study authors.
    + Only push through conference abstracts at this stage if it reports on new info. If you already have the full text included with the same results from the conference abstract, exclude the conference abstract.
  + Wrong patient population (e.g., healthy, pediatric)
  + Wrong outcomes/no mood outcomes
  + Wrong intervention/drug
  + Wrong comparator (e.g., SSRIs)
    + Studies comparing psychedelic drug with SSRIs/escitalopram would fall into this category.
  + Not an RCT
    + Studies that are single-arm, non-randomized open-label studies would fall into this category.
  + Protocol/incomplete study
  + Non-English language
+ The reason must agree between both reviewers, or conflicts will need to be resolved later.


# **Data Extraction**

*The sections below are separated by headers corresponding to different tabs in Covidence's Data Extraction Tool. Read through entire doc before completing data extraction, and be sure to have a copy of the SOP handy during data extraction.*

| General Formatting: |
|:----------------------------------------------------|
|Our coding sheet parses multiple inputs via a semi-colon.<br>There are several places where group or time-point descriptions are used to link information from one place to another in our coding sheet.<br>Please be consistent/don’t make your own abbreviations for things like timepoints or arms (e.g. 6 wks vs 6 weeks or HD1 vs High-dose-1st). The best and simplest practice to keep consistency throughout the coding sheet is to use the identical names reported in the study.|

| General Overview of Data Extraction Process for Reviewer 1 vs. Reviewer 2: |
|:----------------------------------------------------|
|1. Both reviewers will complete the full identification section, full methods section, and full population section. The process does not differ between reviewers for these tabs. <br>2. For the **interventions** section, *Reviewer 1* will set up the interventions table as described below in the SOP, by setting up how many intervention or control arms are in the paper and writing the group names in the table. *Reviewer 2* will not set up the table, but will fill out the information that belongs in the table. <br>3. For the **outcomes** section, *Reviewer 1* sets up the entire outcomes table. *Reviewer 2* does not have to do anything in the outcomes tab, and they can ignore the outcomes section of this SOP. <br>4. For the **results** table, *Reviewer 1* will change the format and set-up the results table as specified in the SOP. *Reviewer 2* cannot change the format of the results table, but will fill out the table with the appropriate values from the paper.|

  
## Summary
| Tips for this section: |
|:----------------------------------------------------|
|1. The summary page is where you are able to click 'complete' once you are done with the full data extraction. This button does not appear in any other section, just in the summary page in the top right corner.<br>2. It is useful to also read the supplement/protocol/appendix provided with a paper. Some information that is especially likely to be found in the supplemental information include details about randomization, recruitment, inclusion & exclusion criteria, and data for additional timepoints aside from the primary endpoint if the primary endpoint is all that is reported in the main paper's tables and graphs.|

## Identification
| Tips for this section: |
|:----------------------------------------------------|
|1. Search for the study title on pubmed<br>2. From pubmed page copy the PMID, trial registry number, and the DOI.<br>3. Search the trial registry number in corresponding database (e.g. ClinicalTrials.gov)<br>
     

SPONSORSHIP SOURCE
+ Here you can write the funding/sponsorship source for a study; you can simply put the name of the institution.

COUNTRY
+ For the United States, write as "USA"
+ For the United Kingdom, write as "UK"
+ For the Czech Republic, write as "the Czech Republic"
+ For Denmark, write as "Denmark"
+ For Germany, write as "Germany"
+ For Ireland, write as "Ireland"
+ For the Netherlands, write as "the Netherlands"
+ For Portugal, write as "Portugal"
+ For Spain, write as "Spain"
+ For Canada, write as "Canada"
+ If there are multiple countries/study sites, separate out by semi-colons.

SETTING
+ This refers to the institution/study site. Be sure to specify if it’s a multi-site study. Covidence refers to this section as “The setting where the study was conducted, which could be a specific healthcare facility, community, or geographic region. This is important for understanding potential contextual factors.”
+ Things to include in setting if provided in the paper:
  + If it is a single-site study, mark it as 'single-site', or if it is a multi-site study, mark it as 'multi-site.'
  + If the dosing takes place in an institutional setting (this is the norm), write 'institutional setting'. Otherwise, mark 'other'.
+ Example format: 'multi site; institutional setting'

COMMENTS
+ Here list anything unusual or that did not fit into the other boxes.

AUTHOR'S CONTACT DETAILS
+ This is usually automatically filled in by Covidence, but you should at least double-check that what is automatically filled in is accurate.

START DATE & END DATE
+ Write as “Month Year”, i.e., “October 2007”
+ If a day is provided, write as "Month Day, Year", i.e., "October 5, 2007"
+ Use the date listed in the paper or protocol as the study start/end date. If it is not in the paper, you can search the trial registry number in corresponding database (e.g., ClinicalTrials.gov), and use the start/end date listed there.
+ If the paper provides both the date for the end of assessment, and end of data analysis, use the end date corresponding to the end of assessment (the end of the actual study involving participants).

DOI, TRIAL REGISTRY ID, & PMID
+ write just the number itself; i.e., don’t put DOI: or PMID: before the number itself
+ If it's a merged study, separate the DOIs out with semi-colons. The primary study should be listed first, followed by any secondary studies. Only the DOI box needs to contain information from both studies.

MERGED STUDY?
+ Write 'yes' if the study is a merged study in Covidence/from multiple papers. Write 'no' if the study just represents one paper.
+ If you included a correction/update to the paper, still answer 'yes' for this question, although there will not be actual new data to extract.
+ Merged study tips:
  1. The primary outcome to list in Methods section should be the primary outcome of the *primary* paper (often the first paper published; PO should match the pre-registered PO).
 
WHAT DO ADDITIONAL PAPER(S)ADD?
+ ONLY use this section if you answered 'yes' to the merged study box before it. Otherwise, leave it blank.
+ *If the only thing merged with your study is a correction to the original paper, ignore the following bullet points on format, and simply write 'Correction' in this box.*
  + If there is an added Correction in addition to a secondary paper, write '; Correction' to the end of your response, after the sentence in the structure of the format below.
+ *If the only thing merged with your study is a conference abstract that reports on something additional/not included in the full text, write 'Conference abstract - [description of what new results the conference abstract adds]'*.
  + If there is an added conference abstract in addition to a secondary paper, include this information after the secondary paper sentence, separated by a semi-colon.
+ Secondary papers that we will merge with the primary paper in Covidence will either have the same outcomes, but follow-up with more timepoints (i.e., a long-term follow up paper), or will include the same timepoints, but include additional outcomes. In this box, you MUST include a) a brief general description of what the paper adds, b) a list of either what the additional outcomes are (abbreviations can be used) and/or what the additional timepoints are. See below for format examples, where the italicized words can be replaced with the appropriate information from the study you are working on:
  + Example additional outcomes:<br>
      '*Goodwin 2023* expands upon *Goodwin 2022* by *adding additional self-report measures in addition to the original clinician-rated measures.* The additional outcome measures are: *GAD-7*, *QIDS-SR-16*, *PANAS*, *SDS*, *WSAS*, *EQ-5D-3L*, and *DSST*.'
  + Example additional timepoints:<br>
      '*Goodwin 2023* expands upon *Goodwin 2022* by adding additional follow-up timepoints after the original study timepoints. The additional study timepoints are: *6-months following the second dose*, and *12 months following the second dose*.'
  + Example both additional outcomes and additional timepoints:<br>
      '*Goodwin 2023* expands upon *Goodwin 2022* by adding both additional outcome measures and additional follow-up timepoints after the original study timepoints. The additional outcome measures are: *GAD-7*, *QIDS-SR-16*, *PANAS*, and *SDS*. The additional study timepoints are: *6-months following the second dose*, and *12 months following the second dose*.'

## Methods
DESIGN
+ By nature of our review, you should always select Randomized Controlled Trial here.
+ Mark the correct circle for parallel group or crossover design.

METHOD OF RANDOMIZATION
+ Be sure to include if it’s cluster randomization, etc. Some studies also include details about how randomization was generated, this would be good to include

METHOD OF RECRUITMENT
+ Online? Mail? Word of mouth? etc.

BLINDING
+ can be brief; simply put “double-blind,” “single-blind,” “open-label,” etc.

WHO WAS BLINDED?
+ Can be brief; usually for a double blind study this includes at least the participants & study staff/clinicians/who administered the drug.

TYPE OF THERAPY
+ Simply put ‘Other’ unless the paper specifies that it uses a standardized type of treatment such as CBT, DBT, ERP, etc. Non-traditional or drug-specific protocols (such as the “set and setting protocol” in Raison 2023 or the MAPS protocol used in many MDMA trials) should be listed if used.

FREQUENCY OF THERAPY SESSIONS
+ Does not need to be detailed; give a rough sense of how much therapy each participant received/at what general timepoint and if it was standardized between arms
  + Example single-dose format: 3 weekly sessions before dosing; 3 weekly sessions post dosing.
  + Example multi-dose format: 3 weekly sessions before dosing; 3 weekly sessions between doses; 3 weekly sessions after dosing.

WHO PERFORMED CLINICAL ASSESSMENTS?

+ The most-common scenarios are:
  
| Answer                       | Explanation                                                                 |
|:-----------------------------|:----------------------------------------------------------------------------|
| 3rd-party independent raters  | Most common in industry-sponsored studies - an attempt to mitigate bias in clinical assessments. |
| unspecified                  | Most common in academic studies - generally presumed to be study staff.     |
| independent study staff       | Study staff who have not been involved in the administration of therapy.    |
| non-independent study staff   | Study staff who have been involved in the administration of therapy.        |


+ NOTE: This question is not asking whether the instruments are clinician administered or self-report. In essence we want to know who asked the questions or handed participants the questionnaire.
+ For older or academic studies, this might not be reported as clearly. Check the 'assessments' section of the study protocol.

CHOSEN PRIMARY OUTCOME MEASURE
+ Use the abbreviation for the primary outcome measure, matching its name in the outcomes table.
+ If there are more than one primary outcome measures, list them later in 'all primary outcome measures,' and select one primary outcome measure based on the following:
  + Choose the measure that most closely relates to the outcome that is the focus of your review; i.e., for psilocybin and depression, pick a depression outcome over an anxiety outcome measure.
  + When selecting the chosen measure, evaluate which measure is most often measured in other studies, prioritizing clinician-administered over self-report, and independent administrations of the clinician-administered outcomes over unspecified or study staff administration.
  + This selection process should involve discussion among multiple team-members and the decision and reasoning should be documented on the study's notion page.

SAFETY AND PHYSIOLOGY MEASURES
+ List all safety and physiology related measures collected, separated by a semi-colon.
+ Use the exact name of the measure or survey instrument if provided.
+ If there are sub-outcomes under any measure, it doesn't hurt to list out the sub-outcomes to provide more detail as well (or the more detailed response can be selected in the consensus stage).
+ Acute drug effects (ASC/MEQ) and longer-term emotional/spiritual/personality scales can be included in this box. However, anything that is an explicit mood scale (related to depression/anxiety, etc.) should be listed under 'all other mood & secondary outcome measures'.

ALL OTHER MOOD & SECONDARY OUTCOME MEASURES
+ Here, list all of the remaining outcome measures that are not the primary outcome measure nor are related to safety and physiology, as these will have been covered above.
+ You can use the abbreviations for each outcome measure, separated by a semi-colon (i.e., MADRS; BDI; STAI)
  + Note that for STAI in particular you can just list 'STAI' here and later in results report STAI-Trait, STAI-State, STAI-Total, etc.
+ Many of the outcomes here will not be reported in the results table/are not reported in the study in detail, but it is still useful to make note of all relevant outcome measures collected for reference.
+ Response & remission are often listed as secondary outcome measures, but do not need to be listed here given that they use scales which would already be included here.

STUDY TIMEPOINTS
+ DON’T calculate anything at this point; keep it how it was written in the study. Separate by semi-colons.
+ Other info to potentially include depending on the study:
  + When the blind was broken
  + When crossover occurred
  + When doses were administered!!!
+ Info that does not need to be included in this box includes when therapy sessions occured, as this is already note in the 'frequency of therapy sessions' box.
+ When deciding what to include in this box, it is helpful to think that the goal is to track the times of doses and survey instruments administered, in line with some of the studies that provide organized graphical timelines. The goal is to use this box as a reference of relative timepoints to contextualize the timepoints in the outcomes/results tabs.
+ Example generic format:
  'Study Timepoint (Covidence timepoint): Description;' OR 'Study Timepoint: Description;'*
    + *The Covidence timepoint in parentheses will not be available for every study timepoint, just those for which we are reporting outcomes (i.e, typically the dose timepoints will not have a corresponding Covidence timepoint)
+ Example format (from Griffiths 2016 paper):
  Day 0: Baseline; Month 1: Dose 1; 5 weeks after session 1 (Post-first dose 1): data assessment; 5 weeks after session 1: Dose 2; 5 weeks after session 1: Crossover; 5 weeks after session 2 (Post-second dose 1): data assessment; 6 months (Follow-up 1): Follow-up assessment
+ Example format (from Goodwin 2022/2023 papers):
  Day -1: Baseline; Day 1: Dose 1; Day 2 (Post-first dose 1): Follow-up at clinic assessment; Week 1 (Post-first dose 2): Follow-up at clinic assessment; Week 2: Follow-up at clinic assessment; Week 3 (Post-first dose 3): Follow-up at clinic assessment; Week 6 (Post-first dose 4): Follow-up remote assessment; Week 9 (Post-first dose 5): Follow-up remote assessment; Week 12 (Post-first dose 6): Follow-up at clinic assessment

OTHER
+ Include any other information not covered in pre-specified boxes in Methods.

NAME OF EACH ARM
+ Write what the paper authors refer to each group as/how it is referenced & mentioned in the study. (This should be the same as 'group name' in Interventions section).
  + For example, the intervention group might be termed “psilocybin group” and the control group might be called “niacin group” in a particular study.
+ It is important to use this exact group name as reported in the study/as specified here throughout the rest of the data extraction template when referring to each arm.

STATISTICAL ANALYSES
+ Here, copy/paste relevant statistical analysis methods described in the paper.
+ The relevant information to include here consists of the 1-3 paragraphs that describe the modeling methods used to adjust for baseline characteristics, impute missing data, and test for significance.

SUPPLEMENTAL ANALYSES
+ Here, include any additional analyses that are included in the paper or more typically, the supplement, that might be interesting to analyze later, but which you do not report on in the results of this Covidence analysis. This might include analyses where the authors subgroup the results based on a particular condition, such as antidepressant use, prior psychedelic use, baseline severity, or Per Protocol (PP) analyses.

MISCELLANEOUS DETAILS
+ Add any notable details on methods or design that do not fall into the above categories. Sometimes this will be blank. This box can also be used to capture misc. details we decide we want to extract at later stages.
+ In general, it is good practice to utilize this 'miscellaneous details' box rather than writing things in the notes section.

ADJUSTED VALUE USED
+ Only use this box if the paper reports their primary results as adjusted values. In the outcomes Notes box (see Outcomes section below), you will note whether the value is adjusted or unadjusted for each scale, but it is important to then come back here to the Methods section to specify in more detail.
+ For example, if the QIDS-SR score uses the least squares mean, you can write "QIDS-SR: least-squares mean"
+ Parse separate outcome measures with a semi-colon, i.e., "QIDS-SR: least-squares mean; MADRS: least-squares mean"

IS PRIMARY ANALYSIS ON INTENT-TO-TREAT (ITT) OR PER-PROTOCOL (PP) POPULATION?
  + If primary analysis is done on intent-to-treat population, write 'ITT.' If it's on per-protocol population, write 'PP'.
  + If it is unclear in the study whether the analysis was done on ITT or PP population, write 'unspecified'.

CHOSEN PRIMARY ENDPOINT
+ The primary endpoint should match one of the time-point descriptions in the outcomes table (See Outcomes -> Overall Process). Both should be in accordance with the timepoint description in the paper. The primary endpoint should be the primary endpoint of the *main paper*.
+ If the primary endpoint is not obvious or explicitly stated in the paper, then look at the pre-registered options (go to the clinical trial registry if possible) and choose the timepoint that is closest to the average timepoint of trial designs in other studies.
+ This selection process should involve discussion among multiple team-members and the decision and reasoning should be documented on the study's notion page.
+ If you have chosen a timepoint according to the points above, then make sure to include all primary endpoints listed in the paper/pre-registered options in the 'All primary endpoints' box below.

ADJUSTED OUTCOMES
+ List all of the outcomes that are reported as adjusted values in outcomes/results. Separate each outcome (you can use their abbreviations) by a semi-colon.
+ Don't list response/remission outcomes in this box.

UNADJUSTED OUTCOMES
+ List all of the outcomes that are reported as unadjusted values in outcomes/results. Separate each outcome (you can use their abbreviations) by a semi-colon.
+ Don't list response/remission outcomes in this box.

CHANGE FROM BASELINE OUTCOMES
+ List all of the outcomes that are reported as a change from baseline (rather than endpoint) in outcomes/results. Separate each outcome (you can use their abbreviations) by a semi-colon.
+ Change from baseline outcomes are those that are reported as a difference from the baseline measure (for example, if the psilocybin intervention worked, most depression scores will be a negative number reflecting a lower depression score compared to baseline following psilocybin intervention).
+ Don't include response/remission outcomes in this box.

ENDPOINT OUTCOMES
+ List all of the outcomes that are reported as an endpoint (rather than change from baseline) in outcomes/results. Separate each outcome (you can use their abbreviations) by a semi-colon.
+ Endpoint outcomes are those that are reported as raw scores for that timepoint, rather than as a difference from baseline.
+ Don't include response/remission outcomes in this box.

HOW IS RESPONSE DEFINED?
+ Here, note how response is defined in the study and its corresponding outcome name in outcomes/results.
  + Example: 'Response 1: 50% or greater reduction in BDI at a particular assessment point relative to baseline'
+ If there are multiple response outcomes/it is defined in multiple ways, indicate which response outcome it corresponds to in the outcomes/results section, and separate each definition by a semi-colon.
  + Example format: 'Response 1: 50% or greater reduction in BDI at a particular assessment point relative to baseline; Response 2: 50% or greater reduction in HADS-D at a particular assessment point relative to baseline'
+ If response is not an outcome for this study, write 'n/a' in this box.

HOW IS REMISSION DEFINED?
+ Here, note how remission is defined in the study and its corresponding outcome name in outcomes/results.
  + Example: 'Remission 1: 50% or greater reduction in depressive symptoms plus HADS D ⩽7'
+ If there are multiple remission outcomes/it is defined in multiple ways, use the same format as specified in the 'how is response defined?' box, separating by a semi-colon.
+ If remission is not an outcome for this study, write 'n/a' in this box.

DATA FROM WEBPLOTDIGITIZER
+ Here, list the data that you have recorded in the results section that you obtained from uploading figures to the WebPlotDigitizer software.
+ Include the outcomes, timepoints, and statistics if relevant: 'Outcome1: Timepoint1 (stat1, stat2), Timepoint2 (stat1); Outcome2: Timepoint1 (stat1, stat2), Timepoint2 (stat1, stat2), Timepoint3 (stat1, stat2)"
  + Example format: "MADRS: Day 2 (mean, SD), Day 14 (mean, SD); BDI: Day -1 (mean, SD), Day 14 (mean, SD), Day 21 (mean, SD)"

DATA FROM CONTACTING AUTHORS
+ Here, list the data that you have recorded in the results section that you obtained from contacting authors via email.
+ Include the outcomes, timepoints, and statistics if relevant, in the same format listed above for the 'Data from WebPlotDigitizer' box.

ALL PRIMARY ENDPOINTS
+ Here, list all primary endpoints pre-registered/listed in the paper.
+ There might be only one primary endpoint listed, in which case the answer to this box will be the same as the 'chosen primary endpoint.'

ALL PRIMARY OUTCOME MEASURES
+ Here, list all primary outcome measures as pre-registered/listed in the paper.
+ There might be only one primary outcome measure listed, in which case the answer to this box will be the same as the 'chosen primary outcome measure.'

ADVERSE EVENTS
+ Briefly describe adverse events as listed in the study. Possible information to include if available in the study, to separate by semi-colons:
  + Number or percentage of AEs (can separate by intervention, control, and total if provided)
    + Example format: 'Number of AEs: intervention = 13, control = 5, total = 18'
  + Number or percentage of serious AEs
  + List of AEs (i.e., 'AEs included headache, nausea, and dizziness')
  + If there are SAE's (serious AEs), give the number in each arm following the same format as above for AEs. 
  + List of serious AEs


## Population
INCLUSION/EXCLUSION CRITERIA
+ Directly copy/paste from protocol. Delete bullet points. Separate lines by adding a semicolon to the end of each line.

GROUP DIFFERENCES
+ ‘n/a’ for most studies. If any group differences are noted, whether due to inclusion/exclusion or randomization, list them here.

TOTAL SAMPLE SIZE
+ The number of participants randomized.

NUMBER OF WITHDRAWALS
+ Give the total number for each arm throughout the study. Arms should be named based on the group name given in the Interventions table.
+ The total number of withdrawals = the number of participants excluded from per-protocol analyses.
+ If it is a crossover study, also include whether the withdrawals were before or after crossover (see example format below).
  + Example formatted input (non-crossover study): “High-dose-1st: 4; Low-dose-1st: 6”
  + Example formatted input (crossover study): "immediate treatment group: 2 total, 1 pre-crossover, 1 post-crossover; delayed treatment group: 1 total, 0 pre-crossover, 1 post-crossover"
    + Be sure to include the total withdrawals in each group, then break the total number down as pre-crossover and post-crossover numbers separated by a comma. Groups/arms will be separated by a semi-colon still.

PRISMA WITHDRAWAL DETAILS
+ Write the info as it is described in study, usually displayed in a flow diagram, staying loyal to how it is written in the study; include the arm, n, reason.
+ Example format for Goodwin 2022:
  + 25-mg group: 79 were randomized, 5 discontinued (2 had adverse event, 1 was lost to follow-up, 2 withdrew); 10-mg group: 75 were randomized, 9 discontinued (1 had lack of efficacy, 2 had adverse event, 6 withdrew); 1-mg group: 79 were randomized, 10 discontinued (1 had lack of efficacy, 1 was withdrawn by physician, 2 were lost to follow-up, 6 withdrew)
  + Note that format will not be exactly the same for each study; prioritize being loyal to how it is written in the PRISMA diagram for that study. At least one paper has noted that some participants have withdrawn before receiving the first dose. If this is the case, be sure to include this in your PRISMA withdrawal details description.

PRIMARY PATIENT DIAGNOSIS
+ Ex: MDD, TRD, life-threatening cancer and DSM-IV diagnosis for a mood/anxiety or related adjustment disorder, etc.

OTHER
+ Include any past drug use recorded that was not included under past psychedelic use (i.e., cannabis use) in notes.
  + Example format: 'Recent use of cannabis or dronabiol: 42% intervention, 52% control, 47% all participants'
  + Separate out multiple things you want to record in the 'Other' section by semi-colons.
+ Include any notable SAE’s or other notable information (ex. death by suicide/cancer in Griffiths 2016) in notes.

EXCLUSION CRITERIA BOXES
+ The following boxes after 'Other' are meant to capture binary yes/no responses to common exclusion criteria for later use in analyses. Write 'yes' or 'no' to the following questions after looking at the full exclusion criteria for the study (if the information cannot be found, write 'missing', if the info is unclear write 'unclear'):
  + Were participants excluded for currently taking SSRIs?
    + Answering 'yes' to this question indicates that participants were not given the opportunity to taper off of the medicine; during intake, if they are on SSRIs, they are automatically ineligible.
  + If participants were taking a psychiatric medication, did they have to taper off the medication before partaking in this study?
    + Differing from the first exclusion question, if you answer 'yes' to this question, this means that during intake/screening participants could have been on SSRIs, but they must taper off of them before actually participanting in the study and receiving the intervention.
    + If you answered 'yes' to the first question, then you can list 'n/a' for this response.
  + Were participants excluded for having a personal history of psychosis/psychotic disorder/schizophrenia?
  + Were participants excluded if they have a family history of psychosis/psychotic disorder/schizophrenia?
    + Write 'yes' in this box if there is any exclusion based on family history, no matter the specifics/if it is a first-degree or second-degree relative.
  + Were participants excluded for **any** previous psychedelic use?
    + Only answer 'yes' to this question if **all** participants included in the study are psychedelic-naive.
    + For example, if a study excludes based on lifetime use or specific parameters of using psychedelics, you would answer 'no' to this question, because some participants could have had some exposure to psychedelics before that didn't fit the specific criteria for exclusion.
    + If there is any history of psychedelic use permitted, or any psychedelic experience allowed, then you should answer 'no' to this question.
  + Were participants excluded for having a **current** alcohol/substance use disorder?

ANY NOTABLE POPULATION CHARACTERISTICS NOT CAPTURED ABOVE
+ This box is meant to capture any other relevant details about the participants not already covered (i.e., co-morbidities, etc.)

BASELINE CHARACTERISTICS
+ *In general, lots of the boxes under baseline characteristics will likely have to be left blank. Not all studies report on the same population characteristics.
  + Also, there are options for reporting either the standard deviation, or standard error. Only one will probably be reported with the mean, so leave the other one blank.

Psychiatric medication discontinuation/use:
+ Specify in the NOTES section what type of medication, if it was specified in the paper (i.e., SSRIs)



## Interventions
*Overall Process*
+ Mark the checkboxes both next to intervention and next to control.
+ For ‘group name’ under each arm, write what the paper authors refer to each group as/how it is referenced & mentioned in the study.
  + For example, the intervention group might be termed “psilocybin group” and the control group might be called “niacin group” in a particular study.
  + This is also helpful for crossover studies, i.e., “high dose 1st group” vs. “low dose 1st group,” for example.
+ If you hover over either the intervention or control column, you can add additional intervention or control arms.
  + This is helpful, for example, for studies that might have two or more intervention groups testing different active doses of the drug.
  + This is also why it is important to add the ‘group name’ under each arm. 


NUMBER OF PARTICIPANTS ALLOCATED
+ Refers to the number of participants who were randomized into each group

DRUG
+ The drug might either be the same (i.e., when a low dose is used as a placebo), or a different drug for the intervention vs. control group.

DOSE
+ Typically reported in mg/kg

NUMBER OF DOSES
+ Only include doses BEFORE the primary endpoint. For example, if a study has an optional second dose after the primary endpoint, you would still put '1' for number of doses.
+ For crossover studies, the number that should go in here is the number of doses they received BEFORE crossover.

FREQUENCY
+ The amount of days/weeks in between the doses if there are multiple doses
+ If there is only one dose, you can leave this box blank.

MODE/ROUTE OF ADMINISTRATION
+ Keep language brief & standardized here: i.e., “oral” or “IV”

DURATION OF FOLLOW-UP/LAST REPORTED ENDPOINT
+ Write in terms of days, weeks, months

SOURCE OF PSILOCYBIN/FORMULA
+ Add the source/formulation of psilocybin used here. Common examples include 'synthetic psilocybin/Usona Institute', 'synthetic psilocybin/David Nichols', or 'COMP360/Compass Pathways'. 

OTHER
+ Write any other details here about the intervention/drug that was not captured in the above categories.

## Outcomes
*Overall Process - Timepoints*
+ For the seond reviewer, this detail will be irrelevant, as the timepoints and outcomes table will already be set up by the first reviewer.
+ Using the check boxes, select only the outcomes in the study that you would like to analyze later
+ For any outcome that is not listed as a possible outcome to check in outcomes already, check one of the ‘Additional Outcome’ boxes, making sure you check one that corresponds to the type of outcome it is (continuous or dichotomous).
+ In the “describe outcomes” section, underneath the large bold column heading where it prompts ‘Add reported name…’, write the scale acronym.
  + *Note that this is not applicable for studies in which the outcome name will be the exact same as what you would write in 'add reported name' (i.e., if you are using a pre-selected outcome that already lists the measure like 'BDI' rather than 'Additional Continuous Outcome 1' and there are no further version specifications that you would want to report in the name). In these cases, in 'add reported name,' write [acronym]_null (for example, 'BDI_null').*
  + This should be the acronym used in the study for the outcome, and it should match exactly one of the acronyms listed in the methods boxes "Change from baseline outcomes" or "Endpoint outcomes"
  + For response and remission outcomes, it is especially important in this describe outcomes section to specify the acronym for the scale that is used to define response and remission.
  + If you are using an ‘Additional Outcome’ box, this description heading is where you would specify what that additional outcome is!
+ For each outcome, delete the timepoints you are not using (this will probably be a significant amount/most of the timepoints). You want to be left with only the timepoints for which the authors of that specific study recorded that specific outcome measure.
  + Note that different outcome measures might have been recorded at different timepoints or some might have been more frequently recorded than others; specify the timepoints for that specific outcome scale.
  + Note: Only include the DOSE timepoint if data is actually being collected on the day of the dosing session; otherwise, this timepoint info will be captured under study timepoints in Methods, and you can delete the “DOSE 1” timepoint, for example. It might be helpful, however, to keep this timepoint briefly as you are adding reported times for the timepoints to keep track of the timeline, but delete this before you go to results.
+ For the timepoints that are remaining, click the edit button icon, then where it prompts ‘Add reported time,’ specify the actual timepoint (day, week, etc.) for the study you are working with.
   + Stay loyal to how the timepoint is written exactly in the paper - do not, at this point, convert or calculate weeks into days, etc.
+ If the study includes a ‘sustained response’ outcome, you can account for this in a ‘response’ timepoint.
  + Use one of the ‘follow-up’ timepoints. In the timepoint description, use the following format: “Weeks #-# Sustained Response”. The reason the weeks are a range is because sustained response often by definition needs to be sustained across the weeks, rather than just having a response just at a later follow-up week, so make sure you specify this.
+ There are multiple response and remission outcome options.
  + Some studies may have a couple of response/remission outcomes defined in different ways (i.e., one defined by anxiety remission & another defined by depression remission). This is why there are multiple response & remission outcomes - Response 1, Response 2, etc. Be sure to specify in the ‘Add reported name’ for these ones what scale is used to define response/remission, adding "Response" or "Remission" after the acronym (i.e., “HAM-A Response”). Be sure to also specify exactly how response/remission is defined in the corresponding methods box.
  + There are also response and remission outcome options for reporting the adjusted versions of these values - Adjusted Response 1, Adjusted Response 2, etc. For example, many papers provide not only n/N for response and remission, but also present the adjusted response and remission data (i.e., odds ratio adjusted for baseline characteristics, etc.). In these cases, use one of the additional adjusted response/remission boxes, and in the 'Add a reported name' description write again what scale was used, adding '(adjusted)' at the end of that same acronym that should be in the corresponding Response 1, Response 2 outcomes (i.e., 'HAM-A Response (adjusted)'). You can later edit the results table such that the adjusted response or remission outcome is reported in the proper format.

SCALE
+ Use the “scale” box in results to write the reference cited in the paper for that scale (e.g. Beck 1998)

RANGE
+ This is the range of possible total scores for that outcome measure.

UNITS
+ For things like depression/anxiety surveys that will most likely be the outcomes you select, you can leave the units blank.

DIRECTION
+ "Lower is better" would mean, for example, that a low score means less depression.

DATA VALUE
+ If the data is reported as a change from baseline, be sure to select that option; this can also be reconfigured in the 'edit' section of the results data.

NOTES
+ Use the “Notes” box in results at the bottom of the table to note if the number give is adjusted or unadjusted.
  + More often than not, the results are unadjusted, but if results are reported as least squares mean, for example, this would be an adjusted value.

*BASELINE OUTCOMES*
+ The "Baseline Outcomes" option to select for an outcome is the way we have been able to work-around reporting baseline outcomes that are reported differently/in a different format than the other timepoints (e.g. where outcomes are reported as a change from baseline). As such, the reporting for this outcome is a bit idiosyncratic:
+ Each 'timepoint' is not a timepoint, but rather will be space to put the baseline data for different outcome measures. The timepoint options for this 'baseline outcomes' outcome are Baseline 1-20. Click on each baseline timepoint (can use however many you need to report for each outcome measure), and label it with the name of the outcome measure that will go in that box (e.g. 'GRID-HAM-D'). This will show up in parentheses in the results table.
+ In results, you will then have a table where you can report on all of the baseline timepoints for outcome measures in the correct format as listed in the paper.

*COLLAPSED OUTCOMES*
+ For waiting list controlled studies especially, you might run into a case in which the results are collapsed across intervention and control groups (i.e., immediate treatment and delayed treatment groups). However, the results tables are built such that results for the intervention and control groups are reported separately. As such, the "Collapsed Outcomes" section is our work-around to report any collapsed results for the same outcomes.
+ You should see the option for Collapsed Outcomes 1-12. You can use as many of these as you need by selecting the checkbox next to the options, and in the "as reported" section under the column for that option, note which outcome measure you are reporting the collapsed values for.
  + Since Covidence does not allow you to use the same name for an outcome where you can write more details underneath the column header, you can write each outcome as "[*Outcome Name*] Collapsed", i.e., "QIDS-SR Collapsed"
+ Select timepoints as normal (whichever timepoints are reported as collapsed data).
  + Repeat this process for however many outcome variables you want to report the collapsed data on.
+ In the results section, you can then edit the Results table such that it's reported as an effect estimate (arm vs. reference arm) in order to allow for only one box per timepoint (ignore the row header that will say intervention vs. control to the side), and add a custom "Reported As" field to correspond to the way the collapsed results are reported.

## Results data
*Overall Process*
+ If you click the edit icon for each results table, you can change the format of the table. Be sure to specify:
  + REPORTED AGAINST: arm or reference arm (effect estimate)
  + REPORTED AS is also a **very important** one to change depending on your study. It is a good idea to try to stick to the “Standard” options, as they should capture most study designs. Sometimes, you might have to make a custom option, which will then show back up later in your list of options. The second reviewer will report the data in accordance to how the first reviewer edited the results tables.
  + (Outcome Group & Outcome Reporting can leave blank)
  + DATA VALUE: Report if this is a change from baseline or Endpoint; can also be configured in outcomes table.
+ If any timepoint in the results table does not have the actual results reported in the study or protocol, or in the case this information is in a graph that does not provide exact values, click the 'missing data' tag button in results. This helps indicate that this information cannot be found/is not reported, rather than left blank because it is incomplete.
+ It is possible that data could be reported in a paper in multiple different formats, but the results table in Covidence only allows for inputting one format. In general, it is best to select the format that is closer to raw data/not converted. Please see the notes below for additional guidance:
  + In the case that results are reported as a mean and also as mean difference, report the basic mean.
  + In the case that results (particularly for response/remission outcomes) are reported as effect estimates and also as number or percentage of participants, report the number/percentage of participants.
+ Covidence does not allow you to input anything other than numbers into the results boxes. In the case that you are reporting a p-value or other value where a character is needed (i.e., if it is reported as p < 0.001), then you can simply put '0.001' in the results box, and make a note in the Notes section of results that the actual value reported is < 0.001.

## Completing extraction
+ When done with data extraction, go back to "Summary" tab and click "Complete".
  + Refrain from clicking Complete until you are finished with the *entire* data extraction and are ready to compare your answers with the other reviewer in the Consensus stage.



# **Consensus Stage**
*Overall Tips/Process*
+ Covidence automatically will mark where the answers of the two reviewers are identical, but there might be some cases in which the answers are identical or almost identical and you will have to manually select which response you would like to choose.
+ To decide on the response, you can either select which of the two reviewers' responses you would like to be your final response by clicking on that reviewer's box, or you can combine both responses or edit the final response based on your deliberations by typing into the 'Consensus' box directly.
+ After going through the more straightforward responses, also set aside a time for both reviewers to discuss anything particularly challenging or confusing about that particular study's extraction. Both reviewers should have some system for marking their questions or thoughts about confusing cases while they are going through extraction; during consensus these questions and thoughts should be brought up.
+ If Reviewer 1 and Reviewer 2 cannot decide/come to a consensus about a particular result, then it is time to loop in a third reviewer/supervisor.

*Style Review*
+ Following the steps for consensus with respect to the content, at the last stage both reviewers should go through a fairly formal "style review" to check that the syntax and extraction format corresponds exactly to how it is specified in the SOP.


# **WebPlotDigitizer Extraction & Consensus**

Some data in the papers we want to extract from will have their data entirely in figures rather than in tables or numbers that we can readily extract. Some papers might have some data in tables, and other data only in figures. In these cases, we will use the software WebPlotDigitizer.
+ Reviewer 1 will complete data extraction from figures using [WebPlotDigitizer](https://automeris.io). The instructions to use this tool are [here](https://automeris.io/docs/digitize/), which consist of calibrating the axes and then manually clicking on data points to acquire their x and y coordinates.
  + An important note is that WebPlotDigitizer will give the coordinates based on the order in which you manually click on data points, so be sure to click the data points sequentially.
  + Reviewer 1 will get the x and y coordinates of the effect size data points (typically the mean), then update the Notion database and within Notion use common sense to adjust the x coordinates given the timepoints used in the study. Reviewer 1 will also acquite the x and y coordinates of the top or bottom of the error bars, then manually calculate standard error or standard deviation by subtracting the value for the bottom of the error bar from the acquired mean value, or the value for the mean from the value for the top of the error bar.
  + R1 should be sure to check with the figure caption from the original paper to verify if the error bars represent the standard deviation or standard error, and note this in the Notion database.
+ Reviewer 2 will review both the common-sense adjusted x and y coordinates for the mean and value for the top of the error bar by visually assessing if the data points acquired by Reviewer 1 are reasonable. If they find a data point that does not appear reasonable, they will do a full replication by uploading the image to WebPlotDigitizer and following the process for Reviewer 1 for that data point for that image.
+ Reviewer 2 will also review the standard deviation/standard error calculation by re-doing the manual calculation of subtracting the mean value from the value for the top of the error bar.
+ Once Reviewer 1 and Reviewer 2 agree on the data points listed in Notion and record their progress in the Notion database, both Reviewer 1 and Reviewer 2 will input these values into their appropriate place in results in Covidence. Then, R1 and R2 will look at the consensus page in Covidence to make sure their numbers match and resolve any discrepancies.
