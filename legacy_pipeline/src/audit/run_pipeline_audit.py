import pandas as pd
import os

def run_pipeline_audit():
    raw_dir = 'data/raw'
    
    print("Loading data for full audit...")
    studies = pd.read_csv(os.path.join(raw_dir, 'studies.txt'), sep='|', low_memory=False)
    interventions = pd.read_csv(os.path.join(raw_dir, 'interventions.txt'), sep='|', low_memory=False)
    
    # 1. Total trials in AACT
    total_aact = len(studies)
    
    # 2. Total Phase 2, 3, 2/3 trials
    target_phases = ['PHASE2', 'PHASE3', 'PHASE2/PHASE3']
    studies_phase = studies[studies['phase'].isin(target_phases)]
    total_phase_2_3 = len(studies_phase)
    
    # 3. Phase 2, 3, 2/3 that were INTERVENTIONAL
    studies_interventional = studies_phase[studies_phase['study_type'] == 'INTERVENTIONAL']
    total_interventional = len(studies_interventional)
    
    # 4. Phase 2, 3, 2/3 Interventional that were DRUG interventions
    # Merge with interventions to filter by intervention_type
    drug_interventions = interventions[interventions['intervention_type'] == 'DRUG']
    studies_drug = pd.merge(studies_interventional[['nct_id', 'overall_status']], 
                            drug_interventions[['nct_id']], 
                            on='nct_id', how='inner').drop_duplicates('nct_id')
    total_drug = len(studies_drug)
    
    # 5. Phase 2, 3, 2/3 Interventional Drug that were TERMINATED
    studies_terminated = studies_drug[studies_drug['overall_status'] == 'TERMINATED']
    total_terminated = len(studies_terminated)
    
    # 6. Final count in SVEF Logic Audit
    # Matches our structural_merged_drug_only snapshot
    total_audit = total_terminated
    
    print("\n--- Pipeline Audit Statistics ---")
    print(f"1. Total trials in AACT: {total_aact}")
    print(f"2. Phase 2, 3, 2/3 trials: {total_phase_2_3}")
    print(f"3. Phase 2, 3, 2/3 Interventional trials: {total_interventional}")
    print(f"4. Phase 2, 3, 2/3 Interventional Drug trials: {total_drug}")
    print(f"5. Phase 2, 3, 2/3 Interventional Drug Terminated trials: {total_terminated}")
    print(f"6. Total trials in SVEF Logic Audit: {total_audit}")

if __name__ == "__main__":
    run_pipeline_audit()
