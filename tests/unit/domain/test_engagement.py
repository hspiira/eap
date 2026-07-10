"""Engagement aggregate tests (Phase 4 #D-Engagement)."""

from datetime import UTC, date, datetime

import pytest

from app.domain.entities.engagement import Engagement, HoursLogEntry
from app.domain.enums import DeliverableStatus, EngagementStatus
from app.domain.events import (
    EngagementActivated,
    EngagementClosed,
    EngagementCreated,
    EngagementDelivered,
    EngagementInvoiced,
    HoursLogged,
)
from app.domain.exceptions import DomainError, InvalidStateError
from app.domain.value_objects.core import (
    ClientId,
    DeliverableId,
    EngagementId,
    HoursLogEntryId,
    TenantId,
    UserId,
)


def _engagement(*, status: EngagementStatus = EngagementStatus.DRAFT) -> Engagement:
    now = datetime.now(UTC)
    return Engagement(
        id=EngagementId("eng-1"),
        tenant_id=TenantId("t-1"),
        client_id=ClientId("client-1"),
        name="Stanbic strategy advisory",
        status=status,
        created_by=UserId("u-1"),
        created_at=now,
        updated_at=now,
        period_start=date(2026, 5, 1),
        period_end=date(2026, 8, 31),
    )


# ---------- Creation invariants ----------


class TestEngagementCreation:
    def test_emits_created_event(self):
        e = _engagement()
        assert any(isinstance(ev, EngagementCreated) for ev in e.events)

    def test_period_invariant(self):
        now = datetime.now(UTC)
        with pytest.raises(DomainError, match="period_end"):
            Engagement(
                id=EngagementId("eng-x"),
                tenant_id=TenantId("t-1"),
                client_id=ClientId("c-1"),
                name="x",
                status=EngagementStatus.DRAFT,
                created_by=UserId("u-1"),
                created_at=now,
                updated_at=now,
                period_start=date(2026, 9, 1),
                period_end=date(2026, 8, 1),
            )

    def test_name_required(self):
        now = datetime.now(UTC)
        with pytest.raises(DomainError):
            Engagement(
                id=EngagementId("eng-x"),
                tenant_id=TenantId("t-1"),
                client_id=ClientId("c-1"),
                name="",
                status=EngagementStatus.DRAFT,
                created_by=UserId("u-1"),
                created_at=now,
                updated_at=now,
            )


# ---------- Deliverables ----------


class TestDeliverables:
    def test_add_deliverable_when_draft(self):
        e = _engagement()
        d = e.add_deliverable(
            deliverable_id=DeliverableId("d-1"), title="Phase 1 plan"
        )
        assert d.status == DeliverableStatus.PENDING
        assert len(e.deliverables) == 1

    def test_remove_deliverable(self):
        e = _engagement()
        e.add_deliverable(deliverable_id=DeliverableId("d-1"), title="x")
        e.remove_deliverable(DeliverableId("d-1"))
        assert e.deliverables == []

    def test_update_deliverable_progresses_status(self):
        e = _engagement()
        e.add_deliverable(deliverable_id=DeliverableId("d-1"), title="x")
        e.activate()
        e.update_deliverable_status(
            deliverable_id=DeliverableId("d-1"),
            status=DeliverableStatus.IN_PROGRESS,
        )
        assert e.deliverables[0].status == DeliverableStatus.IN_PROGRESS
        e.update_deliverable_status(
            deliverable_id=DeliverableId("d-1"),
            status=DeliverableStatus.DELIVERED,
        )
        assert e.deliverables[0].delivered_at is not None
        e.update_deliverable_status(
            deliverable_id=DeliverableId("d-1"),
            status=DeliverableStatus.ACCEPTED,
        )
        assert e.deliverables[0].status == DeliverableStatus.ACCEPTED

    def test_cannot_add_deliverable_after_delivered(self):
        e = _engagement()
        e.add_deliverable(deliverable_id=DeliverableId("d-1"), title="x")
        e.activate()
        e.update_deliverable_status(
            deliverable_id=DeliverableId("d-1"),
            status=DeliverableStatus.DELIVERED,
        )
        e.deliver()
        with pytest.raises(InvalidStateError):
            e.add_deliverable(deliverable_id=DeliverableId("d-2"), title="late")

    def test_remove_unknown_deliverable_raises(self):
        e = _engagement()
        with pytest.raises(DomainError, match="not found"):
            e.remove_deliverable(DeliverableId("nope"))


# ---------- Hours log ----------


