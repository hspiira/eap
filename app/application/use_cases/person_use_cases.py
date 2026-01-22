"""
Person Use Cases

Application services for Person aggregate operations.
"""

from typing import TYPE_CHECKING, Union

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
from app.shared.utils.datetime import utc_now

if TYPE_CHECKING:
    from app.domain.entities.user import UserEntity
    from app.domain.value_objects.core import EmergencyContact


class CreateClientEmployeeUseCase:
    """Use case for creating a client employee person."""

    def __init__(self, person_repository: PersonRepository):
        self.person_repository = person_repository

    async def execute(
        self,
        person_id: PersonId,
        tenant_id: TenantId,
        user_id: UserId,
        profile: "UserEntity",
        employment_info: "EmploymentInfo",
    ) -> PersonEntity:
        """
        Create a new client employee person.

        Args:
            person_id: Unique person identifier
            tenant_id: Tenant identifier
            user_id: User identifier
            profile: UserEntity profile
            employment_info: Employment information

        Returns:
            Created PersonEntity

        Raises:
            ValueError: If person already exists
        """
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

        # Save person
        await self.person_repository.save(person)

        return person


class ActivatePersonUseCase:
    """Use case for activating a person."""

    def __init__(self, person_repository: PersonRepository):
        self.person_repository = person_repository

    async def execute(self, person_id: PersonId) -> PersonEntity:
        """
        Activate a person.

        Args:
            person_id: Person identifier

        Returns:
            Activated PersonEntity

        Raises:
            ValueError: If person not found
        """
        person = await self.person_repository.get_by_id(person_id)
        if not person:
            raise ValueError(f"Person {person_id.value} not found")

        person.activate()
        person._updated_at = utc_now()
        await self.person_repository.save(person)

        return person


class GetPersonUseCase:
    """Use case for retrieving a person."""

    def __init__(self, person_repository: PersonRepository):
        self.person_repository = person_repository

    async def execute(self, person_id: PersonId) -> PersonEntity | None:
        """
        Get person by ID.

        Args:
            person_id: Person identifier

        Returns:
            PersonEntity if found, None otherwise
        """
        return await self.person_repository.get_by_id(person_id)

    async def execute_by_user_id(self, user_id: UserId) -> PersonEntity | None:
        """
        Get person by user ID.

        Args:
            user_id: User identifier

        Returns:
            PersonEntity if found, None otherwise
        """
        return await self.person_repository.get_by_user_id(user_id)


class GetPersonsByTypeUseCase:
    """Use case for retrieving persons by type."""

    def __init__(self, person_repository: PersonRepository):
        self.person_repository = person_repository

    async def execute(
        self, tenant_id: TenantId, person_type: PersonType
    ) -> list[PersonEntity]:
        """
        Get all persons of a specific type within a tenant.

        Args:
            tenant_id: Tenant identifier
            person_type: Person type to filter by

        Returns:
            List of PersonEntity matching the type
        """
        return await self.person_repository.get_by_type(tenant_id, person_type)


class DeactivatePersonUseCase:
    """Use case for deactivating a person."""

    def __init__(self, person_repository: PersonRepository):
        self.person_repository = person_repository

    async def execute(
        self, person_id: PersonId, reason: str | None = None
    ) -> PersonEntity:
        """
        Deactivate a person.

        Args:
            person_id: Person identifier
            reason: Deactivation reason (optional)

        Returns:
            Deactivated PersonEntity

        Raises:
            ValueError: If person not found
            DomainError: If deactivation is invalid
        """
        person = await self.person_repository.get_by_id(person_id)
        if not person:
            raise ValueError(f"Person {person_id.value} not found")

        person.deactivate(reason)
        person._updated_at = utc_now()
        await self.person_repository.save(person)

        return person


class TerminatePersonUseCase:
    """Use case for terminating a person."""

    def __init__(self, person_repository: PersonRepository):
        self.person_repository = person_repository

    async def execute(self, person_id: PersonId, reason: str) -> PersonEntity:
        """
        Terminate a person.

        Args:
            person_id: Person identifier
            reason: Termination reason

        Returns:
            Terminated PersonEntity

        Raises:
            ValueError: If person not found
            DomainError: If termination is invalid
        """
        person = await self.person_repository.get_by_id(person_id)
        if not person:
            raise ValueError(f"Person {person_id.value} not found")

        person.terminate(reason)
        await self.person_repository.save(person)

        return person


class AddSecondaryRoleUseCase:
    """Use case for adding a secondary role to a person."""

    def __init__(self, person_repository: PersonRepository):
        self.person_repository = person_repository

    async def execute(
        self,
        person_id: PersonId,
        role: PersonType,
        info: "EmploymentInfo | LicenseInfo | StaffInfo",
    ) -> PersonEntity:
        """
        Add a secondary role to a person.

        Args:
            person_id: Person identifier
            role: Secondary person type
            info: Role-specific information

        Returns:
            Updated PersonEntity

        Raises:
            ValueError: If person not found
            DomainError: If adding role is invalid
        """
        person = await self.person_repository.get_by_id(person_id)
        if not person:
            raise ValueError(f"Person {person_id.value} not found")

        person.add_secondary_role(role, info)
        await self.person_repository.save(person)

        return person


