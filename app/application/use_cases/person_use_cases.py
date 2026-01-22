"""
Person Use Cases

Application services for Person aggregate operations.
Refactored to use base use case classes.
"""

from typing import TYPE_CHECKING

from app.application.use_cases.base import (
    BaseUseCase,
    create_activate_use_case,
    create_archive_use_case,
    create_deactivate_use_case,
    create_restore_use_case,
    create_terminate_use_case,
)
from app.domain.entities.person import PersonEntity
from app.domain.enums import PersonType
from app.domain.repositories.person_repository import PersonRepository
from app.domain.value_objects.core import (
    EmploymentInfo,
    LicenseInfo,
    PersonId,
    StaffInfo,
    TenantId,
    UserId,
)

if TYPE_CHECKING:
    from app.domain.entities.user import UserEntity
    from app.domain.value_objects.core import EmergencyContact


# =============================================================================
# LIFECYCLE USE CASES (Using Base Factories)
# =============================================================================


class ActivatePersonUseCase:
    """Use case for activating a person."""

    def __init__(self, person_repository: PersonRepository):
        self._use_case = create_activate_use_case(person_repository, "Person")

    async def execute(self, person_id: PersonId) -> PersonEntity:
        return await self._use_case.execute(person_id)


class DeactivatePersonUseCase:
    """Use case for deactivating a person."""

    def __init__(self, person_repository: PersonRepository):
        self._use_case = create_deactivate_use_case(person_repository, "Person")

    async def execute(self, person_id: PersonId, reason: str | None = None) -> PersonEntity:
        return await self._use_case.execute(person_id, reason=reason)


class TerminatePersonUseCase:
    """Use case for terminating a person."""

    def __init__(self, person_repository: PersonRepository):
        self._use_case = create_terminate_use_case(person_repository, "Person")

    async def execute(self, person_id: PersonId, reason: str) -> PersonEntity:
        return await self._use_case.execute(person_id, reason=reason)


class ArchivePersonUseCase:
    """Use case for archiving a person."""

    def __init__(self, person_repository: PersonRepository):
        self._use_case = create_archive_use_case(person_repository, "Person")

    async def execute(self, person_id: PersonId) -> PersonEntity:
        return await self._use_case.execute(person_id)


class RestorePersonUseCase:
    """Use case for restoring a person."""

    def __init__(self, person_repository: PersonRepository):
        self._use_case = create_restore_use_case(person_repository, "Person")

    async def execute(self, person_id: PersonId) -> PersonEntity:
        return await self._use_case.execute(person_id)


# =============================================================================
# CREATE USE CASE
# =============================================================================


class CreateClientEmployeeUseCase(BaseUseCase[PersonEntity, PersonId]):
    """Use case for creating a client employee person."""

    def __init__(self, person_repository: PersonRepository):
        super().__init__(person_repository)
        self.person_repository = person_repository

    async def execute(
        self,
        person_id: PersonId,
        tenant_id: TenantId,
        user_id: UserId,
        profile: "UserEntity",
        employment_info: "EmploymentInfo",
    ) -> PersonEntity:
        """Create a new client employee person."""
        # Check if person already exists for this user
        existing = await self.person_repository.get_by_user_id(user_id)
        if existing:
            raise ValueError(f"Person already exists for user {user_id.value}")

        # Create person entity using factory method
        person = PersonEntity.create_client_employee(
            id=person_id,
            tenant_id=tenant_id,
            user_id=user_id,
            profile=profile,
            employment_info=employment_info,
        )

        return await self._save_and_publish_events(person)


# =============================================================================
# SPECIALIZED COMMAND USE CASES
# =============================================================================


class AddSecondaryRoleUseCase(BaseUseCase[PersonEntity, PersonId]):
    """Use case for adding a secondary role to a person."""

    def __init__(self, person_repository: PersonRepository):
        super().__init__(person_repository)

    async def execute(
        self,
        person_id: PersonId,
        role: PersonType,
        info: "EmploymentInfo | LicenseInfo | StaffInfo",
    ) -> PersonEntity:
        """Add a secondary role to a person."""
        person = await self._get_entity_or_raise(person_id, "Person")
        person.add_secondary_role(role, info)
        return await self._save_and_publish_events(person)


