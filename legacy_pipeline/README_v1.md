# SVEF Dataset Construction: Total Evidence Drug Rescue Pipeline

## 1. Overview
The **Safety-Validated/Efficacy-Failed (SVEF)** project identifies "stranded" drug assets from ClinicalTrials.gov (AACT). These molecules have successfully navigated Phase 1 safety hurdles but were halted in Phases 2 or 3 for reasons other than safety (e.g., lack of efficacy or strategic pivots).

This pipeline utilizes a **Total Evidence Model**, preserving every drug arm in a clinical trial (~20,000+ candidate trials) to provide full interaction context for downstream Deep Learning models like **ICANN**.

## 2. Key Features
*   **Total Evidence Architecture:** Preserves all drugs listed in a trial (Experimental, Placebo, Comparator) and tags them with their clinical role (`group_type`), processing a broad candidate pool of 20,000+ trials.
*   **Architect-Grade Hardening:** Implements robust API retry logic (exponential backoff), atomic cache writing to prevent data corruption, and strict relational join integrity (resolving column collisions).
*   **Bioinformatics Recovery:** Utilizes a 3-tiered fallback system (Name -> CAS Registry -> Synonyms) to maximize SMILES recovery from PubChem.
*   **Signality Tracking:** Categorizes trial halts into scientific failures (`EFFICACY_FAILURE`), strategic pivots (`CLEAN_EXIT`), or logistical withdrawals.
*   **Asset Rescue Leads:** Automatically isolates proprietary internal codes (e.g., AZD-XXXX) into a separate "Rescue Leads" dataset for future research.

## 3. Installation & Setup
1.  **Environment:** Python 3.12+ (Virtual environment recommended).
2.  **Dependencies:** `pip install -r requirements.txt`.
3.  **Tests:** Verify the logic by running `pytest tests/`.

## 4. Pipeline Execution
The pipeline is managed through `main.py` with modular flags for specific auditing, refinement, and enrichment tasks.

### Full Pipeline Run
```bash
python main.py --all
```

### Modular Flags
- `--audit`: Runs Module 1: Global Denominator Analysis (AACT status auditing).
- `--refine`: Runs Module 2: Targeted Asset Identification (SVEF candidate extraction).
- `--enrich`: Runs Module 3: Tiered Chemical Enrichment (PubChem/SMILES recovery).

## 5. Quick Start & QA
### Micro Dataset (Recommended for First Run)
If you don't have the full 1GB+ AACT dataset, use the pre-processed micro dataset in `data/demo/` for testing:
```bash
python src/data/create_micro_dataset.py  # (Optional: regenerates micro files)
python main.py --all --demo              # (Coming soon: flag for demo data)
```
*Note: Currently, point the pipeline to `data/demo/` by renaming it to `data/raw/` for a quick test.*

### Quality Assurance
Before a production run, verify the system integrity:
1.  **Preflight Check:** `python src/features/preflight_test.py` (Validates environment and AACT file structure).
2.  **Pilot Run:** `python src/features/pilot_run.py` (Tests enrichment logic on a 500-trial sample).
3.  **Unit Tests:** `pytest tests/bioinformatics_audit/` (Verifies core logic).

## 6. Project Structure
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
