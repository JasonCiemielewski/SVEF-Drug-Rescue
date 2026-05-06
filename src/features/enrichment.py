import pandas as pd
import json
import os

def load_pubchem_cache(cache_path):
    """
    Loads the PubChem results cache from a JSON file.
    """
    if not os.path.exists(cache_path):
        raise FileNotFoundError(f"Cache file not found at {cache_path}")
        
    with open(cache_path, 'r') as f:
        cache = json.load(f)
    return cache

def prepare_cache_df(cache):
    """
    Converts the PubChem cache dictionary into a normalized DataFrame for merging.
    """
    cache_items = []
    for name, data in cache.items():
        if not data:
            continue
        item = {
            'clean_name_lookup': str(name).lower().strip(),
            'molecular_weight': data.get('MolecularWeight'),
            'xlogp': data.get('XLogP'),
            'smiles': data.get('ConnectivitySMILES') or data.get('CanonicalSMILES')
        }
        cache_items.append(item)
    
    # Drop duplicates in case of normalization collisions
    cache_df = pd.DataFrame(cache_items).drop_duplicates(subset=['clean_name_lookup'])
    return cache_df

def merge_pubchem_features(df, cache_df, name_col='clean_name'):
    """
    Performs a robust, case-insensitive merge of PubChem features into the main DataFrame.
    """
    df = df.copy()
    
    # Create temporary normalized join key
    df['clean_name_lookup'] = df[name_col].astype(str).str.lower().str.strip()
    
    # Drop existing enrichment columns if they exist to avoid suffix duplication
    for col in ['molecular_weight', 'xlogp', 'smiles']:
        if col in df.columns:
            df = df.drop(columns=[col])
            
    # Perform the merge
    df_enriched = pd.merge(df, cache_df, on='clean_name_lookup', how='left')
    
    # Cleanup
    df_enriched = df_enriched.drop(columns=['clean_name_lookup'])
    
    return df_enriched
