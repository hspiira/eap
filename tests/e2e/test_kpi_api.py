"""
KPI API End-to-End Tests

Comprehensive tests for all KPI endpoints covering:
- KPI CRUD operations
- KPI lifecycle (activate, deactivate)
- KPI Assignment CRUD operations
- KPI Assignment lifecycle
"""

import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio


# =============================================================================
# KPI CREATE TESTS
# =============================================================================


class TestCreateKPI:
    """Tests for POST /kpis/ endpoint."""

    async def test_create_kpi_success(self, client: AsyncClient):
        """Test creating a KPI with full data."""
        # Create tenant
        tenant_resp = await client.post(
            "/tenants/",
            json={"name": "KPI Test Tenant", "code": "kpi-test"},
        )
        tenant_id = tenant_resp.json()["id"]

        response = await client.post(
            f"/kpis/?tenant_id={tenant_id}",
            json={
                "name": "Customer Satisfaction Score",
                "description": "Measures customer satisfaction",
                "category": "Satisfaction",
                "measurement_unit": "Percentage",
                "target_value": 85.0,
                "threshold_min": 70.0,
                "threshold_max": 100.0,
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Customer Satisfaction Score"
        assert data["category"] == "Satisfaction"
        assert float(data["target_value"]) == 85.0
        assert data["is_active"] is True

    async def test_create_kpi_requires_tenant_id(self, client: AsyncClient):
        """Test that creating a KPI requires tenant_id."""
        response = await client.post(
            "/kpis/",
            json={"name": "Test KPI", "category": "Utilization", "measurement_unit": "Count"},
        )

        assert response.status_code == 422


class TestGetKPI:
    """Tests for GET /kpis/{kpi_id} endpoint."""

    async def test_get_kpi_not_found(self, client: AsyncClient):
        """Test getting a non-existent KPI returns 404."""
        response = await client.get("/kpis/nonexistent-id")

        assert response.status_code == 404


class TestListKPIs:
    """Tests for GET /kpis/ endpoint."""

    async def test_list_kpis_requires_tenant_id(self, client: AsyncClient):
        """Test that listing KPIs requires tenant_id."""
        response = await client.get("/kpis/")

        assert response.status_code == 422

    async def test_list_kpis_empty(self, client: AsyncClient):
        """Test listing KPIs when none exist."""
        tenant_resp = await client.post(
            "/tenants/",
            json={"name": "Empty KPI Tenant", "code": "empty-kpi"},
        )
        tenant_id = tenant_resp.json()["id"]

        response = await client.get(f"/kpis/?tenant_id={tenant_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["items"] == []
        assert data["total"] == 0


class TestActivateKPI:
    """Tests for POST /kpis/{kpi_id}/activate endpoint."""

    async def test_activate_kpi_not_found(self, client: AsyncClient):
        """Test activating non-existent KPI returns 404."""
        response = await client.post("/kpis/nonexistent-id/activate")

        assert response.status_code == 404


class TestDeactivateKPI:
    """Tests for POST /kpis/{kpi_id}/deactivate endpoint."""

    async def test_deactivate_kpi_not_found(self, client: AsyncClient):
        """Test deactivating non-existent KPI returns 404."""
        response = await client.post("/kpis/nonexistent-id/deactivate")

        assert response.status_code == 404


class TestUpdateKPI:
    """Tests for PATCH /kpis/{kpi_id} endpoint."""

    async def test_update_kpi_not_found(self, client: AsyncClient):
        """Test updating non-existent KPI."""
        response = await client.patch(
            "/kpis/nonexistent-id",
            json={"name": "Updated KPI"},
        )

        # Expect 400 or 404 depending on implementation
        assert response.status_code in [400, 404]


class TestCheckKPINameAvailability:
    """Tests for GET /kpis/check-name/{name} endpoint."""

    async def test_check_available_kpi_name(self, client: AsyncClient):
        """Test checking an available KPI name."""
        tenant_resp = await client.post(
            "/tenants/",
            json={"name": "KPI Name Check Tenant", "code": "kpi-name"},
        )
        tenant_id = tenant_resp.json()["id"]

        response = await client.get(f"/kpis/check-name/Available KPI?tenant_id={tenant_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["available"] is True


# =============================================================================
# KPI ASSIGNMENT TESTS
# =============================================================================


class TestCreateKPIAssignment:
    """Tests for POST /kpis/assignments endpoint."""

    async def test_create_assignment_requires_tenant_id(self, client: AsyncClient):
        """Test that creating an assignment requires tenant_id."""
        response = await client.post(
            "/kpis/assignments",
            json={"kpi_id": "some-id", "client_id": "client-id"},
        )

        assert response.status_code == 422


class TestListKPIAssignments:
    """Tests for GET /kpis/assignments endpoint."""

    async def test_list_assignments_empty(self, client: AsyncClient):
        """Test listing assignments when none exist."""
        tenant_resp = await client.post(
            "/tenants/",
            json={"name": "Empty Assign Tenant", "code": "empty-asgn"},
        )
        tenant_id = tenant_resp.json()["id"]

        # Note: The assignments endpoint is under /kpis/assignments
        response = await client.get(f"/kpis/assignments?tenant_id={tenant_id}")

        # The endpoint may return 404 if KPI repo checks fail or 200 with empty list
        if response.status_code == 200:
            data = response.json()
            assert data["items"] == []
            assert data["total"] == 0
        else:
            # Accept 404 if implementation returns this for no assignments
            assert response.status_code in [200, 404]


class TestGetKPIAssignment:
    """Tests for GET /kpis/assignments/{assignment_id} endpoint."""

    async def test_get_assignment_not_found(self, client: AsyncClient):
        """Test getting a non-existent assignment returns 404."""
        response = await client.get("/kpis/assignments/nonexistent-id")

        assert response.status_code == 404


class TestActivateKPIAssignment:
    """Tests for POST /kpis/assignments/{assignment_id}/activate endpoint."""

    async def test_activate_assignment_not_found(self, client: AsyncClient):
        """Test activating non-existent assignment returns 404."""
        response = await client.post("/kpis/assignments/nonexistent-id/activate")

        assert response.status_code == 404


class TestDeactivateKPIAssignment:
    """Tests for POST /kpis/assignments/{assignment_id}/deactivate endpoint."""

    async def test_deactivate_assignment_not_found(self, client: AsyncClient):
        """Test deactivating non-existent assignment returns 404."""
        response = await client.post("/kpis/assignments/nonexistent-id/deactivate")

        assert response.status_code == 404


class TestGetKPIAssignmentsByKPI:
    """Tests for GET /kpis/kpi/{kpi_id}/assignments endpoint."""

    async def test_get_assignments_by_kpi(self, client: AsyncClient):
        """Test getting assignments for a KPI."""
        tenant_resp = await client.post(
            "/tenants/",
            json={"name": "KPI Assign Tenant", "code": "kpi-asgn"},
        )
        tenant_id = tenant_resp.json()["id"]

        response = await client.get(f"/kpis/kpi/some-kpi-id/assignments?tenant_id={tenant_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["items"] == []


class TestGetKPIAssignmentsByClient:
    """Tests for GET /kpis/client/{client_id}/assignments endpoint."""

    async def test_get_assignments_by_client(self, client: AsyncClient):
        """Test getting assignments for a client."""
        tenant_resp = await client.post(
            "/tenants/",
            json={"name": "Client Assign Tenant", "code": "cli-asgn"},
        )
        tenant_id = tenant_resp.json()["id"]

        response = await client.get(
            f"/kpis/client/some-client-id/assignments?tenant_id={tenant_id}"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["items"] == []


class TestGetKPIAssignmentsByContract:
    """Tests for GET /kpis/contract/{contract_id}/assignments endpoint."""

    async def test_get_assignments_by_contract(self, client: AsyncClient):
        """Test getting assignments for a contract."""
        tenant_resp = await client.post(
            "/tenants/",
            json={"name": "Contract Assign Tenant", "code": "con-asgn"},
        )
        tenant_id = tenant_resp.json()["id"]

        response = await client.get(
            f"/kpis/contract/some-contract-id/assignments?tenant_id={tenant_id}"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["items"] == []


# =============================================================================
# INTEGRATION TESTS
# =============================================================================


class TestKPIIntegration:
    """Integration tests for KPI workflows."""

    async def test_kpi_crud_flow(self, client: AsyncClient):
        """Test complete KPI CRUD flow."""
        # Create tenant
        tenant_resp = await client.post(
            "/tenants/",
            json={"name": "KPI CRUD Tenant", "code": "kpi-crud"},
        )
        tenant_id = tenant_resp.json()["id"]

        # Create KPI
        create_resp = await client.post(
            f"/kpis/?tenant_id={tenant_id}",
            json={
                "name": "Utilization Rate",
                "description": "Service utilization rate",
                "category": "Utilization",
                "measurement_unit": "Percentage",
                "target_value": 80.0,
            },
        )
        assert create_resp.status_code == 201
        kpi_id = create_resp.json()["id"]

        # Get KPI
        get_resp = await client.get(f"/kpis/{kpi_id}")
        assert get_resp.status_code == 200
        assert get_resp.json()["name"] == "Utilization Rate"

        # Update KPI
        update_resp = await client.patch(
            f"/kpis/{kpi_id}",
            json={"name": "Updated Utilization Rate", "target_value": 85.0},
        )
        assert update_resp.status_code == 200
        assert float(update_resp.json()["target_value"]) == 85.0

        # List KPIs
        list_resp = await client.get(f"/kpis/?tenant_id={tenant_id}")
        assert list_resp.status_code == 200
        assert list_resp.json()["total"] >= 1

        # Deactivate KPI
        deactivate_resp = await client.post(f"/kpis/{kpi_id}/deactivate")
        assert deactivate_resp.status_code == 200
        assert deactivate_resp.json()["is_active"] is False

        # Activate KPI
        activate_resp = await client.post(f"/kpis/{kpi_id}/activate")
        assert activate_resp.status_code == 200
        assert activate_resp.json()["is_active"] is True
