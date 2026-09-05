"""
Audit API End-to-End Tests

Comprehensive tests for all audit endpoints covering:
- List audit logs with filtering and pagination
- Get audit log by ID
- Get entity changes for an audit log
- Get change history for a specific entity

Note: Audit logs are immutable (read-only). Audit entries are created
automatically when other operations are performed with audit integration.
"""

import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio


# =============================================================================
# LIST AUDIT LOGS TESTS
# =============================================================================


class TestListAuditLogs:
    """Tests for GET /audit/logs endpoint."""

    async def test_list_audit_logs_requires_tenant_id(self, client: AsyncClient):
        """Test that listing audit logs requires tenant_id."""
        response = await client.get("/audit/logs")

        assert response.status_code == 422

    async def test_list_audit_logs_empty(self, client: AsyncClient, audit_test_tenant: dict):
        """Test listing audit logs when none exist."""
        tenant_id = audit_test_tenant["id"]

        response = await client.get(f"/audit/logs?tenant_id={tenant_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["items"] == []
        assert data["total"] == 0

    async def test_list_audit_logs_pagination(self, client: AsyncClient, audit_test_tenant: dict):
        """Test audit log list pagination."""
        tenant_id = audit_test_tenant["id"]

        response = await client.get(f"/audit/logs?tenant_id={tenant_id}&page=1&limit=10")

        assert response.status_code == 200
        data = response.json()
        assert data["page"] == 1
        assert data["limit"] == 10


# =============================================================================
# GET AUDIT LOG TESTS
# =============================================================================


class TestGetAuditLog:
    """Tests for GET /audit/logs/{audit_log_id} endpoint."""

    async def test_get_audit_log_not_found(self, client: AsyncClient):
        """Test getting a non-existent audit log returns 404."""
        response = await client.get("/audit/logs/nonexistent-id-12345")

        assert response.status_code == 404
        assert "not found" in response.json()["message"].lower()


# =============================================================================
# GET AUDIT LOG CHANGES TESTS
# =============================================================================


class TestGetAuditLogChanges:
    """Tests for GET /audit/logs/{audit_log_id}/changes endpoint."""

    async def test_get_changes_for_nonexistent_log(self, client: AsyncClient):
        """Test getting changes for non-existent audit log returns 404."""
        response = await client.get("/audit/logs/nonexistent-id/changes")
        assert response.status_code == 404


# =============================================================================
# GET ENTITY CHANGES TESTS
# =============================================================================


class TestGetEntityChanges:
    """Tests for GET /audit/entity/{entity_type}/{entity_id}/changes endpoint."""

    async def test_get_entity_changes_requires_tenant_id(self, client: AsyncClient):
        """Test that getting entity changes requires tenant_id."""
        response = await client.get("/audit/entity/Tenant/some-id/changes")

        assert response.status_code == 422

    async def test_get_entity_changes_empty(self, client: AsyncClient, audit_test_tenant: dict):
        """Test getting changes for entity with no change history."""
        tenant_id = audit_test_tenant["id"]

        response = await client.get(
            f"/audit/entity/SomeEntity/nonexistent-id/changes?tenant_id={tenant_id}"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["items"] == []

    async def test_get_entity_changes_pagination(
        self, client: AsyncClient, audit_test_tenant: dict
    ):
        """Test entity changes pagination."""
        tenant_id = audit_test_tenant["id"]

        response = await client.get(
            f"/audit/entity/Tenant/{tenant_id}/changes?tenant_id={tenant_id}&page=1&limit=5"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["page"] == 1
        assert data["limit"] == 5


# =============================================================================
# FILTER TESTS
# =============================================================================


class TestAuditLogFilters:
    """Tests for audit log filtering capabilities."""

    async def test_filter_by_action_type(self, client: AsyncClient, audit_test_tenant: dict):
        """Test filtering audit logs by action type."""
        tenant_id = audit_test_tenant["id"]

        response = await client.get(f"/audit/logs?tenant_id={tenant_id}&action_type=CREATE")

        assert response.status_code == 200

    async def test_filter_by_resource_type(self, client: AsyncClient, audit_test_tenant: dict):
        """Test filtering audit logs by resource type."""
        tenant_id = audit_test_tenant["id"]

        response = await client.get(f"/audit/logs?tenant_id={tenant_id}&resource_type=Tenant")

        assert response.status_code == 200

    async def test_filter_by_resource_id(self, client: AsyncClient, audit_test_tenant: dict):
        """Test filtering audit logs by resource ID."""
        tenant_id = audit_test_tenant["id"]

        response = await client.get(f"/audit/logs?tenant_id={tenant_id}&resource_id={tenant_id}")

        assert response.status_code == 200

    async def test_filter_by_user_id(self, client: AsyncClient, audit_test_tenant: dict):
        """Test filtering audit logs by user ID."""
        tenant_id = audit_test_tenant["id"]

        response = await client.get(f"/audit/logs?tenant_id={tenant_id}&user_id=some-user-id")

        assert response.status_code == 200

    async def test_filter_by_date_range(self, client: AsyncClient, audit_test_tenant: dict):
        """Test filtering audit logs by date range."""
        tenant_id = audit_test_tenant["id"]

        response = await client.get(
            f"/audit/logs?tenant_id={tenant_id}"
            "&start_date=2024-01-01T00:00:00Z"
            "&end_date=2024-12-31T23:59:59Z"
        )

        assert response.status_code == 200


# =============================================================================
# SORTING TESTS
# =============================================================================


class TestAuditLogSorting:
    """Tests for audit log sorting capabilities."""

    async def test_sort_by_occurred_at_desc(self, client: AsyncClient, audit_test_tenant: dict):
        """Test sorting audit logs by occurred_at descending."""
        tenant_id = audit_test_tenant["id"]

        response = await client.get(
            f"/audit/logs?tenant_id={tenant_id}&sort_by=occurred_at&sort_desc=true"
        )

        assert response.status_code == 200

    async def test_sort_by_occurred_at_asc(self, client: AsyncClient, audit_test_tenant: dict):
        """Test sorting audit logs by occurred_at ascending."""
        tenant_id = audit_test_tenant["id"]

        response = await client.get(
            f"/audit/logs?tenant_id={tenant_id}&sort_by=occurred_at&sort_desc=false"
        )

        assert response.status_code == 200


# =============================================================================
# INTEGRATION NOTES
# =============================================================================
#
# Note: More comprehensive audit log testing would require:
# 1. Enabling audit integration on routes
# 2. Performing actions that create audit logs
# 3. Then querying to verify the logs were created
#
# Since audit integration is optional and not yet enabled on all routes,
# these tests focus on the query API structure and error handling.
#
# When audit integration is enabled, additional tests could verify:
# - Audit logs are created when creating/updating entities
# - Field changes are properly tracked
# - User and IP information is captured
# - Action types are correctly mapped
