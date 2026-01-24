"""
Service API End-to-End Tests

Comprehensive tests for all service endpoints covering:
- CRUD operations (Create, Get, List, Update)
- Lifecycle transitions (Activate, Deactivate, Archive, Restore)
- Group settings updates
"""

import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio


# =============================================================================
# CREATE SERVICE TESTS
# =============================================================================


class TestCreateService:
    """Tests for POST /services/ endpoint."""

    async def test_create_service_success(
        self, client: AsyncClient, service_test_tenant: dict
    ):
        """Test creating a service with full data."""
        tenant_id = service_test_tenant["id"]

        response = await client.post(
            f"/services/?tenant_id={tenant_id}",
            json={
                "name": "Stress Management",
                "description": "Workshops for stress management",
                "category": "Wellness",
                "duration_minutes": 60,
                "is_group_service": False,
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Stress Management"
        assert data["description"] == "Workshops for stress management"
        assert data["category"] == "Wellness"
        assert data["duration_minutes"] == 60
        assert data["is_group_service"] is False
        assert data["status"] == "Pending"
        assert data["is_active"] is False

    async def test_create_group_service(
        self, client: AsyncClient, service_test_tenant: dict
    ):
        """Test creating a group service."""
        tenant_id = service_test_tenant["id"]

        response = await client.post(
            f"/services/?tenant_id={tenant_id}",
            json={
                "name": "Team Building Workshop",
                "description": "Group workshop for teams",
                "category": "Training",
                "duration_minutes": 120,
                "is_group_service": True,
                "max_participants": 20,
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["is_group_service"] is True
        assert data["max_participants"] == 20

    async def test_create_service_requires_tenant_id(self, client: AsyncClient):
        """Test that creating a service requires tenant_id."""
        response = await client.post(
            "/services/",
            json={
                "name": "Test Service",
                "category": "Test",
                "duration_minutes": 30,
            },
        )

        assert response.status_code == 422


# =============================================================================
# GET SERVICE TESTS
# =============================================================================


class TestGetService:
    """Tests for GET /services/{service_id} endpoint."""

    async def test_get_service_by_id_success(
        self, client: AsyncClient, test_service: dict
    ):
        """Test getting a service by ID."""
        service_id = test_service["id"]

        response = await client.get(f"/services/{service_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == service_id
        assert data["name"] == "Individual Counseling"

    async def test_get_service_not_found(self, client: AsyncClient):
        """Test getting a non-existent service returns 404."""
        response = await client.get("/services/nonexistent-id-12345")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()


class TestGetServiceByName:
    """Tests for GET /services/name/{name} endpoint."""

    async def test_get_service_by_name_success(
        self, client: AsyncClient, service_test_tenant: dict, test_service: dict
    ):
        """Test getting a service by name."""
        tenant_id = service_test_tenant["id"]
        name = test_service["name"]

        response = await client.get(
            f"/services/name/{name}?tenant_id={tenant_id}"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == name

    async def test_get_service_by_name_not_found(
        self, client: AsyncClient, service_test_tenant: dict
    ):
        """Test getting service by non-existent name returns 404."""
        tenant_id = service_test_tenant["id"]

        response = await client.get(
            f"/services/name/Nonexistent Service?tenant_id={tenant_id}"
        )

        assert response.status_code == 404


class TestCheckNameAvailability:
    """Tests for GET /services/check-name/{name} endpoint."""

    async def test_check_available_name(
        self, client: AsyncClient, service_test_tenant: dict
    ):
        """Test checking an available name."""
        tenant_id = service_test_tenant["id"]

        response = await client.get(
            f"/services/check-name/Available Service?tenant_id={tenant_id}"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["available"] is True

    async def test_check_taken_name(
        self, client: AsyncClient, service_test_tenant: dict, test_service: dict
    ):
        """Test checking a taken name."""
        tenant_id = service_test_tenant["id"]
        name = test_service["name"]

        response = await client.get(
            f"/services/check-name/{name}?tenant_id={tenant_id}"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["available"] is False


# =============================================================================
# LIST SERVICES TESTS
# =============================================================================


class TestListServices:
    """Tests for GET /services/ endpoint."""

    async def test_list_services_requires_tenant_id(self, client: AsyncClient):
        """Test that listing services requires tenant_id."""
        response = await client.get("/services/")

        assert response.status_code == 422

    async def test_list_services_empty(
        self, client: AsyncClient, service_test_tenant: dict
    ):
        """Test listing services when none exist."""
        # Create a new tenant with no services
        new_tenant = await client.post(
            "/tenants/",
            json={"name": "Empty Service Tenant", "code": "empty-svc"},
        )
        tenant_id = new_tenant.json()["id"]

        response = await client.get(f"/services/?tenant_id={tenant_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["items"] == []
        assert data["total"] == 0

    async def test_list_services_success(
        self, client: AsyncClient, service_test_tenant: dict, test_service: dict, test_service_2: dict
    ):
        """Test listing services with results."""
        tenant_id = service_test_tenant["id"]

        response = await client.get(f"/services/?tenant_id={tenant_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 2
        assert len(data["items"]) >= 2

    async def test_list_services_pagination(
        self, client: AsyncClient, service_test_tenant: dict, test_service: dict
    ):
        """Test service list pagination."""
        tenant_id = service_test_tenant["id"]

        response = await client.get(
            f"/services/?tenant_id={tenant_id}&page=1&limit=1"
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) <= 1
        assert data["page"] == 1
        assert data["limit"] == 1

    async def test_list_services_filter_by_status(
        self, client: AsyncClient, service_test_tenant: dict, test_service_active: dict
    ):
        """Test filtering services by status."""
        tenant_id = service_test_tenant["id"]

        response = await client.get(
            f"/services/?tenant_id={tenant_id}&status=Active"
        )
        data = response.json()

        assert response.status_code == 200
        assert all(s["status"] == "Active" for s in data["items"])

    async def test_list_services_filter_by_category(
        self, client: AsyncClient, service_test_tenant: dict, test_service: dict
    ):
        """Test filtering services by category."""
        tenant_id = service_test_tenant["id"]

        response = await client.get(
            f"/services/?tenant_id={tenant_id}&category=Counseling"
        )
        data = response.json()

        assert response.status_code == 200
        assert all(s["category"] == "Counseling" for s in data["items"])

    async def test_list_services_filter_by_group(
        self, client: AsyncClient, service_test_tenant: dict, test_group_service: dict
    ):
        """Test filtering services by group flag."""
        tenant_id = service_test_tenant["id"]

        response = await client.get(
            f"/services/?tenant_id={tenant_id}&is_group_service=true"
        )
        data = response.json()

        assert response.status_code == 200
        assert all(s["is_group_service"] is True for s in data["items"])

    async def test_list_services_search(
        self, client: AsyncClient, service_test_tenant: dict, test_service: dict
    ):
        """Test searching services by name."""
        tenant_id = service_test_tenant["id"]

        response = await client.get(
            f"/services/?tenant_id={tenant_id}&search=Counseling"
        )
        data = response.json()

        assert response.status_code == 200
        assert data["total"] >= 1


# =============================================================================
# LIFECYCLE TESTS (Activate, Deactivate, Archive, Restore)
# =============================================================================


class TestActivateService:
    """Tests for POST /services/{service_id}/activate endpoint."""

    async def test_activate_pending_service(
        self, client: AsyncClient, test_service: dict
    ):
        """Test activating a pending service."""
        service_id = test_service["id"]

        response = await client.post(f"/services/{service_id}/activate")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "Active"
        assert data["is_active"] is True

    async def test_activate_not_found(self, client: AsyncClient):
        """Test activating non-existent service returns 404."""
        response = await client.post("/services/nonexistent-id/activate")

        assert response.status_code == 404


class TestDeactivateService:
    """Tests for POST /services/{service_id}/deactivate endpoint."""

    async def test_deactivate_service_success(
        self, client: AsyncClient, test_service_active: dict
    ):
        """Test deactivating an active service."""
        service_id = test_service_active["id"]

        response = await client.post(
            f"/services/{service_id}/deactivate?reason=Maintenance"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "Inactive"

    async def test_deactivate_not_found(self, client: AsyncClient):
        """Test deactivating non-existent service returns 404."""
        response = await client.post(
            "/services/nonexistent-id/deactivate?reason=Test"
        )

        assert response.status_code == 404


class TestArchiveService:
    """Tests for POST /services/{service_id}/archive endpoint."""

    async def test_archive_service_success(
        self, client: AsyncClient, test_service: dict
    ):
        """Test archiving a service."""
        service_id = test_service["id"]

        response = await client.post(f"/services/{service_id}/archive")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "Archived"

    async def test_archive_not_found(self, client: AsyncClient):
        """Test archiving non-existent service returns 404."""
        response = await client.post("/services/nonexistent-id/archive")

        assert response.status_code == 404


class TestRestoreService:
    """Tests for POST /services/{service_id}/restore endpoint."""

    async def test_restore_archived_service(
        self, client: AsyncClient, test_service: dict
    ):
        """Test restoring an archived service."""
        service_id = test_service["id"]

        # Archive first
        await client.post(f"/services/{service_id}/archive")

        # Then restore
        response = await client.post(f"/services/{service_id}/restore")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] != "Archived"

    async def test_restore_not_found(self, client: AsyncClient):
        """Test restoring non-existent service returns 404."""
        response = await client.post("/services/nonexistent-id/restore")

        assert response.status_code == 404


# =============================================================================
# UPDATE TESTS
# =============================================================================


class TestUpdateService:
    """Tests for PATCH /services/{service_id} endpoint."""

    async def test_update_service_name(
        self, client: AsyncClient, test_service: dict
    ):
        """Test updating service name."""
        service_id = test_service["id"]

        response = await client.patch(
            f"/services/{service_id}",
            json={"name": "Updated Counseling Service"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Counseling Service"

    async def test_update_service_description(
        self, client: AsyncClient, test_service: dict
    ):
        """Test updating service description."""
        service_id = test_service["id"]

        response = await client.patch(
            f"/services/{service_id}",
            json={"description": "Updated description"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["description"] == "Updated description"

    async def test_update_service_duration(
        self, client: AsyncClient, test_service: dict
    ):
        """Test updating service duration."""
        service_id = test_service["id"]

        response = await client.patch(
            f"/services/{service_id}",
            json={"duration_minutes": 90},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["duration_minutes"] == 90

    async def test_update_service_not_found(self, client: AsyncClient):
        """Test updating non-existent service returns 404."""
        response = await client.patch(
            "/services/nonexistent-id",
            json={"name": "Test"},
        )

        assert response.status_code == 404


class TestUpdateGroupSettings:
    """Tests for PATCH /services/{service_id}/group-settings endpoint."""

    async def test_enable_group_service(
        self, client: AsyncClient, test_service: dict
    ):
        """Test enabling group service mode."""
        service_id = test_service["id"]

        response = await client.patch(
            f"/services/{service_id}/group-settings",
            json={"is_group_service": True, "max_participants": 15},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["is_group_service"] is True
        assert data["max_participants"] == 15

    async def test_update_max_participants(
        self, client: AsyncClient, test_group_service: dict
    ):
        """Test updating max participants."""
        service_id = test_group_service["id"]

        response = await client.patch(
            f"/services/{service_id}/group-settings",
            json={"is_group_service": True, "max_participants": 25},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["max_participants"] == 25

    async def test_update_group_settings_not_found(self, client: AsyncClient):
        """Test updating group settings for non-existent service."""
        response = await client.patch(
            "/services/nonexistent-id/group-settings",
            json={"is_group_service": False},
        )

        assert response.status_code == 404


# =============================================================================
# INTEGRATION/FLOW TESTS
# =============================================================================


class TestServiceLifecycleFlow:
    """Integration tests for complete service lifecycle flows."""

    async def test_full_lifecycle_create_to_archive(
        self, client: AsyncClient, service_test_tenant: dict
    ):
        """Test complete flow: create -> activate -> deactivate -> archive."""
        tenant_id = service_test_tenant["id"]

        # Create service
        create_response = await client.post(
            f"/services/?tenant_id={tenant_id}",
            json={
                "name": "Lifecycle Test Service",
                "category": "Testing",
                "duration_minutes": 30,
            },
        )
        assert create_response.status_code == 201
        service_id = create_response.json()["id"]
        assert create_response.json()["status"] == "Pending"

        # Activate
        activate_response = await client.post(f"/services/{service_id}/activate")
        assert activate_response.json()["status"] == "Active"

        # Deactivate
        deactivate_response = await client.post(
            f"/services/{service_id}/deactivate?reason=End of program"
        )
        assert deactivate_response.json()["status"] == "Inactive"

        # Archive
        archive_response = await client.post(f"/services/{service_id}/archive")
        assert archive_response.json()["status"] == "Archived"

    async def test_crud_operations_integration(
        self, client: AsyncClient, service_test_tenant: dict
    ):
        """Test CRUD operations in sequence."""
        tenant_id = service_test_tenant["id"]

        # Create
        create_response = await client.post(
            f"/services/?tenant_id={tenant_id}",
            json={
                "name": "CRUD Test Service",
                "description": "Initial description",
                "category": "Testing",
                "duration_minutes": 45,
            },
        )
        service_id = create_response.json()["id"]

        # Read
        get_response = await client.get(f"/services/{service_id}")
        assert get_response.json()["name"] == "CRUD Test Service"

        # Update
        update_response = await client.patch(
            f"/services/{service_id}",
            json={
                "name": "Updated CRUD Service",
                "description": "Updated description",
                "duration_minutes": 60,
            },
        )
        assert update_response.json()["name"] == "Updated CRUD Service"
        assert update_response.json()["duration_minutes"] == 60

        # Verify in list
        list_response = await client.get(f"/services/?tenant_id={tenant_id}")
        service_ids = [s["id"] for s in list_response.json()["items"]]
        assert service_id in service_ids
