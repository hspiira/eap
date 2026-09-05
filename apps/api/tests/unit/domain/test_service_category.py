"""The service catalogue category is the ServiceCategory enum, not free text.

Guards the gap recorded in apps/api/docs/SERVICES_MODULE.md section 3.6: the
programme caps and authorizations gate on ServiceCategory, so the catalogue has
to speak the same vocabulary.
"""

import pytest
from pydantic import ValidationError

from app.api.schemas.service_schemas import ServiceCreate, ServiceUpdate
from app.domain.enums import ServiceCategory


def test_create_accepts_an_enum_value():
    payload = ServiceCreate(name="Counselling", category="ShortTermCounselling")
    assert payload.category is ServiceCategory.SHORT_TERM_COUNSELLING


def test_create_accepts_a_null_category():
    assert ServiceCreate(name="Counselling").category is None


@pytest.mark.parametrize(
    "value", ["eap", "wellness", "Short Term Counselling", "shorttermcounselling"]
)
def test_create_rejects_free_text(value):
    with pytest.raises(ValidationError):
        ServiceCreate(name="Counselling", category=value)


def test_update_rejects_free_text():
    with pytest.raises(ValidationError):
        ServiceUpdate(category="eap")


def test_every_enum_value_is_accepted():
    for member in ServiceCategory:
        assert ServiceCreate(name="s", category=member.value).category is member