class TestHoursLog:
    def test_log_hours_emits_event_and_updates_total(self):
        e = _engagement()
        e.add_deliverable(deliverable_id=DeliverableId("d-1"), title="x")
        e.activate()
        e.log_hours(
            entry_id=HoursLogEntryId("h-1"),
            user_id=UserId("u-1"),
            logged_on=date(2026, 5, 8),
            hours=4.5,
        )
        assert e.total_hours() == 4.5
        assert any(isinstance(ev, HoursLogged) for ev in e.events)

    def test_hours_by_user_aggregates(self):
        e = _engagement()
        e.add_deliverable(deliverable_id=DeliverableId("d-1"), title="x")
        e.activate()
        e.log_hours(
            entry_id=HoursLogEntryId("h-1"),
            user_id=UserId("u-1"),
            logged_on=date(2026, 5, 8),
            hours=3,
        )
        e.log_hours(
            entry_id=HoursLogEntryId("h-2"),
            user_id=UserId("u-1"),
            logged_on=date(2026, 5, 9),
            hours=2,
        )
        e.log_hours(
            entry_id=HoursLogEntryId("h-3"),
            user_id=UserId("u-2"),
            logged_on=date(2026, 5, 9),
            hours=5,
        )
        assert e.hours_by_user() == {"u-1": 5.0, "u-2": 5.0}

    def test_zero_hours_rejected(self):
        with pytest.raises(DomainError, match="positive"):
            HoursLogEntry(
                id=HoursLogEntryId("h-1"),
                user_id=UserId("u-1"),
                logged_on=date(2026, 5, 8),
                hours=0,
            )

    def test_more_than_24_hours_rejected(self):
        with pytest.raises(DomainError, match="24"):
            HoursLogEntry(
                id=HoursLogEntryId("h-1"),
                user_id=UserId("u-1"),
                logged_on=date(2026, 5, 8),
                hours=25,
            )

    def test_cannot_log_on_closed(self):
        e = _engagement()
        e.add_deliverable(deliverable_id=DeliverableId("d-1"), title="x")
        e.activate()
        e.update_deliverable_status(
            deliverable_id=DeliverableId("d-1"),
            status=DeliverableStatus.DELIVERED,
        )
        e.deliver()
        e.invoice()
        e.close()
        with pytest.raises(InvalidStateError):
            e.log_hours(
                entry_id=HoursLogEntryId("h-1"),
                user_id=UserId("u-1"),
                logged_on=date(2026, 5, 8),
                hours=1,
            )


# ---------- FSM ----------


class TestEngagementFSM:
    def test_cannot_activate_without_deliverables(self):
        e = _engagement()
        with pytest.raises(DomainError, match="no deliverables"):
            e.activate()

    def test_activate_emits_event(self):
        e = _engagement()
        e.add_deliverable(deliverable_id=DeliverableId("d-1"), title="x")
        e.activate()
        assert e.status == EngagementStatus.ACTIVE
        assert e.activated_at is not None
        assert any(isinstance(ev, EngagementActivated) for ev in e.events)

    def test_cannot_deliver_with_outstanding_deliverables(self):
        e = _engagement()
        e.add_deliverable(deliverable_id=DeliverableId("d-1"), title="x")
        e.add_deliverable(deliverable_id=DeliverableId("d-2"), title="y")
        e.activate()
        e.update_deliverable_status(
            deliverable_id=DeliverableId("d-1"),
            status=DeliverableStatus.DELIVERED,
        )
        with pytest.raises(DomainError, match="outstanding"):
            e.deliver()

    def test_full_happy_path(self):
        e = _engagement()
        e.add_deliverable(deliverable_id=DeliverableId("d-1"), title="x")
        e.activate()
        e.update_deliverable_status(
            deliverable_id=DeliverableId("d-1"),
            status=DeliverableStatus.DELIVERED,
        )
        e.deliver()
        assert any(isinstance(ev, EngagementDelivered) for ev in e.events)
        e.invoice()
        assert any(isinstance(ev, EngagementInvoiced) for ev in e.events)
        e.close()
        assert e.status == EngagementStatus.CLOSED
        assert any(isinstance(ev, EngagementClosed) for ev in e.events)

    def test_cannot_close_active(self):
        e = _engagement()
        e.add_deliverable(deliverable_id=DeliverableId("d-1"), title="x")
        e.activate()
        with pytest.raises(InvalidStateError):
            e.close()

    def test_cannot_invoice_draft(self):
        e = _engagement()
        with pytest.raises(InvalidStateError):
            e.invoice()
