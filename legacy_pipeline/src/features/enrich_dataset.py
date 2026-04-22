import pandas as pd
import requests
import time
import os
import numpy as np
import re
import shutil
from datetime import datetime

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
    Ingests relational AACT design tables and filters them to include only data 
    relevant to the NCT IDs present in the base candidate dataset.
    
    Args:
        base_df_path (str): Path to the candidate CSV file (e.g., SVEF_candidates.csv).
        raw_dir (str): Path to the directory containing raw AACT .txt files.
        
    Returns:
        tuple: A tuple containing the base DataFrame and filtered DataFrames for 
               studies, calculated values, sponsors, conditions, references, 
               design groups, and design group interventions.
    """
    print(f"Loading base dataset: {base_df_path}")
    base_df = pd.read_csv(base_df_path)
    target_nct_ids = set(base_df['nct_id'].unique())
    
    def load_filtered(filename, cols, sep='|'):
        """Helper to load AACT files in chunks and filter by NCT ID."""
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
    """
    Maps interventions to their specific roles (e.g., Experimental, Placebo) 
    using the AACT design group tables.
    
    Args:
        base_df (pd.DataFrame): The candidate dataset.
        design_groups (pd.DataFrame): Filtered design_groups data.
        dg_interventions (pd.DataFrame): Filtered design_group_interventions data.
        
    Returns:
        pd.DataFrame: The dataset enriched with a 'group_type' column.
    """
    print("Mapping intervention roles via design groups...")
    if 'id' not in base_df.columns:
        print("Warning: 'id' column missing. Attempting to assign temporary IDs.")
        base_df['id'] = range(len(base_df))
    
    base_df['id'] = base_df['id'].fillna('0').astype(str)
    role_map = pd.merge(dg_interventions, design_groups, on=['nct_id', 'design_group_id'])
    role_map = role_map.groupby(['nct_id', 'intervention_id'])['group_type'].apply(lambda x: '|'.join(sorted(x.unique()))).reset_index()
    df = pd.merge(base_df, role_map, left_on=['nct_id', 'id'], right_on=['nct_id', 'intervention_id'], how='left')
    df['group_type'] = df['group_type'].fillna('Other')
    return df

def merge_clinical_metadata(df, studies, calc_vals, sponsors, conditions):
    """
    Merges core clinical trial metadata (enrollment, duration, sponsors, conditions).
    
    Args:
        df (pd.DataFrame): The candidate dataset.
        studies, calc_vals, sponsors, conditions: Filtered metadata DataFrames.
        
    Returns:
        pd.DataFrame: The enriched dataset.
    """
    print("Merging enriched clinical metadata...")
    # RESOLVE KeyError: Explicitly drop overlapping columns that come from Module 1
    # but are also present in the AACT studies.txt file.
    overlap_cols = ['enrollment', 'start_date', 'primary_completion_date', 'official_title']
    df = df.drop(columns=[c for c in overlap_cols if c in df.columns])
    
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
    Categorizes the reason for a PubChem SMILES recovery failure based on nomenclature.
    
    Args:
        drug_name (str): The name of the drug/intervention.
        
    Returns:
        str: A category label (e.g., 'PLACEBO_EQUIVALENT', 'POSSIBLE_INTERNAL_PROPRIETARY').
    """
    name = str(drug_name).lower()
    
    placebo_keywords = ['placebo', 'vehicle', 'comparator', 'arm 1', 'arm 2', 'control', 'standard of care', 'sham']
    if any(k in name for k in placebo_keywords):
        return 'PLACEBO_EQUIVALENT'
    
    logistical_keywords = ['treatment', 'regimen', 'dosing', 'standard care', 'infusion', 'therapy', 'standard treatment']
    if any(k in name for k in logistical_keywords):
        return 'LOGISTICAL_GENERIC'
    
    if re.search(r'[A-Z]{2,}-\d+', str(drug_name)) or re.search(r'\d+', str(drug_name)):
        return 'POSSIBLE_INTERNAL_PROPRIETARY'
        
    return 'UNKNOWN_NOMENCLATURE'

def query_pubchem(identifier, namespace='name'):
    """
    Queries the PubChem PUG REST API for compound properties.
    
    Args:
        identifier (str): The search term (e.g., drug name or CAS).
        namespace (str): The search namespace (default 'name').
        
    Returns:
        list: A list of result dictionaries containing CID, SMILES, MW, and XLogP.
    """
    base_url = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/{namespace}/{identifier}/property/SMILES,ConnectivitySMILES,MolecularWeight,XLogP/JSON"
    for attempt in range(3):
        try:
            response = requests.get(base_url, timeout=15)
            if response.status_code == 200:
                data = response.json()
                properties = data.get('PropertyTable', {}).get('Properties', [])
                results = []
                for props in properties:
                    smiles = props.get('SMILES') or props.get('ConnectivitySMILES')
                    results.append({
                        'CID': props.get('CID'),
                        'SMILES': smiles,
                        'MolecularWeight': props.get('MolecularWeight'),
                        'XLogP': props.get('XLogP')
                    })
                return results
            elif response.status_code == 503:
                time.sleep((attempt + 1) * 2)
            else: break
        except Exception: time.sleep(1)
    return []

