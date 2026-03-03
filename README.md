# SVEF Dataset Construction: Safety-Validated/Efficacy-Failed

## 1. Overview
The **Safety-Validated/Efficacy-Failed (SVEF)** project identifies "stranded" small-molecule drug assets from ClinicalTrials.gov (AACT). These molecules have successfully passed Phase 1 safety hurdles but were terminated in Phase 2 or 3 for lack of efficacy. 

This dataset is designed for **IP Rescue** pipelines and **Drug Repositioning** using Deep Learning Drug-Target Interaction (DTI) models like ICAN.

## 2. Key Features
*   **Safety_Score (0.0–1.0):** Quantifies human safety exposure based on enrollment and trial duration.
*   **Evidence_Confidence (0.0–5.0):** Ranks scholarly validation by prioritizing direct trial result publications (PMIDs).
*   **DTI-Ready:** Integrated with **PubChem SMILES** strings and molecular descriptors.
*   **Curated Metadata:** Includes MeSH terms, lead sponsor class, and DOI links.

## 3. Installation & Setup
1.  **Clone the Repository:**
    ```bash
    git clone <repository_url>
    cd Final_Project
    ```
2.  **Environment Configuration:**
    Ensure you have Python 3.12+ installed. Create and activate the virtual environment:
    ```bash
    python -m venv .svef
    .svef\Scripts\activate  # Windows
    ```
3.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

## 4. Data Pipeline Execution
The pipeline is designed to be modular and idempotent.

1.  **Phase 1: Base Filtration**
    ```bash
    python src/data/make_dataset.py
    ```
    Identifies the initial 1,067 SVEF candidate trials from raw AACT data.

2.  **Phase 2: Feature Enrichment**
    ```bash
    python src/features/enrich_dataset.py
    ```
    Joins clinical metadata, processes publications (PMIDs/DOIs), and retrieves SMILES from PubChem.

3.  **Phase 3: Coverage Analysis & Visualization**
    ```bash
    python src/visualization/analyze_coverage.py
    ```
    Quantifies the overlap between scholarly and chemical data, exporting the **Gold Standard** subset.

## 5. Project Structure
For a detailed guide to all methodology and definitions, see the [**Documentation Index**](docs/INDEX.md).

```text
├── data/           # Raw source data and processed artifacts
├── docs/           # Detailed planning and methodologies
├── src/            # Modular source code (data, features, visualization)
├── notebooks/      # Exploratory Data Analysis
├── reports/        # Summary figures and plots
└── .svef/          # Local virtual environment
```

## 6. License
This project is for academic/research purposes. Clinical data is sourced from [ClinicalTrials.gov (AACT)](https://aact.ctti-clinicaltrials.org/).
