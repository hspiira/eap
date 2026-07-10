"""
Security hardening E2E tests.

Covers tenant isolation, audit/document by-ID tenant check, user-in-tenant,
login rate limit, and document path/URL validation.
"""

import pytest
from fastapi import Request
from httpx import AsyncClient

from app.core.security import TokenData, get_current_user
from app.main import app
from app.shared.utils.document_validation import (
    validate_document_file_path,
    validate_document_file_url,
)

# =============================================================================
# Document path/URL validation (Phase 3.1 / H2)
# =============================================================================


class TestDocumentPathValidation:
    """Reject path traversal and dangerous URLs."""

    def test_reject_path_traversal(self):
        with pytest.raises(ValueError, match="escape|relative|Invalid"):
            validate_document_file_path("../../../etc/passwd", "./uploads")

    def test_reject_absolute_path(self):
        with pytest.raises(ValueError, match="absolute|Invalid"):
            validate_document_file_path("/etc/passwd", "./uploads")

    def test_accept_relative_path(self):
        out = validate_document_file_path("subdir/file.pdf", "./uploads")
        assert out is not None
        assert ".." not in (out or "")

    def test_reject_file_url_scheme(self):
        with pytest.raises(ValueError, match="scheme|allowed"):
            validate_document_file_url("file:///etc/passwd", ["https"])

    def test_reject_localhost_url(self):
        with pytest.raises(ValueError, match="localhost|private|not allowed"):
            validate_document_file_url("https://localhost/secret", ["https"])

    def test_accept_https_url(self):
        out = validate_document_file_url("https://example.com/doc.pdf", ["https"])
        assert out == "https://example.com/doc.pdf"


# =============================================================================
# Tenant isolation (Phase 2.1) – require_same_tenant on tenant routes
# =============================================================================


@pytest.mark.asyncio
class TestTenantIsolation:
    """Tenant routes require same tenant as token."""

    async def test_activate_other_tenant_forbidden(self, client: AsyncClient):
        """Calling activate on a tenant_id different from token's tenant returns 403."""
        fixed_tenant_id = "my-tenant-id"
        other_tenant_id = "other-tenant-id"

        async def override_fixed_tenant(_request: Request) -> TokenData:
            return TokenData(
                user_id="test-user-id",
                tenant_id=fixed_tenant_id,
                email="test@example.com",
            )

        original = app.dependency_overrides.get(get_current_user)
        app.dependency_overrides[get_current_user] = override_fixed_tenant
        try:
            response = await client.post(f"/tenants/{other_tenant_id}/activate")
            assert response.status_code == 403
        finally:
            if original is not None:
                app.dependency_overrides[get_current_user] = original
            elif get_current_user in app.dependency_overrides:
                del app.dependency_overrides[get_current_user]
