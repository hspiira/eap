"""
Tenant API End-to-End Tests

Comprehensive tests for all tenant endpoints covering:
- CRUD operations (Create, Read, Update, Delete)
- Lifecycle transitions (Activate, Suspend, Terminate, Archive, Restore)
- Query operations (List, Filter, Pagination)
- Utility endpoints (Check code availability, Stats, Subscription)
"""

import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio


# =============================================================================
# Helper Functions
# =============================================================================


async def create_tenant(client: AsyncClient, data: dict) -> dict:
    """Helper to create a tenant and return the response data."""
    response = await client.post("/tenants/", json=data)
    assert response.status_code == 201
    return response.json()


# =============================================================================
# CREATE TENANT TESTS
# =============================================================================


class TestCreateTenant:
    """Tests for POST /tenants/ endpoint."""

    async def test_create_tenant_success(
        self, client: AsyncClient, sample_tenant_data: dict
    ):
        """Test successful tenant creation with all fields."""
        response = await client.post("/tenants/", json=sample_tenant_data)

        assert response.status_code == 201
        data = response.json()

        assert data["name"] == sample_tenant_data["name"]
        assert data["code"] == sample_tenant_data["code"]
        assert data["status"] == "Active"
        assert data["subscription_tier"] == sample_tenant_data["subscription_tier"]
        assert data["is_active"] is True
        assert "id" in data
        assert data["settings"]["max_users"] == sample_tenant_data["settings"]["max_users"]
        assert data["settings"]["max_clients"] == sample_tenant_data["settings"]["max_clients"]
        assert data["settings"]["features_enabled"] == sample_tenant_data["settings"]["features_enabled"]
        assert data["settings"]["custom_branding"] == sample_tenant_data["settings"]["custom_branding"]

    async def test_create_tenant_minimal(
        self, client: AsyncClient, sample_tenant_data_minimal: dict
    ):
        """Test tenant creation with minimal data (uses defaults)."""
        response = await client.post("/tenants/", json=sample_tenant_data_minimal)

        assert response.status_code == 201
        data = response.json()

        assert data["name"] == sample_tenant_data_minimal["name"]
        assert data["code"] == sample_tenant_data_minimal["code"]
        assert data["status"] == "Active"
        assert data["subscription_tier"] == "Free"  # Default
        assert data["settings"]["max_users"] == 10  # Default
        assert data["settings"]["max_clients"] == 5  # Default
        assert data["settings"]["features_enabled"] == []  # Default
        assert data["settings"]["custom_branding"] is False  # Default

    async def test_create_tenant_premium_tier(
        self, client: AsyncClient, sample_tenant_data_premium: dict
    ):
        """Test tenant creation with premium tier settings."""
        response = await client.post("/tenants/", json=sample_tenant_data_premium)

        assert response.status_code == 201
        data = response.json()

        assert data["subscription_tier"] == "Enterprise"
        assert data["settings"]["max_users"] == 100
        assert data["settings"]["max_clients"] == 50
        assert data["settings"]["custom_branding"] is True

    async def test_create_tenant_duplicate_code_fails(
        self, client: AsyncClient, sample_tenant_data: dict
    ):
        """Test that creating a tenant with duplicate code fails."""
        # Create first tenant
        await create_tenant(client, sample_tenant_data)

        # Try to create another with same code
        response = await client.post("/tenants/", json=sample_tenant_data)

        # 409 Conflict for duplicate resource creation (standard error format uses "message")
        assert response.status_code == 409
        assert "already exists" in response.json().get("message", "").lower()

    async def test_create_tenant_invalid_code_format(self, client: AsyncClient):
        """Test that invalid code formats are rejected."""
        invalid_codes = [
            "TEST",  # Uppercase
            "test_co",  # Underscore
            "test.co",  # Dot
            "te",  # Too short
            "this-code-is-way-too-long",  # Too long
            "-test",  # Leading hyphen
            "test-",  # Trailing hyphen
        ]

        for code in invalid_codes:
            response = await client.post(
                "/tenants/",
                json={"name": "Test", "code": code},
            )
            assert response.status_code == 422, f"Code '{code}' should be rejected"

    async def test_create_tenant_missing_required_fields(self, client: AsyncClient):
        """Test that missing required fields return validation error."""
        # Missing name
        response = await client.post("/tenants/", json={"code": "test-co"})
        assert response.status_code == 422

        # Missing code
        response = await client.post("/tenants/", json={"name": "Test Company"})
        assert response.status_code == 422

        # Empty body
        response = await client.post("/tenants/", json={})
        assert response.status_code == 422

    async def test_create_tenant_empty_name_fails(self, client: AsyncClient):
        """Test that empty tenant name is rejected."""
        response = await client.post(
            "/tenants/",
            json={"name": "", "code": "test-co"},
        )
        assert response.status_code == 422

    async def test_create_tenant_all_subscription_tiers(self, client: AsyncClient):
        """Test creating tenants with all subscription tier values."""
        tiers = ["Free", "Basic", "Professional", "Enterprise"]

        for i, tier in enumerate(tiers):
            response = await client.post(
                "/tenants/",
                json={"name": f"Tenant {tier}", "code": f"tier-{i}", "subscription_tier": tier},
            )
            assert response.status_code == 201
            assert response.json()["subscription_tier"] == tier


