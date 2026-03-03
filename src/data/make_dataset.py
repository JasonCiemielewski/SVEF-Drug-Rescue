import pandas as pd
import re
import os
import requests
import time

def load_data(raw_dir):
    """
    Load studies and interventions from AACT flat files.
    """
    print("Loading studies.txt...")
    studies = pd.read_csv(os.path.join(raw_dir, 'studies.txt'), sep='|', low_memory=False)
    
    print("Loading interventions.txt...")
    interventions = pd.read_csv(os.path.join(raw_dir, 'interventions.txt'), sep='|', low_memory=False)
    
    return studies, interventions

def filter_structural(studies, interventions):
    """
    Perform initial structural filtering for Phase 2/3 Terminated Interventional Drug trials.
    """
    # Select relevant columns from studies
    studies_subset = studies[['nct_id', 'study_type', 'phase', 'overall_status', 'why_stopped']].copy()
    
    # Filter for study_type, phase, and overall_status
    mask = (
        (studies_subset['study_type'] == 'INTERVENTIONAL') &
        (studies_subset['phase'].isin(['PHASE2', 'PHASE3', 'PHASE2/PHASE3'])) &
        (studies_subset['overall_status'] == 'TERMINATED')
    )
    filtered_studies = studies_subset[mask]
    
    # Filter interventions for 'Drug' and merge
    drug_interventions = interventions[interventions['intervention_type'] == 'DRUG']
    
    # Join on nct_id
    merged = pd.merge(filtered_studies, drug_interventions, on='nct_id', how='inner')
    
    # Exclude obvious biologics (monoclonal antibodies and vaccines)
    # Using 'name' column from interventions
    biologic_keywords = ['mab', 'vaccine', 'cell therapy', 'antibody', 'gene therapy']
    pattern = '|'.join(biologic_keywords)
    merged = merged[~merged['name'].str.contains(pattern, case=False, na=False)]
    
    return merged

def apply_svef_logic(df):
    """
    Identify efficacy failures that did not fail due to safety issues.
    Refined with keywords from PDF and authoritative sources.
    """
    # Clean why_stopped column
    df['why_stopped_clean'] = df['why_stopped'].fillna('').str.lower()
    
    # Efficacy Mask
    efficacy_keywords = [
        'futility', 'efficacy', 'lack of effect', 'benefit', 
        'endpoint', 'interim analysis', 'superiority',
        'insufficient signal', 'lack of benefit', 'endpoint not met',
        'no significant difference', 'did not meet', 'unprovable'
    ]
    eff_pattern = '|'.join(efficacy_keywords)
    df['eff_mask'] = df['why_stopped_clean'].str.contains(eff_pattern, regex=True)
    
    # Safety Mask
    safety_keywords = [
        'toxic', 'adverse event', 'side effect', 'harm', 
        'risk', 'death', 'mortality', 'aes', 'maximum tolerated dose', 
        'safety profile', 'intolerability', 'adverse reactions'
    ]
    # "safety" is a tricky keyword because of "no safety concerns"
    # We use a negative check for common "no safety" phrases
    safety_negation_phrases = ['no safety concerns', 'no safety issues', 'not due to safety']
    safe_pattern = '|'.join(safety_keywords)
    
    # Preliminary mask for safety keywords
    df['has_safety_keyword'] = df['why_stopped_clean'].str.contains(safe_pattern, regex=True)
    # Check if safety keyword is used in a "safety concerns" context
    # or if "safety" itself is used (excluding specific negations)
    df['is_specifically_safety'] = df['why_stopped_clean'].str.contains('safety', regex=True)
    
    # Final Safety Mask: has safety keyword OR is specifically safety, BUT NOT in a negation context
    # For simplicity, we flag as safety-related if any safety keyword is present
    # Unless it's explicitly "no safety concerns"
    df['negation_mask'] = df['why_stopped_clean'].str.contains('|'.join(safety_negation_phrases), regex=True)
    
    df['safe_mask'] = (df['has_safety_keyword'] | df['is_specifically_safety']) & ~df['negation_mask']
    
    # Final SVEF filter: Efficacy Mask is True AND Safety Mask is False
    svef_candidates = df[df['eff_mask'] & ~df['safe_mask']].copy()
    
    return svef_candidates

def fetch_pubchem_data_placeholder(intervention_name):
    """
    Placeholder for a future PUG-REST API call to PubChem.
    In a production script, this would involve rate-limited requests to:
    https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/{name}/property/SMILES,MolecularWeight,XLogP/JSON
    """
    # For now, just return a template dictionary
    return {
        'intervention_name': intervention_name,
        'smiles': None,
        'molecular_weight': None,
        'logp': None,
        'source': 'PubChem Placeholder'
    }

def main():
    raw_data_dir = os.path.join('data', 'raw')
    output_dir = os.path.join('data', 'processed')
    
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Step 1 & 2: Load and Structural Filter
    studies, interventions = load_data(raw_data_dir)
    total_trials = studies.shape[0]
    
    print("Applying structural filters...")
    initial_filtered = filter_structural(studies, interventions)
    
    # Step 3: SVEF Logic
    print("Applying SVEF logic (Safe but Futile)...")
    svef_candidates = apply_svef_logic(initial_filtered)
    
    # Step 4: Unique Intervention Enrichment
    unique_drugs = svef_candidates['name'].unique()
    print(f"Identified {len(unique_drugs)} unique potential candidates for enrichment.")
    
    # Step 5: Save and Report
    output_path = os.path.join(output_dir, 'SVEF_candidates.csv')
    svef_candidates.to_csv(output_path, index=False)
    
    # Stats
    terminated_phase_2_3 = initial_filtered['nct_id'].nunique()
    svef_count = svef_candidates['nct_id'].nunique()
    
    print("\n--- Summary Statistics ---")
    print(f"Total Trials Processed: {total_trials}")
    print(f"Terminated Phase 2/3 Drug Trials: {terminated_phase_2_3}")
    print(f"Efficacy Failures identified (SVEF): {svef_count}")
    if terminated_phase_2_3 > 0:
        percentage = (svef_count / terminated_phase_2_3) * 100
        print(f"Percentage of Terminated Trials meeting SVEF criteria: {percentage:.2f}%")
    print(f"Output saved to: {output_path}")

if __name__ == "__main__":
    main()
