"""
Client API End-to-End Tests

Comprehensive tests for all client endpoints covering:
- CRUD operations (Create, Get, List, Update)
- Lifecycle transitions (Activate, Deactivate, Suspend, Terminate, Archive, Restore)
- Info updates (Contact Info, Billing Address)
- Queries (By Name, Check Availability, Stats, Children)
- Verification
"""

import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio


# =============================================================================
# CREATE CLIENT TESTS
# =============================================================================


class TestCreateClient:
    """Tests for POST /clients/ endpoint."""

    async def test_create_client_success(
        self, client: AsyncClient, client_test_tenant: dict, sample_client_data: dict
    ):
        """Test creating a client with full data."""
        tenant_id = client_test_tenant["id"]

        response = await client.post(
            f"/clients/?tenant_id={tenant_id}",
            json=sample_client_data,
        )

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == sample_client_data["name"]
        assert data["tenant_id"] == tenant_id
        assert data["status"] == "Pending"
        assert data["is_verified"] is False
        assert data["contact_info"]["phone"] == sample_client_data["contact_info"]["phone"]
        assert data["contact_info"]["email"] == sample_client_data["contact_info"]["email"]
        assert data["billing_address"] is not None
        assert data["billing_address"]["city"] == "New York"

    async def test_create_client_minimal(
        self, client: AsyncClient, client_test_tenant: dict, sample_client_data_minimal: dict
    ):
        """Test creating a client with minimal data."""
        tenant_id = client_test_tenant["id"]

        response = await client.post(
            f"/clients/?tenant_id={tenant_id}",
            json=sample_client_data_minimal,
        )

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == sample_client_data_minimal["name"]
        assert data["billing_address"] is None

    async def test_create_client_with_parent(
        self, client: AsyncClient, client_test_tenant: dict, test_parent_client: dict
    ):
        """Test creating a client with a parent client."""
        tenant_id = client_test_tenant["id"]

        response = await client.post(
            f"/clients/?tenant_id={tenant_id}",
            json={
                "name": "Subsidiary Company",
                "code": "SUB",
                "contact_info": {"phone": "+1-555-777-8888"},
                "parent_client_id": test_parent_client["id"],
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["parent_client_id"] == test_parent_client["id"]

    async def test_create_client_duplicate_name_fails(
        self, client: AsyncClient, client_test_tenant: dict, test_client: dict
    ):
        """Test that creating a client with duplicate name fails."""
        tenant_id = client_test_tenant["id"]

        response = await client.post(
            f"/clients/?tenant_id={tenant_id}",
            json={
                "name": test_client["name"],  # Same name as existing client
                "code": "DUP",
                "contact_info": {"phone": "+1-555-000-0000"},
            },
        )

        # 409 Conflict for duplicate resource creation
        assert response.status_code == 409
        assert "already exists" in response.json()["message"].lower()

    async def test_create_client_requires_tenant_id(
        self, client: AsyncClient, sample_client_data: dict
    ):
        """Test that creating a client requires tenant_id."""
        response = await client.post(
            "/clients/",
            json=sample_client_data,
        )

        assert response.status_code == 422  # Missing required query param

    async def test_create_client_empty_name_fails(
        self, client: AsyncClient, client_test_tenant: dict
    ):
        """Test that creating a client with empty name fails."""
        tenant_id = client_test_tenant["id"]

        response = await client.post(
            f"/clients/?tenant_id={tenant_id}",
            json={
                "name": "",
                "code": "EMPT",
                "contact_info": {"phone": "+1-555-000-0000"},
            },
        )

        assert response.status_code == 422


# =============================================================================
# GET CLIENT TESTS
# =============================================================================


class TestGetClient:
    """Tests for GET /clients/{client_id} endpoint."""

    async def test_get_client_by_id_success(self, client: AsyncClient, test_client: dict):
        """Test getting a client by ID."""
        client_id = test_client["id"]

        response = await client.get(f"/clients/{client_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == client_id
        assert data["name"] == test_client["name"]

    async def test_get_client_not_found(self, client: AsyncClient, client_test_tenant: dict):
        """Test getting a non-existent client returns 404."""
        response = await client.get("/clients/nonexistent-id-12345")

        assert response.status_code == 404
        assert "not found" in response.json()["message"].lower()


class TestGetClientByName:
    """Tests for GET /clients/name/{name} endpoint."""

    async def test_get_client_by_name_success(
        self, client: AsyncClient, client_test_tenant: dict, test_client: dict
    ):
        """Test getting a client by name."""
        tenant_id = client_test_tenant["id"]
        name = test_client["name"]

        response = await client.get(f"/clients/name/{name}?tenant_id={tenant_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == name

    async def test_get_client_by_name_not_found(
        self, client: AsyncClient, client_test_tenant: dict
    ):
        """Test getting a non-existent client by name returns 404."""
        tenant_id = client_test_tenant["id"]

        response = await client.get(f"/clients/name/NonExistentCompany?tenant_id={tenant_id}")

        assert response.status_code == 404


class TestCheckNameAvailability:
    """Tests for GET /clients/check-name/{name} endpoint."""

    async def test_check_available_name(self, client: AsyncClient, client_test_tenant: dict):
        """Test checking an available name."""
        tenant_id = client_test_tenant["id"]

        response = await client.get(f"/clients/check-name/UniqueNewName?tenant_id={tenant_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["available"] is True
        assert data["name"] == "UniqueNewName"

    async def test_check_taken_name(
        self, client: AsyncClient, client_test_tenant: dict, test_client: dict
    ):
        """Test checking a taken name."""
        tenant_id = client_test_tenant["id"]
        name = test_client["name"]

        response = await client.get(f"/clients/check-name/{name}?tenant_id={tenant_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["available"] is False


# =============================================================================
# LIST CLIENTS TESTS
# =============================================================================


class TestListClients:
    """Tests for GET /clients/ endpoint."""

    async def test_list_clients_requires_tenant_id(self, client: AsyncClient):
        """Test that listing clients requires tenant_id parameter."""
        response = await client.get("/clients/")

        assert response.status_code == 422

    async def test_list_clients_empty(self, client: AsyncClient, client_test_tenant: dict):
        """Test listing clients when none exist (besides fixture)."""
        # Create a new tenant with no clients
        new_tenant = await client.post(
            "/tenants/",
            json={"name": "Empty Client Tenant", "code": "empty-cli"},
        )
        tenant_id = new_tenant.json()["id"]

        response = await client.get(f"/clients/?tenant_id={tenant_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["items"] == []
        assert data["total"] == 0

    async def test_list_clients_success(
        self, client: AsyncClient, client_test_tenant: dict, test_client: dict, test_client_2: dict
    ):
        """Test listing clients with results."""
        tenant_id = client_test_tenant["id"]

        response = await client.get(f"/clients/?tenant_id={tenant_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 2
        assert len(data["items"]) >= 2

    async def test_list_clients_pagination(
        self, client: AsyncClient, client_test_tenant: dict, test_client: dict
    ):
        """Test client list pagination."""
        tenant_id = client_test_tenant["id"]

        response = await client.get(f"/clients/?tenant_id={tenant_id}&page=1&limit=1")

        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) <= 1
        assert data["page"] == 1
        assert data["limit"] == 1

    async def test_list_clients_filter_by_status(
        self,
        client: AsyncClient,
        client_test_tenant: dict,
        test_client: dict,
        test_client_active: dict,
    ):
        """Test filtering clients by status."""
        tenant_id = client_test_tenant["id"]

        # Filter by Active status
        response = await client.get(f"/clients/?tenant_id={tenant_id}&status=Active")
        data = response.json()

        assert response.status_code == 200
        assert all(c["status"] == "Active" for c in data["items"])

    async def test_list_clients_filter_by_verified(
        self, client: AsyncClient, client_test_tenant: dict, test_client: dict
    ):
        """Test filtering clients by verification status."""
        tenant_id = client_test_tenant["id"]

        # Filter by not verified
        response = await client.get(f"/clients/?tenant_id={tenant_id}&is_verified=false")
        data = response.json()

        assert response.status_code == 200
        assert all(c["is_verified"] is False for c in data["items"])

    async def test_list_clients_search(
        self, client: AsyncClient, client_test_tenant: dict, test_client: dict
    ):
        """Test searching clients by name."""
        tenant_id = client_test_tenant["id"]
        search_term = test_client["name"][:4]

        response = await client.get(f"/clients/?tenant_id={tenant_id}&search={search_term}")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1


# =============================================================================
# VERIFY CLIENT TESTS
# =============================================================================


class TestVerifyClient:
    """Tests for POST /clients/{client_id}/verify endpoint."""

    async def test_verify_client_success(
        self, client: AsyncClient, test_client: dict, verifier_user: dict
    ):
        """Test verifying a client."""
        client_id = test_client["id"]
        verifier_id = verifier_user["id"]

        response = await client.post(f"/clients/{client_id}/verify?verified_by={verifier_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["is_verified"] is True

    async def test_verify_client_not_found(self, client: AsyncClient, verifier_user: dict):
        """Test verifying a non-existent client."""
        verifier_id = verifier_user["id"]

        response = await client.post(f"/clients/nonexistent-id/verify?verified_by={verifier_id}")

        assert response.status_code == 404


# =============================================================================
# LIFECYCLE TESTS (Activate, Deactivate, Suspend, Terminate, Archive, Restore)
# =============================================================================


class TestActivateClient:
    """Tests for POST /clients/{client_id}/activate endpoint."""

    async def test_activate_pending_client(self, client: AsyncClient, test_client: dict):
        """Test activating a pending client."""
        client_id = test_client["id"]

        response = await client.post(f"/clients/{client_id}/activate")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "Active"
        assert data["is_active"] is True

    async def test_activate_already_active_fails(
        self, client: AsyncClient, test_client_active: dict
    ):
        """Test that activating an already active client fails."""
        client_id = test_client_active["id"]

        response = await client.post(f"/clients/{client_id}/activate")

        assert response.status_code == 409
        assert "already active" in response.json()["message"].lower()

    async def test_activate_not_found(self, client: AsyncClient):
        """Test activating non-existent client returns 404."""
        response = await client.post("/clients/nonexistent-id/activate")

        assert response.status_code == 404


class TestDeactivateClient:
    """Tests for POST /clients/{client_id}/deactivate endpoint."""

    async def test_deactivate_client_success(self, client: AsyncClient, test_client_active: dict):
        """Test deactivating an active client."""
        client_id = test_client_active["id"]

        response = await client.post(
            f"/clients/{client_id}/deactivate",
            json={"reason": "Contract ended"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "Inactive"

    async def test_deactivate_already_inactive_fails(
        self, client: AsyncClient, test_client_active: dict
    ):
        """Test that deactivating an already inactive client fails."""
        client_id = test_client_active["id"]

        # Deactivate first
        await client.post(
            f"/clients/{client_id}/deactivate",
            json={"reason": "First deactivation"},
        )

        # Try to deactivate again
        response = await client.post(
            f"/clients/{client_id}/deactivate",
            json={"reason": "Second deactivation"},
        )

        # 409 Conflict for state conflicts ("already" conditions)
        assert response.status_code == 409
        assert "already inactive" in response.json()["message"].lower()

    async def test_deactivate_not_found(self, client: AsyncClient):
        """Test deactivating non-existent client returns 404."""
        response = await client.post(
            "/clients/nonexistent-id/deactivate",
            json={"reason": "Test"},
        )

        assert response.status_code == 404


class TestSuspendClient:
    """Tests for POST /clients/{client_id}/suspend endpoint."""

    async def test_suspend_client_success(self, client: AsyncClient, test_client_active: dict):
        """Test suspending a client."""
        client_id = test_client_active["id"]

        response = await client.post(
            f"/clients/{client_id}/suspend",
            json={"reason": "Payment issues"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "Inactive"

    async def test_suspend_requires_reason(self, client: AsyncClient, test_client: dict):
        """Test that suspending requires a reason."""
        client_id = test_client["id"]

        response = await client.post(
            f"/clients/{client_id}/suspend",
            json={"reason": ""},
        )

        assert response.status_code == 422

    async def test_suspend_not_found(self, client: AsyncClient):
        """Test suspending non-existent client returns 404."""
        response = await client.post(
            "/clients/nonexistent-id/suspend",
            json={"reason": "Test"},
        )

        assert response.status_code == 404


class TestTerminateClient:
    """Tests for POST /clients/{client_id}/terminate endpoint."""

    async def test_terminate_client_success(self, client: AsyncClient, test_client: dict):
        """Test terminating a client."""
        client_id = test_client["id"]

        response = await client.post(
            f"/clients/{client_id}/terminate",
            json={"reason": "Company closed"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "Deleted"

    async def test_terminate_requires_reason(self, client: AsyncClient, test_client_2: dict):
        """Test that terminating requires a reason."""
        client_id = test_client_2["id"]

        response = await client.post(
            f"/clients/{client_id}/terminate",
            json={"reason": ""},
        )

        assert response.status_code == 422

    async def test_terminate_not_found(self, client: AsyncClient):
        """Test terminating non-existent client returns 404."""
        response = await client.post(
            "/clients/nonexistent-id/terminate",
            json={"reason": "Test"},
        )

        assert response.status_code == 404


class TestArchiveClient:
    """Tests for POST /clients/{client_id}/archive endpoint."""

    async def test_archive_client_success(self, client: AsyncClient, test_client: dict):
        """Test archiving a client."""
        client_id = test_client["id"]

        response = await client.post(f"/clients/{client_id}/archive")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "Archived"

    async def test_archive_already_archived_fails(self, client: AsyncClient, test_client: dict):
        """Test that archiving an already archived client fails."""
        client_id = test_client["id"]

        # Archive first
        await client.post(f"/clients/{client_id}/archive")

        # Try to archive again
        response = await client.post(f"/clients/{client_id}/archive")

        assert response.status_code == 409
        assert "already archived" in response.json()["message"].lower()

    async def test_archive_not_found(self, client: AsyncClient):
        """Test archiving non-existent client returns 404."""
        response = await client.post("/clients/nonexistent-id/archive")

        assert response.status_code == 404


class TestRestoreClient:
    """Tests for POST /clients/{client_id}/restore endpoint."""

    async def test_restore_archived_client(self, client: AsyncClient, test_client: dict):
        """Test restoring an archived client."""
        client_id = test_client["id"]

        # Archive first
        await client.post(f"/clients/{client_id}/archive")

        # Restore
        response = await client.post(f"/clients/{client_id}/restore")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "Active"

    async def test_restore_active_client_fails(self, client: AsyncClient, test_client_active: dict):
        """Test that restoring an already active client fails."""
        client_id = test_client_active["id"]

        response = await client.post(f"/clients/{client_id}/restore")

        assert response.status_code == 409

    async def test_restore_not_found(self, client: AsyncClient):
        """Test restoring non-existent client returns 404."""
        response = await client.post("/clients/nonexistent-id/restore")

        assert response.status_code == 404


# =============================================================================
# UPDATE TESTS
# =============================================================================


class TestUpdateClient:
    """Tests for PATCH /clients/{client_id} endpoint."""

    async def test_update_client_name(self, client: AsyncClient, test_client: dict):
        """Test updating client name."""
        client_id = test_client["id"]

        response = await client.patch(
            f"/clients/{client_id}",
            json={"name": "Updated Company Name"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Company Name"

    async def test_update_client_preferred_contact(self, client: AsyncClient, test_client: dict):
        """Test updating preferred contact method."""
        client_id = test_client["id"]

        response = await client.patch(
            f"/clients/{client_id}",
            json={"preferred_contact_method": "email"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["preferred_contact_method"] == "email"

    async def test_update_client_not_found(self, client: AsyncClient):
        """Test updating non-existent client returns 404."""
        response = await client.patch(
            "/clients/nonexistent-id",
            json={"name": "New Name"},
        )

        assert response.status_code == 404


class TestUpdateContactInfo:
    """Tests for PATCH /clients/{client_id}/contact-info endpoint."""

    async def test_update_contact_info_success(self, client: AsyncClient, test_client: dict):
        """Test updating contact information."""
        client_id = test_client["id"]

        response = await client.patch(
            f"/clients/{client_id}/contact-info",
            json={
                "contact_info": {
                    "phone": "+1-555-NEW-PHONE",
                    "email": "newemail@company.com",
                    "address": "456 New Street",
                }
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["contact_info"]["phone"] == "+1-555-NEW-PHONE"
        assert data["contact_info"]["email"] == "newemail@company.com"
        assert data["contact_info"]["address"] == "456 New Street"

    async def test_update_contact_info_not_found(self, client: AsyncClient):
        """Test updating contact info for non-existent client."""
        response = await client.patch(
            "/clients/nonexistent-id/contact-info",
            json={
                "contact_info": {
                    "phone": "+1-555-000-0000",
                }
            },
        )

        assert response.status_code == 404


class TestUpdateBillingAddress:
    """Tests for PATCH /clients/{client_id}/billing-address endpoint."""

    async def test_update_billing_address_success(self, client: AsyncClient, test_client: dict):
        """Test updating billing address."""
        client_id = test_client["id"]

        response = await client.patch(
            f"/clients/{client_id}/billing-address",
            json={
                "billing_address": {
                    "street": "789 Billing Ave",
                    "city": "Chicago",
                    "country": "USA",
                    "postal_code": "60601",
                }
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["billing_address"]["street"] == "789 Billing Ave"
        assert data["billing_address"]["city"] == "Chicago"

    async def test_update_billing_address_to_null(self, client: AsyncClient, test_client: dict):
        """Test removing billing address by setting to null."""
        client_id = test_client["id"]

        response = await client.patch(
            f"/clients/{client_id}/billing-address",
            json={"billing_address": None},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["billing_address"] is None

    async def test_update_billing_address_not_found(self, client: AsyncClient):
        """Test updating billing address for non-existent client."""
        response = await client.patch(
            "/clients/nonexistent-id/billing-address",
            json={
                "billing_address": {
                    "street": "Test St",
                    "city": "Test City",
                    "country": "Test Country",
                }
            },
        )

        assert response.status_code == 404


# =============================================================================
# STATS AND CHILDREN TESTS
# =============================================================================


class TestGetClientStats:
    """Tests for GET /clients/{client_id}/stats endpoint."""

    async def test_get_client_stats_success(
        self, client: AsyncClient, client_test_tenant: dict, test_client: dict
    ):
        """Test getting client statistics."""
        tenant_id = client_test_tenant["id"]
        client_id = test_client["id"]

        response = await client.get(f"/clients/{client_id}/stats?tenant_id={tenant_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["client_id"] == client_id
        assert "child_clients_count" in data
        assert "total_contracts_count" in data
        assert "active_contracts_count" in data
        assert "is_verified" in data
        assert "status" in data

    async def test_get_client_stats_with_children(
        self,
        client: AsyncClient,
        client_test_tenant: dict,
        test_parent_client: dict,
        test_child_client: dict,
    ):
        """Test getting stats for client with children."""
        tenant_id = client_test_tenant["id"]
        client_id = test_parent_client["id"]

        response = await client.get(f"/clients/{client_id}/stats?tenant_id={tenant_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["child_clients_count"] >= 1

    async def test_get_client_stats_reports_member_relation_breakdown(
        self, client: AsyncClient, client_test_tenant: dict, test_client: dict
    ):
        """Members are counted per relation; domestic partners and other dependents fold into "other"."""
        tenant_id = client_test_tenant["id"]
        client_id = test_client["id"]

        employee = await client.post(
            "/members",
            json={
                "client_id": client_id,
                "relation": "Employee",
                "display_label": "Employee One",
            },
        )
        assert employee.status_code == 201, employee.text
        employee_id = employee.json()["id"]

        for relation in ("Spouse", "Child", "DomesticPartner", "DependentOther"):
            dependent = await client.post(
                "/members",
                json={
                    "client_id": client_id,
                    "relation": relation,
                    "display_label": f"{relation} dependent",
                    "primary_employee_member_id": employee_id,
                },
            )
            assert dependent.status_code == 201, dependent.text

        response = await client.get(f"/clients/{client_id}/stats?tenant_id={tenant_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["employee_members_count"] == 1
        assert data["spouse_members_count"] == 1
        assert data["child_members_count"] == 1
        assert data["other_members_count"] == 2

    async def test_get_client_stats_not_found(self, client: AsyncClient, client_test_tenant: dict):
        """Test getting stats for non-existent client."""
        tenant_id = client_test_tenant["id"]

        response = await client.get(f"/clients/nonexistent-id/stats?tenant_id={tenant_id}")

        assert response.status_code == 404


class TestGetChildClients:
    """Tests for GET /clients/{client_id}/children endpoint."""

    async def test_get_child_clients_success(
        self,
        client: AsyncClient,
        client_test_tenant: dict,
        test_parent_client: dict,
        test_child_client: dict,
    ):
        """Test getting child clients."""
        tenant_id = client_test_tenant["id"]
        parent_id = test_parent_client["id"]

        response = await client.get(f"/clients/{parent_id}/children?tenant_id={tenant_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1
        assert len(data["items"]) >= 1
        assert all(c["parent_client_id"] == parent_id for c in data["items"])

    async def test_get_child_clients_empty(
        self, client: AsyncClient, client_test_tenant: dict, test_client: dict
    ):
        """Test getting child clients when none exist."""
        tenant_id = client_test_tenant["id"]
        client_id = test_client["id"]

        response = await client.get(f"/clients/{client_id}/children?tenant_id={tenant_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert data["items"] == []

    async def test_get_child_clients_parent_not_found(
        self, client: AsyncClient, client_test_tenant: dict
    ):
        """Test getting children for non-existent parent."""
        tenant_id = client_test_tenant["id"]

        response = await client.get(f"/clients/nonexistent-id/children?tenant_id={tenant_id}")

        assert response.status_code == 404


class TestGetClientUtilisationEvents:
    """Tests for GET /clients/{client_id}/utilisation-events endpoint."""

    async def _create_contract(self, client: AsyncClient, tenant_id: str, client_id: str) -> str:
        response = await client.post(
            f"/contracts/?tenant_id={tenant_id}",
            json={
                "client_id": client_id,
                "start_date": "2026-01-01",
                "end_date": "2026-12-31",
                "billing_rate": {"amount": "5000.00", "currency": "USD"},
                "payment_frequency": "Monthly",
                "is_auto_renew": False,
            },
        )
        assert response.status_code == 201
        return response.json()["id"]

    async def _record_event(
        self, client: AsyncClient, tenant_id: str, contract_id: str, occurred_on: str
    ) -> None:
        response = await client.post(
            f"/utilisation-events?tenant_id={tenant_id}",
            json={
                "contract_id": contract_id,
                "event_type": "SessionDelivered",
                "occurred_on": occurred_on,
                "units": 2,
            },
        )
        assert response.status_code == 201

    async def test_pages_events_newest_first_across_contracts(
        self, client: AsyncClient, client_test_tenant: dict, test_client: dict
    ):
        """Events from every contract owned by the client are paged together, newest first."""
        tenant_id = client_test_tenant["id"]
        client_id = test_client["id"]
        contract_id = await self._create_contract(client, tenant_id, client_id)
        for day in ("2026-03-01", "2026-03-05", "2026-03-10"):
            await self._record_event(client, tenant_id, contract_id, day)

        first_page = await client.get(
            f"/clients/{client_id}/utilisation-events?tenant_id={tenant_id}&limit=2"
        )
        assert first_page.status_code == 200
        first_data = first_page.json()
        assert first_data["total"] == 3
        assert first_data["has_more"] is True
        assert [item["occurred_on"] for item in first_data["items"]] == [
            "2026-03-10",
            "2026-03-05",
        ]

        second_page = await client.get(
            f"/clients/{client_id}/utilisation-events?tenant_id={tenant_id}&limit=2&page=2"
        )
        assert second_page.status_code == 200
        second_data = second_page.json()
        assert [item["occurred_on"] for item in second_data["items"]] == ["2026-03-01"]
        assert second_data["has_more"] is False

    async def test_empty_when_no_events_recorded(
        self, client: AsyncClient, client_test_tenant: dict, test_client: dict
    ):
        """A client with no recorded usage returns an empty page, not an error."""
        tenant_id = client_test_tenant["id"]
        client_id = test_client["id"]

        response = await client.get(
            f"/clients/{client_id}/utilisation-events?tenant_id={tenant_id}"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert data["items"] == []

    async def test_not_found_for_unknown_client(
        self, client: AsyncClient, client_test_tenant: dict
    ):
        """Test getting utilisation events for a non-existent client."""
        tenant_id = client_test_tenant["id"]

        response = await client.get(
            f"/clients/nonexistent-id/utilisation-events?tenant_id={tenant_id}"
        )

        assert response.status_code == 404


# =============================================================================
# INTEGRATION/FLOW TESTS
# =============================================================================


class TestClientLifecycleFlow:
    """Integration tests for complete client lifecycle flows."""

    async def test_full_lifecycle_pending_to_active_to_archived_to_restored(
        self, client: AsyncClient, client_test_tenant: dict
    ):
        """Test complete flow: create -> activate -> archive -> restore."""
        tenant_id = client_test_tenant["id"]

        # Create pending client
        create_response = await client.post(
            f"/clients/?tenant_id={tenant_id}",
            json={
                "name": "Lifecycle Test Client",
                "code": "LIFEC",
                "contact_info": {"phone": "+1-555-LIFECYCLE"},
            },
        )
        assert create_response.status_code == 201
        client_id = create_response.json()["id"]
        assert create_response.json()["status"] == "Pending"

        # Activate
        activate_response = await client.post(f"/clients/{client_id}/activate")
        assert activate_response.json()["status"] == "Active"

        # Archive
        archive_response = await client.post(f"/clients/{client_id}/archive")
        assert archive_response.json()["status"] == "Archived"

        # Restore
        restore_response = await client.post(f"/clients/{client_id}/restore")
        assert restore_response.json()["status"] == "Active"

    async def test_full_lifecycle_with_verification(
        self, client: AsyncClient, client_test_tenant: dict, verifier_user: dict
    ):
        """Test complete flow including verification."""
        tenant_id = client_test_tenant["id"]
        verifier_id = verifier_user["id"]

        # Create client
        create_response = await client.post(
            f"/clients/?tenant_id={tenant_id}",
            json={
                "name": "Verified Client",
                "code": "VERIF",
                "contact_info": {"email": "verified@client.com"},
            },
        )
        client_id = create_response.json()["id"]
        assert create_response.json()["is_verified"] is False

        # Verify
        verify_response = await client.post(
            f"/clients/{client_id}/verify?verified_by={verifier_id}"
        )
        assert verify_response.json()["is_verified"] is True

        # Activate
        activate_response = await client.post(f"/clients/{client_id}/activate")
        assert activate_response.json()["status"] == "Active"
        assert activate_response.json()["is_verified"] is True

    async def test_crud_operations_integration(self, client: AsyncClient, client_test_tenant: dict):
        """Test CRUD operations in sequence."""
        tenant_id = client_test_tenant["id"]

        # Create
        create_response = await client.post(
            f"/clients/?tenant_id={tenant_id}",
            json={
                "name": "CRUD Test Client",
                "code": "CCRUD",
                "contact_info": {"phone": "+1-555-CRUD-TEST"},
            },
        )
        client_id = create_response.json()["id"]

        # Read
        get_response = await client.get(f"/clients/{client_id}")
        assert get_response.json()["name"] == "CRUD Test Client"

        # Update name
        update_response = await client.patch(
            f"/clients/{client_id}",
            json={"name": "Updated CRUD Client"},
        )
        assert update_response.json()["name"] == "Updated CRUD Client"

        # Update contact info
        contact_response = await client.patch(
            f"/clients/{client_id}/contact-info",
            json={"contact_info": {"phone": "+1-555-UPDATED", "email": "updated@crud.com"}},
        )
        assert contact_response.json()["contact_info"]["email"] == "updated@crud.com"

        # List to verify it appears
        list_response = await client.get(f"/clients/?tenant_id={tenant_id}")
        client_names = [c["name"] for c in list_response.json()["items"]]
        assert "Updated CRUD Client" in client_names

        # Terminate (soft delete)
        terminate_response = await client.post(
            f"/clients/{client_id}/terminate",
            json={"reason": "End of test"},
        )
        assert terminate_response.json()["status"] == "Deleted"

    async def test_parent_child_relationship_flow(
        self, client: AsyncClient, client_test_tenant: dict
    ):
        """Test parent-child client relationships."""
        tenant_id = client_test_tenant["id"]

        # Create parent
        parent_response = await client.post(
            f"/clients/?tenant_id={tenant_id}",
            json={
                "name": "Corporate HQ",
                "code": "CORPH",
                "contact_info": {"phone": "+1-555-HQ-MAIN"},
            },
        )
        parent_id = parent_response.json()["id"]

        # Create multiple children
        child_ids = []
        for i in range(3):
            child_response = await client.post(
                f"/clients/?tenant_id={tenant_id}",
                json={
                    "name": f"Branch {i + 1}",
                    "code": f"BR{i + 1:03d}",
                    "contact_info": {"phone": f"+1-555-BRANCH-{i}"},
                    "parent_client_id": parent_id,
                },
            )
            child_ids.append(child_response.json()["id"])

        # Verify children
        children_response = await client.get(f"/clients/{parent_id}/children?tenant_id={tenant_id}")
        assert children_response.json()["total"] == 3

        # Verify stats
        stats_response = await client.get(f"/clients/{parent_id}/stats?tenant_id={tenant_id}")
        assert stats_response.json()["child_clients_count"] == 3
