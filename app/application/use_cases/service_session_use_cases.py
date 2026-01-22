"""
Service Session Use Cases

Application services for Service Session aggregate operations.
"""

from datetime import datetime

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


class CreateServiceSessionUseCase:
    """Use case for creating a new service session."""

    def __init__(self, session_repository: ServiceSessionRepository):
        self.session_repository = session_repository

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
        """
        Create a new service session.

        Args:
            session_id: Unique session identifier
            tenant_id: Tenant identifier
            service_id: Service identifier
            provider_id: Provider (person) identifier
            person_id: Person identifier
            scheduled_at: Scheduled date and time
            location: Session location (optional)

        Returns:
            Created ServiceSessionEntity
        """
        # Create session entity
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

        # Save session
        await self.session_repository.save(session)

        return session


class CompleteServiceSessionUseCase:
    """Use case for completing a service session."""

    def __init__(self, session_repository: ServiceSessionRepository):
        self.session_repository = session_repository

    async def execute(
        self, session_id: SessionId, duration: int, notes: str | None = None
    ) -> ServiceSessionEntity:
        """
        Complete a service session.

        Args:
            session_id: Session identifier
            duration: Session duration in minutes
            notes: Session notes

        Returns:
            Completed ServiceSessionEntity

        Raises:
            ValueError: If session not found
            DomainError: If completion is invalid
        """
        session = await self.session_repository.get_by_id(session_id)
        if not session:
            raise ValueError(f"Session {session_id.value} not found")

        session.complete(duration, notes)
        await self.session_repository.save(session)

        return session


class CancelServiceSessionUseCase:
    """Use case for cancelling a service session."""

    def __init__(self, session_repository: ServiceSessionRepository):
        self.session_repository = session_repository

    async def execute(
        self, session_id: SessionId, reason: str
    ) -> ServiceSessionEntity:
        """
        Cancel a service session.

        Args:
            session_id: Session identifier
            reason: Cancellation reason

        Returns:
            Cancelled ServiceSessionEntity

        Raises:
            ValueError: If session not found
            DomainError: If cancellation is invalid
        """
        session = await self.session_repository.get_by_id(session_id)
        if not session:
            raise ValueError(f"Session {session_id.value} not found")

        session.cancel(reason)
        await self.session_repository.save(session)

        return session


class RescheduleServiceSessionUseCase:
    """Use case for rescheduling a service session."""

    def __init__(self, session_repository: ServiceSessionRepository):
        self.session_repository = session_repository

    async def execute(
        self, session_id: SessionId, new_scheduled_at: datetime
    ) -> ServiceSessionEntity:
        """
        Reschedule a service session.

        Args:
            session_id: Session identifier
            new_scheduled_at: New scheduled date and time

        Returns:
            Rescheduled ServiceSessionEntity

        Raises:
            ValueError: If session not found
            DomainError: If rescheduling is invalid
        """
        session = await self.session_repository.get_by_id(session_id)
        if not session:
            raise ValueError(f"Session {session_id.value} not found")

        session.reschedule(new_scheduled_at)
        await self.session_repository.save(session)

        return session


class MarkNoShowServiceSessionUseCase:
    """Use case for marking a service session as no-show."""

    def __init__(self, session_repository: ServiceSessionRepository):
        self.session_repository = session_repository

    async def execute(self, session_id: SessionId) -> ServiceSessionEntity:
        """
        Mark a service session as no-show.

        Args:
            session_id: Session identifier

        Returns:
            Updated ServiceSessionEntity

        Raises:
            ValueError: If session not found
            DomainError: If marking as no-show is invalid
        """
        session = await self.session_repository.get_by_id(session_id)
        if not session:
            raise ValueError(f"Session {session_id.value} not found")

        session.mark_no_show()
        await self.session_repository.save(session)

        return session


