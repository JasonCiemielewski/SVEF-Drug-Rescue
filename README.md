# SVEF Dataset Construction: Total Evidence Drug Rescue Pipeline

## 1. Overview
The **Safety-Validated/Efficacy-Failed (SVEF)** project identifies "stranded" drug assets from ClinicalTrials.gov (AACT). These molecules have successfully navigated Phase 1 safety hurdles but were halted in Phases 2 or 3 for reasons other than safety (e.g., lack of efficacy or strategic pivots).

This pipeline utilizes a **Total Evidence Model**, preserving every drug arm in a clinical trial to provide full interaction context for downstream Deep Learning models like **ICANN**.

## 2. Key Features
*   **Total Evidence Architecture:** Preserves all drugs listed in a trial (Experimental, Placebo, Comparator) and tags them with their clinical role (`group_type`).
*   **Architect-Grade Hardening:** Implements robust API retry logic (exponential backoff), atomic cache writing to prevent data corruption, and strict relational join integrity.
*   **Bioinformatics Recovery:** Utilizes a 3-tiered fallback system (Name -> CAS Registry -> Synonyms) to maximize SMILES recovery from PubChem.
*   **Signality Tracking:** Categorizes trial halts into scientific failures (`EFFICACY_FAILURE`), strategic pivots (`CLEAN_EXIT`), or logistical withdrawals.
*   **Asset Rescue Leads:** Automatically isolates proprietary internal codes (e.g., AZD-XXXX) into a separate "Rescue Leads" dataset for future research.

## 3. Installation & Setup
1.  **Environment:** Python 3.12+ (Virtual environment recommended).
2.  **Dependencies:** `pip install -r requirements.txt`.
3.  **Tests:** Verify the logic by running `pytest tests/bioinformatics_audit/`.

## 4. Pipeline Execution
1.  **Phase 1: Candidate Extraction**
    `python src/data/make_dataset.py`
2.  **Phase 2: Hardened Enrichment**
    `python src/features/enrich_dataset.py`
3.  **Phase 3: Visual Reporting & Gold Standard Export**
    `python src/visualization/analyze_coverage.py`

## 5. Project Structure
```text
├── data/
│   ├── raw/             # AACT source files (.txt)
│   ├── interim/         # Caches, pilot results, and intermediate extractions
│   │   └── audit/       # Decision matrices and structural snapshots
│   └── processed/       # Final SVEF candidates and Gold Standard results
├── docs/                # Detailed methodologies and data dictionaries
├── src/                 # Modular source code (data, features, visualization)
├── tests/               # Comprehensive bioinformatics audit suite
└── reports/             # PNG figures and audit summaries
```
