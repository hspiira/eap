"""
Base Repository Implementation

Generic base class that eliminates repetitive repository patterns.
"""

from abc import ABC, abstractmethod
from collections.abc import Sequence
from typing import Generic, TypeVar, Any

from sqlalchemy import func, select, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.shared.utils.datetime import utc_now

# Type variables
TEntity = TypeVar("TEntity")
TModel = TypeVar("TModel")
TId = TypeVar("TId")


class BaseRepositoryImpl(ABC, Generic[TEntity, TModel, TId]):
    """
    Generic base repository implementation.
    
    Provides common CRUD operations that are identical across repositories.
    Subclasses only need to define:
    - model_class: The SQLAlchemy model class
    - mapper: The mapper class with to_entity/to_model methods
    - id_column: The name of the ID column
    """
    
    model_class: type[TModel]
    id_column: str = "id"
    
    def __init__(self, session: AsyncSession) -> None:
        """Initialize repository with database session."""
        self.session = session
    
    @abstractmethod
    def _to_entity(self, model: TModel) -> TEntity:
        """Convert model to entity. Override in subclass."""
        pass
    
    @abstractmethod
    def _to_model(self, entity: TEntity) -> TModel:
        """Convert entity to model. Override in subclass."""
        pass
    
    @abstractmethod
    def _get_id_value(self, entity_id: TId) -> Any:
        """Extract the raw ID value from the typed ID. Override in subclass."""
        pass
    
    async def get_by_id(self, entity_id: TId) -> TEntity | None:
        """Get entity by ID, excluding soft-deleted records."""
        id_value = self._get_id_value(entity_id)
        id_col = getattr(self.model_class, self.id_column)
        
        stmt = select(self.model_class).where(
            id_col == id_value,
        )
        
        # Add soft-delete filter if model has deleted_at
        if hasattr(self.model_class, 'deleted_at'):
            stmt = stmt.where(self.model_class.deleted_at.is_(None))
        
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        
        if not model:
            return None
        
        return self._to_entity(model)
    
    async def save(self, entity: TEntity) -> None:
        """Save entity (insert or update)."""
        model = self._to_model(entity)
        await self.session.merge(model)
    
    async def delete(self, entity_id: TId) -> None:
        """Soft delete entity."""
        id_value = self._get_id_value(entity_id)
        id_col = getattr(self.model_class, self.id_column)
        
        stmt = select(self.model_class).where(id_col == id_value)
        
        if hasattr(self.model_class, 'deleted_at'):
            stmt = stmt.where(self.model_class.deleted_at.is_(None))
        
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        
        if model and hasattr(model, 'deleted_at'):
            now = utc_now()
            model.deleted_at = now
            if hasattr(model, 'updated_at'):
                model.updated_at = now
            await self.session.merge(model)
    
    async def exists(self, entity_id: TId) -> bool:
        """Check if entity exists (not soft-deleted)."""
        from sqlalchemy import exists as sql_exists
        
        id_value = self._get_id_value(entity_id)
        id_col = getattr(self.model_class, self.id_column)
        
        conditions = [id_col == id_value]
        if hasattr(self.model_class, 'deleted_at'):
            conditions.append(self.model_class.deleted_at.is_(None))
        
        stmt = sql_exists().where(*conditions).select()
        result = await self.session.execute(stmt)
        return result.scalar() or False


