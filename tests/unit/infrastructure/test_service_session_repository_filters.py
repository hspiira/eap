"""
Cover for the scheduled_at window on ServiceSessionRepositoryImpl.

The window exists so the sessions list can filter by date range in SQL. It used
to be done in the browser over one fetched page, which disagreed with the total
the same request returned. Callers pass absolute instants rather than a named
window, so the caller's timezone decides "today" and the server stays
timezone-agnostic.
"""

from datetime import UTC, datetime
from typing import Any

import pytest

from app.domain.value_objects.core import TenantId
from app.infrastructure.repositories.service_session_repository import (
    ServiceSessionRepositoryImpl,
)

FROM = datetime(2026, 7, 13, 0, 0, tzinfo=UTC)
TO = datetime(2026, 7, 13, 23, 59, 59, tzinfo=UTC)


class _SpySession:
    async def execute(self, *_args: Any, **_kwargs: Any) -> Any:  # pragma: no cover
        raise AssertionError("querying must be delegated to the base helpers")


@pytest.fixture
def repo() -> ServiceSessionRepositoryImpl:
    return ServiceSessionRepositoryImpl(_SpySession())


def _sql(conditions: Any) -> list[str]:
    return [str(c) for c in conditions]


class TestScheduledConditions:
    def test_no_bounds_produce_no_conditions(self, repo: ServiceSessionRepositoryImpl) -> None:
        assert repo._scheduled_conditions(None, None) == []

    def test_lower_bound_only(self, repo: ServiceSessionRepositoryImpl) -> None:
        sql = _sql(repo._scheduled_conditions(FROM, None))
        assert len(sql) == 1
        assert "scheduled_at >=" in sql[0]

    def test_upper_bound_only(self, repo: ServiceSessionRepositoryImpl) -> None:
        sql = _sql(repo._scheduled_conditions(None, TO))
        assert len(sql) == 1
        assert "scheduled_at <=" in sql[0]

    def test_both_bounds_are_inclusive(self, repo: ServiceSessionRepositoryImpl) -> None:
        sql = _sql(repo._scheduled_conditions(FROM, TO))
        assert len(sql) == 2
        assert any("scheduled_at >=" in s for s in sql)
        assert any("scheduled_at <=" in s for s in sql)


class TestWindowReachesSql:
    async def _capture(
        self,
        repo: ServiceSessionRepositoryImpl,
        monkeypatch: pytest.MonkeyPatch,
        method: str,
        **kwargs: Any,
    ) -> dict[str, Any]:
        seen: dict[str, Any] = {}
        target = "_query_all" if method == "list_all" else "_count_all"

        async def fake(**call_kwargs: Any) -> Any:
            seen.update(call_kwargs)
            return [] if method == "list_all" else 0

        monkeypatch.setattr(repo, target, fake)
        await getattr(repo, method)(tenant_id=TenantId("tenant-1"), **kwargs)
        return seen

    async def test_list_all_passes_window_as_sql(
        self, repo: ServiceSessionRepositoryImpl, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        seen = await self._capture(
            repo, monkeypatch, "list_all", scheduled_from=FROM, scheduled_to=TO
        )
        assert len(list(seen["extra_conditions"])) == 2

    async def test_count_applies_the_same_window(
        self, repo: ServiceSessionRepositoryImpl, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A count filtered differently from its page is the bug this prevents."""
        seen = await self._capture(repo, monkeypatch, "count", scheduled_from=FROM, scheduled_to=TO)
        assert _sql(seen["extra_conditions"]) == _sql(repo._scheduled_conditions(FROM, TO))

    async def test_list_and_count_agree_on_base_filters(
        self, repo: ServiceSessionRepositoryImpl, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        listed = await self._capture(
            repo, monkeypatch, "list_all", scheduled_from=FROM, scheduled_to=TO
        )
        counted = await self._capture(
            repo, monkeypatch, "count", scheduled_from=FROM, scheduled_to=TO
        )
        assert listed["filters"] == counted["filters"]

    async def test_unbounded_window_adds_no_conditions(
        self, repo: ServiceSessionRepositoryImpl, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        seen = await self._capture(repo, monkeypatch, "list_all")
        assert list(seen["extra_conditions"]) == []

    async def test_pagination_still_reaches_sql(
        self, repo: ServiceSessionRepositoryImpl, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        seen = await self._capture(
            repo, monkeypatch, "list_all", scheduled_from=FROM, limit=20, offset=40
        )
        assert seen["limit"] == 20
        assert seen["offset"] == 40
