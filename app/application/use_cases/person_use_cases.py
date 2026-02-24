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
from app.domain.repositories.client_repository import ClientRepository
from app.domain.services.employee_code_generator import EmployeeCodeGenerator
from app.domain.value_objects.core import (
    ClientId,
    DependentInfo,
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

    def __init__(
        self,
        person_repository: PersonRepository,
        client_repository: ClientRepository,
    ):
        super().__init__(person_repository)
        self.person_repository = person_repository
        self.client_repository = client_repository
        self.code_generator = EmployeeCodeGenerator(
            person_repository, client_repository
        )

    async def execute(
        self,
        person_id: PersonId,
        tenant_id: TenantId,
        user_id: UserId,
        profile: "UserEntity",
        client_id: ClientId,
        role: str,
        start_date: "date",
        status: "WorkStatus",
        department: str | None = None,
        employee_id: str | None = None,
        end_date: "date | None" = None,
        family_id: PersonId | None = None,
    ) -> PersonEntity:
        """
        Create a new client employee person.
        
        Args:
            person_id: Person identifier
            tenant_id: Tenant identifier
            user_id: User identifier
            profile: User profile entity
            client_id: Client identifier
            role: Job role
            start_date: Employment start date
            status: Work status
            department: Department (optional)
            employee_id: External employee ID (optional)
            end_date: Employment end date (optional)
            family_id: Optional family identifier (if adding to existing family)
            
        Returns:
            Created PersonEntity
        """
        existing = await self.person_repository.get_by_user_id(user_id)
        if existing:
            raise ValueError(f"Person already exists for user {user_id.value}")

        employee_code = await self.code_generator.generate_code(
            client_id=client_id,
            tenant_id=tenant_id,
            family_id=family_id,
            person_id=person_id,
        )

        from app.domain.value_objects.core import EmploymentInfo
        from datetime import date as date_type
        
        employment_info = EmploymentInfo(
            client_id=client_id,
            employee_code=employee_code,
            role=role,
            start_date=start_date,
            status=status,
            department=department,
            employee_id=employee_id,
            end_date=end_date,
        )

        actual_family_id = family_id if family_id else person_id

        person = PersonEntity.create_client_employee(
            id=person_id,
            tenant_id=tenant_id,
            user_id=user_id,
            profile=profile,
            employment_info=employment_info,
            family_id=actual_family_id,
        )

        return await self._save_and_publish_events(person)


class CreateDependentUseCase(BaseUseCase[PersonEntity, PersonId]):
    """Use case for creating a dependent person."""

    def __init__(self, person_repository: PersonRepository):
        super().__init__(person_repository)
        self.person_repository = person_repository

    async def execute(
        self,
        person_id: PersonId,
        tenant_id: TenantId,
        user_id: UserId,
        profile: "UserEntity",
        dependent_info: "DependentInfo",
    ) -> PersonEntity:
        """
        Create a new dependent person.
        
        Args:
            person_id: Person identifier
            tenant_id: Tenant identifier
            user_id: User identifier
            profile: User profile entity
            dependent_info: Dependent information (includes primary_employee_id)
            
        Returns:
            Created PersonEntity
            
        Raises:
            ValueError: If person already exists for user or primary employee not found/invalid
        """
        existing = await self.person_repository.get_by_user_id(user_id)
        if existing:
            raise ValueError(f"Person already exists for user {user_id.value}")

        primary_employee = await self.person_repository.get_by_id(
            dependent_info.primary_employee_id
        )
        if not primary_employee:
            raise ValueError(
                f"Primary employee {dependent_info.primary_employee_id.value} not found"
            )

        if primary_employee.person_type != PersonType.CLIENT_EMPLOYEE:
            raise ValueError(
                f"Primary employee must be a CLIENT_EMPLOYEE, got {primary_employee.person_type.value}"
            )

        if primary_employee.tenant_id != tenant_id:
            raise ValueError(
                "Primary employee must belong to the same tenant as the dependent"
            )

        person = PersonEntity.create_dependent(
            id=person_id,
            tenant_id=tenant_id,
            user_id=user_id,
            profile=profile,
            dependent_info=dependent_info,
            primary_employee=primary_employee,
        )

        return await self._save_and_publish_events(person)


# =============================================================================
# SPECIALIZED COMMAND USE CASES
# =============================================================================


class AddSecondaryRoleUseCase(BaseUseCase[PersonEntity, PersonId]):
    """Use case for adding a secondary role to a person."""

    def __init__(
        self,
        person_repository: PersonRepository,
        client_repository: ClientRepository | None = None,
    ):
        super().__init__(person_repository)
        self.client_repository = client_repository
        if client_repository:
            self.code_generator = EmployeeCodeGenerator(
                person_repository, client_repository
            )
        else:
            self.code_generator = None

    async def execute(
        self,
        person_id: PersonId,
        role: PersonType,
        info: "EmploymentInfo | LicenseInfo | StaffInfo",
        tenant_id: TenantId | None = None,
        family_id: PersonId | None = None,
    ) -> PersonEntity:
        """
        Add a secondary role to a person.
        
        Args:
            person_id: Person identifier
            role: Secondary role type
            info: Role-specific information
            tenant_id: Tenant identifier (required for CLIENT_EMPLOYEE to generate code)
            family_id: Optional family identifier (for CLIENT_EMPLOYEE)
        """
        person = await self._get_entity_or_raise(person_id, "Person")
        
        if role == PersonType.CLIENT_EMPLOYEE and isinstance(info, EmploymentInfo):
            if not info.employee_code and self.code_generator and tenant_id:
                employee_code = await self.code_generator.generate_code(
                    client_id=info.client_id,
                    tenant_id=tenant_id,
                    family_id=family_id,
                    person_id=person_id,
                )
                from app.domain.value_objects.core import EmploymentInfo
                info = EmploymentInfo(
                    client_id=info.client_id,
                    employee_code=employee_code,
                    role=info.role,
                    start_date=info.start_date,
                    status=info.status,
                    department=info.department,
                    employee_id=info.employee_id,
                    end_date=info.end_date,
                )
        
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


class UpdateDependentInfoUseCase(BaseUseCase[PersonEntity, PersonId]):
    """Use case for updating dependent information."""

    def __init__(self, person_repository: PersonRepository):
        super().__init__(person_repository)

    async def execute(
        self, person_id: PersonId, dependent_info: "DependentInfo"
    ) -> PersonEntity:
        """Update dependent information for a person (must be DEPENDENT type)."""
        person = await self._get_entity_or_raise(person_id, "Person")
        person.update_dependent_info(dependent_info)
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
