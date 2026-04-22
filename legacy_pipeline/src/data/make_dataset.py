import pandas as pd
import re
import os
import sys

def load_data(raw_dir):
    """
    Load studies, interventions, and id_information from AACT flat files.
    """
    print("Loading studies.txt...")
    studies = pd.read_csv(os.path.join(raw_dir, 'studies.txt'), sep='|', low_memory=False)
    
    print("Loading interventions.txt...")
    interventions = pd.read_csv(os.path.join(raw_dir, 'interventions.txt'), sep='|', low_memory=False)
    
    print("Loading id_information.txt...")
    ids = pd.read_csv(os.path.join(raw_dir, 'id_information.txt'), sep='|', low_memory=False)
    
    return studies, interventions, ids

def filter_structural(studies, interventions):
    """
    Perform initial structural filtering for Phase 2, 3, and 2/3 trials across target statuses.
    Returns the final structural filtered dataset AND a dictionary of audit snapshots.
    """
    snapshots = {}
    target_statuses = ['TERMINATED', 'SUSPENDED', 'WITHDRAWN', 'UNKNOWN']
    
    # Select relevant columns from studies
    studies_subset = studies[['nct_id', 'study_type', 'phase', 'overall_status', 'why_stopped']].copy()
    
    # 1. Basic structural (Phase 2, 3, 2/3, Target Statuses, Interventional)
    mask_basic = (
        (studies_subset['study_type'] == 'INTERVENTIONAL') &
        (studies_subset['phase'].isin(['PHASE2', 'PHASE3', 'PHASE2/PHASE3'])) &
        (studies_subset['overall_status'].isin(target_statuses))
    )
    structural_pool = studies_subset[mask_basic].copy()
    
    # Save snapshots per status
    for status in target_statuses:
        snapshots[f'structural_{status.lower()}'] = structural_pool[structural_pool['overall_status'] == status]
    
    # 2. Drug Interventions
    drug_interventions = interventions[interventions['intervention_type'] == 'DRUG']
    merged_drug = pd.merge(structural_pool, drug_interventions, on='nct_id', how='inner')
    
    # 3. Biologics Exclusion (mAbs, vaccines, etc.)
    biologic_keywords = ['mab', 'vaccine', 'cell therapy', 'antibody', 'gene therapy']
    pattern = '|'.join(biologic_keywords)
    
    # Identify excluded biologics
    is_biologic = merged_drug['name'].str.contains(pattern, case=False, na=False)
    excluded_biologics = merged_drug[is_biologic].copy()
    snapshots['structural_excluded_biologics'] = excluded_biologics
    
    final_structural = merged_drug[~is_biologic].copy()
    
    return final_structural, snapshots

def apply_unified_svef_logic(df):
    """
    Apply unified logic to Terminated, Suspended, Withdrawn, and Unknown trials.
    Returns the SVEF candidates AND a full audit trace dataset.
    """
    df = df.copy()
    df['why_stopped_clean'] = df['why_stopped'].fillna('').str.lower()
    
    # --- Keyword Definitions ---
    
    # Efficacy Keywords
    eff_keywords = ['futility', 'efficacy', 'lack of effect', 'benefit', 'endpoint', 'superiority', 'insufficient signal']
    eff_pattern = r'\b(?:' + '|'.join(eff_keywords) + r')\b'
    
    # Safety Keywords
    safe_keywords = ['toxic', 'adverse event', 'side effect', 'harm', 'risk', 'death', 'mortality', 'aes', 'safety']
    safe_pattern = r'\b(?:' + '|'.join(safe_keywords) + r')\b'
    
    # Logistical Keywords (Specific to Withdrawn/Suspended)
    log_keywords = ['recruitment', 'accrual', 'enrollment', 'funding', 'covid', 'personnel', 'feasibility', 'operational']
    log_pattern = r'\b(?:' + '|'.join(log_keywords) + r')\b'

    # Negation Phrases (e.g., "not for safety or efficacy")
    negation_phrases = [
        'no safety concerns', 'no safety issues', 'not due to safety', 
        'benefit-risk', 'not for efficacy or safety', 'not for safety or efficacy',
        'not related to any efficacy or safety', 'not related to efficacy or safety',
        'no efficacy or safety issues', 'neither efficacy nor safety', 'neither safety nor efficacy',
        'not due to any efficacy or safety', 'not due to efficacy or safety',
        'not for reasons of efficacy or safety'
    ]
    negation_pattern = r'\b(?:' + '|'.join(negation_phrases) + r')\b'

    # --- Masking ---
    
    df['has_eff'] = df['why_stopped_clean'].str.contains(eff_pattern, regex=True, na=False)
    df['has_safe'] = df['why_stopped_clean'].str.contains(safe_pattern, regex=True, na=False)
    df['has_log'] = df['why_stopped_clean'].str.contains(log_pattern, regex=True, na=False)
    df['is_negated'] = df['why_stopped_clean'].str.contains(negation_pattern, regex=True, na=False)

    # Actual Efficacy/Safety flags (respecting negations)
    df['eff_flag'] = df['has_eff'] & ~df['is_negated']
    df['safe_flag'] = df['has_safe'] & ~df['is_negated']
    
    # --- Status Assignment Logic ---
    
    def assign_audit_status(row):
        status = row['overall_status']
        
        if status == 'UNKNOWN':
            return 'UNKNOWN_ABANDONED'
            
        if status == 'WITHDRAWN':
            if row['eff_flag']: return 'WITHDRAWN_STRATEGIC'
            if row['has_log']: return 'WITHDRAWN_LOGISTICAL'
            return 'WITHDRAWN_OTHER'
            
        # For TERMINATED and SUSPENDED
        if row['safe_flag']:
            return f"{status}_SAFETY_CONCERN"
        if row['eff_flag']:
            return f"{status}_EFFICACY_FAILURE"
        return f"{status}_CLEAN_EXIT"

    df['audit_status'] = df.apply(assign_audit_status, axis=1)
    
    # --- Trigger Tracking ---
    import re
    def get_matches(text, keywords):
        matches = [k for k in keywords if re.search(r'\b' + re.escape(k) + r'\b', text)]
        return ", ".join(matches) if matches else None

    df['inclusion_trigger'] = df['why_stopped_clean'].apply(lambda x: get_matches(x, eff_keywords))
    df['exclusion_trigger'] = df['why_stopped_clean'].apply(lambda x: get_matches(x, safe_keywords))
    
    # SVEF Candidates: Anything NOT failing for safety
    # (We keep Efficacy Failures and Clean Exits across Terminated, Suspended, and Withdrawn)
    svef_candidates = df[~df['audit_status'].str.contains('SAFETY_CONCERN') & (df['overall_status'] != 'UNKNOWN')].copy()
    
    return svef_candidates, df

