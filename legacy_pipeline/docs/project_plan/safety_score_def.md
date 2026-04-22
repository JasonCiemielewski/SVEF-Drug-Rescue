# Feature Definition: Safety_Score

## Overview
The **`Safety_Score`** is a quantitative proxy developed to represent the "safety validation depth" of each drug candidate within the SVEF (Safety-Validated/Efficacy-Failed) dataset. It serves as a metric for ranking the historical safety exposure of molecules that survived Phase 2/3 trials without being terminated for toxicity.

## Calculation Logic
The score is a composite, normalized value ranging from **0.0 (low confidence)** to **1.0 (high confidence)**. It is calculated through the following steps:

1.  **Normalization (Min-Max Scaling):**
    *   **Enrollment:** The total number of participants in the trial is scaled relative to the entire dataset (0 to 1).
    *   **Trial Duration:** The total number of days between the trial's start and completion is scaled relative to the entire dataset (0 to 1).
2.  **Weighted Fusion:**
    *   Both normalized values are given an equal weight (50% each) to balance the intensity of exposure (enrollment) with the duration of exposure.
    *   `Safety_Score = (Normalized_Enrollment * 0.5) + (Normalized_Duration * 0.5)`

## Rationale
*   **Exposure Quantification:** A higher enrollment signifies that more human subjects were exposed to the molecule without a safety-triggered halt, providing a larger statistical sample for safety validation.
*   **Temporal Validation:** Longer trial durations suggest the molecule’s safety profile was stable over an extended period of chronic or sub-chronic exposure.
*   **Conservative Bias:** In instances where data is missing (NaN), the score defaults toward 0.0, ensuring the pipeline prioritizes only the most well-documented "de-risked" assets.

## Application in IP Rescue
In the "Target Fishing" and Drug-Target Interaction (DTI) modeling phase, the `Safety_Score` allows researchers to:
1.  **Rank Candidates:** Prioritize molecules with the highest confirmed human safety exposure.
2.  **Filter Assets:** Identify "DTI-Ready" molecules (those with SMILES strings) that also meet a minimum safety validation threshold.