# =============================================================================
# GET TENANT TESTS
# =============================================================================


class TestGetTenant:
    """Tests for GET /tenants/{tenant_id} endpoint."""

    async def test_get_tenant_by_id_success(
        self, client: AsyncClient, sample_tenant_data: dict
    ):
        """Test getting a tenant by ID."""
        # Create tenant
        created = await create_tenant(client, sample_tenant_data)
        tenant_id = created["id"]

        # Get tenant
        response = await client.get(f"/tenants/{tenant_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == tenant_id
        assert data["name"] == sample_tenant_data["name"]
        assert data["code"] == sample_tenant_data["code"]

    async def test_get_tenant_not_found(self, client: AsyncClient):
        """Test getting a non-existent tenant returns 404."""
        response = await client.get("/tenants/nonexistent-id-12345")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()


class TestGetTenantByCode:
    """Tests for GET /tenants/code/{code} endpoint."""

    async def test_get_tenant_by_code_success(
        self, client: AsyncClient, sample_tenant_data: dict
    ):
        """Test getting a tenant by code."""
        # Create tenant
        created = await create_tenant(client, sample_tenant_data)

        # Get tenant by code
        response = await client.get(f"/tenants/code/{sample_tenant_data['code']}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == created["id"]
        assert data["code"] == sample_tenant_data["code"]

    async def test_get_tenant_by_code_not_found(self, client: AsyncClient):
        """Test getting a tenant by non-existent code returns 404."""
        response = await client.get("/tenants/code/nonexistent-code")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()


# =============================================================================
# LIST TENANTS TESTS
# =============================================================================


class TestListTenants:
    """Tests for GET /tenants/ endpoint."""

    async def test_list_tenants_empty(self, client: AsyncClient):
        """Test listing tenants when none exist."""
        response = await client.get("/tenants/")

        assert response.status_code == 200
        data = response.json()
        assert data["items"] == []
        assert data["total"] == 0
        assert data["page"] == 1
        assert data["has_more"] is False

    async def test_list_tenants_success(
        self, client: AsyncClient, sample_tenant_data: dict, sample_tenant_data_premium: dict
    ):
        """Test listing multiple tenants."""
        # Create tenants
        await create_tenant(client, sample_tenant_data)
        await create_tenant(client, sample_tenant_data_premium)

        # List tenants
        response = await client.get("/tenants/")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2
        assert len(data["items"]) == 2

    async def test_list_tenants_pagination(self, client: AsyncClient):
        """Test tenant list pagination."""
        # Create 5 tenants
        for i in range(5):
            await client.post(
                "/tenants/",
                json={"name": f"Tenant {i}", "code": f"tenant-{i}"},
            )

        # Get first page with limit 2
        response = await client.get("/tenants/?page=1&limit=2")
        data = response.json()

        assert response.status_code == 200
        assert len(data["items"]) == 2
        assert data["total"] == 5
        assert data["page"] == 1
        assert data["limit"] == 2
        assert data["has_more"] is True

        # Get second page
        response = await client.get("/tenants/?page=2&limit=2")
        data = response.json()

        assert len(data["items"]) == 2
        assert data["page"] == 2
        assert data["has_more"] is True

        # Get third page
        response = await client.get("/tenants/?page=3&limit=2")
        data = response.json()

        assert len(data["items"]) == 1
        assert data["page"] == 3
        assert data["has_more"] is False

    async def test_list_tenants_filter_by_status(self, client: AsyncClient):
        """Test filtering tenants by status."""
        # Create an active tenant
        created = await client.post(
            "/tenants/",
            json={"name": "Active Tenant", "code": "active-tenant"},
        )
        tenant_id = created.json()["id"]

        # Suspend it
        await client.post(
            f"/tenants/{tenant_id}/suspend",
            json={"reason": "Test suspension"},
        )

        # Create another active tenant
        await client.post(
            "/tenants/",
            json={"name": "Another Active", "code": "another-active"},
        )

        # Filter by active status
        response = await client.get("/tenants/?status=Active")
        data = response.json()

        assert response.status_code == 200
        assert data["total"] == 1
        assert all(item["status"] == "Active" for item in data["items"])

        # Filter by suspended status
        response = await client.get("/tenants/?status=Suspended")
        data = response.json()

        assert data["total"] == 1
        assert all(item["status"] == "Suspended" for item in data["items"])

    async def test_list_tenants_filter_by_subscription_tier(self, client: AsyncClient):
        """Test filtering tenants by subscription tier."""
        # Create tenants with different tiers
        free_resp = await client.post(
            "/tenants/",
            json={"name": "Free Tenant", "code": "free-tier", "subscription_tier": "Free"},
        )
        assert free_resp.status_code == 201
        
        enterprise_resp = await client.post(
            "/tenants/",
            json={"name": "Enterprise Tenant", "code": "ent-tier", "subscription_tier": "Enterprise"},
        )
        assert enterprise_resp.status_code == 201

        # Filter by Free tier
        response = await client.get("/tenants/?subscription_tier=Free")
        data = response.json()

        assert response.status_code == 200
        assert data["total"] >= 1
        assert all(item["subscription_tier"] == "Free" for item in data["items"])

        # Filter by Enterprise tier
        response = await client.get("/tenants/?subscription_tier=Enterprise")
        data = response.json()

        assert data["total"] >= 1
        assert all(item["subscription_tier"] == "Enterprise" for item in data["items"])

    async def test_list_tenants_search(self, client: AsyncClient):
        """Test searching tenants by name or code."""
        # Create tenants
        await client.post(
            "/tenants/",
            json={"name": "Acme Corporation", "code": "acme-corp"},
        )
        await client.post(
            "/tenants/",
            json={"name": "Beta Company", "code": "beta-co"},
        )

        # Search by name
        response = await client.get("/tenants/?search=acme")
        data = response.json()

        assert response.status_code == 200
        assert data["total"] == 1
        assert "Acme" in data["items"][0]["name"]

        # Search by code
        response = await client.get("/tenants/?search=beta")
        data = response.json()

        assert data["total"] == 1
        assert "beta" in data["items"][0]["code"]


# =============================================================================
# UPDATE TENANT TESTS
# =============================================================================


class TestUpdateTenant:
    """Tests for PATCH /tenants/{tenant_id} endpoint."""

    async def test_update_tenant_name(
        self, client: AsyncClient, sample_tenant_data: dict
    ):
        """Test updating tenant name."""
        created = await create_tenant(client, sample_tenant_data)
        tenant_id = created["id"]

        response = await client.patch(
            f"/tenants/{tenant_id}",
            json={"name": "Updated Company Name"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Company Name"
        # Other fields unchanged
        assert data["code"] == sample_tenant_data["code"]

    async def test_update_tenant_not_found(self, client: AsyncClient):
        """Test updating non-existent tenant returns 404."""
        response = await client.patch(
            "/tenants/nonexistent-id",
            json={"name": "New Name"},
        )

        assert response.status_code == 404

    async def test_update_tenant_empty_name_fails(
        self, client: AsyncClient, sample_tenant_data: dict
    ):
        """Test that updating to empty name fails."""
        created = await create_tenant(client, sample_tenant_data)
        tenant_id = created["id"]

        response = await client.patch(
            f"/tenants/{tenant_id}",
            json={"name": ""},
        )

        assert response.status_code == 422


class TestUpdateTenantSettings:
    """Tests for PATCH /tenants/{tenant_id}/settings endpoint."""

    async def test_update_settings_all_fields(
        self, client: AsyncClient, sample_tenant_data: dict
    ):
        """Test updating all tenant settings."""
        created = await create_tenant(client, sample_tenant_data)
        tenant_id = created["id"]

        new_settings = {
            "max_users": 50,
            "max_clients": 25,
            "features_enabled": ["new_feature1", "new_feature2"],
            "custom_branding": True,
        }

        response = await client.patch(
            f"/tenants/{tenant_id}/settings",
            json=new_settings,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["settings"]["max_users"] == 50
        assert data["settings"]["max_clients"] == 25
        assert data["settings"]["features_enabled"] == ["new_feature1", "new_feature2"]
        assert data["settings"]["custom_branding"] is True

    async def test_update_settings_partial(
        self, client: AsyncClient, sample_tenant_data: dict
    ):
        """Test partial settings update."""
        created = await create_tenant(client, sample_tenant_data)
        tenant_id = created["id"]

        # Update only max_users
        response = await client.patch(
            f"/tenants/{tenant_id}/settings",
            json={"max_users": 100},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["settings"]["max_users"] == 100
        # Other settings unchanged
        assert data["settings"]["max_clients"] == sample_tenant_data["settings"]["max_clients"]

    async def test_update_settings_not_found(self, client: AsyncClient):
        """Test updating settings for non-existent tenant."""
        response = await client.patch(
            "/tenants/nonexistent-id/settings",
            json={"max_users": 50},
        )

        assert response.status_code == 404


# =============================================================================
# LIFECYCLE TESTS (Activate, Suspend, Terminate, Archive, Restore)
# =============================================================================


class TestActivateTenant:
    """Tests for POST /tenants/{tenant_id}/activate endpoint."""

    async def test_activate_suspended_tenant(
        self, client: AsyncClient, sample_tenant_data: dict
    ):
        """Test activating a suspended tenant."""
        created = await create_tenant(client, sample_tenant_data)
        tenant_id = created["id"]

        # Suspend first
        await client.post(
            f"/tenants/{tenant_id}/suspend",
            json={"reason": "Test suspension"},
        )

        # Activate
        response = await client.post(f"/tenants/{tenant_id}/activate")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "Active"
        assert data["is_active"] is True

    async def test_activate_already_active_tenant_fails(
        self, client: AsyncClient, sample_tenant_data: dict
    ):
        """Test that activating an already active tenant fails."""
        created = await create_tenant(client, sample_tenant_data)
        tenant_id = created["id"]

        response = await client.post(f"/tenants/{tenant_id}/activate")

        # Returns 409 Conflict for state conflicts
        assert response.status_code == 409
        assert "already active" in response.json()["detail"].lower()

    async def test_activate_terminated_tenant_fails(
        self, client: AsyncClient, sample_tenant_data: dict
    ):
        """Test that activating a terminated tenant fails (returns 404 since terminated tenants are soft-deleted)."""
        created = await create_tenant(client, sample_tenant_data)
        tenant_id = created["id"]

        # Terminate (sets deleted_at, soft-deleting the tenant)
        await client.post(
            f"/tenants/{tenant_id}/terminate",
            json={"reason": "Test termination"},
        )

        # Try to activate - returns 404 because soft-deleted tenants aren't found
        response = await client.post(f"/tenants/{tenant_id}/activate")

        assert response.status_code == 404

    async def test_activate_not_found(self, client: AsyncClient):
        """Test activating non-existent tenant returns 404."""
        response = await client.post("/tenants/nonexistent-id/activate")

        assert response.status_code == 404


class TestSuspendTenant:
    """Tests for POST /tenants/{tenant_id}/suspend endpoint."""

    async def test_suspend_tenant_success(
        self, client: AsyncClient, sample_tenant_data: dict
    ):
        """Test suspending an active tenant."""
        created = await create_tenant(client, sample_tenant_data)
        tenant_id = created["id"]

        response = await client.post(
            f"/tenants/{tenant_id}/suspend",
            json={"reason": "Payment overdue"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "Suspended"
        assert data["is_active"] is False

    async def test_suspend_already_suspended_tenant_fails(
        self, client: AsyncClient, sample_tenant_data: dict
    ):
        """Test that suspending an already suspended tenant fails."""
        created = await create_tenant(client, sample_tenant_data)
        tenant_id = created["id"]

        # Suspend
        await client.post(
            f"/tenants/{tenant_id}/suspend",
            json={"reason": "First suspension"},
        )

        # Try to suspend again
        response = await client.post(
            f"/tenants/{tenant_id}/suspend",
            json={"reason": "Second suspension"},
        )

        # Returns 409 Conflict for state conflicts
        assert response.status_code == 409
        assert "already suspended" in response.json()["detail"].lower()

    async def test_suspend_terminated_tenant_fails(
        self, client: AsyncClient, sample_tenant_data: dict
    ):
        """Test that suspending a terminated tenant fails (returns 404 since terminated tenants are soft-deleted)."""
        created = await create_tenant(client, sample_tenant_data)
        tenant_id = created["id"]

        # Terminate (sets deleted_at, soft-deleting the tenant)
        await client.post(
            f"/tenants/{tenant_id}/terminate",
            json={"reason": "Test termination"},
        )

        # Try to suspend - returns 404 because soft-deleted tenants aren't found
        response = await client.post(
            f"/tenants/{tenant_id}/suspend",
            json={"reason": "Try to suspend"},
        )

        assert response.status_code == 404

    async def test_suspend_requires_reason(
        self, client: AsyncClient, sample_tenant_data: dict
    ):
        """Test that suspension requires a reason."""
        created = await create_tenant(client, sample_tenant_data)
        tenant_id = created["id"]

        response = await client.post(
            f"/tenants/{tenant_id}/suspend",
            json={"reason": ""},
        )

        assert response.status_code == 422

    async def test_suspend_not_found(self, client: AsyncClient):
        """Test suspending non-existent tenant returns 404."""
        response = await client.post(
            "/tenants/nonexistent-id/suspend",
            json={"reason": "Test"},
        )

        assert response.status_code == 404


class TestTerminateTenant:
    """Tests for POST /tenants/{tenant_id}/terminate endpoint."""

    async def test_terminate_tenant_success(
        self, client: AsyncClient, sample_tenant_data: dict
    ):
        """Test terminating an active tenant."""
        created = await create_tenant(client, sample_tenant_data)
        tenant_id = created["id"]

        response = await client.post(
            f"/tenants/{tenant_id}/terminate",
            json={"reason": "Contract ended"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "Terminated"
        assert data["is_active"] is False

    async def test_terminate_already_terminated_fails(
        self, client: AsyncClient, sample_tenant_data: dict
    ):
        """Test that terminating an already terminated tenant fails (returns 404 since terminated tenants are soft-deleted)."""
        created = await create_tenant(client, sample_tenant_data)
        tenant_id = created["id"]

        # Terminate (sets deleted_at, soft-deleting the tenant)
        await client.post(
            f"/tenants/{tenant_id}/terminate",
            json={"reason": "First termination"},
        )

        # Try to terminate again - returns 404 because soft-deleted tenants aren't found
        response = await client.post(
            f"/tenants/{tenant_id}/terminate",
            json={"reason": "Second termination"},
        )

        assert response.status_code == 404

    async def test_terminate_requires_reason(
        self, client: AsyncClient, sample_tenant_data: dict
    ):
        """Test that termination requires a reason."""
        created = await create_tenant(client, sample_tenant_data)
        tenant_id = created["id"]

        response = await client.post(
            f"/tenants/{tenant_id}/terminate",
            json={"reason": ""},
        )

        assert response.status_code == 422

    async def test_terminate_not_found(self, client: AsyncClient):
        """Test terminating non-existent tenant returns 404."""
        response = await client.post(
            "/tenants/nonexistent-id/terminate",
            json={"reason": "Test"},
        )

        assert response.status_code == 404


class TestArchiveTenant:
    """Tests for POST /tenants/{tenant_id}/archive endpoint."""

    async def test_archive_tenant_success(
        self, client: AsyncClient, sample_tenant_data: dict
    ):
        """Test archiving an active tenant."""
        created = await create_tenant(client, sample_tenant_data)
        tenant_id = created["id"]

        response = await client.post(f"/tenants/{tenant_id}/archive")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "Archived"
        assert data["is_active"] is False

    async def test_archive_already_archived_fails(
        self, client: AsyncClient, sample_tenant_data: dict
    ):
        """Test that archiving an already archived tenant fails."""
        created = await create_tenant(client, sample_tenant_data)
        tenant_id = created["id"]

        # Archive
        await client.post(f"/tenants/{tenant_id}/archive")

        # Try to archive again
        response = await client.post(f"/tenants/{tenant_id}/archive")

        # Returns 409 Conflict for state conflicts
        assert response.status_code == 409
        assert "already archived" in response.json()["detail"].lower()

    async def test_archive_terminated_tenant_fails(
        self, client: AsyncClient, sample_tenant_data: dict
    ):
        """Test that archiving a terminated tenant fails (returns 404 since terminated tenants are soft-deleted)."""
        created = await create_tenant(client, sample_tenant_data)
        tenant_id = created["id"]

        # Terminate (sets deleted_at, soft-deleting the tenant)
        await client.post(
            f"/tenants/{tenant_id}/terminate",
            json={"reason": "Test termination"},
        )

        # Try to archive - returns 404 because soft-deleted tenants aren't found
        response = await client.post(f"/tenants/{tenant_id}/archive")

        assert response.status_code == 404

    async def test_archive_not_found(self, client: AsyncClient):
        """Test archiving non-existent tenant returns 404."""
        response = await client.post("/tenants/nonexistent-id/archive")

        assert response.status_code == 404


class TestRestoreTenant:
    """Tests for POST /tenants/{tenant_id}/restore endpoint."""

    async def test_restore_archived_tenant(
        self, client: AsyncClient, sample_tenant_data: dict
    ):
        """Test restoring an archived tenant."""
        created = await create_tenant(client, sample_tenant_data)
        tenant_id = created["id"]

        # Archive
        await client.post(f"/tenants/{tenant_id}/archive")

        # Restore
        response = await client.post(f"/tenants/{tenant_id}/restore")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "Active"
        assert data["is_active"] is True

    async def test_restore_active_tenant_fails(
        self, client: AsyncClient, sample_tenant_data: dict
    ):
        """Test that restoring an already active tenant fails."""
        created = await create_tenant(client, sample_tenant_data)
        tenant_id = created["id"]

        response = await client.post(f"/tenants/{tenant_id}/restore")

        # Returns 409 Conflict for state conflicts
        assert response.status_code == 409
        assert "does not need restoration" in response.json()["detail"].lower() or "already active" in response.json()["detail"].lower()

    async def test_restore_terminated_tenant_fails(
        self, client: AsyncClient, sample_tenant_data: dict
    ):
        """Test that restoring a terminated tenant fails (returns 404 since terminated tenants are soft-deleted)."""
        created = await create_tenant(client, sample_tenant_data)
        tenant_id = created["id"]

        # Terminate (sets deleted_at, soft-deleting the tenant)
        await client.post(
            f"/tenants/{tenant_id}/terminate",
            json={"reason": "Test termination"},
        )

        # Try to restore - returns 404 because soft-deleted tenants aren't found
        response = await client.post(f"/tenants/{tenant_id}/restore")

        assert response.status_code == 404

    async def test_restore_not_found(self, client: AsyncClient):
        """Test restoring non-existent tenant returns 404."""
        response = await client.post("/tenants/nonexistent-id/restore")

        assert response.status_code == 404


# =============================================================================
# SUBSCRIPTION TESTS
# =============================================================================


class TestUpdateSubscription:
    """Tests for POST /tenants/{tenant_id}/subscription endpoint."""

    async def test_update_subscription_tier(
        self, client: AsyncClient, sample_tenant_data: dict
    ):
        """Test updating subscription tier."""
        created = await create_tenant(client, sample_tenant_data)
        tenant_id = created["id"]
        assert created["subscription_tier"] == "Free"

        # Upgrade to Enterprise
        response = await client.post(
            f"/tenants/{tenant_id}/subscription",
            json={"subscription_tier": "Enterprise"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["subscription_tier"] == "Enterprise"

    async def test_update_subscription_all_tiers(
        self, client: AsyncClient, sample_tenant_data: dict
    ):
        """Test cycling through all subscription tiers."""
        created = await create_tenant(client, sample_tenant_data)
        tenant_id = created["id"]

        tiers = ["Basic", "Professional", "Enterprise", "Free"]

        for tier in tiers:
            response = await client.post(
                f"/tenants/{tenant_id}/subscription",
                json={"subscription_tier": tier},
            )
            assert response.status_code == 200
            assert response.json()["subscription_tier"] == tier

    async def test_update_subscription_invalid_tier(
        self, client: AsyncClient, sample_tenant_data: dict
    ):
        """Test that invalid subscription tier is rejected."""
        created = await create_tenant(client, sample_tenant_data)
        tenant_id = created["id"]

        response = await client.post(
            f"/tenants/{tenant_id}/subscription",
            json={"subscription_tier": "InvalidTier"},
        )

        assert response.status_code == 422

    async def test_update_subscription_terminated_tenant_fails(
        self, client: AsyncClient, sample_tenant_data: dict
    ):
        """Test updating subscription for terminated tenant fails (returns 404 since terminated tenants are soft-deleted)."""
        created = await create_tenant(client, sample_tenant_data)
        tenant_id = created["id"]

        # Terminate (sets deleted_at, soft-deleting the tenant)
        await client.post(
            f"/tenants/{tenant_id}/terminate",
            json={"reason": "Test termination"},
        )

        # Try to update subscription - returns 404 because soft-deleted tenants aren't found
        response = await client.post(
            f"/tenants/{tenant_id}/subscription",
            json={"subscription_tier": "Enterprise"},
        )

        assert response.status_code == 404

    async def test_update_subscription_not_found(self, client: AsyncClient):
        """Test updating subscription for non-existent tenant."""
        response = await client.post(
            "/tenants/nonexistent-id/subscription",
            json={"subscription_tier": "Enterprise"},
        )

        assert response.status_code == 404


# =============================================================================
# UTILITY ENDPOINT TESTS
# =============================================================================


class TestCheckCodeAvailability:
    """Tests for GET /tenants/check-code/{code} endpoint."""

    async def test_check_available_code(self, client: AsyncClient):
        """Test checking availability of unused code."""
        response = await client.get("/tenants/check-code/new-code")

        assert response.status_code == 200
        data = response.json()
        assert data["available"] is True
        assert data["code"] == "new-code"

    async def test_check_taken_code(
        self, client: AsyncClient, sample_tenant_data: dict
    ):
        """Test checking availability of used code."""
        await create_tenant(client, sample_tenant_data)

        response = await client.get(f"/tenants/check-code/{sample_tenant_data['code']}")

        assert response.status_code == 200
        data = response.json()
        assert data["available"] is False
        assert data["code"] == sample_tenant_data["code"]


class TestGetTenantStats:
    """Tests for GET /tenants/{tenant_id}/stats endpoint."""

    async def test_get_tenant_stats_success(
        self, client: AsyncClient, sample_tenant_data: dict
    ):
        """Test getting tenant statistics."""
        created = await create_tenant(client, sample_tenant_data)
        tenant_id = created["id"]

        response = await client.get(f"/tenants/{tenant_id}/stats")

        assert response.status_code == 200
        data = response.json()
        assert data["tenant_id"] == tenant_id
        # Admin user is automatically created, so count should be 1
        assert data["current_user_count"] == 1
        assert data["current_client_count"] == 0
        assert data["max_users"] == sample_tenant_data["settings"]["max_users"]
        assert data["max_clients"] == sample_tenant_data["settings"]["max_clients"]
        # User quota usage should reflect the admin user
        expected_user_usage = (1 / sample_tenant_data["settings"]["max_users"] * 100) if sample_tenant_data["settings"]["max_users"] > 0 else 0.0
        assert abs(data["user_quota_usage"] - expected_user_usage) < 0.01
        assert data["client_quota_usage"] == 0.0
        assert data["subscription_tier"] == sample_tenant_data["subscription_tier"]

    async def test_get_tenant_stats_not_found(self, client: AsyncClient):
        """Test getting stats for non-existent tenant."""
        response = await client.get("/tenants/nonexistent-id/stats")

        assert response.status_code == 404


# =============================================================================
# INTEGRATION/FLOW TESTS
# =============================================================================


class TestTenantLifecycleFlow:
    """Integration tests for complete tenant lifecycle flows."""

    async def test_full_lifecycle_active_to_suspended_to_active(
        self, client: AsyncClient, sample_tenant_data: dict
    ):
        """Test complete flow: create -> suspend -> activate."""
        # Create
        created = await create_tenant(client, sample_tenant_data)
        tenant_id = created["id"]
        assert created["status"] == "Active"

        # Suspend
        suspended = await client.post(
            f"/tenants/{tenant_id}/suspend",
            json={"reason": "Payment issue"},
        )
        assert suspended.json()["status"] == "Suspended"

        # Reactivate
        activated = await client.post(f"/tenants/{tenant_id}/activate")
        assert activated.json()["status"] == "Active"

    async def test_full_lifecycle_active_to_archived_to_restored(
        self, client: AsyncClient, sample_tenant_data: dict
    ):
        """Test complete flow: create -> archive -> restore."""
        # Create
        created = await create_tenant(client, sample_tenant_data)
        tenant_id = created["id"]
        assert created["status"] == "Active"

        # Archive
        archived = await client.post(f"/tenants/{tenant_id}/archive")
        assert archived.json()["status"] == "Archived"

        # Restore
        restored = await client.post(f"/tenants/{tenant_id}/restore")
        assert restored.json()["status"] == "Active"

    async def test_termination_is_final(
        self, client: AsyncClient, sample_tenant_data: dict
    ):
        """Test that termination is a final state - tenant becomes inaccessible (soft-deleted)."""
        # Create and terminate
        created = await create_tenant(client, sample_tenant_data)
        tenant_id = created["id"]

        await client.post(
            f"/tenants/{tenant_id}/terminate",
            json={"reason": "Contract ended"},
        )

        # All operations should return 404 (tenant is soft-deleted and not found)
        activate_response = await client.post(f"/tenants/{tenant_id}/activate")
        assert activate_response.status_code == 404

        suspend_response = await client.post(
            f"/tenants/{tenant_id}/suspend",
            json={"reason": "Test"},
        )
        assert suspend_response.status_code == 404

        archive_response = await client.post(f"/tenants/{tenant_id}/archive")
        assert archive_response.status_code == 404

        restore_response = await client.post(f"/tenants/{tenant_id}/restore")
        assert restore_response.status_code == 404

        update_response = await client.patch(
            f"/tenants/{tenant_id}",
            json={"name": "New Name"},
        )
        assert update_response.status_code == 404

        settings_response = await client.patch(
            f"/tenants/{tenant_id}/settings",
            json={"max_users": 100},
        )
        assert settings_response.status_code == 404

        subscription_response = await client.post(
            f"/tenants/{tenant_id}/subscription",
            json={"subscription_tier": "Enterprise"},
        )
        assert subscription_response.status_code == 404

        # GET also returns 404
        get_response = await client.get(f"/tenants/{tenant_id}")
        assert get_response.status_code == 404

    async def test_crud_operations_integration(
        self, client: AsyncClient
    ):
        """Test complete CRUD flow."""
        # Create
        create_response = await client.post(
            "/tenants/",
            json={
                "name": "Integration Test Corp",
                "code": "int-test",
                "subscription_tier": "Basic",
                "settings": {
                    "max_users": 20,
                    "max_clients": 10,
                    "features_enabled": ["feature1"],
                    "custom_branding": False,
                },
            },
        )
        assert create_response.status_code == 201
        tenant_id = create_response.json()["id"]

        # Read
        get_response = await client.get(f"/tenants/{tenant_id}")
        assert get_response.status_code == 200
        assert get_response.json()["name"] == "Integration Test Corp"

        # Update name
        update_response = await client.patch(
            f"/tenants/{tenant_id}",
            json={"name": "Updated Integration Corp"},
        )
        assert update_response.status_code == 200
        assert update_response.json()["name"] == "Updated Integration Corp"

        # Update settings
        settings_response = await client.patch(
            f"/tenants/{tenant_id}/settings",
            json={"max_users": 50, "custom_branding": True},
        )
        assert settings_response.status_code == 200
        assert settings_response.json()["settings"]["max_users"] == 50
        assert settings_response.json()["settings"]["custom_branding"] is True

        # Update subscription
        subscription_response = await client.post(
            f"/tenants/{tenant_id}/subscription",
            json={"subscription_tier": "Professional"},
        )
        assert subscription_response.status_code == 200
        assert subscription_response.json()["subscription_tier"] == "Professional"

        # Verify all changes persisted
        final_response = await client.get(f"/tenants/{tenant_id}")
        final_data = final_response.json()
        assert final_data["name"] == "Updated Integration Corp"
        assert final_data["settings"]["max_users"] == 50
        assert final_data["settings"]["custom_branding"] is True
        assert final_data["subscription_tier"] == "Professional"
