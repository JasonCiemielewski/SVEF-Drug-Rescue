import pandas as pd
import numpy as np
import os

def create_micro_dataset():
    """
    Overhauls the micro-dataset generation to create a "Dirty" high-fidelity demo dataset
    that explicitly demonstrates the filtering and cleaning power of the SVEF pipeline.
    """
    print("Implementing 'Logic-Testing' Selection...")
    
    # --- Step 1: Logic-Testing Selection ---
    
    # 1. SVEF Gold (50 IDs)
    gold_df = pd.read_csv(os.path.join('data', 'processed', 'SVEF_Enriched_Final.csv'))
    gold_ids = gold_df.head(50)['nct_id'].tolist()
    
    # 2. Safety Failures (15 IDs)
    audit_df = pd.read_csv(os.path.join('data', 'interim', 'audit', 'svef_logic_audit.csv'))
    safety_ids = audit_df[audit_df['audit_status'].str.contains('SAFETY_CONCERN', na=False)].head(15)['nct_id'].tolist()
    
    # 3. Biologic Distractors (15 IDs)
    biologic_df = pd.read_csv(os.path.join('data', 'interim', 'audit', 'structural_excluded_biologics.csv'))
    biologic_ids = biologic_df.head(15)['nct_id'].tolist()
    
    # 4. Phase/Status Distractors (20 IDs)
    # Pulling IDs that would be excluded by filter_structural
    studies_sample = pd.read_csv(os.path.join('data', 'raw', 'studies.txt'), sep='|', low_memory=False, nrows=100000)
    distractor_ids = studies_sample[
        (studies_sample['phase'] == 'PHASE1') | 
        (studies_sample['overall_status'] == 'ACTIVE_NOT_RECRUITING')
    ].head(20)['nct_id'].tolist()

    # Combine all target IDs
    target_nct_ids = list(set(gold_ids + safety_ids + biologic_ids + distractor_ids))
    print(f"Total Logic-Testing IDs selected: {len(target_nct_ids)}")
    print(f"  - SVEF Gold: {len(gold_ids)}")
    print(f"  - Safety Failures: {len(safety_ids)}")
    print(f"  - Biologic Distractors: {len(biologic_ids)}")
    print(f"  - Phase/Status Distractors: {len(distractor_ids)}")

    demo_dir = os.path.join('data', 'demo')
    if not os.path.exists(demo_dir): 
        os.makedirs(demo_dir)
    raw_dir = os.path.join('data', 'raw')

    # --- Step 2 & 3: Extraction Logic & Loop ---
    
    def extract_pure_raw(filename):
        """
        Ingests AACT files and aligns them with production expectations:
        1. Renames 'id' to 'design_group_id' in design tables.
        2. Force-casts ALL join keys to strings to prevent ValueErrors.
        3. Cleans 'group_type' to prevent TypeErrors.
        """
        in_path = os.path.join(raw_dir, filename)
        out_path = os.path.join(demo_dir, filename.replace('.txt', '_micro.csv'))
        
        chunks = pd.read_csv(in_path, sep='|', low_memory=False, chunksize=100000)
        micro_df = pd.concat([chunk[chunk['nct_id'].isin(target_nct_ids)] for chunk in chunks])

        # --- Alignment Logic ---
        
        # 1. Standardize design_group_id
        if filename == 'design_groups.txt':
            micro_df = micro_df.rename(columns={'id': 'design_group_id'})
            if 'group_type' in micro_df.columns:
                micro_df['group_type'] = micro_df['group_type'].fillna('Other').astype(str)

        # 2. Hard-cast all potential join keys to strings
        # We use .fillna('') BEFORE casting to string to ensure the column stays an 'object' (string)
        join_keys = ['nct_id', 'id', 'design_group_id', 'intervention_id', 'pmid']
        for col in join_keys:
            if col in micro_df.columns:
                # fillna('') ensures there are no floats (NaNs) to trigger a type-conversion
                micro_df[col] = micro_df[col].fillna('').astype(str)
        
        # ------------------------
        
        micro_df.to_csv(out_path, index=False)
        print(f"Extracted {filename.replace('.txt', '_micro.csv')}: {len(micro_df)} rows")

    # Process all 9 essential AACT tables
    essential_tables = [
        'studies.txt',
        'interventions.txt',
        'design_groups.txt',
        'design_group_interventions.txt',
        'id_information.txt',
        'study_references.txt',
        'sponsors.txt',
        'calculated_values.txt',
        'browse_conditions.txt'
    ]

    for table in essential_tables:
        extract_pure_raw(table)

    print("\nMicro-Dataset overhaul complete! The data in 'data/demo/' now contains intentionally 'Dirty' distractors for pipeline validation.")

if __name__ == "__main__":
    create_micro_dataset()
