"""
Service Session Repository Implementation

SQLAlchemy implementation of ServiceSessionRepository interface.
"""

from typing import Sequence

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

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
from app.shared.utils.datetime import utc_now


class ServiceSessionRepositoryImpl(ServiceSessionRepository):
    """
    SQLAlchemy implementation of ServiceSessionRepository.

    Handles data access for Service Session aggregate.
    Uses mapper to convert between entity and model.
    """

    def __init__(self, session: AsyncSession) -> None:
        """
        Initialize repository with database session.

        Args:
            session: SQLAlchemy async database session
        """
        self.session = session

    async def get_by_id(self, session_id: SessionId) -> ServiceSessionEntity | None:
        """Get session by ID, excluding soft-deleted sessions."""
        stmt = select(ServiceSessionModel).where(
            ServiceSessionModel.id == session_id.value,
            ServiceSessionModel.deleted_at.is_(None),
        )
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()

        if not model:
            return None

        return ServiceSessionMapper.to_entity(model)

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

        return [ServiceSessionMapper.to_entity(model) for model in models]

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

        return [ServiceSessionMapper.to_entity(model) for model in models]

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

        return [ServiceSessionMapper.to_entity(model) for model in models]

    async def save(self, session: ServiceSessionEntity) -> None:
        """
        Save session aggregate atomically.

        Uses merge to handle both insert and update.
        """
        model = ServiceSessionMapper.to_model(session)
        await self.session.merge(model)
        # Note: commit is typically handled by the application service/unit of work

    async def delete(self, session_id: SessionId) -> None:
        """
        Soft delete session.

        In practice, this is usually done by calling session.archive()
        and then save(), but this method provides explicit soft delete.
        """
        stmt = select(ServiceSessionModel).where(
            ServiceSessionModel.id == session_id.value,
            ServiceSessionModel.deleted_at.is_(None),
        )
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()

        if model:
            now = utc_now()
            model.deleted_at = now
            model.updated_at = now
            await self.session.merge(model)

    async def exists(self, session_id: SessionId) -> bool:
        """Check if session exists (not soft-deleted)."""
        stmt = select(ServiceSessionModel.id).where(
            ServiceSessionModel.id == session_id.value,
            ServiceSessionModel.deleted_at.is_(None),
        )
        result = await self.session.execute(stmt)
        return bool(result.scalar())

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
        stmt = select(ServiceSessionModel).where(
            ServiceSessionModel.tenant_id == tenant_id.value,
            ServiceSessionModel.deleted_at.is_(None),
        )

        # Apply filters
        if person_id:
            stmt = stmt.where(ServiceSessionModel.person_id == person_id.value)
        if provider_id:
            stmt = stmt.where(ServiceSessionModel.provider_id == provider_id.value)
        if service_id:
            stmt = stmt.where(ServiceSessionModel.service_id == service_id.value)
        if status:
            stmt = stmt.where(ServiceSessionModel.status == status)

        # Apply sorting
        sort_column = getattr(
            ServiceSessionModel, sort_by, ServiceSessionModel.scheduled_at
        )
        if sort_desc:
            stmt = stmt.order_by(sort_column.desc())
        else:
            stmt = stmt.order_by(sort_column.asc())

        # Apply pagination
        stmt = stmt.limit(limit).offset(offset)

        result = await self.session.execute(stmt)
        models = result.scalars().all()

        return [ServiceSessionMapper.to_entity(model) for model in models]

    async def count(
        self,
        tenant_id: TenantId,
        person_id: PersonId | None = None,
        provider_id: PersonId | None = None,
        service_id: ServiceId | None = None,
        status: SessionStatus | None = None,
    ) -> int:
        """Count sessions matching filters."""
        stmt = select(func.count(ServiceSessionModel.id)).where(
            ServiceSessionModel.tenant_id == tenant_id.value,
            ServiceSessionModel.deleted_at.is_(None),
        )

        # Apply filters
        if person_id:
            stmt = stmt.where(ServiceSessionModel.person_id == person_id.value)
        if provider_id:
            stmt = stmt.where(ServiceSessionModel.provider_id == provider_id.value)
        if service_id:
            stmt = stmt.where(ServiceSessionModel.service_id == service_id.value)
        if status:
            stmt = stmt.where(ServiceSessionModel.status == status)

        result = await self.session.execute(stmt)
        return int(result.scalar() or 0)
