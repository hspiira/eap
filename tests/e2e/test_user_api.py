"""
User API End-to-End Tests

Comprehensive tests for all user endpoints covering:
- CRUD operations (Create, Get, List)
- Lifecycle transitions (Activate, Suspend, Ban, Deactivate, Terminate)
- Email verification
- Two-factor authentication
- Password and preferences updates
"""

import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio


# =============================================================================
# CREATE USER TESTS
# =============================================================================


class TestCreateUser:
    """Tests for POST /users/ endpoint."""

    async def test_create_user_success(self, client: AsyncClient, user_test_tenant: dict):
        """Test creating a user with email and password."""
        tenant_id = user_test_tenant["id"]

        response = await client.post(
            f"/users/?tenant_id={tenant_id}",
            json={
                "email": "newuser@example.com",
                "password": "SecurePassword123!",
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "newuser@example.com"
        assert data["tenant_id"] == tenant_id
        assert data["status"] == "Pending Verification"
        assert data["is_email_verified"] is False
        assert data["is_two_factor_enabled"] is False
        assert data["is_active"] is False

    async def test_create_user_with_preferences(self, client: AsyncClient, user_test_tenant: dict):
        """Test creating a user with preferences."""
        tenant_id = user_test_tenant["id"]

        response = await client.post(
            f"/users/?tenant_id={tenant_id}",
            json={
                "email": "prefuser@example.com",
                "password": "SecurePassword123!",
                "preferred_language": "es",
                "timezone": "America/New_York",
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["preferred_language"] == "es"
        assert data["timezone"] == "America/New_York"

    async def test_create_user_requires_tenant_id(self, client: AsyncClient):
        """Test that creating a user requires tenant_id."""
        response = await client.post(
            "/users/",
            json={"email": "test@example.com", "password": "Password123!"},
        )

        assert response.status_code == 422


# =============================================================================
# GET USER TESTS
# =============================================================================


class TestGetUser:
    """Tests for GET /users/{user_id} endpoint."""

    async def test_get_user_by_id_success(self, client: AsyncClient, test_api_user: dict):
        """Test getting a user by ID."""
        user_id = test_api_user["id"]

        response = await client.get(f"/users/{user_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == user_id
        assert data["email"] == "testuser@example.com"

    async def test_get_user_not_found(self, client: AsyncClient):
        """Test getting a non-existent user returns 404."""
        response = await client.get("/users/nonexistent-id-12345")

        assert response.status_code == 404
        assert "not found" in response.json()["message"].lower()


class TestGetUserByEmail:
    """Tests for GET /users/email/{email} endpoint."""

    async def test_get_user_by_email_success(
        self, client: AsyncClient, user_test_tenant: dict, test_api_user: dict
    ):
        """Test getting a user by email."""
        tenant_id = user_test_tenant["id"]
        email = test_api_user["email"]

        response = await client.get(f"/users/email/{email}?tenant_id={tenant_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["email"] == email

    async def test_get_user_by_email_not_found(self, client: AsyncClient, user_test_tenant: dict):
        """Test getting user by non-existent email returns 404."""
        tenant_id = user_test_tenant["id"]

        response = await client.get(f"/users/email/nonexistent@example.com?tenant_id={tenant_id}")

        assert response.status_code == 404


class TestCheckEmailAvailability:
    """Tests for GET /users/check-email/{email} endpoint."""

    async def test_check_available_email(self, client: AsyncClient, user_test_tenant: dict):
        """Test checking an available email."""
        tenant_id = user_test_tenant["id"]

        response = await client.get(
            f"/users/check-email/available@example.com?tenant_id={tenant_id}"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["available"] is True

    async def test_check_taken_email(
        self, client: AsyncClient, user_test_tenant: dict, test_api_user: dict
    ):
        """Test checking a taken email."""
        tenant_id = user_test_tenant["id"]
        email = test_api_user["email"]

        response = await client.get(f"/users/check-email/{email}?tenant_id={tenant_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["available"] is False


# =============================================================================
# LIST USERS TESTS
# =============================================================================


class TestListUsers:
    """Tests for GET /users/ endpoint."""

    async def test_list_users_requires_tenant_id(self, client: AsyncClient):
        """Test that listing users requires tenant_id."""
        response = await client.get("/users/")

        assert response.status_code == 422

    async def test_list_users_empty(self, client: AsyncClient, user_test_tenant: dict):
        """Test listing users for a newly created tenant (has one admin user)."""
        # Create a new tenant (backend auto-creates one admin user per tenant)
        new_tenant = await client.post(
            "/tenants/",
            json={"name": "Empty User Tenant", "code": "empty-usr"},
        )
        tenant_id = new_tenant.json()["id"]

        response = await client.get(f"/users/?tenant_id={tenant_id}")

        assert response.status_code == 200
        data = response.json()
        # New tenant has exactly the auto-created admin user
        assert data["total"] >= 1
        assert isinstance(data["items"], list)
        assert len(data["items"]) >= 1
        # Admin email format: admin_{code}@evexia.test
        assert any("admin_" in u.get("email", "") for u in data["items"])

    async def test_list_users_success(
        self,
        client: AsyncClient,
        user_test_tenant: dict,
        test_api_user: dict,
        test_api_user_2: dict,
    ):
        """Test listing users with results."""
        tenant_id = user_test_tenant["id"]

        response = await client.get(f"/users/?tenant_id={tenant_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 2
        assert len(data["items"]) >= 2

    async def test_list_users_pagination(
        self, client: AsyncClient, user_test_tenant: dict, test_api_user: dict
    ):
        """Test user list pagination."""
        tenant_id = user_test_tenant["id"]

        response = await client.get(f"/users/?tenant_id={tenant_id}&page=1&limit=1")

        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) <= 1
        assert data["page"] == 1
        assert data["limit"] == 1

    async def test_list_users_filter_by_status(
        self, client: AsyncClient, user_test_tenant: dict, test_api_user_active: dict
    ):
        """Test filtering users by status."""
        tenant_id = user_test_tenant["id"]

        response = await client.get(f"/users/?tenant_id={tenant_id}&status=Active")
        data = response.json()

        assert response.status_code == 200
        assert all(u["status"] == "Active" for u in data["items"])


# =============================================================================
# EMAIL VERIFICATION TESTS
# =============================================================================


class TestVerifyEmail:
    """Tests for POST /users/{user_id}/verify-email endpoint."""

    async def test_verify_email_success(self, client: AsyncClient, test_api_user: dict):
        """Test verifying user email."""
        user_id = test_api_user["id"]

        response = await client.post(f"/users/{user_id}/verify-email")

        assert response.status_code == 200
        data = response.json()
        assert data["is_email_verified"] is True
        assert data["email_verified_at"] is not None

    async def test_verify_email_not_found(self, client: AsyncClient):
        """Test verifying non-existent user returns 404."""
        response = await client.post("/users/nonexistent-id/verify-email")

        assert response.status_code == 404


# =============================================================================
# LIFECYCLE TESTS (Activate, Suspend, Ban, Deactivate, Terminate)
# =============================================================================


class TestActivateUser:
    """Tests for POST /users/{user_id}/activate endpoint."""

    async def test_activate_user_success(self, client: AsyncClient, test_api_user: dict):
        """Test activating a pending user."""
        user_id = test_api_user["id"]

        # Verify email first
        await client.post(f"/users/{user_id}/verify-email")

        response = await client.post(f"/users/{user_id}/activate")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "Active"
        assert data["is_active"] is True

    async def test_activate_not_found(self, client: AsyncClient):
        """Test activating non-existent user returns 404."""
        response = await client.post("/users/nonexistent-id/activate")

        assert response.status_code == 404


class TestSuspendUser:
    """Tests for POST /users/{user_id}/suspend endpoint."""

    async def test_suspend_user_success(self, client: AsyncClient, test_api_user_active: dict):
        """Test suspending an active user."""
        user_id = test_api_user_active["id"]

        response = await client.post(
            f"/users/{user_id}/suspend",
            json={"reason": "Violation of terms"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "Suspended"

    async def test_suspend_requires_reason(self, client: AsyncClient, test_api_user_active: dict):
        """Test that suspending requires a reason."""
        user_id = test_api_user_active["id"]

        response = await client.post(
            f"/users/{user_id}/suspend",
            json={"reason": ""},
        )

        assert response.status_code == 422

    async def test_suspend_not_found(self, client: AsyncClient):
        """Test suspending non-existent user returns 404."""
        response = await client.post(
            "/users/nonexistent-id/suspend",
            json={"reason": "Test"},
        )

        assert response.status_code == 404


class TestBanUser:
    """Tests for POST /users/{user_id}/ban endpoint."""

    async def test_ban_user_success(self, client: AsyncClient, test_api_user_active: dict):
        """Test banning a user."""
        user_id = test_api_user_active["id"]

        response = await client.post(
            f"/users/{user_id}/ban",
            json={"reason": "Security violation"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "Banned"

    async def test_ban_not_found(self, client: AsyncClient):
        """Test banning non-existent user returns 404."""
        response = await client.post(
            "/users/nonexistent-id/ban",
            json={"reason": "Test"},
        )

        assert response.status_code == 404


class TestDeactivateUser:
    """Tests for POST /users/{user_id}/deactivate endpoint."""

    async def test_deactivate_user_success(self, client: AsyncClient, test_api_user_active: dict):
        """Test deactivating a user."""
        user_id = test_api_user_active["id"]

        response = await client.post(
            f"/users/{user_id}/deactivate",
            json={"reason": "User requested deactivation"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "Inactive"

    async def test_deactivate_not_found(self, client: AsyncClient):
        """Test deactivating non-existent user returns 404."""
        response = await client.post(
            "/users/nonexistent-id/deactivate",
            json={"reason": "Test"},
        )

        assert response.status_code == 404


class TestTerminateUser:
    """Tests for POST /users/{user_id}/terminate endpoint."""

    async def test_terminate_user_success(self, client: AsyncClient, test_api_user: dict):
        """Test terminating a user."""
        user_id = test_api_user["id"]

        response = await client.post(
            f"/users/{user_id}/terminate",
            json={"reason": "Account closed"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "Terminated"

    async def test_terminate_not_found(self, client: AsyncClient):
        """Test terminating non-existent user returns 404."""
        response = await client.post(
            "/users/nonexistent-id/terminate",
            json={"reason": "Test"},
        )

        assert response.status_code == 404


# =============================================================================
# TWO-FACTOR AUTHENTICATION TESTS
# =============================================================================


class TestTwoFactorAuthentication:
    """Tests for 2FA endpoints."""

    async def test_enable_two_factor_success(self, client: AsyncClient, test_api_user_active: dict):
        """Test enabling 2FA."""
        user_id = test_api_user_active["id"]

        response = await client.post(f"/users/{user_id}/enable-2fa")

        assert response.status_code == 200
        data = response.json()
        assert data["is_two_factor_enabled"] is True

    async def test_disable_two_factor_success(
        self, client: AsyncClient, test_api_user_active: dict
    ):
        """Test disabling 2FA."""
        user_id = test_api_user_active["id"]

        # Enable first
        await client.post(f"/users/{user_id}/enable-2fa")

        # Then disable
        response = await client.post(f"/users/{user_id}/disable-2fa")

        assert response.status_code == 200
        data = response.json()
        assert data["is_two_factor_enabled"] is False

    async def test_enable_2fa_not_found(self, client: AsyncClient):
        """Test enabling 2FA for non-existent user returns 404."""
        response = await client.post("/users/nonexistent-id/enable-2fa")

        assert response.status_code == 404


# =============================================================================
# UPDATE TESTS
# =============================================================================


class TestUpdatePassword:
    """Tests for PATCH /users/{user_id}/password endpoint."""

    async def test_update_password_success(self, client: AsyncClient, test_api_user: dict):
        """Test updating user password."""
        user_id = test_api_user["id"]

        response = await client.patch(
            f"/users/{user_id}/password",
            json={"password": "NewSecurePassword456!"},
        )

        assert response.status_code == 200

    async def test_update_password_not_found(self, client: AsyncClient):
        """Test updating password for non-existent user."""
        response = await client.patch(
            "/users/nonexistent-id/password",
            json={"password": "NewPassword123!"},
        )

        assert response.status_code == 404


class TestUpdatePreferences:
    """Tests for PATCH /users/{user_id}/preferences endpoint."""

    async def test_update_preferences_language(self, client: AsyncClient, test_api_user: dict):
        """Test updating user preferred language."""
        user_id = test_api_user["id"]

        response = await client.patch(
            f"/users/{user_id}/preferences",
            json={"preferred_language": "fr"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["preferred_language"] == "fr"

    async def test_update_preferences_timezone(self, client: AsyncClient, test_api_user: dict):
        """Test updating user timezone."""
        user_id = test_api_user["id"]

        response = await client.patch(
            f"/users/{user_id}/preferences",
            json={"timezone": "Europe/London"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["timezone"] == "Europe/London"

    async def test_update_preferences_not_found(self, client: AsyncClient):
        """Test updating preferences for non-existent user."""
        response = await client.patch(
            "/users/nonexistent-id/preferences",
            json={"timezone": "UTC"},
        )

        assert response.status_code == 404


class TestRecordLogin:
    """record-login is intentionally not an HTTP route — last_login_at is
    server-derived during login. This pins the removal so it doesn't come back."""

    async def test_record_login_is_not_a_route(
        self, client: AsyncClient, test_api_user_active: dict
    ):
        user_id = test_api_user_active["id"]
        response = await client.post(f"/users/{user_id}/record-login")
        assert response.status_code in (404, 405)


# =============================================================================
# INTEGRATION/FLOW TESTS
# =============================================================================


class TestUserLifecycleFlow:
    """Integration tests for complete user lifecycle flows."""

    async def test_full_lifecycle_create_to_active(
        self, client: AsyncClient, user_test_tenant: dict
    ):
        """Test complete flow: create -> verify email -> activate."""
        tenant_id = user_test_tenant["id"]

        # Create user
        create_response = await client.post(
            f"/users/?tenant_id={tenant_id}",
            json={"email": "lifecycle@example.com", "password": "Password123!"},
        )
        assert create_response.status_code == 201
        user_id = create_response.json()["id"]
        assert create_response.json()["status"] == "Pending Verification"

        # Verify email
        verify_response = await client.post(f"/users/{user_id}/verify-email")
        assert verify_response.json()["is_email_verified"] is True

        # Activate
        activate_response = await client.post(f"/users/{user_id}/activate")
        assert activate_response.json()["status"] == "Active"
        assert activate_response.json()["is_active"] is True

    async def test_full_lifecycle_active_to_terminated(
        self, client: AsyncClient, user_test_tenant: dict
    ):
        """Test complete flow: create -> activate -> suspend -> terminate."""
        tenant_id = user_test_tenant["id"]

        # Create and activate user
        create_response = await client.post(
            f"/users/?tenant_id={tenant_id}",
            json={"email": "terminate@example.com", "password": "Password123!"},
        )
        user_id = create_response.json()["id"]
        await client.post(f"/users/{user_id}/verify-email")
        await client.post(f"/users/{user_id}/activate")

        # Suspend
        suspend_response = await client.post(
            f"/users/{user_id}/suspend",
            json={"reason": "Investigation required"},
        )
        assert suspend_response.json()["status"] == "Suspended"

        # Terminate (sets status to Terminated)
        terminate_response = await client.post(
            f"/users/{user_id}/terminate",
            json={"reason": "Permanent ban"},
        )
        assert terminate_response.json()["status"] == "Terminated"
