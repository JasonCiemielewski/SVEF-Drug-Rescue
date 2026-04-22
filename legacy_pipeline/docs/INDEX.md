# SVEF Project Documentation Index

Welcome to the **Safety-Validated/Efficacy-Failed (SVEF)** project documentation. This index provides a roadmap for navigating the research, implementation, and analysis of the IP Rescue pipeline.

## 1. Project Foundation & Planning
*   [**Initial Project Plan**](project_plan/initial_plan.md): The original implementation strategy and core SVEF filtration logic.
*   [**Enrichment Plan**](project_plan/enrichment_plan.md): Strategy for adding clinical volume, temporal data, and PubChem molecular descriptors.
*   [**Publication Enrichment Plan**](project_plan/publication_enrichment_plan.md): Methodology for linking trials to PMIDs and DOIs.

## 2. Methodology & Definitions
*   [**Molecule Differentiation**](project_plan/molecule_differentiation_method.md): How we distinguish small molecules from biologics using taxonomic and linguistic filtering.
*   [**Safety_Score Definition**](project_plan/safety_score_def.md): Quantitative logic for ranking human safety exposure depth.
*   [**Data Dictionary**](project_plan/data_dictionary.md): Comprehensive definitions for every column in the final enriched dataset.
*   [**Data Cleaning Methodology**](project_plan/data_cleaning_methodology.md): Technical details on regex cleaning and nomenclature standardization.

## 3. Pipeline & Automation
*   [**Pipeline Automation Guide**](PIPELINE.md): Instructions for running `main.py` and the modular execution flow.
*   [**Production Pipeline Trace**](PRODUCTION_PIPELINE_TRACE.md): A line-by-line accounting of every data transformation in the system.

## 4. Analysis & Results
*   [**Coverage Comparison Plan**](project_plan/coverage_comparison_plan.md): Strategy for analyzing the overlap between publication and SMILES data.
*   [**Gold Standard Analysis**](project_plan/coverage_comparison_plan.md): (Refer to results in `reports/figures/` and `data/processed/SVEF_Gold_Standard_Candidates.csv`).

## 5. Technical References
*   [**AACT Schema Reference**](references/aact_schema.png): The relational structure of the source ClinicalTrials.gov data.
*   [**Source Papers**](references/): Key literature supporting the ICAN and SVEF methodologies.
