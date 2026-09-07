"""Global search: authentication, tenant isolation, projection and bounds.

Search must not see further than the modules it searches. These cases prove
the gate runs before any query, that the response carries only the projected
fields, that each category is bounded, and that one category failing is
reported as a failure rather than as an empty result.
"""

import logging
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
import pytest_asyncio
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from app.api.dependencies import get_client_repository, get_provider_repository
from app.api.dependencies.provider_network import get_provider_organisation_repository
from app.api.routes.search import router
from app.core.database import get_db
from app.core.exception_handlers import register_exception_handlers
from app.core.security import TokenData, get_current_user
from app.domain.entities.client import ClientEntity
from app.domain.entities.provider import ProviderEntity
from app.domain.entities.provider_organisation import ProviderOrganisationEntity
from app.domain.enums import (
    AccreditationStatus,
    BaseStatus,
    PanelStatus,
    ProviderTier,
    UgandaRegion,
)
from app.domain.value_objects.core import (
    ClientId,
    ContactInfo,
    ProviderId,
    ProviderProfile,
    TenantId,
)
from app.domain.value_objects.provider_network import ProviderOrganisationId
from app.shared.utils.datetime import utc_now

TENANT = "t-1"
OTHER_TENANT = "t-2"
SECRET_TERM = "nakato"


def _client(index: int = 1) -> ClientEntity:
    now = utc_now()
    return ClientEntity(
        id=ClientId(f"cl-{index}"),
        tenant_id=TenantId(TENANT),
        name=f"Acme {index}",
        code=f"AC{index}",
        contact_info=ContactInfo(phone="+256700000000"),
        status=BaseStatus.ACTIVE,
        is_verified=True,
        created_at=now,
        updated_at=now,
    )


def _provider(index: int = 1) -> ProviderEntity:
    now = utc_now()
    return ProviderEntity(
        id=ProviderId(f"pr-{index}"),
        tenant_id=TenantId(TENANT),
        status=BaseStatus.ACTIVE,
        display_name=f"Alice Nakato {index}",
        created_at=now,
        updated_at=now,
        contact_email="alice@example.com",
        contact_phone="+256700000001",
        provider_profile=ProviderProfile(
            tier=ProviderTier.T1,
            region=UgandaRegion.CENTRAL,
            accreditation_status=AccreditationStatus.ACCREDITED,
            panel_status=PanelStatus.ACTIVE,
            bio="A private biography that search must not disclose.",
        ),
    )


def _organisation(index: int = 1) -> ProviderOrganisationEntity:
    now = utc_now()
    return ProviderOrganisationEntity(
        id=ProviderOrganisationId(f"org-{index}"),
        tenant_id=TenantId(TENANT),
        name=f"Firm {index}",
        registration_number=f"REG-{index}",
        created_at=now,
        updated_at=now,
    )


def _build_app(state: SimpleNamespace, *, authenticate: bool = True) -> FastAPI:
    app = FastAPI()
    app.include_router(router)
    register_exception_handlers(app)
    app.dependency_overrides[get_client_repository] = lambda: state.clients
    app.dependency_overrides[get_provider_repository] = lambda: state.providers
    app.dependency_overrides[get_provider_organisation_repository] = lambda: state.organisations
    app.dependency_overrides[get_db] = lambda: state.db
    if authenticate:
        app.dependency_overrides[get_current_user] = lambda: TokenData(
            user_id="u-1", tenant_id=TENANT, role=state.role
        )
    return app


def _state() -> SimpleNamespace:
    state = SimpleNamespace(
        clients=AsyncMock(),
        providers=AsyncMock(),
        organisations=AsyncMock(),
        db=AsyncMock(),
        role="Admin",
    )
    state.clients.list_all.return_value = [_client()]
    state.providers.search.return_value = [_provider()]
    state.organisations.list_organisations.return_value = ([_organisation()], 1)
    return state


@pytest_asyncio.fixture
async def api():
    state = _state()
    app = _build_app(state)
    state.app = app
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as http:
        state.http = http
        yield state


@pytest_asyncio.fixture
async def anonymous():
    state = _state()
    app = _build_app(state, authenticate=False)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as http:
        state.http = http
        yield state


class TestAuthentication:
    async def test_an_anonymous_caller_is_refused(self, anonymous):
        response = await anonymous.http.post(f"/search?tenant_id={TENANT}", json={"q": "acme"})
        assert response.status_code == 401

    async def test_no_query_runs_for_an_anonymous_caller(self, anonymous):
        await anonymous.http.post(f"/search?tenant_id={TENANT}", json={"q": "acme"})
        anonymous.clients.list_all.assert_not_awaited()
        anonymous.providers.search.assert_not_awaited()
        anonymous.organisations.list_organisations.assert_not_awaited()


