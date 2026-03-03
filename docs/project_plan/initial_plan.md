# Implementation Plan: SVEF Dataset Construction

## 1. Overview
This project aims to identify "stranded" small-molecule drug assets from ClinicalTrials.gov (AACT) that failed due to lack of efficacy in Phase 2 or 3 but maintained a clean safety profile. These candidates are ideal for drug repositioning and "Target Fishing" using deep learning.

## 2. Environment & Data Setup
- **Source Directory:** `raw_data/` (as identified in the workspace).
- **Output Directory:** `data/` (to be created).
- **Tools:** Python 3.x, `pandas` for data manipulation, `re` for regex-based logic.

## 3. Step-by-Step Implementation

### Step 1: Data Ingestion & Joins
- Load `studies.txt` and `interventions.txt` using `pandas` with pipe (`|`) delimiters.
- Handle potential encoding issues and set `low_memory=False` for robust loading.
- Perform an `inner join` on `nct_id` to correlate trial outcomes with specific drug interventions.

### Step 2: Structural Filtering
- Filter for `study_type == 'Interventional'`.
- Filter for `phase` in `['Phase 2', 'Phase 3']`.
- Filter for `overall_status == 'Terminated'`.
- Filter for `intervention_type == 'Drug'`.
- *Refinement:* Implement a secondary filter to exclude obvious biologics (e.g., monoclonal antibodies ending in "-mab") to focus on small molecules.

### Step 3: "Safe but Futile" Logic (NLP/Regex)
- **Cleaning:** Standardize `why_stopped` text (lowercase, strip whitespace, handle nulls).
- **Efficacy Mask (Refined):** Identify trials stopped for futility or lack of efficacy using keywords: `futility`, `efficacy`, `lack of effect`, `benefit`, `endpoint`, `interim analysis`, `superiority`, `insufficient signal`, `lack of benefit`, `no significant difference`, `unprovable`.
- **Safety Mask (Refined):** Identify trials stopped for toxicity or safety using keywords: `safety`, `toxic`, `adverse event`, `side effect`, `harm`, `risk`, `death`, `mortality`, `AEs`, `maximum tolerated dose`, `intolerability`.
- **Validation Logic:** Implement checks to ensure "no safety concerns" doesn't trigger a safety exclusion.
- **SVEF Selection:** Candidates = (Efficacy Mask is True) AND (Safety Mask is False).

### Step 4: Molecular Enrichment (Bioinformatics Framework)
- Extract unique `intervention_name` values from the SVEF candidates.
- Define a modular function `fetch_pubchem_data(drug_name)` using PubChem's PUG-REST API.
- The function will serve as a template for retrieving:
    - Canonical SMILES
    - Molecular Weight
    - LogP

### Step 5: Output & Quality Control
- Export the final dataset to `data/SVEF_candidates.csv`.
- Generate a summary report including:
    - Total trials initially processed.
    - Count of Phase 2/3 terminated trials.
    - Final SVEF candidate count and percentage.

## 4. Technical Constraints & Standards
- **Modularity:** Use a functional programming approach for filtering and cleaning.
- **Documentation:** Graduate-level docstrings explaining the biological rationale for specific filters.
- **Pathing:** Use relative paths consistent with the local workspace.
