"""
Cover for the contract term window on ContractRepositoryImpl.

The FE has offered a renewal window ("Renews in 30 days", "Already expired")
since before there was anything behind it: the term lived in a `period` JSON
blob, unfilterable in SQL, and the FE filter read a `renewal_date` field that
does not exist on the wire, so it matched nothing in every window.

The term is now two indexed columns and the window is a real range scan.
`ends_from`/`ends_to` are absolute instants so the caller decides what "30 days"
means; `is_auto_renew` separates "renews" from "expires".
"""

from datetime import UTC, datetime
from typing import Any

import pytest

from app.domain.value_objects.core import TenantId
from app.infrastructure.repositories.contract_repository import ContractRepositoryImpl

NOW = datetime(2026, 7, 13, 12, 0, tzinfo=UTC)
HORIZON = datetime(2026, 8, 12, 12, 0, tzinfo=UTC)


class _SpySession:
    async def execute(self, *_args: Any, **_kwargs: Any) -> Any:  # pragma: no cover
        raise AssertionError("querying must be delegated to the base helpers")


@pytest.fixture
def repo() -> ContractRepositoryImpl:
    return ContractRepositoryImpl(_SpySession())


def _sql(conditions: Any) -> list[str]:
    return [str(c) for c in conditions]


class TestEndsConditions:
    def test_no_window_produces_no_conditions(self, repo: ContractRepositoryImpl) -> None:
        assert repo._ends_conditions(None, None) == []

    def test_window_targets_end_date_not_start(self, repo: ContractRepositoryImpl) -> None:
        """A renewal window is about when the term ends."""
        sql = _sql(repo._ends_conditions(NOW, HORIZON))
        assert len(sql) == 2
        assert all("end_date" in s for s in sql)
        assert not any("start_date" in s for s in sql)

    def test_lower_bound_only(self, repo: ContractRepositoryImpl) -> None:
        sql = _sql(repo._ends_conditions(NOW, None))
        assert len(sql) == 1
        assert "end_date >=" in sql[0]

    def test_upper_bound_only_expresses_already_expired(
        self, repo: ContractRepositoryImpl
    ) -> None:
        sql = _sql(repo._ends_conditions(None, NOW))
        assert len(sql) == 1
        assert "end_date <=" in sql[0]


class TestAutoRenewFilter:
    async def _filters(
        self, repo: ContractRepositoryImpl, monkeypatch: pytest.MonkeyPatch, **kwargs: Any
    ) -> dict[str, Any]:
        seen: dict[str, Any] = {}

        async def fake_query_all(**call_kwargs: Any) -> list[Any]:
            seen.update(call_kwargs)
            return []

        monkeypatch.setattr(repo, "_query_all", fake_query_all)
        await repo.list_all(tenant_id=TenantId("t1"), **kwargs)
        return seen["filters"]

    async def test_true_is_filtered(
        self, repo: ContractRepositoryImpl, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        assert (await self._filters(repo, monkeypatch, is_auto_renew=True))[
            "is_auto_renew"
        ] is True

    async def test_false_is_filtered_not_dropped(
        self, repo: ContractRepositoryImpl, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A falsy check here would silently drop the filter."""
        assert (await self._filters(repo, monkeypatch, is_auto_renew=False))[
            "is_auto_renew"
        ] is False

    async def test_unset_is_absent(
        self, repo: ContractRepositoryImpl, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        assert "is_auto_renew" not in await self._filters(repo, monkeypatch)


class TestListAndCountAgree:
    """A count filtered differently from its page is the bug this guards."""

    async def _capture(
        self,
        repo: ContractRepositoryImpl,
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
        await getattr(repo, method)(tenant_id=TenantId("t1"), **kwargs)
        return seen

    async def test_same_window_and_filters_on_both_paths(
        self, repo: ContractRepositoryImpl, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        kwargs = dict(is_auto_renew=True, ends_from=NOW, ends_to=HORIZON)
        listed = await self._capture(repo, monkeypatch, "list_all", **kwargs)
        counted = await self._capture(repo, monkeypatch, "count", **kwargs)
        assert listed["filters"] == counted["filters"]
        assert _sql(listed["extra_conditions"]) == _sql(counted["extra_conditions"])

    async def test_pagination_reaches_sql(
        self, repo: ContractRepositoryImpl, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        seen = await self._capture(
            repo, monkeypatch, "list_all", ends_to=NOW, limit=20, offset=40
        )
        assert seen["limit"] == 20
        assert seen["offset"] == 40
