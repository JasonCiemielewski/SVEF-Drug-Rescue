import pytest
import pandas as pd
import os
import sys

# Ensure the src directory is in the path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.audit.audit_engine import categorize_termination, classify_molecule

def test_categorize_termination():
    """Test categorization of termination reasons."""
    assert categorize_termination("Trial stopped due to lack of efficacy") == "Efficacy"
    assert categorize_termination("Safety concerns: severe adverse events") == "Safety"
    assert categorize_termination("Slow accrual and recruitment issues") == "Accrual/Logistics"
    assert categorize_termination("Business decision to discontinue funding") == "Business/Strategic"
    assert categorize_termination("Administrative management reasons") == "Administrative"
    assert categorize_termination("Unknown reason") == "Other/Unspecified"
    assert categorize_termination(None) == "Unknown"

def test_classify_molecule():
    """Test intervention molecule classification."""
    # Test Small Molecule
    row_sm = {'name': 'Aspirin', 'description': 'Pain reliever', 'intervention_type': 'Drug'}
    assert classify_molecule(row_sm) == "Small_Molecule"
    
    # Test Biologic (mab suffix)
    row_bio = {'name': 'Rituximab', 'description': 'Monoclonal antibody', 'intervention_type': 'Drug'}
    assert classify_molecule(row_bio) == "Biologic"
    
    # Test Biologic (description keyword)
    row_bio2 = {'name': 'Drug X', 'description': 'Recombinant protein', 'intervention_type': 'Drug'}
    assert classify_molecule(row_bio2) == "Biologic"
    
    # Test Other (not a Drug)
    row_other = {'name': 'Surgery', 'description': 'Knee replacement', 'intervention_type': 'Procedure'}
    assert classify_molecule(row_other) == "Other"
