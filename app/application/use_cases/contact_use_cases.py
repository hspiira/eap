"""Contact Use Cases - Application services for Contact operations."""

from app.application.use_cases.base import (
    BaseUseCase,
    create_activate_use_case,
    create_deactivate_use_case,
)
from app.domain.entities.contact import ContactEntity
from app.domain.repositories.contact_repository import ContactRepository
from app.domain.value_objects.core import ContactId, Email, TenantId
from app.shared.utils.datetime import utc_now


# =============================================================================
# LIFECYCLE USE CASES (Using Base Factories)
# =============================================================================


class ActivateContactUseCase:
    """Use case for activating a contact."""

    def __init__(self, contact_repository: ContactRepository):
        self._use_case = create_activate_use_case(contact_repository, "Contact")

    async def execute(self, contact_id: ContactId) -> ContactEntity:
        return await self._use_case.execute(contact_id)


class DeactivateContactUseCase:
    """Use case for deactivating a contact."""

    def __init__(self, contact_repository: ContactRepository):
        self._use_case = create_deactivate_use_case(contact_repository, "Contact")

    async def execute(self, contact_id: ContactId) -> ContactEntity:
        return await self._use_case.execute(contact_id)


# =============================================================================
# CREATE USE CASE
# =============================================================================


class CreateContactUseCase(BaseUseCase[ContactEntity, ContactId]):
    """Use case for creating a contact."""

    def __init__(self, contact_repository: ContactRepository):
        super().__init__(contact_repository)

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
        """Create a new contact."""
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

        return await self._save_and_publish_events(contact)


# =============================================================================
# UPDATE USE CASE
# =============================================================================


class UpdateContactUseCase(BaseUseCase[ContactEntity, ContactId]):
    """Use case for updating a contact."""

    def __init__(self, contact_repository: ContactRepository):
        super().__init__(contact_repository)

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
        """Update a contact."""
        contact = await self._get_entity_or_raise(contact_id, "Contact")

        if name:
            contact.update_name(name)
        if email is not None or phone is not None or title is not None or department is not None:
            contact.update_contact_info(
                email=Email(email) if email else contact.email,
                phone=phone if phone is not None else contact.phone,
                title=title if title is not None else contact.title,
                department=department if department is not None else contact.department,
            )
        if is_primary is not None:
            contact.set_primary(is_primary)
        if notes is not None:
            contact._notes = notes
            contact._updated_at = utc_now()

        return await self._save_and_publish_events(contact)


# =============================================================================
# QUERY USE CASE
# =============================================================================


class GetContactUseCase(BaseUseCase[ContactEntity, ContactId]):
    """Use case for retrieving a contact."""

    def __init__(self, contact_repository: ContactRepository):
        super().__init__(contact_repository)

    async def execute(self, contact_id: ContactId) -> ContactEntity | None:
        """Get contact by ID."""
        return await self.repository.get_by_id(contact_id)
