"""Activity Mapper - converts between ActivityEntity and ActivityModel."""

from app.domain.entities.activity import ActivityEntity
from app.domain.value_objects.core import ActivityId, TenantId, UserId
from app.infrastructure.models.activity_model import ActivityModel
from app.shared.utils.datetime import ensure_utc


class ActivityMapper:
    @staticmethod
    def to_entity(model: ActivityModel) -> ActivityEntity:
        return ActivityEntity(
            _id=ActivityId(model.id),
            _tenant_id=TenantId(model.tenant_id),
            _client_id=model.client_id,
            _activity_type=model.activity_type,
            _description=model.description,
            _created_by=UserId(model.created_by),
            _occurred_at=ensure_utc(model.occurred_at),
            _subject=model.subject,
            _outcome=model.outcome,
            _next_follow_up=ensure_utc(model.next_follow_up) if model.next_follow_up else None,
            _is_important=model.is_important,
            _created_at=ensure_utc(model.created_at),
            _updated_at=ensure_utc(model.updated_at),
            _deleted_at=ensure_utc(model.deleted_at) if model.deleted_at else None,
        )

    @staticmethod
    def to_model(entity: ActivityEntity) -> ActivityModel:
        return ActivityModel(
            id=entity._id.value,
            tenant_id=entity._tenant_id.value,
            client_id=entity._client_id,
            activity_type=entity._activity_type,
            subject=entity._subject,
            description=entity._description,
            outcome=entity._outcome,
            created_by=entity._created_by.value,
            occurred_at=ensure_utc(entity._occurred_at),
            next_follow_up=ensure_utc(entity._next_follow_up) if entity._next_follow_up else None,
            is_important=entity._is_important,
            created_at=ensure_utc(entity._created_at),
            updated_at=ensure_utc(entity._updated_at),
            deleted_at=ensure_utc(entity._deleted_at) if entity._deleted_at else None,
        )
