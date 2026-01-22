"""
KPI Repository Implementation

SQLAlchemy implementation of KPI repository interfaces.
"""

from typing import Sequence

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.kpi import KPIEntity, KPIAssignmentEntity
from app.domain.enums import KPICategory
from app.domain.repositories.kpi_repository import (
    KPIAssignmentRepository,
    KPIRepository,
)
from app.domain.value_objects.core import KPIId, KPIAssignmentId, TenantId
from app.infrastructure.mappers.kpi_mapper import (
    KPIAssignmentMapper,
    KPIMapper,
)
from app.infrastructure.models.kpi_model import (
    KPIAssignmentModel,
    KPIModel,
)
from app.shared.utils.datetime import utc_now


class KPIRepositoryImpl(KPIRepository):
    """
    SQLAlchemy implementation of KPIRepository.

    Handles data access for KPI aggregate.
    Uses mapper to convert between entity and model.
    """

    def __init__(self, session: AsyncSession) -> None:
        """
        Initialize repository with database session.

        Args:
            session: SQLAlchemy async database session
        """
        self.session = session

    async def get_by_id(self, kpi_id: KPIId) -> KPIEntity | None:
        """Get KPI by ID, excluding soft-deleted KPIs."""
        stmt = select(KPIModel).where(
            KPIModel.id == kpi_id.value,
            KPIModel.deleted_at.is_(None),
        )
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()

        if not model:
            return None
        return KPIMapper.to_entity(model)

    async def get_by_name(
        self, name: str, tenant_id: TenantId
    ) -> KPIEntity | None:
        """Get KPI by name within tenant, excluding soft-deleted KPIs."""
        stmt = select(KPIModel).where(
            KPIModel.name == name,
            KPIModel.tenant_id == tenant_id.value,
            KPIModel.deleted_at.is_(None),
        )
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        if not model:
            return None
        return KPIMapper.to_entity(model)

    async def list_all(
        self,
        tenant_id: TenantId,
        category: KPICategory | None = None,
        is_active: bool | None = None,
        search: str | None = None,
        limit: int = 100,
        offset: int = 0,
        sort_by: str = "created_at",
        sort_desc: bool = True,
    ) -> Sequence[KPIEntity]:
        """List KPIs with filtering, searching, and pagination."""
        stmt = select(KPIModel).where(
            KPIModel.tenant_id == tenant_id.value,
            KPIModel.deleted_at.is_(None),
        )

        # Apply filters
        if category:
            stmt = stmt.where(KPIModel.category == category)
        if is_active is not None:
            stmt = stmt.where(KPIModel.is_active == is_active)
        if search:
            search_pattern = f"%{search.lower()}%"
            stmt = stmt.where(
                or_(
                    KPIModel.name.ilike(search_pattern),
                    KPIModel.description.ilike(search_pattern),
                )
            )

        # Apply sorting
        sort_column = getattr(KPIModel, sort_by, KPIModel.created_at)
        if sort_desc:
            stmt = stmt.order_by(sort_column.desc())
        else:
            stmt = stmt.order_by(sort_column.asc())

        # Apply pagination
        stmt = stmt.limit(limit).offset(offset)

        result = await self.session.execute(stmt)
        models = result.scalars().all()

        return [KPIMapper.to_entity(model) for model in models]

    async def count(
        self,
        tenant_id: TenantId,
        category: KPICategory | None = None,
        is_active: bool | None = None,
        search: str | None = None,
    ) -> int:
        """Count KPIs matching filters."""
        stmt = select(func.count(KPIModel.id)).where(
            KPIModel.tenant_id == tenant_id.value,
            KPIModel.deleted_at.is_(None),
        )

        # Apply filters
        if category:
            stmt = stmt.where(KPIModel.category == category)
        if is_active is not None:
            stmt = stmt.where(KPIModel.is_active == is_active)
        if search:
            search_pattern = f"%{search.lower()}%"
            stmt = stmt.where(
                or_(
                    KPIModel.name.ilike(search_pattern),
                    KPIModel.description.ilike(search_pattern),
                )
            )

        result = await self.session.execute(stmt)
        return int(result.scalar() or 0)

    async def save(self, kpi: KPIEntity) -> None:
        """
        Save KPI aggregate atomically.

        Uses merge to handle both insert and update.
        """
        model = KPIMapper.to_model(kpi)
        await self.session.merge(model)

    async def delete(self, kpi_id: KPIId) -> None:
        """
        Soft delete KPI.
        """
        stmt = select(KPIModel).where(
            KPIModel.id == kpi_id.value,
            KPIModel.deleted_at.is_(None),
        )
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()

        if model:
            now = utc_now()
            model.deleted_at = now
            model.updated_at = now
            await self.session.merge(model)

    async def exists(self, kpi_id: KPIId) -> bool:
        """Check if KPI exists (not soft-deleted)."""
        from sqlalchemy import exists as sql_exists

        stmt = sql_exists().where(
            KPIModel.id == kpi_id.value,
            KPIModel.deleted_at.is_(None),
        ).select()
        result = await self.session.execute(stmt)
        return bool(result.scalar())


