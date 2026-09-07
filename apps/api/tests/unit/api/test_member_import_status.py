"""The imported status is applied without asking for a transition that does nothing."""

import pytest

from app.api.services.member_import import _apply_imported_status
from app.domain.entities.eligible_member import EligibleMember
from app.domain.enums import EligibilityStatus, MemberRelation
from app.domain.value_objects.core import ClientId, EligibleMemberId, TenantId
from app.shared.utils.datetime import utc_now


def member(status=EligibilityStatus.ACTIVE):
    now = utc_now()
    return EligibleMember(
        id=EligibleMemberId("m1"),
        tenant_id=TenantId("t1"),
        client_id=ClientId("c1"),
        employer_member_id="m1",
        display_label="Amina Namukasa",
        relation=MemberRelation.EMPLOYEE,
        status=status,
        created_at=now,
        updated_at=now,
    )


def test_active_source_row_leaves_a_freshly_enrolled_member_alone():
    """Enrolment already creates an Active member; reinstating one raises."""
    subject = member()
    _apply_imported_status(subject, "Active")
    assert subject.status is EligibilityStatus.ACTIVE


@pytest.mark.parametrize(
    ("source", "expected"),
    [
        ("Suspended", EligibilityStatus.SUSPENDED),
        ("terminated", EligibilityStatus.TERMINATED),
        (" Suspended ", EligibilityStatus.SUSPENDED),
    ],
)
def test_a_status_that_differs_is_reached(source, expected):
    subject = member()
    _apply_imported_status(subject, source)
    assert subject.status is expected


def test_a_suspended_row_can_still_be_reinstated():
    subject = member(EligibilityStatus.SUSPENDED)
    _apply_imported_status(subject, "Active")
    assert subject.status is EligibilityStatus.ACTIVE


@pytest.mark.parametrize("source", [None, "", "Pending", "unrecognised"])
def test_an_unrecognised_or_absent_status_changes_nothing(source):
    subject = member()
    _apply_imported_status(subject, source)
    assert subject.status is EligibilityStatus.ACTIVE
