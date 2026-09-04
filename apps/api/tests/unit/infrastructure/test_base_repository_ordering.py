"""
Regression cover for the ORDER BY that `_query_all` builds.

LIMIT/OFFSET over a result set with no total order lets the database place one
row on two pages and skip another, and `created_at` is not unique, so a page
boundary that lands inside a group of rows sharing a timestamp used to be
arbitrary. An unknown `sort_by` was worse: `hasattr` failed, no ORDER BY was
emitted at all, and every page was a fresh arbitrary slice. These tests pin the
id column as the final sort key in both cases.

`_count_all` is checked alongside because a count built from a different filter
set than its page produces a total the caller can never page to.
"""

from typing import Any

import pytest

from app.infrastructure.repositories.contract_repository import ContractRepositoryImpl

TENANT = "tenant_abc"


class _Result:
    def scalars(self) -> "_Result":
        return self

    def all(self) -> list[Any]:
        return []

    def scalar(self) -> int:
        return 0


class _CapturingSession:
    """Records the statements a repository builds instead of executing them."""

    def __init__(self) -> None:
        self.statements: list[Any] = []

    async def execute(self, statement: Any, *_args: Any, **_kwargs: Any) -> _Result:
        self.statements.append(statement)
        return _Result()


@pytest.fixture
def session() -> _CapturingSession:
    return _CapturingSession()


@pytest.fixture
def repo(session: _CapturingSession) -> ContractRepositoryImpl:
    return ContractRepositoryImpl(session)


def _sql(session: _CapturingSession) -> str:
    assert len(session.statements) == 1
    return " ".join(str(session.statements[0]).split())


class TestOrdering:
    async def test_requested_column_is_followed_by_the_id(
        self, repo: ContractRepositoryImpl, session: _CapturingSession
    ) -> None:
        await repo._query_all(TENANT, sort_by="created_at", sort_desc=True)
        assert "ORDER BY contracts.created_at DESC, contracts.id DESC" in _sql(session)

    async def test_ascending_applies_to_the_tiebreaker_too(
        self, repo: ContractRepositoryImpl, session: _CapturingSession
    ) -> None:
        await repo._query_all(TENANT, sort_by="created_at", sort_desc=False)
        assert "ORDER BY contracts.created_at ASC, contracts.id ASC" in _sql(session)

    async def test_a_non_default_sort_column_is_honoured(
        self, repo: ContractRepositoryImpl, session: _CapturingSession
    ) -> None:
        await repo._query_all(TENANT, sort_by="end_date", sort_desc=True)
        assert "ORDER BY contracts.end_date DESC, contracts.id DESC" in _sql(session)

    async def test_unknown_column_still_produces_a_total_order(
        self, repo: ContractRepositoryImpl, session: _CapturingSession
    ) -> None:
        await repo._query_all(TENANT, sort_by="definitely_not_a_column")
        sql = _sql(session)
        assert "ORDER BY contracts.id DESC" in sql

    @pytest.mark.parametrize("sort_by", ["", "created_at; DROP TABLE contracts", "../id"])
    async def test_hostile_sort_values_never_reach_the_sql(
        self, repo: ContractRepositoryImpl, session: _CapturingSession, sort_by: str
    ) -> None:
        """sort_by comes straight from a query param, so it must be a column lookup."""
        await repo._query_all(TENANT, sort_by=sort_by)
        sql = _sql(session)
        assert "ORDER BY contracts.id DESC" in sql
        assert "DROP TABLE" not in sql

    async def test_every_page_query_is_ordered(
        self, repo: ContractRepositoryImpl, session: _CapturingSession
    ) -> None:
        await repo._query_all(TENANT, limit=20, offset=40)
        sql = _sql(session)
        assert "ORDER BY" in sql
        assert "LIMIT" in sql
        assert "OFFSET" in sql


class TestTenantAndSoftDeleteScoping:
    async def test_page_is_scoped_to_the_tenant_and_excludes_deleted_rows(
        self, repo: ContractRepositoryImpl, session: _CapturingSession
    ) -> None:
        await repo._query_all(TENANT)
        sql = _sql(session)
        assert "contracts.tenant_id = :tenant_id_1" in sql
        assert "contracts.deleted_at IS NULL" in sql

    async def test_count_is_scoped_the_same_way(
        self, repo: ContractRepositoryImpl, session: _CapturingSession
    ) -> None:
        await repo._count_all(TENANT)
        sql = _sql(session)
        assert "count(" in sql.lower()
        assert "contracts.tenant_id = :tenant_id_1" in sql
        assert "contracts.deleted_at IS NULL" in sql


class TestCountMatchesPage:
    """A count that filters differently than its page breaks pagination."""

    async def test_equality_filters_reach_both_queries(self) -> None:
        page_session, count_session = _CapturingSession(), _CapturingSession()
        filters = {"status": "Active", "payment_status": "Paid"}

        await ContractRepositoryImpl(page_session)._query_all(TENANT, filters=filters)
        await ContractRepositoryImpl(count_session)._count_all(TENANT, filters=filters)

        for sql in (_sql(page_session), _sql(count_session)):
            assert "contracts.status = :status_1" in sql
            assert "contracts.payment_status = :payment_status_1" in sql

    async def test_none_valued_filters_are_dropped_by_both(self) -> None:
        page_session, count_session = _CapturingSession(), _CapturingSession()
        filters: dict[str, Any] = {"status": None}

        await ContractRepositoryImpl(page_session)._query_all(TENANT, filters=filters)
        await ContractRepositoryImpl(count_session)._count_all(TENANT, filters=filters)

        for sql in (_sql(page_session), _sql(count_session)):
            # The column is in the SELECT list either way; what must be absent
            # is a predicate on it.
            assert "contracts.status = " not in sql

    async def test_unknown_filter_keys_are_ignored_by_both(self) -> None:
        """A misspelled key must not silently filter one query and not the other."""
        page_session, count_session = _CapturingSession(), _CapturingSession()
        filters = {"stattus": "Active"}

        await ContractRepositoryImpl(page_session)._query_all(TENANT, filters=filters)
        await ContractRepositoryImpl(count_session)._count_all(TENANT, filters=filters)

        for sql in (_sql(page_session), _sql(count_session)):
            assert "stattus" not in sql

    async def test_search_reaches_both_queries(self) -> None:
        page_session, count_session = _CapturingSession(), _CapturingSession()
        kwargs: dict[str, Any] = {"search": "acme", "search_fields": ["termination_reason"]}

        await ContractRepositoryImpl(page_session)._query_all(TENANT, **kwargs)
        await ContractRepositoryImpl(count_session)._count_all(TENANT, **kwargs)

        for sql in (_sql(page_session), _sql(count_session)):
            assert "lower(contracts.termination_reason) like lower(" in sql.lower()

    async def test_search_without_fields_filters_nothing(self) -> None:
        session = _CapturingSession()
        await ContractRepositoryImpl(session)._query_all(TENANT, search="acme")
        assert "LIKE" not in _sql(session).upper()
