"""Contact Use Cases - Application services for Contact operations."""

from app.domain.entities.contact import ContactEntity
from app.domain.repositories.contact_repository import ContactRepository
from app.domain.value_objects.core import ContactId, Email, TenantId
from app.shared.utils.datetime import utc_now


class CreateContactUseCase:
    def __init__(self, contact_repository: ContactRepository):
        self.contact_repository = contact_repository

    async def execute(
        self,
        contact_id: ContactId,
        tenant_id: TenantId,
        client_id: str,
        name: str,
        title: str | None = None,
        email: str | None = None,
        phone: str | None = None,
        department: str | None = None,
        is_primary: bool = False,
        notes: str | None = None,
    ) -> ContactEntity:
        contact = ContactEntity(
            _id=contact_id,
            _tenant_id=tenant_id,
            _client_id=client_id,
            _name=name,
            _title=title,
            _email=Email(email) if email else None,
            _phone=phone,
            _department=department,
            _is_primary=is_primary,
            _notes=notes,
            _is_active=True,
            _created_at=utc_now(),
            _updated_at=utc_now(),
        )

        await self.contact_repository.save(contact)
        return contact


class UpdateContactUseCase:
    def __init__(self, contact_repository: ContactRepository):
        self.contact_repository = contact_repository

    async def execute(
        self,
        contact_id: ContactId,
        name: str | None = None,
        title: str | None = None,
        email: str | None = None,
        phone: str | None = None,
        department: str | None = None,
        is_primary: bool | None = None,
        notes: str | None = None,
    ) -> ContactEntity:
        contact = await self.contact_repository.get_by_id(contact_id)
        if not contact:
            raise ValueError(f"Contact {contact_id.value} not found")

        if name:
            contact.update_name(name)
        if email is not None or phone is not None or title is not None or department is not None:
            contact.update_contact_info(
                email=Email(email) if email else contact._email,
                phone=phone if phone is not None else contact._phone,
                title=title if title is not None else contact._title,
                department=department if department is not None else contact._department,
            )
        if is_primary is not None:
            contact.set_primary(is_primary)
        if notes is not None:
            contact._notes = notes
            contact._updated_at = utc_now()

        await self.contact_repository.save(contact)
        return contact


class ActivateContactUseCase:
    def __init__(self, contact_repository: ContactRepository):
        self.contact_repository = contact_repository

    async def execute(self, contact_id: ContactId) -> ContactEntity:
        contact = await self.contact_repository.get_by_id(contact_id)
        if not contact:
            raise ValueError(f"Contact {contact_id.value} not found")
        contact.activate()
        await self.contact_repository.save(contact)
        return contact


class DeactivateContactUseCase:
    def __init__(self, contact_repository: ContactRepository):
        self.contact_repository = contact_repository

    async def execute(self, contact_id: ContactId) -> ContactEntity:
        contact = await self.contact_repository.get_by_id(contact_id)
        if not contact:
            raise ValueError(f"Contact {contact_id.value} not found")
        contact.deactivate()
        await self.contact_repository.save(contact)
        return contact


class GetContactUseCase:
    def __init__(self, contact_repository: ContactRepository):
        self.contact_repository = contact_repository

    async def execute(self, contact_id: ContactId) -> ContactEntity | None:
        return await self.contact_repository.get_by_id(contact_id)
