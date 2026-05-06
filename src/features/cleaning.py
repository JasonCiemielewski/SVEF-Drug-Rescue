import re
import pandas as pd

def clean_drug_name(drug_name):
    """
    Strips clinical trial prefixes, doses, and salt forms from drug names to 
    improve PubChem match rates.
    
    Args:
        drug_name (str): The raw intervention name.
        
    Returns:
        str: The cleaned drug name.
    """
    if pd.isna(drug_name):
        return ""
        
    raw_name = str(drug_name)
    
    # 1. Remove prefixes like "Comparator:", "Arm 1:", etc.
    clean = re.sub(r'^(?:comparator|arm \d+|arm|group|active|placebo|sham|standard of care|vehicle|regimen)\s*[:\-]\s*', '', raw_name, flags=re.IGNORECASE)
    
    # 2. Remove bracketed or parenthetical info
    clean = re.sub(r'\[.*?\]', '', clean)
    clean = re.sub(r'\(.*?\)', '', clean)
    
    # 3. Take the first part of a comma or semicolon separated list
    clean = clean.split(',')[0].split(';')[0].strip()
    
    # 4. Remove doses and common formulation/salt keywords
    dose_pattern = r'\b(?:\d+ ?mg|\d+ ?g|\d+ ?mcg|\d+ ?u/kg|iv|intravenous|oral|tablets?|capsules?|active drug|matching|hydrochloride|sodium|salt|ointment|gel|solution|capsule|product|treatment|arm|preceding|study|phase|forming|phosphate|besylate|acetate|fumarate|maleate|succinate|tartrate|citrate|mesylate)\b'
    clean = re.sub(dose_pattern, '', clean, flags=re.IGNORECASE).strip()
    
    # 5. Remove percentages and trailing numbers
    clean = re.sub(r'\d*\.?\d*%', '', clean).strip()
    clean = re.sub(r'\s+\d+\.?\d*$', '', clean).strip()
    
    # 6. Cleanup whitespace and non-alphanumeric edges
    clean = re.sub(r'\s+', ' ', clean).strip()
    clean = re.sub(r'^[^a-zA-Z0-9]+|[^a-zA-Z0-9]+$', '', clean).strip()
    
    # 7. Final validation
    if not clean or len(clean) < 2 or 'placebo' in clean.lower(): 
        if re.match(r'^\d+ ?mg|tablet|capsule', raw_name, re.I) or 'placebo' in raw_name.lower():
            return ""
        return raw_name.split(',')[0].strip()
        
    return clean

def categorize_termination_unified(reason):
    """
    Categorizes the termination reason by integrating audit_engine categories 
    with negation logic and expanded keywords.
    
    Args:
        reason (str): The 'why_stopped' text from AACT.
        
    Returns:
        str: A category label (e.g., 'Efficacy', 'Safety', 'Business/Strategic').
    """
    if pd.isnull(reason): 
        return 'Unknown'
    
    text = str(reason).lower()

    # 1. Define Negation Phrases
    negation_phrases = [
        'no safety concerns', 'no safety issues', 'not due to safety', 
        'benefit-risk', 'not for efficacy or safety', 'not for safety or efficacy',
        'not related to any efficacy or safety', 'not related to efficacy or safety',
        'no efficacy or safety issues', 'neither efficacy nor safety', 
        'neither safety nor efficacy', 'not due to any efficacy or safety', 
        'not due to efficacy or safety', 'not for reasons of efficacy or safety'
    ]
    negation_pattern = r'\b(?:' + '|'.join(negation_phrases) + r')\b'
    is_negated = re.search(negation_pattern, text) is not None

    # 2. Define Category Keywords
    eff_keywords = [
        'efficacy', 'futility', 'benefit', 'endpoint', 'signal', 
        'lack of effect', 'superiority', 'insufficient signal'
    ]
    
    safe_keywords = [
        'toxic', 'adverse event', 'safety', 'harm', 'risk', 
        'side effect', 'death', 'mortality', 'aes'
    ]
    
    log_keywords = [
        'accrual', 'recruit', 'enroll', 'slow', 'low', 'insufficient', 
        'participant', 'recruitment', 'enrollment', 'funding', 'covid', 
        'personnel', 'feasibility', 'operational'
    ]
    
    biz_keywords = [
        'business', 'strategic', 'funding', 'sponsor', 'priority', 
        'portfolio', 'commercial', 'budget'
    ]
    
    admin_keywords = [
        'administrative', 'operational', 'process', 'management'
    ]

    # 3. Application Logic (Respecting Negations)
    has_eff = any(kw in text for kw in eff_keywords)
    has_safe = any(kw in text for kw in safe_keywords)
    
    # Flags are only True if terms are present AND not negated
    eff_flag = has_eff and not is_negated
    safe_flag = has_safe and not is_negated

    # 4. Classification Hierarchy
    if safe_flag:
        return 'Safety'
    if eff_flag:
        return 'Efficacy'
    if any(kw in text for kw in biz_keywords):
        return 'Business/Strategic'
    if any(kw in text for kw in admin_keywords):
        return 'Administrative'
    if any(kw in text for kw in log_keywords):
        return 'Accrual/Logistics'
    
    if is_negated:
        return 'Business/Strategic'
        
    return 'Other/Unspecified'
