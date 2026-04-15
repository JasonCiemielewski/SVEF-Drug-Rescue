import pytest
import pandas as pd
import numpy as np
import os
import sys
from datetime import datetime

# Ensure the src directory is in the path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.audit.svef_refinement import calculate_duration

def test_calculate_duration():
    """Test duration calculation logic."""
    # Standard valid dates
    row1 = {'start_date': pd.to_datetime('2020-01-01'), 'primary_completion_date': pd.to_datetime('2021-01-01')}
    assert calculate_duration(row1) == 366 # Leap year 2020
    
    # Missing end date
    row2 = {'start_date': pd.to_datetime('2020-01-01'), 'primary_completion_date': pd.NaT}
    assert np.isnan(calculate_duration(row2))
    
    # Negative duration (end before start)
    row3 = {'start_date': pd.to_datetime('2021-01-01'), 'primary_completion_date': pd.to_datetime('2020-01-01')}
    assert np.isnan(calculate_duration(row3))
    
    # Same date
    row4 = {'start_date': pd.to_datetime('2020-01-01'), 'primary_completion_date': pd.to_datetime('2020-01-01')}
    assert np.isnan(calculate_duration(row4))
