"""
Service Assignment API End-to-End Tests

Comprehensive tests for all service assignment endpoints covering:
- CRUD operations
- Lifecycle (activate, deactivate)
- Service-contract relationships
"""

from datetime import UTC

import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio


# =============================================================================
# CREATE SERVICE ASSIGNMENT TESTS
# =============================================================================


class TestCreateServiceAssignment:
    """Tests for POST /service-assignments/ endpoint."""

    async def test_create_assignment_requires_tenant_id(self, client: AsyncClient):
        """Test that creating an assignment requires tenant_id."""
        response = await client.post(
            "/service-assignments/",
            json={"service_id": "some-id", "contract_id": "contract-id"},
        )

        assert response.status_code == 422


class TestGetServiceAssignment:
    """Tests for GET /service-assignments/{assignment_id} endpoint."""

    async def test_get_assignment_not_found(self, client: AsyncClient):
        """Test getting a non-existent assignment returns 404."""
        response = await client.get("/service-assignments/nonexistent-id")

        assert response.status_code == 404


class TestListServiceAssignments:
    """Tests for GET /service-assignments/ endpoint."""

    async def test_list_assignments_requires_tenant_id(self, client: AsyncClient):
        """Test that listing assignments requires tenant_id."""
        response = await client.get("/service-assignments/")

        assert response.status_code == 422

    async def test_list_assignments_empty(self, client: AsyncClient):
        """Test listing assignments when none exist."""
        tenant_resp = await client.post(
            "/tenants/",
            json={"name": "Empty Assign Tenant", "code": "empty-asn"},
        )
        tenant_id = tenant_resp.json()["id"]

        response = await client.get(f"/service-assignments/?tenant_id={tenant_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["items"] == []
        assert data["total"] == 0


class TestUpdateServiceAssignment:
    """Tests for PATCH /service-assignments/{assignment_id} endpoint."""

    async def test_update_assignment_not_found(self, client: AsyncClient):
        """Test updating non-existent assignment."""
        response = await client.patch(
            "/service-assignments/nonexistent-id",
            json={"notes": "Updated notes"},
        )

        assert response.status_code in [400, 404]


class TestActivateServiceAssignment:
    """Tests for POST /service-assignments/{assignment_id}/activate endpoint."""

    async def test_activate_assignment_not_found(self, client: AsyncClient):
        """Test activating non-existent assignment returns 404."""
        response = await client.post("/service-assignments/nonexistent-id/activate")

        assert response.status_code == 404


class TestDeactivateServiceAssignment:
    """Tests for POST /service-assignments/{assignment_id}/deactivate endpoint."""

    async def test_deactivate_assignment_not_found(self, client: AsyncClient):
        """Test deactivating non-existent assignment returns 404."""
        response = await client.post("/service-assignments/nonexistent-id/deactivate")

        assert response.status_code == 404


class TestGetAssignmentsByService:
    """Tests for GET /service-assignments/service/{service_id} endpoint."""

    async def test_get_assignments_by_service_requires_tenant_id(self, client: AsyncClient):
        """Test that getting assignments by service requires tenant_id."""
        response = await client.get("/service-assignments/service/some-service-id")

        assert response.status_code == 422

    async def test_get_assignments_by_service_empty(self, client: AsyncClient):
        """Test getting assignments for a service with no assignments."""
        tenant_resp = await client.post(
            "/tenants/",
            json={"name": "Service Assign Tenant", "code": "svc-asn"},
        )
        tenant_id = tenant_resp.json()["id"]

        response = await client.get(
            f"/service-assignments/service/some-service-id?tenant_id={tenant_id}"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["items"] == []


class TestGetAssignmentsByContract:
    """Tests for GET /service-assignments/contract/{contract_id} endpoint."""

    async def test_get_assignments_by_contract_requires_tenant_id(self, client: AsyncClient):
        """Test that getting assignments by contract requires tenant_id."""
        response = await client.get("/service-assignments/contract/some-contract-id")

        assert response.status_code == 422

    async def test_get_assignments_by_contract_empty(self, client: AsyncClient):
        """Test getting assignments for a contract with no assignments."""
        tenant_resp = await client.post(
            "/tenants/",
            json={"name": "Contract Assign Tenant", "code": "con-asn"},
        )
        tenant_id = tenant_resp.json()["id"]

        response = await client.get(
            f"/service-assignments/contract/some-contract-id?tenant_id={tenant_id}"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["items"] == []


# =============================================================================
# INTEGRATION TESTS
# =============================================================================


class TestServiceAssignmentIntegration:
    """Integration tests for service assignment workflows."""

    async def test_assignment_crud_flow(self, client: AsyncClient):
        """Test complete service assignment CRUD flow."""
        from datetime import datetime, timedelta

        # Create tenant
        tenant_resp = await client.post(
            "/tenants/",
            json={"name": "Assign CRUD Tenant", "code": "asn-crud"},
        )
        tenant_id = tenant_resp.json()["id"]

        # Create service
        service_resp = await client.post(
            f"/services/?tenant_id={tenant_id}",
            json={
                "name": "Assignment Test Service",
                "category": "Counseling",
                "duration_minutes": 60,
            },
        )
        service_id = service_resp.json()["id"]

        # Create client
        client_resp = await client.post(
            f"/clients/?tenant_id={tenant_id}",
            json={
                "name": "Assignment Test Client",
                "contact_info": {"email": "info@atc.com"},
            },
        )
        assert client_resp.status_code == 201
        client_id = client_resp.json()["id"]

        # Activate client
        await client.post(f"/clients/{client_id}/activate")

        # Create contract
        start_date = datetime.now(UTC).isoformat()
        end_date = (datetime.now(UTC) + timedelta(days=365)).isoformat()
        contract_resp = await client.post(
            f"/contracts/?tenant_id={tenant_id}",
            json={
                "client_id": client_id,
                "start_date": start_date,
                "end_date": end_date,
                "billing_rate": {"amount": "1000.00", "currency": "USD"},
                "payment_frequency": "Monthly",
            },
        )
        contract_id = contract_resp.json()["id"]

        # Create assignment
        create_resp = await client.post(
            f"/service-assignments/?tenant_id={tenant_id}",
            json={
                "service_id": service_id,
                "contract_id": contract_id,
                "notes": "Initial assignment",
            },
        )
        assert create_resp.status_code == 201
        assignment_id = create_resp.json()["id"]

        # Get assignment
        get_resp = await client.get(f"/service-assignments/{assignment_id}")
        assert get_resp.status_code == 200
        assert get_resp.json()["service_id"] == service_id

        # Update assignment
        update_resp = await client.patch(
            f"/service-assignments/{assignment_id}",
            json={"notes": "Updated notes"},
        )
        assert update_resp.status_code == 200

        # List assignments
        list_resp = await client.get(f"/service-assignments/?tenant_id={tenant_id}")
        assert list_resp.status_code == 200
        assert list_resp.json()["total"] >= 1

        # Get assignments by service
        service_assignments = await client.get(
            f"/service-assignments/service/{service_id}?tenant_id={tenant_id}"
        )
        assert service_assignments.status_code == 200
        assert service_assignments.json()["total"] >= 1

        # Get assignments by contract
        contract_assignments = await client.get(
            f"/service-assignments/contract/{contract_id}?tenant_id={tenant_id}"
        )
        assert contract_assignments.status_code == 200
        assert contract_assignments.json()["total"] >= 1

        # Deactivate assignment
        deactivate_resp = await client.post(f"/service-assignments/{assignment_id}/deactivate")
        assert deactivate_resp.status_code == 200

        # Activate assignment
        activate_resp = await client.post(f"/service-assignments/{assignment_id}/activate")
        assert activate_resp.status_code == 200
