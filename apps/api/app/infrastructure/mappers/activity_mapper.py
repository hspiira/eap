"""Activity Mapper - converts between ActivityEntity and ActivityModel."""

from app.domain.entities.activity import ActivityEntity
from app.domain.value_objects.core import ActivityId, TenantId, UserId
from app.infrastructure.models.activity_model import ActivityModel
from app.shared.utils.datetime import ensure_utc


class ActivityMapper:
    @staticmethod
    def to_entity(model: ActivityModel) -> ActivityEntity:
        return ActivityEntity(
            id=ActivityId(model.id),
            tenant_id=TenantId(model.tenant_id),
            client_id=model.client_id,
            activity_type=model.activity_type,
            description=model.description,
            created_by=UserId(model.created_by),
            occurred_at=ensure_utc(model.occurred_at),
            subject=model.subject,
            outcome=model.outcome,
            next_follow_up=ensure_utc(model.next_follow_up) if model.next_follow_up else None,
            is_important=model.is_important,
            created_at=ensure_utc(model.created_at),
            updated_at=ensure_utc(model.updated_at),
            deleted_at=ensure_utc(model.deleted_at) if model.deleted_at else None,
        )

    @staticmethod
    def to_model(entity: ActivityEntity) -> ActivityModel:
        return ActivityModel(
            id=entity.id.value,
            tenant_id=entity.tenant_id.value,
            client_id=entity.client_id,
            activity_type=entity.activity_type,
            subject=entity.subject,
            description=entity.description,
            outcome=entity.outcome,
            created_by=entity.created_by.value,
            occurred_at=ensure_utc(entity.occurred_at),
            next_follow_up=ensure_utc(entity.next_follow_up) if entity.next_follow_up else None,
            is_important=entity.is_important,
            created_at=ensure_utc(entity.created_at),
            updated_at=ensure_utc(entity.updated_at),
            deleted_at=ensure_utc(entity.deleted_at) if entity.deleted_at else None,
        )
