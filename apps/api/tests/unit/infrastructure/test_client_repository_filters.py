"""Regression coverage for the client list's parent-client filter."""

from typing import Any

import pytest

from app.domain.value_objects.core import ClientId, TenantId
from app.infrastructure.repositories.client_repository import ClientRepositoryImpl


class _SpySession:
    async def execute(self, *_args: Any, **_kwargs: Any) -> Any:  # pragma: no cover
        raise AssertionError("querying must be delegated to the base helpers")


@pytest.fixture
def repo() -> ClientRepositoryImpl:
    return ClientRepositoryImpl(_SpySession())


async def test_parent_client_filter_reaches_the_page_query(
    repo: ClientRepositoryImpl, monkeypatch: pytest.MonkeyPatch
) -> None:
    seen: dict[str, Any] = {}

    async def fake_query_all(**kwargs: Any) -> list[Any]:
        seen.update(kwargs)
        return []

    monkeypatch.setattr(repo, "_query_all", fake_query_all)
    await repo.list_all(TenantId("tenant-1"), parent_client_id=ClientId("parent-1"))

    assert seen["filters"]["parent_client_id"] == "parent-1"


async def test_parent_client_filter_reaches_the_count_query(
    repo: ClientRepositoryImpl, monkeypatch: pytest.MonkeyPatch
) -> None:
    seen: dict[str, Any] = {}

    async def fake_count(**kwargs: Any) -> int:
        seen.update(kwargs)
        return 0

    monkeypatch.setattr(repo, "_count_all", fake_count)
    await repo.count(TenantId("tenant-1"), parent_client_id=ClientId("parent-1"))

    assert seen["filters"]["parent_client_id"] == "parent-1"
