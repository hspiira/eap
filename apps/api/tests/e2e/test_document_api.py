"""
Document API End-to-End Tests

Comprehensive tests for all document endpoints covering:
- Document CRUD operations
- Lifecycle (publish, archive)
- Version management
- Confidentiality and expiry settings
"""

from datetime import UTC, datetime, timedelta

import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio


# =============================================================================
# CREATE DOCUMENT TESTS
# =============================================================================


class TestCreateDocument:
    """Tests for POST /documents/ endpoint."""

    async def test_create_document_with_url(self, client: AsyncClient):
        """Test creating a document with URL."""
        tenant_resp = await client.post(
            "/tenants/",
            json={"name": "Doc Test Tenant", "code": "doc-test"},
        )
        tenant_id = tenant_resp.json()["id"]

        response = await client.post(
            f"/documents/?tenant_id={tenant_id}",
            json={
                "name": "Service Agreement",
                "description": "Standard service agreement",
                "document_type": "Contract",
                "file_url": "https://example.com/docs/agreement.pdf",
                "mime_type": "application/pdf",
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Service Agreement"
        assert data["document_type"] == "Contract"
        assert data["status"] == "Draft"
        assert data["version"] == 1
        assert data["is_latest"] is True

    async def test_create_document_requires_tenant_id(self, client: AsyncClient):
        """Test that creating a document requires tenant_id."""
        response = await client.post(
            "/documents/",
            json={"name": "Test Doc", "document_type": "Contract"},
        )

        assert response.status_code == 422


class TestGetDocument:
    """Tests for GET /documents/{document_id} endpoint."""

    async def test_get_document_not_found(self, client: AsyncClient):
        """Test getting a non-existent document returns 404."""
        response = await client.get("/documents/nonexistent-id")

        assert response.status_code == 404


class TestListDocuments:
    """Tests for GET /documents/ endpoint."""

    async def test_list_documents_requires_tenant_id(self, client: AsyncClient):
        """Test that listing documents requires tenant_id."""
        response = await client.get("/documents/")

        assert response.status_code == 422

    async def test_list_documents_empty(self, client: AsyncClient):
        """Test listing documents when none exist."""
        tenant_resp = await client.post(
            "/tenants/",
            json={"name": "Empty Doc Tenant", "code": "empty-doc"},
        )
        tenant_id = tenant_resp.json()["id"]

        response = await client.get(f"/documents/?tenant_id={tenant_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["items"] == []
        assert data["total"] == 0

    async def test_list_documents_pagination(self, client: AsyncClient):
        """Test document list pagination."""
        tenant_resp = await client.post(
            "/tenants/",
            json={"name": "Doc Page Tenant", "code": "doc-page"},
        )
        tenant_id = tenant_resp.json()["id"]

        response = await client.get(f"/documents/?tenant_id={tenant_id}&page=1&limit=10")

        assert response.status_code == 200
        data = response.json()
        assert data["page"] == 1
        assert data["limit"] == 10


class TestPublishDocument:
    """Tests for POST /documents/{document_id}/publish endpoint."""

    async def test_publish_document_not_found(self, client: AsyncClient):
        """Test publishing non-existent document returns 404."""
        response = await client.post("/documents/nonexistent-id/publish")

        assert response.status_code == 404


class TestArchiveDocument:
    """Tests for POST /documents/{document_id}/archive endpoint."""

    async def test_archive_document_not_found(self, client: AsyncClient):
        """Test archiving non-existent document returns 404."""
        response = await client.post("/documents/nonexistent-id/archive")

        assert response.status_code == 404


class TestUpdateDocument:
    """Tests for PATCH /documents/{document_id} endpoint."""

    async def test_update_document_not_found(self, client: AsyncClient):
        """Test updating non-existent document returns 404."""
        response = await client.patch(
            "/documents/nonexistent-id",
            json={"name": "Updated Doc"},
        )

        assert response.status_code == 404


class TestSetDocumentConfidentiality:
    """Tests for PATCH /documents/{document_id}/confidentiality endpoint."""

    async def test_set_confidentiality_not_found(self, client: AsyncClient):
        """Test setting confidentiality for non-existent document."""
        response = await client.patch(
            "/documents/nonexistent-id/confidentiality",
            json={"is_confidential": True},
        )

        assert response.status_code == 404


class TestSetDocumentExpiry:
    """Tests for PATCH /documents/{document_id}/expiry endpoint."""

    async def test_set_expiry_not_found(self, client: AsyncClient):
        """Test setting expiry for non-existent document."""
        expires_at = (datetime.now(UTC) + timedelta(days=365)).isoformat()
        response = await client.patch(
            "/documents/nonexistent-id/expiry",
            json={"expires_at": expires_at},
        )

        assert response.status_code == 404


class TestGetDocumentVersions:
    """Tests for GET /documents/{document_id}/versions endpoint."""

    async def test_get_versions_requires_tenant_id(self, client: AsyncClient):
        """Test that getting versions requires tenant_id."""
        response = await client.get("/documents/some-id/versions")

        assert response.status_code == 422


class TestGetLatestDocumentVersion:
    """Tests for GET /documents/{document_id}/latest endpoint."""

    async def test_get_latest_not_found(self, client: AsyncClient):
        """Test getting latest version of non-existent document."""
        tenant_resp = await client.post(
            "/tenants/",
            json={"name": "Latest Doc Tenant", "code": "latest-doc"},
        )
        tenant_id = tenant_resp.json()["id"]

        response = await client.get(f"/documents/nonexistent-id/latest?tenant_id={tenant_id}")

        assert response.status_code == 404


# =============================================================================
# INTEGRATION TESTS
# =============================================================================


class TestDocumentIntegration:
    """Integration tests for document workflows."""

    async def test_document_lifecycle_flow(self, client: AsyncClient):
        """Test complete document lifecycle: create -> publish -> archive."""
        # Create tenant
        tenant_resp = await client.post(
            "/tenants/",
            json={"name": "Doc Lifecycle Tenant", "code": "doc-life"},
        )
        tenant_id = tenant_resp.json()["id"]

        # Create document
        create_resp = await client.post(
            f"/documents/?tenant_id={tenant_id}",
            json={
                "name": "Policy Document",
                "description": "Company policy",
                "document_type": "Other",
                "file_url": "https://example.com/policy.pdf",
                "mime_type": "application/pdf",
            },
        )
        assert create_resp.status_code == 201
        doc_id = create_resp.json()["id"]
        assert create_resp.json()["status"] == "Draft"

        # Get document
        get_resp = await client.get(f"/documents/{doc_id}")
        assert get_resp.status_code == 200
        assert get_resp.json()["name"] == "Policy Document"

        # Publish document
        publish_resp = await client.post(f"/documents/{doc_id}/publish")
        assert publish_resp.status_code == 200
        assert publish_resp.json()["status"] == "Published"

        # Archive document
        archive_resp = await client.post(f"/documents/{doc_id}/archive")
        assert archive_resp.status_code == 200
        assert archive_resp.json()["status"] == "Archived"

    async def test_document_update_and_settings(self, client: AsyncClient):
        """Test document update with confidentiality and expiry."""
        # Create tenant
        tenant_resp = await client.post(
            "/tenants/",
            json={"name": "Doc Settings Tenant", "code": "doc-set"},
        )
        tenant_id = tenant_resp.json()["id"]

        # Create document
        create_resp = await client.post(
            f"/documents/?tenant_id={tenant_id}",
            json={
                "name": "Confidential Report",
                "document_type": "KPI Report",
                "file_url": "https://example.com/report.pdf",
            },
        )
        doc_id = create_resp.json()["id"]

        # Update metadata
        update_resp = await client.patch(
            f"/documents/{doc_id}",
            json={"name": "Updated Report", "description": "New description"},
        )
        assert update_resp.status_code == 200
        assert update_resp.json()["name"] == "Updated Report"

        # Set confidentiality
        conf_resp = await client.patch(
            f"/documents/{doc_id}/confidentiality",
            json={"is_confidential": True},
        )
        assert conf_resp.status_code == 200
        assert conf_resp.json()["is_confidential"] is True

        # Set expiry
        expires_at = (datetime.now(UTC) + timedelta(days=90)).isoformat()
        expiry_resp = await client.patch(
            f"/documents/{doc_id}/expiry",
            json={"expires_at": expires_at},
        )
        assert expiry_resp.status_code == 200
        assert expiry_resp.json()["expires_at"] is not None