class TenantScopedRepositoryImpl(BaseRepositoryImpl[TEntity, TModel, TId]):
    """
    Base repository for tenant-scoped entities.
    
    Provides helper methods for tenant-scoped queries.
    Subclasses implement domain-specific list_all/count methods
    that can use these helpers internally.
    """
    
    async def get_by_id_in_tenant(
        self,
        entity_id: TId,
        tenant_id: Any,
    ) -> TEntity | None:
        """Get entity by ID within a specific tenant."""
        id_value = self._get_id_value(entity_id)
        id_col = getattr(self.model_class, self.id_column)
        
        stmt = select(self.model_class).where(
            id_col == id_value,
            self.model_class.tenant_id == tenant_id,
        )
        
        if hasattr(self.model_class, 'deleted_at'):
            stmt = stmt.where(self.model_class.deleted_at.is_(None))
        
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        
        if not model:
            return None
        
        return self._to_entity(model)
    
    async def _query_all(
        self,
        tenant_id: Any,
        limit: int = 100,
        offset: int = 0,
        sort_by: str = "created_at",
        sort_desc: bool = True,
        filters: dict[str, Any] | None = None,
        search: str | None = None,
        search_fields: list[str] | None = None,
        extra_conditions: Sequence[Any] | None = None,
    ) -> Sequence[TEntity]:
        """
        Internal helper to query entities with filtering, searching, and pagination.

        Subclasses should call this from their domain-specific list_all methods.

        Args:
            tenant_id: Tenant identifier (raw value)
            limit: Maximum number of results
            offset: Number of results to skip
            sort_by: Field to sort by
            sort_desc: Sort in descending order
            filters: Dictionary of field=value filters
            search: Search string
            search_fields: Fields to search in
            extra_conditions: Pre-built SQLAlchemy conditions for filters that are
                not simple column equality (e.g. nullable-timestamp flags). Pass
                these rather than filtering the returned page in Python — post-
                filtering a paginated result silently drops rows and desynchronises
                the page from its count.
        """
        stmt = select(self.model_class).where(
            self.model_class.tenant_id == tenant_id,
        )

        if hasattr(self.model_class, 'deleted_at'):
            stmt = stmt.where(self.model_class.deleted_at.is_(None))

        # Apply filters
        if filters:
            for key, value in filters.items():
                if value is not None and hasattr(self.model_class, key):
                    stmt = stmt.where(getattr(self.model_class, key) == value)

        for condition in extra_conditions or ():
            stmt = stmt.where(condition)

        # Apply search
        if search and search_fields:
            search_conditions = []
            for field in search_fields:
                if hasattr(self.model_class, field):
                    search_conditions.append(
                        getattr(self.model_class, field).ilike(f"%{search}%")
                    )
            if search_conditions:
                stmt = stmt.where(or_(*search_conditions))
        
        # Apply sorting
        if hasattr(self.model_class, sort_by):
            sort_col = getattr(self.model_class, sort_by)
            stmt = stmt.order_by(sort_col.desc() if sort_desc else sort_col.asc())
        
        # Apply pagination
        stmt = stmt.limit(limit).offset(offset)
        
        result = await self.session.execute(stmt)
        models = result.scalars().all()
        
        return [self._to_entity(model) for model in models]
    
    async def _count_all(
        self,
        tenant_id: Any,
        filters: dict[str, Any] | None = None,
        search: str | None = None,
        search_fields: list[str] | None = None,
    ) -> int:
        """
        Internal helper to count entities in tenant matching filters.
        
        Subclasses should call this from their domain-specific count methods.
        """
        id_col = getattr(self.model_class, self.id_column)
        stmt = select(func.count(id_col)).where(
            self.model_class.tenant_id == tenant_id,
        )
        
        if hasattr(self.model_class, 'deleted_at'):
            stmt = stmt.where(self.model_class.deleted_at.is_(None))
        
        if filters:
            for key, value in filters.items():
                if value is not None and hasattr(self.model_class, key):
                    stmt = stmt.where(getattr(self.model_class, key) == value)
        
        if search and search_fields:
            search_conditions = []
            for field in search_fields:
                if hasattr(self.model_class, field):
                    search_conditions.append(
                        getattr(self.model_class, field).ilike(f"%{search}%")
                    )
            if search_conditions:
                stmt = stmt.where(or_(*search_conditions))
        
        result = await self.session.execute(stmt)
        return int(result.scalar() or 0)
