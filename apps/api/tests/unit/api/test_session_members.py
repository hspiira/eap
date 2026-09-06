from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
import pytest_asyncio
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from app.api.dependencies import (
    get_audit_event_handler,
    get_eligible_member_repository,
    get_provider_repository,
    get_service_repository,
    get_service_session_repository,
    get_session_attribution_reader,
)
from app.api.dependencies.clinical import get_authorization_repository, get_case_repository
from app.api.dependencies.provider_network import (
    get_provider_affiliation_repository,
    get_provider_organisation_repository,
)
from app.api.routes.service_sessions import router
from app.core.authorization import get_service_session_for_current_tenant
from app.core.database import get_db
from app.core.exception_handlers import register_exception_handlers
from app.core.security import TokenData, get_current_user
from app.domain.entities.provider import ProviderEntity
from app.domain.enums import (
    AccreditationStatus,
    BaseStatus,
    PanelStatus,
    ProviderTier,
    SessionDeliveryContext,
    UgandaRegion,
)
from app.domain.enums.provider_network import OrganisationApprovalStatus
from app.domain.value_objects.core import (
    ClientId,
    EligibleMemberId,
    ProviderId,
    ProviderProfile,
    SessionId,
    TenantId,
    UserId,
)
from app.shared.utils.datetime import utc_now

_APPROVED = OrganisationApprovalStatus.APPROVED
_NOT_APPROVED = OrganisationApprovalStatus.PENDING


def _bookable_provider() -> ProviderEntity:
    """An active, accredited, on-panel practitioner: the booking gate passes."""
    now = utc_now()
    return ProviderEntity(
        id=ProviderId("p1"),
        tenant_id=TenantId("t1"),
        status=BaseStatus.ACTIVE,
        display_name="Amina Okello",
        created_at=now,
        updated_at=now,
        provider_profile=ProviderProfile(
            tier=ProviderTier.T2,
            region=UgandaRegion.CENTRAL,
            accreditation_status=AccreditationStatus.ACCREDITED,
            panel_status=PanelStatus.ACTIVE,
        ),
    )


@pytest_asyncio.fixture
async def api():
    app = FastAPI()
    app.include_router(router)
    register_exception_handlers(app)
    state = SimpleNamespace(
        members=AsyncMock(),
        providers=AsyncMock(),
        services=AsyncMock(),
        sessions=AsyncMock(),
        authorizations=AsyncMock(),
        cases=AsyncMock(),
        audit=AsyncMock(),
        db=AsyncMock(),
        user=TokenData(user_id="u1", tenant_id="t1", role="Admin"),
    )
    state.members.get_by_id.return_value = SimpleNamespace(tenant_id=TenantId("t1"))
    state.providers.get_by_id.return_value = _bookable_provider()
    state.providers.get_for_booking.return_value = _bookable_provider()
    state.affiliations = AsyncMock()
    state.organisations = AsyncMock()
    state.affiliations.get_valid_affiliation.return_value = SimpleNamespace(
        organisation_id=SimpleNamespace(value="org-1")
    )
    state.attribution = AsyncMock()
    state.attribution.organisation_ids_by_affiliation.return_value = {"aff-1": "org-1"}
    state.organisations.get_organisation.return_value = SimpleNamespace(
        is_active=True, approval_status=_APPROVED
    )
    state.services.get_by_id.return_value = SimpleNamespace(tenant_id=TenantId("t1"))
    for dep, value in {
        get_eligible_member_repository: state.members,
        get_provider_repository: state.providers,
        get_service_repository: state.services,
        get_service_session_repository: state.sessions,
        get_authorization_repository: state.authorizations,
        get_case_repository: state.cases,
        get_audit_event_handler: state.audit,
        get_provider_affiliation_repository: state.affiliations,
        get_session_attribution_reader: state.attribution,
        get_provider_organisation_repository: state.organisations,
        get_db: state.db,
    }.items():
        app.dependency_overrides[dep] = (lambda v: lambda: v)(value)
    app.dependency_overrides[get_current_user] = lambda: state.user
    state.app = app
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as http:
        state.http = http
        yield state


PAYLOAD = dict(
    member_id="m1",
    provider_id="p1",
    service_id="s1",
    scheduled_at="2026-09-10T09:00:00Z",
    delivery_context="Direct",
)


async def test_create_uses_a_member_without_a_user_account(api):
    response = await api.http.post("/service-sessions/?tenant_id=t1", json=PAYLOAD)
    assert response.status_code == 201, response.text
    assert response.json()["member_id"] == "m1"
    assert "person_id" not in response.json()
    saved = api.sessions.save.call_args.args[0]
    assert saved.member_id == EligibleMemberId("m1")
    api.db.commit.assert_awaited_once()


