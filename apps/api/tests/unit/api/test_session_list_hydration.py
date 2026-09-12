"""The session list carries names, not just ids, and rejects unknown sorts.

C1 and C2 of docs/handoffs/SESSIONS_IMPLEMENTATION.md. The list returned bare identifiers, so
the UI issued one member fetch per row, and a company-wide session, which has
no member, could not name its client at all. The base repository also ignored
an unknown sort column and quietly sorted by id, so a typo produced a silently
wrong order instead of an error.
"""

from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
import pytest_asyncio
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from app.api.dependencies import (
    get_service_session_repository,
    get_session_attribution_reader,
    get_session_name_reader,
)
from app.api.routes.service_sessions import router
from app.core.authorization import get_service_session_for_current_tenant
from app.core.database import get_db
from app.core.exception_handlers import register_exception_handlers
from app.core.security import TokenData, get_current_user
from app.domain.entities.service_session import ServiceSessionEntity
from app.domain.enums import SessionAttendance, SessionStatus
from app.domain.repositories.session_name_reader import SessionNames
from app.domain.value_objects.core import (
    ClientId,
    EligibleMemberId,
    ProviderId,
    ServiceId,
    SessionId,
    TenantId,
)

NOW = datetime(2026, 1, 5, 9, 0, tzinfo=UTC)


def _session(session_id: str, member: str | None) -> ServiceSessionEntity:
    return ServiceSessionEntity(
        id=SessionId(session_id),
        tenant_id=TenantId("t1"),
        service_id=ServiceId("svc-1"),
        provider_id=ProviderId("prv-1"),
        client_id=ClientId("cli-1"),
        attendance=(SessionAttendance.INDIVIDUAL if member else SessionAttendance.COMPANY_WIDE),
        member_id=EligibleMemberId(member) if member else None,
        scheduled_at=NOW,
        status=SessionStatus.SCHEDULED,
        created_at=NOW,
        updated_at=NOW,
        reschedule_count=0,
        headcount=None if member else 40,
    )


@pytest_asyncio.fixture
async def api():
    app = FastAPI()
    app.include_router(router)
    register_exception_handlers(app)
    state = SimpleNamespace(sessions=AsyncMock(), names=AsyncMock(), attribution=AsyncMock())
    page = [_session("s1", "mem-1"), _session("s2", None)]
    state.sessions.list_all.return_value = page
    state.sessions.count.return_value = 2
    # The ordinal is derived per page in one query; an unset mock returns a
    # coroutine the response model cannot read.
    state.sessions.session_ordinals.return_value = {}
    state.sessions.get_by_member_id.return_value = page
    state.sessions.get_by_provider_id.return_value = page
    state.sessions.get_by_service_id.return_value = page
    state.attribution.organisation_ids_by_affiliation.return_value = {}
    state.names.names_for.return_value = SessionNames(
        clients={"cli-1": "Stanbic Bank"},
        members={"mem-1": "Amina Namukasa"},
        providers={"prv-1": "Moses Mpanga"},
        services={"svc-1": "Individual Counselling"},
    )
    for dep, value in {
        get_service_session_repository: state.sessions,
        get_session_attribution_reader: state.attribution,
        get_session_name_reader: state.names,
        get_db: AsyncMock(),
    }.items():
        app.dependency_overrides[dep] = (lambda v: lambda: v)(value)
    app.dependency_overrides[get_current_user] = lambda: TokenData(
        user_id="u1", tenant_id="t1", role="Admin"
    )
    state.app = app
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as http:
        state.http = http
        yield state


def _use_session(api, session: ServiceSessionEntity) -> None:
    api.app.dependency_overrides[get_service_session_for_current_tenant] = lambda: session


class TestHydratedNames:
    async def test_the_list_carries_names_for_every_id_it_returns(self, api):
        response = await api.http.get("/service-sessions/?tenant_id=t1")

        assert response.status_code == 200, response.text
        first = response.json()["items"][0]
        assert first["client_name"] == "Stanbic Bank"
        assert first["member_display_label"] == "Amina Namukasa"
        assert first["provider_display_name"] == "Moses Mpanga"
        assert first["service_name"] == "Individual Counselling"

    async def test_a_company_wide_session_names_its_client_despite_having_no_member(self, api):
        response = await api.http.get("/service-sessions/?tenant_id=t1")

        talk = response.json()["items"][1]
        assert talk["member_id"] is None
        assert talk["member_display_label"] is None
        assert talk["client_name"] == "Stanbic Bank"

    async def test_names_are_resolved_once_per_page_not_once_per_row(self, api):
        await api.http.get("/service-sessions/?tenant_id=t1")

        assert api.names.names_for.await_count == 1
        kwargs = api.names.names_for.await_args.kwargs
        assert kwargs["member_ids"] == ["mem-1"]
        assert set(kwargs["client_ids"]) == {"cli-1"}

    async def test_an_unresolved_id_yields_an_absent_name_not_an_error(self, api):
        api.names.names_for.return_value = SessionNames()

        response = await api.http.get("/service-sessions/?tenant_id=t1")

        assert response.status_code == 200, response.text
        assert response.json()["items"][0]["client_name"] is None


