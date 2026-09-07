"""The eligibility preview answers from the policy the write paths apply.

Two things are pinned here. The preview and the booking gate must not be able
to disagree, and a binding non-compete clause must not block a booking:
decision 9 keeps non-compete where it is, retaining its response fields for
compatibility without activating a restriction.
"""

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
import pytest_asyncio
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from app.api.dependencies import get_non_compete_clause_repository, get_provider_repository
from app.api.routes.panel import router as panel_router
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
from app.domain.services.provider_network_calendar import boundary_day
from app.domain.value_objects.core import ProviderId, ProviderProfile, TenantId, UserId
from app.shared.utils.datetime import utc_now


def _provider(panel: PanelStatus = PanelStatus.ACTIVE) -> ProviderEntity:
    now = utc_now()
    return ProviderEntity(
        id=ProviderId("prov-1"),
        tenant_id=TenantId("t1"),
        status=BaseStatus.ACTIVE,
        display_name="Amina Okello",
        created_at=now,
        updated_at=now,
        provider_profile=ProviderProfile(
            tier=ProviderTier.T1,
            region=UgandaRegion.CENTRAL,
            accreditation_status=AccreditationStatus.ACCREDITED,
            panel_status=panel,
        ),
    )


def _binding_clause():
    return SimpleNamespace(id=SimpleNamespace(value="clause-1"), is_currently_binding=lambda: True)


@pytest_asyncio.fixture
async def api():
    app = FastAPI()
    app.include_router(panel_router)
    register_exception_handlers(app)
    state = SimpleNamespace(providers=AsyncMock(), clauses=AsyncMock(), db=AsyncMock())
    state.providers.get_by_id.return_value = _provider()
    state.clauses.list_for_provider.return_value = []
    app.dependency_overrides[get_provider_repository] = lambda: state.providers
    app.dependency_overrides[get_non_compete_clause_repository] = lambda: state.clauses
    app.dependency_overrides[get_db] = lambda: state.db
    app.dependency_overrides[get_current_user] = lambda: TokenData(
        user_id="u1", tenant_id="t1", role="Admin"
    )
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as http:
        state.http = http
        yield state


@pytest.mark.asyncio
async def test_an_eligible_practitioner_is_reported_eligible(api):
    response = await api.http.get("/panel/prov-1/eligibility")
    assert response.status_code == 200, response.text
    assert response.json()["eligible"] is True


@pytest.mark.asyncio
async def test_a_binding_non_compete_clause_does_not_block_booking(api):
    """Decision 9: repair the references, do not activate the restriction."""
    api.clauses.list_for_provider.return_value = [_binding_clause()]

    response = await api.http.get("/panel/prov-1/eligibility")

    body = response.json()
    assert body["binding_non_compete_count"] == 1, "the field is retained for compatibility"
    assert body["binding_non_compete_ids"] == ["clause-1"]
    assert body["eligible"] is True, "non-compete must not gate a booking"
    assert body["failures"] == []


@pytest.mark.asyncio
async def test_the_preview_reports_the_same_codes_the_write_path_returns(api):
    api.providers.get_by_id.return_value = _provider(panel=PanelStatus.SUSPENDED)

    response = await api.http.get("/panel/prov-1/eligibility")

    body = response.json()
    assert body["eligible"] is False
    assert [f["code"] for f in body["failures"]] == ["panel_not_active"]


@pytest.mark.asyncio
async def test_the_preview_checks_the_supplied_service_date(api):
    """An accreditation valid today need not cover a later booking.

    The expiry is today's business day in Kampala, which is what the rule
    compares against. `utc_now().date()` is a different day for the three
    hours before midnight UTC, so an expiry built from it read as lapsed and
    this test failed in exactly that window.
    """
    provider = _provider()
    provider.change_accreditation(
        UserId("admin"),
        "Certificate lapses next month",
        accreditation_status=AccreditationStatus.ACCREDITED,
        accreditation_expiry=boundary_day(utc_now()),
    )
    api.providers.get_by_id.return_value = provider

    today = await api.http.get("/panel/prov-1/eligibility")
    later = await api.http.get("/panel/prov-1/eligibility?scheduled_at=2027-01-01T09:00:00Z")

    assert today.json()["eligible"] is True
    assert later.json()["eligible"] is False
    assert [f["code"] for f in later.json()["failures"]] == ["accreditation_expired"]


@pytest.mark.asyncio
async def test_a_cross_tenant_provider_is_not_found(api):
    foreign = _provider()
    foreign.tenant_id = TenantId("other")
    api.providers.get_by_id.return_value = foreign

    assert (await api.http.get("/panel/prov-1/eligibility")).status_code == 404
