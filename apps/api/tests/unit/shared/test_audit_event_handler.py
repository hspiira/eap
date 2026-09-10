"""AuditEventHandler now enqueues onto the outbox (Phase 1 #C10)."""

from datetime import UTC, datetime
from typing import Any

import pytest

from app.domain.entities.user import UserEntity
from app.domain.enums import UserStatus
from app.domain.events import UserActivated
from app.domain.repositories.outbox_repository import OutboxBacklog, OutboxRepository
from app.domain.value_objects.core import Email, TenantId, UserId
from app.shared.handlers.audit_event_handler import AuditEventHandler


class _RecordingOutbox(OutboxRepository):
    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []

    async def enqueue(
        self,
        *,
        tenant_id: str,
        event_type: str,
        payload: dict[str, Any],
        occurred_at: datetime,
        aggregate_type: str | None = None,
        aggregate_id: str | None = None,
    ) -> str:
        self.calls.append(
            {
                "tenant_id": tenant_id,
                "event_type": event_type,
                "payload": payload,
                "occurred_at": occurred_at,
                "aggregate_type": aggregate_type,
                "aggregate_id": aggregate_id,
            }
        )
        return "outbox-id"

    async def fetch_undelivered(self, *, limit: int = 100):
        return []

    async def mark_delivered(self, event_id: str) -> None:
        pass

    async def mark_failed(
        self, event_id: str, error: str, next_attempt_at: datetime | None = None
    ) -> None:
        pass

    async def backlog(self) -> OutboxBacklog:
        return OutboxBacklog(depth=0, oldest_undelivered=None, failed=0)


def _user() -> UserEntity:
    now = datetime.now(UTC)
    return UserEntity(
        id=UserId("u-1"),
        tenant_id=TenantId("t-1"),
        email=Email("u@example.com"),
        status=UserStatus.ACTIVE,
        is_two_factor_enabled=False,
        created_at=now,
        updated_at=now,
    )


@pytest.mark.asyncio
async def test_handle_events_enqueues_to_outbox():
    user = _user()
    outbox = _RecordingOutbox()
    handler = AuditEventHandler(outbox)
    now = datetime.now(UTC)
    events = [UserActivated(occurred_at=now, user_id=user.id)]

    await handler.handle_events(
        entity=user,
        events=events,
        tenant_id=user.tenant_id,
        user_id=user.id,
        ip_address="127.0.0.1",
        user_agent="pytest",
    )

    assert len(outbox.calls) == 1
    call = outbox.calls[0]
    assert call["tenant_id"] == "t-1"
    assert call["event_type"] == "UserActivated"
    assert call["payload"]["resource_type"] == "User"
    assert call["payload"]["resource_id"] == "u-1"
    assert call["payload"]["user_id"] == "u-1"
    assert call["payload"]["ip_address"] == "127.0.0.1"
    assert call["payload"]["event_type"] == "UserActivated"


@pytest.mark.asyncio
async def test_handle_events_no_op_when_events_empty():
    outbox = _RecordingOutbox()
    handler = AuditEventHandler(outbox)
    await handler.handle_events(
        entity=_user(),
        events=[],
        tenant_id=TenantId("t-1"),
    )
    assert outbox.calls == []


def _session():
    """A completed session carrying the fields a note would live in."""
    from app.domain.entities.service_session import ServiceSessionEntity
    from app.domain.enums import SessionAttendance, SessionDeliveryContext, SessionStatus
    from app.domain.value_objects.core import ClientId, ProviderId, ServiceId, SessionId

    now = datetime.now(UTC)
    return ServiceSessionEntity(
        id=SessionId("s-1"),
        tenant_id=TenantId("t-1"),
        service_id=ServiceId("svc-1"),
        provider_id=ProviderId("prv-1"),
        client_id=ClientId("cli-1"),
        member_id=None,
        attendance=SessionAttendance.COMPANY_WIDE,
        scheduled_at=now,
        status=SessionStatus.SCHEDULED,
        reschedule_count=0,
        delivery_context=SessionDeliveryContext.DIRECT,
        created_at=now,
        updated_at=now,
    )


@pytest.mark.asyncio
async def test_a_session_diff_records_the_field_and_not_its_content():
    """The audit trail says a note was edited, never what the note says."""
    from copy import deepcopy

    session = _session()
    before = deepcopy(session)
    session.update_notes("Discussed bereavement and sleep")
    outbox = _RecordingOutbox()

    await AuditEventHandler(outbox).handle_events(
        entity=session,
        events=list(session.events),
        tenant_id=TenantId("t-1"),
        user_id=UserId("u-1"),
        old_entity=before,
    )

    payload = outbox.calls[0]["payload"]
    assert payload["is_special_category"] is True
    changed = {c["field_name"]: c["new_value"] for c in payload["field_changes"]}
    assert changed["notes"] == "[redacted]"
    assert "Discussed bereavement and sleep" not in str(payload)


@pytest.mark.asyncio
async def test_an_ordinary_record_keeps_its_values():
    """Redaction is for clinical records, not a blanket rule."""
    from copy import deepcopy

    from app.domain.entities.client import ClientEntity
    from app.domain.enums import BaseStatus
    from app.domain.value_objects.core import ClientId, ContactInfo

    now = datetime.now(UTC)
    client = ClientEntity(
        id=ClientId("c-1"),
        tenant_id=TenantId("t-1"),
        name="Acme Corp",
        code="ACME",
        contact_info=ContactInfo(),
        status=BaseStatus.ACTIVE,
        is_verified=True,
        created_at=now,
        updated_at=now,
    )
    before = deepcopy(client)
    client.update_name("Acme Holdings")
    outbox = _RecordingOutbox()

    await AuditEventHandler(outbox).handle_events(
        entity=client,
        events=list(client.events),
        tenant_id=TenantId("t-1"),
        user_id=UserId("u-1"),
        old_entity=before,
    )

    payload = outbox.calls[0]["payload"]
    assert payload["is_special_category"] is False
    changed = {c["field_name"]: (c["old_value"], c["new_value"]) for c in payload["field_changes"]}
    assert changed["name"] == ("Acme Corp", "Acme Holdings")
