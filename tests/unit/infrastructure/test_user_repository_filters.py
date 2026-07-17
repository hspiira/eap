"""
Regression cover for the `is_email_verified` filter on UserRepositoryImpl.list_all.

The filter used to be applied in Python *after* `_query_all` had already applied
LIMIT/OFFSET in SQL. That silently dropped rows from the requested page (a page of
20 could come back with 12 items) while `count()` applied the same filter in SQL and
returned the true total, so callers rendered "12 of 57" and paginated over a total
they could never reach. These tests pin the filter to the SQL layer.
"""

from typing import Any

import pytest

from app.domain.value_objects.core import TenantId
from app.infrastructure.repositories.user_repository import UserRepositoryImpl


class _SpySession:
    """Stands in for AsyncSession; list_all is not expected to touch it directly."""

    async def execute(self, *_args: Any, **_kwargs: Any) -> Any:  # pragma: no cover
        raise AssertionError("list_all must delegate querying to _query_all")


@pytest.fixture
def repo() -> UserRepositoryImpl:
    return UserRepositoryImpl(_SpySession())


def _condition_sql(conditions: list[Any]) -> list[str]:
    return [str(c) for c in conditions]


class TestVerifiedConditions:
    def test_none_produces_no_condition(self, repo: UserRepositoryImpl) -> None:
        assert repo._verified_conditions(None) == []

    def test_true_filters_on_timestamp_present(self, repo: UserRepositoryImpl) -> None:
        sql = _condition_sql(repo._verified_conditions(True))
        assert len(sql) == 1
        assert "email_verified_at IS NOT NULL" in sql[0]

    def test_false_filters_on_timestamp_absent(self, repo: UserRepositoryImpl) -> None:
        sql = _condition_sql(repo._verified_conditions(False))
        assert len(sql) == 1
        assert "email_verified_at IS NULL" in sql[0]


class TestListAllPushesFilterToSql:
    """list_all must hand the flag to _query_all as SQL, never post-filter the page."""

    async def _capture(
        self, repo: UserRepositoryImpl, monkeypatch: pytest.MonkeyPatch, **kwargs: Any
    ) -> dict[str, Any]:
        seen: dict[str, Any] = {}

        async def fake_query_all(**call_kwargs: Any) -> list[Any]:
            seen.update(call_kwargs)
            # Deliberately return rows the old Python filter would have discarded.
            return ["row-a", "row-b"]

        monkeypatch.setattr(repo, "_query_all", fake_query_all)
        result = await repo.list_all(tenant_id=TenantId("tenant-1"), **kwargs)
        seen["__result__"] = result
        return seen

    async def test_verified_true_is_passed_as_sql_condition(
        self, repo: UserRepositoryImpl, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        seen = await self._capture(repo, monkeypatch, is_email_verified=True)
        sql = _condition_sql(list(seen["extra_conditions"]))
        assert any("email_verified_at IS NOT NULL" in s for s in sql)

    async def test_verified_false_is_passed_as_sql_condition(
        self, repo: UserRepositoryImpl, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        seen = await self._capture(repo, monkeypatch, is_email_verified=False)
        sql = _condition_sql(list(seen["extra_conditions"]))
        assert any("email_verified_at IS NULL" in s for s in sql)

    async def test_unset_flag_adds_no_condition(
        self, repo: UserRepositoryImpl, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        seen = await self._capture(repo, monkeypatch)
        assert list(seen["extra_conditions"]) == []

    async def test_page_is_returned_intact(
        self, repo: UserRepositoryImpl, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """
        The regression itself: rows coming back from SQL must not be filtered again.
        Under the old implementation these plain strings would have been dropped,
        because `e.is_email_verified` was compared against the requested flag.
        """
        seen = await self._capture(repo, monkeypatch, is_email_verified=True, limit=2)
        assert seen["__result__"] == ["row-a", "row-b"]

    async def test_pagination_args_reach_sql(
        self, repo: UserRepositoryImpl, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        seen = await self._capture(
            repo, monkeypatch, is_email_verified=True, limit=20, offset=40
        )
        assert seen["limit"] == 20
        assert seen["offset"] == 40


class TestTwoFactorFilter:
    """`is_two_factor_enabled` is a plain column, so it rides the equality filters."""

    async def _capture_filters(
        self, repo: UserRepositoryImpl, monkeypatch: pytest.MonkeyPatch, **kwargs: Any
    ) -> dict[str, Any]:
        seen: dict[str, Any] = {}

        async def fake_query_all(**call_kwargs: Any) -> list[Any]:
            seen.update(call_kwargs)
            return []

        monkeypatch.setattr(repo, "_query_all", fake_query_all)
        await repo.list_all(tenant_id=TenantId("tenant-1"), **kwargs)
        return seen["filters"]

    async def test_enabled_true_is_filtered_in_sql(
        self, repo: UserRepositoryImpl, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        filters = await self._capture_filters(
            repo, monkeypatch, is_two_factor_enabled=True
        )
        assert filters["is_two_factor_enabled"] is True

    async def test_enabled_false_is_filtered_in_sql(
        self, repo: UserRepositoryImpl, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """False must still filter — a falsy check here would drop the filter."""
        filters = await self._capture_filters(
            repo, monkeypatch, is_two_factor_enabled=False
        )
        assert filters["is_two_factor_enabled"] is False

    async def test_unset_flag_is_absent_from_filters(
        self, repo: UserRepositoryImpl, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        filters = await self._capture_filters(repo, monkeypatch)
        assert "is_two_factor_enabled" not in filters
