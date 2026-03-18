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
    Ingests relational design tables with strict string-casting for join integrity.
    """
    print(f"Loading base dataset: {base_df_path}")
    base_df = pd.read_csv(base_df_path)
    target_nct_ids = set(base_df['nct_id'].unique())
    
    def load_filtered(filename, cols, sep='|'):
        print(f"Loading and filtering {filename}...")
        chunks = pd.read_csv(os.path.join(raw_dir, filename), sep=sep, low_memory=False, usecols=cols, chunksize=100000)
        df = pd.concat([chunk[chunk['nct_id'].isin(target_nct_ids)] for chunk in chunks])
        for col in ['nct_id', 'id', 'design_group_id', 'intervention_id']:
            if col in df.columns:
                df[col] = df[col].astype(str)
        return df

    studies = load_filtered('studies.txt', ['nct_id', 'enrollment', 'start_date', 'primary_completion_date', 'official_title'])
    calc_vals = load_filtered('calculated_values.txt', ['nct_id', 'actual_duration'])
    sponsors = load_filtered('sponsors.txt', ['nct_id', 'agency_class', 'lead_or_collaborator'])
    conditions = load_filtered('browse_conditions.txt', ['nct_id', 'mesh_term'])
    references = load_filtered('study_references.txt', ['nct_id', 'pmid', 'reference_type', 'citation'])
    design_groups = load_filtered('design_groups.txt', ['nct_id', 'id', 'group_type']).rename(columns={'id': 'design_group_id'})
    design_group_interventions = load_filtered('design_group_interventions.txt', ['nct_id', 'design_group_id', 'intervention_id'])
    
    return base_df, studies, calc_vals, sponsors, conditions, references, design_groups, design_group_interventions

def map_intervention_roles(base_df, design_groups, dg_interventions):
    print("Mapping intervention roles via design groups...")
    base_df['id'] = base_df['id'].astype(str)
    role_map = pd.merge(dg_interventions, design_groups, on=['nct_id', 'design_group_id'])
    role_map = role_map.groupby(['nct_id', 'intervention_id'])['group_type'].apply(lambda x: '|'.join(sorted(x.unique()))).reset_index()
    df = pd.merge(base_df, role_map, left_on=['nct_id', 'id'], right_on=['nct_id', 'intervention_id'], how='left')
    df['group_type'] = df['group_type'].fillna('Other')
    return df

def merge_clinical_metadata(df, studies, calc_vals, sponsors, conditions):
    print("Merging enriched clinical metadata...")
    df = df.merge(studies, on='nct_id', how='left')
    df = df.merge(calc_vals, on='nct_id', how='left')
    lead_sponsors = sponsors[sponsors['lead_or_collaborator'] == 'lead'].drop_duplicates(subset=['nct_id'])
    df = df.merge(lead_sponsors[['nct_id', 'agency_class']], on='nct_id', how='left')
    if not conditions.empty:
        collapsed_conditions = conditions.groupby('nct_id')['mesh_term'].apply(lambda x: '|'.join(x.dropna().unique())).reset_index()
        df = df.merge(collapsed_conditions, on='nct_id', how='left')
    
    biologic_pattern = r'-(?:mab|fusp|cept|zumab|ximab|umab|ase|alfa|beta|gamma)$|vaccine|cell therapy|antibody|gene therapy|antigen'
    df = df[~df['name'].str.contains(biologic_pattern, case=False, na=False)]
    return df

def classify_failure(drug_name):
    """
    Categorizes the reason for a PubChem SMILES recovery failure.
    """
    name = str(drug_name).lower()
    
    # 1. Placebo Equivalents
    placebo_keywords = ['placebo', 'vehicle', 'comparator', 'arm 1', 'arm 2', 'control', 'standard of care', 'sham']
    if any(k in name for k in placebo_keywords):
        return 'PLACEBO_EQUIVALENT'
    
    # 2. Logistical/Generic
    logistical_keywords = ['treatment', 'regimen', 'dosing', 'standard care', 'infusion', 'therapy', 'standard treatment']
    if any(k in name for k in logistical_keywords):
        return 'LOGISTICAL_GENERIC'
    
    # 3. Possible Internal Proprietary (Alphanumeric codes like AZD-1234, MK-0873)
    # Check for digit-containing strings or hyphenated codes
    if re.search(r'[A-Z]{2,}-\d+', str(drug_name)) or re.search(r'\d+', str(drug_name)):
        return 'POSSIBLE_INTERNAL_PROPRIETARY'
        
    return 'UNKNOWN_NOMENCLATURE'

def query_pubchem(identifier, namespace='name'):
    base_url = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/{namespace}/{identifier}/property/SMILES,ConnectivitySMILES,MolecularWeight,XLogP/JSON"
    for attempt in range(3):
        try:
            response = requests.get(base_url, timeout=15)
            if response.status_code == 200:
                data = response.json()
                properties = data.get('PropertyTable', {}).get('Properties', [])
                if not properties: return None, None, None, None
                props = properties[0]
                smiles = props.get('SMILES') or props.get('ConnectivitySMILES')
                return props.get('CID'), smiles, props.get('MolecularWeight'), props.get('XLogP')
            elif response.status_code == 503:
                time.sleep((attempt + 1) * 2)
            else: break
        except Exception: time.sleep(1)
    return None, None, None, None

def clean_drug_name(drug_name):
    raw_name = str(drug_name)
    # Strip clinical trial prefixes
    clean = re.sub(r'^(?:comparator|arm|group|active|placebo|sham|standard of care|vehicle|regimen)\s*[:\-]\s*', '', raw_name, flags=re.IGNORECASE)
    clean = re.sub(r'\[.*?\]', '', clean)
    clean = re.sub(r'\(.*?\)', '', clean)
    clean = clean.split(',')[0].split(';')[0].strip()
    dose_pattern = r'\b(\d+ ?mg|\d+ ?g|\d+ ?mcg|\d+ ?u/kg|iv|intravenous|oral|tablets?|capsules?|active drug|matching|hydrochloride|sodium|salt|ointment|gel|solution|capsule|product|treatment|arm|preceding|study|phase|forming|phosphate|besylate|acetate|fumarate|maleate|succinate|tartrate|citrate)\b'
    clean = re.sub(dose_pattern, '', clean, flags=re.IGNORECASE).strip()
    clean = re.sub(r'\d*\.?\d*%', '', clean).strip()
    clean = re.sub(r'\s+\d+\.?\d*$', '', clean).strip()
    clean = re.sub(r'\s+', ' ', clean).strip()
    clean = re.sub(r'^[^a-zA-Z0-9]+|[^a-zA-Z0-9]+$', '', clean).strip()
    if len(clean) < 2: clean = raw_name.split(',')[0].strip()
    return clean

def get_pubchem_data_tiered(drug_name, context_text=""):
    if pd.isnull(drug_name) or drug_name == '' or 'placebo' in str(drug_name).lower():
        return None, None, None, None, "Failed"
    clean_name = clean_drug_name(drug_name)
    cid, smiles, mw, logp = query_pubchem(clean_name, 'name')
    if smiles: return cid, smiles, mw, logp, "Name"
    cas_pattern = r'\b(\d{2,7}-\d{2}-\d)\b'
    cas_matches = re.findall(cas_pattern, str(context_text))
    for cas in cas_matches:
        time.sleep(0.2)
        cid, smiles, mw, logp = query_pubchem(cas, 'name')
        if smiles: return cid, smiles, mw, logp, "CAS"
    syn_url = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/{clean_name}/synonyms/JSON"
    try:
        syn_res = requests.get(syn_url, timeout=10)
        if syn_res.status_code == 200:
            synonyms = syn_res.json().get('InformationList', {}).get('Information', [{}])[0].get('Synonym', [])
            for syn in synonyms[:3]:
                time.sleep(0.2)
                cid, smiles, mw, logp = query_pubchem(syn, 'name')
                if smiles: return cid, smiles, mw, logp, "Synonym"
    except: pass
    return None, None, None, None, "Failed"

def atomic_write_cache(pubchem_cache, cache_path):
    temp_path = cache_path + ".tmp"
    try:
        cache_df = pd.DataFrame.from_dict(pubchem_cache, orient='index').reset_index().rename(columns={'index': 'name_lower'})
        cache_df.to_csv(temp_path, index=False)
        if os.path.exists(cache_path): os.remove(cache_path)
        os.rename(temp_path, cache_path)
    except Exception as e: print(f"Cache write error: {e}")

def enrich_with_pubchem_architect(df, cache_path=None):
    if cache_path is None: cache_path = os.path.join('data', 'interim', 'smiles_cache.csv')
    summary = {"Name": 0, "CAS": 0, "Synonym": 0, "Failed": 0}
    if os.path.exists(cache_path):
        print(f"Loading architectural cache from {cache_path}...")
        cache_df = pd.read_csv(cache_path)
        cache_df['name_lower'] = cache_df['name'].astype(str).str.lower().str.strip()
        cache_df = cache_df.drop_duplicates(subset=['name_lower'], keep='last')
        pubchem_cache = cache_df.set_index('name_lower').to_dict(orient='index')
    else: pubchem_cache = {}

    unique_drugs = df[['name', 'official_title']].drop_duplicates()
    total = len(unique_drugs)
    print(f"Bioinformatics Recovery Phase: {total} unique drug names to process.")
    
    final_results = []
    for counter, (i, row) in enumerate(unique_drugs.iterrows()):
        drug = str(row['name'])
        title = str(row['official_title'])
        drug_key = drug.lower().strip()
        
        if drug_key in pubchem_cache:
            entry = pubchem_cache[drug_key]
            entry['name'] = drug
            m_by = entry.get('matched_by')
            if pd.isna(m_by) or m_by not in summary: m_by = "Name" if pd.notnull(entry.get('smiles')) else "Failed"
            final_results.append(entry)
            summary[m_by] += 1
        else:
            if counter % 50 == 0: print(f"[{datetime.now().strftime('%H:%M:%S')}] Processing {counter}/{total}...")
            cid, smiles, mw, logp, match_tier = get_pubchem_data_tiered(drug, title)
            new_entry = {'name': drug, 'pubchem_cid': cid, 'smiles': smiles, 'molecular_weight': mw, 'logp': logp, 'matched_by': match_tier}
            final_results.append(new_entry)
            pubchem_cache[drug_key] = new_entry
            summary[match_tier] += 1
            time.sleep(0.2)
            if len(final_results) % 100 == 0: atomic_write_cache(pubchem_cache, cache_path)

    print("\n--- SMILES Recovery Summary ---")
    for k, v in summary.items(): print(f"Matched by {k}: {v}")
    atomic_write_cache(pubchem_cache, cache_path)
    
    results_df = pd.DataFrame(final_results).drop_duplicates(subset=['name'])
    results_df['molecular_weight'] = pd.to_numeric(results_df['molecular_weight'], errors='coerce')
    results_df['logp'] = pd.to_numeric(results_df['logp'], errors='coerce')
    
    # NEW: Classify reasons for remaining failures
    results_df.loc[results_df['matched_by'] == 'Failed', 'failure_reason'] = results_df[results_df['matched_by'] == 'Failed']['name'].apply(classify_failure)
    
    # CASE-INSENSITIVE MERGE: Normalize names for joining
    df['name_norm'] = df['name'].astype(str).str.lower().str.strip()
    results_df['name_norm'] = results_df['name'].astype(str).str.lower().str.strip()
    
    # Drop the original 'name' from results_df to avoid suffix confusion, keeping the one from df
    results_df = results_df.drop(columns=['name'])
    
    df = df.merge(results_df, on='name_norm', how='left')
    df = df.drop(columns=['name_norm'])
    
    df['is_dti_ready'] = df['smiles'].notnull()
    df['is_lipinski_compliant'] = (df['molecular_weight'] < 500) & (df['logp'] < 5)
    return df

def feature_engineering_advanced(df):
    print("Executing Advanced Feature Engineering...")
    df['start_date'] = pd.to_datetime(df['start_date'], errors='coerce')
    df['primary_completion_date'] = pd.to_datetime(df['primary_completion_date'], errors='coerce')
    df['trial_duration_days'] = (df['primary_completion_date'] - df['start_date']).dt.days
    df['trial_duration_days'] = df['trial_duration_days'].apply(lambda x: x if x > 0 else np.nan)
    df['log_enrollment'] = np.log1p(df['enrollment'])
    def norm(col):
        if col not in df.columns or df[col].dropna().empty: return np.nan
        c_min, c_max = df[col].min(), df[col].max()
        return (df[col] - c_min) / (c_max - c_min) if (c_max - c_min) != 0 else np.nan
    df['norm_enrollment'] = norm('log_enrollment')
    df['norm_duration'] = norm('trial_duration_days')
    df['Safety_Score'] = df[['norm_enrollment', 'norm_duration']].mean(axis=1)
    return df

def process_publications(refs):
    if refs.empty: return pd.DataFrame()
    refs = refs.copy()
    refs['pmid'] = pd.to_numeric(refs['pmid'], errors='coerce')
    refs['reference_type'] = refs['reference_type'].fillna('background').str.lower()
    doi_pattern = r'doi:\s*([^\s;]+)'
    refs['doi'] = refs['citation'].str.extract(doi_pattern, flags=re.IGNORECASE, expand=False)
    def aggregate_refs(group):
        rp = [str(int(p)) for p in group[group['reference_type'] == 'result']['pmid'].unique() if pd.notna(p)]
        bp = [str(int(p)) for p in group[group['reference_type'] != 'result']['pmid'].unique() if pd.notna(p)]
        score = (len(rp) * 1.0) + (len(bp) * 0.2) + (0.5 if rp else 0)
        return pd.Series({'publication_count': len(set(rp + bp)), 'Evidence_Confidence': round(score, 2), 'results_pmid_list': '|'.join(rp), 'background_pmid_list': '|'.join(bp), 'doi_list': '|'.join(group['doi'].dropna().unique())})
    return refs.groupby('nct_id').apply(aggregate_refs, include_groups=False).reset_index()

def main():
    base_df_path = os.path.join('data', 'interim', 'SVEF_candidates.csv')
    raw_dir = os.path.join('data', 'raw')
    processed_dir = os.path.join('data', 'processed')
    main_output_path = os.path.join(processed_dir, 'SVEF_Enriched_Final.csv')
    if not os.path.exists(os.path.join(processed_dir, 'archive')): os.makedirs(os.path.join(processed_dir, 'archive'))
    if os.path.exists(main_output_path):
        mtime = os.path.getmtime(main_output_path)
        timestamp = datetime.fromtimestamp(mtime).strftime('%Y%m%d_%H%M%S')
        shutil.move(main_output_path, os.path.join(processed_dir, 'archive', f'SVEF_Enriched_{timestamp}.csv'))
    base_df, studies, calc_vals, sponsors, conditions, refs, dg, dg_int = load_data(base_df_path, raw_dir)
    df = map_intervention_roles(base_df, dg, dg_int)
    df = merge_clinical_metadata(df, studies, calc_vals, sponsors, conditions)
    df = feature_engineering_advanced(df)
    pub_data = process_publications(refs)
    if not pub_data.empty: df = df.merge(pub_data, on='nct_id', how='left')
    pub_cols = ['publication_count', 'Evidence_Confidence', 'results_pmid_list', 'background_pmid_list', 'doi_list']
    for col in pub_cols:
        if col not in df.columns: df[col] = 0 if 'count' in col or 'Confidence' in col else ''
        else: df[col] = df[col].fillna(0) if 'count' in col or 'Confidence' in col else df[col].fillna('')
    df = enrich_with_pubchem_architect(df)
    
    print("Finalizing Hardened Total Evidence Dataset...")
    df = df.drop_duplicates(subset=['nct_id', 'name'])
    df.to_csv(main_output_path, index=False)
    
    # NEW: Export possible proprietary rescue leads
    proprietary_leads = df[df['failure_reason'] == 'POSSIBLE_INTERNAL_PROPRIETARY'][['name', 'nct_id', 'group_type', 'agency_class']].drop_duplicates(subset=['name'])
    rescue_path = os.path.join(processed_dir, 'Possible_Internal_Proprietary_Rescue_Leads.csv')
    proprietary_leads.to_csv(rescue_path, index=False)
    
    print(f"\nArchitect-Hardened dataset saved to: {main_output_path}")
    print(f"Identified Possible Internal Proprietary Codes: {len(proprietary_leads)}")
    print(f"Proprietary rescue list saved to: {rescue_path}")

if __name__ == "__main__":
    main()
