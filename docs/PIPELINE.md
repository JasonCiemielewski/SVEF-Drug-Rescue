# Pipeline Automation Guide: SVEF Total Evidence Edition

This guide explains how to execute the SVEF data pipeline. The architecture is designed for high-fidelity chemical recovery and statistical integrity.

## 1. Prerequisites
- **AACT Data:** The pipeline requires the standard AACT flat files in `data/raw/`. 
- **Relational Tables:** Must include `design_groups.txt` and `design_group_interventions.txt` for role mapping.

## 2. Execution Steps

### Step 1: Base Candidate Extraction & Auditing
**Script:** `src/data/make_dataset.py`
- **Action:** Filters ~570k trials for Phase 2/3 halted studies.
- **NLP Logic:** Identifies scientific vs. strategic reasons for termination.
- **Output:** `data/interim/SVEF_candidates.csv`.

### Step 2: Total Evidence Enrichment (Hardened)
**Script:** `src/features/enrich_dataset.py`
- **Total Evidence Model:** Preserves every drug in the trial. Joins with trial design tables to identify if a drug was `EXPERIMENTAL` or a `PLACEBO`.
- **Bioinformatics Recovery:**
    - **Tier 1:** Name lookup.
    - **Tier 2:** CAS Registry Number extraction from trial titles.
    - **Tier 3:** Alias/Synonym lookup.
- **Hardening Features:**
    - **Retries:** 3 attempts with exponential backoff for API calls.
    - **Atomic Writes:** Saves `smiles_cache.csv` to a temporary file before renaming to prevent corruption.
    - **Type Integrity:** Forced string-casting for all relational join keys.
- **Output:** `data/processed/SVEF_Enriched_Final.csv`.

### Step 3: Failure Categorization & Rescue leads
- **Action:** Assets that fail PubChem are categorized (e.g., `PLACEBO_EQUIVALENT` vs `POSSIBLE_INTERNAL_PROPRIETARY`).
- **Output:** `data/processed/Possible_Internal_Proprietary_Rescue_Leads.csv`.

### Step 4: Coverage Analysis
**Script:** `src/visualization/analyze_coverage.py`
- **Action:** Generates PNG reports quantifying the success of the bioinformatics recovery and identifying the "Gold Standard" subset for ICANN.

## 3. Recommended QA Workflow
Before running a production-scale job, it is recommended to follow this sequence:
1.  **Unit Tests:** `pytest tests/bioinformatics_audit/` (Verifies logic).
2.  **Pilot Run:** `python src/features/pilot_run.py` (Verifies API and AACT joins on a 500-trial sample).
3.  **Production:** `python src/features/enrich_dataset.py`.
