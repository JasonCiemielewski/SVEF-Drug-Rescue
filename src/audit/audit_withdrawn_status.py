import pandas as pd
import os

def audit_withdrawn_status():
    raw_dir = 'data/raw'
    studies = pd.read_csv(os.path.join(raw_dir, 'studies.txt'), sep='|', low_memory=False)
    
    withdrawn = studies[studies['overall_status'] == 'WITHDRAWN'].copy()
    
    print("\n--- Audit of WITHDRAWN Status Trials ---")
    print(f"Total WITHDRAWN trials: {len(withdrawn)}")
    
    # Check why_stopped
    why_stopped_count = withdrawn['why_stopped'].notna().sum()
    print(f"WITHDRAWN trials with a 'why_stopped' entry: {why_stopped_count}")
    
    # Phase distribution for WITHDRAWN
    phase_counts = withdrawn['phase'].value_counts(dropna=False).reset_index()
    phase_counts.columns = ['phase', 'count']
    print("\nPhase Distribution for WITHDRAWN trials:")
    print(phase_counts.to_string(index=False))
    
    # Sample reasons
    print("\nSample 'why_stopped' reasons for WITHDRAWN trials:")
    print(withdrawn['why_stopped'].dropna().head(10).to_string(index=False))
    
    # Save the audit
    output_path = 'data/interim/audit/withdrawn_status_audit.csv'
    phase_counts.to_csv(output_path, index=False)
    print(f"\nAudit summary saved to {output_path}")

if __name__ == "__main__":
    audit_withdrawn_status()
