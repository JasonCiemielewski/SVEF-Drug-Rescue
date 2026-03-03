import pandas as pd
import requests
import time
import os
import numpy as np
import re
import shutil
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
    
    references = pd.read_csv(os.path.join(raw_dir, 'study_references.txt'), sep='|', low_memory=False,
                             usecols=['nct_id', 'pmid', 'reference_type', 'citation'])
    
    return base_df, studies, calc_vals, sponsors, conditions, references

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
    
    # Secondary biologic cleanup (suffixes that missed the first pass)
    biologic_suffixes = ['ase', 'fusp', 'cept', 'alfa', 'beta', 'gamma']
    # Filter for names ending with these suffixes or containing them
    pattern = '|'.join([f"{s}$" for s in biologic_suffixes])
    df = df[~df['name'].str.contains(pattern, case=False, na=False)]
    
    return df

def process_publications(refs):
    """
    Extract DOIs, categorize PMIDs, and compute Evidence_Confidence score.
    """
    print("Processing publication metadata (PMIDs and DOIs)...")
    # Clean refs
    refs['pmid'] = pd.to_numeric(refs['pmid'], errors='coerce')
    refs['reference_type'] = refs['reference_type'].fillna('background').str.lower()
    
    # DOI Extraction from citation
    doi_pattern = r'doi:\s*([^\s;]+)'
    refs['doi'] = refs['citation'].str.extract(doi_pattern, flags=re.IGNORECASE, expand=False)
    
    # Aggregation per nct_id
    def aggregate_refs(group):
        results_pmids = group[group['reference_type'] == 'result']['pmid'].unique()
        results_pmids = [str(int(p)) for p in results_pmids if pd.notna(p)]
        
        bg_pmids = group[group['reference_type'] != 'result']['pmid'].unique()
        bg_pmids = [str(int(p)) for p in bg_pmids if pd.notna(p)]
        
        dois = group['doi'].dropna().unique()
        
        # Evidence Confidence Score
        # Weight 1.0 for results, 0.2 for background, +0.5 bonus if any results
        score = (len(results_pmids) * 1.0) + (len(bg_pmids) * 0.2)
        if len(results_pmids) > 0:
            score += 0.5
            
        return pd.Series({
            'results_pmid_list': '|'.join(results_pmids),
            'background_pmid_list': '|'.join(bg_pmids),
            'doi_list': '|'.join(dois),
            'publication_count': len(set(results_pmids + bg_pmids)),
            'Evidence_Confidence': round(score, 2)
        })

    agg_refs = refs.groupby('nct_id').apply(aggregate_refs, include_groups=False).reset_index()
    return agg_refs

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
    Enhanced with name cleaning and combination handling.
    """
    if pd.isnull(drug_name) or drug_name == '':
        return None, None, None, None
    
    # Skip placebos
    if 'placebo' in drug_name.lower():
        return None, None, None, None
    
    # Clean drug name for API
    # 1. Remove descriptive text
    clean_name = drug_name.split(',')[0].strip()
    clean_name = re.sub(r'\b(iv|intravenous|oral|tablets|capsules|active drug|matching)\b', '', clean_name, flags=re.IGNORECASE).strip()
    
    # 2. Handle simple combinations (take the first active if multiple)
    # e.g., "Drug A + Drug B" -> "Drug A"
    for separator in ['+', '/', ' and ', ' with ']:
        if separator in clean_name.lower():
            clean_name = clean_name.lower().split(separator)[0].strip()
            break
    
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
    
    # Define paths
    processed_dir = os.path.join('data', 'processed')
    archive_dir = os.path.join(processed_dir, 'archive')
    main_output_path = os.path.join(processed_dir, 'SVEF_Enriched_Final.csv')
    
    if not os.path.exists(archive_dir):
        os.makedirs(archive_dir)

    # 1. Archive existing final file if it exists
    if os.path.exists(main_output_path):
        mtime = os.path.getmtime(main_output_path)
        timestamp = datetime.fromtimestamp(mtime).strftime('%Y%m%d_%H%M%S')
        archive_path = os.path.join(archive_dir, f'SVEF_Enriched_{timestamp}.csv')
        print(f"Archiving existing dataset to: {archive_path}")
        shutil.move(main_output_path, archive_path)
    
    # Load and Join
    base_df, studies, calc_vals, sponsors, conditions, references = load_data(base_df_path, raw_dir)
    enriched_df = merge_clinical_data(base_df, studies, calc_vals, sponsors, conditions)
    
    # Feature Engineering
    enriched_df = feature_engineering(enriched_df)
    
    # Publication Enrichment
    pub_data = process_publications(references)
    enriched_df = enriched_df.merge(pub_data, on='nct_id', how='left')
    
    # Cheminformatics
    enriched_df = enrich_with_pubchem(enriched_df)
    
    # Save as the new 'Final'
    enriched_df.to_csv(main_output_path, index=False)
    print(f"\nNew enriched dataset saved to: {main_output_path}")
    
    # Summary Report
    print("\n--- Enrichment Summary Report ---")
    print(f"Total Candidate Trials: {len(enriched_df)}")
    print(f"Average Enrollment: {enriched_df['enrollment'].mean():.2f}")
    print(f"SMILES Matches Found: {enriched_df['is_dti_ready'].sum()}")
    print(f"DTI-Ready Coverage: {(enriched_df['is_dti_ready'].sum() / len(enriched_df)) * 100:.2f}%")
    
    # Publication Summary
    has_pubs = enriched_df['publication_count'].fillna(0) > 0
    has_results = enriched_df['results_pmid_list'].fillna('').str.len() > 0
    print(f"Candidates with Scholarly Evidence: {has_pubs.sum()} ({(has_pubs.sum()/len(enriched_df))*100:.2f}%)")
    print(f"Candidates with Result Publications: {has_results.sum()} ({(has_results.sum()/len(enriched_df))*100:.2f}%)")
    print(f"Average Evidence_Confidence: {enriched_df['Evidence_Confidence'].mean():.2f}")
    
    if 'agency_class' in enriched_df.columns:
        dist = enriched_df['agency_class'].value_counts()
        print("\nSponsor Distribution (Asset Origin):")
        print(dist)

if __name__ == "__main__":
    main()
