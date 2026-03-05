import pandas as pd
import re
import os
import sys

def audit_global_trials(raw_dir, processed_dir):
    """
    Module 1: Global Denominator Analysis
    - Categorize ALL trials by why_stopped.
    - Classify interventions into Small_Molecule, Biologic, or Other.
    """
    print("Module 1: Starting Global Denominator Analysis...")
    
    # Load AACT files
    studies_path = os.path.join(raw_dir, 'studies.txt')
    interv_path = os.path.join(raw_dir, 'interventions.txt')
    
    print(f"Loading {studies_path}...")
    studies = pd.read_csv(studies_path, sep='|', low_memory=False)
    print(f"Loading {interv_path}...")
    interventions = pd.read_csv(interv_path, sep='|', low_memory=False)
    
    # 1. Global Categorization of why_stopped
    def categorize_termination(reason):
        if pd.isnull(reason): return 'Unknown'
        reason = reason.lower()
        if any(kw in reason for kw in ['efficacy', 'futility', 'benefit', 'endpoint', 'signal']):
            return 'Efficacy'
        if any(kw in reason for kw in ['toxic', 'adverse event', 'safety', 'harm', 'risk', 'side effect', 'death', 'mortality', 'aes']):
            return 'Safety'
        if any(kw in reason for kw in ['accrual', 'recruit', 'enroll', 'slow', 'low', 'insufficient', 'participant']):
            return 'Accrual/Logistics'
        if any(kw in reason for kw in ['business', 'strategic', 'funding', 'sponsor', 'priority', 'portfolio', 'commercial', 'budget']):
            return 'Business/Strategic'
        if any(kw in reason for kw in ['administrative', 'operational', 'process', 'management']):
            return 'Administrative'
        return 'Other/Unspecified'

    print("Categorizing termination reasons...")
    studies['termination_category'] = studies['why_stopped'].apply(categorize_termination)
    
    # 2. Global Molecule Classification
    biologic_kws = [
        'mab', 'cept', 'recombinant', 'protein', 'cell therapy', 
        'antibody', 'gene therapy', 'alfa', 'beta', 'gamma', 
        'monoclonal', 'vaccine', 'polypeptide', 'enzyme'
    ]
    biologic_pattern = '|'.join(biologic_kws)
    
    def classify_molecule(row):
        name = str(row['name']).lower()
        desc = str(row['description']).lower()
        combined = f"{name} {desc}"
        
        if row['intervention_type'].upper() != 'DRUG':
            return 'Other'
        if re.search(biologic_pattern, combined):
            return 'Biologic'
        return 'Small_Molecule'

    print("Classifying interventions into molecule types...")
    interventions['molecule_type'] = interventions.apply(classify_molecule, axis=1)
    
    # Merge for global audit
    print("Merging datasets for global audit...")
    global_audit = pd.merge(
        studies[['nct_id', 'study_type', 'phase', 'overall_status', 'why_stopped', 'termination_category', 'enrollment', 'start_date', 'primary_completion_date']],
        interventions[['nct_id', 'intervention_type', 'name', 'description', 'molecule_type']],
        on='nct_id', 
        how='inner'
    )
    
    # Save as Parquet for performance
    output_path = os.path.join(processed_dir, 'global_trial_audit.parquet')
    global_audit.to_parquet(output_path, index=False)
    
    # Summary Report
    total_trials = global_audit['nct_id'].nunique()
    sm_count = global_audit[global_audit['molecule_type'] == 'Small_Molecule']['nct_id'].nunique()
    eff_count = global_audit[global_audit['termination_category'] == 'Efficacy']['nct_id'].nunique()
    
    print("\n--- Module 1 Summary ---")
    print(f"Global Trials Audited: {total_trials:,}")
    print(f"Small Molecule trials: {sm_count:,} ({ (sm_count/total_trials)*100:.1f}%)")
    print(f"Trials terminated for Efficacy failure: {eff_count:,} ({ (eff_count/total_trials)*100:.1f}%)")
    print(f"Global Audit saved to: {output_path}")

if __name__ == "__main__":
    raw_dir = 'data/raw'
    processed_dir = 'data/processed'
    if not os.path.exists(processed_dir): os.makedirs(processed_dir)
    audit_global_trials(raw_dir, processed_dir)
