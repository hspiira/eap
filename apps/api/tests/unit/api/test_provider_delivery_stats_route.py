"""GET /providers/{id}/delivery-stats serialises the aggregate the repository returns.

The route is authenticated and tenant-scoped through the provider load, and it
asks the repository for counts rather than counting a fetched page.
"""

from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest_asyncio
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from app.api.dependencies import (
    get_provider_repository,
    get_service_session_repository,
)
from app.api.routes.providers import router
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
from app.domain.repositories.service_session_repository import (
    ProviderDeliveryStats,
    ProviderOrganisationSessionCount,
)
from app.domain.value_objects.core import ProviderId, ProviderProfile, TenantId
from app.shared.utils.datetime import utc_now

TENANT = "t-1"
PROVIDER = "p-1"
URL = f"/providers/{PROVIDER}/delivery-stats"


def _provider(tenant: str = TENANT) -> ProviderEntity:
    now = utc_now()
    return ProviderEntity(
        id=ProviderId(PROVIDER),
        tenant_id=TenantId(tenant),
        status=BaseStatus.ACTIVE,
        display_name="Amina Okello",
        created_at=now,
        updated_at=now,
        provider_profile=ProviderProfile(
            tier=ProviderTier.T1,
            region=UgandaRegion.CENTRAL,
            accreditation_status=AccreditationStatus.ACCREDITED,
            panel_status=PanelStatus.ACTIVE,
        ),
    )


def _stats() -> ProviderDeliveryStats:
    return ProviderDeliveryStats(
        total_sessions=86,
        first_session_at=datetime(2023, 2, 3, 8, 30, tzinfo=UTC),
        last_session_at=datetime(2025, 9, 9, 16, 0, tzinfo=UTC),
        by_delivery_context={
            SessionDeliveryContext.UNKNOWN: 85,
            SessionDeliveryContext.DIRECT: 1,
        },
        by_organisation=[
            ProviderOrganisationSessionCount("org-a", "Kampala Counselling Partners", 60),
            ProviderOrganisationSessionCount("org-b", "Entebbe Wellbeing Group", 12),
        ],
    )


def _build_app(state, *, authenticate: bool = True) -> FastAPI:
    app = FastAPI()
    app.include_router(router)
    register_exception_handlers(app)
    if authenticate:
        app.dependency_overrides[get_current_user] = lambda: TokenData(
            user_id="u-1", tenant_id=TENANT, role="Admin"
        )
    app.dependency_overrides[get_provider_repository] = lambda: state.providers
    app.dependency_overrides[get_service_session_repository] = lambda: state.sessions
    app.dependency_overrides[get_db] = lambda: state.db
    return app


def _state() -> SimpleNamespace:
    state = SimpleNamespace(providers=AsyncMock(), sessions=AsyncMock(), db=AsyncMock())
    state.providers.get_by_id.return_value = _provider()
    state.sessions.provider_delivery_stats.return_value = _stats()
    return state


@pytest_asyncio.fixture
async def api():
    state = _state()
    async with AsyncClient(
        transport=ASGITransport(app=_build_app(state)), base_url="http://test"
    ) as http:
        state.http = http
        yield state


@pytest_asyncio.fixture
async def anonymous():
    state = _state()
    async with AsyncClient(
        transport=ASGITransport(app=_build_app(state, authenticate=False)),
        base_url="http://test",
    ) as http:
        state.http = http
        yield state


class TestAccess:
    async def test_an_anonymous_read_is_refused(self, anonymous):
        response = await anonymous.http.get(URL)
        assert response.status_code == 401
        anonymous.sessions.provider_delivery_stats.assert_not_awaited()

    async def test_another_tenants_practitioner_is_not_found(self, api):
        api.providers.get_by_id.return_value = _provider(tenant="t-2")

        response = await api.http.get(URL)

        assert response.status_code == 404
        api.sessions.provider_delivery_stats.assert_not_awaited()

    async def test_a_missing_practitioner_is_not_found(self, api):
        api.providers.get_by_id.return_value = None
        assert (await api.http.get(URL)).status_code == 404


class TestResponse:
    async def test_the_totals_come_from_the_repository_aggregate(self, api):
        response = await api.http.get(URL)

        assert response.status_code == 200, response.text
        body = response.json()
        assert body["total_sessions"] == 86
        assert body["first_session_at"] == "2023-02-03T08:30:00Z"
        assert body["last_session_at"] == "2025-09-09T16:00:00Z"

    async def test_the_context_breakdown_is_keyed_by_enum_value(self, api):
        body = (await api.http.get(URL)).json()
        assert body["by_delivery_context"] == {"Unknown": 85, "Direct": 1}

    async def test_the_organisation_breakdown_keeps_the_repository_order(self, api):
        body = (await api.http.get(URL)).json()
        assert body["by_organisation"] == [
            {
                "organisation_id": "org-a",
                "organisation_name": "Kampala Counselling Partners",
                "session_count": 60,
            },
            {
                "organisation_id": "org-b",
                "organisation_name": "Entebbe Wellbeing Group",
                "session_count": 12,
            },
        ]

    async def test_an_empty_record_reports_zero_and_no_bounds(self, api):
        api.sessions.provider_delivery_stats.return_value = ProviderDeliveryStats(
            total_sessions=0,
            first_session_at=None,
            last_session_at=None,
            by_delivery_context={},
            by_organisation=[],
        )

        body = (await api.http.get(URL)).json()

        assert body == {
            "total_sessions": 0,
            "first_session_at": None,
            "last_session_at": None,
            "by_delivery_context": {},
            "by_organisation": [],
        }

    async def test_the_repository_is_asked_for_this_tenants_practitioner(self, api):
        await api.http.get(URL)

        tenant, provider = api.sessions.provider_delivery_stats.await_args.args
        assert (tenant.value, provider.value) == (TENANT, PROVIDER)
