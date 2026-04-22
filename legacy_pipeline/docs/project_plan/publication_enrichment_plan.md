# Implementation Plan: Publication Metadata Enrichment (Refined)

## 1. Overview
The goal of this phase is to correlate clinical trials in the SVEF dataset with their corresponding peer-reviewed literature. By identifying trials with associated PubMed IDs (PMIDs) and Digital Object Identifiers (DOIs), we can quantify the scholarly output and validation level of each drug asset, prioritizing direct clinical results over background context.

## 2. Data Source Identification
- **Table:** `data/raw/study_references.txt`
- **Key Columns:** 
    - `nct_id`: Linking key.
    - `pmid`: PubMed Identifier.
    - `reference_type`: Classification (e.g., 'RESULT', 'BACKGROUND').
    - `citation`: Full bibliographic text (contains DOIs).

## 3. Step-by-Step Implementation

### Step 1: Data Ingestion & DOI Extraction
- Load `study_references.txt` into a pandas DataFrame.
- **Regex Extraction:** Extract DOIs from the `citation` column using the pattern `doi:\s*([^\s;]+)`.
- Create a new `doi` column for each reference entry.

### Step 2: Aggregation Logic (Prioritized Grouping)
To maintain the "one row per intervention" structure without losing clinical context:
- **`results_pmid_list`**: Pipe-separated string (`|`) of PMIDs where `reference_type == 'RESULT'`.
- **`background_pmid_list`**: Pipe-separated string (`|`) of PMIDs where `reference_type == 'BACKGROUND'`.
- **`doi_list`**: Pipe-separated string (`|`) of all extracted DOIs.
- **`publication_count`**: Total unique PMIDs associated with the trial.

### Step 3: Feature Engineering - "Evidence_Confidence" Score
Instead of a simple count, we will implement a weighted score to represent the scholarly validation depth:
- **Base Score:** 
    - `(Number of RESULT PMIDs * 1.0)`
    - `(Number of BACKGROUND PMIDs * 0.2)`
- **Bonus:** `+0.5` if the trial has at least one 'RESULT' publication (indicating successful peer-review of trial findings).
- **Normalization:** Cap or scale the `Evidence_Confidence` score to a 0.0–5.0 range for easier ranking.

### Step 4: Integration into Pipeline
- Update `src/features/enrich_dataset.py` to include the publication join and scoring logic.
- Ensure the **Archiving Logic** (timestamps) captures this change for comparative analysis.

## 4. Documentation & Quality Control
- Update `docs/project_plan/data_dictionary.md` with the new publication and evidence-related headers.
- **Summary Report:**
    - Percentage of candidates with 'RESULT' publications.
    - Total unique DOIs recovered from the AACT citations.
    - Average `Evidence_Confidence` score for Industry vs. Academic assets.

## 5. Technical Constraints
- Use Python's `re` module for DOI extraction.
- Existing `.svef` virtual environment.
- Relative pathing (`data/raw/` and `data/processed/`).
