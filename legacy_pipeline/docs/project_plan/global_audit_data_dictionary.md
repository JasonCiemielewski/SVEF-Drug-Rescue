# Data Dictionary: global_trial_audit.parquet

This document defines and explains each header (feature) within the global trial audit dataset, which serves as the "denominator" for all ClinicalTrials.gov (AACT) trials and interventions.

## Core Trial Metadata (AACT)
*   **nct_id:** The unique ClinicalTrials.gov identifier for the trial.
*   **study_type:** Classification of the study (e.g., 'INTERVENTIONAL', 'OBSERVATIONAL').
*   **phase:** The clinical trial phase (e.g., 'PHASE1', 'PHASE2', 'PHASE3').
*   **overall_status:** The current recruitment/completion status (e.g., 'COMPLETED', 'TERMINATED', 'WITHDRAWN').
*   **why_stopped:** The free-text reason provided by the sponsor for terminating the trial.
*   **enrollment:** The total number of participants in the trial.
*   **start_date:** The date the trial officially commenced.
*   **primary_completion_date:** The date the trial reached its primary endpoint assessment.

## Automated Audit Classifications (Audit Engine)
*   **termination_category:** A regex-derived classification of the `why_stopped` field.
    *   `Efficacy`: Stopped for futility, lack of benefit, or failing to meet endpoints.
    *   `Safety`: Stopped for toxicity, adverse events, or safety concerns.
    *   `Accrual/Logistics`: Stopped due to slow recruitment or enrollment difficulties.
    *   `Business/Strategic`: Stopped due to sponsor priorities, funding, or portfolio changes.
    *   `Administrative`: Stopped for operational or management reasons.
    *   `Unknown`: Reason is null or does not match any keyword criteria.
    *   `Other/Unspecified`: Reason is provided but does not fit into standard categories.

## Intervention & Molecule Metadata
*   **intervention_type:** The AACT category of intervention (e.g., 'DRUG', 'DEVICE', 'PROCEDURE').
*   **name:** The specific name of the intervention (drug name, device name, etc.).
*   **description:** A detailed description of the intervention, including dosage or mechanism.
*   **molecule_type:** A regex-derived classification of the intervention to identify "Rescue-Ready" assets.
    *   `Small_Molecule`: Standard pharmacological drugs (default for 'DRUG' type without biologic indicators).
    *   `Biologic`: Large-molecule assets identified by keywords such as 'mab', 'cept', 'recombinant', 'protein', 'vaccine', 'cell therapy', or 'gene therapy'.
    *   `Other`: Interventions that are not classified as 'DRUG' (e.g., devices, procedures).
