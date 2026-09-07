"""The engagement-document checklist routes (P-02).

The write is Admin-only, tenant-scoped through the provider load, and skips
both save and audit when the upsert changes nothing.
"""

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest_asyncio
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from app.api.dependencies import (
    get_audit_event_handler,
    get_provider_engagement_document_repository,
    get_provider_repository,
)
from app.api.routes.providers import router
from app.core.authorization import get_current_user_entity
from app.core.database import get_db
from app.core.exception_handlers import register_exception_handlers
from app.core.security import TokenData, get_current_user
from app.domain.entities.provider import ProviderEntity
from app.domain.entities.provider_engagement_document import ProviderEngagementDocument
from app.domain.enums import (
    AccreditationStatus,
    BaseStatus,
    EngagementDocumentKind,
    EngagementDocumentState,
    PanelStatus,
    ProviderTier,
    TenantRole,
    UgandaRegion,
)
from app.domain.value_objects.core import ProviderId, ProviderProfile, TenantId
from app.domain.value_objects.ids import ProviderEngagementDocumentId
from app.shared.utils.datetime import utc_now

TENANT = "t-1"
PROVIDER = "p-1"


def _provider(tenant: str = TENANT) -> ProviderEntity:
    now = utc_now()
    return ProviderEntity(
        id=ProviderId(PROVIDER),
        tenant_id=TenantId(tenant),
        status=BaseStatus.ACTIVE,
        display_name="Amina Okello",
        created_at=now,
        updated_at=now,
        provider_profile=ProviderProfile(
            tier=ProviderTier.T1,
            region=UgandaRegion.CENTRAL,
            accreditation_status=AccreditationStatus.ACCREDITED,
            panel_status=PanelStatus.ACTIVE,
        ),
    )


def _document(
    kind: EngagementDocumentKind = EngagementDocumentKind.CONTRACT,
    state: EngagementDocumentState = EngagementDocumentState.PRESENT,
    note: str | None = None,
) -> ProviderEngagementDocument:
    now = utc_now()
    return ProviderEngagementDocument(
        id=ProviderEngagementDocumentId("doc-1"),
        tenant_id=TenantId(TENANT),
        provider_id=ProviderId(PROVIDER),
        document_kind=kind,
        state=state,
        note=note,
        created_at=now,
        updated_at=now,
    )


def _build_app(state, *, authenticate: bool = True) -> FastAPI:
    app = FastAPI()
    app.include_router(router)
    register_exception_handlers(app)

    def _user() -> TokenData:
        return TokenData(user_id="u-1", tenant_id=TENANT, role=state.role)

    def _user_entity():
        return SimpleNamespace(id="u-1", tenant_id=TenantId(TENANT), role=TenantRole(state.role))

    if authenticate:
        app.dependency_overrides[get_current_user] = _user
        app.dependency_overrides[get_current_user_entity] = _user_entity
    app.dependency_overrides[get_provider_repository] = lambda: state.providers
    app.dependency_overrides[get_provider_engagement_document_repository] = lambda: state.documents
    app.dependency_overrides[get_audit_event_handler] = lambda: state.audit
    app.dependency_overrides[get_db] = lambda: state.db
    return app


def _state() -> SimpleNamespace:
    state = SimpleNamespace(
        providers=AsyncMock(),
        documents=AsyncMock(),
        audit=AsyncMock(),
        db=AsyncMock(),
        role="Admin",
    )
    state.providers.get_by_id.return_value = _provider()
    state.documents.get_for_kind.return_value = None
    state.documents.list_for_provider.return_value = []
    return state


@pytest_asyncio.fixture
async def api():
    state = _state()
    app = _build_app(state)
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
    async def test_an_anonymous_read_is_refused(self, anonymous):
        response = await anonymous.http.get(f"/providers/{PROVIDER}/engagement-documents")
        assert response.status_code == 401
        anonymous.documents.list_for_provider.assert_not_awaited()

    async def test_an_anonymous_write_is_refused(self, anonymous):
        response = await anonymous.http.put(
            f"/providers/{PROVIDER}/engagement-documents/Contract",
            json={"state": "Present"},
        )
        assert response.status_code == 401
        anonymous.documents.save.assert_not_awaited()


