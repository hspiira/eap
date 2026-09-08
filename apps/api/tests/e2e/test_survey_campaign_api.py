"""Server-side paging and filtering on GET /survey-campaigns."""

from typing import Any

import pytest
import pytest_asyncio
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio

SECRET = "s" * 32


async def _create(client: AsyncClient, name: str, client_id: str) -> dict[str, Any]:
    response = await client.post(
        "/survey-campaigns",
        json={
            "client_id": client_id,
            "name": name,
            "source": "GoogleForms",
            "external_form_id": f"form-{name}",
            "webhook_secret": SECRET,
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


@pytest_asyncio.fixture
async def campaigns(client: AsyncClient, test_tenant: dict) -> list[dict[str, Any]]:
    """Five campaigns: three for client-a (two activated), two for client-b."""
    rows = [await _create(client, f"Pulse check {i}", "client-a") for i in range(3)]
    rows += [await _create(client, f"Exit survey {i}", "client-b") for i in range(2)]
    for row in rows[:2]:
        activated = await client.post(f"/survey-campaigns/{row['id']}/activate")
        assert activated.status_code == 200, activated.text
    return rows


async def test_list_returns_the_standard_envelope(
    client: AsyncClient, campaigns: list[dict]
) -> None:
    body = (await client.get("/survey-campaigns")).json()

    assert set(body) == {"items", "total", "page", "limit", "has_more"}
    assert body["total"] == 5
    assert body["page"] == 1
    assert body["limit"] == 20
    assert body["has_more"] is False
    assert len(body["items"]) == 5


async def test_pages_are_sliced_server_side(client: AsyncClient, campaigns: list[dict]) -> None:
    first = (await client.get("/survey-campaigns", params={"page": 1, "limit": 2})).json()
    second = (await client.get("/survey-campaigns", params={"page": 2, "limit": 2})).json()
    third = (await client.get("/survey-campaigns", params={"page": 3, "limit": 2})).json()

    assert [len(p["items"]) for p in (first, second, third)] == [2, 2, 1]
    assert [p["total"] for p in (first, second, third)] == [5, 5, 5]
    assert [p["has_more"] for p in (first, second, third)] == [True, True, False]

    ids = [[item["id"] for item in page["items"]] for page in (first, second, third)]
    assert ids[0] != ids[1]
    assert len({i for page in ids for i in page}) == 5


async def test_status_filter_narrows_items_and_total(
    client: AsyncClient, campaigns: list[dict]
) -> None:
    body = (await client.get("/survey-campaigns", params={"status": "Active"})).json()

    assert body["total"] == 2
    assert {item["status"] for item in body["items"]} == {"Active"}


async def test_total_reflects_the_filter_not_the_page(
    client: AsyncClient, campaigns: list[dict]
) -> None:
    body = (
        await client.get("/survey-campaigns", params={"client_id": "client-a", "limit": 1})
    ).json()

    assert body["total"] == 3
    assert len(body["items"]) == 1
    assert body["has_more"] is True


async def test_search_matches_the_campaign_name(client: AsyncClient, campaigns: list[dict]) -> None:
    body = (await client.get("/survey-campaigns", params={"search": "exit"})).json()

    assert body["total"] == 2
    assert all("Exit" in item["name"] for item in body["items"])