class TestTenantIsolation:
    async def test_another_tenants_search_is_refused(self, api):
        response = await api.http.post(f"/search?tenant_id={OTHER_TENANT}", json={"q": "acme"})
        assert response.status_code == 403

    async def test_the_gate_runs_before_any_query(self, api):
        """A refusal must not have read another tenant's rows first."""
        await api.http.post(f"/search?tenant_id={OTHER_TENANT}", json={"q": "acme"})
        api.clients.list_all.assert_not_awaited()
        api.providers.search.assert_not_awaited()
        api.organisations.list_organisations.assert_not_awaited()

    async def test_every_query_is_scoped_to_the_authenticated_tenant(self, api):
        await api.http.post(f"/search?tenant_id={TENANT}", json={"q": "acme"})
        assert api.clients.list_all.await_args.kwargs["tenant_id"] == TenantId(TENANT)
        assert api.providers.search.await_args.args[0] == TenantId(TENANT)
        assert api.organisations.list_organisations.await_args.args[0] == TenantId(TENANT)


class TestRoles:
    @pytest.mark.parametrize("role", ["Admin", "User", "Viewer"])
    async def test_every_role_that_may_read_the_lists_may_search(self, api, role):
        """Search reuses list-route access, which Viewers already hold."""
        api.role = role
        response = await api.http.post(f"/search?tenant_id={TENANT}", json={"q": "acme"})
        assert response.status_code == 200, response.text


class TestProjection:
    async def test_each_result_carries_only_the_projected_fields(self, api):
        response = await api.http.post(f"/search?tenant_id={TENANT}", json={"q": "acme"})
        for category in response.json().values():
            for item in category["items"]:
                assert set(item) == {"id", "label", "secondary", "type"}

    async def test_a_practitioner_bio_is_not_disclosed(self, api):
        """A search preview discloses even when the detail route would refuse."""
        body = await api.http.post(f"/search?tenant_id={TENANT}", json={"q": "nakato"})
        assert "biography" not in body.text

    async def test_a_practitioner_contact_email_is_not_disclosed(self, api):
        body = await api.http.post(f"/search?tenant_id={TENANT}", json={"q": "nakato"})
        assert "alice@example.com" not in body.text

    async def test_each_category_labels_its_own_type(self, api):
        body = (await api.http.post(f"/search?tenant_id={TENANT}", json={"q": "ac"})).json()
        assert body["clients"]["items"][0]["type"] == "client"
        assert body["practitioners"]["items"][0]["type"] == "practitioner"
        assert body["provider_organisations"]["items"][0]["type"] == "provider_organisation"

    async def test_the_secondary_label_disambiguates_a_record(self, api):
        body = (await api.http.post(f"/search?tenant_id={TENANT}", json={"q": "ac"})).json()
        assert body["clients"]["items"][0]["secondary"] == "AC1"
        assert body["practitioners"]["items"][0]["secondary"] == "T1 · Central"
        assert body["provider_organisations"]["items"][0]["secondary"] == "REG-1"

    async def test_a_practitioner_without_a_profile_still_resolves(self, api):
        """A 409 on one incomplete record must not fail the whole search."""
        provider = _provider()
        provider.provider_profile = None
        api.providers.search.return_value = [provider]
        response = await api.http.post(f"/search?tenant_id={TENANT}", json={"q": "nakato"})
        assert response.status_code == 200
        assert response.json()["practitioners"]["items"][0]["secondary"] is None


class TestBounds:
    async def test_results_are_truncated_to_the_limit(self, api):
        api.clients.list_all.return_value = [_client(i) for i in range(1, 8)]
        body = (
            await api.http.post(f"/search?tenant_id={TENANT}", json={"q": "acme", "limit": 3})
        ).json()
        assert len(body["clients"]["items"]) == 3
        assert body["clients"]["has_more"] is True

    async def test_has_more_is_false_when_the_page_is_not_full(self, api):
        api.clients.list_all.return_value = [_client(1), _client(2)]
        body = (
            await api.http.post(f"/search?tenant_id={TENANT}", json={"q": "acme", "limit": 5})
        ).json()
        assert body["clients"]["has_more"] is False

    async def test_each_category_over_fetches_by_one_row_only(self, api):
        """has_more comes from an extra row, not from a count over the dataset."""
        await api.http.post(f"/search?tenant_id={TENANT}", json={"q": "acme", "limit": 5})
        assert api.clients.list_all.await_args.kwargs["limit"] == 6
        assert api.providers.search.await_args.args[1].limit == 6
        assert api.organisations.list_organisations.await_args.kwargs["limit"] == 6

    async def test_no_count_is_returned(self, api):
        body = (await api.http.post(f"/search?tenant_id={TENANT}", json={"q": "acme"})).json()
        for category in body.values():
            assert "total" not in category

    @pytest.mark.parametrize("limit", [0, 11, 500])
    async def test_an_out_of_range_limit_is_refused(self, api, limit):
        response = await api.http.post(
            f"/search?tenant_id={TENANT}", json={"q": "acme", "limit": limit}
        )
        assert response.status_code == 422

    async def test_an_over_long_query_is_refused(self, api):
        response = await api.http.post(f"/search?tenant_id={TENANT}", json={"q": "a" * 101})
        assert response.status_code == 422

    @pytest.mark.parametrize("query", ["a", " a ", "  "])
    async def test_a_query_below_the_floor_runs_no_record_query(self, api, query):
        response = await api.http.post("/search", params={"tenant_id": TENANT}, json={"q": query})
        assert response.status_code == 200
        assert response.json()["clients"]["items"] == []
        api.clients.list_all.assert_not_awaited()

    async def test_a_short_query_is_empty_rather_than_failed(self, api):
        body = (
            await api.http.post("/search", params={"tenant_id": TENANT}, json={"q": "a"})
        ).json()
        assert body["clients"]["failed"] is False


