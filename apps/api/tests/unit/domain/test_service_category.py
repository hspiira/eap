"""The service catalogue category is a service_categories code, not a fixed enum.

Guards the gap recorded in apps/api/docs/SERVICES_MODULE.md section 3.6: the
programme caps and authorizations gate on this code, so the catalogue has to
speak the same vocabulary. Unlike the ``ServiceCategory`` enum this replaces
(migration 7af2412c8b90), the valid set is a database table rather than a
Python type, so the schema layer accepts any string; an unknown code is
rejected at the route (see test_service_api.py's category-not-found case)
against the live taxonomy, not here against a fixed list.
"""

import pytest
from pydantic import ValidationError

from app.api.schemas.service_schemas import ServiceCreate, ServiceUpdate


def test_create_accepts_a_category_code():
    payload = ServiceCreate(name="Counselling", category="ShortTermCounselling")
    assert payload.category == "ShortTermCounselling"


def test_create_accepts_a_null_category():
    assert ServiceCreate(name="Counselling").category is None


def test_create_requires_a_name():
    with pytest.raises(ValidationError):
        ServiceCreate(name="", category="ShortTermCounselling")


def test_update_accepts_any_category_string():
    """Format validation moved to the route, which checks the live taxonomy."""
    assert ServiceUpdate(category="not-yet-a-real-code").category == "not-yet-a-real-code"
