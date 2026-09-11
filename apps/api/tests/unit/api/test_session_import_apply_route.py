"""The apply route: Admin-only, and honest about importing nothing."""

from datetime import UTC, date, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
import pytest_asyncio
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from app.api.dependencies import (
    get_client_repository,
    get_eligible_member_repository,
    get_service_repository,
)
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
from app.domain.exceptions import DomainError
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
    state = SimpleNamespace(
        imports=AsyncMock(),
        writer=AsyncMock(),
        clients=AsyncMock(),
        members=AsyncMock(),
        services=AsyncMock(),
        db=AsyncMock(),
        role="Admin",
    )
    state.imports.get_batch.return_value = _batch()
    state.imports.list_rows.return_value = ([_row()], 1)
    state.imports.list_pending_rows.return_value = []
    state.imports.count_pending_rows.return_value = 0
    state.imports.count_imported_rows.return_value = 0
    state.imports.outcome_counts.return_value = {"UnresolvedMember": 1}
    state.clients.get_by_id.return_value = SimpleNamespace(tenant_id=TenantId(TENANT))
    state.members.get_by_id.return_value = SimpleNamespace(tenant_id=TenantId(TENANT))
    state.services.get_by_id.return_value = SimpleNamespace(tenant_id=TenantId(TENANT))

    def _user() -> TokenData:
        return TokenData(user_id="u-1", tenant_id=TENANT, role=state.role)

    def _user_entity():
        return SimpleNamespace(id="u-1", tenant_id=TenantId(TENANT), role=TenantRole(state.role))

    app.dependency_overrides[get_current_user] = _user
    app.dependency_overrides[get_current_user_entity] = _user_entity
    app.dependency_overrides[get_session_import_repository] = lambda: state.imports
    app.dependency_overrides[get_historical_session_writer] = lambda: state.writer
    app.dependency_overrides[get_client_repository] = lambda: state.clients
    app.dependency_overrides[get_eligible_member_repository] = lambda: state.members
    app.dependency_overrides[get_service_repository] = lambda: state.services
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

    async def test_a_batch_with_nothing_pending_reports_zero_imported_and_done(self, api):
        """UnresolvedMember and friends never reach list_pending_rows in the real repo."""
        response = await api.http.post(f"/session-imports/b-1/apply?tenant_id={TENANT}")
        body = response.json()
        assert body["imported"] == 0
        assert body["done"] is True
        assert body["remaining"] == 0
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


class TestChunkedApply:
    def _accepted_row(self):
        return SessionImportRowEntity(
            id=SessionImportRowId("r-2"),
            batch_id=SessionImportBatchId("b-1"),
            tenant_id=TenantId(TENANT),
            row_number=2,
            source_record_key=None,
            raw_practitioner_name="Alice Nakato",
            session_date=date(2025, 4, 2),
            outcome=ImportRowOutcome.ACCEPTED,
            provider_id=ProviderId("prov-1"),
            client_id="cli-1",
            service_id="svc-1",
            reasons=(),
            created_at=NOW,
        )

    async def test_a_pending_row_is_written_and_the_response_reports_it_left_open(self, api):
        api.imports.list_pending_rows.return_value = [self._accepted_row()]
        api.imports.count_pending_rows.return_value = 3
        api.writer.record.return_value = "sess-1"
        response = await api.http.post(f"/session-imports/b-1/apply?tenant_id={TENANT}")
        body = response.json()
        assert response.status_code == 200, response.text
        assert (body["imported"], body["remaining"], body["done"]) == (1, 3, False)
        api.imports.save_batch.assert_not_awaited()

    async def test_the_limit_query_param_reaches_the_pending_row_query(self, api):
        await api.http.post(f"/session-imports/b-1/apply?tenant_id={TENANT}&limit=10")
        assert api.imports.list_pending_rows.await_args.kwargs["limit"] == 10

    async def test_the_default_limit_is_used_when_none_is_given(self, api):
        await api.http.post(f"/session-imports/b-1/apply?tenant_id={TENANT}")
        assert api.imports.list_pending_rows.await_args.kwargs["limit"] == 50

    async def test_a_row_the_writer_refuses_is_reported_failed_not_a_500(self, api):
        api.imports.list_pending_rows.return_value = [self._accepted_row()]
        api.writer.record.side_effect = DomainError("no such thing", error_code="x")
        response = await api.http.post(f"/session-imports/b-1/apply?tenant_id={TENANT}")
        body = response.json()
        assert response.status_code == 200, response.text
        assert (body["imported"], body["failed"]) == (0, 1)