class UpdateServiceSessionUseCase:
    """Use case for updating service session information."""

    def __init__(self, session_repository: ServiceSessionRepository):
        self.session_repository = session_repository

    async def execute(
        self,
        session_id: SessionId,
        location: str | None = None,
        notes: str | None = None,
    ) -> ServiceSessionEntity:
        """
        Update service session information.

        Args:
            session_id: Session identifier
            location: Session location (optional)
            notes: Session notes (optional)

        Returns:
            Updated ServiceSessionEntity

        Raises:
            ValueError: If session not found
            DomainError: If update is invalid
        """
        session = await self.session_repository.get_by_id(session_id)
        if not session:
            raise ValueError(f"Session {session_id.value} not found")

        if location is not None:
            session.update_location(location)
        if notes is not None:
            session.update_notes(notes)

        await self.session_repository.save(session)

        return session


class UpdateServiceSessionFeedbackUseCase:
    """Use case for updating service session feedback."""

    def __init__(self, session_repository: ServiceSessionRepository):
        self.session_repository = session_repository

    async def execute(
        self, session_id: SessionId, feedback: str
    ) -> ServiceSessionEntity:
        """
        Update service session feedback.

        Args:
            session_id: Session identifier
            feedback: Session feedback

        Returns:
            Updated ServiceSessionEntity

        Raises:
            ValueError: If session not found
            DomainError: If update is invalid
        """
        session = await self.session_repository.get_by_id(session_id)
        if not session:
            raise ValueError(f"Session {session_id.value} not found")

        session.update_feedback(feedback)
        await self.session_repository.save(session)

        return session


class ArchiveServiceSessionUseCase:
    """Use case for archiving a service session."""

    def __init__(self, session_repository: ServiceSessionRepository):
        self.session_repository = session_repository

    async def execute(self, session_id: SessionId) -> ServiceSessionEntity:
        """
        Archive a service session.

        Args:
            session_id: Session identifier

        Returns:
            Archived ServiceSessionEntity

        Raises:
            ValueError: If session not found
            DomainError: If archive is invalid
        """
        session = await self.session_repository.get_by_id(session_id)
        if not session:
            raise ValueError(f"Session {session_id.value} not found")

        session.archive()
        await self.session_repository.save(session)

        return session


class RestoreServiceSessionUseCase:
    """Use case for restoring a service session."""

    def __init__(self, session_repository: ServiceSessionRepository):
        self.session_repository = session_repository

    async def execute(self, session_id: SessionId) -> ServiceSessionEntity:
        """
        Restore an archived service session.

        Args:
            session_id: Session identifier

        Returns:
            Restored ServiceSessionEntity

        Raises:
            ValueError: If session not found
            DomainError: If restore is invalid
        """
        session = await self.session_repository.get_by_id(session_id)
        if not session:
            raise ValueError(f"Session {session_id.value} not found")

        session.restore()
        await self.session_repository.save(session)

        return session


class GetServiceSessionUseCase:
    """Use case for retrieving service sessions."""

    def __init__(self, session_repository: ServiceSessionRepository):
        self.session_repository = session_repository

    async def execute(self, session_id: SessionId) -> ServiceSessionEntity | None:
        """
        Get session by ID.

        Args:
            session_id: Session identifier

        Returns:
            ServiceSessionEntity if found, None otherwise
        """
        return await self.session_repository.get_by_id(session_id)

    async def execute_by_person(
        self, tenant_id: TenantId, person_id: PersonId
    ) -> list[ServiceSessionEntity]:
        """
        Get all sessions for a person.

        Args:
            tenant_id: Tenant identifier
            person_id: Person identifier

        Returns:
            List of ServiceSessionEntity for the person
        """
        return await self.session_repository.get_by_person_id(tenant_id, person_id)

    async def execute_by_provider(
        self, tenant_id: TenantId, provider_id: PersonId
    ) -> list[ServiceSessionEntity]:
        """
        Get all sessions for a provider.

        Args:
            tenant_id: Tenant identifier
            provider_id: Provider identifier

        Returns:
            List of ServiceSessionEntity for the provider
        """
        return await self.session_repository.get_by_provider_id(tenant_id, provider_id)

    async def execute_by_service(
        self, tenant_id: TenantId, service_id: ServiceId
    ) -> list[ServiceSessionEntity]:
        """
        Get all sessions for a service.

        Args:
            tenant_id: Tenant identifier
            service_id: Service identifier

        Returns:
            List of ServiceSessionEntity for the service
        """
        return await self.session_repository.get_by_service_id(tenant_id, service_id)
