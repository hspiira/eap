"""A session is attributed to a client, and may have no member.

Company-wide sessions, health talks and site visits, are delivered to a client
with nobody individual to name. The source extract holds 642 of them. Until
now `member_id` was required, so they could not be recorded at all.

`attendance` states which kind a session is rather than leaving it to be
inferred from a null member. The extract also holds 569 rows marked Staff or
Dependant with no member id: unresolved identities, which must stay staged and
must never be storable as a session that looks deliberately member-less.
"""

from datetime import UTC, datetime

import pytest

from app.domain.entities.service_session import ServiceSessionEntity
from app.domain.enums import SessionAttendance, SessionStatus
from app.domain.exceptions import DomainError
from app.domain.value_objects.core import (
    ClientId,
    EligibleMemberId,
    ProviderId,
    ServiceId,
    SessionId,
    TenantId,
)

NOW = datetime(2026, 1, 5, 9, 0, tzinfo=UTC)


def session(**changes) -> ServiceSessionEntity:
    return ServiceSessionEntity(
        **{
            "id": SessionId("s-1"),
            "tenant_id": TenantId("t-1"),
            "service_id": ServiceId("svc-1"),
            "provider_id": ProviderId("prv-1"),
            "client_id": ClientId("cli-1"),
            "member_id": EligibleMemberId("mem-1"),
            "scheduled_at": NOW,
            "status": SessionStatus.SCHEDULED,
            "created_at": NOW,
            "updated_at": NOW,
            "reschedule_count": 0,
            **changes,
        }
    )


class TestCompanyWideSessions:
    def test_a_health_talk_is_recorded_against_the_client_with_no_member(self):
        talk = session(
            attendance=SessionAttendance.COMPANY_WIDE,
            member_id=None,
            headcount=42,
        )

        assert talk.client_id == ClientId("cli-1")
        assert talk.member_id is None
        assert talk.headcount == 42

    def test_a_company_wide_session_cannot_also_name_a_member(self):
        """The two states must stay distinguishable, so this is not a warning."""
        with pytest.raises(DomainError, match="cannot name a member"):
            session(attendance=SessionAttendance.COMPANY_WIDE)


class TestIndividualSessions:
    def test_an_individual_session_still_requires_its_member(self):
        with pytest.raises(DomainError, match="requires a member"):
            session(member_id=None)

    def test_individual_is_the_default_so_existing_callers_are_unaffected(self):
        assert session().attendance is SessionAttendance.INDIVIDUAL

    def test_a_session_always_carries_its_client(self):
        """Company is a primary reporting dimension; it is not optional."""
        assert session().client_id == ClientId("cli-1")
