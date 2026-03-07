# Full Production Pipeline Trace: Every Data Transformation

This document provides a line-by-line accounting of every action, join, rename, and calculation performed by the SVEF production pipeline.

---

## Top-Level Orchestration (`main.py`)
The pipeline is entry-pointed through `main.py`, which manages the sequence and dependencies:
1.  **`--audit`**: Triggers `audit_global_trials`. (Global Denominator Audit)
2.  **`--refine`**: Triggers `refine_svef_assets`. (SVEF Candidate Identification)
3.  **`--enrich`**: Triggers `recover_smiles`. (Bioinformatics Enrichment)

---

## Stage 1: Candidate Extraction (`src/audit/audit_engine.py`)

### 1. Ingestion
*   **Action:** Loads `studies.txt`, `interventions.txt`, and `id_information.txt`.
*   **Parameter:** Pipe (`|`) delimited.

### 2. Structural Gating (`filter_structural`)
*   **Subset Selection:** Selects `nct_id`, `study_type`, `phase`, `overall_status`, `why_stopped`.
*   **Metadata Masking:**
    *   Filter: `study_type == 'INTERVENTIONAL'`
    *   Filter: `phase in ['PHASE2', 'PHASE3', 'PHASE2/PHASE3']`
    *   Filter: `overall_status in ['TERMINATED', 'SUSPENDED', 'WITHDRAWN', 'UNKNOWN']`
*   **Intervention Join:** 
    *   **Action:** Inner merge with `interventions.txt` on `nct_id`.
    *   **Transformation:** Filters rows where `intervention_type == 'DRUG'`.
*   **Primary Biologics Purge:**
    *   **Action:** Regex exclusion on `name` column.
    *   **Pattern:** `-(?:mab|fusp|cept|zumab|ximab|umab|ase|alfa|beta|gamma)$|vaccine|cell therapy|antibody|gene therapy|antigen`.

### 3. NLP Signality Audit (`apply_unified_svef_logic`)
*   **Text Normalization:**
    *   **Action:** Lowercase and strip `why_stopped`.
    *   **Transformation:** Fill `NaN` with empty string `""`.
*   **Signality Triggering (Regex):**
    *   `has_eff`: `\b(?:futility|efficacy|lack of effect|benefit|endpoint|superiority|insufficient signal)\b`
    *   `has_safe`: `\b(?:toxic|adverse event|harm|safety|risk|death|mortality|aes)\b`
    *   `is_negated`: Comprehensive list of 14+ protection phrases (e.g., "not for efficacy").
*   **Classification Logic:**
    *   `eff_flag`: `has_eff` AND NOT `is_negated`.
    *   `safe_flag`: `has_safe` AND NOT `is_negated`.
*   **Audit Status Assignment:**
    *   Assigns `EFFICACY_FAILURE`, `CLEAN_EXIT`, or `SAFETY_CONCERN`.
    *   **Rule:** Safety always takes precedence in exclusion.

### 4. Cross-Trial Linking (`link_trials`)
*   **ID Extraction:**
    *   **Action:** Regex `(NCT\d{8})` applied to `id_information.id_value`.
*   **Aggregation:**
    *   **Action:** `groupby('nct_id')`.
    *   **Transformation:** Join unique linked NCT IDs into a pipe-separated string in column `connected_trials`.

---

## Stage 2: Enrichment & Recovery (`src/features/enrich_dataset.py`)

### 1. Relational Ingestion & Hardening (`load_data`)
*   **Ingestion:** Loads 7 supplemental AACT tables using chunk-based filter-loading.
*   **Transformation (Renaming):**
    *   `design_groups`: `id` -> `design_group_id`
    *   `interventions`: `id` -> `intervention_id`
*   **Transformation (Type Casting):**
    *   **Action:** `astype(str)` applied to all `nct_id`, `id`, `design_group_id`, and `intervention_id` columns.

### 2. Total Evidence Role Mapping (`map_intervention_roles`)
*   **Action:** Inner merge `design_group_interventions` and `design_groups`.
*   **Transformation (Aggregation):**
    *   **Action:** `groupby(['nct_id', 'intervention_id'])`.
    *   **Result:** Collapses multiple arm roles into a single pipe-separated string (e.g., `Placebo|Active Comparator`).
*   **Action:** Left merge roles back to candidates on `nct_id` and `id`.

### 3. Clinical Metadata Merging
*   **Lead Sponsor Join:** Left merge with `sponsors.txt` filtered for `lead_or_collaborator == 'lead'`.
*   **MeSH Aggregation:**
    *   **Action:** `groupby('nct_id')`.
    *   **Transformation:** Join unique `mesh_term` into pipe-separated string.
*   **Date and Duration Merge:** Left merge with `studies` and `calculated_values`.

### 4. Advanced Feature Engineering
*   **Duration Calculation:**
    *   **Formula:** `primary_completion_date - start_date`.
    *   **Constraint:** Keeps `NaN` if dates are missing.
*   **Enrollment Normalization:**
    *   **Formula:** $f(x) = \ln(1 + enrollment)$
*   **Safety Score Calculation:**
    *   **Formula:** $mean(norm\_enrollment, norm\_duration)$.
    *   **Mechanism:** NaN-aware mean (if one is missing, use the other; if both missing, result is `NaN`).

### 5. Scholarly Evidence Processing
*   **DOI Extraction:** Regex `doi:\s*([^\s;]+)` on citation text.
*   **Confidence Scoring:**
    *   **Formula:** $(1.0 	imes count(Result)) + (0.2 	imes count(Background)) + 0.5 	ext{ (if Result exists)}$.

### 6. Bioinformatics Recovery (`enrich_with_pubchem_architect`)
*   **Nomenclature Cleaning (`clean_drug_name`):**
    1.  Regex: Strip `[]` and `()`.
    2.  Split: `,`, `;`, `+`, `/`, ` and `, ` with `.
    3.  Regex: Strip dosage units (`mg`, `mg/kg`, etc.).
    4.  Regex: Strip salt forms (`hydrochloride`, `phosphate`, etc.).
    5.  Regex: Strip percentages (`0.5%`).
    6.  Regex: Strip trailing lone digits.
    7.  Trim: Non-alphanumeric characters from ends.
*   **Tiered Lookup Logic:**
    *   **Tier 1:** Name lookup.
    *   **Tier 2:** CAS extraction from Title + Lookup.
    *   **Tier 3:** Synonym retrieval + Lookup.
*   **Hardened JSON Parsing:**
    *   **Priority:** `IsomericSMILES` -> `SMILES` -> `CanonicalSMILES`.
*   **Lipinski Compliance:**
    *   **Threshold:** `(MW < 500) & (LogP < 5)`.

### 7. Failure Categorization
*   **Action:** Non-matched assets classified into `PLACEBO_EQUIVALENT`, `LOGISTICAL_GENERIC`, or `POSSIBLE_INTERNAL_PROPRIETARY`.

---

## Stage 3: Quality Control & finalization (`src/visualization/analyze_coverage.py`)

### 1. Deduplication
*   **Action:** `drop_duplicates(subset=['nct_id', 'name'])`.
*   **Purpose:** Ensures unique primary key.

### 2. Integrity Imputation
*   **Action:** `fillna(0)` applied **only** to `publication_count` and `Evidence_Confidence`.
*   **Rationale:** Factual representation of zero evidence.

### 3. Gold Standard Identification
*   **Rule:** Trial must possess both `is_dti_ready (SMILES)` AND `has_pub (Publication)`.