class TestDetailNames:
    """The detail response carries the names the list does.

    It did not, so the detail page fetched the member, the practitioner and the
    service separately to fill in what the row beside it already showed.
    """

    async def test_a_single_session_carries_every_name(self, api):
        _use_session(api, _session("s1", "mem-1"))

        response = await api.http.get("/service-sessions/s1")

        assert response.status_code == 200, response.text
        body = response.json()
        assert body["client_name"] == "Stanbic Bank"
        assert body["member_display_label"] == "Amina Namukasa"
        assert body["provider_display_name"] == "Moses Mpanga"
        assert body["service_name"] == "Individual Counselling"

    async def test_a_company_wide_session_names_everything_but_its_absent_member(self, api):
        _use_session(api, _session("s2", None))

        response = await api.http.get("/service-sessions/s2")

        assert response.status_code == 200, response.text
        body = response.json()
        assert body["member_id"] is None
        assert body["member_display_label"] is None
        assert body["client_name"] == "Stanbic Bank"
        assert body["provider_display_name"] == "Moses Mpanga"
        assert body["service_name"] == "Individual Counselling"

    async def test_one_session_costs_one_bulk_resolution_not_one_per_name(self, api):
        _use_session(api, _session("s1", "mem-1"))

        await api.http.get("/service-sessions/s1")

        assert api.names.names_for.await_count == 1
        kwargs = api.names.names_for.await_args.kwargs
        assert kwargs["client_ids"] == ["cli-1"]
        assert kwargs["member_ids"] == ["mem-1"]

    async def test_a_company_wide_session_asks_for_no_member_name(self, api):
        _use_session(api, _session("s2", None))

        await api.http.get("/service-sessions/s2")

        assert api.names.names_for.await_args.kwargs["member_ids"] == []


class TestScopedListNames:
    @pytest.mark.parametrize(
        ("path", "repository_method"),
        [
            ("member/mem-1", "get_by_member_id"),
            ("provider/prv-1", "get_by_provider_id"),
            ("service/svc-1", "get_by_service_id"),
        ],
    )
    async def test_a_scoped_list_carries_names(self, api, path, repository_method):
        response = await api.http.get(f"/service-sessions/{path}?tenant_id=t1")

        assert response.status_code == 200, response.text
        assert getattr(api.sessions, repository_method).await_count == 1
        first = response.json()[0]
        assert first["client_name"] == "Stanbic Bank"
        assert first["member_display_label"] == "Amina Namukasa"
        assert first["provider_display_name"] == "Moses Mpanga"
        assert first["service_name"] == "Individual Counselling"
        assert api.names.names_for.await_count == 1


class TestSortAllowlist:
    async def test_an_unknown_sort_column_is_rejected_not_silently_ignored(self, api):
        response = await api.http.get("/service-sessions/?tenant_id=t1&sort_by=notes")

        assert response.status_code == 422, response.text
        assert "sort_by must be one of" in response.text
        api.sessions.list_all.assert_not_awaited()

    @pytest.mark.parametrize("column", ["scheduled_at", "attendance", "session_number"])
    async def test_a_listed_column_sorts(self, api, column):
        response = await api.http.get(f"/service-sessions/?tenant_id=t1&sort_by={column}")

        assert response.status_code == 200, response.text
        assert api.sessions.list_all.await_args.kwargs["sort_by"] == column


class TestOperatorFilters:
    """C4: the dimensions an operator slices by reach the repository."""

    @pytest.mark.parametrize(
        ("param", "value", "kwarg"),
        [
            ("session_type", "Physical", "session_type"),
            ("category", "Group", "category"),
            ("clinical_outcome", "Terminated", "clinical_outcome"),
            ("provider_id", "prv-1", "provider_id"),
        ],
    )
    async def test_a_filter_is_passed_to_both_list_and_count(self, api, param, value, kwarg):
        response = await api.http.get(f"/service-sessions/?tenant_id=t1&{param}={value}")

        assert response.status_code == 200, response.text
        listed = api.sessions.list_all.await_args.kwargs[kwarg]
        counted = api.sessions.count.await_args.kwargs[kwarg]
        assert listed is not None and counted is not None
        assert str(getattr(listed, "value", listed)) == value
        assert str(getattr(counted, "value", counted)) == value

    async def test_an_invalid_filter_value_is_rejected(self, api):
        response = await api.http.get("/service-sessions/?tenant_id=t1&category=Webinar")

        assert response.status_code == 422, response.text
        api.sessions.list_all.assert_not_awaited()
