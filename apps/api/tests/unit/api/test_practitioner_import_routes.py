"""The staging route: Admin-only writes, tenant-scoped reads, replay conflict."""

from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
import pytest_asyncio
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from app.api.dependencies import get_audit_event_handler
from app.api.dependencies.provider_network import (
    get_practitioner_import_repository,
    get_provider_alias_repository,
)
from app.api.routes.practitioner_imports import router
from app.core.authorization import get_current_user_entity
from app.core.database import get_db
from app.core.exception_handlers import register_exception_handlers
from app.core.security import TokenData, get_current_user
from app.domain.entities.practitioner_import import (
    PractitionerImportBatchEntity,
    PractitionerImportRowEntity,
)
from app.domain.enums.provider_network import PractitionerImportOutcome
from app.domain.enums.tenancy import TenantRole
from app.domain.value_objects.core import TenantId, UserId
from app.domain.value_objects.provider_network import (
    PractitionerImportBatchId,
    PractitionerImportRowId,
)
from tests.unit.shared.practitioner_workbook_builder import (
    consultant_row,
    partner_row,
    workbook_bytes,
)

TENANT = "t-1"
NOW = datetime(2026, 9, 7, tzinfo=UTC)


def _batch():
    return PractitionerImportBatchEntity(
        id=PractitionerImportBatchId("b-1"),
        tenant_id=TenantId(TENANT),
        source_system="practitioners-orgs-workbook",
        file_name="wb.xlsx",
        file_hash="sha256:abc",
        row_count=2,
        staged_by=UserId("u-1"),
        created_at=NOW,
        updated_at=NOW,
    )


def _row_entity():
    return PractitionerImportRowEntity(
        id=PractitionerImportRowId("r-1"),
        batch_id=PractitionerImportBatchId("b-1"),
        tenant_id=TenantId(TENANT),
        sheet_name="Minet EAP Partner list",
        row_number=3,
        raw_name="Jane Doe",
        normalized_name="jane doe",
        organisation_name="Safe Places Uganda",
        raw_profession="Clinical Psychology",
        mapped_profession="Clinical Psychologist",
        contact_email="jane@example.com",
        outcome=PractitionerImportOutcome.ACCEPTED,
        created_at=NOW,
        provenance={"OFFICE LOCATION": "Muyenga"},
    )


def _upload(content: bytes):
    mime = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    return {"file": ("wb.xlsx", content, mime)}


@pytest_asyncio.fixture
async def api():
    app = FastAPI()
    app.include_router(router)
    register_exception_handlers(app)
    state = SimpleNamespace(imports=AsyncMock(), aliases=AsyncMock(), db=AsyncMock(), role="Admin")
    state.imports.find_batch_by_hash.return_value = None
    state.imports.find_row_by_replay_key.return_value = None
    state.imports.get_batch.return_value = _batch()
    state.imports.list_rows.return_value = ([_row_entity()], 1)
    state.imports.outcome_counts.return_value = {"Accepted": 2}
    state.aliases.find_alias.return_value = None

    def _user() -> TokenData:
        return TokenData(user_id="u-1", tenant_id=TENANT, role=state.role)

    def _user_entity():
        return SimpleNamespace(id="u-1", tenant_id=TenantId(TENANT), role=TenantRole(state.role))

    app.dependency_overrides[get_current_user] = _user
    app.dependency_overrides[get_current_user_entity] = _user_entity
    app.dependency_overrides[get_practitioner_import_repository] = lambda: state.imports
    app.dependency_overrides[get_provider_alias_repository] = lambda: state.aliases
    app.dependency_overrides[get_audit_event_handler] = lambda: AsyncMock()
    app.dependency_overrides[get_db] = lambda: state.db
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as http:
        state.http = http
        state.app = app
        yield state


def _content():
    return workbook_bytes(
        [partner_row(company="Safe Places Uganda")],
        [consultant_row()],
    )


class TestAuthorization:
    async def test_an_anonymous_caller_is_refused(self, api):
        api.app.dependency_overrides.pop(get_current_user)
        response = await api.http.post(
            f"/practitioner-imports?tenant_id={TENANT}", files=_upload(_content())
        )
        assert response.status_code == 401
        api.imports.save_batch.assert_not_awaited()

    async def test_another_tenants_caller_is_refused(self, api):
        response = await api.http.post(
            "/practitioner-imports?tenant_id=t-other", files=_upload(_content())
        )
        assert response.status_code == 403
        api.imports.save_batch.assert_not_awaited()

    @pytest.mark.parametrize("role", ["User", "Viewer"])
    async def test_a_non_admin_may_not_stage(self, api, role):
        api.role = role
        response = await api.http.post(
            f"/practitioner-imports?tenant_id={TENANT}", files=_upload(_content())
        )
        assert response.status_code == 403
        api.imports.save_batch.assert_not_awaited()

    async def test_a_viewer_may_read_a_batch(self, api):
        api.role = "Viewer"
        response = await api.http.get(f"/practitioner-imports/b-1?tenant_id={TENANT}")
        assert response.status_code == 200


class TestStaging:
    async def test_staging_returns_the_batch_with_outcome_counts(self, api):
        response = await api.http.post(
            f"/practitioner-imports?tenant_id={TENANT}", files=_upload(_content())
        )
        assert response.status_code == 201, response.text
        body = response.json()
        assert body["row_count"] == 2
        assert body["source_system"] == "practitioners-orgs-workbook"
        assert body["outcome_counts"] == {"Accepted": 2}
        assert body["status"] == "Staged"
        api.imports.save_batch.assert_awaited_once()

    async def test_staged_rows_carry_sheet_scoped_replay_keys(self, api):
        await api.http.post(f"/practitioner-imports?tenant_id={TENANT}", files=_upload(_content()))
        rows = api.imports.add_rows.await_args.args[0]
        file_hash = api.imports.add_rows.await_args.kwargs["file_hash"]
        keys = {row.replay_key(file_hash) for row in rows}
        assert keys == {
            f"file:{file_hash}:sheet:Minet EAP Partner list:row:3",
            f"file:{file_hash}:sheet:EAP Consultants - General:row:2",
        }

    async def test_restaging_the_same_file_is_a_conflict(self, api):
        api.imports.find_batch_by_hash.return_value = _batch()
        response = await api.http.post(
            f"/practitioner-imports?tenant_id={TENANT}", files=_upload(_content())
        )
        assert response.status_code == 409
        api.imports.save_batch.assert_not_awaited()

    async def test_an_unreadable_file_is_refused(self, api):
        response = await api.http.post(
            f"/practitioner-imports?tenant_id={TENANT}", files=_upload(b"not a workbook")
        )
        assert response.status_code == 422
        api.imports.save_batch.assert_not_awaited()


class TestReading:
    async def test_an_unknown_batch_is_a_404(self, api):
        api.imports.get_batch.return_value = None
        response = await api.http.get(f"/practitioner-imports/b-9?tenant_id={TENANT}")
        assert response.status_code == 404

    async def test_rows_expose_outcome_reasons_and_provenance(self, api):
        response = await api.http.get(f"/practitioner-imports/b-1/rows?tenant_id={TENANT}")
        assert response.status_code == 200
        body = response.json()
        assert body["total"] == 1
        item = body["items"][0]
        assert item["sheet_name"] == "Minet EAP Partner list"
        assert item["organisation_name"] == "Safe Places Uganda"
        assert item["provenance"] == {"OFFICE LOCATION": "Muyenga"}
        assert item["outcome"] == "Accepted"
