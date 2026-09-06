"""EligibleMember + ClinicalSubject + pseudonymisation tests."""

from datetime import UTC, date, datetime, timedelta

import pytest

from app.domain.entities.clinical_subject import ClinicalSubject
from app.domain.entities.eligible_member import EligibleMember
from app.domain.enums import EligibilityStatus, MemberRelation
from app.domain.exceptions import DomainError, InvalidStateError
from app.domain.services.pseudonymisation import generate_pseudonym
from app.domain.value_objects.core import (
    ClientId,
    ClinicalSubjectId,
    EligibleMemberId,
    TenantId,
    UserId,
)
from app.shared.utils.datetime import utc_now


def _member(
    *,
    relation: MemberRelation = MemberRelation.EMPLOYEE,
    status: EligibilityStatus = EligibilityStatus.ACTIVE,
    primary: EligibleMemberId | None = None,
) -> EligibleMember:
    now = datetime.now(UTC)
    return EligibleMember(
        id=EligibleMemberId("em-1"),
        tenant_id=TenantId("t-1"),
        client_id=ClientId("client-1"),
        employer_member_id="HR-12345",
        relation=relation,
        status=status,
        primary_employee_member_id=primary,
        created_at=now,
        updated_at=now,
    )


class TestEligibleMemberInvariants:
    def test_employer_member_id_required(self):
        now = datetime.now(UTC)
        with pytest.raises(DomainError, match="employer_member_id"):
            EligibleMember(
                id=EligibleMemberId("em-x"),
                tenant_id=TenantId("t-1"),
                client_id=ClientId("c-1"),
                employer_member_id="",
                relation=MemberRelation.EMPLOYEE,
                status=EligibilityStatus.ACTIVE,
                created_at=now,
                updated_at=now,
            )

    def test_dependent_requires_primary(self):
        with pytest.raises(DomainError, match="primary_employee_member_id"):
            _member(relation=MemberRelation.SPOUSE)

    def test_coverage_window_invariant(self):
        now = datetime.now(UTC)
        with pytest.raises(DomainError, match="coverage_end"):
            EligibleMember(
                id=EligibleMemberId("em-x"),
                tenant_id=TenantId("t-1"),
                client_id=ClientId("c-1"),
                employer_member_id="HR-2",
                relation=MemberRelation.EMPLOYEE,
                status=EligibilityStatus.ACTIVE,
                coverage_start=date(2026, 6, 1),
                coverage_end=date(2026, 5, 1),
                created_at=now,
                updated_at=now,
            )


class TestEligibleMemberFSM:
    def test_account_link_requires_unlink_before_replacement(self):
        member = _member()
        member.link_account(UserId("user-1"))
        member.link_account(UserId("user-1"))
        with pytest.raises(InvalidStateError, match="already has"):
            member.link_account(UserId("user-2"))
        member.unlink_account()
        assert member.user_id is None

    def test_suspend_then_reinstate(self):
        m = _member()
        m.suspend()
        assert m.status == EligibilityStatus.SUSPENDED
        m.reinstate()
        assert m.status == EligibilityStatus.ACTIVE
        assert m.suspended_at is None

    def test_cannot_suspend_terminated(self):
        m = _member(status=EligibilityStatus.TERMINATED)
        with pytest.raises(InvalidStateError):
            m.suspend()

    def test_cannot_reinstate_terminated(self):
        m = _member(status=EligibilityStatus.TERMINATED)
        with pytest.raises(InvalidStateError):
            m.reinstate()

    def test_terminate_sets_coverage_end(self):
        m = _member()
        m.terminate(end_date=date(2026, 5, 8))
        assert m.status == EligibilityStatus.TERMINATED
        assert m.coverage_end == date(2026, 5, 8)

    def test_is_currently_eligible_respects_window(self):
        m = _member()
        m.coverage_start = utc_now().date() + timedelta(days=10)
        assert m.is_currently_eligible() is False
        m.coverage_start = utc_now().date() - timedelta(days=10)
        m.coverage_end = utc_now().date() - timedelta(days=1)
        assert m.is_currently_eligible() is False
        m.coverage_end = utc_now().date() + timedelta(days=1)
        assert m.is_currently_eligible() is True

    def test_roster_update_can_clear_optional_values(self):
        m = _member()
        m.coverage_start = date(2026, 1, 1)
        m.coverage_end = date(2026, 12, 31)
        m.display_label = "Former label"
        m.update_roster_details(
            employer_member_id="HR-987",
            relation=MemberRelation.EMPLOYEE,
            primary_employee_member_id=None,
            coverage_start=None,
            coverage_end=None,
            work_email=None,
            personal_email=None,
            display_label=None,
        )
        assert m.employer_member_id == "HR-987"
        assert m.coverage_start is None
        assert m.coverage_end is None
        assert m.display_label is None

    def test_roster_update_preserves_relationship_invariants(self):
        m = _member()
        with pytest.raises(DomainError, match="primary_employee_member_id"):
            m.update_roster_details(
                employer_member_id="HR-12345",
                relation=MemberRelation.SPOUSE,
                primary_employee_member_id=None,
            )


class TestClinicalSubject:
    def test_pseudonym_required(self):
        now = datetime.now(UTC)
        with pytest.raises(DomainError, match="pseudonym"):
            ClinicalSubject(
                id=ClinicalSubjectId("cs-x"),
                tenant_id=TenantId("t-1"),
                pseudonym="",
                created_at=now,
                updated_at=now,
            )

    def test_pseudonym_min_length(self):
        now = datetime.now(UTC)
        with pytest.raises(DomainError, match="8 characters"):
            ClinicalSubject(
                id=ClinicalSubjectId("cs-x"),
                tenant_id=TenantId("t-1"),
                pseudonym="short",
                created_at=now,
                updated_at=now,
            )

    def test_continuity_metadata_update(self):
        now = datetime.now(UTC)
        s = ClinicalSubject(
            id=ClinicalSubjectId("cs-1"),
            tenant_id=TenantId("t-1"),
            pseudonym="cs_abcdef1234567890",
            created_at=now,
            updated_at=now,
        )
        s.update_continuity_metadata(preferred_language="en", preferred_pronouns="they/them")
        assert s.preferred_language == "en"
        assert s.preferred_pronouns == "they/them"

    def test_deactivate_idempotent(self):
        now = datetime.now(UTC)
        s = ClinicalSubject(
            id=ClinicalSubjectId("cs-1"),
            tenant_id=TenantId("t-1"),
            pseudonym="cs_abcdef1234567890",
            created_at=now,
            updated_at=now,
        )
        s.deactivate()
        first = s.deactivated_at
        s.deactivate()
        assert s.deactivated_at == first


class TestPseudonymisation:
    def test_pseudonym_is_opaque_hex(self):
        p = generate_pseudonym(tenant_secret="this-is-a-strong-secret-with-length")
        assert p.startswith("cs_")
        assert len(p) == 19

    def test_seed_makes_pseudonym_deterministic(self):
        p1 = generate_pseudonym(tenant_secret="this-is-a-strong-secret-with-length", seed="abc")
        p2 = generate_pseudonym(tenant_secret="this-is-a-strong-secret-with-length", seed="abc")
        assert p1 == p2

    def test_different_secrets_yield_different_pseudonyms(self):
        p1 = generate_pseudonym(tenant_secret="secret-one-of-ample-length", seed="x")
        p2 = generate_pseudonym(tenant_secret="secret-two-of-ample-length", seed="x")
        assert p1 != p2

    def test_short_secret_rejected(self):
        with pytest.raises(ValueError, match="16 characters"):
            generate_pseudonym(tenant_secret="short")