def link_trials(svef_df, ids_df):
    """
    Link trials based on secondary_id and nct_alias.
    """
    print("Linking trials across Secondary IDs...")
    svef_nct_ids = set(svef_df['nct_id'].unique())
    relevant_ids = ids_df[ids_df['nct_id'].isin(svef_nct_ids)].copy()
    
    nct_pattern = r'(NCT\d{8})'
    relevant_ids['linked_nct'] = relevant_ids['id_value'].str.extract(nct_pattern)
    links = relevant_ids[relevant_ids['linked_nct'].notna()][['nct_id', 'linked_nct']].drop_duplicates()
    links = links[links['nct_id'] != links['linked_nct']]
    
    grouped_links = links.groupby('nct_id')['linked_nct'].apply(lambda x: ', '.join(sorted(list(set(x))))).reset_index()
    grouped_links.columns = ['nct_id', 'connected_trials']
    
    svef_df = pd.merge(svef_df, grouped_links, on='nct_id', how='left')
    svef_df['connected_trials'] = svef_df['connected_trials'].fillna('')
    
    return svef_df

def main():
    raw_dir = 'data/raw'
    output_dir = 'data/processed'
    audit_dir = 'data/interim/audit'
    
    for d in [output_dir, audit_dir]:
        if not os.path.exists(d): os.makedirs(d)
    
    # 1. Load
    studies, interventions, ids = load_data(raw_dir)
    
    # 2. Structural Filter (Expanded Statuses)
    print("Applying structural filters for Terminated, Suspended, Withdrawn, and Unknown...")
    initial_filtered, snapshots = filter_structural(studies, interventions)
    
    for name, snap_df in snapshots.items():
        snap_df.to_csv(os.path.join(audit_dir, f"{name}.csv"), index=False)
        print(f"Saved snapshot: {name} ({len(snap_df)} rows)")
    
    # 3. Unified SVEF Logic
    print("Applying Unified SVEF Logic (Efficacy vs Safety vs Strategic)...")
    svef_candidates, audit_trace = apply_unified_svef_logic(initial_filtered)
    
    # 4. Link Trials
    svef_candidates = link_trials(svef_candidates, ids)
    
    # 5. Save Outputs
    audit_trace.to_csv(os.path.join(audit_dir, 'svef_logic_audit.csv'), index=False)
    svef_candidates.to_csv(os.path.join('data', 'interim', 'SVEF_candidates.csv'), index=False)
    
    # 6. Summary Stats
    print("\n--- Unified Pipeline Summary ---")
    print(f"Total Trials Audited: {len(audit_trace)}")
    print(f"Total SVEF Candidates: {len(svef_candidates)}")
    print("\nStatus Breakdown of Candidates:")
    print(svef_candidates['audit_status'].value_counts().to_string())
    print(f"\nFinal output saved to: {os.path.join('data', 'interim', 'SVEF_candidates.csv')}")

if __name__ == "__main__":
    main()
