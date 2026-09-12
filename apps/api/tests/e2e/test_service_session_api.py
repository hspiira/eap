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

    async def test_complete_session_success(self, client: AsyncClient, test_service_session: dict):
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

    async def test_update_session_notes(self, client: AsyncClient, test_service_session: dict):
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

    async def test_update_feedback_success(self, client: AsyncClient, test_service_session: dict):
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
