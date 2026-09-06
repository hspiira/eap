"""Provider routes: authorization, protected fields and the audit call.

These run against the real routers with mocked persistence, so they pin the
route's behaviour rather than a use case no route calls. That a handler was
awaited is not evidence that a row was written; persistence and rollback are
proved in tests/integration/test_provider_audit_persistence.py.
"""

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
import pytest_asyncio
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from app.api.dependencies import get_audit_event_handler, get_provider_repository
from app.api.routes.panel import router as panel_router
from app.api.routes.providers import router as providers_router
from app.core.authorization import get_current_user_entity
from app.core.database import get_db
from app.core.exception_handlers import register_exception_handlers
from app.core.security import TokenData, get_current_user
from app.domain.entities.provider import ProviderEntity
from app.domain.enums import (
    AccreditationStatus,
    BaseStatus,
    PanelStatus,
    ProviderTier,
    TenantRole,
    UgandaRegion,
)
from app.domain.value_objects.core import ProviderId, ProviderProfile, TenantId, UserId
from app.shared.utils.datetime import utc_now


def _provider() -> ProviderEntity:
    now = utc_now()
    return ProviderEntity(
        id=ProviderId("prov-1"),
        tenant_id=TenantId("t1"),
        user_id=UserId("u1"),
        display_name="Amina Okello",
        contact_email="amina@example.com",
        status=BaseStatus.ACTIVE,
        created_at=now,
        updated_at=now,
        provider_profile=ProviderProfile(
            tier=ProviderTier.T1,
            region=UgandaRegion.CENTRAL,
            accreditation_status=AccreditationStatus.ACCREDITED,
            panel_status=PanelStatus.ACTIVE,
        ),
    )


@pytest_asyncio.fixture
async def api():
    app = FastAPI()
    app.include_router(panel_router)
    app.include_router(providers_router)
    register_exception_handlers(app)
    state = SimpleNamespace(
        providers=AsyncMock(),
        audit=AsyncMock(),
        db=AsyncMock(),
        user=TokenData(user_id="u1", tenant_id="t1", role="Admin"),
        entity=SimpleNamespace(id=UserId("u1"), tenant_id=TenantId("t1"), role=TenantRole.ADMIN),
    )
    state.providers.get_by_id.return_value = _provider()
    state.providers.get_by_user_id.return_value = None
    state.providers.get_user_in_tenant.return_value = SimpleNamespace(
        id=UserId("u9"), email="p@example.com", display_name="P"
    )
    app.dependency_overrides[get_provider_repository] = lambda: state.providers
    app.dependency_overrides[get_audit_event_handler] = lambda: state.audit
    app.dependency_overrides[get_db] = lambda: state.db
    app.dependency_overrides[get_current_user] = lambda: state.user
    app.dependency_overrides[get_current_user_entity] = lambda: state.entity
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as http:
        state.http = http
        yield state


def _event_names(audit: AsyncMock) -> list[str]:
    call = audit.handle_events.await_args
    events = call.kwargs.get("events") or call.args[0]
    return [type(event).__name__ for event in events]


# --------------------------------------------------------------------------
# Lifecycle commands emit and audit
# --------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("path", "body", "event"),
    [
        ("/providers/prov-1/tier", {"tier": "T2", "reason": "Panel review"}, "ProviderTierChanged"),
        (
            "/providers/prov-1/panel-status",
            {"panel_status": "Suspended", "reason": "Panel review"},
            "ProviderPanelStatusChanged",
        ),
        (
            "/providers/prov-1/accreditation",
            {"accreditation_status": "Lapsed", "reason": "Certificate expired"},
            "ProviderAccreditationChanged",
        ),
        (
            "/providers/prov-1/status",
            {"status": "Inactive", "reason": "On leave"},
            "ProviderStatusChanged",
        ),
    ],
)
async def test_lifecycle_command_is_audited(api, path, body, event):
    response = await api.http.patch(path, json=body)
    assert response.status_code == 200, response.text
    api.audit.handle_events.assert_awaited()
    assert event in _event_names(api.audit)


@pytest.mark.asyncio
async def test_create_is_audited(api):
    response = await api.http.post(
        "/providers?tenant_id=t1",
        json={"display_name": "New Practitioner", "tier": "T2", "region": "Central"},
    )
    assert response.status_code == 201, response.text
    assert "ProviderCreated" in _event_names(api.audit)


@pytest.mark.asyncio
async def test_create_starts_pending_with_no_account(api):
    response = await api.http.post(
        "/providers?tenant_id=t1",
        json={"display_name": "New Practitioner", "tier": "T2", "region": "Central"},
    )
    body = response.json()
    assert body["status"] == "Pending"
    assert body["provider_profile"]["panel_status"] == "Pending"
    assert body["provider_profile"]["accreditation_status"] == "Pending"
    assert body["user_id"] is None


