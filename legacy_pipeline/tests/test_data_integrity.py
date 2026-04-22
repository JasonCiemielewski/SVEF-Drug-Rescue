import pandas as pd
import pytest
import os

def test_processed_dataset_integrity():
    """
    Perform structural and data-level checks on the final SVEF Enriched dataset.
    """
    file_path = os.path.join('data', 'processed', 'SVEF_Enriched_Final.csv')
    
    if not os.path.exists(file_path):
        pytest.skip("SVEF_Enriched_Final.csv not found, skipping data integrity test.")
    
    df = pd.read_csv(file_path)
    
    # 1. No Duplicates
    duplicates = df.duplicated(subset=['nct_id', 'name']).sum()
    assert duplicates == 0, f"Found {duplicates} duplicate trial-intervention pairs."
    
    # 2. Safety_Score Range [0.0, 1.0]
    assert df['Safety_Score'].between(0.0, 1.0).all(), "Safety_Score contains values outside 0-1 range."
    
    # 3. Evidence_Confidence Non-Negative
    assert (df['Evidence_Confidence'].fillna(0) >= 0).all(), "Evidence_Confidence contains negative values."
    
    # 4. Mandatory Columns Present
    mandatory_cols = ['nct_id', 'name', 'eff_mask', 'safe_mask', 'Safety_Score', 'is_dti_ready']
    for col in mandatory_cols:
        assert col in df.columns, f"Mandatory column '{col}' missing from final dataset."

def test_gold_standard_subset_validity():
    """
    Ensure the Gold Standard subset actually meets its criteria.
    """
    file_path = os.path.join('data', 'processed', 'SVEF_Gold_Standard_Candidates.csv')
    
    if not os.path.exists(file_path):
        pytest.skip("SVEF_Gold_Standard_Candidates.csv not found, skipping gold standard test.")
    
    df = pd.read_csv(file_path)
    
    # Gold Standard criteria: is_dti_ready AND publication_count > 0
    assert df['is_dti_ready'].all(), "Found non-DTI-ready candidates in Gold Standard subset."
    assert (df['publication_count'] > 0).all(), "Found candidates with zero publications in Gold Standard subset."
