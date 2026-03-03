# SVEF Dataset Construction: Safety-Validated/Efficacy-Failed

## Overview
This project identifies "stranded" small-molecule drug assets from ClinicalTrials.gov (AACT) that failed in Phase 2 or 3 due to lack of efficacy but maintained a clean safety profile. These candidates are valuable for drug repositioning and "Target Fishing" using deep learning models.

## Structure
- `data/`: Raw AACT files and processed SVEF results.
- `docs/`: References and project planning documents.
- `src/`: Source code for data processing and future enrichment.
- `notebooks/`: Exploratory Data Analysis.

## Quick Start
1. Ensure the `.svef` environment is activated.
2. Run the dataset generation:
   ```bash
   python src/data/make_dataset.py
   ```
3. Processed results are available in `data/processed/SVEF_candidates.csv`.
