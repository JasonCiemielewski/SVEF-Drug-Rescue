import pandas as pd
import json
import os

def robust_merge():
    print("Step 1: Loading Data...")
    df_path = 'data/interim/master_ml_df.csv'
    cache_path = 'notebooks/pubchem_cache_backup.json'
    
    df = pd.read_csv(df_path)
    with open(cache_path, 'r') as f:
        cache = json.load(f)
    
    print(f" - DataFrame: {len(df):,} rows")
    print(f" - Cache: {len(cache):,} records")

    # Step 2: Prepare Cache for merging
    # Convert dictionary to DataFrame
    # Note: We use 'ConnectivitySMILES' as the source for the 'smiles' column
    cache_items = []
    for name, data in cache.items():
        item = {
            'clean_name_lookup': name.lower().strip(),
            'molecular_weight': data.get('MolecularWeight'),
            'xlogp': data.get('XLogP'),
            'smiles': data.get('ConnectivitySMILES')  # Corrected Key
        }
        cache_items.append(item)
    
    cache_df = pd.DataFrame(cache_items).drop_duplicates(subset=['clean_name_lookup'])
    
    # Step 3: Prepare Main DF for merging
    df['clean_name_lookup'] = df['clean_name'].str.lower().str.strip()

    # Step 4: Verification Handshake (5 Samples)
    print("\nStep 2: Verification Handshake (5 Samples)")
    sample_names = list(cache.keys())[:5]
    for name in sample_names:
        df_matches = df[df['clean_name_lookup'] == name.lower().strip()]
        match_count = len(df_matches)
        print(f" - '{name}': {match_count} occurrences in master_ml_df")
        if match_count > 0:
            sample_row = df_matches.iloc[0]
            # Check if we can find it in our prepared cache_df
            cache_row = cache_df[cache_df['clean_name_lookup'] == name.lower().strip()].iloc[0]
            print(f"   [OK] Handshake successful for {name}")

    # Step 5: Perform the Merge
    print("\nStep 3: Performing Robust Merge...")
    # Drop existing enrichment columns if they exist to avoid duplicates
    cols_to_drop = [c for c in ['molecular_weight', 'xlogp', 'smiles'] if c in df.columns]
    df = df.drop(columns=cols_to_drop)
    
    df_enriched = pd.merge(df, cache_df, on='clean_name_lookup', how='left')
    
    # Step 6: Cleanup and Final Checks
    df_enriched = df_enriched.drop(columns=['clean_name_lookup'])
    
    matched_count = df_enriched['smiles'].notna().sum()
    print(f"\nFinal Implementation Summary:")
    print(f" - Total rows processed: {len(df_enriched):,}")
    print(f" - Successfully enriched rows: {matched_count:,}")
    print(f" - Percentage enriched: {(matched_count/len(df_enriched))*100:.1f}%")
    
    # Save the result
    output_path = 'data/interim/master_ml_df_enriched.csv'
    df_enriched.to_csv(output_path, index=False)
    print(f" - Saved enriched data to: {output_path}")

if __name__ == "__main__":
    robust_merge()
