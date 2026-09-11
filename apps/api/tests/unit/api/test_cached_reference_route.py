"""A cached lookup over HTTP, hit and miss, through the route's response_model.

The cache stores the JSON-able form rather than the model the route built, so
a hit returns a different Python shape from a miss. What has to be identical
is the response body, and only going through FastAPI shows that.
"""

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
import pytest_asyncio
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from app.api.dependencies import get_client_tier_repository
from app.api.routes.client_tiers import router
from app.core.database import get_db
from app.core.exception_handlers import register_exception_handlers
from app.core.reference_cache import InProcessBackend, set_backend
from app.core.security import TokenData, get_current_user


def _tier(code: str = "GOLD", sort_order: int = 1):
    return SimpleNamespace(
        id=f"tier-{code}", code=code, name=code.title(), description=None, sort_order=sort_order
    )


@pytest_asyncio.fixture
async def api():
    app = FastAPI()
    app.include_router(router)
    register_exception_handlers(app)
    repo = AsyncMock()
    repo.list_all.return_value = [_tier()]
    app.dependency_overrides[get_client_tier_repository] = lambda: repo
    app.dependency_overrides[get_db] = lambda: AsyncMock()
    app.dependency_overrides[get_current_user] = lambda: TokenData(
        user_id="u1", tenant_id="t1", role="Admin"
    )
    set_backend(InProcessBackend())
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield SimpleNamespace(http=client, repo=repo, app=app)
    set_backend(None)


@pytest.mark.asyncio
async def test_a_hit_returns_the_same_body_as_the_miss_that_filled_it(api):
    first = await api.http.get("/client-tiers")
    second = await api.http.get("/client-tiers")

    assert first.status_code == 200, first.text
    assert second.status_code == 200, second.text
    assert first.json() == second.json()
    assert first.json() == [
        {"id": "tier-GOLD", "code": "GOLD", "name": "Gold", "description": None, "sort_order": 1}
    ]


@pytest.mark.asyncio
async def test_the_second_call_does_not_reach_the_repository(api):
    await api.http.get("/client-tiers")
    await api.http.get("/client-tiers")

    api.repo.list_all.assert_awaited_once()


@pytest.mark.asyncio
async def test_a_different_query_param_is_a_different_entry(api):
    await api.http.get("/client-tiers?active_only=true")
    await api.http.get("/client-tiers?active_only=false")

    assert api.repo.list_all.await_count == 2
