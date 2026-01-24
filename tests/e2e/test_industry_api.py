"""
Industry API End-to-End Tests

Comprehensive tests for all industry endpoints covering:
- CRUD operations
- Lifecycle (activate, deactivate)
- Hierarchical industries (parent-child)
"""

import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio


# =============================================================================
# CREATE INDUSTRY TESTS
# =============================================================================


class TestCreateIndustry:
    """Tests for POST /industries/ endpoint."""

    async def test_create_industry_success(self, client: AsyncClient):
        """Test creating an industry."""
        tenant_resp = await client.post(
            "/tenants/",
            json={"name": "Industry Test Tenant", "code": "ind-test"},
        )
        tenant_id = tenant_resp.json()["id"]

        response = await client.post(
            f"/industries/?tenant_id={tenant_id}",
            json={
                "name": "Technology",
                "description": "Technology sector",
                "code": "TECH",
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Technology"
        assert data["code"] == "TECH"
        assert data["is_active"] is True

    async def test_create_industry_requires_tenant_id(self, client: AsyncClient):
        """Test that creating an industry requires tenant_id."""
        response = await client.post(
            "/industries/",
            json={"name": "Test Industry", "code": "TEST"},
        )

        assert response.status_code == 422

    async def test_create_child_industry(self, client: AsyncClient):
        """Test creating a child industry."""
        tenant_resp = await client.post(
            "/tenants/",
            json={"name": "Child Ind Tenant", "code": "child-ind"},
        )
        tenant_id = tenant_resp.json()["id"]

        # Create parent industry
        parent_resp = await client.post(
            f"/industries/?tenant_id={tenant_id}",
            json={"name": "Finance", "code": "FIN"},
        )
        parent_id = parent_resp.json()["id"]

        # Create child industry
        child_resp = await client.post(
            f"/industries/?tenant_id={tenant_id}",
            json={
                "name": "Banking",
                "code": "BANK",
                "parent_industry_id": parent_id,
            },
        )

        assert child_resp.status_code == 201
        assert child_resp.json()["parent_industry_id"] == parent_id


class TestGetIndustry:
    """Tests for GET /industries/{industry_id} endpoint."""

    async def test_get_industry_not_found(self, client: AsyncClient):
        """Test getting a non-existent industry returns 404."""
        response = await client.get("/industries/nonexistent-id")

        assert response.status_code == 404


class TestListIndustries:
    """Tests for GET /industries/ endpoint."""

    async def test_list_industries_requires_tenant_id(self, client: AsyncClient):
        """Test that listing industries requires tenant_id."""
        response = await client.get("/industries/")

        assert response.status_code == 422

    async def test_list_industries_empty(self, client: AsyncClient):
        """Test listing industries when none exist."""
        tenant_resp = await client.post(
            "/tenants/",
            json={"name": "Empty Ind Tenant", "code": "empty-ind"},
        )
        tenant_id = tenant_resp.json()["id"]

        response = await client.get(f"/industries/?tenant_id={tenant_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["items"] == []
        assert data["total"] == 0


class TestUpdateIndustry:
    """Tests for PATCH /industries/{industry_id} endpoint."""

    async def test_update_industry_not_found(self, client: AsyncClient):
        """Test updating non-existent industry."""
        response = await client.patch(
            "/industries/nonexistent-id",
            json={"name": "Updated Industry"},
        )

        assert response.status_code in [400, 404]


class TestActivateIndustry:
    """Tests for POST /industries/{industry_id}/activate endpoint."""

    async def test_activate_industry_not_found(self, client: AsyncClient):
        """Test activating non-existent industry returns 404."""
        response = await client.post("/industries/nonexistent-id/activate")

        assert response.status_code == 404


class TestDeactivateIndustry:
    """Tests for POST /industries/{industry_id}/deactivate endpoint."""

    async def test_deactivate_industry_not_found(self, client: AsyncClient):
        """Test deactivating non-existent industry returns 404."""
        response = await client.post("/industries/nonexistent-id/deactivate")

        assert response.status_code == 404


class TestGetIndustryChildren:
    """Tests for GET /industries/{industry_id}/children endpoint."""

    async def test_get_children_requires_tenant_id(self, client: AsyncClient):
        """Test that getting children requires tenant_id."""
        response = await client.get("/industries/some-id/children")

        assert response.status_code == 422


class TestCheckIndustryNameAvailability:
    """Tests for GET /industries/check-name/{name} endpoint."""

    async def test_check_available_name(self, client: AsyncClient):
        """Test checking an available industry name."""
        tenant_resp = await client.post(
            "/tenants/",
            json={"name": "Ind Name Tenant", "code": "ind-name"},
        )
        tenant_id = tenant_resp.json()["id"]

        response = await client.get(
            f"/industries/check-name/Available Industry?tenant_id={tenant_id}"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["available"] is True


# =============================================================================
# INTEGRATION TESTS
# =============================================================================


class TestIndustryIntegration:
    """Integration tests for industry workflows."""

    async def test_industry_crud_flow(self, client: AsyncClient):
        """Test complete industry CRUD flow."""
        # Create tenant
        tenant_resp = await client.post(
            "/tenants/",
            json={"name": "Ind CRUD Tenant", "code": "ind-crud"},
        )
        tenant_id = tenant_resp.json()["id"]

        # Create industry
        create_resp = await client.post(
            f"/industries/?tenant_id={tenant_id}",
            json={
                "name": "Healthcare",
                "description": "Healthcare sector",
                "code": "HEALTH",
            },
        )
        assert create_resp.status_code == 201
        industry_id = create_resp.json()["id"]

        # Get industry
        get_resp = await client.get(f"/industries/{industry_id}")
        assert get_resp.status_code == 200
        assert get_resp.json()["name"] == "Healthcare"

        # Update industry
        update_resp = await client.patch(
            f"/industries/{industry_id}",
            json={"description": "Updated healthcare description"},
        )
        assert update_resp.status_code == 200

        # List industries
        list_resp = await client.get(f"/industries/?tenant_id={tenant_id}")
        assert list_resp.status_code == 200
        assert list_resp.json()["total"] >= 1

        # Deactivate industry
        deactivate_resp = await client.post(f"/industries/{industry_id}/deactivate")
        assert deactivate_resp.status_code == 200
        assert deactivate_resp.json()["is_active"] is False

        # Activate industry
        activate_resp = await client.post(f"/industries/{industry_id}/activate")
        assert activate_resp.status_code == 200
        assert activate_resp.json()["is_active"] is True

    async def test_industry_hierarchy_flow(self, client: AsyncClient):
        """Test industry hierarchy with parent-child relationships."""
        # Create tenant
        tenant_resp = await client.post(
            "/tenants/",
            json={"name": "Ind Hierarchy Tenant", "code": "ind-hier"},
        )
        tenant_id = tenant_resp.json()["id"]

        # Create parent industry
        parent_resp = await client.post(
            f"/industries/?tenant_id={tenant_id}",
            json={"name": "Manufacturing", "code": "MFG"},
        )
        parent_id = parent_resp.json()["id"]

        # Create child industries
        await client.post(
            f"/industries/?tenant_id={tenant_id}",
            json={"name": "Automotive", "code": "AUTO", "parent_industry_id": parent_id},
        )
        await client.post(
            f"/industries/?tenant_id={tenant_id}",
            json={"name": "Electronics", "code": "ELEC", "parent_industry_id": parent_id},
        )

        # Get children
        children_resp = await client.get(
            f"/industries/{parent_id}/children?tenant_id={tenant_id}"
        )
        assert children_resp.status_code == 200
        assert children_resp.json()["total"] == 2
