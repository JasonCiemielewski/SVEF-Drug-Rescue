import pandas as pd
import requests
import time
import os
import re
import sys
import shutil
from datetime import datetime

def get_pubchem_data(identifier, id_type='name'):
    """
    Tiered Lookup on PubChem PUG-REST API.
    """
    if not identifier or str(identifier).lower() in ['nan', 'placebo', 'active drug']:
        return None, None, None, None
    
    # Cleaning for API
    clean_id = str(identifier).split(',')[0].strip()
    if id_type == 'name':
        clean_id = re.sub(r'\b(iv|intravenous|oral|tablets|capsules|active drug|matching)\b', '', clean_id, flags=re.IGNORECASE).strip()
        # Handle combinations (take first)
        for separator in ['+', '/', ' and ', ' with ']:
            if separator in clean_id.lower():
                clean_id = clean_id.lower().split(separator)[0].strip()
                break
    
    base_url = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/{id_type}/{clean_id}/property/IsomericSMILES,ConnectivitySMILES,MolecularWeight,XLogP/JSON"
    
    try:
        response = requests.get(base_url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            props = data['PropertyTable']['Properties'][0]
            smiles = props.get('IsomericSMILES') or props.get('ConnectivitySMILES')
            return props.get('CID'), smiles, props.get('MolecularWeight'), props.get('XLogP')
    except Exception:
        pass
    return None, None, None, None

def get_synonyms(drug_name):
    """
    Fetch synonyms for a drug name from PubChem.
    """
    clean_name = str(drug_name).split(',')[0].strip()
    url = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/{clean_name}/synonyms/JSON"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            return response.json()['InformationList']['Information'][0].get('Synonym', [])[:3]
    except Exception:
        pass
    return []

def recover_smiles(processed_dir):
    """
    Module 3: Tiered Chemical Enrichment
    """
    print("Module 3: Starting Tiered Chemical Enrichment...")
    
    input_path = os.path.join(processed_dir, 'SVEF_candidates_raw.csv')
    main_output_path = os.path.join(processed_dir, 'SVEF_Enriched_Final.csv')
    archive_dir = os.path.join(processed_dir, 'archive')
    
    if not os.path.exists(archive_dir):
        os.makedirs(archive_dir)
        
    # Archive existing final file if it exists
    if os.path.exists(main_output_path):
        mtime = os.path.getmtime(main_output_path)
        timestamp = datetime.fromtimestamp(mtime).strftime('%Y%m%d_%H%M%S')
        archive_path = os.path.join(archive_dir, f'SVEF_Enriched_{timestamp}.csv')
        print(f"Archiving existing dataset to: {archive_path}")
        shutil.move(main_output_path, archive_path)
    
    if not os.path.exists(input_path):
        print(f"Error: {input_path} not found. Run Module 2 first.")
        return
    
    df = pd.read_csv(input_path)
    unique_drugs = df['name'].dropna().unique()
    print(f"Total Unique Drug Names to Process: {len(unique_drugs):,}")
    
    # Checkpoint logic
    checkpoint_path = os.path.join(processed_dir, 'smiles_cache.csv')
    if os.path.exists(checkpoint_path):
        cache_df = pd.read_csv(checkpoint_path)
        cache = cache_df.set_index('name').to_dict('index')
        print(f"Loaded {len(cache):,} results from checkpoint cache.")
    else:
        cache = {}

    processed_count = 0
    for drug in unique_drugs:
        if drug in cache and pd.notnull(cache[drug].get('smiles')):
            continue
            
        processed_count += 1
        if processed_count % 10 == 0:
            print(f"Processing drug {processed_count}/{len(unique_drugs)}...")
            # Periodic save of cache
            pd.DataFrame.from_dict(cache, orient='index').reset_index().rename(columns={'index': 'name'}).to_csv(checkpoint_path, index=False)
            
        # Tier 1: Direct Name Lookup
        cid, smiles, mw, logp = get_pubchem_data(drug, 'name')
        time.sleep(0.2)
        
        # Tier 2: CAS Regex if Tier 1 Fails
        if not smiles:
            # Search in name or look back at description if available
            # We'll just try CAS in the name for now, or assume more robust logic if we had full description
            cas_pattern = r'(\d{2,7}-\d{2}-\d)'
            # Search in original name
            match = re.search(cas_pattern, str(drug))
            if match:
                cas_number = match.group(1)
                cid, smiles, mw, logp = get_pubchem_data(cas_number, 'name') # name lookup works for CAS in PubChem too
                time.sleep(0.2)
        
        # Tier 3: Synonym Expansion
        if not smiles:
            synonyms = get_synonyms(drug)
            time.sleep(0.2)
            for syn in synonyms:
                cid, smiles, mw, logp = get_pubchem_data(syn, 'name')
                time.sleep(0.2)
                if smiles: break
        
        cache[drug] = {
            'pubchem_cid': cid,
            'smiles': smiles,
            'molecular_weight': mw,
            'logp': logp,
            'enrichment_tier': 'Tier 1' if cid and not smiles else ('Tier 2' if 'cas' in str(drug).lower() else 'Tier 3' if smiles else 'Failed')
        }

    # Final cache save
    pd.DataFrame.from_dict(cache, orient='index').reset_index().rename(columns={'index': 'name'}).to_csv(checkpoint_path, index=False)
    
    # Merge back
    cache_df = pd.DataFrame.from_dict(cache, orient='index').reset_index().rename(columns={'index': 'name'})
    enriched_df = pd.merge(df, cache_df, on='name', how='left')
    
    # Save Final Output
    output_path = os.path.join(processed_dir, 'SVEF_Enriched_Final.csv')
    enriched_df.to_csv(output_path, index=False)
    
    # Summary Report
    if 'smiles' in enriched_df.columns:
        matches = enriched_df['smiles'].notnull().sum()
        coverage = (matches / len(enriched_df)) * 100 if len(enriched_df) > 0 else 0
    else:
        matches = 0
        coverage = 0
    print("\n--- Module 3 Summary ---")
    print(f"SMILES Recovery Matches: {matches:,}")
    print(f"Final Coverage: {coverage:.1f}%")
    print(f"Enriched dataset saved to: {output_path}")

if __name__ == "__main__":
    processed_dir = 'data/processed'
    recover_smiles(processed_dir)
