# Data Dictionary: SVEF_Enriched_Final.csv

This document defines and explains each header (feature) within the final enriched SVEF (Safety-Validated/Efficacy-Failed) dataset.

## AACT Core Features
*   **nct_id:** The unique ClinicalTrials.gov identifier for the trial.
*   **study_type:** The type of study (e.g., 'INTERVENTIONAL').
*   **phase:** The clinical trial phase ('PHASE2', 'PHASE3', or 'PHASE2/PHASE3').
*   **overall_status:** The current status of the trial ('TERMINATED').
*   **why_stopped:** The free-text reason provided by the sponsor for stopping the trial.
*   **id:** Internal AACT identifier for the intervention entry.
*   **intervention_type:** The category of intervention ('DRUG').
*   **name:** The name of the specific drug or intervention.
*   **description:** A detailed description of the drug or intervention, often including dosage and administration.
*   **agency_class:** Classification of the lead sponsor (e.g., 'INDUSTRY', 'OTHER', 'NIH').
*   **mesh_term:** Pipe-separated (|) list of Medical Subject Headings (MeSH) for the original failed indications.
*   **enrollment:** Total number of participants enrolled in the trial.
*   **start_date:** The date the trial officially started.
*   **primary_completion_date:** The date the trial reached its primary endpoint assessment.
*   **actual_duration:** The reported duration of the trial (in days or months), sourced from AACT's calculated_values.

## SVEF Filter Logic (Boolean Masks)
*   **why_stopped_clean:** The `why_stopped` text, lowercased and cleaned for regex processing.
*   **eff_mask:** (True/False) Flag indicating if the trial was stopped for lack of efficacy/futility.
*   **has_safety_keyword:** (True/False) Flag indicating if a safety-related keyword was present in `why_stopped`.
*   **is_specifically_safety:** (True/False) Flag indicating if the word 'safety' was specifically used.
*   **negation_mask:** (True/False) Flag indicating if common safety negations (e.g., "no safety concerns") were present.
*   **safe_mask:** (True/False) Final flag indicating if the trial was terminated for safety or toxicity reasons.

## Calculated Features
*   **trial_duration_days:** The computed duration of the trial in days, using `actual_duration` or the delta between `start_date` and `primary_completion_date`.
*   **norm_enrollment:** Min-Max normalized value of the `enrollment` column (0.0 to 1.0).
*   **norm_duration:** Min-Max normalized value of the `trial_duration_days` column (0.0 to 1.0).
*   **Safety_Score:** A weighted composite score `(0.5 * norm_enrollment + 0.5 * norm_duration)` representing the depth of human safety exposure.
*   **Evidence_Confidence:** A weighted scholarly validation score: `(Number of RESULT PMIDs * 1.0) + (Number of BACKGROUND PMIDs * 0.2) + 0.5 bonus if RESULTS exist`.

## Publication Metadata
*   **results_pmid_list:** Pipe-separated (|) list of PMIDs classified as 'RESULT'.
*   **background_pmid_list:** Pipe-separated (|) list of PMIDs classified as 'BACKGROUND' or other.
*   **doi_list:** Pipe-separated (|) list of Digital Object Identifiers (DOIs) extracted from trial citations.
*   **publication_count:** Total unique PMIDs associated with the trial.

## PubChem Molecular Descriptors
*   **pubchem_cid:** The unique Compound ID assigned by PubChem.
*   **smiles:** The Canonical or Connectivity SMILES string, used for Drug-Target Interaction (DTI) modeling.
*   **molecular_weight:** The molecular weight of the compound.
*   **logp:** The calculated partition coefficient (XLogP), indicating the molecule's lipophilicity.
*   **is_dti_ready:** (True/False) Flag indicating if the candidate has a valid SMILES string and is ready for deep learning pipelines.
