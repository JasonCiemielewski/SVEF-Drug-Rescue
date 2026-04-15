import pandas as pd
import numpy as np
import os
import sys
import shutil
from datetime import datetime

import pandas as pd
import numpy as np
import os
import sys
import shutil
from datetime import datetime

def calculate_duration(row):
    """
    Calculates the duration of a trial in days based on start and completion dates.
    
    Args:
        row (pd.Series): A row from a trials DataFrame containing 'start_date' 
                         and 'primary_completion_date'.
    
    Returns:
        float: Duration in days if both dates are valid and duration is positive, else NaN.
    """
    if pd.notnull(row['start_date']) and pd.notnull(row['primary_completion_date']):
        delta = (row['primary_completion_date'] - row['start_date']).days
        return delta if delta > 0 else np.nan
    return np.nan

def refine_svef_assets(processed_dir):
    """
    Module 2: Targeted Asset Identification.
    Refines the broad candidate list by calculating safety scores and performing
    non-destructive filtering to prepare for chemical enrichment.
    
    Args:
        processed_dir (str): Path to the directory containing processed data files.
    """
    print("Module 2: Starting SVEF Refinement...")
    
    # Use the broad candidates list from Module 1
    input_path = os.path.join(os.path.dirname(processed_dir), 'interim', 'SVEF_candidates.csv')
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
    
    # Load broad candidates
    print(f"Loading broad candidates from {input_path}...")
    svef_raw = pd.read_csv(input_path)
    print(f"Initial Candidate Pool: {len(svef_raw):,}")
    
    # 1. Refinement Filtering (REMOVED AGGRESSIVE PRE-FILTERING)
    # We preserve the broad set for enrichment, only ensuring we have valid trial data.
    print("Refining for Rescue Candidates (Preserving broad set)...")
    svef_refined = svef_raw.copy()
    
    # Secondary check: Ensure NO safety keywords in why_stopped (safety mask)
    # This labels but doesn't necessarily drop if the goal is maximum enrichment.
    # However, for 'SVEF_candidates_raw', we focus on efficacy-likely failures.
    print("Ensuring zero safety-triggered halts for the priority candidate list...")
    safety_keywords = ['toxic', 'adverse event', 'safety', 'harm', 'risk', 'side effect', 'death', 'mortality', 'aes', 'maximum tolerated dose', 'intolerability']
    safe_pattern = '|'.join(safety_keywords)
    svef_refined = svef_refined[~svef_refined['why_stopped'].str.contains(safe_pattern, case=False, na=False)]
    
    # 2. Safety_Score (Log-Enrollment 50% / Duration 50%)
    print("Calculating Safety_Score (Log-Scaled)...")
    
    # Duration Calculation
    svef_refined['start_date'] = pd.to_datetime(svef_refined['start_date'], errors='coerce')
    svef_refined['primary_completion_date'] = pd.to_datetime(svef_refined['primary_completion_date'], errors='coerce')
    
    svef_refined['duration_days'] = svef_refined.apply(calculate_duration, axis=1)
    
    # Normalization (Min-Max)
    # Enrollment: Use log1p to handle skewed distribution
    svef_refined['log_enrollment'] = np.log1p(svef_refined['enrollment'].fillna(0))
    e_min = svef_refined['log_enrollment'].min()
    e_max = svef_refined['log_enrollment'].max()
    d_min = svef_refined['duration_days'].min()
    d_max = svef_refined['duration_days'].max()
    
    # Scalers
    svef_refined['norm_enrollment'] = (svef_refined['log_enrollment'] - e_min) / (e_max - e_min) if (e_max - e_min) != 0 else 0
    svef_refined['norm_duration'] = (svef_refined['duration_days'] - d_min) / (d_max - d_min) if (d_max - d_min) != 0 else 0
    
    # Composite Safety_Score
    svef_refined['Safety_Score'] = (svef_refined['norm_enrollment'].fillna(0) * 0.5) + (svef_refined['norm_duration'].fillna(0) * 0.5)
    
    # 3. Save Output
    svef_refined.to_csv(main_output_path, index=False)
    
    # Summary Report
    print("\n--- Module 2 Summary ---")
    print(f"Candidates Identified: {len(svef_refined):,}")
    print(f"Average Safety Score: {svef_refined['Safety_Score'].mean():.4f}")
    print(f"Average Enrollment: {svef_refined['enrollment'].mean():.1f}")
    print(f"Raw Candidates saved to: {main_output_path}")

if __name__ == "__main__":
    processed_dir = 'data/processed'
    refine_svef_assets(processed_dir)
