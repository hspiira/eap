"""
Service Session Use Cases

Application services for Service Session aggregate operations.
Refactored to use base use case classes.
"""

from datetime import datetime

from app.application.use_cases.base import (
    BaseUseCase,
    create_archive_use_case,
    create_restore_use_case,
)
from app.domain.entities.service_session import ServiceSessionEntity
from app.domain.enums import SessionStatus
from app.domain.repositories.service_session_repository import (
    ServiceSessionRepository,
)
from app.domain.value_objects.core import (
    PersonId,
    ServiceId,
    SessionId,
    TenantId,
)
from app.shared.utils.datetime import utc_now


# =============================================================================
# LIFECYCLE USE CASES (Using Base Factories)
# =============================================================================


class ArchiveServiceSessionUseCase:
    """Use case for archiving a service session."""

    def __init__(self, session_repository: ServiceSessionRepository):
        self._use_case = create_archive_use_case(session_repository, "Session")

    async def execute(self, session_id: SessionId) -> ServiceSessionEntity:
        return await self._use_case.execute(session_id)


class RestoreServiceSessionUseCase:
    """Use case for restoring a service session."""

    def __init__(self, session_repository: ServiceSessionRepository):
        self._use_case = create_restore_use_case(session_repository, "Session")

    async def execute(self, session_id: SessionId) -> ServiceSessionEntity:
        return await self._use_case.execute(session_id)


# =============================================================================
# CREATE USE CASE
# =============================================================================


class CreateServiceSessionUseCase(BaseUseCase[ServiceSessionEntity, SessionId]):
    """Use case for creating a new service session."""

    def __init__(self, session_repository: ServiceSessionRepository):
        super().__init__(session_repository)

    async def execute(
        self,
        session_id: SessionId,
        tenant_id: TenantId,
        service_id: ServiceId,
        provider_id: PersonId,
        person_id: PersonId,
        scheduled_at: datetime,
        location: str | None = None,
    ) -> ServiceSessionEntity:
        """Create a new service session."""
        session = ServiceSessionEntity(
            _id=session_id,
            _tenant_id=tenant_id,
            _service_id=service_id,
            _provider_id=provider_id,
            _person_id=person_id,
            _scheduled_at=scheduled_at,
            _status=SessionStatus.SCHEDULED,
            _created_at=utc_now(),
            _updated_at=utc_now(),
            _reschedule_count=0,
            _location=location,
        )

        return await self._save_and_publish_events(session)


# =============================================================================
# SPECIALIZED COMMAND USE CASES
# =============================================================================


class CompleteServiceSessionUseCase(BaseUseCase[ServiceSessionEntity, SessionId]):
    """Use case for completing a service session."""

    def __init__(self, session_repository: ServiceSessionRepository):
        super().__init__(session_repository)

    async def execute(
        self, session_id: SessionId, duration: int, notes: str | None = None
    ) -> ServiceSessionEntity:
        """Complete a service session."""
        session = await self._get_entity_or_raise(session_id, "Session")
        session.complete(duration, notes)
        return await self._save_and_publish_events(session)


class CancelServiceSessionUseCase(BaseUseCase[ServiceSessionEntity, SessionId]):
    """Use case for cancelling a service session."""

    def __init__(self, session_repository: ServiceSessionRepository):
        super().__init__(session_repository)

    async def execute(
        self, session_id: SessionId, reason: str
    ) -> ServiceSessionEntity:
        """Cancel a service session."""
        session = await self._get_entity_or_raise(session_id, "Session")
        session.cancel(reason)
        return await self._save_and_publish_events(session)


class RescheduleServiceSessionUseCase(BaseUseCase[ServiceSessionEntity, SessionId]):
    """Use case for rescheduling a service session."""

    def __init__(self, session_repository: ServiceSessionRepository):
        super().__init__(session_repository)

    async def execute(
        self, session_id: SessionId, new_scheduled_at: datetime
    ) -> ServiceSessionEntity:
        """Reschedule a service session."""
        session = await self._get_entity_or_raise(session_id, "Session")
        session.reschedule(new_scheduled_at)
        return await self._save_and_publish_events(session)


class MarkNoShowServiceSessionUseCase(BaseUseCase[ServiceSessionEntity, SessionId]):
    """Use case for marking a service session as no-show."""

    def __init__(self, session_repository: ServiceSessionRepository):
        super().__init__(session_repository)

    async def execute(self, session_id: SessionId) -> ServiceSessionEntity:
        """Mark a service session as no-show."""
        session = await self._get_entity_or_raise(session_id, "Session")
        session.mark_no_show()
        return await self._save_and_publish_events(session)


# =============================================================================
# UPDATE USE CASES
# =============================================================================


class UpdateServiceSessionUseCase(BaseUseCase[ServiceSessionEntity, SessionId]):
    """Use case for updating service session information."""

    def __init__(self, session_repository: ServiceSessionRepository):
        super().__init__(session_repository)

    async def execute(
        self,
        session_id: SessionId,
        location: str | None = None,
        notes: str | None = None,
    ) -> ServiceSessionEntity:
        """Update service session information."""
        session = await self._get_entity_or_raise(session_id, "Session")

        if location is not None:
            session.update_location(location)
        if notes is not None:
            session.update_notes(notes)

        return await self._save_and_publish_events(session)


class UpdateServiceSessionFeedbackUseCase(BaseUseCase[ServiceSessionEntity, SessionId]):
    """Use case for updating service session feedback."""

    def __init__(self, session_repository: ServiceSessionRepository):
        super().__init__(session_repository)

    async def execute(
        self, session_id: SessionId, feedback: str
    ) -> ServiceSessionEntity:
        """Update service session feedback."""
        session = await self._get_entity_or_raise(session_id, "Session")
        session.update_feedback(feedback)
        return await self._save_and_publish_events(session)


# =============================================================================
# QUERY USE CASE
# =============================================================================


class GetServiceSessionUseCase(BaseUseCase[ServiceSessionEntity, SessionId]):
    """Use case for retrieving service sessions."""

    def __init__(self, session_repository: ServiceSessionRepository):
        super().__init__(session_repository)
        self.session_repository = session_repository

    async def execute(self, session_id: SessionId) -> ServiceSessionEntity | None:
        """Get session by ID."""
        return await self.repository.get_by_id(session_id)

    async def execute_by_person(
        self, tenant_id: TenantId, person_id: PersonId
    ) -> list[ServiceSessionEntity]:
        """Get all sessions for a person."""
        return await self.session_repository.get_by_person_id(tenant_id, person_id)

    async def execute_by_provider(
        self, tenant_id: TenantId, provider_id: PersonId
    ) -> list[ServiceSessionEntity]:
        """Get all sessions for a provider."""
        return await self.session_repository.get_by_provider_id(tenant_id, provider_id)

    async def execute_by_service(
        self, tenant_id: TenantId, service_id: ServiceId
    ) -> list[ServiceSessionEntity]:
        """Get all sessions for a service."""
        return await self.session_repository.get_by_service_id(tenant_id, service_id)
