"""EAPProgramme + Authorization aggregate tests."""

from datetime import UTC, date, datetime, timedelta

from app.shared.utils.datetime import utc_now

import pytest

from app.domain.entities.authorization import Authorization
from app.domain.entities.eap_programme import EAPProgramme
from app.domain.enums import (
    AuthorizationStatus,
    RelationType,
    ServiceCategory,
)
from app.domain.events import (
    AuthorizationConsumed,
    AuthorizationExtended,
    AuthorizationExtensionRequested,
    AuthorizationGranted,
    EAPProgrammeCreated,
)
from app.domain.exceptions import DomainError, InvalidStateError
from app.domain.value_objects.core import (
    AuthorizationId,
    CaseId,
    ClinicalSubjectId,
    ContractId,
    EAPProgrammeId,
    TenantId,
    UserId,
)
from app.domain.value_objects.programme import ProgrammeSessionCap


def _cap(
    cat: ServiceCategory = ServiceCategory.SHORT_TERM_COUNSELLING,
    *,
    per_issue: int = 6,
    per_year: int | None = 12,
) -> ProgrammeSessionCap:
    return ProgrammeSessionCap(
        service_category=cat,
        per_issue_per_year=per_issue,
        per_year=per_year,
    )


def _programme(*, caps: tuple[ProgrammeSessionCap, ...] | None = None) -> EAPProgramme:
    now = datetime.now(UTC)
    return EAPProgramme(
        id=EAPProgrammeId("prog-1"),
        tenant_id=TenantId("t-1"),
        contract_id=ContractId("contract-1"),
        name="ABSA EAP 2026",
        effective_from=date(2026, 1, 1),
        caps=caps or (_cap(),),
        eligible_dependent_relations=(RelationType.SPOUSE, RelationType.CHILD),
        created_at=now,
        updated_at=now,
    )


class TestProgrammeSessionCap:
    def test_negative_per_issue_rejected(self):
        with pytest.raises(DomainError):
            ProgrammeSessionCap(
                service_category=ServiceCategory.SHORT_TERM_COUNSELLING,
                per_issue_per_year=-1,
            )

    def test_per_year_must_not_be_below_per_issue(self):
        with pytest.raises(DomainError):
            ProgrammeSessionCap(
                service_category=ServiceCategory.SHORT_TERM_COUNSELLING,
                per_issue_per_year=8,
                per_year=4,
            )

    def test_per_household_must_not_be_below_per_year(self):
        with pytest.raises(DomainError):
            ProgrammeSessionCap(
                service_category=ServiceCategory.SHORT_TERM_COUNSELLING,
                per_issue_per_year=4,
                per_year=12,
                per_household_per_year=10,
            )


class TestEAPProgrammeInvariants:
    def test_creation_emits_event(self):
        p = _programme()
        assert any(isinstance(e, EAPProgrammeCreated) for e in p.events)

    def test_name_required(self):
        now = datetime.now(UTC)
        with pytest.raises(DomainError):
            EAPProgramme(
                id=EAPProgrammeId("p-x"),
                tenant_id=TenantId("t-1"),
                contract_id=ContractId("c-1"),
                name="",
                effective_from=date(2026, 1, 1),
                caps=(_cap(),),
                eligible_dependent_relations=(),
                created_at=now,
                updated_at=now,
            )

    def test_at_least_one_cap(self):
        now = datetime.now(UTC)
        with pytest.raises(DomainError):
            EAPProgramme(
                id=EAPProgrammeId("p-x"),
                tenant_id=TenantId("t-1"),
                contract_id=ContractId("c-1"),
                name="x",
                effective_from=date(2026, 1, 1),
                caps=(),
                eligible_dependent_relations=(),
                created_at=now,
                updated_at=now,
            )

    def test_duplicate_cap_categories_rejected(self):
        now = datetime.now(UTC)
        with pytest.raises(DomainError, match="Duplicate cap"):
            EAPProgramme(
                id=EAPProgrammeId("p-x"),
                tenant_id=TenantId("t-1"),
                contract_id=ContractId("c-1"),
                name="x",
                effective_from=date(2026, 1, 1),
                caps=(_cap(), _cap()),
                eligible_dependent_relations=(),
                created_at=now,
                updated_at=now,
            )

    def test_cap_for_lookup(self):
        p = _programme(caps=(_cap(), _cap(ServiceCategory.SUBSTANCE_USE, per_issue=4)))
        assert (
            p.cap_for(ServiceCategory.SHORT_TERM_COUNSELLING).per_issue_per_year
            == 6
        )
        assert p.cap_for(ServiceCategory.WELLNESS_COACHING) is None


