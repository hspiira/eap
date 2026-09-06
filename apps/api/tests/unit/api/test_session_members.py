from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
import pytest_asyncio
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from app.api.dependencies import (
    get_audit_event_handler,
    get_eligible_member_repository,
    get_person_repository,
    get_service_repository,
    get_service_session_repository,
)
from app.api.dependencies.clinical import get_authorization_repository, get_case_repository
from app.api.routes.service_sessions import router
from app.core.database import get_db
from app.core.exception_handlers import register_exception_handlers
from app.core.security import TokenData, get_current_user
from app.domain.enums import PersonType
from app.domain.value_objects.core import ClientId, EligibleMemberId, TenantId


@pytest_asyncio.fixture
async def api():
    app = FastAPI()
    app.include_router(router)
    register_exception_handlers(app)
    state = SimpleNamespace(
        members=AsyncMock(),
        persons=AsyncMock(),
        services=AsyncMock(),
        sessions=AsyncMock(),
        authorizations=AsyncMock(),
        cases=AsyncMock(),
        audit=AsyncMock(),
        db=AsyncMock(),
        user=TokenData(user_id="u1", tenant_id="t1", role="Admin"),
    )
    state.members.get_by_id.return_value = SimpleNamespace(tenant_id=TenantId("t1"))
    state.persons.get_by_id.return_value = SimpleNamespace(
        tenant_id=TenantId("t1"), person_type=PersonType.SERVICE_PROVIDER
    )
    state.services.get_by_id.return_value = SimpleNamespace(tenant_id=TenantId("t1"))
    for dep, value in {
        get_eligible_member_repository: state.members,
        get_person_repository: state.persons,
        get_service_repository: state.services,
        get_service_session_repository: state.sessions,
        get_authorization_repository: state.authorizations,
        get_case_repository: state.cases,
        get_audit_event_handler: state.audit,
        get_db: state.db,
    }.items():
        app.dependency_overrides[dep] = (lambda v: lambda: v)(value)
    app.dependency_overrides[get_current_user] = lambda: state.user
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as http:
        state.http = http
        yield state


PAYLOAD = dict(
    member_id="m1", provider_id="p1", service_id="s1", scheduled_at="2026-09-10T09:00:00Z"
)


async def test_create_uses_a_member_without_a_user_account(api):
    response = await api.http.post("/service-sessions/?tenant_id=t1", json=PAYLOAD)
    assert response.status_code == 201, response.text
    assert response.json()["member_id"] == "m1"
    assert "person_id" not in response.json()
    saved = api.sessions.save.call_args.args[0]
    assert saved.member_id == EligibleMemberId("m1")
    api.db.commit.assert_awaited_once()


@pytest.mark.parametrize("resource", ["members", "persons", "services"])
async def test_rejects_foreign_tenant_references(api, resource):
    getattr(api, resource).get_by_id.return_value.tenant_id = TenantId("other")
    response = await api.http.post("/service-sessions/?tenant_id=t1", json=PAYLOAD)
    assert response.status_code == 404
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
