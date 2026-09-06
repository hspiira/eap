"""Vocabulary write controls and alias reconciliation authorization."""

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
import pytest_asyncio
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from app.api.dependencies import get_audit_event_handler
from app.api.dependencies.provider_network import (
    get_provider_alias_repository,
    get_provider_specialty_repository,
)
from app.api.routes.provider_aliases import router as alias_router
from app.api.routes.provider_specialties import router as specialty_router
from app.core.authorization import get_current_user_entity, require_platform_admin
from app.core.database import get_db
from app.core.exception_handlers import register_exception_handlers
from app.core.security import TokenData, get_current_user
from app.domain.entities.provider_alias import ProviderAliasEntity
from app.domain.entities.provider_specialty import ProviderSpecialtyEntity
from app.domain.enums.tenancy import TenantRole
from app.domain.value_objects.core import TenantId
from app.domain.value_objects.provider_network import ProviderAliasId, ProviderSpecialtyId
from app.shared.utils.datetime import utc_now

TENANT = "t-1"


def _specialty(is_active: bool = True) -> ProviderSpecialtyEntity:
    now = utc_now()
    return ProviderSpecialtyEntity(
        id=ProviderSpecialtyId("spec-1"),
        code="cbt",
        label="CBT",
        is_active=is_active,
        created_at=now,
        updated_at=now,
    )


def _alias() -> ProviderAliasEntity:
    now = utc_now()
    return ProviderAliasEntity(
        id=ProviderAliasId("al-1"),
        tenant_id=TenantId(TENANT),
        source_system="sessions-csv",
        source_value="Dr Alice Nakato",
        normalized_value="alice nakato",
        created_at=now,
        updated_at=now,
    )


@pytest_asyncio.fixture
async def api():
    app = FastAPI()
    app.include_router(specialty_router)
    app.include_router(alias_router)
    register_exception_handlers(app)
    state = SimpleNamespace(
        specialties=AsyncMock(),
        aliases=AsyncMock(),
        audit=AsyncMock(),
        db=AsyncMock(),
        role="Admin",
        is_platform_admin=True,
    )
    state.specialties.get_specialty.return_value = _specialty()
    state.specialties.list_specialties.return_value = [_specialty()]
    state.aliases.get_alias.return_value = _alias()

    def _user() -> TokenData:
        return TokenData(user_id="u-1", tenant_id=TENANT, role=state.role)

    def _user_entity():
        return SimpleNamespace(id="u-1", tenant_id=TenantId(TENANT), role=TenantRole(state.role))

    async def _platform_admin() -> TokenData:
        if not state.is_platform_admin:
            from fastapi import HTTPException

            raise HTTPException(status_code=403, detail="Platform admin required")
        return _user()

    app.dependency_overrides[get_current_user] = _user
    app.dependency_overrides[get_current_user_entity] = _user_entity
    app.dependency_overrides[require_platform_admin] = _platform_admin
    app.dependency_overrides[get_provider_specialty_repository] = lambda: state.specialties
    app.dependency_overrides[get_provider_alias_repository] = lambda: state.aliases
    app.dependency_overrides[get_audit_event_handler] = lambda: state.audit
    app.dependency_overrides[get_db] = lambda: state.db
    state.app = app
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as http:
        state.http = http
        yield state


class TestCatalogueWriteControl:
    async def test_a_platform_admin_may_create_a_specialty(self, api):
        response = await api.http.post(
            "/provider-specialties", json={"code": "CBT", "label": "CBT"}
        )
        assert response.status_code == 201, response.text
        api.specialties.save_specialty.assert_awaited()

    async def test_a_tenant_admin_may_not_create_a_specialty(self, api):
        """Decision 5 keeps the vocabulary shared, so tenants cannot mint entries."""
        api.is_platform_admin = False
        response = await api.http.post(
            "/provider-specialties", json={"code": "CBT", "label": "CBT"}
        )
        assert response.status_code == 403
        api.specialties.save_specialty.assert_not_awaited()

    async def test_a_tenant_admin_may_not_retire_a_specialty(self, api):
        api.is_platform_admin = False
        response = await api.http.post("/provider-specialties/spec-1/retire")
        assert response.status_code == 403
        api.specialties.save_specialty.assert_not_awaited()

    async def test_the_code_is_normalised_to_lower_case(self, api):
        response = await api.http.post(
            "/provider-specialties", json={"code": "  CBT  ", "label": " CBT "}
        )
        assert response.json()["code"] == "cbt"


class TestLinkSelection:
    async def test_an_active_specialty_can_be_linked(self, api):
        response = await api.http.post(
            f"/provider-specialties/links?tenant_id={TENANT}",
            json={"provider_id": "prov-1", "specialty_id": "spec-1"},
        )
        assert response.status_code == 201, response.text
        api.specialties.add_link.assert_awaited()

    async def test_a_retired_specialty_cannot_be_newly_selected(self, api):
        api.specialties.get_specialty.return_value = _specialty(is_active=False)
        response = await api.http.post(
            f"/provider-specialties/links?tenant_id={TENANT}",
            json={"provider_id": "prov-1", "specialty_id": "spec-1"},
        )
        assert response.status_code == 422
        api.specialties.add_link.assert_not_awaited()

    async def test_a_viewer_cannot_link(self, api):
        api.role = "Viewer"
        response = await api.http.post(
            f"/provider-specialties/links?tenant_id={TENANT}",
            json={"provider_id": "prov-1", "specialty_id": "spec-1"},
        )
        assert response.status_code == 403
        api.specialties.add_link.assert_not_awaited()


class TestAliasReconciliation:
    async def test_an_admin_may_resolve_an_alias(self, api):
        response = await api.http.post(
            f"/provider-aliases/al-1/resolve?tenant_id={TENANT}",
            json={"provider_id": "prov-1"},
        )
        assert response.status_code == 200, response.text
        body = response.json()
        assert body["state"] == "Resolved"
        assert body["provider_id"] == "prov-1"

    @pytest.mark.parametrize("role", ["User", "Viewer"])
    async def test_a_non_admin_may_not_resolve_an_alias(self, api, role):
        """A wrong mapping silently reattributes historical work."""
        api.role = role
        response = await api.http.post(
            f"/provider-aliases/al-1/resolve?tenant_id={TENANT}",
            json={"provider_id": "prov-1"},
        )
        assert response.status_code == 403
        api.aliases.save_alias.assert_not_awaited()

    async def test_resolving_is_audited_with_the_actor(self, api):
        await api.http.post(
            f"/provider-aliases/al-1/resolve?tenant_id={TENANT}",
            json={"provider_id": "prov-1"},
        )
        api.audit.handle_events.assert_awaited()
        events = (
            api.audit.handle_events.await_args.kwargs.get("events")
            or (api.audit.handle_events.await_args.args[0])
        )
        assert any(type(e).__name__ == "ProviderAliasResolved" for e in events)

    async def test_rejecting_requires_a_note(self, api):
        response = await api.http.post(
            f"/provider-aliases/al-1/reject?tenant_id={TENANT}", json={"note": "   "}
        )
        assert response.status_code == 422
        api.aliases.save_alias.assert_not_awaited()

    async def test_there_is_no_automatic_resolution_endpoint(self, api):
        """Identity is never inferred; every resolution names an actor."""
        paths = {getattr(route, "path", "") for route in api.app.routes}
        assert not any("auto" in path or "match" in path for path in paths)

    async def test_another_tenants_alias_is_refused(self, api):
        response = await api.http.post(
            "/provider-aliases/al-1/resolve?tenant_id=t-other",
            json={"provider_id": "prov-1"},
        )
        assert response.status_code == 403
