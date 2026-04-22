import pytest
import pandas as pd
import numpy as np
from src.features.enrich_dataset import feature_engineering_advanced

def test_feature_engineering_nan_integrity():
    """Verify that missing enrollment/duration stays NaN and doesn't bias the score."""
    mock_df = pd.DataFrame([
        {'nct_id': 'NCT1', 'enrollment': 100, 'start_date': '2020-01-01', 'primary_completion_date': '2020-01-11'}, # 10 days
        {'nct_id': 'NCT2', 'enrollment': np.nan, 'start_date': '2020-01-01', 'primary_completion_date': '2020-01-21'}, # 20 days
        {'nct_id': 'NCT3', 'enrollment': np.nan, 'start_date': np.nan, 'primary_completion_date': np.nan} # All missing
    ])
    
    result = feature_engineering_advanced(mock_df)
    
    # Assert NaN integrity
    assert pd.isna(result.loc[1, 'enrollment'])
    assert pd.isna(result.loc[1, 'norm_enrollment'])
    
    # Assert Safety_Score calculation
    # NCT1: Has both (should be non-NaN)
    assert not pd.isna(result.loc[0, 'Safety_Score'])
    
    # NCT2: Has duration (20 days) but missing enrollment. 
    # Safety_Score should be non-NaN because it averages available components.
    assert not pd.isna(result.loc[1, 'Safety_Score'])
    
    # NCT3: Both missing. Score must be NaN.
    assert pd.isna(result.loc[2, 'Safety_Score'])

def test_log_enrollment_normalization():
    """Verify that log1p is applied to enrollment."""
    mock_df = pd.DataFrame([
        {'nct_id': 'NCT1', 'enrollment': 0, 'start_date': '2020-01-01', 'primary_completion_date': '2020-01-02'},
        {'nct_id': 'NCT2', 'enrollment': 99, 'start_date': '2020-01-01', 'primary_completion_date': '2020-01-02'}
    ])
    result = feature_engineering_advanced(mock_df)
    
    # log1p(0) = 0
    assert result.loc[0, 'log_enrollment'] == 0
    # log1p(99) = log(100) approx 4.6
    assert result.loc[1, 'log_enrollment'] > 4.6