def _authorization(
    *,
    granted: int = 6,
    used: int = 0,
    status: AuthorizationStatus = AuthorizationStatus.ACTIVE,
    expires_on: date | None = None,
) -> Authorization:
    now = datetime.now(UTC)
    return Authorization(
        id=AuthorizationId("auth-1"),
        tenant_id=TenantId("t-1"),
        case_id=CaseId("case-1"),
        clinical_subject_id=ClinicalSubjectId("cs_aaaaaaaa11111111"),
        programme_id=EAPProgrammeId("prog-1"),
        service_category=ServiceCategory.SHORT_TERM_COUNSELLING,
        sessions_granted=granted,
        sessions_used=used,
        status=status,
        granted_at=now,
        expires_on=expires_on,
        created_at=now,
        updated_at=now,
    )


class TestAuthorizationInvariants:
    def test_grant_event_on_creation(self):
        a = _authorization()
        assert any(isinstance(e, AuthorizationGranted) for e in a.events)

    def test_used_cannot_exceed_granted(self):
        with pytest.raises(DomainError):
            _authorization(granted=2, used=4)

    def test_sessions_remaining(self):
        assert _authorization(granted=6, used=2).sessions_remaining == 4
        assert _authorization(granted=6, used=6).sessions_remaining == 0


class TestAuthorizationConsume:
    def test_consume_decrements_and_emits(self):
        a = _authorization()
        a.events.clear()
        a.consume_session()
        assert a.sessions_used == 1
        assert any(isinstance(e, AuthorizationConsumed) for e in a.events)

    def test_consume_to_exhaust_sets_status(self):
        a = _authorization(granted=2, used=1)
        a.consume_session()
        assert a.status == AuthorizationStatus.EXHAUSTED

    def test_consume_when_exhausted_raises(self):
        a = _authorization(granted=1, used=1, status=AuthorizationStatus.EXHAUSTED)
        with pytest.raises(InvalidStateError):
            a.consume_session()

    def test_expired_authorization_rejects_consume(self):
        a = _authorization(expires_on=utc_now().date() - timedelta(days=1))
        with pytest.raises(InvalidStateError, match="expired"):
            a.consume_session()
        assert a.status == AuthorizationStatus.EXPIRED


class TestAuthorizationExtension:
    def test_request_then_grant(self):
        a = _authorization(granted=6, used=6, status=AuthorizationStatus.EXHAUSTED)
        a.events.clear()
        a.request_extension(
            additional_sessions=4, requested_by=UserId("clin-1")
        )
        assert a.status == AuthorizationStatus.EXTENSION_REQUESTED
        assert any(
            isinstance(e, AuthorizationExtensionRequested) for e in a.events
        )
        a.grant_extension(
            clinician_signoff=UserId("clin-1"),
            admin_signoff=UserId("admin-1"),
        )
        assert a.sessions_granted == 10
        assert a.status == AuthorizationStatus.EXTENDED
        assert a.extended_at is not None
        assert any(isinstance(e, AuthorizationExtended) for e in a.events)

    def test_request_zero_sessions_rejected(self):
        a = _authorization()
        with pytest.raises(DomainError, match="positive"):
            a.request_extension(
                additional_sessions=0, requested_by=UserId("clin-1")
            )

    def test_grant_without_request_blocked(self):
        a = _authorization()
        with pytest.raises(InvalidStateError):
            a.grant_extension(
                clinician_signoff=UserId("clin-1"),
                admin_signoff=UserId("admin-1"),
            )


class TestAuthorizationClose:
    def test_close_idempotent(self):
        a = _authorization()
        a.close()
        first = a.closed_at
        a.close()
        assert a.closed_at == first
        assert a.status == AuthorizationStatus.CLOSED
