"""
Person API End-to-End Tests

Comprehensive tests for all person endpoints covering:
- Query operations (Get by ID, Get by User ID, List, Get by Type)
- Lifecycle transitions (Activate, Deactivate, Terminate, Archive, Restore)
- Info updates (Emergency Contact, Employment, License, Staff)
- Secondary roles (Add, Remove)
"""

import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio


# =============================================================================
# GET PERSON TESTS
# =============================================================================


class TestGetPerson:
    """Tests for GET /persons/{person_id} endpoint."""

    async def test_get_person_by_id_success(self, client: AsyncClient, test_client_employee: dict):
        """Test getting a person by ID."""
        person_id = test_client_employee["id"]

        response = await client.get(f"/persons/{person_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == person_id
        assert data["tenant_id"] == test_client_employee["tenant_id"]
        assert data["user_id"] == test_client_employee["user_id"]
        assert data["person_type"] == "ClientEmployee"
        assert data["status"] == "Active"
        assert data["is_dual_role"] is False
        assert data["employment_info"] is not None
        assert data["employment_info"]["role"] == "Software Engineer"

    async def test_get_person_not_found(self, client: AsyncClient, test_tenant: dict):
        """Test getting a non-existent person returns 404."""
        response = await client.get("/persons/nonexistent-id-12345")

        assert response.status_code == 404
        assert "not found" in response.json()["message"].lower()


class TestGetPersonByUserId:
    """Tests for GET /persons/by-user/{user_id} endpoint."""

    async def test_get_person_by_user_id_success(
        self, client: AsyncClient, test_client_employee: dict, test_user: dict
    ):
        """Test getting a person by user ID."""
        user_id = test_user["id"]

        response = await client.get(f"/persons/by-user/{user_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["user_id"] == user_id
        assert data["id"] == test_client_employee["id"]

    async def test_get_person_by_user_id_not_found(self, client: AsyncClient, test_tenant: dict):
        """Test getting person by non-existent user ID returns 404."""
        response = await client.get("/persons/by-user/nonexistent-user-id")

        assert response.status_code == 404


class TestGetPersonsByType:
    """Tests for GET /persons/tenant/{tenant_id}/type/{person_type} endpoint."""

    async def test_get_persons_by_type_success(
        self, client: AsyncClient, test_tenant: dict, test_client_employee: dict
    ):
        """Test getting persons by type."""
        tenant_id = test_tenant["id"]

        response = await client.get(f"/persons/tenant/{tenant_id}/type/ClientEmployee")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        assert all(p["person_type"] == "ClientEmployee" for p in data)

    async def test_get_persons_by_type_empty(self, client: AsyncClient, test_tenant: dict):
        """Test getting persons by type when none exist."""
        tenant_id = test_tenant["id"]

        response = await client.get(f"/persons/tenant/{tenant_id}/type/Dependent")

        assert response.status_code == 200
        data = response.json()
        assert data == []

    async def test_get_persons_by_type_multiple(
        self,
        client: AsyncClient,
        test_tenant: dict,
        test_client_employee: dict,
        test_service_provider: dict,
    ):
        """Test getting persons filters correctly by type."""
        tenant_id = test_tenant["id"]

        # Get client employees
        ce_response = await client.get(f"/persons/tenant/{tenant_id}/type/ClientEmployee")
        assert ce_response.status_code == 200
        ce_data = ce_response.json()
        assert len(ce_data) >= 1
        assert all(p["person_type"] == "ClientEmployee" for p in ce_data)

        # Get service providers
        sp_response = await client.get(f"/persons/tenant/{tenant_id}/type/ServiceProvider")
        assert sp_response.status_code == 200
        sp_data = sp_response.json()
        assert len(sp_data) >= 1
        assert all(p["person_type"] == "ServiceProvider" for p in sp_data)


# =============================================================================
# LIST PERSONS TESTS
# =============================================================================


class TestListPersons:
    """Tests for GET /persons/ endpoint."""

    async def test_list_persons_requires_tenant_id(self, client: AsyncClient):
        """Test that listing persons requires tenant_id parameter."""
        response = await client.get("/persons/")

        assert response.status_code == 422  # Missing required query param

    async def test_list_persons_empty(self, client: AsyncClient, test_tenant: dict):
        """Test listing persons when none exist."""
        # Create a new tenant with no persons
        new_tenant = await client.post(
            "/tenants/",
            json={"name": "Empty Tenant", "code": "empty-list"},
        )
        tenant_id = new_tenant.json()["id"]

        response = await client.get(f"/persons/?tenant_id={tenant_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["items"] == []
        assert data["total"] == 0

    async def test_list_persons_success(
        self,
        client: AsyncClient,
        test_tenant: dict,
        test_client_employee: dict,
        test_service_provider: dict,
    ):
        """Test listing persons with results."""
        tenant_id = test_tenant["id"]

        response = await client.get(f"/persons/?tenant_id={tenant_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 2
        assert len(data["items"]) >= 2

    async def test_list_persons_pagination(
        self, client: AsyncClient, test_tenant: dict, test_client_employee: dict
    ):
        """Test person list pagination."""
        tenant_id = test_tenant["id"]

        response = await client.get(f"/persons/?tenant_id={tenant_id}&page=1&limit=1")

        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) <= 1
        assert data["page"] == 1
        assert data["limit"] == 1

    async def test_list_persons_filter_by_status(
        self,
        client: AsyncClient,
        test_tenant: dict,
        test_client_employee: dict,
        test_pending_person: dict,
    ):
        """Test filtering persons by status."""
        tenant_id = test_tenant["id"]

        # Filter by Active status
        response = await client.get(f"/persons/?tenant_id={tenant_id}&status=Active")
        data = response.json()

        assert response.status_code == 200
        assert all(p["status"] == "Active" for p in data["items"])

        # Filter by Pending status
        response = await client.get(f"/persons/?tenant_id={tenant_id}&status=Pending")
        data = response.json()

        assert response.status_code == 200
        assert all(p["status"] == "Pending" for p in data["items"])

    async def test_list_persons_filter_by_person_type(
        self,
        client: AsyncClient,
        test_tenant: dict,
        test_client_employee: dict,
        test_service_provider: dict,
    ):
        """Test filtering persons by person type."""
        tenant_id = test_tenant["id"]

        # Filter by ClientEmployee
        response = await client.get(f"/persons/?tenant_id={tenant_id}&person_type=ClientEmployee")
        data = response.json()

        assert response.status_code == 200
        assert all(p["person_type"] == "ClientEmployee" for p in data["items"])


# =============================================================================
# LIFECYCLE TESTS (Activate, Deactivate, Terminate, Archive, Restore)
# =============================================================================


class TestActivatePerson:
    """Tests for POST /persons/{person_id}/activate endpoint."""

    async def test_activate_pending_person(self, client: AsyncClient, test_pending_person: dict):
        """Test activating a pending person."""
        person_id = test_pending_person["id"]

        response = await client.post(f"/persons/{person_id}/activate")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "Active"

    async def test_activate_already_active_fails(
        self, client: AsyncClient, test_client_employee: dict
    ):
        """Test that activating an already active person fails."""
        person_id = test_client_employee["id"]

        response = await client.post(f"/persons/{person_id}/activate")

        # Returns 409 Conflict for state conflicts
        assert response.status_code == 409
        assert "already active" in response.json()["message"].lower()

    async def test_activate_not_found(self, client: AsyncClient, test_tenant: dict):
        """Test activating non-existent person returns 404."""
        response = await client.post("/persons/nonexistent-id/activate")

        assert response.status_code == 404


class TestDeactivatePerson:
    """Tests for POST /persons/{person_id}/deactivate endpoint."""

    async def test_deactivate_person_success(self, client: AsyncClient, test_client_employee: dict):
        """Test deactivating an active person."""
        person_id = test_client_employee["id"]

        response = await client.post(
            f"/persons/{person_id}/deactivate",
            json={"reason": "On leave"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "Inactive"

    async def test_deactivate_already_inactive_fails(
        self, client: AsyncClient, test_client_employee: dict
    ):
        """Test that deactivating an already inactive person fails."""
        person_id = test_client_employee["id"]

        # Deactivate first
        await client.post(
            f"/persons/{person_id}/deactivate",
            json={"reason": "First deactivation"},
        )

        # Try to deactivate again
        response = await client.post(
            f"/persons/{person_id}/deactivate",
            json={"reason": "Second deactivation"},
        )

        # 409 Conflict for state conflicts ("already" conditions)
        assert response.status_code == 409
        assert "already inactive" in response.json()["message"].lower()

    async def test_deactivate_not_found(self, client: AsyncClient, test_tenant: dict):
        """Test deactivating non-existent person returns 404."""
        response = await client.post(
            "/persons/nonexistent-id/deactivate",
            json={"reason": "Test"},
        )

        assert response.status_code == 404


class TestTerminatePerson:
    """Tests for POST /persons/{person_id}/terminate endpoint."""

    async def test_terminate_person_success(self, client: AsyncClient, test_client_employee: dict):
        """Test terminating a person."""
        person_id = test_client_employee["id"]

        response = await client.post(
            f"/persons/{person_id}/terminate",
            json={"reason": "Contract ended"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "Deleted"

    async def test_terminate_requires_reason(self, client: AsyncClient, test_pending_person: dict):
        """Test that termination requires a reason."""
        person_id = test_pending_person["id"]

        response = await client.post(
            f"/persons/{person_id}/terminate",
            json={"reason": ""},
        )

        assert response.status_code == 422

    async def test_terminate_not_found(self, client: AsyncClient, test_tenant: dict):
        """Test terminating non-existent person returns 404."""
        response = await client.post(
            "/persons/nonexistent-id/terminate",
            json={"reason": "Test"},
        )

        assert response.status_code == 404


class TestArchivePerson:
    """Tests for POST /persons/{person_id}/archive endpoint."""

    async def test_archive_person_success(self, client: AsyncClient, test_client_employee: dict):
        """Test archiving a person."""
        person_id = test_client_employee["id"]

        response = await client.post(f"/persons/{person_id}/archive")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "Archived"

    async def test_archive_already_archived_fails(
        self, client: AsyncClient, test_client_employee: dict
    ):
        """Test that archiving an already archived person fails."""
        person_id = test_client_employee["id"]

        # Archive first
        await client.post(f"/persons/{person_id}/archive")

        # Try to archive again
        response = await client.post(f"/persons/{person_id}/archive")

        # Returns 409 Conflict for state conflicts
        assert response.status_code == 409
        assert "already archived" in response.json()["message"].lower()

    async def test_archive_not_found(self, client: AsyncClient, test_tenant: dict):
        """Test archiving non-existent person returns 404."""
        response = await client.post("/persons/nonexistent-id/archive")

        assert response.status_code == 404


class TestRestorePerson:
    """Tests for POST /persons/{person_id}/restore endpoint."""

    async def test_restore_archived_person(self, client: AsyncClient, test_client_employee: dict):
        """Test restoring an archived person."""
        person_id = test_client_employee["id"]

        # Archive first
        await client.post(f"/persons/{person_id}/archive")

        # Restore
        response = await client.post(f"/persons/{person_id}/restore")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "Active"

    async def test_restore_active_person_fails(
        self, client: AsyncClient, test_client_employee: dict
    ):
        """Test that restoring an already active person fails."""
        person_id = test_client_employee["id"]

        response = await client.post(f"/persons/{person_id}/restore")

        # Returns 409 Conflict for state conflicts
        assert response.status_code == 409

    async def test_restore_not_found(self, client: AsyncClient, test_tenant: dict):
        """Test restoring non-existent person returns 404."""
        response = await client.post("/persons/nonexistent-id/restore")

        assert response.status_code == 404


# =============================================================================
# INFO UPDATE TESTS
# =============================================================================


class TestUpdateEmergencyContact:
    """Tests for PATCH /persons/{person_id}/emergency-contact endpoint."""

    async def test_update_emergency_contact_success(
        self,
        client: AsyncClient,
        test_client_employee: dict,
        sample_emergency_contact: dict,
    ):
        """Test updating emergency contact."""
        person_id = test_client_employee["id"]

        response = await client.patch(
            f"/persons/{person_id}/emergency-contact",
            json={"emergency_contact": sample_emergency_contact},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["emergency_contact"] is not None
        assert data["emergency_contact"]["name"] == sample_emergency_contact["name"]
        assert data["emergency_contact"]["phone"] == sample_emergency_contact["phone"]
        assert data["emergency_contact"]["email"] == sample_emergency_contact["email"]

    async def test_update_emergency_contact_phone_only(
        self, client: AsyncClient, test_client_employee: dict
    ):
        """Test updating emergency contact with phone only."""
        person_id = test_client_employee["id"]

        response = await client.patch(
            f"/persons/{person_id}/emergency-contact",
            json={
                "emergency_contact": {
                    "name": "John Smith",
                    "phone": "+1-555-999-8888",
                }
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["emergency_contact"]["phone"] == "+1-555-999-8888"

    async def test_update_emergency_contact_not_found(
        self, client: AsyncClient, test_tenant: dict, sample_emergency_contact: dict
    ):
        """Test updating emergency contact for non-existent person."""
        response = await client.patch(
            "/persons/nonexistent-id/emergency-contact",
            json={"emergency_contact": sample_emergency_contact},
        )

        assert response.status_code == 404


class TestUpdateEmploymentInfo:
    """Tests for PATCH /persons/{person_id}/employment-info endpoint."""

    async def test_update_employment_info_success(
        self,
        client: AsyncClient,
        test_client_employee: dict,
        sample_employment_info: dict,
    ):
        """Test updating employment information."""
        person_id = test_client_employee["id"]

        response = await client.patch(
            f"/persons/{person_id}/employment-info",
            json={"employment_info": sample_employment_info},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["employment_info"]["role"] == sample_employment_info["role"]
        assert data["employment_info"]["department"] == sample_employment_info["department"]
        assert data["employment_info"]["employee_id"] == sample_employment_info["employee_id"]

    async def test_update_employment_info_not_found(
        self, client: AsyncClient, test_tenant: dict, sample_employment_info: dict
    ):
        """Test updating employment info for non-existent person."""
        response = await client.patch(
            "/persons/nonexistent-id/employment-info",
            json={"employment_info": sample_employment_info},
        )

        assert response.status_code == 404


class TestUpdateLicenseInfo:
    """Tests for PATCH /persons/{person_id}/license-info endpoint."""

    async def test_update_license_info_success(
        self,
        client: AsyncClient,
        test_service_provider: dict,
        sample_license_info: dict,
    ):
        """Test updating license information."""
        person_id = test_service_provider["id"]

        response = await client.patch(
            f"/persons/{person_id}/license-info",
            json={"license_info": sample_license_info},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["license_info"]["number"] == sample_license_info["number"]
        assert data["license_info"]["issuing_authority"] == sample_license_info["issuing_authority"]

    async def test_update_license_info_not_found(
        self, client: AsyncClient, test_tenant: dict, sample_license_info: dict
    ):
        """Test updating license info for non-existent person."""
        response = await client.patch(
            "/persons/nonexistent-id/license-info",
            json={"license_info": sample_license_info},
        )

        assert response.status_code == 404


class TestUpdateStaffInfo:
    """Tests for PATCH /persons/{person_id}/staff-info endpoint."""

    async def test_update_staff_info_not_found(
        self, client: AsyncClient, test_tenant: dict, sample_staff_info: dict
    ):
        """Test updating staff info for non-existent person."""
        response = await client.patch(
            "/persons/nonexistent-id/staff-info",
            json={"staff_info": sample_staff_info},
        )

        assert response.status_code == 404


# =============================================================================
# SECONDARY ROLE TESTS
# =============================================================================


class TestAddSecondaryRole:
    """Tests for POST /persons/{person_id}/secondary-role endpoint."""

    async def test_add_secondary_role_service_provider(
        self,
        client: AsyncClient,
        test_client_employee: dict,
        sample_license_info: dict,
    ):
        """Test adding SERVICE_PROVIDER as secondary role to CLIENT_EMPLOYEE."""
        person_id = test_client_employee["id"]
        tenant_id = test_client_employee["tenant_id"]

        response = await client.post(
            f"/persons/{person_id}/secondary-role?tenant_id={tenant_id}",
            json={
                "role": "ServiceProvider",
                "license_info": sample_license_info,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["is_dual_role"] is True
        assert data["secondary_person_type"] == "ServiceProvider"
        assert data["license_info"] is not None

    async def test_add_secondary_role_missing_info_fails(
        self, client: AsyncClient, test_client_employee: dict
    ):
        """Test that adding secondary role without required info fails."""
        person_id = test_client_employee["id"]
        tenant_id = test_client_employee["tenant_id"]

        # Try to add SERVICE_PROVIDER role without license_info
        response = await client.post(
            f"/persons/{person_id}/secondary-role?tenant_id={tenant_id}",
            json={"role": "ServiceProvider"},
        )

        # The request schema rejects the missing license_info before the route
        # runs, so this is a body validation failure rather than a domain error.
        assert response.status_code == 422
        assert "license_info" in response.json()["message"].lower()

    async def test_add_secondary_role_same_as_primary_fails(
        self,
        client: AsyncClient,
        test_client_employee: dict,
        sample_employment_info: dict,
    ):
        """Test that adding same role as primary fails."""
        person_id = test_client_employee["id"]
        tenant_id = test_client_employee["tenant_id"]

        response = await client.post(
            f"/persons/{person_id}/secondary-role?tenant_id={tenant_id}",
            json={
                "role": "ClientEmployee",
                "employment_info": sample_employment_info,
            },
        )

        # 409 Conflict - role already exists as primary
        assert response.status_code == 409

    async def test_add_secondary_role_not_found(
        self, client: AsyncClient, test_tenant: dict, sample_license_info: dict
    ):
        """Test adding secondary role to non-existent person."""
        response = await client.post(
            "/persons/nonexistent-id/secondary-role",
            json={
                "role": "ServiceProvider",
                "license_info": sample_license_info,
            },
        )

        assert response.status_code == 404


class TestRemoveSecondaryRole:
    """Tests for DELETE /persons/{person_id}/secondary-role endpoint."""

    async def test_remove_secondary_role_success(
        self,
        client: AsyncClient,
        test_client_employee: dict,
        sample_license_info: dict,
    ):
        """Test removing secondary role."""
        person_id = test_client_employee["id"]
        tenant_id = test_client_employee["tenant_id"]

        # First add a secondary role
        await client.post(
            f"/persons/{person_id}/secondary-role?tenant_id={tenant_id}",
            json={
                "role": "ServiceProvider",
                "license_info": sample_license_info,
            },
        )

        # Then remove it
        response = await client.delete(f"/persons/{person_id}/secondary-role?tenant_id={tenant_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["is_dual_role"] is False
        assert data["secondary_person_type"] is None

    async def test_remove_secondary_role_when_none_exists_fails(
        self, client: AsyncClient, test_client_employee: dict
    ):
        """Test that removing secondary role when none exists fails."""
        person_id = test_client_employee["id"]
        tenant_id = test_client_employee["tenant_id"]

        response = await client.delete(f"/persons/{person_id}/secondary-role?tenant_id={tenant_id}")

        assert response.status_code == 400

    async def test_remove_secondary_role_not_found(self, client: AsyncClient, test_tenant: dict):
        """Test removing secondary role from non-existent person."""
        response = await client.delete("/persons/nonexistent-id/secondary-role")

        assert response.status_code == 404


# =============================================================================
# INTEGRATION/FLOW TESTS
# =============================================================================


class TestPersonLifecycleFlow:
    """Integration tests for complete person lifecycle flows."""

    async def test_full_lifecycle_pending_to_active_to_archived_to_restored(
        self, client: AsyncClient, test_pending_person: dict
    ):
        """Test complete flow: pending -> active -> archived -> restored."""
        person_id = test_pending_person["id"]

        # Start as pending
        get_response = await client.get(f"/persons/{person_id}")
        assert get_response.json()["status"] == "Pending"

        # Activate
        activate_response = await client.post(f"/persons/{person_id}/activate")
        assert activate_response.json()["status"] == "Active"

        # Archive
        archive_response = await client.post(f"/persons/{person_id}/archive")
        assert archive_response.json()["status"] == "Archived"

        # Restore
        restore_response = await client.post(f"/persons/{person_id}/restore")
        assert restore_response.json()["status"] == "Active"

    async def test_dual_role_lifecycle(
        self,
        client: AsyncClient,
        test_client_employee: dict,
        sample_license_info: dict,
    ):
        """Test adding and removing secondary roles."""
        person_id = test_client_employee["id"]
        tenant_id = test_client_employee["tenant_id"]

        # Verify initially not dual role
        get_response = await client.get(f"/persons/{person_id}")
        assert get_response.json()["is_dual_role"] is False

        # Add secondary role
        add_response = await client.post(
            f"/persons/{person_id}/secondary-role?tenant_id={tenant_id}",
            json={
                "role": "ServiceProvider",
                "license_info": sample_license_info,
            },
        )
        assert add_response.json()["is_dual_role"] is True
        assert add_response.json()["secondary_person_type"] == "ServiceProvider"

        # Verify secondary role persisted
        get_response = await client.get(f"/persons/{person_id}")
        assert get_response.json()["is_dual_role"] is True

        # Remove secondary role
        remove_response = await client.delete(f"/persons/{person_id}/secondary-role?tenant_id={tenant_id}")
        assert remove_response.json()["is_dual_role"] is False

        # Verify removal persisted
        get_response = await client.get(f"/persons/{person_id}")
        assert get_response.json()["is_dual_role"] is False

    async def test_info_updates_integration(
        self,
        client: AsyncClient,
        test_client_employee: dict,
        sample_emergency_contact: dict,
        sample_employment_info: dict,
    ):
        """Test multiple info updates in sequence."""
        person_id = test_client_employee["id"]

        # Update emergency contact
        ec_response = await client.patch(
            f"/persons/{person_id}/emergency-contact",
            json={"emergency_contact": sample_emergency_contact},
        )
        assert ec_response.status_code == 200
        assert ec_response.json()["emergency_contact"]["name"] == sample_emergency_contact["name"]

        # Update employment info
        emp_response = await client.patch(
            f"/persons/{person_id}/employment-info",
            json={"employment_info": sample_employment_info},
        )
        assert emp_response.status_code == 200
        assert emp_response.json()["employment_info"]["role"] == sample_employment_info["role"]

        # Verify both updates persisted
        get_response = await client.get(f"/persons/{person_id}")
        data = get_response.json()
        assert data["emergency_contact"]["name"] == sample_emergency_contact["name"]
        assert data["employment_info"]["role"] == sample_employment_info["role"]
