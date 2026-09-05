from datetime import UTC, datetime

import pytest

from app.domain.entities.member_next_of_kin import MemberNextOfKin
from app.domain.enums import NextOfKinRelationship
from app.domain.exceptions import DomainError
from app.domain.value_objects.core import EligibleMemberId, Email, MemberNextOfKinId, TenantId


def make_contact(*, phone: str | None = "+256700000000") -> MemberNextOfKin:
    now = datetime.now(UTC)
    return MemberNextOfKin(
        id=MemberNextOfKinId("nok-1"),
        tenant_id=TenantId("tenant-1"),
        member_id=EligibleMemberId("member-1"),
        name="Jane Doe",
        relationship=NextOfKinRelationship.SPOUSE,
        phone=phone,
        email=None,
        is_primary=False,
        created_at=now,
        updated_at=now,
    )


def test_next_of_kin_requires_phone_or_email():
    with pytest.raises(DomainError, match="phone or email"):
        make_contact(phone=None)


def test_next_of_kin_update_keeps_contact_invariant():
    contact = make_contact()
    updated_at = datetime.now(UTC)

    contact.update(
        name="Jane Updated",
        relationship=NextOfKinRelationship.GUARDIAN,
        phone=None,
        email=Email("jane@example.com"),
        is_primary=True,
        now=updated_at,
    )

    assert contact.name == "Jane Updated"
    assert contact.relationship == NextOfKinRelationship.GUARDIAN
    assert contact.email == Email("jane@example.com")
    assert contact.is_primary is True
    assert contact.updated_at == updated_at
