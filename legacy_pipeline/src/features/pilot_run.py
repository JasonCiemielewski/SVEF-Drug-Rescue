import pandas as pd
import os
import sys
from datetime import datetime

# Import the architect logic
from src.features.enrich_dataset import (
    load_data, map_intervention_roles, merge_clinical_metadata, 
    feature_engineering_advanced, process_publications, 
    enrich_with_pubchem_architect
)


def run_pilot():
    print("--- STARTING 100-TRIAL TOTAL EVIDENCE PILOT ---")
    raw_dir = os.path.join('data', 'raw')
    base_df_path = os.path.join('data', 'interim', 'SVEF_candidates.csv')
    
    # 1. Load full data
    base_df, studies, calc_vals, sponsors, conditions, refs, dg, dg_int = load_data(base_df_path, raw_dir)
    
    # 2. Sample 500 trials (NCT IDs)
    pilot_nct_ids = base_df['nct_id'].drop_duplicates().sample(500, random_state=42).tolist()
    base_pilot = base_df[base_df['nct_id'].isin(pilot_nct_ids)].copy()
    print(f"Sampled 500 trials. Row count (Trial-Drug combos): {len(base_pilot)}")

    # 3. Filter other tables
    studies = studies[studies['nct_id'].isin(pilot_nct_ids)]
    dg = dg[dg['nct_id'].isin(pilot_nct_ids)]
    dg_int = dg_int[dg_int['nct_id'].isin(pilot_nct_ids)]
    
    # 4. Run total evidence mapping
    df = map_intervention_roles(base_pilot, dg, dg_int)
    df = merge_clinical_metadata(df, studies, calc_vals, sponsors, conditions)
    df = feature_engineering_advanced(df)
    
    # Publication Evidence
    pub_data = process_publications(refs[refs['nct_id'].isin(pilot_nct_ids)])
    if not pub_data.empty:
        df = df.merge(pub_data, on='nct_id', how='left')
    
    # 5. Enrichment (Temporary pilot cache)
    print("\nExecuting Tiered Recovery on Pilot Sample...")
    pilot_cache_path = os.path.join('data', 'interim', 'pilot_smiles_cache.csv')
    if os.path.exists(pilot_cache_path): os.remove(pilot_cache_path)
    
    df = enrich_with_pubchem_architect(df, cache_path=pilot_cache_path)
    
    # 6. Summary and Save
    pilot_output = os.path.join('data', 'interim', 'pilot_results.csv')
    df.to_csv(pilot_output, index=False)
    
    print(f"\n--- PILOT COMPLETE ---")
    print(f"Sample contained {df['name'].nunique()} unique drugs.")
    print(f"Roles identified: {df['group_type'].value_counts().to_dict()}")
    print(f"Results saved to: {pilot_output}")

if __name__ == "__main__":
    run_pilot()
