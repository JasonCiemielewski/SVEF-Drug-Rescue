# Comprehensive Data Cleaning and Filtration Methodology (Architect Edition)

This document provides a high-resolution technical reference for the SVEF data pipeline. It details the transition from text-based assumptions to evidence-based relational mapping and tiered chemical recovery.

---

## Stage 1: Structural Extraction & NLP Logic
**Script:** `src/data/make_dataset.py`

*   **Metadata Gating:** Filters for Phase 2/3 Interventional trials with statuses indicating a halt (`TERMINATED`, `SUSPENDED`, `WITHDRAWN`, `UNKNOWN`).
*   **NLP Signality Audit:** 
    *   Uses regex word boundaries (`\b`) to prevent substring false positives.
    *   **Safety Precedence:** If both safety and efficacy keywords appear, safety triggers an automatic exclusion.
    *   **Negation Protection:** Explicitly handles phrases like "not for safety or efficacy" to prevent mislabeling strategic business decisions as scientific failures.

---

## Stage 2: Evidence-Based Asset Identification
**Script:** `src/features/enrich_dataset.py`  
**Function:** `identify_lead_assets`

This stage eliminates "text-blind" selection by using trial design structures to identify the true experimental molecule.

*   **Relational Mapping:** Ingests `design_groups.txt` and `design_group_interventions.txt` from AACT.
*   **Priority Hierarchy:**
    1.  **Experimental Arm:** Prioritizes drugs explicitly assigned to an "Experimental" arm in the trial design.
    2.  **SoC Filtering:** Automatically de-prioritizes known Standard of Care (SoC) drugs (e.g., Metformin, Aspirin, Placebo) even if they appear in experimental groups.
    3.  **Ambiguity Resolution:** If multiple novel drugs exist, it selects the primary listed intervention associated with the experimental arm.

---

## Stage 3: Tiered Chemical Recovery
**Script:** `src/features/enrich_dataset.py`  
**Function:** `get_pubchem_data_tiered`

Maximizes SMILES recovery by utilizing a three-tiered fallback mechanism via the PubChem PUG-REST API.

*   **Tier 1: Standard Name Lookup:** Standard string-based search using the cleaned drug name.
*   **Tier 2: CAS Registry Extraction:** Uses regex (`\b\d{2,7}-\d{2}-\d\b`) to extract CAS numbers from trial titles or descriptions and queries PubChem by CAS identifier.
*   **Tier 3: Synonym Resolution:** If Tiers 1 and 2 fail, the script retrieves all known synonyms for the name and attempts recovery on the top 3 aliases.

---

## Stage 4: Advanced Feature Engineering
**Script:** `src/features/enrich_dataset.py`  
**Function:** `feature_engineering_advanced`

*   **Log-Normalized Safety Metrics:** Applies `np.log1p` to enrollment data before Min-Max normalization to prevent large-scale trials from skewing the `Safety_Score`.
*   **Lipinski Compliance Check:** Calculates a boolean `is_lipinski_compliant` flag based on Rule of 5 criteria (MW < 500 Da, LogP < 5).
*   **NaN Integrity:** Maintains `NaN` for missing clinical values. `Safety_Score` is calculated using a NaN-aware mean of available components (Enrollment and Duration).

---

## Stage 5: Quality Control & Final Reporting
**Script:** `src/visualization/analyze_coverage.py`

*   **Evidence Traceability:** Every recovery is tagged with its source (Matched by: Name, CAS, or Synonym) in the `smiles_cache.csv`.
*   **Gold Standard Identification:** Filters for assets possessing both valid chemical structures (SMILES) and scholarly results (Publications).
*   **Data Integrity:** Fills missing publication counts with `0` (factual absence) while preserving `NaN` for clinical gaps.