@pytest.mark.asyncio
async def test_general_patch_is_audited(api):
    response = await api.http.patch("/providers/prov-1", json={"region": "Eastern"})
    assert response.status_code == 200, response.text
    assert "ProviderProfileUpdated" in _event_names(api.audit)


@pytest.mark.asyncio
async def test_bulk_panel_status_is_audited(api):
    response = await api.http.patch(
        "/panel/bulk-panel-status",
        json={"provider_ids": ["prov-1"], "new_status": "Suspended", "reason": "Panel review"},
    )
    assert response.status_code == 200, response.text
    assert "ProviderPanelStatusChanged" in _event_names(api.audit)


@pytest.mark.asyncio
async def test_unchanged_command_writes_no_event(api):
    """Repeating a command that changes nothing is a no-op, not a new audit row."""
    response = await api.http.patch(
        "/providers/prov-1/tier", json={"tier": "T1", "reason": "reaffirm"}
    )
    assert response.status_code == 200
    api.audit.handle_events.assert_not_awaited()


# --------------------------------------------------------------------------
# General PATCH cannot reach a lifecycle field
# --------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "body",
    [
        {"tier": "T3"},
        {"panel_status": "Active"},
        {"accreditation_status": "Accredited"},
        {"accreditation_expiry": "2030-01-01"},
        {"status": "Active"},
        {"user_id": "u9"},
        {"provider_profile": {"tier": "T3", "region": "Central"}},
        {"specialties": ["Trauma"]},
    ],
)
async def test_patch_rejects_protected_fields(api, body):
    response = await api.http.patch("/providers/prov-1", json=body)
    assert response.status_code == 422, response.text
    api.providers.save.assert_not_awaited()
    api.audit.handle_events.assert_not_awaited()


@pytest.mark.asyncio
async def test_patch_is_partial_and_clears_only_what_it_names(api):
    response = await api.http.patch("/providers/prov-1", json={"email": None})
    assert response.status_code == 200, response.text
    saved = api.providers.save.await_args.args[0]
    assert saved.contact_email is None
    assert saved.display_name == "Amina Okello"
    assert saved.provider_profile.tier == ProviderTier.T1


# --------------------------------------------------------------------------
# Authorization
# --------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("method", "path", "body"),
    [
        ("patch", "/providers/prov-1/tier", {"tier": "T2", "reason": "x"}),
        ("patch", "/providers/prov-1/panel-status", {"panel_status": "Removed", "reason": "x"}),
        (
            "patch",
            "/providers/prov-1/accreditation",
            {"accreditation_status": "Lapsed", "reason": "x"},
        ),
        ("patch", "/providers/prov-1/status", {"status": "Inactive", "reason": "x"}),
        ("patch", "/providers/prov-1", {"region": "Eastern"}),
        (
            "patch",
            "/panel/bulk-panel-status",
            {"provider_ids": ["prov-1"], "new_status": "Removed", "reason": "x"},
        ),
        ("patch", "/panel/prov-1/tier", {"new_tier": "T2", "reason": "x"}),
        ("post", "/providers/prov-1/account-link", {"user_id": "u9", "reason": "x"}),
    ],
)
async def test_viewer_cannot_mutate(api, method, path, body):
    api.user.role = "Viewer"
    api.entity.role = TenantRole.VIEWER
    response = await getattr(api.http, method)(path, json=body)
    assert response.status_code == 403, response.text
    api.providers.save.assert_not_awaited()
    api.audit.handle_events.assert_not_awaited()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("method", "path", "body"),
    [
        ("patch", "/providers/prov-1/tier", {"tier": "T2", "reason": "x"}),
        ("patch", "/providers/prov-1/panel-status", {"panel_status": "Removed", "reason": "x"}),
        (
            "patch",
            "/providers/prov-1/accreditation",
            {"accreditation_status": "Lapsed", "reason": "x"},
        ),
        ("patch", "/providers/prov-1/status", {"status": "Inactive", "reason": "x"}),
        ("post", "/providers/prov-1/account-link", {"user_id": "u9", "reason": "x"}),
    ],
)
async def test_non_admin_cannot_run_lifecycle_commands(api, method, path, body):
    """A non-Viewer operational role may edit contact data but not lifecycle fields."""
    api.user.role = "User"
    api.entity.role = TenantRole.USER
    response = await getattr(api.http, method)(path, json=body)
    assert response.status_code == 403, response.text
    api.providers.save.assert_not_awaited()


