# Analysis Plan: Publication vs. SMILES Data Coverage

## 1. Objective
To quantify and visualize the overlap between trials that have associated peer-reviewed publications and candidates that have retrieved SMILES data. This identifies the most "de-risked" and "model-ready" drug assets in the SVEF dataset.

## 2. Methodology

### Step 1: Feature Binarization
- Load `data/processed/SVEF_Enriched_Final.csv`.
- Create two indicator variables:
    - **`has_pub`**: `True` if `publication_count > 0`, else `False`.
    - **`has_smiles`**: `True` if `is_dti_ready == True`, else `False`.

### Step 2: Contingency Analysis (Cross-Tabulation)
- Generate a 2x2 contingency table to count candidates in each quadrant:
    1. **Gold Standard:** (Has Publication AND Has SMILES)
    2. **Model-Ready Only:** (No Publication BUT Has SMILES)
    3. **Evidence-Rich Only:** (Has Publication BUT No SMILES)
    4. **Data Poor:** (No Publication AND No SMILES)

### Step 3: Statistical Comparison
- Calculate the percentage of SMILES-matched drugs that also have publication support.
- Compare the average `Safety_Score` between the "Gold Standard" group and the rest of the dataset.
- Evaluate if Industry-sponsored assets are more likely to have both data types compared to Academic assets.

### Step 4: Visualization
- **Venn Diagram:** To visualize the intersection of the two sets.
- **Stacked Bar Chart:** Distribution of publication status across SMILES-ready vs. non-SMILES-ready candidates.

### Step 5: Identification of "Gold Standard" Subset
- Export a filtered CSV: `data/processed/SVEF_Gold_Standard_Candidates.csv`.
- This subset contains candidates that are ready for immediate DTI modeling and have peer-reviewed clinical context.

## 3. Implementation Strategy
- Create a new Jupyter Notebook `notebooks/Coverage_Comparison_Analysis.ipynb` OR a standalone script `src/visualization/analyze_coverage.py`.
- Use `matplotlib` and `seaborn` for visualizations.

## 4. Expected Deliverables
- A summary report in the console/notebook.
- A high-quality plot (PNG) saved to `reports/figures/`.
- The "Gold Standard" candidate list.