class TestCategoryFailure:
    async def test_a_failing_category_is_reported_as_failed(self, api):
        api.clients.list_all.side_effect = RuntimeError("boom")
        body = (await api.http.post(f"/search?tenant_id={TENANT}", json={"q": "acme"})).json()
        assert body["clients"]["failed"] is True
        assert body["clients"]["items"] == []

    async def test_a_failing_category_does_not_fail_the_response(self, api):
        api.clients.list_all.side_effect = RuntimeError("boom")
        response = await api.http.post(f"/search?tenant_id={TENANT}", json={"q": "acme"})
        assert response.status_code == 200

    async def test_the_other_categories_still_return_their_results(self, api):
        api.clients.list_all.side_effect = RuntimeError("boom")
        body = (await api.http.post(f"/search?tenant_id={TENANT}", json={"q": "acme"})).json()
        assert body["practitioners"]["failed"] is False
        assert len(body["practitioners"]["items"]) == 1
        assert len(body["provider_organisations"]["items"]) == 1

    async def test_a_failure_rolls_back_so_later_categories_can_query(self, api):
        api.clients.list_all.side_effect = RuntimeError("boom")
        await api.http.post(f"/search?tenant_id={TENANT}", json={"q": "acme"})
        api.db.rollback.assert_awaited()

    async def test_a_successful_search_never_reports_a_failure(self, api):
        body = (await api.http.post(f"/search?tenant_id={TENANT}", json={"q": "acme"})).json()
        for category in body.values():
            assert category["failed"] is False

    async def test_an_empty_category_is_not_reported_as_failed(self, api):
        api.clients.list_all.return_value = []
        body = (await api.http.post(f"/search?tenant_id={TENANT}", json={"q": "zzzz"})).json()
        assert body["clients"]["items"] == []
        assert body["clients"]["failed"] is False


class TestQueryIsNotLogged:
    @staticmethod
    def _app_log(caplog) -> str:
        """Everything the application logged, traceback included.

        Formats each record rather than reading `getMessage()`, because an
        exception logged with `exc_info` carries the leaking text in its
        traceback and not in the message. Scoped to `app.` loggers: the test
        client logs the request URL itself, which is not the app's doing.
        """
        formatter = logging.Formatter("%(name)s %(message)s")
        return "\n".join(formatter.format(r) for r in caplog.records if r.name.startswith("app."))

    async def test_the_raw_query_is_absent_from_the_failure_log(self, api, caplog):
        """A SQLAlchemy exception string carries its statement and parameters,
        and the parameter here is the caller's search text."""
        api.clients.list_all.side_effect = RuntimeError(
            f"boom [SQL: SELECT ...] [parameters: ('%{SECRET_TERM}%',)]"
        )
        with caplog.at_level(logging.DEBUG):
            await api.http.post(f"/search?tenant_id={TENANT}", json={"q": SECRET_TERM})
        logged = self._app_log(caplog)
        assert "global search category clients failed" in logged
        assert SECRET_TERM not in logged
        assert "SELECT" not in logged

    async def test_nothing_is_logged_on_a_successful_search(self, api, caplog):
        with caplog.at_level(logging.DEBUG):
            await api.http.post(f"/search?tenant_id={TENANT}", json={"q": SECRET_TERM})
        assert SECRET_TERM not in self._app_log(caplog)


class TestQueryStaysOutOfTheUrl:
    """A query parameter is written to the access log and to every proxy log
    in front of the app, whatever the handler does. The term is body-only."""

    async def test_the_endpoint_is_not_reachable_by_get(self, api):
        response = await api.http.get(f"/search?tenant_id={TENANT}&q={SECRET_TERM}")
        assert response.status_code == 405

    async def test_a_query_in_the_url_is_ignored(self, api):
        """Even if a caller appends one, the body is the only source."""
        await api.http.post(f"/search?tenant_id={TENANT}&q=ignored", json={"q": SECRET_TERM})
        assert api.clients.list_all.await_args.kwargs["search"] == SECRET_TERM

    async def test_the_body_is_required(self, api):
        response = await api.http.post(f"/search?tenant_id={TENANT}")
        assert response.status_code == 422