class RemoveSecondaryRoleUseCase:
    """Use case for removing a secondary role from a person."""

    def __init__(self, person_repository: PersonRepository):
        self.person_repository = person_repository

    async def execute(self, person_id: PersonId) -> PersonEntity:
        """
        Remove secondary role from a person.

        Args:
            person_id: Person identifier

        Returns:
            Updated PersonEntity

        Raises:
            ValueError: If person not found
            DomainError: If person doesn't have secondary role
        """
        person = await self.person_repository.get_by_id(person_id)
        if not person:
            raise ValueError(f"Person {person_id.value} not found")

        person.remove_secondary_role()
        await self.person_repository.save(person)

        return person


class UpdateEmergencyContactUseCase:
    """Use case for updating emergency contact."""

    def __init__(self, person_repository: PersonRepository):
        self.person_repository = person_repository

    async def execute(
        self, person_id: PersonId, contact: "EmergencyContact"
    ) -> PersonEntity:
        """
        Update emergency contact for a person.

        Args:
            person_id: Person identifier
            contact: Emergency contact information

        Returns:
            Updated PersonEntity

        Raises:
            ValueError: If person not found
        """
        person = await self.person_repository.get_by_id(person_id)
        if not person:
            raise ValueError(f"Person {person_id.value} not found")

        person.update_emergency_contact(contact)
        await self.person_repository.save(person)

        return person


class UpdateEmploymentInfoUseCase:
    """Use case for updating employment information."""

    def __init__(self, person_repository: PersonRepository):
        self.person_repository = person_repository

    async def execute(
        self, person_id: PersonId, info: "EmploymentInfo"
    ) -> PersonEntity:
        """
        Update employment information for a person.

        Args:
            person_id: Person identifier
            info: Employment information

        Returns:
            Updated PersonEntity

        Raises:
            ValueError: If person not found
            DomainError: If update is invalid
        """
        person = await self.person_repository.get_by_id(person_id)
        if not person:
            raise ValueError(f"Person {person_id.value} not found")

        person.update_employment_info(info)
        await self.person_repository.save(person)

        return person


class UpdateLicenseInfoUseCase:
    """Use case for updating license information."""

    def __init__(self, person_repository: PersonRepository):
        self.person_repository = person_repository

    async def execute(self, person_id: PersonId, info: "LicenseInfo") -> PersonEntity:
        """
        Update license information for a person.

        Args:
            person_id: Person identifier
            info: License information

        Returns:
            Updated PersonEntity

        Raises:
            ValueError: If person not found
            DomainError: If update is invalid
        """
        person = await self.person_repository.get_by_id(person_id)
        if not person:
            raise ValueError(f"Person {person_id.value} not found")

        person.update_license_info(info)
        await self.person_repository.save(person)

        return person


class UpdateStaffInfoUseCase:
    """Use case for updating staff information."""

    def __init__(self, person_repository: PersonRepository):
        self.person_repository = person_repository

    async def execute(self, person_id: PersonId, info: "StaffInfo") -> PersonEntity:
        """
        Update staff information for a person.

        Args:
            person_id: Person identifier
            info: Staff information

        Returns:
            Updated PersonEntity

        Raises:
            ValueError: If person not found
            DomainError: If update is invalid
        """
        person = await self.person_repository.get_by_id(person_id)
        if not person:
            raise ValueError(f"Person {person_id.value} not found")

        person.update_staff_info(info)
        await self.person_repository.save(person)

        return person


class ArchivePersonUseCase:
    """Use case for archiving a person."""

    def __init__(self, person_repository: PersonRepository):
        self.person_repository = person_repository

    async def execute(self, person_id: PersonId) -> PersonEntity:
        """
        Archive a person.

        Args:
            person_id: Person identifier

        Returns:
            Archived PersonEntity

        Raises:
            ValueError: If person not found
            DomainError: If archive is invalid
        """
        person = await self.person_repository.get_by_id(person_id)
        if not person:
            raise ValueError(f"Person {person_id.value} not found")

        person.archive()
        await self.person_repository.save(person)

        return person


class RestorePersonUseCase:
    """Use case for restoring a person."""

    def __init__(self, person_repository: PersonRepository):
        self.person_repository = person_repository

    async def execute(self, person_id: PersonId) -> PersonEntity:
        """
        Restore an archived or soft-deleted person.

        Args:
            person_id: Person identifier

        Returns:
            Restored PersonEntity

        Raises:
            ValueError: If person not found
            DomainError: If restore is invalid
        """
        person = await self.person_repository.get_by_id(person_id)
        if not person:
            raise ValueError(f"Person {person_id.value} not found")

        person.restore()
        await self.person_repository.save(person)

        return person
