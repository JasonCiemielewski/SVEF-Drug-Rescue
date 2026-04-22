# SVEF Enriched Dataset: Data Dictionary (Architect Edition)

This document defines the features, underlying formulas, and rationales for the final `SVEF_Enriched_Final.csv` dataset.

---

## 1. Clinical Core Identifiers
| Feature | Description | Source |
| :--- | :--- | :--- |
| `nct_id` | Unique identifier for the clinical trial. | AACT: `studies` |
| `name` | Raw name of the drug intervention. | AACT: `interventions` |
| `group_type` | Clinical role assigned to the drug (e.g., EXPERIMENTAL, PLACEBO). | Relational Mapping |
| `overall_status` | Status at snapshot (TERMINATED, SUSPENDED, WITHDRAWN, UNKNOWN). | AACT: `studies` |
| `phase` | Clinical Phase (PHASE2, PHASE3, PHASE2/PHASE3). | AACT: `studies` |

## 2. NLP Signality & Audit
| Feature | Description | Logic |
| :--- | :--- | :--- |
| `audit_status` | Final pipeline verdict (e.g., `EFFICACY_FAILURE`, `CLEAN_EXIT`). | NLP Audit |
| `why_stopped` | Sponsor-provided reason for trial halt. | AACT: `studies` |
| `inclusion_trigger` | Keywords that flagged an efficacy failure. | `\b(futility|efficacy|...)\b` |
| `exclusion_trigger` | Keywords that flagged a safety concern. | `\b(toxic|ae|side effect|...)\b` |

## 3. Chemical Properties & Recovery
| Feature | Description | Formula / Threshold |
| :--- | :--- | :--- |
| `smiles` | Simplified Molecular Input Line Entry System. | PubChem API |
| `matched_by` | Recovery tier used (Name, CAS, or Synonym). | Pipeline Tier Logic |
| `failure_reason` | Classification of match failure (e.g., `PLACEBO_EQUIVALENT`). | NLP Classification |
| `molecular_weight` | Molecular mass in Daltons. | PubChem API |
| `logp` | Octanol-water partition coefficient (hydrophobicity). | PubChem API |
| `is_lipinski_compliant` | Boolean flag for small-molecule "druggability." | `(MW < 500) & (LogP < 5)` |

## 4. Human Safety & Exposure Metrics
| Feature | Description | Formula |
| :--- | :--- | :--- |
| `enrollment` | Total raw participant count. | AACT: `studies` |
| `log_enrollment` | Log-transformed enrollment to normalize outliers. | $f(x) = \ln(1 + enrollment)$ |
| `trial_duration_days` | Calculated lifespan of the trial. | $primary\_completion - start\_date$ |
| `Safety_Score` | Normalized metric of human safety data volume. | $mean(norm\_enrollment, norm\_duration)^*$ |

*\*Note: Safety_Score is calculated using NaN-aware averaging. If one component is missing, the other is used. If both are missing, the result is `NaN`.*

## 5. Scholarly Evidence Metrics
| Feature | Description | Formula |
| :--- | :--- | :--- |
| `publication_count` | Distinct PMIDs associated with the trial. | $count(PMIDs)$ |
| `Evidence_Confidence` | Weighted score of published scientific evidence. | $1.0(R) + 0.2(B) + 0.5^*$ |

**Evidence_Confidence Weighting:**
*   **R (Results):** 1.0 points for each result-type publication.
*   **B (Background):** 0.2 points for each background reference.
*   **Bonus (0.5):** Added if at least one result-type publication exists.
*   **Goal:** Prioritizes drugs with confirmed results over those only mentioned in background literature.
