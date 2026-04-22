import pytest
import pandas as pd
from src.features.enrich_dataset import map_intervention_roles

def test_map_intervention_roles_preserves_all():
    """Verify that multiple drugs in a trial are preserved with their roles."""
    mock_base = pd.DataFrame([
        {'nct_id': 'NCT1', 'id': '101', 'name': 'Metformin'},
        {'nct_id': 'NCT1', 'id': '102', 'name': 'Novel-X'}
    ])
    mock_groups = pd.DataFrame([
        {'nct_id': 'NCT1', 'design_group_id': '1', 'group_type': 'Placebo'},
        {'nct_id': 'NCT1', 'design_group_id': '2', 'group_type': 'Experimental'}
    ])
    mock_dg_int = pd.DataFrame([
        {'nct_id': 'NCT1', 'design_group_id': '1', 'intervention_id': '101'},
        {'nct_id': 'NCT1', 'design_group_id': '2', 'intervention_id': '102'}
    ])
    
    result = map_intervention_roles(mock_base, mock_groups, mock_dg_int)
    
    # Assert we still have 2 rows
    assert len(result) == 2
    # Assert roles are mapped
    assert result[result['name'] == 'Metformin']['group_type'].values[0] == 'Placebo'
    assert result[result['name'] == 'Novel-X']['group_type'].values[0] == 'Experimental'

def test_map_intervention_roles_collapses_multi_arm():
    """Verify that a drug in multiple arms has its roles collapsed."""
    mock_base = pd.DataFrame([{'nct_id': 'NCT2', 'id': '201', 'name': 'DrugY'}])
    mock_groups = pd.DataFrame([
        {'nct_id': 'NCT2', 'design_group_id': '1', 'group_type': 'Experimental'},
        {'nct_id': 'NCT2', 'design_group_id': '2', 'group_type': 'Active Comparator'}
    ])
    mock_dg_int = pd.DataFrame([
        {'nct_id': 'NCT2', 'design_group_id': '1', 'intervention_id': '201'},
        {'nct_id': 'NCT2', 'design_group_id': '2', 'intervention_id': '201'}
    ])
    
    result = map_intervention_roles(mock_base, mock_groups, mock_dg_int)
    # Roles should be sorted and pipe-separated
    assert result.iloc[0]['group_type'] == 'Active Comparator|Experimental'
