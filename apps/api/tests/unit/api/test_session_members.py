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
from app.api.routes.service_sessions import router
from app.core.database import get_db
from app.core.exception_handlers import register_exception_handlers
from app.core.security import TokenData, get_current_user
from app.domain.enums import PersonType
from app.domain.value_objects.core import EligibleMemberId, TenantId


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
