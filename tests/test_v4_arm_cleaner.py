import pytest
import pandas as pd
from src.data.v4_arm_cleaner import v4_arm_cleaner

@pytest.mark.parametrize("design, results, expected", [
    ("vandetanib 300mg", "vandetanib 300 mg", "vandetanib 300 mg"),
    ("arm 1: dasatinib", "dasatinib cohort", "dasatinib"),
    ("lurasidone 80 mg tablet", "lurasidone 80 mg", "lurasidone 80 mg"),
    ("treatment (bintrafusp alfa)", "arm a: bintrafusp alfa", "bintrafusp alfa"),
    ("oros mph", "oros-methylphenidate", "oros methylphenidate"),
    ("tapentadol", "tapentadol pr", "tapentadol prolonged release"),
])
def test_v4_arm_cleaner_equality(design, results, expected):
    """Verify that both Design and Results titles normalize to the exact same expected string."""
    assert v4_arm_cleaner(design) == expected
    assert v4_arm_cleaner(results) == expected

def test_collision_guard_decimal():
    """Ensure decimals are preserved and not merged."""
    assert v4_arm_cleaner("Drug 0.5 mg") == "drug 0.5 mg"
    assert v4_arm_cleaner("Drug .5 mg") == "drug 0.5 mg" # Wait, my regex might not handle leading dot
    # Actually, current regex: r'(?<!\d)\.|\.(?!\d)'
    # For '.5', the dot is NOT preceded by a digit, so it matches the first part and is replaced by space.
    # So '.5' becomes ' 5'. This is a known issue I should check.

def test_unit_anchors():
    """Ensure units are properly spaced but numbers are preserved."""
    assert v4_arm_cleaner("100mg") == "100 mg"
    assert v4_arm_cleaner("100 mg") == "100 mg"

def test_synonym_expansion():
    """Ensure abbreviations are expanded correctly with word boundaries."""
    assert v4_arm_cleaner("pregabalin pr") == "pregabalin prolonged release"
    assert v4_arm_cleaner("pregabalin") == "pregabalin"
    # Collision check: 'pregabalin' should NOT contain 'prolonged release'
    assert "prolonged release" not in v4_arm_cleaner("pregabalin")