@pytest.mark.parametrize("resource", ["members", "services"])
async def test_rejects_foreign_tenant_references(api, resource):
    getattr(api, resource).get_by_id.return_value.tenant_id = TenantId("other")
    response = await api.http.post("/service-sessions/?tenant_id=t1", json=PAYLOAD)
    assert response.status_code == 404
    api.sessions.save.assert_not_awaited()


async def test_rejects_foreign_tenant_provider(api):
    """The provider read is tenant-scoped in SQL, so a foreign id resolves to nothing."""
    api.providers.get_for_booking.return_value = None
    response = await api.http.post("/service-sessions/?tenant_id=t1", json=PAYLOAD)
    assert response.status_code == 404
    api.sessions.save.assert_not_awaited()


async def test_rejects_booking_an_ineligible_provider(api):
    suspended = _bookable_provider()
    suspended.change_panel_status(PanelStatus.SUSPENDED, UserId("admin"), "Quality review")
    api.providers.get_for_booking.return_value = suspended
    response = await api.http.post("/service-sessions/?tenant_id=t1", json=PAYLOAD)
    assert response.status_code == 409, response.text
    body = response.json()
    assert body["error"] == "PROVIDER_NOT_ELIGIBLE"
    assert "panel_not_active" in [d["code"] for d in body["details"]]
    api.sessions.save.assert_not_awaited()


async def test_rejects_person_id_payload(api):
    response = await api.http.post(
        "/service-sessions/?tenant_id=t1",
        json={**{k: v for k, v in PAYLOAD.items() if k != "member_id"}, "person_id": "p1"},
    )
    assert response.status_code == 422
    api.sessions.save.assert_not_awaited()


async def test_viewer_cannot_create(api):
    api.user.role = "Viewer"
    response = await api.http.post("/service-sessions/?tenant_id=t1", json=PAYLOAD)
    assert response.status_code == 403
    api.sessions.save.assert_not_awaited()


# ---------------------------------------------------------------------------
# Entitlement drawdown on completion.
#
# The route has accepted case_id since drawdown landed, but no product caller
# ever sent one, so these pin the seam the frontend now drives.
# ---------------------------------------------------------------------------


def _authorization(remaining: int = 3):
    """A live authorization the drawdown selector will pick."""
    from datetime import date

    from app.domain.entities.authorization import Authorization
    from app.domain.enums import AuthorizationStatus, ServiceCategory
    from app.domain.value_objects.core import (
        AuthorizationId,
        CaseId,
        ClinicalSubjectId,
        EAPProgrammeId,
    )
    from app.shared.utils.datetime import utc_now

    now = utc_now()
    return Authorization(
        id=AuthorizationId("a1"),
        tenant_id=TenantId("t1"),
        case_id=CaseId("case-1"),
        clinical_subject_id=ClinicalSubjectId("subj-1"),
        programme_id=EAPProgrammeId("prog-1"),
        service_category=ServiceCategory.SHORT_TERM_COUNSELLING,
        sessions_granted=remaining + 1,
        sessions_used=1,
        status=AuthorizationStatus.ACTIVE,
        granted_at=now,
        expires_on=date(2999, 1, 1),
        created_at=now,
        updated_at=now,
    )


@pytest_asyncio.fixture
async def completable(api):
    """Point the session and service fixtures at a completable session."""
    from app.domain.entities.service_session import ServiceSessionEntity
    from app.domain.enums import ServiceCategory, SessionStatus
    from app.domain.value_objects.core import PersonId, ServiceId, SessionId
    from app.shared.utils.datetime import utc_now

    now = utc_now()
    # A real entity, not a stub: the route runs the domain transition, so a
    # SimpleNamespace would only prove the mock was called.
    session = ServiceSessionEntity(
        id=SessionId("ss1"),
        tenant_id=TenantId("t1"),
        service_id=ServiceId("s1"),
        provider_id=PersonId("p1"),
        member_id=EligibleMemberId("m1"),
        scheduled_at=now,
        status=SessionStatus.SCHEDULED,
        created_at=now,
        updated_at=now,
        reschedule_count=0,
    )
    api.sessions.get_by_id.return_value = session
    api.sessions.save.return_value = None
    # The case and the member must agree on the client for a drawdown to run.
    api.cases.get_by_id.return_value = SimpleNamespace(
        tenant_id=TenantId("t1"), client_id=ClientId("c1")
    )
    api.members.get_by_id.return_value = SimpleNamespace(
        tenant_id=TenantId("t1"), client_id=ClientId("c1")
    )
    api.services.get_by_id.return_value = SimpleNamespace(
        tenant_id=TenantId("t1"), category=ServiceCategory.SHORT_TERM_COUNSELLING
    )
    return api


