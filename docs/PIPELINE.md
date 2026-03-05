# Pipeline Automation Guide: SVEF Project (Unified Edition)

This guide explains how to execute the expanded SVEF data pipeline. The process is designed to be idempotent and provide a complete audit trail of all inclusion/exclusion decisions.

## 1. Prerequisites
- **Raw Data:** AACT flat files (`studies.txt`, `interventions.txt`, `id_information.txt`) must be in `data/raw/`.
- **Python:** 3.12+ with all dependencies in `requirements.txt` installed.

## 2. Pipeline Execution Steps

### Step 1: Unified Base Candidate Filtration & Auditing
**Script:** `src/data/make_dataset.py`
- **Action:** 
    1. Loads ~570k AACT trials.
    2. Filters for Phase 2/3 Interventional trials with statuses: `TERMINATED`, `SUSPENDED`, `WITHDRAWN`, and `UNKNOWN`.
    3. **Structural Auditing:** Saves snapshots of the initial filtered pool for each status in `data/interim/audit/`.
    4. **Text-Mining Logic:** Applies an NLP-based "Efficacy vs. Safety" filter to `why_stopped` text using word boundaries and complex negation rules (e.g., "not for safety or efficacy").
    5. **Categorization:** Assigns audit statuses like `TERMINATED_EFFICACY_FAILURE`, `SUSPENDED_CLEAN_EXIT`, or `WITHDRAWN_STRATEGIC`.
    6. **Trial Linking:** Scans `id_information.txt` to identify and link previous or successive clinical studies for the same drug.
- **Outputs:** 
    - `data/processed/SVEF_candidates.csv` (~22k trials).
    - `data/interim/audit/svef_logic_audit.csv` (Decision matrix for all ~41k audited trials).

### Step 2: Feature Enrichment & Chemical Linking
**Script:** `src/features/enrich_dataset.py`
- **Action:** 
    1. Joins clinical metadata (enrollment, start dates, lead sponsor, MeSH terms).
    2. Processes publication metadata (PMIDs, DOI extraction).
    3. Fetches molecular SMILES from the PubChem PUG-REST API.
    4. Automatically archives previous versions of the enriched dataset to `data/processed/archive/`.
- **Output:** `data/processed/SVEF_Enriched_Final.csv`.

### Step 3: Coverage Analysis & Subsetting
**Script:** `src/visualization/analyze_coverage.py`
- **Action:** 
    1. Identifies trials with both successful SMILES retrieval and available publication metadata.
    2. Generates quality reports (Venn diagrams/Bar charts).
    3. Exports the final "Gold Standard" subset for ICAN modeling.
- **Outputs:** 
    - `data/processed/SVEF_Gold_Standard_Candidates.csv`.
    - `reports/figures/coverage_venn.png`.
    - `reports/figures/coverage_stacked_bar.png`.

## 3. Automation Workflow
To run the entire pipeline in sequence (Windows PowerShell):
```powershell
python src/data/make_dataset.py; python src/features/enrich_dataset.py; python src/visualization/analyze_coverage.py
```

## 4. Troubleshooting & Auditing
- **Why was a trial excluded?** Open `data/interim/audit/svef_logic_audit.csv` and search for the `nct_id`. Check the `inclusion_trigger` and `exclusion_trigger` columns to see which words were detected.
- **How were trials linked?** Review the `connected_trials` column in the final processed files.
