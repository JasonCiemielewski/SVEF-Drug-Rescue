import re

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