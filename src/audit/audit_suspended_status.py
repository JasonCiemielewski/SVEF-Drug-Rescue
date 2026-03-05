import pandas as pd
import os

def audit_suspended_status():
    raw_dir = 'data/raw'
    studies = pd.read_csv(os.path.join(raw_dir, 'studies.txt'), sep='|', low_memory=False)
    
    suspended = studies[studies['overall_status'] == 'SUSPENDED'].copy()
    
    print("\n--- Audit of SUSPENDED Status Trials ---")
    print(f"Total SUSPENDED trials: {len(suspended)}")
    
    # Check why_stopped
    why_stopped_count = suspended['why_stopped'].notna().sum()
    print(f"SUSPENDED trials with a 'why_stopped' entry: {why_stopped_count}")
    
    # Phase distribution for SUSPENDED
    phase_counts = suspended['phase'].value_counts(dropna=False).reset_index()
    phase_counts.columns = ['phase', 'count']
    print("\nPhase Distribution for SUSPENDED trials:")
    print(phase_counts.to_string(index=False))
    
    # Sample reasons
    print("\nSample 'why_stopped' reasons for SUSPENDED trials:")
    sample_reasons = suspended['why_stopped'].dropna().head(10).tolist()
    if sample_reasons:
        for reason in sample_reasons:
            print(f"- {reason}")
    else:
        print("No 'why_stopped' reasons found in sample.")
    
    # Save the audit
    output_path = 'data/interim/audit/suspended_status_audit.csv'
    phase_counts.to_csv(output_path, index=False)
    print(f"\nAudit summary saved to {output_path}")

if __name__ == "__main__":
    audit_suspended_status()