async def test_completion_without_a_case_leaves_the_authorization_alone(completable):
    api = completable
    response = await api.http.post(
        "/service-sessions/ss1/complete", json={"duration": 60, "notes": "Attended"}
    )
    assert response.status_code == 200, response.text
    drawdown = response.json()["drawdown"]
    assert drawdown["consumed"] is False
    assert "No case supplied" in drawdown["reason"]


async def test_completion_with_a_case_draws_the_session_down(completable):
    api = completable
    authorization = _authorization(remaining=3)
    api.authorizations.list_for_case.return_value = [authorization]

    response = await api.http.post(
        "/service-sessions/ss1/complete",
        json={"duration": 60, "notes": "Attended", "case_id": "case-1"},
    )

    assert response.status_code == 200, response.text
    drawdown = response.json()["drawdown"]
    assert drawdown["consumed"] is True
    assert drawdown["authorization_id"] == "a1"
    assert drawdown["sessions_remaining"] == 2
    api.authorizations.save.assert_awaited_once()


async def test_completion_reports_why_a_named_case_did_not_draw_down(completable):
    """A session is a fact; a billing condition must not fail it."""
    api = completable
    api.authorizations.list_for_case.return_value = []

    response = await api.http.post(
        "/service-sessions/ss1/complete",
        json={"duration": 60, "notes": "Attended", "case_id": "case-1"},
    )

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["session"]["status"] == "Completed"
    assert body["drawdown"]["consumed"] is False
    assert "No active authorization" in body["drawdown"]["reason"]
    api.authorizations.save.assert_not_awaited()


async def test_a_case_from_another_client_cannot_be_drawn_down(completable):
    """The caller supplies the case, so it is checked rather than trusted."""
    api = completable
    api.cases.get_by_id.return_value = SimpleNamespace(
        tenant_id=TenantId("t1"), client_id=ClientId("some-other-client")
    )

    response = await api.http.post(
        "/service-sessions/ss1/complete",
        json={"duration": 60, "notes": "Attended", "case_id": "case-1"},
    )

    assert response.status_code == 200, response.text
    drawdown = response.json()["drawdown"]
    assert drawdown["consumed"] is False
    assert "different client" in drawdown["reason"]
    api.authorizations.list_for_case.assert_not_awaited()


async def test_a_case_from_another_tenant_is_not_found(completable):
    api = completable
    api.cases.get_by_id.return_value = SimpleNamespace(
        tenant_id=TenantId("other"), client_id=ClientId("c1")
    )

    response = await api.http.post(
        "/service-sessions/ss1/complete",
        json={"duration": 60, "notes": "Attended", "case_id": "case-1"},
    )

    assert response.json()["drawdown"]["reason"] == "Case not found"
    api.authorizations.list_for_case.assert_not_awaited()


async def test_a_missing_case_does_not_fail_the_completion(completable):
    """A session is a fact; a bad case reference must not lose it."""
    api = completable
    api.cases.get_by_id.return_value = None

    response = await api.http.post(
        "/service-sessions/ss1/complete",
        json={"duration": 60, "notes": "Attended", "case_id": "nope"},
    )

    assert response.status_code == 200, response.text
    assert response.json()["session"]["status"] == "Completed"
    assert response.json()["drawdown"]["consumed"] is False


# ---------------------------------------------------------------------------
# Delivery context. A booking must say how it is delivered; a historical record
# is the only thing allowed to say it does not know.
# ---------------------------------------------------------------------------


async def test_booking_must_state_a_delivery_context(api):
    payload = {k: v for k, v in PAYLOAD.items() if k != "delivery_context"}
    response = await api.http.post("/service-sessions/?tenant_id=t1", json=payload)
    assert response.status_code == 422
    api.sessions.save.assert_not_awaited()


async def test_unknown_delivery_is_refused_on_a_live_booking(api):
    response = await api.http.post(
        "/service-sessions/?tenant_id=t1", json={**PAYLOAD, "delivery_context": "Unknown"}
    )
    assert response.status_code in {400, 422}, response.text
    api.sessions.save.assert_not_awaited()


async def test_direct_delivery_cannot_cite_an_affiliation(api):
    response = await api.http.post(
        "/service-sessions/?tenant_id=t1",
        json={**PAYLOAD, "delivery_context": "Direct", "provider_affiliation_id": "aff-1"},
    )
    assert response.status_code == 409, response.text
    codes = {d["code"] for d in response.json()["details"]}
    assert "affiliation_not_permitted_for_direct" in codes
    api.sessions.save.assert_not_awaited()


