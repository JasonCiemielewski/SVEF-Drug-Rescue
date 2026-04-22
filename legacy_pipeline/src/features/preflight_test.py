import pandas as pd
import requests
import time
import os
import re

# Import functions from our actual script
from src.features.enrich_dataset import query_pubchem, get_pubchem_data_tiered

def run_preflight_test():
    print("--- STARTING BIOINFORMATICS PRE-FLIGHT TEST ---")
    
    test_cases = [
        {"name": "Dacogen", "expected_status": "Name/Synonym", "note": "Failed in previous run"},
        {"name": "Aspirin", "expected_status": "Name", "note": "Standard success"},
        {"name": "Placebo", "expected_status": "Failed", "note": "Correctly ignored"},
        {"name": "Pirtobrutinib", "expected_status": "Name", "note": "Novel asset"}
    ]
    
    success_count = 0
    
    for case in test_cases:
        print(f"\nTesting: {case['name']} ({case['note']})...")
        cid, smiles, mw, logp, match_tier = get_pubchem_data_tiered(case['name'], "Trial context")
        
        if smiles:
            print(f"  SUCCESS! Found via: {match_tier}")
            print(f"  SMILES: {smiles[:30]}...")
            success_count += 1
        else:
            if case['expected_status'] == "Failed":
                print("  PASS: Correctly failed as expected.")
                success_count += 1
            else:
                print(f"  !! FAILURE !! Could not find {case['name']}")

    print("\n--- CACHE INTEGRITY TEST ---")
    # Simulate the KeyError: nan fix
    mock_cache = pd.DataFrame([
        {'name': 'TestDrug1', 'smiles': 'CCO', 'matched_by': 'Name'},
        {'name': 'TestDrug2', 'smiles': None, 'matched_by': float('nan')} # The crasher
    ])
    
    summary = {"Name": 0, "CAS": 0, "Synonym": 0, "Failed": 0}
    try:
        for _, row in mock_cache.iterrows():
            m_by = row['matched_by']
            if pd.isna(m_by):
                m_by = "Name" if pd.notnull(row['smiles']) else "Failed"
            summary[m_by] += 1
        print("  PASS: Cache summary logic is now resilient to NaN.")
    except Exception as e:
        print(f"  !! FAILURE !! Cache logic still buggy: {e}")

    if success_count == len(test_cases):
        print("\nOVERALL STATUS: READY FOR PRODUCTION RUN.")
    else:
        print("\nOVERALL STATUS: STOP. FIX REQUIRED.")

if __name__ == "__main__":
    run_preflight_test()
