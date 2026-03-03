# Methodology: Small-Molecule vs. Biologic Differentiation

This document explains the multi-tiered filtering strategy used to isolate small-molecule drug candidates from the broader AACT dataset.

## 1. Taxonomic Filtering (AACT Metadata)
The initial processing step in `src/data/make_dataset.py` utilizes the structured `intervention_type` field.
*   **Filter:** `intervention_type == 'DRUG'`
*   **Rationale:** This removes non-pharmacological interventions such as `DEVICE`, `PROCEDURE`, `BEHAVIORAL`, and `DIETARY_SUPPLEMENT`. However, the 'DRUG' category still contains large-molecule biologics.

## 2. Linguistic Filtering (Keyword Exclusion)
To refine the 'DRUG' category, a regex-based exclusion is applied to the `name` column of the interventions table. This identifies and removes "obvious" biologics based on nomenclature conventions.
*   **Excluded Keywords:**
    *   `mab`: Targeting monoclonal antibodies (e.g., adalimumab).
    *   `vaccine`: Excluding prophylactic and therapeutic vaccines.
    *   `cell therapy`: Excluding cellular-based products.
    *   `antibody`: Excluding polyclonal or specific antibody treatments.
    *   `gene therapy`: Excluding viral vectors and genetic constructs.

## 3. Structural Validation (PubChem Enrichment)
The final and most robust distinction occurs during the "Feature Engineering" phase in `src/features/enrich_dataset.py`.
*   **Logic:** The script attempts to retrieve a **SMILES** (Simplified Molecular Input Line Entry System) string and **Molecular Weight** from the PubChem PUG-REST API.
*   **Differentiation:** 
    *   **Small Molecules:** Typically possess a unique CID (Compound ID) and a canonical SMILES string in the PubChem `compound` property table.
    *   **Biologics:** Large proteins, antibodies, and complex vaccines often lack a canonical SMILES string or fall outside the property table scope for standard chemical descriptors.
*   **DTI-Ready Flag:** Only candidates with a successfully retrieved SMILES string are flagged as `is_dti_ready = True`, effectively filtering the final dataset for molecules compatible with Deep Learning Drug-Target Interaction (DTI) models.
