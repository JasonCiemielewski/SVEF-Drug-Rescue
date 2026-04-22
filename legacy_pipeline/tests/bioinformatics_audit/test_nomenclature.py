import pytest
from src.features.enrich_dataset import clean_drug_name

def test_nomenclature_aggressive_stripping():
    """Verify that complex dosage and bracketed names are cleaned via production logic."""
    assert clean_drug_name("Dasatinib 100 MG [Sprycel]") == "Dasatinib"
    assert clean_drug_name("Antroquinonol Capsule 50mg") == "Antroquinonol"
    assert clean_drug_name("Nilotinib 150mg oral capsule [Tasigna]") == "Nilotinib"
    assert clean_drug_name("Timolol 0.5% Gel Forming Solution (GFS)") == "Timolol" 

def test_nomenclature_salt_stripping():
    """Verify that salt forms are stripped via production logic."""
    assert clean_drug_name("gemcitabine hydrochloride") == "gemcitabine"
    assert clean_drug_name("Dexamethasone Sodium Phosphate") == "Dexamethasone"
    assert clean_drug_name("Amlodipine Besylate") == "Amlodipine"

def test_combination_logic_direct():
    """Verify how multi-drug strings are cleaned."""
    def simulate_tier_split(name):
        clean = clean_drug_name(name)
        for sep in ['+', '/', ' and ', ' with ']:
            if sep in clean.lower():
                clean = clean.lower().split(sep)[0].strip()
                break
        return clean

    assert simulate_tier_split("Metformin + Sitagliptin") == "metformin"
    assert simulate_tier_split("Aspirin/Dipyridamole") == "aspirin"

def test_classify_failure():
    """Verify categorization of match failures."""
    from src.features.enrich_dataset import classify_failure
    
    assert classify_failure("Placebo oral capsule") == "PLACEBO_EQUIVALENT"
    assert classify_failure("Sham Comparator") == "PLACEBO_EQUIVALENT"
    assert classify_failure("Standard Treatment") == "LOGISTICAL_GENERIC"
    assert classify_failure("Metformin therapy") == "LOGISTICAL_GENERIC"
    assert classify_failure("AZD-1234") == "POSSIBLE_INTERNAL_PROPRIETARY"
    assert classify_failure("RO6811135") == "POSSIBLE_INTERNAL_PROPRIETARY"
    assert classify_failure("MCI-186 100mg") == "POSSIBLE_INTERNAL_PROPRIETARY"
