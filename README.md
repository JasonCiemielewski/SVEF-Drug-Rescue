# SVEF - Drug Rescue Project (v2.0)

## Project Goal
This project focuses on identifying potential drug rescue leads from clinical trial failures in the Aggregate Analysis of ClinicalTrials.gov (AACT).  The database flat text files. (https://aact.ctti-clinicaltrials.org/downloads/snapshots?type=flatfiles).

The SVEF- Drug Rescue Project (v2.0) attempts to predict drug repositioning potential using a machine learning model.  A Random Forest model is used to analyze clinical features, safety signals, and biological indicators to identify successful "rescue" candidates. Drug and target protein interaction predictions for repositioning will be performed using a Interpretable Cross-Attention Network (ICAN) model. (https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0276609)

The current project approach has shifted from the Version 1 that relied on heuristic regular expression mining of the ['why_stopped'] field to a Version 2 that relies on the analyzing the group and intervention design, outcomes, reported events, and heuristic regular expression mining.

Some notebooks and source code in the project are not being shared.

Google Gemini CLI and Google Gemini was used to assist in the develop of various aspects of this project, including code documentation, code generation/refactoring, and documentation.

## Techniques Used
The model utilizes a Random Forest Classifier.

The model's primary objective is to classify trials into a binary `rescue_target`: **Safety Failures** (Class 0) vs. **Other/Safe Potential** (Class 1).

* **Rescue Probability Scores**: The model generates a `rescue_probability_score` (probability of belonging to Class 1) for trials previously labeled as "Unknown" or "Other/Unspecified" in the AACT database.

* **The ICAN Priority List**: The analysis culminates in a prioritized ranking of rescue candidates. This list is sorted by **high probability score** and **low p-value**, identifying interventions that are predicted to be safe and showed strong efficacy signals before termination.


* **Ensemble Configuration**:
    * **Estimators**: 300 decision trees.
    * **Max Depth**: 20 levels to capture complex non-linear relationships.
    * **Min Samples Split**: 5, preventing over-segmentation of the data.
    * **Class Weight**: Set to `balanced` to handle the inherent imbalance between safety-related stops and other termination categories.
* **Preprocessing Logic**:
    * **Numerical Data**: Handled via a `SimpleImputer` (median strategy) and `StandardScaler`.
    * **Categorical Data**: Processed using `OneHotEncoder` after imputing with the most frequent value.
* **Feature Selection**: Recursive Feature Elimination with Cross-Validation (**RFECV**) was employed using a 5-fold Stratified K-Fold approach to identify the optimal feature subset based on the weighted F1-score.

---

### **Feature Set: Molecular & Clinical Signals**


The model specifically targets trials where "Deep Features" (molecular data) are present. The feature set is composed of 8 primary variables:

* **Numerical Features**:
    * **Molecular Data**: `molecular_weight` and `xlogp` (lipophilicity).
    * **Safety/Risk Metrics**: `sae_incidence_rate` and the total `arm_subjects_at_risk`.
    * **Statistical Signal**: `arm_p_value` (measuring the efficacy signal of the original trial).
* **Categorical Features**:
    * **Regulatory Context**: `phase` of the trial and `is_fda_regulated_drug` status.
    * **Trial Design**: `is_superiority` (indicating if the trial was designed to show superior efficacy).
    * **Termination_Category** utilizes heuristic regex from the why_stopped to categorize into different buckets of "Efficacy", "Safety", "Accrual/Logistics", "Business/Strategic", "Administrative", or "Unknown"


 Feature engineering was performed to represent:

Serious Adverse Events (SAE) frequency

$$SAE\text{ Incidence Rate} = \min\left(1.0, \frac{\sum \text{Subjects Affected}}{\text{Arm Subjects at Risk}}\right)$$


SAE intensity

$$SAE \text{ Intensity} = \frac{\sum \text{Total SAE Occurrences}}{\sum \text{Subjects Affected}}$$

Mortality

$$\text{Mortality Rate}_{\text{arm}} = \frac{\sum \text{Subjects Affected}_{(\text{event\_type} = \text{'deaths'})}}{\max(\text{Subjects at Risk}_{\text{arm}})}$$  
 

## Dataset Source
The AACT database flat text files can be found here: https://aact.ctti-clinicaltrials.org/downloads/snapshots?type=flatfiles.  (April 14, 2026 historical file used in SVEF - Drug Rescue Project v2.0)


## Summary of Findings
The original production pipeline (v1.0), including its modular source code, tests, and documentation, has been archived for future reference and comparison.
- **Location**: `legacy_pipeline/`
- **Reference**: See `legacy_pipeline/README_v1.md` and `legacy_pipeline/PIPELINE_DETAILS.md` for details on the previous architecture.

---
*BIFX546 Final Project*
