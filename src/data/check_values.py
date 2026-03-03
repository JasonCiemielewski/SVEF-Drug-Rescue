import pandas as pd
import os

def check_values():
    raw_dir = 'raw_data'
    studies = pd.read_csv(os.path.join(raw_dir, 'studies.txt'), sep='|', low_memory=False)
    interventions = pd.read_csv(os.path.join(raw_dir, 'interventions.txt'), sep='|', low_memory=False)
    
    print("Unique study types:")
    print(studies['study_type'].unique()[:10])
    
    print("Unique overall statuses:")
    print(studies['overall_status'].unique()[:10])
    
    print("Unique phases:")
    print(studies['phase'].unique()[:10])
    
    print("Unique intervention types:")
    print(interventions['intervention_type'].unique()[:10])

if __name__ == "__main__":
    check_values()
