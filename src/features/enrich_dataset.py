import pandas as pd
import requests
import time
import os
import numpy as np
from datetime import datetime

def load_data(base_df_path, raw_dir):
    """
    Load the base SVEF dataset and the additional AACT tables for enrichment.
    """
    print(f"Loading base dataset: {base_df_path}")
    base_df = pd.read_csv(base_df_path)
    
    print("Loading supplemental AACT tables...")
    studies = pd.read_csv(os.path.join(raw_dir, 'studies.txt'), sep='|', low_memory=False, 
                          usecols=['nct_id', 'enrollment', 'start_date', 'primary_completion_date'])
    
    calc_vals = pd.read_csv(os.path.join(raw_dir, 'calculated_values.txt'), sep='|', low_memory=False,
                            usecols=['nct_id', 'actual_duration'])
    
    sponsors = pd.read_csv(os.path.join(raw_dir, 'sponsors.txt'), sep='|', low_memory=False,
                           usecols=['nct_id', 'agency_class', 'lead_or_collaborator'])
    
    conditions = pd.read_csv(os.path.join(raw_dir, 'browse_conditions.txt'), sep='|', low_memory=False,
                             usecols=['nct_id', 'mesh_term'])
    
    return base_df, studies, calc_vals, sponsors, conditions

def merge_clinical_data(base_df, studies, calc_vals, sponsors, conditions):
    """
    Perform left-joins and aggregate multiple entries (MeSH and Sponsors).
    """
    print("Merging clinical volume and duration data...")
    # Join studies and calculated values
    df = base_df.merge(studies, on='nct_id', how='left')
    df = df.merge(calc_vals, on='nct_id', how='left')
    
    # Handle sponsors (filter for lead sponsors only)
    lead_sponsors = sponsors[sponsors['lead_or_collaborator'] == 'lead'].drop_duplicates(subset=['nct_id'])
    df = df.merge(lead_sponsors[['nct_id', 'agency_class']], on='nct_id', how='left')
    
    # Handle browse_conditions (collapse MeSH terms to pipe-separated strings)
    print("Collapsing MeSH terms...")
    collapsed_conditions = conditions.groupby('nct_id')['mesh_term'].apply(lambda x: '|'.join(x.dropna().unique())).reset_index()
    df = df.merge(collapsed_conditions, on='nct_id', how='left')
    
    return df

def feature_engineering(df):
    """
    Temporal calculations and safety score normalization.
    """
    print("Performing temporal feature engineering...")
    # Convert dates
    df['start_date'] = pd.to_datetime(df['start_date'], errors='coerce')
    df['primary_completion_date'] = pd.to_datetime(df['primary_completion_date'], errors='coerce')
    
    # Calculate duration if missing
    def calculate_duration(row):
        if pd.notnull(row['actual_duration']):
            return row['actual_duration']
        if pd.notnull(row['start_date']) and pd.notnull(row['primary_completion_date']):
            delta = (row['primary_completion_date'] - row['start_date']).days
            return delta if delta > 0 else np.nan
        return np.nan

    df['trial_duration_days'] = df.apply(calculate_duration, axis=1)
    
    # Safety Score Calculation (Min-Max scaling for enrollment and duration)
    print("Calculating Safety_Score...")
    # Fill NaNs for normalization (conservative approach: 0)
    e_min = df['enrollment'].min()
    e_max = df['enrollment'].max()
    d_min = df['trial_duration_days'].min()
    d_max = df['trial_duration_days'].max()
    
    df['norm_enrollment'] = (df['enrollment'] - e_min) / (e_max - e_min) if (e_max - e_min) != 0 else 0
    df['norm_duration'] = (df['trial_duration_days'] - d_min) / (d_max - d_min) if (d_max - d_min) != 0 else 0
    
    # Weighted Safety_Score (0.0 to 1.0)
    df['Safety_Score'] = (df['norm_enrollment'].fillna(0) * 0.5) + (df['norm_duration'].fillna(0) * 0.5)
    
    return df

def get_pubchem_data(drug_name):
    """
    Retrieve molecular properties from PubChem PUG-REST API.
    """
    if pd.isnull(drug_name) or drug_name == '':
        return None, None, None, None
    
    # Clean drug name for API (e.g., handle common salt forms or prefixes)
    clean_name = drug_name.split(',')[0].strip()
    
    base_url = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/{clean_name}/property/IsomericSMILES,ConnectivitySMILES,MolecularWeight,XLogP/JSON"
    
    try:
        response = requests.get(base_url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            props = data['PropertyTable']['Properties'][0]
            # Use IsomericSMILES if available, otherwise ConnectivitySMILES
            smiles = props.get('IsomericSMILES') or props.get('ConnectivitySMILES')
            return (
                props.get('CID'),
                smiles,
                props.get('MolecularWeight'),
                props.get('XLogP')
            )
        else:
            return None, None, None, None
    except Exception as e:
        print(f"Error fetching data for {drug_name}: {e}")
        return None, None, None, None

def enrich_with_pubchem(df):
    """
    Asynchronously retrieve PubChem data for unique drug names and map back.
    """
    unique_drugs = df['name'].dropna().unique()
    print(f"Querying PubChem for {len(unique_drugs)} unique drug candidates...")
    
    pubchem_cache = {}
    for i, drug in enumerate(unique_drugs):
        if i % 10 == 0:
            print(f"Processed {i}/{len(unique_drugs)} drugs...")
        
        cid, smiles, mw, logp = get_pubchem_data(drug)
        pubchem_cache[drug] = {
            'pubchem_cid': cid,
            'smiles': smiles,
            'molecular_weight': mw,
            'logp': logp
        }
        time.sleep(0.2) # Rate limiting (5 requests/sec)
        
    # Map cache back to main dataframe
    cache_df = pd.DataFrame.from_dict(pubchem_cache, orient='index').reset_index().rename(columns={'index': 'name'})
    df = df.merge(cache_df, on='name', how='left')
    
    # DTI-Ready Flag
    df['is_dti_ready'] = df['smiles'].notnull()
    
    return df

def main():
    base_df_path = os.path.join('data', 'processed', 'SVEF_candidates.csv')
    raw_dir = os.path.join('data', 'raw')
    output_path = os.path.join('data', 'processed', 'SVEF_Enriched_Final.csv')
    
    # Load and Join
    base_df, studies, calc_vals, sponsors, conditions = load_data(base_df_path, raw_dir)
    enriched_df = merge_clinical_data(base_df, studies, calc_vals, sponsors, conditions)
    
    # Feature Engineering
    enriched_df = feature_engineering(enriched_df)
    
    # Cheminformatics
    enriched_df = enrich_with_pubchem(enriched_df)
    
    # Save
    enriched_df.to_csv(output_path, index=False)
    print(f"\nFinal enriched dataset saved to: {output_path}")
    
    # Summary Report
    print("\n--- Enrichment Summary Report ---")
    print(f"Total Candidate Trials: {len(enriched_df)}")
    print(f"Average Enrollment: {enriched_df['enrollment'].mean():.2f}")
    print(f"SMILES Matches Found: {enriched_df['is_dti_ready'].sum()}")
    print(f"DTI-Ready Coverage: {(enriched_df['is_dti_ready'].sum() / len(enriched_df)) * 100:.2f}%")
    
    if 'agency_class' in enriched_df.columns:
        dist = enriched_df['agency_class'].value_counts()
        print("\nSponsor Distribution (Asset Origin):")
        print(dist)

if __name__ == "__main__":
    main()
