# Feature Engineering Plan: SVEF Dataset Enrichment

## 1. Overview
This phase enhances the foundational SVEF candidates list (1,067 trials) by integrating quantitative clinical data from AACT and molecular descriptors from PubChem. The goal is to create a "DTI-Ready" dataset for deep learning models.

## 2. Data Sources & Integration (AACT)
- **Tables to Load:**
    - `data/raw/studies.txt`: `enrollment`, `start_date`, `primary_completion_date`.
    - `data/raw/calculated_values.txt`: `actual_duration` (if available).
    - `data/raw/sponsors.txt`: `agency_class` (Lead Sponsor classification).
    - `data/raw/browse_conditions.txt`: `mesh_term` (Disease indications).
- **Join Strategy:**
    - Perform `left joins` on the existing SVEF dataframe using `nct_id`.
    - **MeSH Term Handling:** Group `browse_conditions` by `nct_id` and aggregate multiple terms into a single pipe-separated (`|`) string to prevent row duplication.
    - **Sponsor Handling:** Select the `lead` sponsor entry for each trial.

## 3. Temporal Feature Engineering
- **Date Conversion:** Parse `start_date` and `primary_completion_date` into datetime objects.
- **Duration Calculation:** 
    - Use `actual_duration` from `calculated_values.txt` if present.
    - Otherwise, calculate `trial_duration_days` as the delta between start and completion.
- **Validation:** Handle missing dates or negative durations by setting them to `NaN`.

## 4. Cheminformatics Enrichment (PubChem PUG-REST)
- **API Function:** `get_pubchem_data(drug_name)`
- **Lookup Logic:**
    - Use the PUG-REST JSON endpoint: `compound/name/{name}/property/CanonicalSMILES,MolecularWeight,XLogP/JSON`.
    - Retrieve: `CanonicalSMILES`, `MolecularWeight`, and `XLogP`.
- **Resilience & Ethics:**
    - **Rate Limiting:** `time.sleep(0.2)` to stay within PubChem's 5 requests/second limit.
    - **Error Handling:** Use `try-except` blocks for 404s (not found) or 400s (bad request, e.g., for combination drug names).
    - **Caching:** Only lookup unique drug names to minimize API calls.

## 5. Quantitative Scoring & Final Export
- **Safety_Score (Normalization):**
    - Normalize `enrollment` and `trial_duration_days` using Min-Max scaling.
    - Compute `Safety_Score = (norm_enrollment * 0.5) + (norm_duration * 0.5)`.
- **DTI-Ready Flag:** Boolean flag `is_dti_ready = True` if a valid SMILES string exists.
- **Output:** Save final dataset to `data/processed/SVEF_Enriched_Final.csv`.

## 6. Validation & Summary Stats
- Report average enrollment.
- Report SMILES matching success rate.
- Report Asset Origin distribution (Industry vs. Academic).
