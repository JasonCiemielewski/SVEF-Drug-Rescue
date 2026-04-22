import pandas as pd
import sys
import os

def audit_studies_status():
    file_path = 'data/raw/studies.txt'
    output_path_full = 'data/interim/study_status_audit.csv'
    output_path_filtered = 'data/interim/study_status_audit_filtered.csv'
    
    # Ensure the output directory exists
    os.makedirs(os.path.dirname(output_path_full), exist_ok=True)
    
    print(f"Loading {file_path} with memory-efficient usecols...")
    try:
        # Load both overall_status and phase columns
        df = pd.read_csv(file_path, sep='|', usecols=['overall_status', 'phase'])
        
        # 1. Audit for ALL studies
        counts_full = df['overall_status'].value_counts().reset_index()
        counts_full.columns = ['overall_status', 'count']
        counts_full = counts_full.sort_values(by='count', ascending=False)
        
        # 2. Audit for PHASE 2, PHASE 3, and PHASE 2/3 studies
        # Based on the earlier check, these values are: 'PHASE2', 'PHASE3', 'PHASE2/PHASE3'
        phase_filter = ['PHASE2', 'PHASE3', 'PHASE2/PHASE3']
        df_filtered = df[df['phase'].isin(phase_filter)]
        
        counts_filtered = df_filtered['overall_status'].value_counts().reset_index()
        counts_filtered.columns = ['overall_status', 'count']
        counts_filtered = counts_filtered.sort_values(by='count', ascending=False)
        
        # Display the results
        print("\nStudy Overall Status Audit (ALL):")
        print(counts_full.to_string(index=False))
        
        print(f"\nStudy Overall Status Audit (Filtered: {', '.join(phase_filter)}):")
        print(counts_filtered.to_string(index=False))
        
        # Save to CSVs
        counts_full.to_csv(output_path_full, index=False)
        counts_filtered.to_csv(output_path_filtered, index=False)
        
        print(f"\nFull results saved to {output_path_full}")
        print(f"Filtered results saved to {output_path_filtered}")
        
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    audit_studies_status()
