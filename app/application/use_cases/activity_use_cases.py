"""Activity Use Cases - Application services for Activity operations."""

from datetime import datetime

from app.domain.entities.activity import ActivityEntity
from app.domain.repositories.activity_repository import ActivityRepository
from app.domain.value_objects.core import ActivityId, TenantId, UserId
from app.shared.utils.datetime import utc_now


class CreateActivityUseCase:
    def __init__(self, activity_repository: ActivityRepository):
        self.activity_repository = activity_repository

    async def execute(
        self,
        activity_id: ActivityId,
        tenant_id: TenantId,
        client_id: str,
        activity_type: str,
        description: str,
        created_by: UserId,
        subject: str | None = None,
        outcome: str | None = None,
        occurred_at: datetime | None = None,
        next_follow_up: datetime | None = None,
        is_important: bool = False,
    ) -> ActivityEntity:
        activity = ActivityEntity(
            _id=activity_id,
            _tenant_id=tenant_id,
            _client_id=client_id,
            _activity_type=activity_type,
            _description=description,
            _created_by=created_by,
            _occurred_at=occurred_at or utc_now(),
            _subject=subject,
            _outcome=outcome,
            _next_follow_up=next_follow_up,
            _is_important=is_important,
            _created_at=utc_now(),
            _updated_at=utc_now(),
        )

        await self.activity_repository.save(activity)
        return activity


class UpdateActivityUseCase:
    def __init__(self, activity_repository: ActivityRepository):
        self.activity_repository = activity_repository

    async def execute(
        self,
        activity_id: ActivityId,
        description: str | None = None,
        outcome: str | None = None,
        next_follow_up: datetime | None = None,
        is_important: bool | None = None,
    ) -> ActivityEntity:
        activity = await self.activity_repository.get_by_id(activity_id)
        if not activity:
            raise ValueError(f"Activity {activity_id.value} not found")

        if description:
            activity.update_description(description)
        if outcome is not None:
            activity.update_outcome(outcome)
        if next_follow_up is not None:
            activity.set_follow_up(next_follow_up)
        if is_important is not None:
            activity.mark_important(is_important)

        await self.activity_repository.save(activity)
        return activity


class GetActivityUseCase:
    def __init__(self, activity_repository: ActivityRepository):
        self.activity_repository = activity_repository

    async def execute(self, activity_id: ActivityId) -> ActivityEntity | None:
        return await self.activity_repository.get_by_id(activity_id)
