import pandas as pd
import os
import sys
import shutil
from datetime import datetime

# Add the project root to sys.path to allow importing from src
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from src.features.enrich_dataset import (
    enrich_with_pubchem_architect,
    load_data,
    map_intervention_roles,
    merge_clinical_metadata,
    feature_engineering_advanced,
    process_publications
)

def recover_smiles(processed_dir):
    """
    Module 3: Tiered Chemical Enrichment (Total Evidence Edition).
    Orchestrates the full enrichment workflow: loading raw data, joining metadata,
    and performing tiered SMILES recovery for the broad candidate list.
    
    Args:
        processed_dir (str): Path to the directory where processed files are saved.
    """
    print("Module 3: Starting Tiered Chemical Enrichment (Multi-SMILES Architecture)...")
    
    # EXPLICITLY USE BROAD CANDIDATES
    input_path = os.path.join(os.path.dirname(processed_dir), 'interim', 'SVEF_candidates.csv')
    raw_dir = 'data/raw'
    main_output_path = os.path.join(processed_dir, 'SVEF_Enriched_Final.csv')
    archive_dir = os.path.join(processed_dir, 'archive')
    cache_path = os.path.join(processed_dir, 'smiles_cache.csv')
    
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
        print(f"Error: {input_path} not found. Run Module 1 first.")
        return
    
    # 1. Full Clinical Metadata Enrichment (Total Evidence)
    print(f"Loading base candidates for Total Evidence enrichment: {input_path}")
    base_df, studies, calc_vals, sponsors, conditions, refs, dg, dg_int = load_data(input_path, raw_dir)
    
    print("Executing clinical data joins and role mapping...")
    df = map_intervention_roles(base_df, dg, dg_int)
    df = merge_clinical_metadata(df, studies, calc_vals, sponsors, conditions)
    df = feature_engineering_advanced(df)
    
    print("Processing publication evidence...")
    pub_data = process_publications(refs)
    if not pub_data.empty:
        df = df.merge(pub_data, on='nct_id', how='left')
    
    # Ensure publication columns are filled
    pub_cols = ['publication_count', 'Evidence_Confidence', 'results_pmid_list', 'background_pmid_list', 'doi_list']
    for col in pub_cols:
        if col not in df.columns:
            df[col] = 0 if 'count' in col or 'Confidence' in col else ''
        else:
            df[col] = df[col].fillna(0) if 'count' in col or 'Confidence' in col else df[col].fillna('')

    print(f"Total Rows for SMILES Recovery: {len(df):,}")

    # 2. Bioinformatics Recovery Phase
    # Use the architect-hardened enrichment engine
    enriched_df = enrich_with_pubchem_architect(df, cache_path=cache_path)
    
    # Save Final Output
    print("Finalizing Hardened Total Evidence Dataset...")
    enriched_df = enriched_df.drop_duplicates(subset=['nct_id', 'name'])
    enriched_df.to_csv(main_output_path, index=False)
    
    # Export possible proprietary rescue leads
    if 'failure_reason' in enriched_df.columns:
        proprietary_leads = enriched_df[enriched_df['failure_reason'] == 'POSSIBLE_INTERNAL_PROPRIETARY'][['name', 'nct_id', 'group_type', 'agency_class']].drop_duplicates(subset=['name'])
        rescue_path = os.path.join(processed_dir, 'Possible_Internal_Proprietary_Rescue_Leads.csv')
        proprietary_leads.to_csv(rescue_path, index=False)
        print(f"Proprietary rescue list saved to: {rescue_path}")
    
    # Summary Report
    matches = enriched_df['smiles'].notnull().sum()
    print("\n--- Module 3 Summary ---")
    print(f"Total Rows after SMILES Expansion: {len(enriched_df):,}")
    print(f"SMILES Recovery Matches: {matches:,}")
    print(f"Enriched dataset saved to: {main_output_path}")

if __name__ == "__main__":
    processed_dir = 'data/processed'
    recover_smiles(processed_dir)

if __name__ == "__main__":
    processed_dir = 'data/processed'
    recover_smiles(processed_dir)
