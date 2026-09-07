"""The dev seed must satisfy the enum-backed columns it writes to.

`data/seed_data.json` shipped ten `services` rows carrying categories that were
never `ServiceCategory` values: Counseling, Workshop, Crisis, Referral,
Training, Assessment, Webinar. `EnumValueType` raises on the way in and the
`service_category_check` constraint refuses them at the database, so
`scripts/load_seed_data.py` failed on the services table against any schema at
head. Typing the column in migration a5b8c1d4e7f0 is what made the seed
invalid, and nothing caught it.

These assert the seed against the enums rather than against a snapshot, so
adding a row with a made-up value fails here rather than at load time.
"""

import json
from pathlib import Path

import pytest

from app.domain.enums import BaseStatus, ServiceCategory

SEED = Path(__file__).resolve().parents[3] / "data/seed_data.json"


@pytest.fixture(scope="module")
def seed() -> dict:
    return json.loads(SEED.read_text())


def test_the_seed_file_is_where_the_loader_expects_it(seed):
    assert seed["services"], "no services to check; the loader reads this key"


def test_every_seeded_service_category_is_a_service_category(seed):
    valid = {e.value for e in ServiceCategory}
    offenders = [
        (s["id"], s["category"])
        for s in seed["services"]
        if s["category"] is not None and s["category"] not in valid
    ]
    assert offenders == [], f"not ServiceCategory values: {offenders}"


def test_every_seeded_service_status_is_a_base_status(seed):
    valid = {e.value for e in BaseStatus}
    offenders = [(s["id"], s["status"]) for s in seed["services"] if s["status"] not in valid]
    assert offenders == [], f"not BaseStatus values: {offenders}"


def test_a_null_category_is_allowed(seed):
    """The column is nullable: a company-wide service draws down nothing.

    See TAXONOMY_FINDINGS.md item 4. Requiring a category here would push the
    seed back into inventing one.
    """
    assert any(s["category"] is None for s in seed["services"])


def test_the_seed_exercises_more_than_one_category(seed):
    """A seed that only ever used one value would not catch a mapping error."""
    used = {s["category"] for s in seed["services"] if s["category"]}
    assert len(used) >= 2, f"only {used} exercised"