async def test_organisation_delivery_requires_an_affiliation(api):
    response = await api.http.post(
        "/service-sessions/?tenant_id=t1",
        json={**PAYLOAD, "delivery_context": "Organisation"},
    )
    assert response.status_code == 409, response.text
    codes = {d["code"] for d in response.json()["details"]}
    assert "affiliation_required" in codes


async def test_an_affiliation_invalid_at_the_scheduled_time_is_refused(api):
    api.affiliations.get_valid_affiliation.return_value = None
    response = await api.http.post(
        "/service-sessions/?tenant_id=t1",
        json={
            **PAYLOAD,
            "delivery_context": "Organisation",
            "provider_affiliation_id": "aff-1",
        },
    )
    assert response.status_code == 409, response.text
    codes = {d["code"] for d in response.json()["details"]}
    assert "affiliation_not_valid_at_time" in codes


async def test_an_unapproved_organisation_is_refused_with_both_facts(api):
    api.organisations.get_organisation.return_value = SimpleNamespace(
        is_active=False, approval_status=_NOT_APPROVED
    )
    response = await api.http.post(
        "/service-sessions/?tenant_id=t1",
        json={
            **PAYLOAD,
            "delivery_context": "Organisation",
            "provider_affiliation_id": "aff-1",
        },
    )
    assert response.status_code == 409, response.text
    codes = {d["code"] for d in response.json()["details"]}
    assert {"organisation_not_active", "organisation_not_approved"} <= codes


async def test_organisation_delivery_succeeds_and_reports_its_own_organisation(api):
    response = await api.http.post(
        "/service-sessions/?tenant_id=t1",
        json={
            **PAYLOAD,
            "delivery_context": "Organisation",
            "provider_affiliation_id": "aff-1",
        },
    )
    assert response.status_code == 201, response.text
    body = response.json()
    assert body["delivery_context"] == "Organisation"
    assert body["provider_affiliation_id"] == "aff-1"
    assert body["provider_organisation_id"] == "org-1"


# ---------------------------------------------------------------------------
# Rescheduling reapplies the whole gate, not just the practitioner's half.
# The route once called the gate without its delivery arguments at all, and
# only the e2e suite caught it, so these pin every branch at the unit level.
# ---------------------------------------------------------------------------


def _scheduled_session(*, delivery_context="Direct", affiliation_id=None) -> SimpleNamespace:
    return SimpleNamespace(
        id=SessionId("sess-1"),
        tenant_id=TenantId("t1"),
        provider_id=ProviderId("p1"),
        delivery_context=SessionDeliveryContext(delivery_context),
        provider_affiliation_id=affiliation_id,
    )


def _use_session(api, session) -> None:
    api.app.dependency_overrides[get_service_session_for_current_tenant] = lambda: session


async def _reschedule(api):
    return await api.http.post(
        "/service-sessions/sess-1/reschedule",
        json={"new_scheduled_at": "2026-10-01T09:00:00Z"},
    )


def _codes(response) -> set[str]:
    return {d["code"] for d in response.json()["details"]}


async def test_reschedule_reapplies_the_practitioner_gate(api):
    _use_session(api, _scheduled_session())
    suspended = _bookable_provider()
    suspended.change_panel_status(PanelStatus.SUSPENDED, UserId("admin"), "Quality review")
    api.providers.get_for_booking.return_value = suspended

    response = await _reschedule(api)

    assert response.status_code == 409, response.text
    assert "panel_not_active" in _codes(response)


async def test_reschedule_reapplies_the_affiliation_check_for_the_new_date(api):
    """An affiliation valid at the original time need not cover the new one."""
    _use_session(api, _scheduled_session(delivery_context="Organisation", affiliation_id="aff-1"))
    api.affiliations.get_valid_affiliation.return_value = None

    response = await _reschedule(api)

    assert response.status_code == 409, response.text
    assert "affiliation_not_valid_at_time" in _codes(response)


async def test_reschedule_reapplies_the_organisation_check(api):
    _use_session(api, _scheduled_session(delivery_context="Organisation", affiliation_id="aff-1"))
    api.organisations.get_organisation.return_value = SimpleNamespace(
        is_active=True, approval_status=_NOT_APPROVED
    )

    response = await _reschedule(api)

    assert response.status_code == 409, response.text
    assert "organisation_not_approved" in _codes(response)


async def test_reschedule_refuses_a_session_of_unknown_delivery(api):
    """A historical record describes the past; it is not reschedulable."""
    _use_session(api, _scheduled_session(delivery_context="Unknown"))

    response = await _reschedule(api)

    assert response.status_code in {400, 422}, response.text
