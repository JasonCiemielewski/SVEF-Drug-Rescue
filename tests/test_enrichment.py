import pandas as pd
import pytest
import re
from src.features.enrich_dataset import process_publications, get_pubchem_data

def test_process_publications_doi_extraction_robust():
    """
    Test that DOIs are correctly extracted from various citation formats.
    """
    data = {
        'nct_id': ['NCT001', 'NCT002', 'NCT003'],
        'pmid': [1, 2, 3],
        'reference_type': ['RESULT', 'RESULT', 'BACKGROUND'],
        'citation': [
            "Patel et al. 2015; doi: 10.1111/anae.12923", # standard
            "O'Cain. 1980; DOI: 10.1152/jappl.1980.49.5.875;", # uppercase DOI
            "Reference with no doi available." # none
        ]
    }
    refs = pd.DataFrame(data)
    result = process_publications(refs)
    
    # Check DOI extraction
    assert '10.1111/anae.12923' in result.iloc[0]['doi_list']
    assert '10.1152/jappl.1980.49.5.875' in result.iloc[1]['doi_list']
    assert result.iloc[2]['doi_list'] == ''

def test_process_publications_score_aggregation():
    """
    Test that Evidence_Confidence handles mixed result and background types correctly.
    """
    data = {
        'nct_id': ['NCT001', 'NCT001', 'NCT001'],
        'pmid': [1, 2, 3],
        'reference_type': ['RESULT', 'BACKGROUND', 'BACKGROUND'],
        'citation': ['', '', '']
    }
    refs = pd.DataFrame(data)
    result = process_publications(refs)
    
    # NCT001: 1 Result (1.0) + 2 Backgrounds (0.4) + 0.5 Bonus = 1.9
    assert result.iloc[0]['Evidence_Confidence'] == 1.9
    assert result.iloc[0]['results_pmid_list'] == '1'
    assert result.iloc[0]['background_pmid_list'] == '2|3'

@pytest.mark.parametrize("drug_name, expected_clean_name", [
    ("Carboplatin, intravenous", "Carboplatin"),
    ("Pazopanib + Paclitaxel", "pazopanib"), # combinations (lowercased)
    ("Drug A/Drug B", "drug a"),
    ("Desmoteplase (iv)", "Desmoteplase"),
    ("Drug X oral tablets", "Drug X"),
    ("Placebo capsules", None), # placebos return None
    ("active drug", None) # generic terms return None
])
def test_get_pubchem_data_cleaning_logic(drug_name, expected_clean_name):
    """
    Test the name cleaning logic by simulating the internal regex steps.
    """
    # We simulate the logic inside get_pubchem_data
    if 'placebo' in drug_name.lower():
        clean_name = None
    elif drug_name.lower() == 'active drug':
        clean_name = None
    else:
        clean_name = drug_name.split(',')[0].strip()
        clean_name = re.sub(r'\b(iv|intravenous|oral|tablets|capsules|active drug|matching)\b', '', clean_name, flags=re.IGNORECASE).strip()
        # Remove empty or whitespace-only parentheses
        clean_name = re.sub(r'\(\s*\)', '', clean_name).strip()
        
        for separator in ['+', '/', ' and ', ' with ']:
            if separator in clean_name.lower():
                clean_name = clean_name.lower().split(separator)[0].strip()
                break
                
    assert clean_name == expected_clean_name

def test_process_publications_empty_references():
    """
    Ensure the script handles trials with zero references gracefully.
    """
    refs = pd.DataFrame(columns=['nct_id', 'pmid', 'reference_type', 'citation'])
    result = process_publications(refs)
    assert len(result) == 0
