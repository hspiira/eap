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

from datetime import UTC, datetime, timedelta

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.services.outbox_consumers import make_audit_consumer
from app.application.services.outbox_dispatcher import OutboxDispatcher
from app.infrastructure.repositories.audit_repository import AuditRepositoryImpl
from app.infrastructure.repositories.outbox_repository import OutboxRepositoryImpl

pytestmark = pytest.mark.asyncio


async def _drain(db_session: AsyncSession) -> int:
    """Run the dispatcher the worker process runs, against the test's own session.

    Mutations enqueue an outbox row; nothing drains it into audit_logs
    without this, in tests or in a deployment with no worker running.
    """
    dispatcher = OutboxDispatcher(OutboxRepositoryImpl(db_session))
    dispatcher.register_consumer(make_audit_consumer(AuditRepositoryImpl(db_session)))
    delivered = await dispatcher.drain_once()
    await db_session.commit()
    return delivered


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

    async def test_action_type_filter_actually_narrows_the_results(
        self, client: AsyncClient, audit_test_tenant: dict, db_session: AsyncSession
    ):
        """R8b: a filter that only returns 200 on any input proves nothing.

        One CREATE (the client itself) and one UPDATE (renaming it) exist in
        this tenant; each filter must return only its own action, and the
        count must move with it.
        """
        tenant_id = audit_test_tenant["id"]
        created = await client.post(
            f"/clients/?tenant_id={tenant_id}",
            json={"name": "Filter Probe Co", "code": "FLTR", "contact_info": {"phone": "+1-555-1"}},
        )
        assert created.status_code == 201, created.text
        client_id = created.json()["id"]

        updated = await client.patch(
            f"/clients/{client_id}?tenant_id={tenant_id}", json={"name": "Filter Probe Co Renamed"}
        )
        assert updated.status_code == 200, updated.text
        await _drain(db_session)

        creates = await client.get(
            f"/audit/logs?tenant_id={tenant_id}&resource_id={client_id}&action_type=CREATE"
        )
        assert creates.status_code == 200, creates.text
        assert creates.json()["total"] == 1
        assert all(item["action_type"] == "CREATE" for item in creates.json()["items"])

        updates = await client.get(
            f"/audit/logs?tenant_id={tenant_id}&resource_id={client_id}&action_type=UPDATE"
        )
        assert updates.status_code == 200, updates.text
        assert updates.json()["total"] == 1
        assert all(item["action_type"] == "UPDATE" for item in updates.json()["items"])

    async def test_date_range_filter_actually_narrows_the_results(
        self, client: AsyncClient, audit_test_tenant: dict, db_session: AsyncSession
    ):
        tenant_id = audit_test_tenant["id"]
        created = await client.post(
            f"/clients/?tenant_id={tenant_id}",
            json={"name": "Date Probe Co", "code": "DATP", "contact_info": {"phone": "+1-555-2"}},
        )
        assert created.status_code == 201, created.text
        client_id = created.json()["id"]
        await _drain(db_session)

        far_future_start = (datetime.now(UTC) + timedelta(days=365)).isoformat()
        excluded = await client.get(
            "/audit/logs",
            params={
                "tenant_id": tenant_id,
                "resource_id": client_id,
                "start_date": far_future_start,
            },
        )
        assert excluded.status_code == 200, excluded.text
        assert excluded.json()["total"] == 0

        far_past_end = (datetime.now(UTC) - timedelta(days=365)).isoformat()
        also_excluded = await client.get(
            "/audit/logs",
            params={"tenant_id": tenant_id, "resource_id": client_id, "end_date": far_past_end},
        )
        assert also_excluded.status_code == 200, also_excluded.text
        assert also_excluded.json()["total"] == 0

        included = await client.get(f"/audit/logs?tenant_id={tenant_id}&resource_id={client_id}")
        assert included.json()["total"] == 1


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
# REDACTION AND ISOLATION (R8b)
# =============================================================================