class TestTenantScope:
    async def test_a_wrong_tenant_read_is_a_404(self, api):
        api.providers.get_by_id.return_value = _provider(tenant="t-other")
        response = await api.http.get(f"/providers/{PROVIDER}/engagement-documents")
        assert response.status_code == 404
        api.documents.list_for_provider.assert_not_awaited()

    async def test_a_wrong_tenant_write_is_a_404_and_saves_nothing(self, api):
        api.providers.get_by_id.return_value = _provider(tenant="t-other")
        response = await api.http.put(
            f"/providers/{PROVIDER}/engagement-documents/KYC",
            json={"state": "Missing"},
        )
        assert response.status_code == 404
        api.documents.save.assert_not_awaited()

    async def test_a_non_admin_write_is_refused(self, api):
        api.role = "User"
        response = await api.http.put(
            f"/providers/{PROVIDER}/engagement-documents/Contract",
            json={"state": "Present"},
        )
        assert response.status_code == 403
        api.documents.save.assert_not_awaited()


class TestUpsert:
    async def test_a_new_entry_is_persisted_and_audited(self, api):
        response = await api.http.put(
            f"/providers/{PROVIDER}/engagement-documents/UcaLicence",
            json={"state": "Open", "note": "1year"},
        )
        assert response.status_code == 200, response.text
        api.documents.save.assert_awaited_once()
        saved = api.documents.save.await_args.args[0]
        assert saved.document_kind == EngagementDocumentKind.UCA_LICENCE
        assert saved.state == EngagementDocumentState.OPEN
        assert saved.note == "1year"
        assert saved.tenant_id.value == TENANT
        api.audit.handle_events.assert_awaited()
        body = response.json()
        assert body["document_kind"] == "UcaLicence"
        assert body["state"] == "Open"
        assert body["note"] == "1year"

    async def test_an_existing_entry_is_updated_in_place(self, api):
        api.documents.get_for_kind.return_value = _document(state=EngagementDocumentState.MISSING)
        response = await api.http.put(
            f"/providers/{PROVIDER}/engagement-documents/Contract",
            json={"state": "Present", "note": "2024"},
        )
        assert response.status_code == 200, response.text
        saved = api.documents.save.await_args.args[0]
        assert saved.id.value == "doc-1"
        assert saved.state == EngagementDocumentState.PRESENT
        assert saved.note == "2024"

    async def test_an_unchanged_upsert_writes_neither_state_nor_audit(self, api):
        api.documents.get_for_kind.return_value = _document(
            state=EngagementDocumentState.PRESENT, note="2024"
        )
        response = await api.http.put(
            f"/providers/{PROVIDER}/engagement-documents/Contract",
            json={"state": "Present", "note": "2024"},
        )
        assert response.status_code == 200, response.text
        api.documents.save.assert_not_awaited()
        api.audit.handle_events.assert_not_awaited()

    async def test_an_unknown_kind_is_refused(self, api):
        response = await api.http.put(
            f"/providers/{PROVIDER}/engagement-documents/Passport",
            json={"state": "Present"},
        )
        assert response.status_code == 422
        api.documents.save.assert_not_awaited()


class TestListing:
    async def test_listing_returns_what_was_written(self, api):
        api.documents.list_for_provider.return_value = [
            _document(EngagementDocumentKind.CONTRACT, EngagementDocumentState.PRESENT),
            _document(EngagementDocumentKind.KYC, EngagementDocumentState.MISSING, note="open"),
        ]
        response = await api.http.get(f"/providers/{PROVIDER}/engagement-documents")
        assert response.status_code == 200, response.text
        body = response.json()
        assert [(entry["document_kind"], entry["state"]) for entry in body] == [
            ("Contract", "Present"),
            ("KYC", "Missing"),
        ]
        assert body[1]["note"] == "open"
