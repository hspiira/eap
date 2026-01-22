"""
Client Tag API End-to-End Tests

Comprehensive tests for all client tag endpoints covering:
- CRUD operations
- Lifecycle (activate, deactivate)
"""

import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio


# =============================================================================
# CREATE CLIENT TAG TESTS
# =============================================================================


class TestCreateClientTag:
    """Tests for POST /client-tags/ endpoint."""

    async def test_create_tag_success(self, client: AsyncClient):
        """Test creating a client tag."""
        tenant_resp = await client.post(
            "/tenants/",
            json={"name": "Tag Test Tenant", "code": "tag-test"},
        )
        tenant_id = tenant_resp.json()["id"]

        response = await client.post(
            f"/client-tags/?tenant_id={tenant_id}",
            json={
                "name": "VIP",
                "description": "VIP clients",
                "color": "#FFD700",
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "VIP"
        assert data["color"] == "#FFD700"
        assert data["is_active"] is True

    async def test_create_tag_requires_tenant_id(self, client: AsyncClient):
        """Test that creating a tag requires tenant_id."""
        response = await client.post(
            "/client-tags/",
            json={"name": "Test Tag"},
        )

        assert response.status_code == 422


class TestGetClientTag:
    """Tests for GET /client-tags/{tag_id} endpoint."""

    async def test_get_tag_not_found(self, client: AsyncClient):
        """Test getting a non-existent tag returns 404."""
        response = await client.get("/client-tags/nonexistent-id")

        assert response.status_code == 404


class TestListClientTags:
    """Tests for GET /client-tags/ endpoint."""

    async def test_list_tags_requires_tenant_id(self, client: AsyncClient):
        """Test that listing tags requires tenant_id."""
        response = await client.get("/client-tags/")

        assert response.status_code == 422

    async def test_list_tags_empty(self, client: AsyncClient):
        """Test listing tags when none exist."""
        tenant_resp = await client.post(
            "/tenants/",
            json={"name": "Empty Tag Tenant", "code": "empty-tag"},
        )
        tenant_id = tenant_resp.json()["id"]

        response = await client.get(f"/client-tags/?tenant_id={tenant_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["items"] == []
        assert data["total"] == 0


class TestUpdateClientTag:
    """Tests for PATCH /client-tags/{tag_id} endpoint."""

    async def test_update_tag_not_found(self, client: AsyncClient):
        """Test updating non-existent tag."""
        response = await client.patch(
            "/client-tags/nonexistent-id",
            json={"name": "Updated Tag"},
        )

        assert response.status_code in [400, 404]


class TestActivateClientTag:
    """Tests for POST /client-tags/{tag_id}/activate endpoint."""

    async def test_activate_tag_not_found(self, client: AsyncClient):
        """Test activating non-existent tag returns 404."""
        response = await client.post("/client-tags/nonexistent-id/activate")

        assert response.status_code == 404


class TestDeactivateClientTag:
    """Tests for POST /client-tags/{tag_id}/deactivate endpoint."""

    async def test_deactivate_tag_not_found(self, client: AsyncClient):
        """Test deactivating non-existent tag returns 404."""
        response = await client.post("/client-tags/nonexistent-id/deactivate")

        assert response.status_code == 404


class TestCheckClientTagNameAvailability:
    """Tests for GET /client-tags/check-name/{name} endpoint."""

    async def test_check_available_name(self, client: AsyncClient):
        """Test checking an available tag name."""
        tenant_resp = await client.post(
            "/tenants/",
            json={"name": "Tag Name Tenant", "code": "tag-name"},
        )
        tenant_id = tenant_resp.json()["id"]

        response = await client.get(
            f"/client-tags/check-name/Available Tag?tenant_id={tenant_id}"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["available"] is True


# =============================================================================
# INTEGRATION TESTS
# =============================================================================


class TestClientTagIntegration:
    """Integration tests for client tag workflows."""

    async def test_tag_crud_flow(self, client: AsyncClient):
        """Test complete client tag CRUD flow."""
        # Create tenant
        tenant_resp = await client.post(
            "/tenants/",
            json={"name": "Tag CRUD Tenant", "code": "tag-crud"},
        )
        tenant_id = tenant_resp.json()["id"]

        # Create tag
        create_resp = await client.post(
            f"/client-tags/?tenant_id={tenant_id}",
            json={
                "name": "Enterprise",
                "description": "Enterprise clients",
                "color": "#0000FF",
            },
        )
        assert create_resp.status_code == 201
        tag_id = create_resp.json()["id"]

        # Get tag
        get_resp = await client.get(f"/client-tags/{tag_id}")
        assert get_resp.status_code == 200
        assert get_resp.json()["name"] == "Enterprise"

        # Update tag
        update_resp = await client.patch(
            f"/client-tags/{tag_id}",
            json={"color": "#00FF00"},
        )
        assert update_resp.status_code == 200
        assert update_resp.json()["color"] == "#00FF00"

        # List tags
        list_resp = await client.get(f"/client-tags/?tenant_id={tenant_id}")
        assert list_resp.status_code == 200
        assert list_resp.json()["total"] >= 1

        # Deactivate tag
        deactivate_resp = await client.post(f"/client-tags/{tag_id}/deactivate")
        assert deactivate_resp.status_code == 200
        assert deactivate_resp.json()["is_active"] is False

        # Activate tag
        activate_resp = await client.post(f"/client-tags/{tag_id}/activate")
        assert activate_resp.status_code == 200
        assert activate_resp.json()["is_active"] is True

    async def test_multiple_tags_creation(self, client: AsyncClient):
        """Test creating multiple tags."""
        tenant_resp = await client.post(
            "/tenants/",
            json={"name": "Multi Tag Tenant", "code": "multi-tag"},
        )
        tenant_id = tenant_resp.json()["id"]

        tags = [
            {"name": "Priority", "color": "#FF0000"},
            {"name": "New", "color": "#00FF00"},
            {"name": "Renewal", "color": "#0000FF"},
        ]

        for tag_data in tags:
            resp = await client.post(
                f"/client-tags/?tenant_id={tenant_id}",
                json=tag_data,
            )
            assert resp.status_code == 201

        # List all tags
        list_resp = await client.get(f"/client-tags/?tenant_id={tenant_id}")
        assert list_resp.json()["total"] == 3