class TestChangesAreRedactedThroughTheReadApi:
    """R8b gate: the console must not be able to reveal clinical values.

    Redaction happens at write time (AuditEventHandler._enqueue), not at
    read time, so this proves the already-redacted payload survives all the
    way through GET /audit/logs/{id}/changes rather than asserting it at the
    DB layer only, per docs/reviews/UI_BACKEND_EXECUTION_PLAN_2026_09_12.md.
    """

    async def test_a_clinical_field_edit_is_redacted_in_the_http_response(
        self,
        client_with_clinical_scope: AsyncClient,
        session_test_tenant: dict,
        session_test_service: dict,
        session_test_provider: dict,
        session_test_client_person: dict,
        db_session: AsyncSession,
    ):
        tenant_id = session_test_tenant["id"]
        created = await client_with_clinical_scope.post(
            f"/service-sessions/?tenant_id={tenant_id}",
            json={
                "service_id": session_test_service["id"],
                "provider_id": session_test_provider["id"],
                "member_id": session_test_client_person["id"],
                "scheduled_at": (datetime.now(UTC) + timedelta(days=500)).isoformat(),
                "delivery_context": "Direct",
            },
        )
        assert created.status_code == 201, created.text
        session_id = created.json()["id"]

        updated = await client_with_clinical_scope.patch(
            f"/service-sessions/{session_id}", json={"notes": "a real clinical note"}
        )
        assert updated.status_code == 200, updated.text
        await _drain(db_session)

        logs = await client_with_clinical_scope.get(
            f"/audit/logs?tenant_id={tenant_id}&resource_id={session_id}&action_type=UPDATE"
        )
        assert logs.status_code == 200, logs.text
        matching = logs.json()["items"]
        assert len(matching) >= 1
        audit_log_id = matching[0]["id"]

        changes = await client_with_clinical_scope.get(f"/audit/logs/{audit_log_id}/changes")
        assert changes.status_code == 200, changes.text
        field_changes = [fc for ec in changes.json() for fc in ec["field_changes"]]
        notes_change = next((fc for fc in field_changes if fc["field_name"] == "notes"), None)
        assert notes_change is not None, field_changes
        assert notes_change["new_value"] == "[redacted]"
        assert "clinical note" not in str(changes.json())


class TestAuditLogsStayWithinTheirTenant:
    """A same-named resource in another tenant must not leak into a query."""

    async def test_a_client_created_in_one_tenant_does_not_appear_in_another(
        self, client: AsyncClient, audit_test_tenant: dict, db_session: AsyncSession
    ):
        tenant_id = audit_test_tenant["id"]
        created = await client.post(
            f"/clients/?tenant_id={tenant_id}",
            json={"name": "Tenant Probe Co", "code": "TNTP", "contact_info": {"phone": "+1-555-3"}},
        )
        assert created.status_code == 201, created.text
        client_id = created.json()["id"]
        await _drain(db_session)

        # Proves the event exists and was drained, so the empty result below
        # is isolation, not an undrained outbox.
        own_tenant = await client.get(f"/audit/logs?tenant_id={tenant_id}&resource_id={client_id}")
        assert own_tenant.json()["total"] == 1

        other_tenant = await client.post(
            "/tenants/", json={"name": "Other Audit Tenant", "code": "other-audit"}
        )
        assert other_tenant.status_code == 201, other_tenant.text

        response = await client.get(
            f"/audit/logs?tenant_id={other_tenant.json()['id']}&resource_id={client_id}"
        )
        assert response.status_code == 200, response.text
        assert response.json()["total"] == 0
        assert response.json()["items"] == []


# =============================================================================
# INTEGRATION NOTES
# =============================================================================
#
# Content-verifying coverage for the list/filter/redaction/tenant-isolation
# axes lives in TestAuditLogFilters, TestChangesAreRedactedThroughTheReadApi
# and TestAuditLogsStayWithinTheirTenant above. Remaining gap, not closed
# here: GET /audit/logs/{id} and GET /audit/logs/{id}/changes use
# get_audit_log_for_current_tenant, which the shared `client` fixture
# overrides with a version that skips the tenant check entirely
# (tests/conftest.py, `override_get_audit_log`) — so no HTTP test in this
# file can prove cross-tenant isolation for those two routes specifically;
# only the list endpoint's isolation (proven above) and the production
# dependency code itself cover that path. Fixing the shared fixture affects
# every other test file using it and was judged out of scope here.