def get_pubchem_data_tiered(drug_name, context_text=""):
    """
    Performs a tiered lookup (Name -> CAS -> Synonym) to maximize SMILES recovery.
    
    Args:
        drug_name (str): Primary drug name.
        context_text (str): Additional text (e.g., trial title) to search for CAS numbers.
        
    Returns:
        tuple: (list of results, final match tier string).
    """
    if pd.isnull(drug_name) or drug_name == '' or 'placebo' in str(drug_name).lower():
        return [], "Failed"
    
    clean_name = clean_drug_name(drug_name)
    all_results = {}

    def add_results(results, tier):
        for r in results:
            cid = r.get('CID')
            if cid and cid not in all_results:
                r['matched_by'] = tier
                all_results[cid] = r

    name_results = query_pubchem(clean_name, 'name')
    add_results(name_results, "Name")
    
    cas_pattern = r'\b(\d{2,7}-\d{2}-\d)\b'
    cas_matches = re.findall(cas_pattern, str(context_text))
    for cas in cas_matches:
        time.sleep(0.2)
        cas_results = query_pubchem(cas, 'name')
        add_results(cas_results, "CAS")
    
    syn_url = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/{clean_name}/synonyms/JSON"
    try:
        syn_res = requests.get(syn_url, timeout=10)
        if syn_res.status_code == 200:
            synonyms = syn_res.json().get('InformationList', {}).get('Information', [{}])[0].get('Synonym', [])
            for syn in synonyms[:3]:
                time.sleep(0.2)
                syn_results = query_pubchem(syn, 'name')
                add_results(syn_results, "Synonym")
    except: pass

    if all_results:
        tiers = [r['matched_by'] for r in all_results.values()]
        final_tier = "Name" if "Name" in tiers else ("CAS" if "CAS" in tiers else "Synonym")
        return list(all_results.values()), final_tier
    
    return [], "Failed"

def clean_drug_name(drug_name):
    """
    Strips clinical trial prefixes, doses, and salt forms from drug names to 
    improve PubChem match rates.
    
    Args:
        drug_name (str): The raw intervention name.
        
    Returns:
        str: The cleaned drug name.
    """
    raw_name = str(drug_name)
    clean = re.sub(r'^(?:comparator|arm \d+|arm|group|active|placebo|sham|standard of care|vehicle|regimen)\s*[:\-]\s*', '', raw_name, flags=re.IGNORECASE)
    clean = re.sub(r'\[.*?\]', '', clean)
    clean = re.sub(r'\(.*?\)', '', clean)
    clean = clean.split(',')[0].split(';')[0].strip()
    
    dose_pattern = r'\b(?:\d+ ?mg|\d+ ?g|\d+ ?mcg|\d+ ?u/kg|iv|intravenous|oral|tablets?|capsules?|active drug|matching|hydrochloride|sodium|salt|ointment|gel|solution|capsule|product|treatment|arm|preceding|study|phase|forming|phosphate|besylate|acetate|fumarate|maleate|succinate|tartrate|citrate|mesylate)\b'
    clean = re.sub(dose_pattern, '', clean, flags=re.IGNORECASE).strip()
    clean = re.sub(r'\d*\.?\d*%', '', clean).strip()
    clean = re.sub(r'\s+\d+\.?\d*$', '', clean).strip()
    clean = re.sub(r'\s+', ' ', clean).strip()
    clean = re.sub(r'^[^a-zA-Z0-9]+|[^a-zA-Z0-9]+$', '', clean).strip()
    
    if not clean or len(clean) < 2 or 'placebo' in clean.lower(): 
        if re.match(r'^\d+ ?mg|tablet|capsule', raw_name, re.I) or 'placebo' in raw_name.lower():
            return ""
        return raw_name.split(',')[0].strip()
    return clean