class KPIAssignmentRepositoryImpl(KPIAssignmentRepository):
    """
    SQLAlchemy implementation of KPIAssignmentRepository.

    Handles data access for KPI Assignment aggregate.
    Uses mapper to convert between entity and model.
    """

    def __init__(self, session: AsyncSession) -> None:
        """
        Initialize repository with database session.

        Args:
            session: SQLAlchemy async database session
        """
        self.session = session

    async def get_by_id(
        self, assignment_id: KPIAssignmentId
    ) -> KPIAssignmentEntity | None:
        """Get assignment by ID, excluding soft-deleted assignments."""
        stmt = select(KPIAssignmentModel).where(
            KPIAssignmentModel.id == assignment_id.value,
            KPIAssignmentModel.deleted_at.is_(None),
        )
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()

        if not model:
            return None
        return KPIAssignmentMapper.to_entity(model)

    async def get_by_kpi_id(
        self, kpi_id: KPIId, tenant_id: TenantId
    ) -> Sequence[KPIAssignmentEntity]:
        """Get all assignments for a KPI."""
        stmt = select(KPIAssignmentModel).where(
            KPIAssignmentModel.kpi_id == kpi_id.value,
            KPIAssignmentModel.tenant_id == tenant_id.value,
            KPIAssignmentModel.deleted_at.is_(None),
        )
        result = await self.session.execute(stmt)
        models = result.scalars().all()

        return [KPIAssignmentMapper.to_entity(model) for model in models]

    async def get_by_client_id(
        self, client_id: str, tenant_id: TenantId
    ) -> Sequence[KPIAssignmentEntity]:
        """Get all assignments for a client."""
        stmt = select(KPIAssignmentModel).where(
            KPIAssignmentModel.client_id == client_id,
            KPIAssignmentModel.tenant_id == tenant_id.value,
            KPIAssignmentModel.deleted_at.is_(None),
        )
        result = await self.session.execute(stmt)
        models = result.scalars().all()

        return [KPIAssignmentMapper.to_entity(model) for model in models]

    async def get_by_contract_id(
        self, contract_id: str, tenant_id: TenantId
    ) -> Sequence[KPIAssignmentEntity]:
        """Get all assignments for a contract."""
        stmt = select(KPIAssignmentModel).where(
            KPIAssignmentModel.contract_id == contract_id,
            KPIAssignmentModel.tenant_id == tenant_id.value,
            KPIAssignmentModel.deleted_at.is_(None),
        )
        result = await self.session.execute(stmt)
        models = result.scalars().all()

        return [KPIAssignmentMapper.to_entity(model) for model in models]

    async def list_all(
        self,
        tenant_id: TenantId,
        kpi_id: KPIId | None = None,
        client_id: str | None = None,
        contract_id: str | None = None,
        is_active: bool | None = None,
        limit: int = 100,
        offset: int = 0,
        sort_by: str = "created_at",
        sort_desc: bool = True,
    ) -> Sequence[KPIAssignmentEntity]:
        """List assignments with filtering and pagination."""
        stmt = select(KPIAssignmentModel).where(
            KPIAssignmentModel.tenant_id == tenant_id.value,
            KPIAssignmentModel.deleted_at.is_(None),
        )

        # Apply filters
        if kpi_id:
            stmt = stmt.where(KPIAssignmentModel.kpi_id == kpi_id.value)
        if client_id:
            stmt = stmt.where(KPIAssignmentModel.client_id == client_id)
        if contract_id:
            stmt = stmt.where(KPIAssignmentModel.contract_id == contract_id)
        if is_active is not None:
            stmt = stmt.where(KPIAssignmentModel.is_active == is_active)

        # Apply sorting
        sort_column = getattr(
            KPIAssignmentModel, sort_by, KPIAssignmentModel.created_at
        )
        if sort_desc:
            stmt = stmt.order_by(sort_column.desc())
        else:
            stmt = stmt.order_by(sort_column.asc())

        # Apply pagination
        stmt = stmt.limit(limit).offset(offset)

        result = await self.session.execute(stmt)
        models = result.scalars().all()

        return [KPIAssignmentMapper.to_entity(model) for model in models]

    async def count(
        self,
        tenant_id: TenantId,
        kpi_id: KPIId | None = None,
        client_id: str | None = None,
        contract_id: str | None = None,
        is_active: bool | None = None,
    ) -> int:
        """Count assignments matching filters."""
        stmt = select(func.count(KPIAssignmentModel.id)).where(
            KPIAssignmentModel.tenant_id == tenant_id.value,
            KPIAssignmentModel.deleted_at.is_(None),
        )

        # Apply filters
        if kpi_id:
            stmt = stmt.where(KPIAssignmentModel.kpi_id == kpi_id.value)
        if client_id:
            stmt = stmt.where(KPIAssignmentModel.client_id == client_id)
        if contract_id:
            stmt = stmt.where(KPIAssignmentModel.contract_id == contract_id)
        if is_active is not None:
            stmt = stmt.where(KPIAssignmentModel.is_active == is_active)

        result = await self.session.execute(stmt)
        return int(result.scalar() or 0)

    async def save(self, assignment: KPIAssignmentEntity) -> None:
        """
        Save assignment aggregate atomically.

        Uses merge to handle both insert and update.
        """
        model = KPIAssignmentMapper.to_model(assignment)
        await self.session.merge(model)

    async def delete(self, assignment_id: KPIAssignmentId) -> None:
        """
        Soft delete assignment.
        """
        stmt = select(KPIAssignmentModel).where(
            KPIAssignmentModel.id == assignment_id.value,
            KPIAssignmentModel.deleted_at.is_(None),
        )
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()

        if model:
            now = utc_now()
            model.deleted_at = now
            model.updated_at = now
            await self.session.merge(model)

    async def exists(self, assignment_id: KPIAssignmentId) -> bool:
        """Check if assignment exists (not soft-deleted)."""
        from sqlalchemy import exists as sql_exists

        stmt = sql_exists().where(
            KPIAssignmentModel.id == assignment_id.value,
            KPIAssignmentModel.deleted_at.is_(None),
        ).select()
        result = await self.session.execute(stmt)
        return bool(result.scalar())