class RemoveSecondaryRoleUseCase(BaseUseCase[PersonEntity, PersonId]):
    """Use case for removing a secondary role from a person."""

    def __init__(self, person_repository: PersonRepository):
        super().__init__(person_repository)

    async def execute(self, person_id: PersonId) -> PersonEntity:
        """Remove secondary role from a person."""
        person = await self._get_entity_or_raise(person_id, "Person")
        person.remove_secondary_role()
        return await self._save_and_publish_events(person)


# =============================================================================
# UPDATE USE CASES
# =============================================================================


class UpdateEmergencyContactUseCase(BaseUseCase[PersonEntity, PersonId]):
    """Use case for updating emergency contact."""

    def __init__(self, person_repository: PersonRepository):
        super().__init__(person_repository)

    async def execute(
        self, person_id: PersonId, contact: "EmergencyContact"
    ) -> PersonEntity:
        """Update emergency contact for a person."""
        person = await self._get_entity_or_raise(person_id, "Person")
        person.update_emergency_contact(contact)
        return await self._save_and_publish_events(person)


class UpdateEmploymentInfoUseCase(BaseUseCase[PersonEntity, PersonId]):
    """Use case for updating employment information."""

    def __init__(self, person_repository: PersonRepository):
        super().__init__(person_repository)

    async def execute(
        self, person_id: PersonId, info: "EmploymentInfo"
    ) -> PersonEntity:
        """Update employment information for a person."""
        person = await self._get_entity_or_raise(person_id, "Person")
        person.update_employment_info(info)
        return await self._save_and_publish_events(person)


class UpdateLicenseInfoUseCase(BaseUseCase[PersonEntity, PersonId]):
    """Use case for updating license information."""

    def __init__(self, person_repository: PersonRepository):
        super().__init__(person_repository)

    async def execute(self, person_id: PersonId, info: "LicenseInfo") -> PersonEntity:
        """Update license information for a person."""
        person = await self._get_entity_or_raise(person_id, "Person")
        person.update_license_info(info)
        return await self._save_and_publish_events(person)


class UpdateStaffInfoUseCase(BaseUseCase[PersonEntity, PersonId]):
    """Use case for updating staff information."""

    def __init__(self, person_repository: PersonRepository):
        super().__init__(person_repository)

    async def execute(self, person_id: PersonId, info: "StaffInfo") -> PersonEntity:
        """Update staff information for a person."""
        person = await self._get_entity_or_raise(person_id, "Person")
        person.update_staff_info(info)
        return await self._save_and_publish_events(person)


# =============================================================================
# QUERY USE CASES
# =============================================================================


class GetPersonUseCase(BaseUseCase[PersonEntity, PersonId]):
    """Use case for retrieving a person."""

    def __init__(self, person_repository: PersonRepository):
        super().__init__(person_repository)
        self.person_repository = person_repository

    async def execute(self, person_id: PersonId) -> PersonEntity | None:
        """Get person by ID."""
        return await self.repository.get_by_id(person_id)

    async def execute_by_user_id(self, user_id: UserId) -> PersonEntity | None:
        """Get person by user ID."""
        return await self.person_repository.get_by_user_id(user_id)


class GetPersonsByTypeUseCase(BaseUseCase[PersonEntity, PersonId]):
    """Use case for retrieving persons by type."""

    def __init__(self, person_repository: PersonRepository):
        super().__init__(person_repository)
        self.person_repository = person_repository

    async def execute(
        self, tenant_id: TenantId, person_type: PersonType
    ) -> list[PersonEntity]:
        """Get all persons of a specific type within a tenant."""
        return await self.person_repository.get_by_type(tenant_id, person_type)
