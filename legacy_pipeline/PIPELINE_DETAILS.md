# Sequential Pipeline Documentation for `main.py -all`

This document provides an in-depth, sequential trace of every function executed when running `main.py -all`. It describes the purpose, activities, inputs, and outputs of each function, as well as the data columns generated throughout the pipeline.

## Overview
The `--all` flag triggers a three-module pipeline designed to audit clinical trial data, refine candidates for drug rescue, and enrich them with chemical metadata (SMILES).

---

## Module 1: Global Denominator Analysis
**Primary Function:** `audit_global_trials(raw_dir, processed_dir)`  
**File:** `src/audit/audit_engine.py`

### 1.1 `audit_global_trials(raw_dir, processed_dir)`
- **Purpose:** Performs a global audit of all AACT trials to categorize terminations and classify intervention types.
- **Activities:**
    - Loads `studies.txt` and `interventions.txt` from the raw data directory.
    - Applies categorization logic to termination reasons.
    - Classifies interventions into molecule types (Small Molecule, Biologic, Other).
    - Merges studies and interventions.
    - Filters for Phase 2/3 terminated trials as "Base Candidates".
- **Inputs:** `raw_dir` (path), `processed_dir` (path).
- **Outputs:** 
    - `global_trial_audit.parquet`: Full merged dataset.
    - `SVEF_candidates.csv`: Filtered base candidates (Phase 2/3, TERMINATED).
- **Columns Created:**
    - `termination_category`: Broad bucket for why a trial stopped (Efficacy, Safety, Accrual, etc.).
    - `molecule_type`: Classification of the intervention (Small_Molecule, Biologic, Other).

### 1.2 `categorize_termination(reason)` (Sub-function)
- **Purpose:** Maps the raw `why_stopped` text to a standardized category.
- **Activities:** Uses keyword matching (e.g., "futility" -> "Efficacy", "toxic" -> "Safety").
- **Inputs:** `reason` (string from `why_stopped`).
- **Outputs:** `category` (string).

### 1.3 `classify_molecule(row)` (Sub-function)
- **Purpose:** Distinguishes between Small Molecules and Biologics.
- **Activities:** 
    - Checks if `intervention_type` is 'DRUG'.
    - Searches for biologic keywords (e.g., "mab", "recombinant") in the name and description.
- **Inputs:** `row` (DataFrame row with `name`, `description`, `intervention_type`).
- **Outputs:** `molecule_type` (string).

---

## Module 2: Targeted Asset Identification (Refinement)
**Primary Function:** `refine_svef_assets(processed_dir)`  
**File:** `src/audit/svef_refinement.py`

### 2.1 `refine_svef_assets(processed_dir)`
- **Purpose:** Refines the base candidate list and calculates a "Safety Score" to prioritize assets.
- **Activities:**
    - Loads `SVEF_candidates.csv` (from Module 1).
    - Filters out trials that mention safety issues in `why_stopped` to focus on efficacy failures.
    - Calculates trial duration.
    - Normalizes enrollment and duration to create a composite `Safety_Score`.
- **Inputs:** `processed_dir` (path).
- **Outputs:** `SVEF_candidates_raw.csv` (refined candidates with safety scores).
- **Columns Created:**
    - `duration_days`: Difference between `start_date` and `primary_completion_date`.
    - `log_enrollment`: Log-scaled enrollment value.
    - `norm_enrollment`: Min-Max normalized log enrollment (0 to 1).
    - `norm_duration`: Min-Max normalized duration (0 to 1).
    - `Safety_Score`: Average of `norm_enrollment` and `norm_duration`.

### 2.2 `calculate_duration(row)` (Sub-function)
- **Purpose:** Computes the length of the trial.
- **Inputs:** `row` (with `start_date` and `primary_completion_date`).
- **Outputs:** `delta` (integer days).

---

## Module 3: Tiered Chemical Enrichment
**Primary Function:** `recover_smiles(processed_dir)`  
**File:** `src/audit/smiles_recovery.py`

### 3.1 `recover_smiles(processed_dir)`
- **Purpose:** Orchestrates the enrichment of candidates with clinical metadata and PubChem chemical data.
- **Activities:**
    - Coordinates calls to specialized enrichment functions in `src/features/enrich_dataset.py`.
    - Saves the final enriched dataset and a list of proprietary rescue leads.
- **Inputs:** `processed_dir` (path).
- **Outputs:**
    - `SVEF_Enriched_Final.csv`: The master dataset with SMILES and full metadata.
    - `Possible_Internal_Proprietary_Rescue_Leads.csv`: List of drugs with proprietary codes.

