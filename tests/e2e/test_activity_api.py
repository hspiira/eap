"""
Activity API End-to-End Tests

Comprehensive tests for all activity endpoints covering:
- CRUD operations
- Filtering by client, type, date range
"""

from datetime import datetime, timedelta, timezone

import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio


# =============================================================================
# CREATE ACTIVITY TESTS
# =============================================================================


class TestCreateActivity:
    """Tests for POST /activities/ endpoint."""

    async def test_create_activity_success(self, client: AsyncClient):
        """Test creating an activity."""
        # Create tenant
        tenant_resp = await client.post(
            "/tenants/",
            json={"name": "Activity Test Tenant", "code": "act-test"},
        )
        tenant_id = tenant_resp.json()["id"]

        # Create user for created_by
        user_resp = await client.post(
            f"/users/?tenant_id={tenant_id}",
            json={"email": "activity-user@example.com", "password": "Password123!"},
        )
        user_id = user_resp.json()["id"]

        # Create client
        client_resp = await client.post(
            f"/clients/?tenant_id={tenant_id}",
            json={
                "name": "Activity Client",
                "code": "ACTV",
                "contact_info": {"email": "info@activity.com"},
            },
        )
        assert client_resp.status_code == 201
        client_id = client_resp.json()["id"]

        from datetime import datetime, timezone
        occurred_at = datetime.now(timezone.utc).isoformat()
        
        response = await client.post(
            f"/activities/?tenant_id={tenant_id}&created_by={user_id}",
            json={
                "client_id": client_id,
                "activity_type": "Meeting",
                "subject": "Quarterly Review",
                "description": "Quarterly review meeting with client",
                "occurred_at": occurred_at,
                "is_important": True,
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["activity_type"] == "Meeting"
        assert data["subject"] == "Quarterly Review"
        assert data["is_important"] is True

    async def test_create_activity_requires_tenant_and_created_by(self, client: AsyncClient):
        """Test that creating an activity requires tenant_id and created_by."""
        response = await client.post(
            "/activities/",
            json={"client_id": "some-id", "activity_type": "Call", "description": "Test"},
        )

        assert response.status_code == 422


class TestGetActivity:
    """Tests for GET /activities/{activity_id} endpoint."""

    async def test_get_activity_not_found(self, client: AsyncClient):
        """Test getting a non-existent activity returns 404."""
        response = await client.get("/activities/nonexistent-id")

        assert response.status_code == 404


class TestListActivities:
    """Tests for GET /activities/ endpoint."""

    async def test_list_activities_requires_tenant_id(self, client: AsyncClient):
        """Test that listing activities requires tenant_id."""
        response = await client.get("/activities/")

        assert response.status_code == 422

    async def test_list_activities_empty(self, client: AsyncClient):
        """Test listing activities when none exist."""
        tenant_resp = await client.post(
            "/tenants/",
            json={"name": "Empty Activity Tenant", "code": "empty-act"},
        )
        tenant_id = tenant_resp.json()["id"]

        response = await client.get(f"/activities/?tenant_id={tenant_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["items"] == []
        assert data["total"] == 0


class TestUpdateActivity:
    """Tests for PATCH /activities/{activity_id} endpoint."""

    async def test_update_activity_not_found(self, client: AsyncClient):
        """Test updating non-existent activity."""
        response = await client.patch(
            "/activities/nonexistent-id",
            json={"description": "Updated description"},
        )

        assert response.status_code in [400, 404]


class TestGetActivitiesByClient:
    """Tests for GET /activities/client/{client_id} endpoint."""

    async def test_get_activities_by_client_requires_tenant_id(self, client: AsyncClient):
        """Test that getting activities by client requires tenant_id."""
        response = await client.get("/activities/client/some-client-id")

        assert response.status_code == 422

    async def test_get_activities_by_client_empty(self, client: AsyncClient):
        """Test getting activities for a client with no activities."""
        tenant_resp = await client.post(
            "/tenants/",
            json={"name": "Client Activity Tenant", "code": "cli-act"},
        )
        tenant_id = tenant_resp.json()["id"]

        response = await client.get(
            f"/activities/client/some-client-id?tenant_id={tenant_id}"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["items"] == []


# =============================================================================
# INTEGRATION TESTS
# =============================================================================


class TestActivityIntegration:
    """Integration tests for activity workflows."""

    async def test_activity_crud_flow(self, client: AsyncClient):
        """Test complete activity CRUD flow."""
        # Create tenant
        tenant_resp = await client.post(
            "/tenants/",
            json={"name": "Activity CRUD Tenant", "code": "act-crud"},
        )
        tenant_id = tenant_resp.json()["id"]

        # Create user
        user_resp = await client.post(
            f"/users/?tenant_id={tenant_id}",
            json={"email": "activity-crud@example.com", "password": "Password123!"},
        )
        user_id = user_resp.json()["id"]

        # Create client
        client_resp = await client.post(
            f"/clients/?tenant_id={tenant_id}",
            json={
                "name": "Activity CRUD Client",
                "contact_info": {"email": "info@acc.com"},
            },
        )
        assert client_resp.status_code == 201
        client_id = client_resp.json()["id"]

        # Create activity
        occurred_at = datetime.now(timezone.utc).isoformat()
        create_resp = await client.post(
            f"/activities/?tenant_id={tenant_id}&created_by={user_id}",
            json={
                "client_id": client_id,
                "activity_type": "Call",
                "subject": "Introduction Call",
                "description": "Initial call with client",
                "occurred_at": occurred_at,
            },
        )
        assert create_resp.status_code == 201
        activity_id = create_resp.json()["id"]

        # Get activity
        get_resp = await client.get(f"/activities/{activity_id}")
        assert get_resp.status_code == 200
        assert get_resp.json()["activity_type"] == "Call"

        # Update activity
        next_follow_up = (datetime.now(timezone.utc) + timedelta(days=7)).isoformat()
        update_resp = await client.patch(
            f"/activities/{activity_id}",
            json={
                "outcome": "Positive response",
                "next_follow_up": next_follow_up,
            },
        )
        assert update_resp.status_code == 200
        assert update_resp.json()["outcome"] == "Positive response"

        # List activities
        list_resp = await client.get(f"/activities/?tenant_id={tenant_id}")
        assert list_resp.status_code == 200
        assert list_resp.json()["total"] >= 1

        # Get activities by client
        client_activities = await client.get(
            f"/activities/client/{client_id}?tenant_id={tenant_id}"
        )
        assert client_activities.status_code == 200
        assert client_activities.json()["total"] >= 1

    async def test_activity_filtering(self, client: AsyncClient):
        """Test activity filtering options."""
        # Create tenant
        tenant_resp = await client.post(
            "/tenants/",
            json={"name": "Activity Filter Tenant", "code": "act-flt"},
        )
        tenant_id = tenant_resp.json()["id"]

        # Create user
        user_resp = await client.post(
            f"/users/?tenant_id={tenant_id}",
            json={"email": "activity-filter@example.com", "password": "Password123!"},
        )
        user_id = user_resp.json()["id"]

        # Create client
        client_resp = await client.post(
            f"/clients/?tenant_id={tenant_id}",
            json={
                "name": "Activity Filter Client",
                "contact_info": {"email": "info@afc.com"},
            },
        )
        assert client_resp.status_code == 201
        client_id = client_resp.json()["id"]

        # Create multiple activities
        occurred_at = datetime.now(timezone.utc).isoformat()
        activities = [
            {"activity_type": "Meeting", "subject": "Meeting 1", "description": "D1", "occurred_at": occurred_at, "is_important": True},
            {"activity_type": "Call", "subject": "Call 1", "description": "D2", "occurred_at": occurred_at, "is_important": False},
            {"activity_type": "Email", "subject": "Email 1", "description": "D3", "occurred_at": occurred_at, "is_important": True},
        ]

        for act_data in activities:
            await client.post(
                f"/activities/?tenant_id={tenant_id}&created_by={user_id}",
                json={"client_id": client_id, **act_data},
            )

        # Filter by activity type
        type_resp = await client.get(
            f"/activities/?tenant_id={tenant_id}&activity_type=Meeting"
        )
        assert type_resp.status_code == 200
        assert all(a["activity_type"] == "Meeting" for a in type_resp.json()["items"])

        # Filter by important
        important_resp = await client.get(
            f"/activities/?tenant_id={tenant_id}&is_important=true"
        )
        assert important_resp.status_code == 200
        assert all(a["is_important"] is True for a in important_resp.json()["items"])
