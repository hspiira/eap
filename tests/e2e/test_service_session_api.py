"""
Service Session API End-to-End Tests

Comprehensive tests for all service session endpoints covering:
- CRUD operations (Create, Get, List, Update)
- Lifecycle transitions (Complete, Cancel, Reschedule, No-Show, Archive, Restore)
- Feedback updates
- Query by person, provider, service
"""

from datetime import UTC, datetime, timedelta

import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio


# =============================================================================
# CREATE SERVICE SESSION TESTS
# =============================================================================


class TestCreateServiceSession:
    """Tests for POST /service-sessions/ endpoint."""

    async def test_create_session_success(
        self,
        client: AsyncClient,
        session_test_tenant: dict,
        session_test_service: dict,
        session_test_provider: dict,
        session_test_client_person: dict,
    ):
        """Test creating a service session with full data."""
        tenant_id = session_test_tenant["id"]
        scheduled_at = (datetime.now(UTC) + timedelta(days=3)).isoformat()

        response = await client.post(
            f"/service-sessions/?tenant_id={tenant_id}",
            json={
                "service_id": session_test_service["id"],
                "provider_id": session_test_provider["id"],
                "person_id": session_test_client_person["id"],
                "scheduled_at": scheduled_at,
                "location": "Conference Room A",
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["service_id"] == session_test_service["id"]
        assert data["provider_id"] == session_test_provider["id"]
        assert data["person_id"] == session_test_client_person["id"]
        assert data["location"] == "Conference Room A"
        assert data["status"] == "Scheduled"
        assert data["reschedule_count"] == 0
        assert data["is_active"] is True

    async def test_create_session_requires_tenant_id(
        self,
        client: AsyncClient,
        session_test_service: dict,
        session_test_provider: dict,
        session_test_client_person: dict,
    ):
        """Test that creating a session requires tenant_id."""
        scheduled_at = (datetime.now(UTC) + timedelta(days=1)).isoformat()

        response = await client.post(
            "/service-sessions/",
            json={
                "service_id": session_test_service["id"],
                "provider_id": session_test_provider["id"],
                "person_id": session_test_client_person["id"],
                "scheduled_at": scheduled_at,
            },
        )

        assert response.status_code == 422


# =============================================================================
# GET SERVICE SESSION TESTS
# =============================================================================


class TestGetServiceSession:
    """Tests for GET /service-sessions/{session_id} endpoint."""

    async def test_get_session_by_id_success(
        self, client: AsyncClient, test_service_session: dict
    ):
        """Test getting a session by ID."""
        session_id = test_service_session["id"]

        response = await client.get(f"/service-sessions/{session_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == session_id
        assert data["location"] == "Office A"

    async def test_get_session_not_found(self, client: AsyncClient):
        """Test getting a non-existent session returns 404."""
        response = await client.get("/service-sessions/nonexistent-id-12345")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()


class TestGetSessionsByPerson:
    """Tests for GET /service-sessions/person/{person_id} endpoint."""

    async def test_get_sessions_by_person_success(
        self,
        client: AsyncClient,
        session_test_tenant: dict,
        session_test_client_person: dict,
        test_service_session: dict,
    ):
        """Test getting all sessions for a person."""
        tenant_id = session_test_tenant["id"]
        person_id = session_test_client_person["id"]

        response = await client.get(
            f"/service-sessions/person/{person_id}?tenant_id={tenant_id}"
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        assert all(s["person_id"] == person_id for s in data)


class TestGetSessionsByProvider:
    """Tests for GET /service-sessions/provider/{provider_id} endpoint."""

    async def test_get_sessions_by_provider_success(
        self,
        client: AsyncClient,
        session_test_tenant: dict,
        session_test_provider: dict,
        test_service_session: dict,
    ):
        """Test getting all sessions for a provider."""
        tenant_id = session_test_tenant["id"]
        provider_id = session_test_provider["id"]

        response = await client.get(
            f"/service-sessions/provider/{provider_id}?tenant_id={tenant_id}"
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        assert all(s["provider_id"] == provider_id for s in data)


class TestGetSessionsByService:
    """Tests for GET /service-sessions/service/{service_id} endpoint."""

    async def test_get_sessions_by_service_success(
        self,
        client: AsyncClient,
        session_test_tenant: dict,
        session_test_service: dict,
        test_service_session: dict,
    ):
        """Test getting all sessions for a service."""
        tenant_id = session_test_tenant["id"]
        service_id = session_test_service["id"]

        response = await client.get(
            f"/service-sessions/service/{service_id}?tenant_id={tenant_id}"
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        assert all(s["service_id"] == service_id for s in data)


# =============================================================================
# LIST SERVICE SESSIONS TESTS
# =============================================================================


class TestListServiceSessions:
    """Tests for GET /service-sessions/ endpoint."""

    async def test_list_sessions_requires_tenant_id(self, client: AsyncClient):
        """Test that listing sessions requires tenant_id."""
        response = await client.get("/service-sessions/")

        assert response.status_code == 422

    async def test_list_sessions_empty(
        self, client: AsyncClient, session_test_tenant: dict
    ):
        """Test listing sessions when none exist."""
        # Create a new tenant with no sessions
        new_tenant = await client.post(
            "/tenants/",
            json={"name": "Empty Session Tenant", "code": "empty-sess"},
        )
        tenant_id = new_tenant.json()["id"]

        response = await client.get(f"/service-sessions/?tenant_id={tenant_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["items"] == []
        assert data["total"] == 0

    async def test_list_sessions_success(
        self,
        client: AsyncClient,
        session_test_tenant: dict,
        test_service_session: dict,
        test_service_session_2: dict,
    ):
        """Test listing sessions with results."""
        tenant_id = session_test_tenant["id"]

        response = await client.get(f"/service-sessions/?tenant_id={tenant_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 2
        assert len(data["items"]) >= 2

    async def test_list_sessions_pagination(
        self, client: AsyncClient, session_test_tenant: dict, test_service_session: dict
    ):
        """Test session list pagination."""
        tenant_id = session_test_tenant["id"]

        response = await client.get(
            f"/service-sessions/?tenant_id={tenant_id}&page=1&limit=1"
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) <= 1
        assert data["page"] == 1
        assert data["limit"] == 1

    async def test_list_sessions_filter_by_status(
        self, client: AsyncClient, session_test_tenant: dict, test_service_session: dict
    ):
        """Test filtering sessions by status."""
        tenant_id = session_test_tenant["id"]

        response = await client.get(
            f"/service-sessions/?tenant_id={tenant_id}&status=Scheduled"
        )
        data = response.json()

        assert response.status_code == 200
        assert all(s["status"] == "Scheduled" for s in data["items"])

    async def test_list_sessions_filter_by_person(
        self,
        client: AsyncClient,
        session_test_tenant: dict,
        session_test_client_person: dict,
        test_service_session: dict,
    ):
        """Test filtering sessions by person."""
        tenant_id = session_test_tenant["id"]
        person_id = session_test_client_person["id"]

        response = await client.get(
            f"/service-sessions/?tenant_id={tenant_id}&person_id={person_id}"
        )
        data = response.json()

        assert response.status_code == 200
        assert all(s["person_id"] == person_id for s in data["items"])


# =============================================================================
# LIFECYCLE TESTS (Complete, Cancel, Reschedule, No-Show, Archive, Restore)
# =============================================================================


class TestCompleteServiceSession:
    """Tests for POST /service-sessions/{session_id}/complete endpoint."""

    async def test_complete_session_success(
        self, client: AsyncClient, test_service_session: dict
    ):
        """Test completing a scheduled session."""
        session_id = test_service_session["id"]

        response = await client.post(
            f"/service-sessions/{session_id}/complete",
            json={
                "duration": 60,
                "notes": "Session completed successfully",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "Completed"
        assert data["duration"] == 60
        assert data["notes"] == "Session completed successfully"
        assert data["completed_at"] is not None

    async def test_complete_not_found(self, client: AsyncClient):
        """Test completing non-existent session returns 404."""
        response = await client.post(
            "/service-sessions/nonexistent-id/complete",
            json={"duration": 30, "notes": "Test"},
        )

        assert response.status_code == 404


class TestCancelServiceSession:
    """Tests for POST /service-sessions/{session_id}/cancel endpoint."""

    async def test_cancel_session_success(
        self, client: AsyncClient, test_service_session: dict
    ):
        """Test cancelling a scheduled session."""
        session_id = test_service_session["id"]

        response = await client.post(
            f"/service-sessions/{session_id}/cancel",
            json={"reason": "Client requested cancellation"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "Cancelled"
        assert data["cancellation_reason"] == "Client requested cancellation"

    async def test_cancel_requires_reason(
        self, client: AsyncClient, test_service_session_2: dict
    ):
        """Test that cancelling requires a reason."""
        session_id = test_service_session_2["id"]

        response = await client.post(
            f"/service-sessions/{session_id}/cancel",
            json={"reason": ""},
        )

        assert response.status_code == 422

    async def test_cancel_not_found(self, client: AsyncClient):
        """Test cancelling non-existent session returns 404."""
        response = await client.post(
            "/service-sessions/nonexistent-id/cancel",
            json={"reason": "Test"},
        )

        assert response.status_code == 404


class TestRescheduleServiceSession:
    """Tests for POST /service-sessions/{session_id}/reschedule endpoint."""

    async def test_reschedule_session_success(
        self, client: AsyncClient, test_service_session: dict
    ):
        """Test rescheduling a session."""
        session_id = test_service_session["id"]
        new_time = (datetime.now(UTC) + timedelta(days=10)).isoformat()

        response = await client.post(
            f"/service-sessions/{session_id}/reschedule",
            json={"new_scheduled_at": new_time},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["reschedule_count"] >= 1

    async def test_reschedule_not_found(self, client: AsyncClient):
        """Test rescheduling non-existent session returns 404."""
        new_time = (datetime.now(UTC) + timedelta(days=5)).isoformat()

        response = await client.post(
            "/service-sessions/nonexistent-id/reschedule",
            json={"new_scheduled_at": new_time},
        )

        assert response.status_code == 404


class TestNoShowServiceSession:
    """Tests for POST /service-sessions/{session_id}/no-show endpoint."""

    async def test_no_show_session_success(
        self, client: AsyncClient, test_service_session: dict
    ):
        """Test marking a session as no-show."""
        session_id = test_service_session["id"]

        response = await client.post(f"/service-sessions/{session_id}/no-show")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "No Show"

    async def test_no_show_not_found(self, client: AsyncClient):
        """Test marking non-existent session as no-show returns 404."""
        response = await client.post("/service-sessions/nonexistent-id/no-show")

        assert response.status_code == 404


class TestArchiveServiceSession:
    """Tests for POST /service-sessions/{session_id}/archive endpoint."""

    async def test_archive_session_success(
        self, client: AsyncClient, test_service_session: dict
    ):
        """Test archiving a session."""
        session_id = test_service_session["id"]

        response = await client.post(f"/service-sessions/{session_id}/archive")

        assert response.status_code == 200

    async def test_archive_not_found(self, client: AsyncClient):
        """Test archiving non-existent session returns 404."""
        response = await client.post("/service-sessions/nonexistent-id/archive")

        assert response.status_code == 404


class TestRestoreServiceSession:
    """Tests for POST /service-sessions/{session_id}/restore endpoint."""

    async def test_restore_not_found(self, client: AsyncClient):
        """Test restoring non-existent session returns 404."""
        response = await client.post("/service-sessions/nonexistent-id/restore")

        assert response.status_code == 404


# =============================================================================
# UPDATE TESTS
# =============================================================================


class TestUpdateServiceSession:
    """Tests for PATCH /service-sessions/{session_id} endpoint."""

    async def test_update_session_location(
        self, client: AsyncClient, test_service_session: dict
    ):
        """Test updating session location."""
        session_id = test_service_session["id"]

        response = await client.patch(
            f"/service-sessions/{session_id}",
            json={"location": "Conference Room B"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["location"] == "Conference Room B"

    async def test_update_session_notes(
        self, client: AsyncClient, test_service_session: dict
    ):
        """Test updating session notes."""
        session_id = test_service_session["id"]

        response = await client.patch(
            f"/service-sessions/{session_id}",
            json={"notes": "Updated notes for the session"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["notes"] == "Updated notes for the session"

    async def test_update_session_not_found(self, client: AsyncClient):
        """Test updating non-existent session returns 404."""
        response = await client.patch(
            "/service-sessions/nonexistent-id",
            json={"location": "Test"},
        )

        assert response.status_code == 404


class TestUpdateSessionFeedback:
    """Tests for PATCH /service-sessions/{session_id}/feedback endpoint."""

    async def test_update_feedback_success(
        self, client: AsyncClient, test_service_session: dict
    ):
        """Test updating session feedback (requires completed session)."""
        session_id = test_service_session["id"]

        # Complete the session first (feedback requires completed status)
        await client.post(
            f"/service-sessions/{session_id}/complete",
            json={"duration": 60, "notes": "Session completed"},
        )

        # Now add feedback
        response = await client.patch(
            f"/service-sessions/{session_id}/feedback",
            json={"feedback": "Excellent session, very helpful."},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["feedback"] == "Excellent session, very helpful."

    async def test_update_feedback_not_found(self, client: AsyncClient):
        """Test updating feedback for non-existent session."""
        response = await client.patch(
            "/service-sessions/nonexistent-id/feedback",
            json={"feedback": "Test feedback"},
        )

        assert response.status_code == 404


# =============================================================================
# INTEGRATION/FLOW TESTS
# =============================================================================


class TestServiceSessionLifecycleFlow:
    """Integration tests for complete service session lifecycle flows."""

    async def test_full_lifecycle_scheduled_to_completed(
        self,
        client: AsyncClient,
        session_test_tenant: dict,
        session_test_service: dict,
        session_test_provider: dict,
        session_test_client_person: dict,
    ):
        """Test complete flow: create -> update -> complete -> feedback."""
        tenant_id = session_test_tenant["id"]
        scheduled_at = (datetime.now(UTC) + timedelta(days=1)).isoformat()

        # Create session
        create_response = await client.post(
            f"/service-sessions/?tenant_id={tenant_id}",
            json={
                "service_id": session_test_service["id"],
                "provider_id": session_test_provider["id"],
                "person_id": session_test_client_person["id"],
                "scheduled_at": scheduled_at,
                "location": "Initial Location",
            },
        )
        assert create_response.status_code == 201
        session_id = create_response.json()["id"]
        assert create_response.json()["status"] == "Scheduled"

        # Update location
        update_response = await client.patch(
            f"/service-sessions/{session_id}",
            json={"location": "Updated Location"},
        )
        assert update_response.json()["location"] == "Updated Location"

        # Complete session
        complete_response = await client.post(
            f"/service-sessions/{session_id}/complete",
            json={"duration": 55, "notes": "Good progress made"},
        )
        assert complete_response.json()["status"] == "Completed"
        assert complete_response.json()["duration"] == 55

        # Add feedback
        feedback_response = await client.patch(
            f"/service-sessions/{session_id}/feedback",
            json={"feedback": "Client reported positive experience"},
        )
        assert feedback_response.json()["feedback"] == "Client reported positive experience"

    async def test_full_lifecycle_scheduled_to_cancelled(
        self,
        client: AsyncClient,
        session_test_tenant: dict,
        session_test_service: dict,
        session_test_provider: dict,
        session_test_client_person: dict,
    ):
        """Test complete flow: create -> reschedule -> cancel."""
        tenant_id = session_test_tenant["id"]
        scheduled_at = (datetime.now(UTC) + timedelta(days=2)).isoformat()

        # Create session
        create_response = await client.post(
            f"/service-sessions/?tenant_id={tenant_id}",
            json={
                "service_id": session_test_service["id"],
                "provider_id": session_test_provider["id"],
                "person_id": session_test_client_person["id"],
                "scheduled_at": scheduled_at,
            },
        )
        session_id = create_response.json()["id"]

        # Reschedule
        new_time = (datetime.now(UTC) + timedelta(days=5)).isoformat()
        reschedule_response = await client.post(
            f"/service-sessions/{session_id}/reschedule",
            json={"new_scheduled_at": new_time},
        )
        assert reschedule_response.json()["reschedule_count"] == 1

        # Cancel
        cancel_response = await client.post(
            f"/service-sessions/{session_id}/cancel",
            json={"reason": "Client unavailable"},
        )
        assert cancel_response.json()["status"] == "Cancelled"
