"""Staging conflicts: a restage while a batch is undecided is a 409, not a 500."""

from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest_asyncio
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy.exc import IntegrityError

from app.api.dependencies import (
    get_audit_event_handler,
    get_client_repository,
    get_diagnosis_repository,
    get_eligible_member_repository,
    get_service_repository,
    get_user_repository,
)
from app.api.dependencies.provider_network import (
    get_provider_affiliation_repository,
    get_provider_alias_repository,
    get_session_import_repository,
)
from app.api.routes.session_imports import router
from app.core.authorization import get_current_user_entity
from app.core.database import get_db
from app.core.exception_handlers import register_exception_handlers
from app.core.security import TokenData, get_current_user
from app.domain.entities.session_import import SessionImportBatchEntity
from app.domain.enums.provider_network import ImportBatchStatus
from app.domain.enums.tenancy import TenantRole
from app.domain.value_objects.core import TenantId, UserId
from app.domain.value_objects.provider_network import SessionImportBatchId

TENANT = "t-1"
NOW = datetime(2026, 9, 6, tzinfo=UTC)


def _batch():
    return SessionImportBatchEntity(
        id=SessionImportBatchId("b-1"),
        tenant_id=TenantId(TENANT),
        source_system="activity-log-workbook",
        file_name="f.csv",
        file_hash="sha256:abc",
        row_count=1,
        status=ImportBatchStatus.STAGED,
        staged_by=UserId("u-1"),
        created_at=NOW,
        updated_at=NOW,
    )


@pytest_asyncio.fixture
async def api():
    app = FastAPI()
    app.include_router(router)
    register_exception_handlers(app)
    state = SimpleNamespace(
        imports=AsyncMock(),
        aliases=AsyncMock(),
        affiliations=AsyncMock(),
        clients=AsyncMock(),
        members=AsyncMock(),
        services=AsyncMock(),
        diagnoses=AsyncMock(),
        users=AsyncMock(),
        audit_handler=AsyncMock(),
        db=AsyncMock(),
    )
    state.imports.find_batch_by_hash.return_value = None
    state.diagnoses.alias_lookup.return_value = {}
    state.users.list_all.return_value = []

    def _user() -> TokenData:
        return TokenData(user_id="u-1", tenant_id=TENANT, role="Admin")

    def _user_entity():
        return SimpleNamespace(id="u-1", tenant_id=TenantId(TENANT), role=TenantRole.ADMIN)

    app.dependency_overrides[get_current_user] = _user
    app.dependency_overrides[get_current_user_entity] = _user_entity
    app.dependency_overrides[get_session_import_repository] = lambda: state.imports
    app.dependency_overrides[get_provider_alias_repository] = lambda: state.aliases
    app.dependency_overrides[get_provider_affiliation_repository] = lambda: state.affiliations
    app.dependency_overrides[get_client_repository] = lambda: state.clients
    app.dependency_overrides[get_eligible_member_repository] = lambda: state.members
    app.dependency_overrides[get_service_repository] = lambda: state.services
    app.dependency_overrides[get_diagnosis_repository] = lambda: state.diagnoses
    app.dependency_overrides[get_user_repository] = lambda: state.users
    app.dependency_overrides[get_audit_event_handler] = lambda: state.audit_handler
    app.dependency_overrides[get_db] = lambda: state.db
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as http:
        state.http = http
        yield state


def _stage(http, filename="f.csv", content=b"DATE\n2026-01-01\n"):
    return http.post(
        f"/session-imports?tenant_id={TENANT}&source_system=activity-log-workbook",
        files={"file": (filename, content, "text/csv")},
    )


class TestSequentialConflict:
    async def test_restaging_a_still_staged_file_is_a_clean_409(self, api):
        api.imports.find_batch_by_hash.return_value = _batch()

        response = await _stage(api.http)

        assert response.status_code == 409
        assert response.json()["error"] == "IMPORT_ALREADY_STAGED"

    async def test_the_conflicting_batch_id_is_a_usable_detail(self, api):
        """A client needs the bare id to offer discard-and-retry, not just the sentence."""
        api.imports.find_batch_by_hash.return_value = _batch()

        response = await _stage(api.http)

        details = response.json()["details"]
        batch_id_detail = next(d for d in details if d["field"] == "batch_id")
        assert batch_id_detail["message"] == "b-1"
        file_detail = next(d for d in details if d["field"] == "file")
        assert "b-1" in file_detail["message"]


class TestConcurrentConflict:
    async def test_a_race_at_the_insert_is_also_a_clean_409_not_a_500(self, api):
        """The pre-check is read-then-write; a genuine race must not surface as an unhandled 500."""
        api.imports.save_batch.side_effect = IntegrityError("insert", {}, Exception("dup key"))

        response = await _stage(api.http)

        assert response.status_code == 409
        assert response.json()["error"] == "IMPORT_ALREADY_STAGED"
