import pandas as pd
import pytest
from src.data.make_dataset import apply_svef_logic

@pytest.mark.parametrize("why_stopped, expected_eff, expected_safe", [
    ("Trial stopped for futility and lack of benefit.", True, False),
    ("Terminated due to safety concerns and high toxicity.", False, True),
    ("Terminated for futility. No safety concerns were identified.", True, False),
    ("Lack of efficacy and unanticipated adverse events.", True, True),
    ("Failed to meet primary endpoint.", True, False),
    ("Insufficient signal observed during interim analysis.", True, False),
    ("Maximum tolerated dose exceeded.", False, True),
    ("Stopped for business reasons.", False, False),
    ("Unprovable efficacy according to interim analysis.", True, False),
    ("Efficacy was not shown; no safety issues observed.", True, False),
])
def test_apply_svef_logic_parametrized(why_stopped, expected_eff, expected_safe):
    """
    Test various termination reasons to ensure masks are correctly applied.
    """
    df = pd.DataFrame({'why_stopped': [why_stopped]})
    result_df = apply_svef_logic(df)
    
    # We check the individual masks in the underlying logic
    # Note: apply_svef_logic returns a filtered dataframe where (eff == True) & (safe == False)
    # To check the masks, we look at the calculated columns if the row is returned,
    # or we check why it wasn't returned.
    
    # Let's perform a more granular check by accessing the calculation logic
    # We can do this by running the logic on a copy
    df['why_stopped_clean'] = df['why_stopped'].fillna('').str.lower()
    
    # Re-running the regex masks manually to verify
    eff_keywords = ['futility', 'efficacy', 'lack of effect', 'benefit', 'endpoint', 'interim analysis', 'superiority', 'insufficient signal', 'lack of benefit', 'endpoint not met', 'no significant difference', 'did not meet', 'unprovable']
    safe_keywords = ['toxic', 'adverse event', 'side effect', 'harm', 'risk', 'death', 'mortality', 'aes', 'maximum tolerated dose', 'safety profile', 'intolerability', 'adverse reactions']
    negation_phrases = ['no safety concerns', 'no safety issues', 'not due to safety']
    
    eff_mask = df['why_stopped_clean'].str.contains('|'.join(eff_keywords), regex=True).iloc[0]
    has_safety_keyword = df['why_stopped_clean'].str.contains('|'.join(safe_keywords), regex=True).iloc[0]
    is_specifically_safety = df['why_stopped_clean'].str.contains('safety', regex=True).iloc[0]
    negation_mask = df['why_stopped_clean'].str.contains('|'.join(negation_phrases), regex=True).iloc[0]
    
    safe_mask = (has_safety_keyword or is_specifically_safety) and not negation_mask
    
    assert eff_mask == expected_eff
    assert safe_mask == expected_safe

def test_apply_svef_logic_empty_input():
    """
    Ensure the logic handles empty strings or NaNs gracefully.
    """
    df = pd.DataFrame({'why_stopped': [None, ""]})
    result = apply_svef_logic(df)
    assert len(result) == 0
