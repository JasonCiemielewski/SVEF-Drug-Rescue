# Pipeline Automation Guide: SVEF Project

This guide explains how to execute the SVEF project's data processing pipeline, from initial filtration to the final "Gold Standard" candidate report.

## 1. Prerequisites
- **Raw Data:** AACT flat files must be placed in `data/raw/`.
- **Environment:** The `.svef` virtual environment must be active with all dependencies installed.

## 2. Pipeline Execution Steps

### Step 1: Base Candidate Filtration
**Script:** `src/data/make_dataset.py`
- **Action:** Filters `studies.txt` and `interventions.txt` for Phase 2/3 Terminated drug trials where `why_stopped` indicates efficacy failure and no safety concerns.
- **Output:** `data/processed/SVEF_candidates.csv` (1,067 initial trials).

### Step 2: Feature Enrichment
**Script:** `src/features/enrich_dataset.py`
- **Action:** 
    1. Joins clinical data (enrollment, start dates, lead sponsor, MeSH terms).
    2. Processes publication metadata (PMIDs, DOI extraction, Evidence_Confidence score).
    3. Fetches molecular SMILES from the PubChem PUG-REST API.
    4. Automatically archives previous versions of the enriched dataset to `data/processed/archive/`.
- **Output:** `data/processed/SVEF_Enriched_Final.csv`.

### Step 3: Coverage Analysis & Subsetting
**Script:** `src/visualization/analyze_coverage.py`
- **Action:** 
    1. Analyzes the overlap between trials with publications and trials with SMILES data.
    2. Generates Venn diagrams and stacked bar charts for data quality reporting.
    3. Exports the final "Gold Standard" subset (candidates that are both DTI-ready and evidence-rich).
- **Outputs:** 
    - `data/processed/SVEF_Gold_Standard_Candidates.csv`.
    - `reports/figures/coverage_venn.png`.
    - `reports/figures/coverage_stacked_bar.png`.

## 3. Automation Workflow
To run the entire pipeline in sequence, you can use the following command (Windows PowerShell):
```powershell
python src/data/make_dataset.py; python src/features/enrich_dataset.py; python src/visualization/analyze_coverage.py
```

## 4. Archiving & Comparison
The `src/features/enrich_dataset.py` script automatically maintains an audit trail in `data/processed/archive/`. Older datasets are timestamped (`SVEF_Enriched_YYYYMMDD_HHMMSS.csv`) whenever a new run is initiated, allowing for longitudinal comparison of enrichment improvements.
