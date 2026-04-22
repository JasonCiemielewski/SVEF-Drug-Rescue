# SVEF - Drug Rescue Project (v2.0)

## Project Overview
This project focuses on identifying potential drug rescue leads from clinical trial failures in the AACT database.

## Project Update
The current project approach has shifted from the Version 1 that relied on heuristic regular expression mining of the ['why_stopped'] field to a Version 2 that relies on the analyzing the group and intervention design, outcomes, and reported events.  New features are developed to represent:

Serious Adverse Events (SAE) frequency

$$SAE\text{ Incidence Rate} = \min\left(1.0, \frac{\sum \text{Subjects Affected}}{\text{Arm Subjects at Risk}}\right)$$


SAE intensity

$$SAE \text{ Intensity} = \frac{\sum \text{Total SAE Occurrences}}{\sum \text{Subjects Affected}}$$

Mortality

$$Mortality\ Rate_{arm} = \frac{\sum \text{Subjects\ Affected}_{(\text{event\_type} = \text{'deaths'})}}{\max(\text{Subjects\ at\ Risk}_{arm})}$$

Efficacy is being evaluated by examining the type of hypothesis test and results for the primary endpoint.  Currently, Superiority, Non-Inferiority, and Equivalence are compared with p_value for labeling of efficacy success or failure.  Confidence Intervals may also become included as time allows.

Features from Version 1 will be reintroduced, such as lipophilicity, molecular weight, published literature evidence, and heuroistic regular expression mining in the near future.  Expectation is desired aspects of Version 1 architecure can be easily adapted for Version 2. Attempting to revise Version 1 architure to achieve unmeet needs were too time consuming.  A second fresh approach to gaining new/better features was needed.  Determination was made that fitting positive architechure aspects of Version 1 to Version 2 would be more beneficial and efficient than repeatedly modifying Version 1 to meet needs.

Two approaches for labeling data are under consideration.  Approach 1 involves using 

## Current Primary Workflow
New feature development are now centered in:
- **`notebooks/model_creation.ipynb`**: This notebook contains the sequential steps to creating the new data features.  **`notebooks/EDA_AACT.ipynb`** contains the exploratory analysis of the AACT datafiles.  The size of this notebook is becoming a bit unwieldy and difficult to navigate for creating new data features.

Scripts will be developed in the near future that will produce outputs that the EDA notebook will be able to analyze.

## Legacy Archive
The original production pipeline (v1.0), including its modular source code, tests, and documentation, has been archived for future reference and comparison.
- **Location**: `legacy_pipeline/`
- **Reference**: See `legacy_pipeline/README_v1.md` and `legacy_pipeline/PIPELINE_DETAILS.md` for details on the previous architecture.

---
*BIFX546 Final Project*
