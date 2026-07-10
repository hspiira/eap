"""Engagement mapper (Phase 4 #D-Engagement)."""

from datetime import date, datetime

from app.domain.entities.engagement import Deliverable, Engagement, HoursLogEntry
from app.domain.enums import DeliverableStatus, EngagementStatus
from app.domain.value_objects.core import (
    ClientId,
    DeliverableId,
    EngagementId,
    HoursLogEntryId,
    TenantId,
    UserId,
)
from app.infrastructure.models.engagement_model import EngagementModel
from app.shared.utils.datetime import ensure_utc


def _deliverable_to_dict(d: Deliverable) -> dict:
    return {
        "id": d.id.value,
        "title": d.title,
        "description": d.description,
        "due_date": d.due_date.isoformat() if d.due_date else None,
        "status": d.status.value,
        "delivered_at": ensure_utc(d.delivered_at).isoformat()
        if d.delivered_at
        else None,
    }


def _deliverable_from_dict(raw: dict) -> Deliverable:
    delivered_at = raw.get("delivered_at")
    return Deliverable(
        id=DeliverableId(raw["id"]),
        title=raw["title"],
        description=raw.get("description"),
        due_date=date.fromisoformat(raw["due_date"]) if raw.get("due_date") else None,
        status=DeliverableStatus(raw["status"]),
        delivered_at=ensure_utc(datetime.fromisoformat(delivered_at))
        if delivered_at
        else None,
    )


def _hours_to_dict(h: HoursLogEntry) -> dict:
    return {
        "id": h.id.value,
        "user_id": h.user_id.value,
        "logged_on": h.logged_on.isoformat(),
        "hours": h.hours,
        "note": h.note,
    }


def _hours_from_dict(raw: dict) -> HoursLogEntry:
    return HoursLogEntry(
        id=HoursLogEntryId(raw["id"]),
        user_id=UserId(raw["user_id"]),
        logged_on=date.fromisoformat(raw["logged_on"]),
        hours=float(raw["hours"]),
        note=raw.get("note"),
    )


class EngagementMapper:
    @staticmethod
    def to_entity(model: EngagementModel) -> Engagement:
        entity = Engagement(
            id=EngagementId(model.id),
            tenant_id=TenantId(model.tenant_id),
            client_id=ClientId(model.client_id),
            name=model.name,
            description=model.description,
            status=EngagementStatus(model.status),
            period_start=model.period_start,
            period_end=model.period_end,
            deliverables=[_deliverable_from_dict(d) for d in (model.deliverables or [])],
            hours_log=[_hours_from_dict(h) for h in (model.hours_log or [])],
            created_by=UserId(model.created_by),
            activated_at=ensure_utc(model.activated_at)
            if model.activated_at
            else None,
            delivered_at=ensure_utc(model.delivered_at)
            if model.delivered_at
            else None,
            invoiced_at=ensure_utc(model.invoiced_at)
            if model.invoiced_at
            else None,
            closed_at=ensure_utc(model.closed_at) if model.closed_at else None,
            created_at=ensure_utc(model.created_at),
            updated_at=ensure_utc(model.updated_at),
        )
        entity.events.clear()
        return entity

    @staticmethod
    def to_model(entity: Engagement) -> EngagementModel:
        return EngagementModel(
            id=entity.id.value,
            tenant_id=entity.tenant_id.value,
            client_id=entity.client_id.value,
            name=entity.name,
            description=entity.description,
            status=entity.status,
            period_start=entity.period_start,
            period_end=entity.period_end,
            deliverables=[_deliverable_to_dict(d) for d in entity.deliverables],
            hours_log=[_hours_to_dict(h) for h in entity.hours_log],
            created_by=entity.created_by.value,
            activated_at=ensure_utc(entity.activated_at)
            if entity.activated_at
            else None,
            delivered_at=ensure_utc(entity.delivered_at)
            if entity.delivered_at
            else None,
            invoiced_at=ensure_utc(entity.invoiced_at)
            if entity.invoiced_at
            else None,
            closed_at=ensure_utc(entity.closed_at) if entity.closed_at else None,
            created_at=ensure_utc(entity.created_at),
            updated_at=ensure_utc(entity.updated_at),
        )
