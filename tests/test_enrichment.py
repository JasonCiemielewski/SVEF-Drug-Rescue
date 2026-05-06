import pandas as pd
import pytest
from src.features.enrichment import prepare_cache_df, merge_pubchem_features

def test_prepare_cache_df():
    sample_cache = {
        "Foscarnet": {"MolecularWeight": 126.0, "CanonicalSMILES": "C1", "XLogP": 1.0},
        "Ganciclovir": {"MolecularWeight": 255.0, "ConnectivitySMILES": "C2", "XLogP": 2.0},
        "Empty": None
    }
    
    cache_df = prepare_cache_df(sample_cache)
    
    assert len(cache_df) == 2
    assert "foscarnet" in cache_df['clean_name_lookup'].values
    assert cache_df.loc[cache_df['clean_name_lookup'] == 'ganciclovir', 'smiles'].values[0] == "C2"

def test_merge_pubchem_features():
    main_df = pd.DataFrame({
        "clean_name": ["FOSCARNET", " Ganciclovir ", "UnknownDrug"]
    })
    
    cache_df = pd.DataFrame([
        {"clean_name_lookup": "foscarnet", "smiles": "C1", "molecular_weight": 126.0, "xlogp": 1.0},
        {"clean_name_lookup": "ganciclovir", "smiles": "C2", "molecular_weight": 255.0, "xlogp": 2.0}
    ])
    
    enriched = merge_pubchem_features(main_df, cache_df)
    
    assert len(enriched) == 3
    assert enriched.loc[0, 'smiles'] == "C1"
    assert enriched.loc[1, 'smiles'] == "C2"
    assert pd.isna(enriched.loc[2, 'smiles'])
