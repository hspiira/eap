"""
Service Session Use Cases

Application services for Service Session aggregate operations.
Refactored to use base use case classes.
"""

from datetime import datetime

from app.application.use_cases.base import BaseUseCase
from app.domain.entities.service_session import ServiceSessionEntity
from app.domain.enums import (
    ClientType,
    SessionCategory,
    SessionClinicalStatus,
    SessionStatus,
    SessionType,
)
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


# Lifecycle / single-method commands dispatched via TransitionUseCase + ServiceSessionTransition.


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
        session_type: SessionType | None = None,
        category: SessionCategory | None = None,
        rate_ugx: int | None = None,
        issue_topic: str | None = None,
        diagnosis_type_id: str | None = None,
        diagnosis_id: str | None = None,
        approved_by: str | None = None,
        session_number: int | None = None,
        partner_name: str | None = None,
        partner_relationship: str | None = None,
        headcount: int | None = None,
        client_type: ClientType | None = None,
        clinical_outcome: SessionClinicalStatus | None = None,
    ) -> ServiceSessionEntity:
        """Create a new service session."""
        session = ServiceSessionEntity(
            id=session_id,
            tenant_id=tenant_id,
            service_id=service_id,
            provider_id=provider_id,
            person_id=person_id,
            scheduled_at=scheduled_at,
            status=SessionStatus.SCHEDULED,
            created_at=utc_now(),
            updated_at=utc_now(),
            reschedule_count=0,
            location=location,
            session_type=session_type,
            category=category,
            rate_ugx=rate_ugx,
            issue_topic=issue_topic,
            diagnosis_type_id=diagnosis_type_id,
            diagnosis_id=diagnosis_id,
            approved_by=approved_by,
            session_number=session_number,
            partner_name=partner_name,
            partner_relationship=partner_relationship,
            headcount=headcount,
            client_type=client_type,
            clinical_outcome=clinical_outcome,
        )

        return await self._save_and_publish_events(session)


class UpdateServiceSessionUseCase(BaseUseCase[ServiceSessionEntity, SessionId]):
    """Composite update for ServiceSession."""

    async def execute(
        self,
        session_id: SessionId,
        location: str | None = None,
        notes: str | None = None,
        session_type: SessionType | None = None,
        category: SessionCategory | None = None,
        headcount: int | None = None,
        rate_ugx: int | None = None,
        issue_topic: str | None = None,
        diagnosis_type_id: str | None = None,
        diagnosis_id: str | None = None,
        approved_by: str | None = None,
        partner_name: str | None = None,
        partner_relationship: str | None = None,
        client_type: ClientType | None = None,
        clinical_outcome: SessionClinicalStatus | None = None,
    ) -> ServiceSessionEntity:
        session = await self._get_entity_or_raise(session_id, "Session")
        if location is not None:
            session.update_location(location)
        if notes is not None:
            session.update_notes(notes)
        if session_type is not None:
            session.set_session_type(session_type)
        if category is not None:
            session.set_category(category, headcount=headcount)
        elif headcount is not None:
            session.headcount = headcount
        if any(v is not None for v in (issue_topic, diagnosis_type_id, diagnosis_id, approved_by, rate_ugx)):
            session.set_clinical_details(
                issue_topic=issue_topic,
                diagnosis_type_id=diagnosis_type_id,
                diagnosis_id=diagnosis_id,
                approved_by=approved_by,
                rate_ugx=rate_ugx,
            )
        if partner_name is not None or partner_relationship is not None:
            session.set_partner_details(partner_name, partner_relationship)
        if client_type is not None:
            session.set_client_type(client_type)
        if clinical_outcome is not None:
            session.set_clinical_outcome(clinical_outcome)
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
