# Implementation Plan: Global AACT Audit & Tiered SMILES Recovery

## 1. Overview
This plan outlines the engineering of a modular pipeline to perform a global denominator analysis of the AACT database, identify high-value "SVEF" assets, and execute a tiered chemical recovery strategy.

## 2. System Architecture & Directory Structure
We will align the new modules with the existing project structure while ensuring clear separation of concerns.

- **`data/raw/`**: Input AACT pipe-delimited files (already established).
- **`data/processed/`**: 
  - `global_trial_audit.parquet`: The full denominator dataset.
  - `SVEF_candidates_raw.csv`: Filtered small-molecule assets.
  - `SVEF_Enriched_Final.csv`: Final model-ready dataset.
- **`src/audit/`**:
  - `audit_engine.py`: Categorization and molecule classification.
  - `svef_refinement.py`: Filtering and Safety_Score calculation.
  - `smiles_recovery.py`: Tiered PubChem lookups.
- **`main.py`**: Entry point for orchestration.

## 3. Module Specifications

### Module 1: `audit_engine.py` (Global Denominator Analysis)
- **Categorization:** Uses regex on `why_stopped` for all ~570k trials.
  - *Categories:* Efficacy, Safety, Accrual/Logistics, Business/Strategic, Administrative, Unknown.
- **Molecule Classification:** Categorizes interventions based on `name` and `description`.
  - *Small_Molecule:* Default or specific indicators (e.g., `-tinib`, `-stat`).
  - *Biologic:* Keywords (`mab`, `cept`, `recombinant`, `protein`, `cell therapy`, `antibody`, `gene therapy`, `alfa`, `beta`).
- **Output:** Saves to `data/processed/global_trial_audit.parquet` (using Parquet for performance with large datasets).

### Module 2: `svef_refinement.py` (Targeted Asset Identification)
- **Logic:** Filters for the "Rescue Sweet Spot": 
  - `Phase 2/3` + `Terminated` + `Small_Molecule` + `Efficacy Failure` + `NO Safety Keywords`.
- **Safety_Score:** Calculated as `(Log1p(Enrollment) * 0.5) + (Duration * 0.5)`.
- **Output:** `data/processed/SVEF_candidates_raw.csv`.

### Module 3: `smiles_recovery.py` (Tiered Chemical Enrichment)
- **Tier 1:** PubChem API lookup by `intervention_name`.
- **Tier 2 (CAS Lookup):** Scan `description` and `official_title` for CAS numbers (`\d{2,7}-\d{2}-\d`) and query PubChem by CAS.
- **Tier 3 (Synonym Expansion):** Fetch synonyms via PubChem API, retry lookup on the top 3 results.
- **Constraint:** Strict 200ms rate-limiter (`time.sleep(0.2)`).

## 4. Orchestration: `main.py`
- Provides CLI flags to run modules independently (`--audit`, `--refine`, `--enrich`) or the full sequence (`--all`).
- Validates the `.svef` virtual environment before execution.

## 5. Architectural Suggestions for Improvement
1.  **Parquet for Global Audit:** I suggest using **Parquet** instead of CSV for the `global_trial_audit` file. At ~570,000 trials joined with ~800,000 interventions, the resulting file will be significantly smaller and faster to load than a flat CSV.
2.  **Log-Scaling Enrollment:** In Module 2, I suggest using `log1p(enrollment)` for the `Safety_Score`. Clinical enrollment varies from 1 to 40,000+; log-scaling prevents outliers from skewing the normalized score.
3.  **Checkpointing:** Implement a checkpoint file for `smiles_recovery.py` so that if the API call is interrupted, it can resume from the last processed drug name rather than restarting.
4.  **Tqdm Integration:** Add progress bars for the PubChem lookups to provide real-time feedback during the time-intensive enrichment phase.
