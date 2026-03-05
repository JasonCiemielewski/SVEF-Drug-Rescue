# SVEF Dataset Construction: Safety-Validated/Efficacy-Failed (Expanded)

## 1. Overview
The **Safety-Validated/Efficacy-Failed (SVEF)** project identifies "stranded" small-molecule drug assets from ClinicalTrials.gov (AACT). These molecules have passed Phase 1 safety hurdles but were halted in later phases for reasons other than safety (primarily lack of efficacy or strategic pivots).

This dataset is designed for **IP Rescue** and **Drug Repositioning** using Deep Learning models like ICAN.

## 2. Expanded Pipeline Scope
Previously focused only on **Terminated** trials, the pipeline now integrates four major clinical statuses to provide a 360-degree view of drug "signality":
*   **TERMINATED:** Official halts with documented reasons.
*   **SUSPENDED:** Temporary or early-warning halts (often precursors to termination).
*   **WITHDRAWN:** Cancelled before enrollment (identifies strategic pivots and logistical failures).
*   **UNKNOWN:** Abandoned/stale trials (identifies "zombie" drugs with no recent updates).

## 3. Key Features & Auditability
*   **Unified Audit Trail:** Every decision (Inclusion/Exclusion) is logged with the specific keyword "trigger" that caused it.
*   **Signality Tracking:** Categorizes trials into `EFFICACY_FAILURE`, `CLEAN_EXIT` (strategic/business), or `SAFETY_CONCERN`.
*   **Cross-Trial Linking:** Automatically identifies previous and successive trials using Secondary IDs and NCT Aliases.
*   **SMILES Integration:** Automated retrieval of molecular structures from PubChem for DTI-ready analysis.

## 4. Installation & Setup
1.  **Clone the Repository:**
    ```bash
    git clone <repository_url>
    cd Final_Project
    ```
2.  **Environment Configuration:**
    Ensure Python 3.12+ is installed. Create and activate the environment:
    ```bash
    python -m venv .svef
    .svef\Scripts\activate  # Windows
    ```
3.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

## 5. Pipeline Execution
1.  **Phase 1: Multi-Status Audited Extraction**
    ```bash
    python src/data/make_dataset.py
    ```
    Processes ~41k trials across 4 statuses, generating a decision matrix and the SVEF candidate pool (~22k candidates).

2.  **Phase 2: Feature Enrichment**
    ```bash
    python src/features/enrich_dataset.py
    ```
    Joins clinical metadata and retrieves molecular SMILES.

3.  **Phase 3: Coverage Analysis**
    ```bash
    python src/visualization/analyze_coverage.py
    ```
    Quantifies data quality and exports the **Gold Standard** subset.

## 6. Project Structure
```text
├── data/
│   ├── raw/             # AACT source files (.txt)
│   ├── interim/audit/   # Detailed snapshots and decision matrices
│   └── processed/       # Final SVEF and Gold Standard datasets
├── docs/                # Detailed methodologies and pipeline guides
├── src/                 # Source code (audit, data, features, viz)
└── reports/             # Figures and audit summaries
```
