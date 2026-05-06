# SVEF - Drug Rescue Project (v2.0)

## Project Goal
This project focuses on identifying potential drug rescue leads from clinical trial failures in the Aggregate Analysis of ClinicalTrials.gov (AACT).  The database flat text files. (https://aact.ctti-clinicaltrials.org/downloads/snapshots?type=flatfiles).

The SVEF- Drug Rescue Project (v2.0) attempts to predict drug repositioning potential using a machine learning model.  A **Random Forest** model is used to analyze clinical features, safety signals, and biological indicators to identify successful "rescue" candidates. Drug and target protein interaction predictions for repositioning will be performed using a Interpretable Cross-Attention Network (ICAN) model. (https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0276609)



Some notebooks and source code in the project are not being shared.

## Techniques Used
The current project approach has shifted from the Version 1 that relied on heuristic regular expression mining of the ['why_stopped'] field to a Version 2 that relies on the analyzing the group and intervention design, outcomes, and reported events.  Feature engineering was performed to represent:

Serious Adverse Events (SAE) frequency

$$SAE\text{ Incidence Rate} = \min\left(1.0, \frac{\sum \text{Subjects Affected}}{\text{Arm Subjects at Risk}}\right)$$


SAE intensity

$$SAE \text{ Intensity} = \frac{\sum \text{Total SAE Occurrences}}{\sum \text{Subjects Affected}}$$

Mortality

$$Mortality\ Rate_{arm} = \frac{\sum \text{Subjects\ Affected}_{(\text{event\_type} = \text{'deaths'})}}{\max(\text{Subjects\ at\ Risk}_{arm})}$$

Efficacy is being evaluated by examining the type of hypothesis test and results for the primary endpoint.  Currently, Superiority, Non-Inferiority, and Equivalence are compared with p_value for labeling of efficacy success or failure.  Confidence Intervals may also become included as time allows.

Features from Version 1 will be reintroduced, such as lipophilicity, molecular weight, published literature evidence, and heuroistic regular expression mining in the near future.  Expectation is desired aspects of Version 1 architecure can be easily adapted for Version 2. Attempting to revise Version 1 architure to achieve unmeet needs were too time consuming.  A second fresh approach to gaining new/better features was needed.  Determination was made that fitting positive architechure aspects of Version 1 to Version 2 would be more beneficial and efficient than repeatedly modifying Version 1 to meet needs.

 

## Dataset Source
The AACT database flat text files can be found here: https://aact.ctti-clinicaltrials.org/downloads/snapshots?type=flatfiles.  (April 14, 2026 historical file used in SVEF - Drug Rescue Project v2.0)


## Summary of Findings
The original production pipeline (v1.0), including its modular source code, tests, and documentation, has been archived for future reference and comparison.
- **Location**: `legacy_pipeline/`
- **Reference**: See `legacy_pipeline/README_v1.md` and `legacy_pipeline/PIPELINE_DETAILS.md` for details on the previous architecture.

---
*BIFX546 Final Project*
