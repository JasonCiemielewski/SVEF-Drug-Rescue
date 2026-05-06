import pytest
from src.features.cleaning import clean_drug_name, categorize_termination_unified

@pytest.mark.parametrize("input_name, expected", [
    ("Arm 1: Foscarnet 20mg", "Foscarnet"),
    ("Comparator: Placebo", ""),
    ("Active: Ganciclovir (IV)", "Ganciclovir"),
    ("Etoposide Hydrochloride", "Etoposide"),
    ("Cyclophosphamide [Experimental]", "Cyclophosphamide"),
    ("10% Glucose Solution", "Glucose"),
    ("Saline matching placebo", ""),
    ("Aspirin, 325 mg", "Aspirin"),
    ("Study Drug (ABC-123)", "Drug"),
])
def test_clean_drug_name(input_name, expected):
    assert clean_drug_name(input_name) == expected

@pytest.mark.parametrize("reason, expected", [
    ("Lack of efficacy", "Efficacy"),
    ("Futility based on interim analysis", "Efficacy"),
    ("Toxicities observed in cohort", "Safety"),
    ("Severe adverse events", "Safety"),
    ("Slow accrual of patients", "Accrual/Logistics"),
    ("Business decision to stop funding", "Business/Strategic"),
    ("Terminated due to COVID-19", "Accrual/Logistics"),
    ("Not for safety or efficacy reasons", "Business/Strategic"), # Negation test
    ("Neither efficacy nor safety concerns", "Business/Strategic"), # Negation test
    (None, "Unknown"),
])
def test_categorize_termination_unified(reason, expected):
    assert categorize_termination_unified(reason) == expected
