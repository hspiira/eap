"""The seeded alias set, and what is deliberately missing from it.

Nine of the 51 normalised keys in the reference extract carry no alias. Each
exclusion is a decision, not an oversight, so they are pinned here: a later
change that quietly maps one should fail this file.
"""

import importlib.util
from pathlib import Path

import pytest

from app.application.services.diagnosis_seed_data import TAXONOMY
from app.domain.services.diagnosis_alias import normalise_diagnosis_value

_MIGRATION = (
    Path(__file__).resolve().parents[3]
    / "alembic"
    / "versions"
    / "e9f2a5b8c1d4_seed_diagnosis_aliases.py"
)


def _aliases():
    spec = importlib.util.spec_from_file_location("_alias_seed", _MIGRATION)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module._ALIASES


TYPE_CODES = {t[0] for t in TAXONOMY}
DIAGNOSIS_OWNER = {d[0]: t[0] for t in TAXONOMY for d in t[2]}


def test_every_alias_targets_a_real_type():
    for raw, type_code, _ in _aliases():
        assert type_code in TYPE_CODES, raw


def test_every_leaf_belongs_to_the_type_it_is_filed_under():
    for raw, type_code, diagnosis_code in _aliases():
        if diagnosis_code is None:
            continue
        assert DIAGNOSIS_OWNER.get(diagnosis_code) == type_code, raw


def test_normalised_keys_are_unique():
    keys = [normalise_diagnosis_value(raw) for raw, _, _ in _aliases()]
    assert len(keys) == len(set(keys))


def test_no_alias_key_is_empty():
    for raw, _, _ in _aliases():
        assert normalise_diagnosis_value(raw) != "", raw


@pytest.mark.parametrize(
    ("raw", "why"),
    [
        ("No show", "a scheduling outcome, SessionStatus covers it"),
        ("Coaching & Mentorship", "an intervention, belongs in the service catalogue"),
        ("Other", "unsettled, question 5"),
        ("Personality", "source classification unconfirmed, question 4"),
        ("Change Magement Risks", "source classification unconfirmed, question 4"),
        ("Family Stress, fatigue, Burnout", "source classification unconfirmed, question 4"),
        (
            "The client presented with heavy grief/ sadness and loss of meaning in life",
            "clinical narrative, belongs in issue_topic",
        ),
    ],
)
def test_excluded_values_have_no_alias(raw, why):
    keys = {normalise_diagnosis_value(r) for r, _, _ in _aliases()}
    assert normalise_diagnosis_value(raw) not in keys, why


def test_the_corrected_entry_maps_where_the_clinical_owner_said():
    """The extract files this under Mental Ill Health; it is a promotion."""
    entry = next(a for a in _aliases() if a[0] == "Nurturing mental wellness in the workplace")
    assert entry[1] == "HEALTH_PROMOTION"


def test_emotional_challenges_folds_into_a_type_rather_than_gaining_a_leaf():
    entry = next(a for a in _aliases() if a[0] == "Emotional_challenges")
    assert entry == ("Emotional_challenges", "MENTAL_ILL_HEALTH", None)
