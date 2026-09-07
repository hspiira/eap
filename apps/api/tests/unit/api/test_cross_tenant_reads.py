"""Wrong-tenant and anonymous reads are refused before any data is serialised.

These exercise the real routers through ASGI with mock repositories, so they
fail if the guard is removed, reordered after the response is built, or written
as an unawaited coroutine again.

Each entity here is a stand-in carrying only the field the guard reads. That is
deliberate: if a guard is ever moved below the response mapping, the mapping
raises on the stand-in and the test fails, which is the outcome we want.
"""

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
import pytest_asyncio
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from app.api.dependencies import (
    get_activity_repository,
    get_care_callback_campaign_repository,
    get_client_tag_repository,
    get_contact_repository,
    get_outreach_record_repository,
    get_report_run_repository,
    get_report_template_repository,
    get_service_assignment_repository,
)
from app.core.database import get_db
from app.core.exception_handlers import register_exception_handlers
from app.core.security import TokenData, get_current_user
from app.domain.value_objects.core import TenantId

OTHER_TENANT = SimpleNamespace(tenant_id=TenantId("tenant-b"))


def _client(router, overrides, *, authenticated=True):
    app = FastAPI()
    app.include_router(router)
    register_exception_handlers(app)
    app.dependency_overrides[get_db] = lambda: AsyncMock()
    if authenticated:
        app.dependency_overrides[get_current_user] = lambda: TokenData(
            user_id="u-a", tenant_id="tenant-a", role="Admin"
        )
    for dependency, value in overrides.items():
        app.dependency_overrides[dependency] = lambda value=value: value
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


def _repo(**attrs):
    repo = AsyncMock()
    for name, value in attrs.items():
        getattr(repo, name).return_value = value
    return repo


@pytest_asyncio.fixture
async def reports():
    from app.api.routes.reports import router

    overrides = {
        get_report_template_repository: _repo(get_by_id=OTHER_TENANT),
        get_report_run_repository: _repo(get_by_id=OTHER_TENANT),
    }
    async with _client(router, overrides) as http:
        yield http


@pytest_asyncio.fixture
async def anonymous_reports():
    from app.api.routes.reports import router

    overrides = {
        get_report_template_repository: _repo(get_by_id=OTHER_TENANT),
        get_report_run_repository: _repo(get_by_id=OTHER_TENANT),
    }
    async with _client(router, overrides, authenticated=False) as http:
        yield http


class TestReportsRequireAuthentication:
    """SEC-01: both routes returned 200 to a caller with no credentials."""

    @pytest.mark.parametrize(
        "path", ["/reports/templates/tpl-1", "/reports/runs/run-1"], ids=["template", "run"]
    )
    async def test_an_anonymous_read_is_refused(self, anonymous_reports, path):
        response = await anonymous_reports.get(path)
        assert response.status_code in (401, 403), response.text

    @pytest.mark.parametrize(
        "path", ["/reports/templates/tpl-1", "/reports/runs/run-1"], ids=["template", "run"]
    )
    async def test_another_tenants_record_is_refused(self, reports, path):
        response = await reports.get(path)
        assert response.status_code == 403, response.text
        assert "tenant" in response.text.lower()


class TestEntityReadsAreTenantScoped:
    """SEC-01/SEC-03: entity-ID reads whose sibling list routes were guarded."""

    @pytest.mark.parametrize(
        ("module", "path", "dependency"),
        [
            ("activities", "/activities/act-1", get_activity_repository),
            ("client_tags", "/client-tags/tag-1", get_client_tag_repository),
            ("contacts", "/contacts/con-1", get_contact_repository),
            (
                "service_assignments",
                "/service-assignments/asg-1",
                get_service_assignment_repository,
            ),
            (
                "care_callbacks",
                "/care-callback-campaigns/cmp-1",
                get_care_callback_campaign_repository,
            ),
            ("care_callbacks", "/outreach-records/out-1", get_outreach_record_repository),
        ],
        ids=["activity", "client-tag", "contact", "service-assignment", "campaign", "outreach"],
    )
    async def test_another_tenants_record_is_refused(self, module, path, dependency):
        import importlib

        router = importlib.import_module(f"app.api.routes.{module}").router
        async with _client(router, {dependency: _repo(get_by_id=OTHER_TENANT)}) as http:
            response = await http.get(path)
        assert response.status_code == 403, response.text

    async def test_an_anonymous_read_is_refused(self):
        from app.api.routes.activities import router

        overrides = {get_activity_repository: _repo(get_by_id=OTHER_TENANT)}
        async with _client(router, overrides, authenticated=False) as http:
            response = await http.get("/activities/act-1")
        assert response.status_code in (401, 403), response.text
