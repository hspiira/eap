"""The apply route: Admin-only, and honest about importing nothing."""

from datetime import UTC, date, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
import pytest_asyncio
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from app.api.dependencies.provider_network import (
    get_historical_session_writer,
    get_session_import_repository,
)
from app.api.routes.session_imports import router
from app.core.authorization import get_current_user_entity
from app.core.database import get_db
from app.core.exception_handlers import register_exception_handlers
from app.core.security import TokenData, get_current_user
from app.domain.entities.session_import import (
    SessionImportBatchEntity,
    SessionImportRowEntity,
)
from app.domain.enums.provider_network import ImportBatchStatus, ImportRowOutcome
from app.domain.enums.tenancy import TenantRole
from app.domain.value_objects.core import ProviderId, TenantId, UserId
from app.domain.value_objects.provider_network import (
    SessionImportBatchId,
    SessionImportRowId,
)

TENANT = "t-1"
NOW = datetime(2026, 9, 6, tzinfo=UTC)


def _batch(status=ImportBatchStatus.STAGED):
    return SessionImportBatchEntity(
        id=SessionImportBatchId("b-1"),
        tenant_id=TenantId(TENANT),
        source_system="sessions-csv",
        file_name="f.csv",
        file_hash="sha256:abc",
        row_count=1,
        status=status,
        staged_by=UserId("u-1"),
        created_at=NOW,
        updated_at=NOW,
    )


def _row(outcome=ImportRowOutcome.UNRESOLVED_MEMBER):
    return SessionImportRowEntity(
        id=SessionImportRowId("r-1"),
        batch_id=SessionImportBatchId("b-1"),
        tenant_id=TenantId(TENANT),
        row_number=1,
        source_record_key=None,
        raw_practitioner_name="Alice Nakato",
        session_date=date(2025, 4, 2),
        outcome=outcome,
        provider_id=ProviderId("prov-1"),
        reasons=("member reconciliation is not built",),
        created_at=NOW,
    )


@pytest_asyncio.fixture
async def api():
    app = FastAPI()
    app.include_router(router)
    register_exception_handlers(app)
    state = SimpleNamespace(imports=AsyncMock(), writer=AsyncMock(), db=AsyncMock(), role="Admin")
    state.imports.get_batch.return_value = _batch()
    state.imports.list_rows.return_value = ([_row()], 1)
    state.imports.outcome_counts.return_value = {"UnresolvedMember": 1}

    def _user() -> TokenData:
        return TokenData(user_id="u-1", tenant_id=TENANT, role=state.role)

    def _user_entity():
        return SimpleNamespace(id="u-1", tenant_id=TenantId(TENANT), role=TenantRole(state.role))

    app.dependency_overrides[get_current_user] = _user
    app.dependency_overrides[get_current_user_entity] = _user_entity
    app.dependency_overrides[get_session_import_repository] = lambda: state.imports
    app.dependency_overrides[get_historical_session_writer] = lambda: state.writer
    app.dependency_overrides[get_db] = lambda: state.db
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as http:
        state.http = http
        yield state


class TestAuthorization:
    async def test_an_admin_may_apply(self, api):
        response = await api.http.post(f"/session-imports/b-1/apply?tenant_id={TENANT}")
        assert response.status_code == 200, response.text

    @pytest.mark.parametrize("role", ["User", "Viewer"])
    async def test_a_non_admin_may_not_apply(self, api, role):
        api.role = role
        response = await api.http.post(f"/session-imports/b-1/apply?tenant_id={TENANT}")
        assert response.status_code == 403
        api.imports.save_batch.assert_not_awaited()

    async def test_another_tenants_batch_is_refused(self, api):
        response = await api.http.post("/session-imports/b-1/apply?tenant_id=t-other")
        assert response.status_code == 403


class TestHonestResult:
    async def test_it_no_longer_returns_501(self, api):
        """The route used to 501 while the write path did not exist."""
        response = await api.http.post(f"/session-imports/b-1/apply?tenant_id={TENANT}")
        assert response.status_code != 501

    async def test_an_unresolved_batch_reports_zero_imported(self, api):
        response = await api.http.post(f"/session-imports/b-1/apply?tenant_id={TENANT}")
        body = response.json()
        assert body["imported"] == 0
        assert body["not_importable"] == 1
        api.writer.record.assert_not_awaited()

    async def test_applying_twice_is_refused(self, api):
        api.imports.get_batch.return_value = _batch(ImportBatchStatus.APPLIED)
        response = await api.http.post(f"/session-imports/b-1/apply?tenant_id={TENANT}")
        assert response.status_code == 409
        assert response.json()["error"] == "import_batch_not_staged"

    async def test_an_unknown_batch_is_a_404(self, api):
        api.imports.get_batch.return_value = None
        response = await api.http.post(f"/session-imports/b-1/apply?tenant_id={TENANT}")
        assert response.status_code == 404
