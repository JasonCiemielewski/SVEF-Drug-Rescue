import pytest
import pandas as pd
from unittest.mock import patch, MagicMock
from src.features.enrich_dataset import query_pubchem, get_pubchem_data_tiered

def test_query_pubchem_isomeric_key():
    """Verify handling when PubChem returns 'IsomericSMILES' (Standard)."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "PropertyTable": {
            "Properties": [{"CID": 123, "IsomericSMILES": "CC(=O)O", "SMILES": "CC(=O)O", "MolecularWeight": 60.05, "XLogP": 0.5}]
        }
    }
    
    with patch('requests.get', return_value=mock_response):
        cid, smiles, mw, logp = query_pubchem("TestDrug")
        assert cid == 123
        assert smiles == "CC(=O)O"

def test_query_pubchem_generic_smiles_key():
    """Verify handling when PubChem returns the generic 'SMILES' key (The recent bug fix)."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "PropertyTable": {
            "Properties": [{"CID": 456, "SMILES": "C1=CC=CC=C1", "MolecularWeight": 78.11, "XLogP": 2.1}]
        }
    }
    
    with patch('requests.get', return_value=mock_response):
        cid, smiles, mw, logp = query_pubchem("Benzene")
        assert smiles == "C1=CC=CC=C1"
        assert cid == 456

def test_query_pubchem_503_retry_logic():
    """Verify handling of 503 Server Busy errors."""
    mock_response_503 = MagicMock()
    mock_response_503.status_code = 503
    
    with patch('requests.get', return_value=mock_response_503):
        with patch('time.sleep', return_value=None) as mock_sleep:
            cid, smiles, mw, logp = query_pubchem("BusyDrug")
            assert smiles is None
            assert mock_sleep.called

def test_get_pubchem_data_tiered_cas_fallback():
    """Verify that CAS numbers are extracted and used if name lookup fails."""
    # First call (Name) returns nothing, Second call (CAS) returns SMILES
    mock_fail = MagicMock()
    mock_fail.status_code = 404
    
    mock_success = MagicMock()
    mock_success.status_code = 200
    mock_success.json.return_value = {
        "PropertyTable": {
            "Properties": [{"CID": 2244, "SMILES": "CC(=O)OC1=CC=CC=C1C(=O)O"}]
        }
    }
    
    with patch('requests.get', side_effect=[mock_fail, mock_success]):
        # Context contains CAS 50-78-2 (Aspirin)
        cid, smiles, mw, logp, tier = get_pubchem_data_tiered("UnknownName", "Trial context with CAS 50-78-2")
        assert smiles == "CC(=O)OC1=CC=CC=C1C(=O)O"
        assert tier == "CAS"

def test_get_pubchem_data_tiered_placebo():
    """Verify that placebos are ignored without API calls."""
    with patch('requests.get') as mock_get:
        cid, smiles, mw, logp, tier = get_pubchem_data_tiered("Placebo matching Drug X")
        assert tier == "Failed"
        assert not mock_get.called
