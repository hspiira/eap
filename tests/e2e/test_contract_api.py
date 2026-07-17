"""
Contract API End-to-End Tests

Comprehensive tests for all contract endpoints covering:
- CRUD operations (Create, Get, List, Update)
- Lifecycle transitions (Activate, Sign, Renew, Terminate, Archive, Restore)
- Payment status updates
- Client-specific queries
"""

from datetime import UTC, datetime, timedelta

import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio


# =============================================================================
# CREATE CONTRACT TESTS
# =============================================================================


class TestCreateContract:
    """Tests for POST /contracts/ endpoint."""

    async def test_create_contract_success(
        self,
        client: AsyncClient,
        contract_test_tenant: dict,
        contract_test_client: dict,
    ):
        """Test creating a contract with full data."""
        tenant_id = contract_test_tenant["id"]
        start_date = datetime.now(UTC).isoformat()
        end_date = (datetime.now(UTC) + timedelta(days=365)).isoformat()

        response = await client.post(
            f"/contracts/?tenant_id={tenant_id}",
            json={
                "client_id": contract_test_client["id"],
                "start_date": start_date,
                "end_date": end_date,
                "billing_rate": {
                    "amount": "5000.00",
                    "currency": "USD",
                },
                "payment_frequency": "Monthly",
                "is_auto_renew": False,
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["client_id"] == contract_test_client["id"]
        assert data["tenant_id"] == tenant_id
        assert data["status"] == "Draft"
        assert data["payment_status"] == "Pending"
        assert data["billing_rate"]["amount"] == "5000.00"
        assert data["billing_rate"]["currency"] == "USD"
        assert data["payment_frequency"] == "Monthly"
        assert data["is_auto_renew"] is False
        assert data["is_active"] is False

    async def test_create_contract_with_auto_renew(
        self,
        client: AsyncClient,
        contract_test_tenant: dict,
        contract_test_client: dict,
    ):
        """Test creating a contract with auto-renew enabled."""
        tenant_id = contract_test_tenant["id"]
        start_date = datetime.now(UTC).isoformat()
        end_date = (datetime.now(UTC) + timedelta(days=365)).isoformat()

        response = await client.post(
            f"/contracts/?tenant_id={tenant_id}",
            json={
                "client_id": contract_test_client["id"],
                "start_date": start_date,
                "end_date": end_date,
                "billing_rate": {
                    "amount": "10000.00",
                    "currency": "EUR",
                },
                "payment_frequency": "Quarterly",
                "is_auto_renew": True,
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["is_auto_renew"] is True
        assert data["payment_frequency"] == "Quarterly"

    async def test_create_contract_requires_tenant_id(
        self, client: AsyncClient, contract_test_client: dict
    ):
        """Test that creating a contract requires tenant_id."""
        start_date = datetime.now(UTC).isoformat()
        end_date = (datetime.now(UTC) + timedelta(days=365)).isoformat()

        response = await client.post(
            "/contracts/",
            json={
                "client_id": contract_test_client["id"],
                "start_date": start_date,
                "end_date": end_date,
                "billing_rate": {"amount": "1000.00", "currency": "USD"},
                "payment_frequency": "Monthly",
            },
        )

        assert response.status_code == 422


# =============================================================================
# GET CONTRACT TESTS
# =============================================================================


class TestGetContract:
    """Tests for GET /contracts/{contract_id} endpoint."""

    async def test_get_contract_by_id_success(
        self, client: AsyncClient, test_contract: dict
    ):
        """Test getting a contract by ID."""
        contract_id = test_contract["id"]

        response = await client.get(f"/contracts/{contract_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == contract_id
        assert data["billing_rate"]["amount"] == "5000.00"

    async def test_get_contract_not_found(
        self, client: AsyncClient, contract_test_tenant: dict
    ):
        """Test getting a non-existent contract returns 404."""
        response = await client.get("/contracts/nonexistent-id-12345")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()


class TestGetContractsByClient:
    """Tests for GET /contracts/client/{client_id} endpoint."""

    async def test_get_contracts_by_client_success(
        self,
        client: AsyncClient,
        contract_test_tenant: dict,
        contract_test_client: dict,
        test_contract: dict,
    ):
        """Test getting all contracts for a client."""
        tenant_id = contract_test_tenant["id"]
        client_id = contract_test_client["id"]

        response = await client.get(
            f"/contracts/client/{client_id}?tenant_id={tenant_id}"
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        assert all(c["client_id"] == client_id for c in data)

    async def test_get_contracts_by_client_empty(
        self, client: AsyncClient, contract_test_tenant: dict
    ):
        """Test getting contracts for client with none."""
        tenant_id = contract_test_tenant["id"]

        # Create a client with no contracts
        client_response = await client.post(
            f"/clients/?tenant_id={tenant_id}",
            json={
                "name": "No Contract Client",
                "contact_info": {"phone": "+1-555-NOCON"},
            },
        )
        client_id = client_response.json()["id"]

        response = await client.get(
            f"/contracts/client/{client_id}?tenant_id={tenant_id}"
        )

        assert response.status_code == 200
        assert response.json() == []


class TestGetActiveContractByClient:
    """Tests for GET /contracts/client/{client_id}/active endpoint."""

    async def test_get_active_contract_success(
        self,
        client: AsyncClient,
        contract_test_tenant: dict,
        contract_test_client: dict,
        test_contract_active: dict,
    ):
        """Test getting active contract for a client."""
        tenant_id = contract_test_tenant["id"]
        client_id = contract_test_client["id"]

        response = await client.get(
            f"/contracts/client/{client_id}/active?tenant_id={tenant_id}"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["client_id"] == client_id
        assert data["status"] == "Active"

    async def test_get_active_contract_not_found(
        self, client: AsyncClient, contract_test_tenant: dict, contract_test_client_2: dict
    ):
        """Test getting active contract when none exists."""
        tenant_id = contract_test_tenant["id"]
        client_id = contract_test_client_2["id"]

        response = await client.get(
            f"/contracts/client/{client_id}/active?tenant_id={tenant_id}"
        )

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()


# =============================================================================
# LIST CONTRACTS TESTS
# =============================================================================


class TestListContracts:
    """Tests for GET /contracts/ endpoint."""

    async def test_list_contracts_requires_tenant_id(self, client: AsyncClient):
        """Test that listing contracts requires tenant_id parameter."""
        response = await client.get("/contracts/")

        assert response.status_code == 422

    async def test_list_contracts_empty(
        self, client: AsyncClient, contract_test_tenant: dict
    ):
        """Test listing contracts when none exist."""
        # Create a new tenant with no contracts
        new_tenant = await client.post(
            "/tenants/",
            json={"name": "Empty Contract Tenant", "code": "empty-con"},
        )
        tenant_id = new_tenant.json()["id"]

        response = await client.get(f"/contracts/?tenant_id={tenant_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["items"] == []
        assert data["total"] == 0

    async def test_list_contracts_success(
        self,
        client: AsyncClient,
        contract_test_tenant: dict,
        test_contract: dict,
        test_contract_2: dict,
    ):
        """Test listing contracts with results."""
        tenant_id = contract_test_tenant["id"]

        response = await client.get(f"/contracts/?tenant_id={tenant_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 2
        assert len(data["items"]) >= 2

    async def test_list_contracts_pagination(
        self, client: AsyncClient, contract_test_tenant: dict, test_contract: dict
    ):
        """Test contract list pagination."""
        tenant_id = contract_test_tenant["id"]

        response = await client.get(
            f"/contracts/?tenant_id={tenant_id}&page=1&limit=1"
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) <= 1
        assert data["page"] == 1
        assert data["limit"] == 1

    async def test_list_contracts_filter_by_status(
        self,
        client: AsyncClient,
        contract_test_tenant: dict,
        test_contract: dict,
        test_contract_active: dict,
    ):
        """Test filtering contracts by status."""
        tenant_id = contract_test_tenant["id"]

        # Filter by Active status
        response = await client.get(
            f"/contracts/?tenant_id={tenant_id}&status=Active"
        )
        data = response.json()

        assert response.status_code == 200
        assert all(c["status"] == "Active" for c in data["items"])

    async def test_list_contracts_filter_by_client(
        self,
        client: AsyncClient,
        contract_test_tenant: dict,
        contract_test_client: dict,
        test_contract: dict,
    ):
        """Test filtering contracts by client."""
        tenant_id = contract_test_tenant["id"]
        client_id = contract_test_client["id"]

        response = await client.get(
            f"/contracts/?tenant_id={tenant_id}&client_id={client_id}"
        )
        data = response.json()

        assert response.status_code == 200
        assert all(c["client_id"] == client_id for c in data["items"])


# =============================================================================
# LIFECYCLE TESTS (Activate, Sign, Renew, Terminate, Archive, Restore)
# =============================================================================


class TestActivateContract:
    """Tests for POST /contracts/{contract_id}/activate endpoint."""

    async def test_activate_draft_contract(
        self, client: AsyncClient, test_contract: dict
    ):
        """Test activating a draft contract."""
        contract_id = test_contract["id"]

        response = await client.post(f"/contracts/{contract_id}/activate")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "Active"
        assert data["is_active"] is True

    async def test_activate_already_active_fails(
        self, client: AsyncClient, test_contract_active: dict
    ):
        """Test that activating an already active contract fails."""
        contract_id = test_contract_active["id"]

        response = await client.post(f"/contracts/{contract_id}/activate")

        assert response.status_code == 409
        assert "already active" in response.json()["detail"].lower()

    async def test_activate_not_found(self, client: AsyncClient):
        """Test activating non-existent contract returns 404."""
        response = await client.post("/contracts/nonexistent-id/activate")

        assert response.status_code == 404


class TestSignContract:
    """Tests for POST /contracts/{contract_id}/sign endpoint."""

    async def test_sign_contract_success(
        self, client: AsyncClient, test_contract: dict
    ):
        """Test signing a contract."""
        contract_id = test_contract["id"]

        response = await client.post(
            f"/contracts/{contract_id}/sign",
            json={"signed_by": "John Smith, CEO"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["signed_by"] == "John Smith, CEO"
        assert data["signed_at"] is not None
        # Contract should auto-activate when signed
        assert data["status"] == "Active"

    async def test_sign_contract_requires_signer(
        self, client: AsyncClient, test_contract: dict
    ):
        """Test that signing requires signer name."""
        contract_id = test_contract["id"]

        response = await client.post(
            f"/contracts/{contract_id}/sign",
            json={"signed_by": ""},
        )

        assert response.status_code == 422

    async def test_sign_already_signed_fails(
        self, client: AsyncClient, test_contract: dict
    ):
        """Test that signing an already signed contract fails."""
        contract_id = test_contract["id"]

        # Sign first
        await client.post(
            f"/contracts/{contract_id}/sign",
            json={"signed_by": "First Signer"},
        )

        # Try to sign again
        response = await client.post(
            f"/contracts/{contract_id}/sign",
            json={"signed_by": "Second Signer"},
        )

        # 409 Conflict for state conflicts ("already" conditions)
        assert response.status_code == 409
        assert "already signed" in response.json()["detail"].lower()

    async def test_sign_not_found(self, client: AsyncClient):
        """Test signing non-existent contract returns 404."""
        response = await client.post(
            "/contracts/nonexistent-id/sign",
            json={"signed_by": "Test"},
        )

        assert response.status_code == 404


class TestRenewContract:
    """Tests for POST /contracts/{contract_id}/renew endpoint."""

    async def test_renew_contract_success(
        self, client: AsyncClient, test_contract_active: dict
    ):
        """Test renewing a contract."""
        contract_id = test_contract_active["id"]
        new_end_date = (datetime.now(UTC) + timedelta(days=730)).isoformat()

        response = await client.post(
            f"/contracts/{contract_id}/renew",
            json={"new_end_date": new_end_date},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "Renewed"

    async def test_renew_contract_with_new_rate(
        self, client: AsyncClient, test_contract_active: dict
    ):
        """Test renewing a contract with new rate."""
        contract_id = test_contract_active["id"]
        new_end_date = (datetime.now(UTC) + timedelta(days=730)).isoformat()

        response = await client.post(
            f"/contracts/{contract_id}/renew",
            json={
                "new_end_date": new_end_date,
                "new_rate": {
                    "amount": "12000.00",
                    "currency": "USD",
                },
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["billing_rate"]["amount"] == "12000.00"

    async def test_renew_not_found(self, client: AsyncClient):
        """Test renewing non-existent contract returns 404."""
        new_end_date = (datetime.now(UTC) + timedelta(days=730)).isoformat()

        response = await client.post(
            "/contracts/nonexistent-id/renew",
            json={"new_end_date": new_end_date},
        )

        assert response.status_code == 404


class TestTerminateContract:
    """Tests for POST /contracts/{contract_id}/terminate endpoint."""

    async def test_terminate_contract_success(
        self, client: AsyncClient, test_contract: dict
    ):
        """Test terminating a contract."""
        contract_id = test_contract["id"]

        response = await client.post(
            f"/contracts/{contract_id}/terminate",
            json={"reason": "Client requested termination"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "Terminated"
        assert data["termination_reason"] == "Client requested termination"

    async def test_terminate_requires_reason(
        self, client: AsyncClient, test_contract_2: dict
    ):
        """Test that terminating requires a reason."""
        contract_id = test_contract_2["id"]

        response = await client.post(
            f"/contracts/{contract_id}/terminate",
            json={"reason": ""},
        )

        assert response.status_code == 422

    async def test_terminate_not_found(self, client: AsyncClient):
        """Test terminating non-existent contract returns 404."""
        response = await client.post(
            "/contracts/nonexistent-id/terminate",
            json={"reason": "Test"},
        )

        assert response.status_code == 404


class TestArchiveContract:
    """Tests for POST /contracts/{contract_id}/archive endpoint."""

    async def test_archive_contract_success(
        self, client: AsyncClient, test_contract: dict
    ):
        """Test archiving a contract."""
        contract_id = test_contract["id"]

        response = await client.post(f"/contracts/{contract_id}/archive")

        assert response.status_code == 200

    async def test_archive_not_found(self, client: AsyncClient):
        """Test archiving non-existent contract returns 404."""
        response = await client.post("/contracts/nonexistent-id/archive")

        assert response.status_code == 404


class TestRestoreContract:
    """Tests for POST /contracts/{contract_id}/restore endpoint."""

    async def test_restore_not_found(self, client: AsyncClient):
        """Test restoring non-existent contract returns 404."""
        response = await client.post("/contracts/nonexistent-id/restore")

        assert response.status_code == 404


# =============================================================================
# UPDATE TESTS
# =============================================================================


class TestUpdateContract:
    """Tests for PATCH /contracts/{contract_id} endpoint."""

    async def test_update_contract_billing_rate(
        self, client: AsyncClient, test_contract: dict
    ):
        """Test updating contract billing rate."""
        contract_id = test_contract["id"]

        response = await client.patch(
            f"/contracts/{contract_id}",
            json={
                "billing_rate": {
                    "amount": "7500.00",
                    "currency": "USD",
                }
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["billing_rate"]["amount"] == "7500.00"

    async def test_update_contract_payment_frequency(
        self, client: AsyncClient, test_contract: dict
    ):
        """Test updating contract payment frequency."""
        contract_id = test_contract["id"]

        response = await client.patch(
            f"/contracts/{contract_id}",
            json={"payment_frequency": "Quarterly"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["payment_frequency"] == "Quarterly"

    async def test_update_contract_auto_renew(
        self, client: AsyncClient, test_contract: dict
    ):
        """Test updating contract auto-renew setting."""
        contract_id = test_contract["id"]

        response = await client.patch(
            f"/contracts/{contract_id}",
            json={"is_auto_renew": True},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["is_auto_renew"] is True

    async def test_update_contract_not_found(self, client: AsyncClient):
        """Test updating non-existent contract returns 404."""
        response = await client.patch(
            "/contracts/nonexistent-id",
            json={"is_auto_renew": True},
        )

        assert response.status_code == 404


class TestUpdatePaymentStatus:
    """Tests for PATCH /contracts/{contract_id}/payment-status endpoint."""

    async def test_update_payment_status_success(
        self, client: AsyncClient, test_contract_active: dict
    ):
        """Test updating contract payment status."""
        contract_id = test_contract_active["id"]

        response = await client.patch(
            f"/contracts/{contract_id}/payment-status",
            json={"payment_status": "Paid"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["payment_status"] == "Paid"

    async def test_update_payment_status_overdue(
        self, client: AsyncClient, test_contract: dict
    ):
        """Test updating payment status to overdue."""
        contract_id = test_contract["id"]

        response = await client.patch(
            f"/contracts/{contract_id}/payment-status",
            json={"payment_status": "Overdue"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["payment_status"] == "Overdue"

    async def test_update_payment_status_not_found(self, client: AsyncClient):
        """Test updating payment status for non-existent contract."""
        response = await client.patch(
            "/contracts/nonexistent-id/payment-status",
            json={"payment_status": "Paid"},
        )

        assert response.status_code == 404


# =============================================================================
# INTEGRATION/FLOW TESTS
# =============================================================================


class TestContractLifecycleFlow:
    """Integration tests for complete contract lifecycle flows."""

    async def test_full_lifecycle_draft_to_signed_to_renewed(
        self, client: AsyncClient, contract_test_tenant: dict, contract_test_client: dict
    ):
        """Test complete flow: create -> sign -> renew."""
        tenant_id = contract_test_tenant["id"]
        start_date = datetime.now(UTC).isoformat()
        end_date = (datetime.now(UTC) + timedelta(days=365)).isoformat()

        # Create draft contract
        create_response = await client.post(
            f"/contracts/?tenant_id={tenant_id}",
            json={
                "client_id": contract_test_client["id"],
                "start_date": start_date,
                "end_date": end_date,
                "billing_rate": {"amount": "5000.00", "currency": "USD"},
                "payment_frequency": "Monthly",
            },
        )
        assert create_response.status_code == 201
        contract_id = create_response.json()["id"]
        assert create_response.json()["status"] == "Draft"

        # Sign contract (auto-activates)
        sign_response = await client.post(
            f"/contracts/{contract_id}/sign",
            json={"signed_by": "Jane Doe, CFO"},
        )
        assert sign_response.json()["status"] == "Active"
        assert sign_response.json()["signed_by"] == "Jane Doe, CFO"

        # Renew contract
        new_end_date = (datetime.now(UTC) + timedelta(days=730)).isoformat()
        renew_response = await client.post(
            f"/contracts/{contract_id}/renew",
            json={
                "new_end_date": new_end_date,
                "new_rate": {"amount": "6000.00", "currency": "USD"},
            },
        )
        assert renew_response.json()["status"] == "Renewed"
        assert renew_response.json()["billing_rate"]["amount"] == "6000.00"

    async def test_full_lifecycle_activate_to_terminate(
        self, client: AsyncClient, contract_test_tenant: dict, contract_test_client: dict
    ):
        """Test complete flow: create -> activate -> terminate."""
        tenant_id = contract_test_tenant["id"]
        start_date = datetime.now(UTC).isoformat()
        end_date = (datetime.now(UTC) + timedelta(days=365)).isoformat()

        # Create draft contract
        create_response = await client.post(
            f"/contracts/?tenant_id={tenant_id}",
            json={
                "client_id": contract_test_client["id"],
                "start_date": start_date,
                "end_date": end_date,
                "billing_rate": {"amount": "8000.00", "currency": "USD"},
                "payment_frequency": "Monthly",
            },
        )
        contract_id = create_response.json()["id"]

        # Activate
        activate_response = await client.post(f"/contracts/{contract_id}/activate")
        assert activate_response.json()["status"] == "Active"

        # Terminate
        terminate_response = await client.post(
            f"/contracts/{contract_id}/terminate",
            json={"reason": "Client closed business"},
        )
        assert terminate_response.json()["status"] == "Terminated"
        assert terminate_response.json()["termination_reason"] == "Client closed business"

    async def test_payment_lifecycle(
        self, client: AsyncClient, contract_test_tenant: dict, contract_test_client: dict
    ):
        """Test payment status transitions."""
        tenant_id = contract_test_tenant["id"]
        start_date = datetime.now(UTC).isoformat()
        end_date = (datetime.now(UTC) + timedelta(days=365)).isoformat()

        # Create and activate contract
        create_response = await client.post(
            f"/contracts/?tenant_id={tenant_id}",
            json={
                "client_id": contract_test_client["id"],
                "start_date": start_date,
                "end_date": end_date,
                "billing_rate": {"amount": "4000.00", "currency": "USD"},
                "payment_frequency": "Monthly",
            },
        )
        contract_id = create_response.json()["id"]
        assert create_response.json()["payment_status"] == "Pending"

        await client.post(f"/contracts/{contract_id}/activate")

        # Update to Paid
        paid_response = await client.patch(
            f"/contracts/{contract_id}/payment-status",
            json={"payment_status": "Paid"},
        )
        assert paid_response.json()["payment_status"] == "Paid"

        # Update to Overdue
        overdue_response = await client.patch(
            f"/contracts/{contract_id}/payment-status",
            json={"payment_status": "Overdue"},
        )
        assert overdue_response.json()["payment_status"] == "Overdue"

    async def test_crud_operations_integration(
        self, client: AsyncClient, contract_test_tenant: dict, contract_test_client: dict
    ):
        """Test CRUD operations in sequence."""
        tenant_id = contract_test_tenant["id"]
        start_date = datetime.now(UTC).isoformat()
        end_date = (datetime.now(UTC) + timedelta(days=365)).isoformat()

        # Create
        create_response = await client.post(
            f"/contracts/?tenant_id={tenant_id}",
            json={
                "client_id": contract_test_client["id"],
                "start_date": start_date,
                "end_date": end_date,
                "billing_rate": {"amount": "3500.00", "currency": "USD"},
                "payment_frequency": "Monthly",
                "is_auto_renew": False,
            },
        )
        contract_id = create_response.json()["id"]

        # Read
        get_response = await client.get(f"/contracts/{contract_id}")
        assert get_response.json()["billing_rate"]["amount"] == "3500.00"

        # Update billing rate
        update_response = await client.patch(
            f"/contracts/{contract_id}",
            json={
                "billing_rate": {"amount": "4000.00", "currency": "USD"},
                "is_auto_renew": True,
            },
        )
        assert update_response.json()["billing_rate"]["amount"] == "4000.00"
        assert update_response.json()["is_auto_renew"] is True

        # Verify in list
        list_response = await client.get(f"/contracts/?tenant_id={tenant_id}")
        contract_ids = [c["id"] for c in list_response.json()["items"]]
        assert contract_id in contract_ids

        # Terminate
        terminate_response = await client.post(
            f"/contracts/{contract_id}/terminate",
            json={"reason": "End of test"},
        )
        assert terminate_response.json()["status"] == "Terminated"
