"""GET /providers/stats serialises the panel readiness rollup.

Declared before /{provider_id}, so "stats" must reach the rollup and never be
read as a practitioner id.
"""

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
import pytest_asyncio
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from app.api.dependencies import get_provider_repository
from app.api.routes.providers import router
from app.core.database import get_db
from app.core.exception_handlers import register_exception_handlers
from app.core.security import TokenData, get_current_user

TENANT = "t-1"
URL = f"/providers/stats?tenant_id={TENANT}"


def _api(counts: dict[str, int]):
    app = FastAPI()
    app.include_router(router)
    register_exception_handlers(app)
    state = SimpleNamespace(providers=AsyncMock(), db=AsyncMock())
    state.providers.count_by_panel_status.return_value = counts
    app.dependency_overrides[get_current_user] = lambda: TokenData(
        user_id="u-1", tenant_id=TENANT, role="Admin"
    )
    app.dependency_overrides[get_provider_repository] = lambda: state.providers
    app.dependency_overrides[get_db] = lambda: state.db
    return app, state


@pytest_asyncio.fixture
async def onboarding():
    app, state = _api({"Pending": 112, "Active": 1})
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as http:
        state.http = http
        yield state


@pytest.mark.asyncio
async def test_counts_come_back_by_readiness_with_absent_statuses_at_zero(onboarding):
    response = await onboarding.http.get(URL)

    assert response.status_code == 200, response.text
    assert response.json() == {
        "total": 113,
        "active": 1,
        "pending": 112,
        "suspended": 0,
        "removed": 0,
    }


@pytest.mark.asyncio
async def test_stats_is_not_swallowed_by_the_provider_id_route(onboarding):
    """The rollup answers; a 404 here means the path was read as an id."""
    response = await onboarding.http.get(URL)

    assert response.status_code == 200
    onboarding.providers.count_by_panel_status.assert_awaited_once()
    onboarding.providers.get_by_id.assert_not_awaited()


@pytest.mark.asyncio
async def test_another_tenants_stats_are_refused():
    app, _ = _api({"Active": 5})
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as http:
        response = await http.get("/providers/stats?tenant_id=t-other")

    assert response.status_code == 403, response.text


@pytest.mark.asyncio
async def test_an_empty_directory_is_all_zeroes():
    app, state = _api({})
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as http:
        response = await http.get(URL)

    assert response.status_code == 200
    assert response.json()["total"] == 0
    state.providers.count_by_panel_status.assert_awaited_once()
