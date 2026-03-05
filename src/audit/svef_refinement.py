import pandas as pd
import numpy as np
import os
import sys
import shutil
from datetime import datetime

def refine_svef_assets(processed_dir):
    """
    Module 2: Targeted Asset Identification
    """
    print("Module 2: Starting SVEF Refinement...")
    
    input_path = os.path.join(processed_dir, 'global_trial_audit.parquet')
    main_output_path = os.path.join(processed_dir, 'SVEF_candidates_raw.csv')
    archive_dir = os.path.join(processed_dir, 'archive')
    
    if not os.path.exists(archive_dir):
        os.makedirs(archive_dir)
        
    # Archive existing raw candidates file if it exists
    if os.path.exists(main_output_path):
        mtime = os.path.getmtime(main_output_path)
        timestamp = datetime.fromtimestamp(mtime).strftime('%Y%m%d_%H%M%S')
        archive_path = os.path.join(archive_dir, f'SVEF_Candidates_Raw_{timestamp}.csv')
        print(f"Archiving existing raw candidates to: {archive_path}")
        shutil.move(main_output_path, archive_path)
    
    if not os.path.exists(input_path):
        print(f"Error: {input_path} not found. Run Module 1 first.")
        return
    
    # Load global audit data
    global_audit = pd.read_parquet(input_path)
    
    # 1. Filter for the "Rescue Sweet Spot"
    print("Filtering for Phase 2/3 Terminated Small Molecules...")
    mask = (
        (global_audit['study_type'] == 'INTERVENTIONAL') &
        (global_audit['phase'].isin(['PHASE2', 'PHASE3', 'PHASE2/PHASE3'])) &
        (global_audit['overall_status'] == 'TERMINATED') &
        (global_audit['molecule_type'] == 'Small_Molecule') &
        (global_audit['termination_category'] == 'Efficacy')
    )
    
    svef_raw = global_audit[mask].copy()
    
    # Secondary check: Ensure NO safety keywords in why_stopped (safety mask)
    print("Ensuring zero safety-triggered halts...")
    safety_keywords = ['toxic', 'adverse event', 'safety', 'harm', 'risk', 'side effect', 'death', 'mortality', 'aes', 'maximum tolerated dose', 'intolerability']
    safe_pattern = '|'.join(safety_keywords)
    svef_raw = svef_raw[~svef_raw['why_stopped'].str.contains(safe_pattern, case=False, na=False)]
    
    # 2. Safety_Score (Log-Enrollment 50% / Duration 50%)
    print("Calculating Safety_Score (Log-Scaled)...")
    
    # Duration Calculation
    svef_raw['start_date'] = pd.to_datetime(svef_raw['start_date'], errors='coerce')
    svef_raw['primary_completion_date'] = pd.to_datetime(svef_raw['primary_completion_date'], errors='coerce')
    
    def calculate_duration(row):
        if pd.notnull(row['start_date']) and pd.notnull(row['primary_completion_date']):
            delta = (row['primary_completion_date'] - row['start_date']).days
            return delta if delta > 0 else np.nan
        return np.nan

    svef_raw['duration_days'] = svef_raw.apply(calculate_duration, axis=1)
    
    # Normalization (Min-Max)
    # Enrollment: Use log1p to handle skewed distribution
    svef_raw['log_enrollment'] = np.log1p(svef_raw['enrollment'].fillna(0))
    e_min = svef_raw['log_enrollment'].min()
    e_max = svef_raw['log_enrollment'].max()
    d_min = svef_raw['duration_days'].min()
    d_max = svef_raw['duration_days'].max()
    
    # Scalers
    svef_raw['norm_enrollment'] = (svef_raw['log_enrollment'] - e_min) / (e_max - e_min) if (e_max - e_min) != 0 else 0
    svef_raw['norm_duration'] = (svef_raw['duration_days'] - d_min) / (d_max - d_min) if (d_max - d_min) != 0 else 0
    
    # Composite Safety_Score
    svef_raw['Safety_Score'] = (svef_raw['norm_enrollment'].fillna(0) * 0.5) + (svef_raw['norm_duration'].fillna(0) * 0.5)
    
    # 3. Save Output
    svef_raw.to_csv(main_output_path, index=False)
    
    # Summary Report
    print("\n--- Module 2 Summary ---")
    print(f"Candidates Identified: {len(svef_raw):,}")
    print(f"Average Safety Score: {svef_raw['Safety_Score'].mean():.4f}")
    print(f"Average Enrollment: {svef_raw['enrollment'].mean():.1f}")
    print(f"Raw Candidates saved to: {main_output_path}")

if __name__ == "__main__":
    processed_dir = 'data/processed'
    refine_svef_assets(processed_dir)
