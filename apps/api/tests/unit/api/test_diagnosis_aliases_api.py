"""Legacy spellings can be mapped without shipping a migration.

Adding an alias used to mean writing Alembic, which is why the values awaiting
a clinical decision stayed unmapped and kept failing the import they were meant
to feed. These cover the routes that close that loop.
"""

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest_asyncio
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from app.api.dependencies import get_diagnosis_repository
from app.api.routes.diagnoses import router
from app.core.authorization import require_platform_admin
from app.core.database import get_db
from app.core.exception_handlers import register_exception_handlers
from app.core.security import TokenData, get_current_user


def _alias(**changes):
    base = {
        "id": "dxa_1",
        "raw_value": "Personality",
        "normalised_key": "personality",
        "diagnosis_type_id": "type-1",
        "diagnosis_id": None,
        "source": "reference_extract_2026_09",
        "confidence": "inferred",
    }
    return SimpleNamespace(**{**base, **changes})


@pytest_asyncio.fixture
async def api():
    app = FastAPI()
    app.include_router(router)
    register_exception_handlers(app)
    state = SimpleNamespace(
        repo=AsyncMock(),
        db=AsyncMock(),
        user=TokenData(user_id="u1", tenant_id="t1", role="Admin"),
    )
    state.repo.list_types.return_value = [SimpleNamespace(id="type-1", code="MENTAL_ILL_HEALTH")]
    state.repo.list_diagnoses.return_value = [
        SimpleNamespace(id="dx-1", type_id="type-1", code="DEPRESSION"),
        SimpleNamespace(id="dx-other", type_id="type-2", code="BURNOUT"),
    ]
    state.repo.list_aliases.return_value = [_alias()]
    state.repo.upsert_alias.return_value = _alias()
    app.dependency_overrides[get_diagnosis_repository] = lambda: state.repo
    app.dependency_overrides[get_db] = lambda: state.db
    app.dependency_overrides[get_current_user] = lambda: state.user
    app.dependency_overrides[require_platform_admin] = lambda: state.user
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as http:
        state.http = http
        yield state


UPSERT = {
    "raw_value": "Personality",
    "diagnosis_type_id": "type-1",
    "source": "clinical_review_2026_09",
}


async def test_an_alias_can_be_mapped_to_a_type_alone(api):
    """Most legacy classifications name a type, not a leaf."""
    response = await api.http.put("/diagnoses/aliases", json=UPSERT)

    assert response.status_code == 200, response.text
    assert response.json()["diagnosis_id"] is None
    kwargs = api.repo.upsert_alias.call_args.kwargs
    assert kwargs["diagnosis_type_id"] == "type-1"
    assert kwargs["diagnosis_id"] is None


async def test_confidence_defaults_to_inferred(api):
    """An unreviewed mapping must stay filterable, so it cannot default to confirmed."""
    await api.http.put("/diagnoses/aliases", json=UPSERT)

    assert api.repo.upsert_alias.call_args.kwargs["confidence"] == "inferred"


async def test_confidence_can_be_confirmed_once_signed_off(api):
    await api.http.put("/diagnoses/aliases", json={**UPSERT, "confidence": "confirmed"})

    assert api.repo.upsert_alias.call_args.kwargs["confidence"] == "confirmed"


async def test_an_unknown_confidence_is_refused(api):
    response = await api.http.put("/diagnoses/aliases", json={**UPSERT, "confidence": "maybe"})

    assert response.status_code == 422
    api.repo.upsert_alias.assert_not_awaited()


async def test_an_alias_cannot_point_at_a_missing_type(api):
    response = await api.http.put(
        "/diagnoses/aliases", json={**UPSERT, "diagnosis_type_id": "nope"}
    )

    assert response.status_code == 404
    api.repo.upsert_alias.assert_not_awaited()


async def test_an_alias_cannot_point_at_a_missing_diagnosis(api):
    response = await api.http.put("/diagnoses/aliases", json={**UPSERT, "diagnosis_id": "nope"})

    assert response.status_code == 404
    api.repo.upsert_alias.assert_not_awaited()


async def test_a_leaf_must_belong_to_the_named_type(api):
    """Otherwise the alias resolves to a pair that contradicts itself."""
    response = await api.http.put("/diagnoses/aliases", json={**UPSERT, "diagnosis_id": "dx-other"})

    assert response.status_code == 422
    api.repo.upsert_alias.assert_not_awaited()


async def test_aliases_can_be_filtered_to_the_unreviewed_ones(api):
    response = await api.http.get("/diagnoses/aliases", params={"confidence": "inferred"})

    assert response.status_code == 200, response.text
    assert api.repo.list_aliases.call_args.kwargs["confidence"] == "inferred"
    assert response.json()[0]["raw_value"] == "Personality"


async def test_listing_without_a_filter_returns_every_alias(api):
    response = await api.http.get("/diagnoses/aliases")

    assert response.status_code == 200, response.text
    assert api.repo.list_aliases.call_args.kwargs["confidence"] is None