@pytest.mark.asyncio
async def test_non_admin_may_still_edit_ordinary_fields(api):
    api.user.role = "User"
    api.entity.role = TenantRole.USER
    response = await api.http.patch("/providers/prov-1", json={"phone": "+256700000000"})
    assert response.status_code == 200, response.text


@pytest.mark.asyncio
async def test_cross_tenant_provider_is_not_found(api):
    foreign = _provider()
    foreign.tenant_id = TenantId("other")
    api.providers.get_by_id.return_value = foreign
    response = await api.http.patch("/providers/prov-1/tier", json={"tier": "T2", "reason": "x"})
    assert response.status_code == 404
    api.providers.save.assert_not_awaited()


# --------------------------------------------------------------------------
# Reasons and account linking
# --------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("path", "body"),
    [
        ("/providers/prov-1/tier", {"tier": "T2", "reason": ""}),
        ("/providers/prov-1/panel-status", {"panel_status": "Removed", "reason": ""}),
        ("/providers/prov-1/accreditation", {"accreditation_status": "Lapsed", "reason": ""}),
        ("/providers/prov-1/status", {"status": "Inactive", "reason": ""}),
    ],
)
async def test_lifecycle_command_requires_a_reason(api, path, body):
    response = await api.http.patch(path, json=body)
    assert response.status_code == 422, response.text
    api.providers.save.assert_not_awaited()


@pytest.mark.asyncio
async def test_account_link_rejects_a_user_from_another_tenant(api):
    api.providers.get_user_in_tenant.return_value = None
    response = await api.http.post(
        "/providers/prov-1/account-link", json={"user_id": "u9", "reason": "Onboarding"}
    )
    assert response.status_code == 404
    api.providers.save.assert_not_awaited()


@pytest.mark.asyncio
async def test_account_link_rejects_an_account_already_linked_elsewhere(api):
    other = _provider()
    other.id = ProviderId("prov-2")
    api.providers.get_by_user_id.return_value = other
    api.providers.get_by_id.return_value = _provider()
    api.providers.get_by_id.return_value.user_id = None
    response = await api.http.post(
        "/providers/prov-1/account-link", json={"user_id": "u9", "reason": "Onboarding"}
    )
    assert response.status_code == 409, response.text
    api.providers.save.assert_not_awaited()


@pytest.mark.asyncio
async def test_unlinking_keeps_the_practitioner_visible(api):
    response = await api.http.request(
        "DELETE",
        "/providers/prov-1/account-link",
        json={"reason": "Left the organisation"},
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["user_id"] is None
    assert body["display_name"] == "Amina Okello"
    assert "ProviderAccountUnlinked" in _event_names(api.audit)


# --------------------------------------------------------------------------
# A blank reason is one shape, whatever kind of blank it is.
#
# min_length is checked before stripping, so "   " satisfied it, reached the
# domain, and came back as a 400 with nothing a form could attach to a field,
# while "" came back as a 422 field error. A client could not handle both with
# one path, and spaces are the variant a real user types.
# --------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.parametrize("blank", ["", "   ", "\t", "\n  \t "])
@pytest.mark.parametrize(
    ("path", "body"),
    [
        ("/providers/prov-1/tier", {"tier": "T2"}),
        ("/providers/prov-1/panel-status", {"panel_status": "Removed"}),
        ("/providers/prov-1/accreditation", {"accreditation_status": "Lapsed"}),
        ("/providers/prov-1/status", {"status": "Inactive"}),
    ],
)
async def test_every_blank_reason_is_the_same_422(api, path, body, blank):
    response = await api.http.patch(path, json={**body, "reason": blank})

    assert response.status_code == 422, response.text
    assert any("reason" in str(d.get("field", "")) for d in response.json()["details"])
    api.providers.save.assert_not_awaited()


@pytest.mark.asyncio
async def test_a_reason_is_stored_stripped(api):
    response = await api.http.patch(
        "/providers/prov-1/tier", json={"tier": "T2", "reason": "  Panel review  "}
    )

    assert response.status_code == 200, response.text
    events = api.audit.handle_events.await_args
    reasons = [
        e.reason for e in (events.kwargs.get("events") or events.args[0]) if hasattr(e, "reason")
    ]
    assert reasons == ["Panel review"]


@pytest.mark.asyncio
async def test_the_account_link_commands_reject_a_blank_reason_the_same_way(api):
    link = await api.http.post(
        "/providers/prov-1/account-link", json={"user_id": "u9", "reason": "   "}
    )
    unlink = await api.http.request(
        "DELETE", "/providers/prov-1/account-link", json={"reason": "   "}
    )

    assert link.status_code == 422, link.text
    assert unlink.status_code == 422, unlink.text
    api.providers.save.assert_not_awaited()