class TestAbandon:
    """A batch staged before its review data existed has to be closable."""

    async def test_an_admin_may_abandon_a_staged_batch(self, api):
        response = await api.http.post(
            f"/session-imports/b-1/abandon?tenant_id={TENANT}",
            json={"reason": "staged before the practitioner aliases were loaded"},
        )
        assert response.status_code == 200, response.text
        assert response.json()["status"] == "Abandoned"
        saved = api.imports.save_batch.await_args.args[0]
        assert saved.notes == "staged before the practitioner aliases were loaded"
        assert saved.applied_by == UserId("u-1")

    async def test_abandoning_frees_the_rows_to_be_staged_again(self, api):
        """A row nobody will import must stop claiming its source row."""
        await api.http.post(
            f"/session-imports/b-1/abandon?tenant_id={TENANT}",
            json={"reason": "superseded"},
        )
        api.imports.release_replay_keys.assert_awaited_once()

    async def test_a_refused_abandon_frees_nothing(self, api):
        api.imports.get_batch.return_value = _batch(ImportBatchStatus.APPLIED)
        await api.http.post(
            f"/session-imports/b-1/abandon?tenant_id={TENANT}", json={"reason": "superseded"}
        )
        api.imports.release_replay_keys.assert_not_awaited()

    async def test_a_reason_is_required(self, api):
        response = await api.http.post(
            f"/session-imports/b-1/abandon?tenant_id={TENANT}", json={"reason": "   "}
        )
        assert response.status_code == 422
        api.imports.save_batch.assert_not_awaited()

    async def test_an_applied_batch_cannot_be_abandoned(self, api):
        api.imports.get_batch.return_value = _batch(ImportBatchStatus.APPLIED)
        response = await api.http.post(
            f"/session-imports/b-1/abandon?tenant_id={TENANT}", json={"reason": "wrong file"}
        )
        assert response.status_code == 400
        api.imports.save_batch.assert_not_awaited()

    @pytest.mark.parametrize("role", ["User", "Viewer"])
    async def test_a_non_admin_may_not_abandon(self, api, role):
        api.role = role
        response = await api.http.post(
            f"/session-imports/b-1/abandon?tenant_id={TENANT}", json={"reason": "wrong file"}
        )
        assert response.status_code == 403
        api.imports.save_batch.assert_not_awaited()

    async def test_an_unknown_batch_is_a_404(self, api):
        api.imports.get_batch.return_value = None
        response = await api.http.post(
            f"/session-imports/b-1/abandon?tenant_id={TENANT}", json={"reason": "wrong file"}
        )
        assert response.status_code == 404


class TestTemplate:
    async def test_the_template_is_server_generated(self, api):
        response = await api.http.get("/session-imports/template")

        assert response.status_code == 200
        assert response.headers["content-type"].startswith("text/csv")
        assert response.text.splitlines()[0] == (
            "Date,Company (CLEAN),Client-ID#,Counselor (CLEAN),Client Type (Staff/Dep),Gender,"
            "Session Type,Session Category,Client Type,Intervention,Status (CLEAN),Rate (UGX),"
            "Session #"
        )
        assert "Example Client" in response.text

    async def test_the_template_shows_both_an_individual_and_a_company_wide_row(self, api):
        """Client-ID# and Gender are blank on the company-wide row; nothing else demonstrates that shape."""
        response = await api.http.get("/session-imports/template")
        rows = response.text.strip().splitlines()
        assert len(rows) == 3
        assert ",Staff," in rows[1]
        assert ",Group/Event," in rows[2]

    async def test_a_non_admin_may_still_read_the_template(self, api):
        """Staging is Admin-only; knowing the file shape is not."""
        api.role = "Viewer"
        response = await api.http.get("/session-imports/template")
        assert response.status_code == 200