### 3.2 `load_data(input_path, raw_dir)`
- **Purpose:** Ingests relational AACT tables (sponsors, conditions, references, etc.) filtered by the candidate NCT IDs.
- **Inputs:** `input_path` (SVEF candidates), `raw_dir` (raw AACT text files).
- **Outputs:** Multiple DataFrames (studies, calc_vals, sponsors, conditions, refs, design_groups, dg_int).

### 3.3 `map_intervention_roles(df, dg, dg_int)`
- **Purpose:** Identifies if an intervention was "Experimental", "Placebo", etc.
- **Activities:** Joins `design_groups` and `design_group_interventions` tables.
- **Columns Created:**
    - `group_type`: The role of the intervention in the trial.

### 3.4 `merge_clinical_metadata(df, studies, calc_vals, sponsors, conditions)`
- **Purpose:** Consolidates clinical metadata into the main candidate list.
- **Activities:** Merges sponsor classes, MeSH terms, and duration data. Filters out remaining biologics using regex.
- **Columns Created:**
    - `actual_duration`: Duration from `calculated_values.txt`.
    - `agency_class`: Sponsor type (INDUSTRY, NIH, etc.).
    - `mesh_term`: Pipe-separated list of conditions associated with the trial.

### 3.5 `feature_engineering_advanced(df)`
- **Purpose:** Re-calculates and standardizes statistical features for the final dataset.
- **Columns Created:**
    - `trial_duration_days`: Standardized duration.
    - `log_enrollment`: Re-standardized log enrollment.
    - `Safety_Score`: Final normalized safety priority score.

### 3.6 `process_publications(refs)`
- **Purpose:** Analyzes trial references to determine evidence depth.
- **Activities:** Groups references by type (result vs background) and calculates a confidence score.
- **Columns Created:**
    - `publication_count`: Total number of PMIDs.
    - `Evidence_Confidence`: Score based on presence of results-type publications.
    - `results_pmid_list`: PMIDs for trial results.
    - `background_pmid_list`: PMIDs for background info.
    - `doi_list`: DOIs associated with the trial.

### 3.7 `enrich_with_pubchem_architect(df, cache_path)`
- **Purpose:** The core engine for SMILES recovery.
- **Activities:**
    - Uses a tiered lookup (Name -> CAS -> Synonym).
    - Consults `smiles_cache.csv` to avoid redundant API calls.
    - Performs 1:Many matching if a name matches multiple chemical structures.
- **Inputs:** `df` (candidate list), `cache_path` (SMILES cache).
- **Columns Created:**
    - `pubchem_cid`: PubChem Compound ID.
    - `smiles`: Simplified Molecular Input Line Entry System (chemical structure).
    - `molecular_weight`: MW of the compound.
    - `logp`: Octanol-water partition coefficient (hydrophobicity).
    - `matched_by`: The tier that succeeded (Name, CAS, or Synonym).
    - `failure_reason`: Why a match failed (PLACEBO, PROPRIETARY, etc.).
    - `is_dti_ready`: Boolean; true if SMILES is available for Drug-Target Interaction modeling.
    - `is_lipinski_compliant`: Boolean; true if MW < 500 and LogP < 5.

### 3.8 `get_pubchem_data_tiered(drug_name, context_text)` (Sub-function)
- **Purpose:** Executes the tiered search strategy.
- **Activities:** Calls `query_pubchem` for the drug name, then searches trial titles for CAS numbers, then tries synonyms.

### 3.9 `query_pubchem(identifier, namespace)` (Sub-function)
- **Purpose:** Low-level API client for PubChem PUG REST.
- **Inputs:** `identifier` (search term), `namespace` (e.g., 'name').
- **Outputs:** JSON property list (SMILES, CID, MW, XLogP).

### 3.10 `clean_drug_name(drug_name)` (Sub-function)
- **Purpose:** Strips noise (doses, salt forms, prefixes) from drug names to improve match rates.
- **Activities:** Regex removal of "mg", "kg", "tablet", "hydrochloride", etc.
- **Inputs:** Raw name.
- **Outputs:** Cleaned name for API search.

### 3.11 `classify_failure(drug_name)` (Sub-function)
- **Purpose:** Labels why a compound couldn't be found in PubChem.
- **Activities:** Pattern matching for placebo keywords or proprietary codes (e.g., "MK-1234").
- **Outputs:** `failure_reason` category.

### 3.12 `atomic_write_cache_df(df, cache_path)` (Utility)
- **Purpose:** Safely writes the SMILES cache to disk.
- **Activities:** Writes to a temporary file first, then replaces the original to prevent data corruption during crashes.
