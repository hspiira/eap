"""
Service Session Repository Implementation

SQLAlchemy implementation of ServiceSessionRepository interface.
Uses TenantScopedRepositoryImpl base class to eliminate boilerplate.
"""

from typing import Any, Sequence

from sqlalchemy import select

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
from app.infrastructure.mappers.service_session_mapper import ServiceSessionMapper
from app.infrastructure.models.service_session_model import ServiceSessionModel
from app.infrastructure.repositories.base import TenantScopedRepositoryImpl


class ServiceSessionRepositoryImpl(TenantScopedRepositoryImpl[ServiceSessionEntity, ServiceSessionModel, SessionId], ServiceSessionRepository):
    """
    SQLAlchemy implementation of ServiceSessionRepository.

    Inherits common CRUD operations from TenantScopedRepositoryImpl.
    Only implements domain-specific queries.
    """

    model_class = ServiceSessionModel
    id_column = "id"

    def _to_entity(self, model: ServiceSessionModel) -> ServiceSessionEntity:
        """Convert model to entity."""
        return ServiceSessionMapper.to_entity(model)

    def _to_model(self, entity: ServiceSessionEntity) -> ServiceSessionModel:
        """Convert entity to model."""
        return ServiceSessionMapper.to_model(entity)

    def _get_id_value(self, entity_id: SessionId) -> Any:
        """Extract raw ID value."""
        return entity_id.value

    # Domain-specific queries (not in base class)

    async def get_by_person_id(
        self, tenant_id: TenantId, person_id: PersonId
    ) -> list[ServiceSessionEntity]:
        """Get all sessions for a person within tenant, excluding soft-deleted."""
        stmt = select(ServiceSessionModel).where(
            ServiceSessionModel.tenant_id == tenant_id.value,
            ServiceSessionModel.person_id == person_id.value,
            ServiceSessionModel.deleted_at.is_(None),
        )
        result = await self.session.execute(stmt)
        models = result.scalars().all()

        return [self._to_entity(model) for model in models]

    async def get_by_provider_id(
        self, tenant_id: TenantId, provider_id: PersonId
    ) -> list[ServiceSessionEntity]:
        """Get all sessions for a provider within tenant, excluding soft-deleted."""
        stmt = select(ServiceSessionModel).where(
            ServiceSessionModel.tenant_id == tenant_id.value,
            ServiceSessionModel.provider_id == provider_id.value,
            ServiceSessionModel.deleted_at.is_(None),
        )
        result = await self.session.execute(stmt)
        models = result.scalars().all()

        return [self._to_entity(model) for model in models]

    async def get_by_service_id(
        self, tenant_id: TenantId, service_id: ServiceId
    ) -> list[ServiceSessionEntity]:
        """Get all sessions for a service within tenant, excluding soft-deleted."""
        stmt = select(ServiceSessionModel).where(
            ServiceSessionModel.tenant_id == tenant_id.value,
            ServiceSessionModel.service_id == service_id.value,
            ServiceSessionModel.deleted_at.is_(None),
        )
        result = await self.session.execute(stmt)
        models = result.scalars().all()

        return [self._to_entity(model) for model in models]

    async def list_all(
        self,
        tenant_id: TenantId,
        person_id: PersonId | None = None,
        provider_id: PersonId | None = None,
        service_id: ServiceId | None = None,
        status: SessionStatus | None = None,
        limit: int = 100,
        offset: int = 0,
        sort_by: str = "scheduled_at",
        sort_desc: bool = True,
    ) -> Sequence[ServiceSessionEntity]:
        """List sessions with filtering, searching, and pagination."""
        # Build filters dict for base class
        filters: dict[str, Any] = {}
        if person_id:
            filters["person_id"] = person_id.value
        if provider_id:
            filters["provider_id"] = provider_id.value
        if service_id:
            filters["service_id"] = service_id.value
        if status:
            filters["status"] = status

        return await self._query_all(
            tenant_id=tenant_id.value,
            limit=limit,
            offset=offset,
            sort_by=sort_by,
            sort_desc=sort_desc,
            filters=filters,
            search=None,
            search_fields=None,
        )

    async def count(
        self,
        tenant_id: TenantId,
        person_id: PersonId | None = None,
        provider_id: PersonId | None = None,
        service_id: ServiceId | None = None,
        status: SessionStatus | None = None,
    ) -> int:
        """Count sessions matching filters."""
        filters: dict[str, Any] = {}
        if person_id:
            filters["person_id"] = person_id.value
        if provider_id:
            filters["provider_id"] = provider_id.value
        if service_id:
            filters["service_id"] = service_id.value
        if status:
            filters["status"] = status

        return await self._count_all(
            tenant_id=tenant_id.value,
            filters=filters,
            search=None,
            search_fields=None,
        )