def enrich_with_pubchem_architect(df, cache_path=None):
    """
    The primary engine for chemical recovery. Handles caching, 1:Many matching, 
    and multi-threaded lookups.
    
    Args:
        df (pd.DataFrame): Candidate dataset.
        cache_path (str): Path to the SMILES cache file.
        
    Returns:
        pd.DataFrame: Dataset exploded with SMILES and chemical properties.
    """
    if cache_path is None: cache_path = os.path.join('data', 'interim', 'smiles_cache.csv')
    summary = {"Name": 0, "CAS": 0, "Synonym": 0, "Failed": 0}
    
    pubchem_cache = {}
    if os.path.exists(cache_path):
        print(f"Loading architectural cache from {cache_path}...")
        cache_df = pd.read_csv(cache_path)
        cache_df['name_lower'] = cache_df['name'].astype(str).str.lower().str.strip()
        for name_l, group in cache_df.groupby('name_lower'):
            pubchem_cache[name_l] = group.to_dict(orient='records')

    unique_drugs = df[['name', 'official_title']].drop_duplicates()
    total = len(unique_drugs)
    print(f"Bioinformatics Recovery Phase: {total} unique drug names to process.")
    
    all_drug_results = []
    
    for counter, (i, row) in enumerate(unique_drugs.iterrows()):
        drug = str(row['name'])
        title = str(row['official_title'])
        drug_key = drug.lower().strip()
        
        if drug_key in pubchem_cache:
            entries = pubchem_cache[drug_key]
            for entry in entries:
                entry['name'] = drug
                m_by = entry.get('matched_by', 'Failed')
                if m_by in summary: summary[m_by] += 1
            all_drug_results.extend(entries)
        else:
            if counter % 50 == 0: print(f"[{datetime.now().strftime('%H:%M:%S')}] Processing {counter}/{total}...")
            results, match_tier = get_pubchem_data_tiered(drug, title)
            
            if not results:
                new_entry = {
                    'name': drug, 'pubchem_cid': np.nan, 'smiles': np.nan, 
                    'molecular_weight': np.nan, 'logp': np.nan, 'matched_by': 'Failed'
                }
                all_drug_results.append(new_entry)
                pubchem_cache[drug_key] = [new_entry]
                summary['Failed'] += 1
            else:
                entries = []
                for r in results:
                    new_entry = {
                        'name': drug,
                        'pubchem_cid': r['CID'],
                        'smiles': r['SMILES'],
                        'molecular_weight': r['MolecularWeight'],
                        'logp': r['XLogP'],
                        'matched_by': r['matched_by']
                    }
                    entries.append(new_entry)
                    summary[r['matched_by']] += 1
                all_drug_results.extend(entries)
                pubchem_cache[drug_key] = entries
            
            time.sleep(0.2)
            if len(all_drug_results) % 100 == 0: 
                flat_cache = [item for sublist in pubchem_cache.values() for item in sublist]
                atomic_write_cache_df(pd.DataFrame(flat_cache), cache_path)

    print("\n--- SMILES Recovery Summary ---")
    for k, v in summary.items(): print(f"Matched by {k}: {v}")
    
    flat_cache = [item for sublist in pubchem_cache.values() for item in sublist]
    atomic_write_cache_df(pd.DataFrame(flat_cache), cache_path)
    
    results_df = pd.DataFrame(all_drug_results)
    results_df['molecular_weight'] = pd.to_numeric(results_df['molecular_weight'], errors='coerce')
    results_df['logp'] = pd.to_numeric(results_df['logp'], errors='coerce')
    
    results_df.loc[results_df['matched_by'] == 'Failed', 'failure_reason'] = results_df[results_df['matched_by'] == 'Failed']['name'].apply(classify_failure)
    
    df['name_norm'] = df['name'].astype(str).str.lower().str.strip()
    results_df['name_norm'] = results_df['name'].astype(str).str.lower().str.strip()
    
    results_df = results_df.drop(columns=['name'])
    df = df.merge(results_df, on='name_norm', how='left')
    df = df.drop(columns=['name_norm'])
    
    df['is_dti_ready'] = df['smiles'].notnull()
    df['is_lipinski_compliant'] = (df['molecular_weight'] < 500) & (df['logp'] < 5)
    return df

def atomic_write_cache_df(df, cache_path):
    """Safely writes a DataFrame to CSV using a temporary file to prevent corruption."""
    temp_path = cache_path + ".tmp"
    try:
        df.to_csv(temp_path, index=False)
        if os.path.exists(cache_path): os.remove(cache_path)
        os.rename(temp_path, cache_path)
    except Exception as e: print(f"Cache write error: {e}")

def feature_engineering_advanced(df):
    """
    Calculates trial duration, log-scaled enrollment, and normalized safety scores.
    
    Args:
        df (pd.DataFrame): Enriched dataset.
        
    Returns:
        pd.DataFrame: Dataset with advanced statistical features.
    """
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
    """
    Aggregates trial references into publication counts and evidence confidence scores.
    
    Args:
        refs (pd.DataFrame): Filtered study_references data.
        
    Returns:
        pd.DataFrame: Aggregated evidence metrics grouped by NCT ID.
    """
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
    """Standalone execution logic for enrichment testing."""
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
    
    proprietary_leads = df[df['failure_reason'] == 'POSSIBLE_INTERNAL_PROPRIETARY'][['name', 'nct_id', 'group_type', 'agency_class']].drop_duplicates(subset=['name'])
    rescue_path = os.path.join(processed_dir, 'Possible_Internal_Proprietary_Rescue_Leads.csv')
    proprietary_leads.to_csv(rescue_path, index=False)
    
    print(f"\nArchitect-Hardened dataset saved to: {main_output_path}")
    print(f"Identified Possible Internal Proprietary Codes: {len(proprietary_leads)}")
    print(f"Proprietary rescue list saved to: {rescue_path}")

if __name__ == "__main__":
    main()
