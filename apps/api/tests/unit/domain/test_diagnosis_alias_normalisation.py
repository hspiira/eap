"""Normalisation cases taken from the reference extract, not invented.

Measured against the supplied services.csv: 53 distinct raw values normalise to
51 keys, with two genuine merges and no case where two spellings that collapse
were classified differently.
"""

import pytest

from app.domain.services.diagnosis_alias import normalise_diagnosis_value as norm


@pytest.mark.parametrize(
    ("spellings", "expected"),
    [
        (["Loss & Grief", "Loss___Grief"], "loss grief"),
        (
            ["Work Stress, Fatigue, Burnout", "Work_Stress_Fatigue_Burnout"],
            "work stress fatigue burnout",
        ),
    ],
)
def test_real_variants_collapse(spellings, expected):
    assert {norm(s) for s in spellings} == {expected}


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("Family___Relationship", "family relationship"),
        ("Family &  Relationship", "family relationship"),
        ("Sexual Abuse ", "sexual abuse"),
        ("Health_Promotion", "health promotion"),
        ("Physical_fitness", "physical fitness"),
        ("Gender_Based_Violence", "gender based violence"),
        ("SUD", "sud"),
    ],
)
def test_source_spellings_normalise(raw, expected):
    assert norm(raw) == expected


def test_distinct_concepts_do_not_merge():
    """Two source values that mean different things must not share a key."""
    assert norm("Family &  Relationship discord") != norm("Family___Relationship")
    assert norm("ADHD Assessment") != norm("ADHD Coaching")


def test_an_empty_or_punctuation_only_value_normalises_to_empty():
    for raw in ("", "   ", "---", "&&"):
        assert norm(raw) == ""
