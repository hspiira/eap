from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
import pytest_asyncio
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from app.api.dependencies import (
    get_audit_event_handler,
    get_contract_repository,
    get_document_repository,
)
from app.api.routes.documents import router
from app.core.config import settings
from app.core.database import get_db
from app.core.exception_handlers import register_exception_handlers
from app.core.security import TokenData, get_current_user
from app.domain.value_objects.core import ClientId, ContractId, TenantId
from app.shared.utils.contract_files import MAX_ATTACHMENT_BYTES, attachment_path


@pytest_asyncio.fixture
async def api(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "DOCUMENT_STORAGE_PATH", str(tmp_path))
    app = FastAPI()
    app.include_router(router)
    register_exception_handlers(app)
    state = SimpleNamespace(
        contracts=AsyncMock(),
        documents=AsyncMock(),
        audit=AsyncMock(),
        db=AsyncMock(),
        user=TokenData(user_id="u1", tenant_id="t1", role="Admin"),
        root=tmp_path,
    )
    state.contracts.get_by_id.return_value = SimpleNamespace(
        id=ContractId("c1"), client_id=ClientId("client1"), tenant_id=TenantId("t1")
    )
    state.documents.save.side_effect = lambda document: document
    for dep, value in {
        get_contract_repository: state.contracts,
        get_document_repository: state.documents,
        get_audit_event_handler: state.audit,
        get_db: state.db,
    }.items():
        app.dependency_overrides[dep] = (lambda v: lambda: v)(value)
    app.dependency_overrides[get_current_user] = lambda: state.user
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as http:
        state.http = http
        yield state


PDF = b"%PDF-1.7\ncontract test fixture"
UPLOAD = "/documents/contracts/c1/attachments"


async def upload(api, filename="agreement.pdf", content=PDF):
    return await api.http.post(UPLOAD, files={"file": (filename, content, "application/pdf")})


async def test_upload_links_to_contract_and_client_and_downloads(api):
    response = await upload(api, "../../agreement.pdf")
    assert response.status_code == 201, response.text
    data = response.json()
    assert data["name"] == "agreement.pdf"
    assert data["client_id"] == "client1"
    assert data["contract_id"] == "c1"
    assert data["uploaded_by"] == "u1"
    assert data["is_confidential"] is True
    assert (api.root / data["file_path"]).read_bytes() == PDF
    api.db.commit.assert_awaited_once()
    document = api.documents.save.call_args.args[0]
    api.documents.get_by_id.return_value = document
    downloaded = await api.http.get(f"/documents/{data['id']}/download")
    assert downloaded.status_code == 200
    assert downloaded.content == PDF
    assert downloaded.headers["content-disposition"].startswith("attachment;")
    assert downloaded.headers["cache-control"] == "private, no-store"


async def test_foreign_contract_is_not_uploadable(api):
    api.contracts.get_by_id.return_value.tenant_id = TenantId("other")
    assert (await upload(api)).status_code == 404
    assert not list(api.root.iterdir())
    api.documents.save.assert_not_awaited()


async def test_viewer_cannot_upload(api):
    api.user.role = "Viewer"
    assert (await upload(api)).status_code == 403
    api.documents.save.assert_not_awaited()


@pytest.mark.parametrize(
    "filename,content", [("script.html", b"<script>"), ("fake.pdf", b"fake"), ("empty.pdf", b"")]
)
async def test_invalid_files_are_rejected(api, filename, content):
    assert (await upload(api, filename, content)).status_code == 400
    assert not list(api.root.iterdir())


async def test_size_limit(api):
    assert (await upload(api, content=PDF + b"x" * MAX_ATTACHMENT_BYTES)).status_code == 413
    api.documents.save.assert_not_awaited()


async def test_failed_commit_removes_file_and_rolls_back(api):
    api.db.commit.side_effect = RuntimeError("database unavailable")
    assert (await upload(api)).status_code == 500
    assert not [path for path in api.root.rglob("*") if path.is_file()]
    api.db.rollback.assert_awaited_once()


async def test_download_rejects_foreign_tenant_and_forged_paths(api):
    data = (await upload(api)).json()
    document = api.documents.save.call_args.args[0]
    api.documents.get_by_id.return_value = document
    api.user.tenant_id = "other"
    assert (await api.http.get(f"/documents/{data['id']}/download")).status_code == 404
    api.user.tenant_id = "t1"
    document.file_path = "../secret"
    assert (await api.http.get(f"/documents/{data['id']}/download")).status_code == 404


def test_attachment_path_rejects_traversal(tmp_path):
    with pytest.raises(ValueError, match="Invalid attachment path"):
        attachment_path(str(tmp_path), "tenant1", "../../secret")
