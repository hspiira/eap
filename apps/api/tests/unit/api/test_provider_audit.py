"""Provider mutations must reach audit_logs.

panel.py injected an audit handler and advertised itself as audit-trailed
without ever calling it, and providers.py had no audit at all, so panel status,
tier, create and patch all mutated providers silently. A route summary is not
evidence; these assert the call.
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
from app.core.database import get_db
from app.core.exception_handlers import register_exception_handlers
from app.core.security import TokenData, get_current_user
from app.domain.entities.provider import ProviderEntity
from app.domain.enums import (
    AccreditationStatus,
    BaseStatus,
    PanelStatus,
    ProviderTier,
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
    )
    state.providers.get_by_id.return_value = _provider()
    state.providers.get_user_in_tenant.return_value = SimpleNamespace(
        id=UserId("u1"), email="p@example.com", display_name="P"
    )
    app.dependency_overrides[get_provider_repository] = lambda: state.providers
    app.dependency_overrides[get_audit_event_handler] = lambda: state.audit
    app.dependency_overrides[get_db] = lambda: state.db
    app.dependency_overrides[get_current_user] = lambda: state.user
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as http:
        state.http = http
        yield state


@pytest.mark.asyncio
async def test_tier_change_is_audited(api):
    response = await api.http.patch(
        "/panel/prov-1/tier", json={"new_tier": "T2", "reason": "Panel review"}
    )
    assert response.status_code == 200, response.text
    api.audit.handle_events.assert_awaited()
    events = (
        api.audit.handle_events.await_args.kwargs.get("events")
        or (api.audit.handle_events.await_args.args[0])
    )
    assert any(type(e).__name__ == "ProviderTierChanged" for e in events)


@pytest.mark.asyncio
async def test_bulk_panel_status_is_audited(api):
    response = await api.http.patch(
        "/panel/bulk-panel-status",
        json={
            "provider_ids": ["prov-1"],
            "new_status": "Suspended",
            "reason": "Panel review",
        },
    )
    assert response.status_code == 200, response.text
    api.audit.handle_events.assert_awaited()
    events = (
        api.audit.handle_events.await_args.kwargs.get("events")
        or (api.audit.handle_events.await_args.args[0])
    )
    assert any(type(e).__name__ == "ProviderPanelStatusChanged" for e in events)
