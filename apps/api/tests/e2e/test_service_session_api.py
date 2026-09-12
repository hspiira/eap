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
                "member_id": session_test_client_person["id"],
                "scheduled_at": scheduled_at,
                "delivery_context": "Direct",
                "location": "Conference Room A",
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["service_id"] == session_test_service["id"]
        assert data["provider_id"] == session_test_provider["id"]
        assert data["member_id"] == session_test_client_person["id"]
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
                "member_id": session_test_client_person["id"],
                "scheduled_at": scheduled_at,
                "delivery_context": "Direct",
            },
        )

        assert response.status_code == 422


# =============================================================================
# GET SERVICE SESSION TESTS
# =============================================================================


class TestGetServiceSession:
    """Tests for GET /service-sessions/{session_id} endpoint."""

    async def test_get_session_by_id_success(self, client: AsyncClient, test_service_session: dict):
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
        assert "not found" in response.json()["message"].lower()


class TestGetSessionsByPerson:
    """Tests for GET /service-sessions/member/{member_id} endpoint."""

    async def test_get_sessions_by_member_success(
        self,
        client: AsyncClient,
        session_test_tenant: dict,
        session_test_client_person: dict,
        test_service_session: dict,
    ):
        """Test getting all sessions for a person."""
        tenant_id = session_test_tenant["id"]
        member_id = session_test_client_person["id"]

        response = await client.get(f"/service-sessions/member/{member_id}?tenant_id={tenant_id}")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        assert all(s["member_id"] == member_id for s in data)


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

        response = await client.get(f"/service-sessions/service/{service_id}?tenant_id={tenant_id}")

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

    async def test_list_sessions_empty(self, client: AsyncClient, session_test_tenant: dict):
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

        response = await client.get(f"/service-sessions/?tenant_id={tenant_id}&page=1&limit=1")

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

        response = await client.get(f"/service-sessions/?tenant_id={tenant_id}&status=Scheduled")
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
        member_id = session_test_client_person["id"]

        response = await client.get(
            f"/service-sessions/?tenant_id={tenant_id}&member_id={member_id}"
        )
        data = response.json()

        assert response.status_code == 200
        assert all(s["member_id"] == member_id for s in data["items"])

    async def test_list_sessions_filter_by_client(
        self,
        client: AsyncClient,
        session_test_tenant: dict,
        test_service_session: dict,
    ):
        """A client's own sessions, which is what a client page asks for."""
        tenant_id = session_test_tenant["id"]
        client_id = test_service_session["client_id"]

        response = await client.get(
            f"/service-sessions/?tenant_id={tenant_id}&client_id={client_id}"
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1
        assert all(s["client_id"] == client_id for s in data["items"])
        assert test_service_session["id"] in [s["id"] for s in data["items"]]

        # The count has to move with the filter, not just the page.
        other = await client.get(
            f"/service-sessions/?tenant_id={tenant_id}&client_id=nobody-owns-this"
        )
        assert other.status_code == 200
        assert other.json()["total"] == 0


# =============================================================================
# LIFECYCLE TESTS (Complete, Cancel, Reschedule, No-Show, Archive, Restore)
# =============================================================================


class TestCompleteServiceSession:
    """Tests for POST /service-sessions/{session_id}/complete endpoint."""

    async def test_complete_session_success(
        self, client_with_clinical_scope: AsyncClient, test_service_session: dict
    ):
        """Test completing a scheduled session."""
        client = client_with_clinical_scope
        session_id = test_service_session["id"]

        response = await client.post(
            f"/service-sessions/{session_id}/complete",
            json={
                "duration": 60,
                "notes": "Session completed successfully",
            },
        )

        assert response.status_code == 200
        # /complete now returns the session alongside the authorization drawdown.
        body = response.json()
        data = body["session"]
        assert data["status"] == "Completed"
        assert data["duration"] == 60
        assert data["notes"] == "Session completed successfully"
        assert data["completed_at"] is not None
        # No case_id was supplied, so no authorization was consumed.
        assert body["drawdown"]["consumed"] is False

    async def test_complete_not_found(self, client: AsyncClient):
        """Test completing non-existent session returns 404."""
        response = await client.post(
            "/service-sessions/nonexistent-id/complete",
            json={"duration": 30, "notes": "Test"},
        )

        assert response.status_code == 404


class TestCancelServiceSession:
    """Tests for POST /service-sessions/{session_id}/cancel endpoint."""

    async def test_cancel_session_success(self, client: AsyncClient, test_service_session: dict):
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

    async def test_cancel_requires_reason(self, client: AsyncClient, test_service_session_2: dict):
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

    async def test_no_show_session_success(self, client: AsyncClient, test_service_session: dict):
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

    async def test_archive_session_success(self, client: AsyncClient, test_service_session: dict):
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

    async def test_update_session_location(self, client: AsyncClient, test_service_session: dict):
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
        self, client_with_clinical_scope: AsyncClient, test_service_session: dict
    ):
        """Test updating session notes."""
        client = client_with_clinical_scope
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
        self, client_with_clinical_scope: AsyncClient, test_service_session: dict
    ):
        """Test updating session feedback (requires completed session)."""
        client = client_with_clinical_scope
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
        client_with_clinical_scope: AsyncClient,
        session_test_tenant: dict,
        session_test_service: dict,
        session_test_provider: dict,
        session_test_client_person: dict,
    ):
        """Test complete flow: create -> update -> complete -> feedback."""
        client = client_with_clinical_scope
        tenant_id = session_test_tenant["id"]
        scheduled_at = (datetime.now(UTC) + timedelta(days=1)).isoformat()

        # Create session
        create_response = await client.post(
            f"/service-sessions/?tenant_id={tenant_id}",
            json={
                "service_id": session_test_service["id"],
                "provider_id": session_test_provider["id"],
                "member_id": session_test_client_person["id"],
                "scheduled_at": scheduled_at,
                "delivery_context": "Direct",
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
        assert complete_response.json()["session"]["status"] == "Completed"
        assert complete_response.json()["session"]["duration"] == 55

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
                "member_id": session_test_client_person["id"],
                "scheduled_at": scheduled_at,
                "delivery_context": "Direct",
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


# =============================================================================
# AWAITING CONFIRMATION QUEUE
# =============================================================================


class TestAwaitingConfirmation:
    """GET /service-sessions/awaiting-confirmation.

    Delivery happens outside the system, so a booking stays Scheduled until a
    counsellor's month-end log confirms it. Past its date it stops being a plan
    and becomes an open question. See docs/design/REALTIME_SESSION_CAPTURE.md.
    """

    async def _book(self, client, tenant_id, service, provider, member, *, days):
        response = await client.post(
            f"/service-sessions/?tenant_id={tenant_id}",
            json={
                "service_id": service["id"],
                "provider_id": provider["id"],
                "member_id": member["id"],
                "scheduled_at": (datetime.now(UTC) + timedelta(days=days)).isoformat(),
                "delivery_context": "Direct",
            },
        )
        assert response.status_code == 201, response.text
        return response.json()

    async def test_lists_a_booking_whose_date_has_passed(
        self,
        client: AsyncClient,
        session_test_tenant: dict,
        session_test_service: dict,
        session_test_provider: dict,
        session_test_client_person: dict,
    ):
        tenant_id = session_test_tenant["id"]
        overdue = await self._book(
            client,
            tenant_id,
            session_test_service,
            session_test_provider,
            session_test_client_person,
            days=-5,
        )

        response = await client.get(
            f"/service-sessions/awaiting-confirmation?tenant_id={tenant_id}"
        )

        assert response.status_code == 200, response.text
        ids = [item["id"] for item in response.json()["items"]]
        assert overdue["id"] in ids

    async def test_leaves_out_a_booking_still_in_the_future(
        self,
        client: AsyncClient,
        session_test_tenant: dict,
        session_test_service: dict,
        session_test_provider: dict,
        session_test_client_person: dict,
    ):
        """The distinction the queue exists to draw: last Tuesday is not next Tuesday."""
        tenant_id = session_test_tenant["id"]
        upcoming = await self._book(
            client,
            tenant_id,
            session_test_service,
            session_test_provider,
            session_test_client_person,
            days=3,
        )

        response = await client.get(
            f"/service-sessions/awaiting-confirmation?tenant_id={tenant_id}"
        )

        assert response.status_code == 200, response.text
        ids = [item["id"] for item in response.json()["items"]]
        assert upcoming["id"] not in ids

    async def test_drops_a_booking_once_it_is_completed(
        self,
        client: AsyncClient,
        session_test_tenant: dict,
        session_test_service: dict,
        session_test_provider: dict,
        session_test_client_person: dict,
    ):
        tenant_id = session_test_tenant["id"]
        overdue = await self._book(
            client,
            tenant_id,
            session_test_service,
            session_test_provider,
            session_test_client_person,
            days=-5,
        )

        completed = await client.post(
            f"/service-sessions/{overdue['id']}/complete",
            json={"duration": 60, "notes": "Confirmed from the monthly log"},
        )
        assert completed.status_code == 200, completed.text

        response = await client.get(
            f"/service-sessions/awaiting-confirmation?tenant_id={tenant_id}"
        )

        ids = [item["id"] for item in response.json()["items"]]
        assert overdue["id"] not in ids

    async def test_is_not_swallowed_by_the_session_id_route(
        self,
        client: AsyncClient,
        session_test_tenant: dict,
    ):
        """Declared before /{session_id}, so the literal path wins the match."""
        tenant_id = session_test_tenant["id"]

        response = await client.get(
            f"/service-sessions/awaiting-confirmation?tenant_id={tenant_id}"
        )

        assert response.status_code == 200, response.text
        assert "items" in response.json()

    async def test_oldest_first(
        self,
        client: AsyncClient,
        session_test_tenant: dict,
        session_test_service: dict,
        session_test_provider: dict,
        session_test_client_person: dict,
    ):
        """The oldest is the one most likely to have been forgotten."""
        tenant_id = session_test_tenant["id"]
        for days in (-2, -30, -9):
            await self._book(
                client,
                tenant_id,
                session_test_service,
                session_test_provider,
                session_test_client_person,
                days=days,
            )

        response = await client.get(
            f"/service-sessions/awaiting-confirmation?tenant_id={tenant_id}"
        )

        dates = [item["scheduled_at"] for item in response.json()["items"]]
        assert dates == sorted(dates)


# =============================================================================
# DOUBLE BOOKING AND AVAILABILITY
# =============================================================================


class TestDoubleBooking:
    """A practitioner cannot be in two places at once.

    A booking carries no length of its own until it is completed, so the span
    it occupies comes from the service. See "Decision 6" in
    docs/design/REALTIME_SESSION_CAPTURE.md.
    """

    async def _book(self, client, tenant_id, service, provider, member, *, at):
        return await client.post(
            f"/service-sessions/?tenant_id={tenant_id}",
            json={
                "service_id": service["id"],
                "provider_id": provider["id"],
                "member_id": member["id"],
                "scheduled_at": at.isoformat(),
                "delivery_context": "Direct",
            },
        )

    async def test_a_second_booking_at_the_same_time_is_refused(
        self,
        client: AsyncClient,
        session_test_tenant: dict,
        session_test_service: dict,
        session_test_provider: dict,
        session_test_client_person: dict,
    ):
        tenant_id = session_test_tenant["id"]
        at = datetime.now(UTC) + timedelta(days=4)
        first = await self._book(
            client,
            tenant_id,
            session_test_service,
            session_test_provider,
            session_test_client_person,
            at=at,
        )
        assert first.status_code == 201, first.text

        second = await self._book(
            client,
            tenant_id,
            session_test_service,
            session_test_provider,
            session_test_client_person,
            at=at,
        )

        assert second.status_code == 409, second.text
        assert second.json()["error"] == "PRACTITIONER_DOUBLE_BOOKED"

    async def test_a_booking_that_starts_as_the_last_one_ends_is_allowed(
        self,
        client: AsyncClient,
        session_test_tenant: dict,
        session_test_service: dict,
        session_test_provider: dict,
        session_test_client_person: dict,
    ):
        """Back-to-back is a normal working day, not a clash."""
        tenant_id = session_test_tenant["id"]
        at = datetime.now(UTC) + timedelta(days=5)
        first = await self._book(
            client,
            tenant_id,
            session_test_service,
            session_test_provider,
            session_test_client_person,
            at=at,
        )
        assert first.status_code == 201, first.text

        later = await self._book(
            client,
            tenant_id,
            session_test_service,
            session_test_provider,
            session_test_client_person,
            at=at + timedelta(minutes=60),
        )

        assert later.status_code == 201, later.text

    async def test_a_cancelled_booking_frees_the_slot(
        self,
        client: AsyncClient,
        session_test_tenant: dict,
        session_test_service: dict,
        session_test_provider: dict,
        session_test_client_person: dict,
    ):
        tenant_id = session_test_tenant["id"]
        at = datetime.now(UTC) + timedelta(days=6)
        first = await self._book(
            client,
            tenant_id,
            session_test_service,
            session_test_provider,
            session_test_client_person,
            at=at,
        )
        cancelled = await client.post(
            f"/service-sessions/{first.json()['id']}/cancel",
            json={"reason": "Member withdrew"},
        )
        assert cancelled.status_code == 200, cancelled.text

        again = await self._book(
            client,
            tenant_id,
            session_test_service,
            session_test_provider,
            session_test_client_person,
            at=at,
        )

        assert again.status_code == 201, again.text

    async def test_rescheduling_onto_a_taken_slot_is_refused(
        self,
        client: AsyncClient,
        session_test_tenant: dict,
        session_test_service: dict,
        session_test_provider: dict,
        session_test_client_person: dict,
    ):
        tenant_id = session_test_tenant["id"]
        first_at = datetime.now(UTC) + timedelta(days=7)
        taken = await self._book(
            client,
            tenant_id,
            session_test_service,
            session_test_provider,
            session_test_client_person,
            at=first_at,
        )
        assert taken.status_code == 201, taken.text
        mover = await self._book(
            client,
            tenant_id,
            session_test_service,
            session_test_provider,
            session_test_client_person,
            at=first_at + timedelta(days=1),
        )
        assert mover.status_code == 201, mover.text

        response = await client.post(
            f"/service-sessions/{mover.json()['id']}/reschedule",
            json={"new_scheduled_at": first_at.isoformat(), "reason": "Member asked"},
        )

        assert response.status_code == 409, response.text

    async def test_rescheduling_a_booking_does_not_clash_with_itself(
        self,
        client: AsyncClient,
        session_test_tenant: dict,
        session_test_service: dict,
        session_test_provider: dict,
        session_test_client_person: dict,
    ):
        """The booking being moved is excluded, or no session could ever move."""
        tenant_id = session_test_tenant["id"]
        at = datetime.now(UTC) + timedelta(days=8)
        booked = await self._book(
            client,
            tenant_id,
            session_test_service,
            session_test_provider,
            session_test_client_person,
            at=at,
        )
        assert booked.status_code == 201, booked.text

        response = await client.post(
            f"/service-sessions/{booked.json()['id']}/reschedule",
            json={
                "new_scheduled_at": (at + timedelta(minutes=30)).isoformat(),
                "reason": "Shifted half an hour",
            },
        )

        assert response.status_code == 200, response.text


class TestAvailability:
    async def test_reports_a_free_practitioner_and_says_what_it_assumed(
        self,
        client: AsyncClient,
        session_test_tenant: dict,
        session_test_service: dict,
        session_test_provider: dict,
    ):
        tenant_id = session_test_tenant["id"]
        at = datetime.now(UTC) + timedelta(days=20)

        response = await client.get(
            "/service-sessions/availability",
            params={
                "tenant_id": tenant_id,
                "at": at.isoformat(),
                "service_id": session_test_service["id"],
                "provider_id": [session_test_provider["id"]],
            },
        )

        assert response.status_code == 200, response.text
        body = response.json()
        assert body["items"][0]["available"] is True
        assert body["items"][0]["clashing_session_id"] is None
        # It must say what length it measured, since a booking carries none.
        assert body["assumed_minutes"] > 0

    async def test_reports_a_busy_practitioner_and_names_the_booking(
        self,
        client: AsyncClient,
        session_test_tenant: dict,
        session_test_service: dict,
        session_test_provider: dict,
        session_test_client_person: dict,
    ):
        tenant_id = session_test_tenant["id"]
        at = datetime.now(UTC) + timedelta(days=21)
        booked = await client.post(
            f"/service-sessions/?tenant_id={tenant_id}",
            json={
                "service_id": session_test_service["id"],
                "provider_id": session_test_provider["id"],
                "member_id": session_test_client_person["id"],
                "scheduled_at": at.isoformat(),
                "delivery_context": "Direct",
            },
        )
        assert booked.status_code == 201, booked.text

        response = await client.get(
            "/service-sessions/availability",
            params={
                "tenant_id": tenant_id,
                "at": at.isoformat(),
                "service_id": session_test_service["id"],
                "provider_id": [session_test_provider["id"]],
            },
        )

        assert response.status_code == 200, response.text
        item = response.json()["items"][0]
        assert item["available"] is False
        assert item["clashing_session_id"] == booked.json()["id"]

    async def test_an_unknown_service_is_refused_rather_than_assumed(
        self,
        client: AsyncClient,
        session_test_tenant: dict,
        session_test_provider: dict,
    ):
        """The service sets the span, so guessing one would report a made-up answer."""
        response = await client.get(
            "/service-sessions/availability",
            params={
                "tenant_id": session_test_tenant["id"],
                "at": (datetime.now(UTC) + timedelta(days=22)).isoformat(),
                "service_id": "does-not-exist",
                "provider_id": [session_test_provider["id"]],
            },
        )

        assert response.status_code == 404, response.text


class TestCompanyWideSessions:
    """A health talk is delivered to a client, not to a member.

    The clash and availability checks are attendance-blind on purpose: a
    practitioner giving a talk cannot also be in a one-to-one at that hour, and
    the reverse. See docs/design/REALTIME_SESSION_CAPTURE.md.
    """

    async def _talk(self, client, tenant_id, service, provider, client_person, *, at):
        return await client.post(
            f"/service-sessions/?tenant_id={tenant_id}",
            json={
                "service_id": service["id"],
                "provider_id": provider["id"],
                "attendance": "CompanyWide",
                "client_id": client_person["client_id"],
                # A talk is measured by the room, not by a member.
                "headcount": 40,
                "scheduled_at": at.isoformat(),
                "delivery_context": "Direct",
            },
        )

    async def test_a_talk_books_against_the_client_with_no_member(
        self,
        client: AsyncClient,
        session_test_tenant: dict,
        session_test_service: dict,
        session_test_provider: dict,
        session_test_client_person: dict,
    ):
        at = datetime.now(UTC) + timedelta(days=30)
        response = await self._talk(
            client,
            session_test_tenant["id"],
            session_test_service,
            session_test_provider,
            session_test_client_person,
            at=at,
        )

        assert response.status_code == 201, response.text
        assert response.json()["attendance"] == "CompanyWide"
        assert response.json()["member_id"] is None

    async def test_a_talk_blocks_a_one_to_one_at_the_same_hour(
        self,
        client: AsyncClient,
        session_test_tenant: dict,
        session_test_service: dict,
        session_test_provider: dict,
        session_test_client_person: dict,
    ):
        """The practitioner is the scarce thing, not the audience."""
        tenant_id = session_test_tenant["id"]
        at = datetime.now(UTC) + timedelta(days=31)
        talk = await self._talk(
            client,
            tenant_id,
            session_test_service,
            session_test_provider,
            session_test_client_person,
            at=at,
        )
        assert talk.status_code == 201, talk.text

        individual = await client.post(
            f"/service-sessions/?tenant_id={tenant_id}",
            json={
                "service_id": session_test_service["id"],
                "provider_id": session_test_provider["id"],
                "member_id": session_test_client_person["id"],
                "scheduled_at": at.isoformat(),
                "delivery_context": "Direct",
            },
        )

        assert individual.status_code == 409, individual.text
        assert individual.json()["error"] == "PRACTITIONER_DOUBLE_BOOKED"

    async def test_availability_reports_a_practitioner_giving_a_talk_as_busy(
        self,
        client: AsyncClient,
        session_test_tenant: dict,
        session_test_service: dict,
        session_test_provider: dict,
        session_test_client_person: dict,
    ):
        tenant_id = session_test_tenant["id"]
        at = datetime.now(UTC) + timedelta(days=32)
        talk = await self._talk(
            client,
            tenant_id,
            session_test_service,
            session_test_provider,
            session_test_client_person,
            at=at,
        )
        assert talk.status_code == 201, talk.text

        response = await client.get(
            "/service-sessions/availability",
            params={
                "tenant_id": tenant_id,
                "at": at.isoformat(),
                "service_id": session_test_service["id"],
                "provider_id": [session_test_provider["id"]],
            },
        )

        assert response.status_code == 200, response.text
        assert response.json()["items"][0]["available"] is False

    async def test_an_overdue_talk_joins_the_confirmation_queue(
        self,
        client: AsyncClient,
        session_test_tenant: dict,
        session_test_service: dict,
        session_test_provider: dict,
        session_test_client_person: dict,
    ):
        """A talk is delivery too, and needs confirming like any other booking."""
        tenant_id = session_test_tenant["id"]
        talk = await self._talk(
            client,
            tenant_id,
            session_test_service,
            session_test_provider,
            session_test_client_person,
            at=datetime.now(UTC) - timedelta(days=3),
        )
        assert talk.status_code == 201, talk.text

        response = await client.get(
            f"/service-sessions/awaiting-confirmation?tenant_id={tenant_id}"
        )

        ids = [item["id"] for item in response.json()["items"]]
        assert talk.json()["id"] in ids


class TestFollowUpSessions:
    """A session booked off the back of a previous one.

    The link is session to session on purpose: both ends are employer-side, so
    it carries the scheduling fact without bridging to the pseudonymous
    clinical subject. See decision 7 in docs/design/REALTIME_SESSION_CAPTURE.md.
    """

    async def _book(self, client, tenant_id, service, provider, member, *, at, follows=None):
        body = {
            "service_id": service["id"],
            "provider_id": provider["id"],
            "member_id": member["id"],
            "scheduled_at": at.isoformat(),
            "delivery_context": "Direct",
        }
        if follows:
            body["follow_up_of_session_id"] = follows
        return await client.post(f"/service-sessions/?tenant_id={tenant_id}", json=body)

    async def test_a_follow_up_names_the_session_it_came_from(
        self,
        client: AsyncClient,
        session_test_tenant: dict,
        session_test_service: dict,
        session_test_provider: dict,
        session_test_client_person: dict,
    ):
        tenant_id = session_test_tenant["id"]
        first = await self._book(
            client,
            tenant_id,
            session_test_service,
            session_test_provider,
            session_test_client_person,
            at=datetime.now(UTC) + timedelta(days=40),
        )
        assert first.status_code == 201, first.text

        second = await self._book(
            client,
            tenant_id,
            session_test_service,
            session_test_provider,
            session_test_client_person,
            at=datetime.now(UTC) + timedelta(days=47),
            follows=first.json()["id"],
        )

        assert second.status_code == 201, second.text
        assert second.json()["follow_up_of_session_id"] == first.json()["id"]

    async def test_an_ordinary_booking_names_nothing(
        self,
        client: AsyncClient,
        session_test_tenant: dict,
        session_test_service: dict,
        session_test_provider: dict,
        session_test_client_person: dict,
    ):
        response = await self._book(
            client,
            session_test_tenant["id"],
            session_test_service,
            session_test_provider,
            session_test_client_person,
            at=datetime.now(UTC) + timedelta(days=41),
        )

        assert response.status_code == 201, response.text
        assert response.json()["follow_up_of_session_id"] is None

    async def test_the_link_survives_a_reread(
        self,
        client: AsyncClient,
        session_test_tenant: dict,
        session_test_service: dict,
        session_test_provider: dict,
        session_test_client_person: dict,
    ):
        """Persisted, not just echoed back from the request."""
        tenant_id = session_test_tenant["id"]
        first = await self._book(
            client,
            tenant_id,
            session_test_service,
            session_test_provider,
            session_test_client_person,
            at=datetime.now(UTC) + timedelta(days=42),
        )
        second = await self._book(
            client,
            tenant_id,
            session_test_service,
            session_test_provider,
            session_test_client_person,
            at=datetime.now(UTC) + timedelta(days=49),
            follows=first.json()["id"],
        )
        assert second.status_code == 201, second.text

        reread = await client.get(f"/service-sessions/{second.json()['id']}")

        assert reread.status_code == 200, reread.text
        assert reread.json()["follow_up_of_session_id"] == first.json()["id"]

    async def test_a_continuing_outcome_and_a_follow_up_are_different_things(
        self,
        client_with_clinical_scope: AsyncClient,
        session_test_tenant: dict,
        session_test_service: dict,
        session_test_provider: dict,
        session_test_client_person: dict,
    ):
        """The outcome says the person is coming back; the link says which
        booking answered that. One does not imply the other, and a session can
        carry either alone."""
        client = client_with_clinical_scope
        response = await client.post(
            f"/service-sessions/?tenant_id={session_test_tenant['id']}",
            json={
                "service_id": session_test_service["id"],
                "provider_id": session_test_provider["id"],
                "member_id": session_test_client_person["id"],
                "scheduled_at": (datetime.now(UTC) + timedelta(days=43)).isoformat(),
                "delivery_context": "Direct",
                "clinical_outcome": "ToBeContinued",
            },
        )

        assert response.status_code == 201, response.text
        assert response.json()["clinical_outcome"] == "ToBeContinued"
        assert response.json()["follow_up_of_session_id"] is None


class TestSessionNumbering:
    """The ordinal is counted from the chain, not typed.

    A typed ordinal is entered per session, by hand, from memory. Counting from
    the session a booking follows removes every entry after the first. See
    decision 7 in docs/design/REALTIME_SESSION_CAPTURE.md.
    """

    async def _book(self, client, tenant_id, service, provider, member, *, at, **extra):
        return await client.post(
            f"/service-sessions/?tenant_id={tenant_id}",
            json={
                "service_id": service["id"],
                "provider_id": provider["id"],
                "member_id": member["id"],
                "scheduled_at": at.isoformat(),
                "delivery_context": "Direct",
                **extra,
            },
        )

    async def test_a_follow_up_counts_on_from_the_session_it_follows(
        self,
        client: AsyncClient,
        session_test_tenant: dict,
        session_test_service: dict,
        session_test_provider: dict,
        session_test_client_person: dict,
    ):
        tenant_id = session_test_tenant["id"]
        first = await self._book(
            client,
            tenant_id,
            session_test_service,
            session_test_provider,
            session_test_client_person,
            at=datetime.now(UTC) + timedelta(days=60),
            session_number=1,
        )
        assert first.status_code == 201, first.text

        second = await self._book(
            client,
            tenant_id,
            session_test_service,
            session_test_provider,
            session_test_client_person,
            at=datetime.now(UTC) + timedelta(days=67),
            follow_up_of_session_id=first.json()["id"],
        )

        assert second.status_code == 201, second.text
        assert second.json()["session_number"] == 2

    async def test_the_count_carries_along_a_chain(
        self,
        client: AsyncClient,
        session_test_tenant: dict,
        session_test_service: dict,
        session_test_provider: dict,
        session_test_client_person: dict,
    ):
        tenant_id = session_test_tenant["id"]
        previous = await self._book(
            client,
            tenant_id,
            session_test_service,
            session_test_provider,
            session_test_client_person,
            at=datetime.now(UTC) + timedelta(days=61),
            session_number=1,
        )
        numbers = []
        for week in range(2, 5):
            nxt = await self._book(
                client,
                tenant_id,
                session_test_service,
                session_test_provider,
                session_test_client_person,
                at=datetime.now(UTC) + timedelta(days=61 + week * 7),
                follow_up_of_session_id=previous.json()["id"],
            )
            assert nxt.status_code == 201, nxt.text
            numbers.append(nxt.json()["session_number"])
            previous = nxt

        assert numbers == [2, 3, 4]

    async def test_the_first_session_numbers_itself(
        self,
        client,
        session_test_tenant,
        session_test_service,
        session_test_provider,
        session_test_client_person,
    ):
        """Nothing is typed. A person filling a form cannot know the ordinal."""
        response = await self._book(
            client,
            session_test_tenant["id"],
            session_test_service,
            session_test_provider,
            session_test_client_person,
            at=datetime.now(UTC) + timedelta(days=62),
        )

        assert response.status_code == 201, response.text
        assert response.json()["session_number"] == 1

    async def test_a_backdated_session_takes_its_place_and_pushes_the_others_along(
        self,
        client,
        session_test_tenant,
        session_test_service,
        session_test_provider,
        session_test_client_person,
    ):
        """The ordinal is a view of the dates, so a backlog entry resequences.

        Nothing is renumbered because nothing was numbered.
        """
        tenant_id = session_test_tenant["id"]
        later = await self._book(
            client,
            tenant_id,
            session_test_service,
            session_test_provider,
            session_test_client_person,
            at=datetime.now(UTC) + timedelta(days=63),
        )
        assert later.json()["session_number"] == 1

        await self._book(
            client,
            tenant_id,
            session_test_service,
            session_test_provider,
            session_test_client_person,
            at=datetime.now(UTC) - timedelta(days=5),
        )

        reread = await client.get(f"/service-sessions/{later.json()['id']}")
        assert reread.json()["session_number"] == 2

    async def test_a_follow_up_cannot_name_an_unknown_session(
        self,
        client: AsyncClient,
        session_test_tenant: dict,
        session_test_service: dict,
        session_test_provider: dict,
        session_test_client_person: dict,
    ):
        response = await self._book(
            client,
            session_test_tenant["id"],
            session_test_service,
            session_test_provider,
            session_test_client_person,
            at=datetime.now(UTC) + timedelta(days=64),
            follow_up_of_session_id="does-not-exist",
        )

        assert response.status_code == 404, response.text

    async def test_a_follow_up_cannot_chain_onto_another_person(
        self,
        client: AsyncClient,
        session_test_tenant: dict,
        session_test_service: dict,
        session_test_provider: dict,
        session_test_client_person: dict,
    ):
        """Otherwise the ordinal would count somebody else's history."""
        tenant_id = session_test_tenant["id"]
        talk = await client.post(
            f"/service-sessions/?tenant_id={tenant_id}",
            json={
                "service_id": session_test_service["id"],
                "provider_id": session_test_provider["id"],
                "attendance": "CompanyWide",
                "client_id": session_test_client_person["client_id"],
                "headcount": 30,
                "scheduled_at": (datetime.now(UTC) + timedelta(days=65)).isoformat(),
                "delivery_context": "Direct",
            },
        )
        assert talk.status_code == 201, talk.text

        response = await self._book(
            client,
            tenant_id,
            session_test_service,
            session_test_provider,
            session_test_client_person,
            at=datetime.now(UTC) + timedelta(days=72),
            follow_up_of_session_id=talk.json()["id"],
        )

        assert response.status_code == 422, response.text


class TestAFollowUpMayChangeIntervention:
    """Care moves between interventions: individual, then couples, then family.

    Those are separate services that share the ShortTermCounselling category,
    which is also what an authorisation is keyed on. The follow-up link does not
    pin the service, so the chain survives the change.
    """

    async def _service(self, client, tenant_id, name, category):
        response = await client.post(
            f"/services/?tenant_id={tenant_id}",
            json={
                "name": name,
                "description": name,
                "category": category,
                "duration_minutes": 60,
                "is_group_service": False,
            },
        )
        assert response.status_code == 201, response.text
        return response.json()

    async def test_a_chain_moves_from_individual_to_couples_to_family(
        self,
        client: AsyncClient,
        session_test_tenant: dict,
        session_test_provider: dict,
        session_test_client_person: dict,
    ):
        tenant_id = session_test_tenant["id"]
        individual = await self._service(
            client, tenant_id, "Individual Counselling", "ShortTermCounselling"
        )
        couples = await self._service(
            client, tenant_id, "Couple Counselling", "ShortTermCounselling"
        )
        family = await self._service(client, tenant_id, "Family Therapy", "ShortTermCounselling")

        previous, numbers, services = None, [], []
        for offset, service in enumerate((individual, couples, family)):
            body = {
                "service_id": service["id"],
                "provider_id": session_test_provider["id"],
                "member_id": session_test_client_person["id"],
                "scheduled_at": (datetime.now(UTC) + timedelta(days=80 + offset * 7)).isoformat(),
                "delivery_context": "Direct",
            }
            if previous is None:
                pass
            else:
                body["follow_up_of_session_id"] = previous
            response = await client.post(f"/service-sessions/?tenant_id={tenant_id}", json=body)
            assert response.status_code == 201, response.text
            previous = response.json()["id"]
            numbers.append(response.json()["session_number"])
            services.append(response.json()["service_id"])

        # The intervention changes at every step; the count does not restart.
        assert numbers == [1, 2, 3]
        assert services == [individual["id"], couples["id"], family["id"]]
        assert len(set(services)) == 3

    async def test_the_chain_is_not_pinned_to_one_service_category_either(
        self,
        client: AsyncClient,
        session_test_tenant: dict,
        session_test_provider: dict,
        session_test_client_person: dict,
    ):
        """Recorded rather than asserted as correct: nothing currently stops a
        follow-up crossing into another category, and whether it should is an
        open question in docs/design/REALTIME_SESSION_CAPTURE.md."""
        tenant_id = session_test_tenant["id"]
        counselling = await self._service(
            client, tenant_id, "Individual Counselling B", "ShortTermCounselling"
        )
        crisis = await self._service(
            client, tenant_id, "Crisis Intervention B", "CrisisIntervention"
        )

        first = await client.post(
            f"/service-sessions/?tenant_id={tenant_id}",
            json={
                "service_id": counselling["id"],
                "provider_id": session_test_provider["id"],
                "member_id": session_test_client_person["id"],
                "scheduled_at": (datetime.now(UTC) + timedelta(days=90)).isoformat(),
                "delivery_context": "Direct",
                "session_number": 1,
            },
        )
        assert first.status_code == 201, first.text

        crossing = await client.post(
            f"/service-sessions/?tenant_id={tenant_id}",
            json={
                "service_id": crisis["id"],
                "provider_id": session_test_provider["id"],
                "member_id": session_test_client_person["id"],
                "scheduled_at": (datetime.now(UTC) + timedelta(days=97)).isoformat(),
                "delivery_context": "Direct",
                "follow_up_of_session_id": first.json()["id"],
            },
        )

        assert crossing.status_code == 201, crossing.text
        assert crossing.json()["session_number"] == 2


class TestClientTypeIsCounted:
    """New or Repeat is read off the dates, not asked on a form.

    It used to be a field someone typed, carried in from the counsellor's
    spreadsheet. Nothing in the platform read it.
    """

    async def _book(self, client, tenant_id, service, provider, member, *, at):
        return await client.post(
            f"/service-sessions/?tenant_id={tenant_id}",
            json={
                "service_id": service["id"],
                "provider_id": provider["id"],
                "member_id": member["id"],
                "scheduled_at": at.isoformat(),
                "delivery_context": "Direct",
            },
        )

    async def test_a_members_first_session_is_new_and_the_next_is_repeat(
        self,
        client,
        session_test_tenant,
        session_test_service,
        session_test_provider,
        session_test_client_person,
    ):
        tenant_id = session_test_tenant["id"]
        first = await self._book(
            client,
            tenant_id,
            session_test_service,
            session_test_provider,
            session_test_client_person,
            at=datetime.now(UTC) + timedelta(days=110),
        )
        second = await self._book(
            client,
            tenant_id,
            session_test_service,
            session_test_provider,
            session_test_client_person,
            at=datetime.now(UTC) + timedelta(days=117),
        )

        assert first.json()["client_type"] == "New"
        assert second.json()["client_type"] == "Repeat"

    async def test_a_backdated_session_takes_over_as_the_new_one(
        self,
        client,
        session_test_tenant,
        session_test_service,
        session_test_provider,
        session_test_client_person,
    ):
        """Same counting as the ordinal, so the two can never disagree."""
        tenant_id = session_test_tenant["id"]
        booked = await self._book(
            client,
            tenant_id,
            session_test_service,
            session_test_provider,
            session_test_client_person,
            at=datetime.now(UTC) + timedelta(days=111),
        )
        assert booked.json()["client_type"] == "New"

        earlier = await self._book(
            client,
            tenant_id,
            session_test_service,
            session_test_provider,
            session_test_client_person,
            at=datetime.now(UTC) - timedelta(days=9),
        )

        assert earlier.json()["client_type"] == "New"
        reread = await client.get(f"/service-sessions/{booked.json()['id']}")
        assert reread.json()["client_type"] == "Repeat"

    async def test_the_form_can_no_longer_send_one(
        self,
        client,
        session_test_tenant,
        session_test_service,
        session_test_provider,
        session_test_client_person,
    ):
        """Accepting a value it then ignores would be worse than refusing it."""
        response = await client.post(
            f"/service-sessions/?tenant_id={session_test_tenant['id']}",
            json={
                "service_id": session_test_service["id"],
                "provider_id": session_test_provider["id"],
                "member_id": session_test_client_person["id"],
                "scheduled_at": (datetime.now(UTC) + timedelta(days=112)).isoformat(),
                "delivery_context": "Direct",
                "client_type": "Repeat",
                "session_number": 7,
            },
        )

        assert response.status_code == 201, response.text
        # Counted, not taken from the request.
        assert response.json()["client_type"] == "New"
        assert response.json()["session_number"] == 1


class TestSessionChain:
    async def _book(self, client, tenant_id, service, provider, member, *, at, follows=None):
        body = {
            "service_id": service["id"],
            "provider_id": provider["id"],
            "member_id": member["id"],
            "scheduled_at": at.isoformat(),
            "delivery_context": "Direct",
        }
        if follows:
            body["follow_up_of_session_id"] = follows
        return await client.post(f"/service-sessions/?tenant_id={tenant_id}", json=body)

    async def test_the_middle_of_a_chain_sees_both_ways(
        self,
        client,
        session_test_tenant,
        session_test_service,
        session_test_provider,
        session_test_client_person,
    ):
        tenant_id = session_test_tenant["id"]
        first = await self._book(
            client,
            tenant_id,
            session_test_service,
            session_test_provider,
            session_test_client_person,
            at=datetime.now(UTC) + timedelta(days=120),
        )
        second = await self._book(
            client,
            tenant_id,
            session_test_service,
            session_test_provider,
            session_test_client_person,
            at=datetime.now(UTC) + timedelta(days=127),
            follows=first.json()["id"],
        )
        third = await self._book(
            client,
            tenant_id,
            session_test_service,
            session_test_provider,
            session_test_client_person,
            at=datetime.now(UTC) + timedelta(days=134),
            follows=second.json()["id"],
        )

        response = await client.get(f"/service-sessions/{second.json()['id']}/chain")

        assert response.status_code == 200, response.text
        body = response.json()
        assert body["previous"]["id"] == first.json()["id"]
        assert [f["id"] for f in body["following"]] == [third.json()["id"]]

    async def test_a_lone_session_has_nothing_either_way(
        self,
        client,
        session_test_tenant,
        session_test_service,
        session_test_provider,
        session_test_client_person,
    ):
        booked = await self._book(
            client,
            session_test_tenant["id"],
            session_test_service,
            session_test_provider,
            session_test_client_person,
            at=datetime.now(UTC) + timedelta(days=121),
        )

        response = await client.get(f"/service-sessions/{booked.json()['id']}/chain")

        assert response.status_code == 200, response.text
        assert response.json()["previous"] is None
        assert response.json()["following"] == []

    async def test_the_chain_is_not_swallowed_by_the_session_id_route(
        self,
        client,
        session_test_tenant,
        session_test_service,
        session_test_provider,
        session_test_client_person,
    ):
        booked = await self._book(
            client,
            session_test_tenant["id"],
            session_test_service,
            session_test_provider,
            session_test_client_person,
            at=datetime.now(UTC) + timedelta(days=122),
        )

        response = await client.get(f"/service-sessions/{booked.json()['id']}/chain")

        assert response.status_code == 200, response.text
        assert "following" in response.json()


CLINICAL_FIELDS = (
    "notes",
    "feedback",
    "issue_topic",
    "diagnosis_type_id",
    "diagnosis_id",
    "partner_name",
    "partner_relationship",
    "clinical_outcome",
)


class TestClinicalScopeGating:
    """R1: clinical fields are null without AccessScope.CLINICAL, on every read path."""

    async def _clinical_session(self, client, tenant_id, service, provider, member, *, at) -> dict:
        response = await client.post(
            f"/service-sessions/?tenant_id={tenant_id}",
            json={
                "service_id": service["id"],
                "provider_id": provider["id"],
                "member_id": member["id"],
                "scheduled_at": at.isoformat(),
                "delivery_context": "Direct",
                "category": "Couples",
                "issue_topic": "Workplace stress",
                "diagnosis_type_id": "dx-type-1",
                "diagnosis_id": "dx-1",
                "partner_name": "Alex",
                "partner_relationship": "Spouse",
                "clinical_outcome": "ToBeContinued",
            },
        )
        assert response.status_code == 201, response.text
        return response.json()

    def _assert_redacted(self, data: dict) -> None:
        for field in CLINICAL_FIELDS:
            assert data[field] is None, f"{field} was not redacted: {data[field]!r}"

    def _assert_visible(self, data: dict) -> None:
        assert data["issue_topic"] == "Workplace stress"
        assert data["diagnosis_id"] == "dx-1"
        assert data["partner_name"] == "Alex"
        assert data["clinical_outcome"] == "ToBeContinued"

    # `client` and `client_with_clinical_scope` share one FastAPI app whose
    # dependency_overrides is a single global dict, so requesting both in one
    # test would have the second fixture's scope silently apply to calls made
    # with the "other" client too. Each test below picks exactly one.

    async def test_detail_redacts_without_scope(
        self,
        client: AsyncClient,
        session_test_tenant: dict,
        session_test_service: dict,
        session_test_provider: dict,
        session_test_client_person: dict,
    ):
        session = await self._clinical_session(
            client,
            session_test_tenant["id"],
            session_test_service,
            session_test_provider,
            session_test_client_person,
            at=datetime.now(UTC) + timedelta(days=200),
        )
        response = await client.get(f"/service-sessions/{session['id']}")
        assert response.status_code == 200
        self._assert_redacted(response.json())
        assert response.json()["status"] == "Scheduled"  # operational field intact

    async def test_detail_visible_with_clinical_scope(
        self,
        client_with_clinical_scope: AsyncClient,
        session_test_tenant: dict,
        session_test_service: dict,
        session_test_provider: dict,
        session_test_client_person: dict,
    ):
        session = await self._clinical_session(
            client_with_clinical_scope,
            session_test_tenant["id"],
            session_test_service,
            session_test_provider,
            session_test_client_person,
            at=datetime.now(UTC) + timedelta(days=201),
        )
        response = await client_with_clinical_scope.get(f"/service-sessions/{session['id']}")
        assert response.status_code == 200
        self._assert_visible(response.json())

    async def test_list_redacts_without_scope(
        self,
        client: AsyncClient,
        session_test_tenant: dict,
        session_test_service: dict,
        session_test_provider: dict,
        session_test_client_person: dict,
    ):
        tenant_id = session_test_tenant["id"]
        await self._clinical_session(
            client,
            tenant_id,
            session_test_service,
            session_test_provider,
            session_test_client_person,
            at=datetime.now(UTC) + timedelta(days=202),
        )
        response = await client.get(f"/service-sessions/?tenant_id={tenant_id}")
        assert response.status_code == 200
        for item in response.json()["items"]:
            self._assert_redacted(item)

    async def test_list_visible_with_clinical_scope(
        self,
        client_with_clinical_scope: AsyncClient,
        session_test_tenant: dict,
        session_test_service: dict,
        session_test_provider: dict,
        session_test_client_person: dict,
    ):
        tenant_id = session_test_tenant["id"]
        await self._clinical_session(
            client_with_clinical_scope,
            tenant_id,
            session_test_service,
            session_test_provider,
            session_test_client_person,
            at=datetime.now(UTC) + timedelta(days=203),
        )
        response = await client_with_clinical_scope.get(f"/service-sessions/?tenant_id={tenant_id}")
        assert response.status_code == 200
        assert any(item["clinical_outcome"] == "ToBeContinued" for item in response.json()["items"])

    async def test_by_member_provider_service_redact_without_scope(
        self,
        client: AsyncClient,
        session_test_tenant: dict,
        session_test_service: dict,
        session_test_provider: dict,
        session_test_client_person: dict,
    ):
        tenant_id = session_test_tenant["id"]
        await self._clinical_session(
            client,
            tenant_id,
            session_test_service,
            session_test_provider,
            session_test_client_person,
            at=datetime.now(UTC) + timedelta(days=204),
        )
        member_id = session_test_client_person["id"]
        provider_id = session_test_provider["id"]
        service_id = session_test_service["id"]

        for path in (
            f"/service-sessions/member/{member_id}?tenant_id={tenant_id}",
            f"/service-sessions/provider/{provider_id}?tenant_id={tenant_id}",
            f"/service-sessions/service/{service_id}?tenant_id={tenant_id}",
        ):
            response = await client.get(path)
            assert response.status_code == 200, response.text
            for item in response.json():
                self._assert_redacted(item)

    async def test_by_member_provider_service_visible_with_clinical_scope(
        self,
        client_with_clinical_scope: AsyncClient,
        session_test_tenant: dict,
        session_test_service: dict,
        session_test_provider: dict,
        session_test_client_person: dict,
    ):
        tenant_id = session_test_tenant["id"]
        await self._clinical_session(
            client_with_clinical_scope,
            tenant_id,
            session_test_service,
            session_test_provider,
            session_test_client_person,
            at=datetime.now(UTC) + timedelta(days=205),
        )
        member_id = session_test_client_person["id"]
        provider_id = session_test_provider["id"]
        service_id = session_test_service["id"]

        for path in (
            f"/service-sessions/member/{member_id}?tenant_id={tenant_id}",
            f"/service-sessions/provider/{provider_id}?tenant_id={tenant_id}",
            f"/service-sessions/service/{service_id}?tenant_id={tenant_id}",
        ):
            response = await client_with_clinical_scope.get(path)
            assert response.status_code == 200, response.text
            assert any(item["clinical_outcome"] == "ToBeContinued" for item in response.json())

    async def test_chain_redacts_without_scope(
        self,
        client: AsyncClient,
        session_test_tenant: dict,
        session_test_service: dict,
        session_test_provider: dict,
        session_test_client_person: dict,
    ):
        tenant_id = session_test_tenant["id"]
        first = await self._clinical_session(
            client,
            tenant_id,
            session_test_service,
            session_test_provider,
            session_test_client_person,
            at=datetime.now(UTC) + timedelta(days=206),
        )
        follow_up = await self._clinical_session(
            client,
            tenant_id,
            session_test_service,
            session_test_provider,
            session_test_client_person,
            at=datetime.now(UTC) + timedelta(days=207),
        )
        await client.patch(
            f"/service-sessions/{follow_up['id']}",
            json={"follow_up_of_session_id": first["id"]},
        )

        response = await client.get(f"/service-sessions/{first['id']}/chain")
        assert response.status_code == 200
        for item in response.json()["following"]:
            self._assert_redacted(item)

    async def test_awaiting_confirmation_redacts_without_scope(
        self,
        client: AsyncClient,
        session_test_tenant: dict,
        session_test_service: dict,
        session_test_provider: dict,
        session_test_client_person: dict,
    ):
        tenant_id = session_test_tenant["id"]
        past = await self._clinical_session(
            client,
            tenant_id,
            session_test_service,
            session_test_provider,
            session_test_client_person,
            at=datetime.now(UTC) - timedelta(days=1),
        )

        response = await client.get(
            f"/service-sessions/awaiting-confirmation?tenant_id={tenant_id}"
        )
        assert response.status_code == 200, response.text
        matching = [item for item in response.json()["items"] if item["id"] == past["id"]]
        assert len(matching) == 1
        self._assert_redacted(matching[0])

    async def test_wrong_tenant_still_gets_404_with_clinical_scope(
        self,
        client_with_clinical_scope: AsyncClient,
        session_test_tenant: dict,
        session_test_service: dict,
        session_test_provider: dict,
        session_test_client_person: dict,
    ):
        """Clinical scope is not a substitute for tenant membership."""
        session = await self._clinical_session(
            client_with_clinical_scope,
            session_test_tenant["id"],
            session_test_service,
            session_test_provider,
            session_test_client_person,
            at=datetime.now(UTC) + timedelta(days=208),
        )
        other_tenant = await client_with_clinical_scope.post(
            "/tenants/", json={"name": "Other Tenant", "code": "other-scope"}
        )
        assert other_tenant.status_code == 201, other_tenant.text

        response = await client_with_clinical_scope.get(
            f"/service-sessions/{session['id']}?tenant_id={other_tenant.json()['id']}"
        )
        assert response.status_code == 404
