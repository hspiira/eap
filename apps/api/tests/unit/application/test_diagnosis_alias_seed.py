"""The seeded alias set, and what is deliberately missing from it.

Two migrations load aliases: the confirmed set the clinical owner signed off,
and the inferred set covering the four values question 4 left open. The
inferred rows are importable but filterable, so a reviewer can find and correct
exactly them.

Five keys still carry no alias. Each exclusion is a decision, not an oversight,
so they are pinned here: a later change that quietly maps one should fail this
file.
"""

import importlib.util
from pathlib import Path

import pytest

from app.application.services.diagnosis_seed_data import TAXONOMY
from app.domain.services.diagnosis_alias import normalise_diagnosis_value

_VERSIONS = Path(__file__).resolve().parents[3] / "alembic" / "versions"
_CONFIRMED = _VERSIONS / "e9f2a5b8c1d4_seed_diagnosis_aliases.py"
_INFERRED = _VERSIONS / "c1e4a7b9d2f6_load_inferred_diagnosis_aliases.py"


def _load(path: Path):
    spec = importlib.util.spec_from_file_location(f"_alias_seed_{path.stem}", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module._ALIASES


def _confirmed_aliases():
    return _load(_CONFIRMED)


def _inferred_aliases():
    return _load(_INFERRED)


def _aliases():
    """Every alias that lands, from either migration."""
    return _confirmed_aliases() + _inferred_aliases()


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
        (
            "The client presented with heavy grief/ sadness and loss of meaning in life",
            "clinical narrative, belongs in issue_topic",
        ),
    ],
)
def test_excluded_values_have_no_alias(raw, why):
    keys = {normalise_diagnosis_value(r) for r, _, _ in _aliases()}
    assert normalise_diagnosis_value(raw) not in keys, why


@pytest.mark.parametrize(
    "raw",
    [
        "Personality",
        "Change Magement Risks",
        "Family Stress, fatigue, Burnout",
        "The client presented with symptoms of depression and fear about living without any parent",
    ],
)
def test_question_four_values_load_as_inferred_not_confirmed(raw):
    """Importable, so the legacy rows land, but flagged for review.

    Loading these as 'confirmed' would launder a guess into a signed-off fact,
    which is exactly what the confidence column exists to prevent.
    """
    key = normalise_diagnosis_value(raw)
    assert key in {normalise_diagnosis_value(r) for r, _, _ in _inferred_aliases()}
    assert key not in {normalise_diagnosis_value(r) for r, _, _ in _confirmed_aliases()}


def test_the_two_alias_migrations_do_not_overlap():
    confirmed = {normalise_diagnosis_value(r) for r, _, _ in _confirmed_aliases()}
    inferred = {normalise_diagnosis_value(r) for r, _, _ in _inferred_aliases()}
    assert confirmed & inferred == set()


def test_the_inferred_migration_declares_its_confidence():
    """The rows must not be written as 'confirmed' by a later careless edit."""
    source = _INFERRED.read_text()
    assert '"confidence": "inferred"' in source
    assert '"confidence": "confirmed"' not in source


def test_the_corrected_entry_maps_where_the_clinical_owner_said():
    """The extract files this under Mental Ill Health; it is a promotion."""
    entry = next(a for a in _aliases() if a[0] == "Nurturing mental wellness in the workplace")
    assert entry[1] == "HEALTH_PROMOTION"


def test_emotional_challenges_folds_into_a_type_rather_than_gaining_a_leaf():
    entry = next(a for a in _aliases() if a[0] == "Emotional_challenges")
    assert entry == ("Emotional_challenges", "MENTAL_ILL_HEALTH", None)
