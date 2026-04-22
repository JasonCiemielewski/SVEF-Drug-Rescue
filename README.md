# SVEF - Drug Rescue Project (v2.0)

## Project Overview
This project focuses on identifying potential drug rescue leads from clinical trial failures using high-fidelity data modeling. The current project direction has shifted from a modular CLI-based pipeline to a model-centric workflow.

## Current Primary Method
The core logic and development are now centered in:
- **`notebooks/model_creation.ipynb`**: This notebook handles the raw AACT data processing using a chunk-based "Sieve" approach to filter for Interventional, Experimental Drug trials and prepares the data for high-fidelity modeling.

## Legacy Archive
The original production pipeline (v1.0), including its modular source code, tests, and documentation, has been archived for future reference and comparison.
- **Location**: `legacy_pipeline/`
- **Reference**: See `legacy_pipeline/README_v1.md` and `legacy_pipeline/PIPELINE_DETAILS.md` for details on the previous architecture.

---
*BIFX546 Final Project*
