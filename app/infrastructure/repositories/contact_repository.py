"""Contact Repository Implementation - SQLAlchemy implementation."""

from typing import Sequence

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.contact import ContactEntity
from app.domain.repositories.contact_repository import ContactRepository
from app.domain.value_objects.core import ContactId, TenantId
from app.infrastructure.mappers.contact_mapper import ContactMapper
from app.infrastructure.models.contact_model import ContactModel
from app.shared.utils.datetime import utc_now


class ContactRepositoryImpl(ContactRepository):
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(self, contact_id: ContactId) -> ContactEntity | None:
        stmt = select(ContactModel).where(
            ContactModel.id == contact_id.value,
            ContactModel.deleted_at.is_(None),
        )
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        return ContactMapper.to_entity(model) if model else None

    async def get_by_client_id(self, client_id: str, tenant_id: TenantId) -> Sequence[ContactEntity]:
        stmt = select(ContactModel).where(
            ContactModel.client_id == client_id,
            ContactModel.tenant_id == tenant_id.value,
            ContactModel.deleted_at.is_(None),
        )
        result = await self.session.execute(stmt)
        models = result.scalars().all()
        return [ContactMapper.to_entity(m) for m in models]

    async def get_primary_contact(self, client_id: str, tenant_id: TenantId) -> ContactEntity | None:
        stmt = select(ContactModel).where(
            ContactModel.client_id == client_id,
            ContactModel.tenant_id == tenant_id.value,
            ContactModel.is_primary == True,
            ContactModel.deleted_at.is_(None),
        )
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        return ContactMapper.to_entity(model) if model else None

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
        stmt = select(ContactModel).where(
            ContactModel.tenant_id == tenant_id.value,
            ContactModel.deleted_at.is_(None),
        )
        if client_id:
            stmt = stmt.where(ContactModel.client_id == client_id)
        if is_active is not None:
            stmt = stmt.where(ContactModel.is_active == is_active)
        if is_primary is not None:
            stmt = stmt.where(ContactModel.is_primary == is_primary)
        if search:
            stmt = stmt.where(ContactModel.name.ilike(f"%{search}%"))
        stmt = stmt.limit(limit).offset(offset).order_by(ContactModel.name)
        result = await self.session.execute(stmt)
        return [ContactMapper.to_entity(m) for m in result.scalars().all()]

    async def count(
        self,
        tenant_id: TenantId,
        client_id: str | None = None,
        is_active: bool | None = None,
        is_primary: bool | None = None,
        search: str | None = None,
    ) -> int:
        stmt = select(func.count(ContactModel.id)).where(
            ContactModel.tenant_id == tenant_id.value,
            ContactModel.deleted_at.is_(None),
        )
        if client_id:
            stmt = stmt.where(ContactModel.client_id == client_id)
        if is_active is not None:
            stmt = stmt.where(ContactModel.is_active == is_active)
        if is_primary is not None:
            stmt = stmt.where(ContactModel.is_primary == is_primary)
        if search:
            stmt = stmt.where(ContactModel.name.ilike(f"%{search}%"))
        result = await self.session.execute(stmt)
        return int(result.scalar() or 0)

    async def save(self, contact: ContactEntity) -> None:
        model = ContactMapper.to_model(contact)
        await self.session.merge(model)

    async def delete(self, contact_id: ContactId) -> None:
        stmt = select(ContactModel).where(
            ContactModel.id == contact_id.value,
            ContactModel.deleted_at.is_(None),
        )
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        if model:
            model.deleted_at = utc_now()
            model.updated_at = utc_now()
            await self.session.merge(model)

    async def exists(self, contact_id: ContactId) -> bool:
        from sqlalchemy import exists as sql_exists
        stmt = sql_exists().where(
            ContactModel.id == contact_id.value,
            ContactModel.deleted_at.is_(None),
        ).select()
        result = await self.session.execute(stmt)
        return bool(result.scalar())
