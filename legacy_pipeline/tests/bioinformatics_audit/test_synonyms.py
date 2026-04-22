import pytest
from unittest.mock import patch, MagicMock
from src.features.enrich_dataset import get_pubchem_data_tiered

def test_get_pubchem_data_tiered_synonym_fallback():
    """Verify that synonyms are queried if Tier 1 and Tier 2 fail."""
    # Mock sequence:
    # 1. Tier 1 Name lookup -> 404
    # 2. Tier 3 Synonym List lookup -> 200 (Returns ['AliasX'])
    # 3. Tier 3 Synonym lookup -> 200 (Returns SMILES)
    
    mock_404 = MagicMock()
    mock_404.status_code = 404
    
    mock_syn_list = MagicMock()
    mock_syn_list.status_code = 200
    mock_syn_list.json.return_value = {
        "InformationList": {
            "Information": [{"Synonym": ["AliasX"]}]
        }
    }
    
    mock_success = MagicMock()
    mock_success.status_code = 200
    mock_success.json.return_value = {
        "PropertyTable": {
            "Properties": [{"CID": 999, "SMILES": "CN1C=NC2=C1C(=O)N(C(=O)N2C)C"}] # Caffeine
        }
    }
    
    # We patch requests.get to return this sequence
    with patch('requests.get', side_effect=[mock_404, mock_syn_list, mock_success]):
        cid, smiles, mw, logp, tier = get_pubchem_data_tiered("UnknownBrandName", "")
        
        assert tier == "Synonym"
        assert smiles == "CN1C=NC2=C1C(=O)N(C(=O)N2C)C"
        assert cid == 999
