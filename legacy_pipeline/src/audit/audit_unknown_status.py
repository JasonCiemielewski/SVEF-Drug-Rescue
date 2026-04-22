import pandas as pd
import os

def audit_unknown_status():
    raw_dir = 'data/raw'
    studies = pd.read_csv(os.path.join(raw_dir, 'studies.txt'), sep='|', low_memory=False)
    
    unknown = studies[studies['overall_status'] == 'UNKNOWN'].copy()
    
    # Analyze the 'last_update_submitted_date'
    unknown['last_update_year'] = pd.to_datetime(unknown['last_update_submitted_date']).dt.year
    
    # Analyze completion dates
    unknown['completion_date'] = pd.to_datetime(unknown['completion_date'], errors='coerce')
    unknown['completion_year'] = unknown['completion_date'].dt.year
    
    # Grouping by Last Update Year
    update_counts = unknown['last_update_year'].value_counts().sort_index().reset_index()
    update_counts.columns = ['last_update_year', 'count']
    
    print("\n--- Audit of UNKNOWN Status Trials ---")
    print(f"Total UNKNOWN trials: {len(unknown)}")
    
    print("\nTop 10 Last Update Years for UNKNOWN trials:")
    print(update_counts.tail(10).to_string(index=False))
    
    # Checking for 'why_stopped' in UNKNOWN trials
    why_stopped_count = unknown['why_stopped'].notna().sum()
    print(f"\nUNKNOWN trials with a 'why_stopped' entry: {why_stopped_count}")
    
    # Save the detailed audit
    output_path = 'data/interim/audit/unknown_status_audit.csv'
    update_counts.to_csv(output_path, index=False)
    print(f"\nAudit summary saved to {output_path}")

if __name__ == "__main__":
    audit_unknown_status()
