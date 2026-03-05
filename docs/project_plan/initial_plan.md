# Implementation Plan: SVEF Unified Dataset Construction

## 1. Overview
This project identifies "stranded" small-molecule drug assets from ClinicalTrials.gov (AACT). It prioritizes trials that failed Phase 2/3 for efficacy while maintaining a clean safety profile across four key clinical statuses: **Terminated**, **Suspended**, **Withdrawn**, and **Unknown**.

## 2. Technical Stack
- **Source Directory:** `data/raw/` (AACT flat files).
- **Environment:** Python 3.12+ (Virtual environment `.svef`).
- **Core Libraries:** `pandas`, `re` (regex), `requests` (PUG-REST API).

## 3. Step-by-Step Methodology

### Step 1: Structural Audit (Wide Net)
- **Target Phases:** Phase 2, Phase 3, Phase 2/3.
- **Target Statuses:** Terminated, Suspended, Withdrawn, Unknown.
- **Study Type:** Interventional only.
- **Snapshot Logic:** Save snapshots of initial Phase 2/3 pools to `data/interim/audit/` for each status to ensure transparency.

### Step 2: Intervention Filtering
- Perform an `inner join` with `interventions.txt` to isolate trials with "DRUG" types.
- **Biologics Exclusion:** Use a regex-based pattern to exclude monoclonal antibodies (`mab`), vaccines, cell/gene therapies, and other complex biologics. This ensures a clean set of small molecules for DTI analysis.

### Step 3: Unified Signality Logic (The "Core Audit")
- **Word Boundaries:** All text-mining uses regex word boundaries (`\bkeyword\b`) to prevent false positives (e.g., "harm" matching within "pharmaceutical").
- **Complex Negation Logic:** Advanced logic detects phrases that negate both safety and efficacy (e.g., "not for reasons of efficacy or safety," "not related to any efficacy issues").
- **Audit Categorization:**
    - **EFFICACY_FAILURE:** Explicit scientific failure keywords (futility, endpoint not met).
    - **CLEAN_EXIT:** Terminated for non-scientific reasons (business, logistics).
    - **SAFETY_CONCERN:** Explicit safety/toxicity triggers (toxic, side effect).
- **Output Audit Trace:** Generate `svef_logic_audit.csv` containing every trial and the keywords ("triggers") that determined its classification.

### Step 4: Cross-Trial Linking
- **NCT Aliases:** Scan `id_information.txt` to identify shared NCT IDs or organization study IDs.
- **Connected Trials Feature:** Concatenate related NCT IDs into a `connected_trials` feature for each candidate. This allows researchers to track a drug's entire clinical history across different phases.

### Step 5: Chemical & Evidence Enrichment
- Retrieve Canonical SMILES from the **PubChem PUG-REST API**.
- Process scholarly publications and rank them by **Evidence_Confidence** (prioritizing PMIDs).

## 4. Final Quality Control
- **Coverage Analysis:** Generate visualizations (Venn/Stacked Bar) to show the overlap of chemical and scholarly data.
- **Gold Standard Subset:** Export a subset of candidates that have both structural data and evidence-rich publications.
