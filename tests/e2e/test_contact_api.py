"""
Contact API End-to-End Tests

Comprehensive tests for all contact endpoints covering:
- CRUD operations
- Lifecycle (activate, deactivate)
- Client-contact relationships
"""

import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio


# =============================================================================
# CREATE CONTACT TESTS
# =============================================================================


class TestCreateContact:
    """Tests for POST /contacts/ endpoint."""

    async def test_create_contact_success(self, client: AsyncClient):
        """Test creating a contact."""
        # Create tenant
        tenant_resp = await client.post(
            "/tenants/",
            json={"name": "Contact Test Tenant", "code": "contact-test"},
        )
        tenant_id = tenant_resp.json()["id"]

        # Create client first
        client_resp = await client.post(
            f"/clients/?tenant_id={tenant_id}",
            json={
                "name": "Test Client Co",
                "code": "TSTC",
                "contact_info": {"phone": "+1-555-0000", "email": "info@testclient.com"},
            },
        )
        assert client_resp.status_code == 201
        client_id = client_resp.json()["id"]

        response = await client.post(
            f"/contacts/?tenant_id={tenant_id}",
            json={
                "client_id": client_id,
                "name": "John Smith",
                "title": "HR Director",
                "email": "john.smith@example.com",
                "phone": "+1-555-0100",
                "department": "Human Resources",
                "is_primary": True,
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "John Smith"
        assert data["email"] == "john.smith@example.com"
        assert data["is_primary"] is True
        assert data["is_active"] is True

    async def test_create_contact_requires_tenant_id(self, client: AsyncClient):
        """Test that creating a contact requires tenant_id."""
        response = await client.post(
            "/contacts/",
            json={"client_id": "some-id", "name": "Test Contact"},
        )

        assert response.status_code == 422


class TestGetContact:
    """Tests for GET /contacts/{contact_id} endpoint."""

    async def test_get_contact_not_found(self, client: AsyncClient):
        """Test getting a non-existent contact returns 404."""
        response = await client.get("/contacts/nonexistent-id")

        assert response.status_code == 404


class TestListContacts:
    """Tests for GET /contacts/ endpoint."""

    async def test_list_contacts_requires_tenant_id(self, client: AsyncClient):
        """Test that listing contacts requires tenant_id."""
        response = await client.get("/contacts/")

        assert response.status_code == 422

    async def test_list_contacts_empty(self, client: AsyncClient):
        """Test listing contacts when none exist."""
        tenant_resp = await client.post(
            "/tenants/",
            json={"name": "Empty Contact Tenant", "code": "empty-con"},
        )
        tenant_id = tenant_resp.json()["id"]

        response = await client.get(f"/contacts/?tenant_id={tenant_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["items"] == []
        assert data["total"] == 0


class TestUpdateContact:
    """Tests for PATCH /contacts/{contact_id} endpoint."""

    async def test_update_contact_not_found(self, client: AsyncClient):
        """Test updating non-existent contact."""
        response = await client.patch(
            "/contacts/nonexistent-id",
            json={"name": "Updated Contact"},
        )

        assert response.status_code in [400, 404]


class TestActivateContact:
    """Tests for POST /contacts/{contact_id}/activate endpoint."""

    async def test_activate_contact_not_found(self, client: AsyncClient):
        """Test activating non-existent contact returns 404."""
        response = await client.post("/contacts/nonexistent-id/activate")

        assert response.status_code == 404


class TestDeactivateContact:
    """Tests for POST /contacts/{contact_id}/deactivate endpoint."""

    async def test_deactivate_contact_not_found(self, client: AsyncClient):
        """Test deactivating non-existent contact returns 404."""
        response = await client.post("/contacts/nonexistent-id/deactivate")

        assert response.status_code == 404


class TestGetContactsByClient:
    """Tests for GET /contacts/client/{client_id} endpoint."""

    async def test_get_contacts_by_client_requires_tenant_id(self, client: AsyncClient):
        """Test that getting contacts by client requires tenant_id."""
        response = await client.get("/contacts/client/some-client-id")

        assert response.status_code == 422

    async def test_get_contacts_by_client_empty(self, client: AsyncClient):
        """Test getting contacts for a client with no contacts."""
        tenant_resp = await client.post(
            "/tenants/",
            json={"name": "Client Contact Tenant", "code": "cli-con"},
        )
        tenant_id = tenant_resp.json()["id"]

        response = await client.get(
            f"/contacts/client/some-client-id?tenant_id={tenant_id}"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["items"] == []


class TestGetPrimaryContact:
    """Tests for GET /contacts/client/{client_id}/primary endpoint."""

    async def test_get_primary_contact_not_found(self, client: AsyncClient):
        """Test getting primary contact when none exists."""
        tenant_resp = await client.post(
            "/tenants/",
            json={"name": "Primary Contact Tenant", "code": "pri-con"},
        )
        tenant_id = tenant_resp.json()["id"]

        response = await client.get(
            f"/contacts/client/some-client-id/primary?tenant_id={tenant_id}"
        )

        assert response.status_code == 404


# =============================================================================
# INTEGRATION TESTS
# =============================================================================


class TestContactIntegration:
    """Integration tests for contact workflows."""

    async def test_contact_crud_flow(self, client: AsyncClient):
        """Test complete contact CRUD flow."""
        # Create tenant
        tenant_resp = await client.post(
            "/tenants/",
            json={"name": "Contact CRUD Tenant", "code": "con-crud"},
        )
        tenant_id = tenant_resp.json()["id"]

        # Create client
        client_resp = await client.post(
            f"/clients/?tenant_id={tenant_id}",
            json={
                "name": "Contact Test Client",
                "code": "CTTC",
                "contact_info": {"email": "info@ctc.com"},
            },
        )
        assert client_resp.status_code == 201
        client_id = client_resp.json()["id"]

        # Create contact
        create_resp = await client.post(
            f"/contacts/?tenant_id={tenant_id}",
            json={
                "client_id": client_id,
                "name": "Jane Doe",
                "email": "jane@example.com",
                "is_primary": True,
            },
        )
        assert create_resp.status_code == 201
        contact_id = create_resp.json()["id"]

        # Get contact
        get_resp = await client.get(f"/contacts/{contact_id}")
        assert get_resp.status_code == 200
        assert get_resp.json()["name"] == "Jane Doe"

        # Update contact
        update_resp = await client.patch(
            f"/contacts/{contact_id}",
            json={"phone": "+1-555-0200"},
        )
        assert update_resp.status_code == 200

        # List contacts
        list_resp = await client.get(f"/contacts/?tenant_id={tenant_id}")
        assert list_resp.status_code == 200
        assert list_resp.json()["total"] >= 1

        # Get contacts by client
        client_contacts = await client.get(
            f"/contacts/client/{client_id}?tenant_id={tenant_id}"
        )
        assert client_contacts.status_code == 200
        assert client_contacts.json()["total"] >= 1

        # Get primary contact
        primary_resp = await client.get(
            f"/contacts/client/{client_id}/primary?tenant_id={tenant_id}"
        )
        assert primary_resp.status_code == 200
        assert primary_resp.json()["is_primary"] is True

        # Deactivate contact
        deactivate_resp = await client.post(f"/contacts/{contact_id}/deactivate")
        assert deactivate_resp.status_code == 200

        # Activate contact
        activate_resp = await client.post(f"/contacts/{contact_id}/activate")
        assert activate_resp.status_code == 200

    async def test_multiple_contacts_per_client(self, client: AsyncClient):
        """Test multiple contacts for one client."""
        # Create tenant
        tenant_resp = await client.post(
            "/tenants/",
            json={"name": "Multi Contact Tenant", "code": "multi-con"},
        )
        tenant_id = tenant_resp.json()["id"]

        # Create client
        client_resp = await client.post(
            f"/clients/?tenant_id={tenant_id}",
            json={
                "name": "Multi Contact Client",
                "code": "MCC",
                "contact_info": {"email": "info@mcc.com"},
            },
        )
        assert client_resp.status_code == 201
        client_id = client_resp.json()["id"]

        # Create multiple contacts
        contacts = [
            {"name": "Contact 1", "email": "c1@example.com", "is_primary": True},
            {"name": "Contact 2", "email": "c2@example.com", "is_primary": False},
            {"name": "Contact 3", "email": "c3@example.com", "is_primary": False},
        ]

        for contact_data in contacts:
            resp = await client.post(
                f"/contacts/?tenant_id={tenant_id}",
                json={"client_id": client_id, **contact_data},
            )
            assert resp.status_code == 201

        # List contacts for client
        list_resp = await client.get(
            f"/contacts/client/{client_id}?tenant_id={tenant_id}"
        )
        assert list_resp.json()["total"] == 3
