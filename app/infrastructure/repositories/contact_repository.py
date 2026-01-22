"""Contact Repository Implementation - SQLAlchemy implementation."""

from typing import Any, Sequence

from sqlalchemy import select

from app.domain.entities.contact import ContactEntity
from app.domain.repositories.contact_repository import ContactRepository
from app.domain.value_objects.core import ContactId, TenantId
from app.infrastructure.mappers.contact_mapper import ContactMapper
from app.infrastructure.models.contact_model import ContactModel
from app.infrastructure.repositories.base import TenantScopedRepositoryImpl


class ContactRepositoryImpl(TenantScopedRepositoryImpl[ContactEntity, ContactModel, ContactId], ContactRepository):
    """
    SQLAlchemy implementation of ContactRepository.

    Inherits common CRUD operations from TenantScopedRepositoryImpl.
    Only implements domain-specific queries.
    """

    model_class = ContactModel
    id_column = "id"

    def _to_entity(self, model: ContactModel) -> ContactEntity:
        """Convert model to entity."""
        return ContactMapper.to_entity(model)

    def _to_model(self, entity: ContactEntity) -> ContactModel:
        """Convert entity to model."""
        return ContactMapper.to_model(entity)

    def _get_id_value(self, entity_id: ContactId) -> Any:
        """Extract raw ID value."""
        return entity_id.value

    # Domain-specific queries (not in base class)

    async def get_by_client_id(self, client_id: str, tenant_id: TenantId) -> Sequence[ContactEntity]:
        """Get all contacts for a client."""
        stmt = select(ContactModel).where(
            ContactModel.client_id == client_id,
            ContactModel.tenant_id == tenant_id.value,
            ContactModel.deleted_at.is_(None),
        )
        result = await self.session.execute(stmt)
        models = result.scalars().all()
        return [self._to_entity(m) for m in models]

    async def get_primary_contact(self, client_id: str, tenant_id: TenantId) -> ContactEntity | None:
        """Get the primary contact for a client."""
        stmt = select(ContactModel).where(
            ContactModel.client_id == client_id,
            ContactModel.tenant_id == tenant_id.value,
            ContactModel.is_primary == True,
            ContactModel.deleted_at.is_(None),
        )
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def list_all(
        self,
        tenant_id: TenantId,
        client_id: str | None = None,
        is_active: bool | None = None,
        is_primary: bool | None = None,
        search: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> Sequence[ContactEntity]:
        """List contacts with filtering, searching, and pagination."""
        # Build filters dict for base class
        filters: dict[str, Any] = {}
        if client_id:
            filters["client_id"] = client_id
        if is_active is not None:
            filters["is_active"] = is_active
        if is_primary is not None:
            filters["is_primary"] = is_primary

        return await self._query_all(
            tenant_id=tenant_id.value,
            limit=limit,
            offset=offset,
            sort_by="name",
            sort_desc=False,
            filters=filters,
            search=search,
            search_fields=["name"],
        )

    async def count(
        self,
        tenant_id: TenantId,
        client_id: str | None = None,
        is_active: bool | None = None,
        is_primary: bool | None = None,
        search: str | None = None,
    ) -> int:
        """Count contacts matching filters."""
        filters: dict[str, Any] = {}
        if client_id:
            filters["client_id"] = client_id
        if is_active is not None:
            filters["is_active"] = is_active
        if is_primary is not None:
            filters["is_primary"] = is_primary

        return await self._count_all(
            tenant_id=tenant_id.value,
            filters=filters,
            search=search,
            search_fields=["name"],
        )
