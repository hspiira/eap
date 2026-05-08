"""Activity Use Cases - Application services for Activity operations."""

from datetime import datetime

from app.application.use_cases.base import BaseUseCase
from app.domain.entities.activity import ActivityEntity
from app.domain.repositories.activity_repository import ActivityRepository
from app.domain.value_objects.core import ActivityId, TenantId, UserId
from app.shared.utils.datetime import utc_now


class CreateActivityUseCase(BaseUseCase[ActivityEntity, ActivityId]):
    """Use case for creating an activity."""

    def __init__(self, activity_repository: ActivityRepository):
        super().__init__(activity_repository)

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
        """Create a new activity."""
        now = utc_now()
        activity = ActivityEntity(
            id=activity_id,
            tenant_id=tenant_id,
            client_id=client_id,
            activity_type=activity_type,
            description=description,
            created_by=created_by,
            occurred_at=occurred_at or now,
            subject=subject,
            outcome=outcome,
            next_follow_up=next_follow_up,
            is_important=is_important,
            created_at=now,
            updated_at=now,
        )

        return await self._save_and_publish_events(activity)


class UpdateActivityUseCase(BaseUseCase[ActivityEntity, ActivityId]):
    """Use case for updating an activity."""

    def __init__(self, activity_repository: ActivityRepository):
        super().__init__(activity_repository)

    async def execute(
        self,
        activity_id: ActivityId,
        description: str | None = None,
        outcome: str | None = None,
        next_follow_up: datetime | None = None,
        is_important: bool | None = None,
    ) -> ActivityEntity:
        """Update an activity."""
        activity = await self._get_entity_or_raise(activity_id, "Activity")

        if description is not None:
            activity.update_description(description)
        if outcome is not None:
            activity.update_outcome(outcome)
        if next_follow_up is not None:
            activity.set_follow_up(next_follow_up)
        if is_important is not None:
            activity.mark_important(is_important)

        return await self._save_and_publish_events(activity)


class GetActivityUseCase(BaseUseCase[ActivityEntity, ActivityId]):
    """Use case for retrieving an activity."""

    def __init__(self, activity_repository: ActivityRepository):
        super().__init__(activity_repository)

    async def execute(self, activity_id: ActivityId) -> ActivityEntity | None:
        """Get activity by ID."""
        return await self.repository.get_by_id(activity_id)
