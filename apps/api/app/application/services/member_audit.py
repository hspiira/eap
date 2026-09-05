"""Durable roster audit metadata without copying member/contact PII."""

from app.domain.repositories.outbox_repository import OutboxRepository
from app.shared.utils.datetime import utc_now


async def record_member_change(
    outbox: OutboxRepository,
    *,
    tenant_id: str,
    user_id: str,
    resource_id: str,
    action: str,
    operation: str,
    member_id: str | None = None,
) -> None:
    resource_type = "MemberNextOfKin" if member_id else "EligibleMember"
    event_type = f"{resource_type}{operation}"
    await outbox.enqueue(
        tenant_id=tenant_id,
        event_type=event_type,
        occurred_at=utc_now(),
        aggregate_type=resource_type,
        aggregate_id=resource_id,
        payload={
            "action_type": action,
            "resource_type": resource_type,
            "resource_id": resource_id,
            "user_id": user_id,
            "event_type": event_type,
            "event_data": {"member_id": member_id} if member_id else {},
            "field_changes": [],
            "is_special_category": True,
        },
    )
