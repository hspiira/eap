"""Route-level authorization and the protected-field boundary.

Decision 7 puts approval and activation behind tenant Admin and bars Viewers
from any mutation. Decision 8 requires one audited path, so a general PATCH
must not be able to move approval.
"""

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
import pytest_asyncio
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from app.api.dependencies import get_audit_event_handler
from app.api.dependencies.provider_network import get_provider_organisation_repository
from app.api.routes.provider_organisations import router
from app.api.schemas.provider_network_schemas import ProviderOrganisationUpdate
from app.core.authorization import get_current_user_entity
from app.core.database import get_db
from app.core.exception_handlers import register_exception_handlers
from app.core.security import TokenData, get_current_user
from app.domain.entities.provider_organisation import ProviderOrganisationEntity
from app.domain.entities.user import UserEntity
from app.domain.enums.provider_network import OrganisationApprovalStatus
from app.domain.enums.tenancy import TenantRole
from app.domain.value_objects.core import TenantId
from app.domain.value_objects.provider_network import ProviderOrganisationId
from app.shared.utils.datetime import utc_now

TENANT = "t-1"


def _organisation() -> ProviderOrganisationEntity:
    now = utc_now()
    return ProviderOrganisationEntity(
        id=ProviderOrganisationId("org-1"),
        tenant_id=TenantId(TENANT),
        name="Firm A",
        created_at=now,
        updated_at=now,
    )


@pytest_asyncio.fixture
async def api():
    app = FastAPI()
    app.include_router(router)
    register_exception_handlers(app)
    state = SimpleNamespace(
        repo=AsyncMock(),
        audit=AsyncMock(),
        db=AsyncMock(),
        role="Admin",
    )
    state.repo.get_organisation.return_value = _organisation()
    state.repo.name_exists.return_value = False

    def _user() -> TokenData:
        return TokenData(user_id="u-1", tenant_id=TENANT, role=state.role)

    def _user_entity() -> UserEntity:
        """require_tenant_role reads the role from the user entity, not the token."""
        return SimpleNamespace(id="u-1", tenant_id=TenantId(TENANT), role=TenantRole(state.role))

    app.dependency_overrides[get_current_user_entity] = _user_entity
    app.dependency_overrides[get_provider_organisation_repository] = lambda: state.repo
    app.dependency_overrides[get_audit_event_handler] = lambda: state.audit
    app.dependency_overrides[get_db] = lambda: state.db
    app.dependency_overrides[get_current_user] = _user
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as http:
        state.http = http
        yield state


class TestLifecycleAuthorization:
    @pytest.mark.parametrize("command", ["approve", "suspend", "revoke", "deactivate"])
    async def test_an_admin_may_run_each_command(self, api, command):
        response = await api.http.post(
            f"/provider-organisations/org-1/{command}?tenant_id={TENANT}",
            json={"reason": "Panel review"},
        )
        assert response.status_code == 200, response.text
        api.repo.save_organisation.assert_awaited()

    @pytest.mark.parametrize("role", ["User", "Viewer"])
    @pytest.mark.parametrize("command", ["approve", "suspend", "deactivate"])
    async def test_a_non_admin_is_refused_and_nothing_is_saved(self, api, role, command):
        api.role = role
        response = await api.http.post(
            f"/provider-organisations/org-1/{command}?tenant_id={TENANT}",
            json={"reason": "Panel review"},
        )
        assert response.status_code == 403, response.text
        api.repo.save_organisation.assert_not_awaited()

    async def test_a_blank_reason_is_refused(self, api):
        response = await api.http.post(
            f"/provider-organisations/org-1/approve?tenant_id={TENANT}",
            json={"reason": "   "},
        )
        assert response.status_code == 422
        api.repo.save_organisation.assert_not_awaited()

    async def test_a_missing_reason_is_refused(self, api):
        response = await api.http.post(
            f"/provider-organisations/org-1/approve?tenant_id={TENANT}", json={}
        )
        assert response.status_code == 422
        api.repo.save_organisation.assert_not_awaited()

    async def test_an_approval_change_is_audited(self, api):
        await api.http.post(
            f"/provider-organisations/org-1/approve?tenant_id={TENANT}",
            json={"reason": "Vetted"},
        )
        api.audit.handle_events.assert_awaited()
        events = (
            api.audit.handle_events.await_args.kwargs.get("events")
            or (api.audit.handle_events.await_args.args[0])
        )
        assert any(type(e).__name__ == "ProviderOrganisationApprovalChanged" for e in events)


class TestViewerCannotMutate:
    async def test_a_viewer_cannot_create(self, api):
        api.role = "Viewer"
        response = await api.http.post(
            f"/provider-organisations?tenant_id={TENANT}", json={"name": "New Firm"}
        )
        assert response.status_code == 403
        api.repo.save_organisation.assert_not_awaited()

    async def test_a_viewer_cannot_patch(self, api):
        api.role = "Viewer"
        response = await api.http.patch(
            f"/provider-organisations/org-1?tenant_id={TENANT}", json={"name": "Renamed"}
        )
        assert response.status_code == 403
        api.repo.save_organisation.assert_not_awaited()

    async def test_a_viewer_may_read(self, api):
        api.role = "Viewer"
        response = await api.http.get(f"/provider-organisations/org-1?tenant_id={TENANT}")
        assert response.status_code == 200


class TestProtectedFields:
    def test_the_patch_schema_has_no_lifecycle_fields(self):
        """A general edit cannot carry approval or activation state."""
        fields = set(ProviderOrganisationUpdate.model_fields)
        assert "approval_status" not in fields
        assert "is_active" not in fields

    async def test_patching_approval_status_is_ignored_not_applied(self, api):
        response = await api.http.patch(
            f"/provider-organisations/org-1?tenant_id={TENANT}",
            json={"approval_status": "Approved", "is_active": False},
        )
        assert response.status_code == 200
        body = response.json()
        assert body["approval_status"] == OrganisationApprovalStatus.PENDING.value
        assert body["is_active"] is True

    async def test_a_partial_patch_leaves_unsent_fields_alone(self, api):
        response = await api.http.patch(
            f"/provider-organisations/org-1?tenant_id={TENANT}",
            json={"contact_phone": "+256700000000"},
        )
        assert response.status_code == 200
        assert response.json()["name"] == "Firm A"

    async def test_an_explicit_null_clears_an_optional_field(self, api):
        api.repo.get_organisation.return_value = _organisation()
        api.repo.get_organisation.return_value.contact_phone = "+256700000000"
        response = await api.http.patch(
            f"/provider-organisations/org-1?tenant_id={TENANT}",
            json={"contact_phone": None},
        )
        assert response.status_code == 200
        assert response.json()["contact_phone"] is None


class TestTenantScoping:
    async def test_another_tenants_id_is_refused(self, api):
        response = await api.http.get("/provider-organisations/org-1?tenant_id=t-other")
        assert response.status_code == 403

    async def test_an_unknown_organisation_is_a_404(self, api):
        api.repo.get_organisation.return_value = None
        response = await api.http.get(f"/provider-organisations/org-1?tenant_id={TENANT}")
        assert response.status_code == 404
