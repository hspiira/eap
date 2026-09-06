"""
Person Entity (Aggregate Root)

Represents a uniquely identifiable person within the EAP domain.
Identity and lifecycle define the entity, not role-specific attributes.

Supports multiple person types via a discriminator:
- PLATFORM_STAFF
- CLIENT_EMPLOYEE
- DEPENDENT
- SERVICE_PROVIDER

Responsibilities:
- Enforce type-specific business rules and invariants
- Manage lifecycle (activation, deactivation)
- Determine service eligibility
- Handle dual roles where permitted
- Maintain dependent → employee relationships

Key Invariants:
- Dependents must have a primary employee and no dual roles
- Service providers must have valid licenses
- Client employees must have valid employment details
- Eligibility depends on status, type, and relationships

Design Notes:
- Aggregate root for all person-related rules
- Identity-based equality (PersonId)
- Pure domain entity (no persistence or framework concerns)
"""

from dataclasses import dataclass, field
from datetime import date, datetime

from app.domain.entities.user import UserEntity
from app.domain.enums import BaseStatus, PersonType
from app.domain.events import (
    DomainEvent,
    PersonActivated,
    PersonDeactivated,
    PersonSecondaryRoleAdded,
    PersonSecondaryRoleRemoved,
    PersonTerminated,
)
from app.domain.exceptions import ConflictError, DomainError, InvariantViolation
from app.domain.value_objects.core import (
    ClientId,
    DependentInfo,
    EmergencyContact,
    EmploymentInfo,
    LicenseInfo,
    PersonId,
    ProviderProfile,
    StaffInfo,
    TenantId,
    UserId,
)
from app.shared.utils.datetime import utc_now

# Error messages
_DEPENDENT_DUAL_ROLE_ERROR = "Dependents cannot have dual roles"


@dataclass
class PersonEntity:
    # Required fields (no defaults)
    id: PersonId
    tenant_id: TenantId
    person_type: PersonType
    is_dual_role: bool
    user_id: UserId
    profile: UserEntity  # Entity inside aggregate
    status: BaseStatus
    created_at: datetime
    updated_at: datetime

    # Optional fields with defaults
    secondary_person_type: PersonType | None = None
    employment_info: EmploymentInfo | None = None  # CLIENT_EMPLOYEE
    license_info: LicenseInfo | None = None  # SERVICE_PROVIDER
    provider_profile: ProviderProfile | None = None  # SERVICE_PROVIDER (panel metadata)
    staff_info: StaffInfo | None = None  # PLATFORM_STAFF
    dependent_info: DependentInfo | None = None  # DEPENDENT
    emergency_contact: EmergencyContact | None = None
    family_id: PersonId | None = (
        None  # Points to primary employee in family (for family code grouping)
    )
    last_service_date: date | None = None
    deleted_at: datetime | None = None
    events: list[DomainEvent] = field(default_factory=list[DomainEvent])

    # === Behaviors ===

    def activate(self) -> None:
        """Activate person for operation"""
        if self.status == BaseStatus.DELETED:
            raise DomainError("Cannot activate deleted person")
        if self.status == BaseStatus.ACTIVE:
            raise ConflictError("Person is already active")
        self.status = BaseStatus.ACTIVE
        now = utc_now()
        self.updated_at = now
        self.events.append(
            PersonActivated(occurred_at=now, person_id=self.id, person_type=self.person_type)
        )

    def deactivate(self, reason: str | None = None) -> None:
        """Deactivate person"""
        if self.status == BaseStatus.DELETED:
            raise DomainError("Cannot deactivate deleted person")
        if self.status == BaseStatus.INACTIVE:
            raise ConflictError("Person is already inactive")
        self.status = BaseStatus.INACTIVE
        now = utc_now()
        self.updated_at = now
        self.events.append(PersonDeactivated(occurred_at=now, person_id=self.id, reason=reason))

    def terminate(self, reason: str) -> None:
        """Permanently terminate person"""
        if not reason:
            raise DomainError("Termination requires reason")
        if self.status == BaseStatus.DELETED:
            raise ConflictError("Person is already terminated")
        self.status = BaseStatus.DELETED
        now = utc_now()
        self.deleted_at = now
        self.updated_at = now
        self.events.append(PersonTerminated(occurred_at=now, person_id=self.id, reason=reason))

    def is_eligible_for_services(self, primary_employee: "PersonEntity | None" = None) -> bool:
        """Whether this person is eligible to receive services.

        For DEPENDENT persons, eligibility is composed of:
        - the dependent's own status is ACTIVE
        - DependentInfo.is_eligible() (intrinsic relationship validity)
        - the primary employee is also eligible

        Callers in the application layer must load the primary employee and
        pass it in for dependents. If omitted, eligibility fails closed
        (returns False) rather than silently passing.
        """
        if self.status != BaseStatus.ACTIVE:
            return False

        if self.person_type == PersonType.CLIENT_EMPLOYEE:
            return self.employment_info is not None and self.employment_info.is_active()

        if self.person_type == PersonType.DEPENDENT:
            if self.dependent_info is None or not self.dependent_info.is_eligible():
                return False
            if primary_employee is None:
                return False
            return primary_employee.is_eligible_for_services()

        if self.person_type == PersonType.SERVICE_PROVIDER:
            return self.license_info is not None and self.license_info.is_valid()

        return True  # PLATFORM_STAFF

    def add_secondary_role(
        self, role: PersonType, info: EmploymentInfo | LicenseInfo | StaffInfo
    ) -> None:
        """Add a secondary role to the person with role-specific information.

        Args:
            role: The secondary person type to add
            info: The role-specific value object (EmploymentInfo, LicenseInfo, or StaffInfo)

        Raises:
            DomainError: If the person is a dependent, role matches primary, or role/info mismatch
        """
        if self.person_type == PersonType.DEPENDENT:
            raise DomainError(_DEPENDENT_DUAL_ROLE_ERROR)

        if role == PersonType.DEPENDENT:
            raise DomainError("Cannot add dependent as secondary role")

        if role == self.person_type:
            raise ConflictError(
                f"Cannot add {role.value} as secondary role when it is already the primary role"
            )

        # Check max 2 clients rule for CLIENT_EMPLOYEE roles
        if role == PersonType.CLIENT_EMPLOYEE:
            if not isinstance(info, EmploymentInfo):
                raise DomainError(
                    f"CLIENT_EMPLOYEE role requires EmploymentInfo, got {type(info).__name__}"
                )
            self._check_max_clients_rule(info.client_id)
            self.employment_info = info
        elif role == PersonType.SERVICE_PROVIDER:
            if not isinstance(info, LicenseInfo):
                raise DomainError(
                    f"SERVICE_PROVIDER role requires LicenseInfo, got {type(info).__name__}"
                )
            self.license_info = info
        elif role == PersonType.PLATFORM_STAFF:
            if not isinstance(info, StaffInfo):
                raise DomainError(
                    f"PLATFORM_STAFF role requires StaffInfo, got {type(info).__name__}"
                )
            self.staff_info = info
        else:
            raise DomainError(f"Invalid secondary role: {role}")

        self.is_dual_role = True
        self.secondary_person_type = role
        now = utc_now()
        self.updated_at = now
        self._ensure_invariants()
        self.events.append(PersonSecondaryRoleAdded(occurred_at=now, person_id=self.id, role=role))

    def remove_secondary_role(self) -> None:
        """Remove the secondary role from the person.

        Raises:
            DomainError: If the person doesn't have a secondary role
        """
        if not self.is_dual_role or not self.secondary_person_type:
            raise DomainError("Person does not have a secondary role to remove")

        # Clear role-specific info based on secondary role
        if self.secondary_person_type == PersonType.CLIENT_EMPLOYEE:
            # Only clear if it's not the primary role
            if self.person_type != PersonType.CLIENT_EMPLOYEE:
                self.employment_info = None
        elif self.secondary_person_type == PersonType.SERVICE_PROVIDER:
            if self.person_type != PersonType.SERVICE_PROVIDER:
                self.license_info = None
        elif self.secondary_person_type == PersonType.PLATFORM_STAFF:
            if self.person_type != PersonType.PLATFORM_STAFF:
                self.staff_info = None

        removed_role = self.secondary_person_type
        self.is_dual_role = False
        self.secondary_person_type = None
        now = utc_now()
        self.updated_at = now
        self._ensure_invariants()
        self.events.append(
            PersonSecondaryRoleRemoved(occurred_at=now, person_id=self.id, role=removed_role)
        )

    def update_emergency_contact(self, contact: EmergencyContact) -> None:
        """Update emergency contact information."""
        if self.status == BaseStatus.DELETED:
            raise DomainError("Cannot update emergency contact for deleted person")
        self.emergency_contact = contact
        now = utc_now()
        self.updated_at = now

    def update_employment_info(self, info: EmploymentInfo) -> None:
        """Update employment information."""
        if self.status == BaseStatus.DELETED:
            raise DomainError("Cannot update employment info for deleted person")
        if self.employment_info and self.employment_info.client_id != info.client_id:
            self._check_max_clients_rule(info.client_id)
        self.employment_info = info
        self.updated_at = utc_now()
        self._ensure_invariants()

    def _check_max_clients_rule(self, new_client_id: ClientId) -> None:
        """Check that person is not already employee/dependent for more than 1 client."""
        clients: set[ClientId] = set()

        if self.person_type == PersonType.CLIENT_EMPLOYEE and self.employment_info:
            clients.add(self.employment_info.client_id)
        elif self.person_type == PersonType.DEPENDENT and self.dependent_info:
            pass

        if self.secondary_person_type == PersonType.CLIENT_EMPLOYEE and self.employment_info:
            clients.add(self.employment_info.client_id)

        if new_client_id in clients:
            return

        if len(clients) >= 2:
            raise DomainError("Person cannot be employee or dependent for more than 2 clients")

    def update_license_info(self, info: LicenseInfo) -> None:
        """Update license information."""
        if self.status == BaseStatus.DELETED:
            raise DomainError("Cannot update license info for deleted person")
        self.license_info = info
        self.updated_at = utc_now()
        self._ensure_invariants()

    def update_staff_info(self, info: StaffInfo) -> None:
        """Update staff information."""
        if self.status == BaseStatus.DELETED:
            raise DomainError("Cannot update staff info for deleted person")
        self.staff_info = info
        self.updated_at = utc_now()
        self._ensure_invariants()

    def update_dependent_info(self, info: DependentInfo) -> None:
        """Update dependent information. Only valid when person_type is DEPENDENT."""
        if self.status == BaseStatus.DELETED:
            raise DomainError("Cannot update dependent info for deleted person")
        if self.person_type != PersonType.DEPENDENT:
            raise DomainError("Only dependents have dependent info to update")
        self.dependent_info = info
        self.updated_at = utc_now()
        self._ensure_invariants()

    def archive(self) -> None:
        """Archive person (softer than terminate).

        Sets status to ARCHIVED. This is reversible via restore().
        Note: archive() does NOT set _deleted_at; only terminate() does.
        """
        if self.status == BaseStatus.DELETED:
            raise DomainError("Cannot archive deleted person")
        if self.status == BaseStatus.ARCHIVED:
            raise ConflictError("Person is already archived")
        self.status = BaseStatus.ARCHIVED
        self.updated_at = utc_now()

    def restore(self) -> None:
        """Restore archived person to active status.

        Only restores from ARCHIVED to ACTIVE. Terminated persons (DELETED status)
        cannot be restored as termination is permanent.
        """
        if self.status == BaseStatus.DELETED:
            raise DomainError("Cannot restore deleted person")
        if self.status == BaseStatus.ACTIVE:
            raise ConflictError("Person is already active")
        if self.status != BaseStatus.ARCHIVED:
            raise ConflictError("Person must be archived to restore")
        self.status = BaseStatus.ACTIVE
        self.updated_at = utc_now()

    # === Factory Methods ===

    @classmethod
    def create_client_employee(
        cls,
        id: PersonId,
        tenant_id: TenantId,
        user_id: UserId,
        profile: UserEntity,
        employment_info: EmploymentInfo,
        family_id: PersonId | None = None,
    ) -> "PersonEntity":
        """Factory for CLIENT_EMPLOYEE type

        Args:
            id: Person identifier
            tenant_id: Tenant identifier
            user_id: User identifier
            profile: User profile entity
            employment_info: Employment information (includes client_id and employee_code)
            family_id: Optional family identifier (points to primary employee in family)
        """
        now = utc_now()
        person = cls(
            id=id,
            tenant_id=tenant_id,
            person_type=PersonType.CLIENT_EMPLOYEE,
            is_dual_role=False,
            user_id=user_id,
            profile=profile,
            employment_info=employment_info,
            family_id=family_id,  # Set family_id if part of existing family
            status=BaseStatus.PENDING,
            created_at=now,
            updated_at=now,
        )
        person._ensure_invariants()
        return person

    @classmethod
    def create_dependent(
        cls,
        id: PersonId,
        tenant_id: TenantId,
        user_id: UserId,
        profile: UserEntity,
        dependent_info: DependentInfo,
        primary_employee: "PersonEntity",
    ) -> "PersonEntity":
        """
        Factory for DEPENDENT type.

        Args:
            id: Person identifier
            tenant_id: Tenant identifier
            user_id: User identifier
            profile: User profile entity
            dependent_info: Dependent information (includes primary_employee_id)
            primary_employee: The primary employee person entity (must be CLIENT_EMPLOYEE)

        Raises:
            DomainError: If primary employee is not a CLIENT_EMPLOYEE
        """
        if primary_employee.person_type != PersonType.CLIENT_EMPLOYEE:
            raise DomainError("Primary employee must be a CLIENT_EMPLOYEE")

        if not primary_employee.employment_info:
            raise DomainError("Primary employee must have employment info")

        if dependent_info.primary_employee_id != primary_employee.id:
            raise DomainError(
                "Dependent info primary_employee_id must match provided primary_employee"
            )

        now = utc_now()
        person = cls(
            id=id,
            tenant_id=tenant_id,
            person_type=PersonType.DEPENDENT,
            is_dual_role=False,
            user_id=user_id,
            profile=profile,
            dependent_info=dependent_info,
            family_id=primary_employee.family_id or primary_employee.id,
            status=BaseStatus.PENDING,
            created_at=now,
            updated_at=now,
        )
        person._ensure_invariants()
        return person

    def _ensure_invariants(self) -> None:
        """Ensure person invariants are met"""
        if not self.id:
            raise InvariantViolation("Person must have an ID")
        if not self.tenant_id:
            raise InvariantViolation("Person must have a tenant ID")
        if not self.user_id:
            raise InvariantViolation("Person must have a user ID")

        if self.person_type == PersonType.DEPENDENT:
            if not self.dependent_info:
                raise InvariantViolation("Dependents must have dependent info")
            if self.is_dual_role:
                raise InvariantViolation("Dependents cannot have dual roles")
            if not self.family_id:
                raise InvariantViolation("Dependents must have a family_id (primary employee)")

        if self.person_type == PersonType.SERVICE_PROVIDER:
            if not self.license_info:
                raise InvariantViolation("Service providers must have license info")

        if self.person_type == PersonType.CLIENT_EMPLOYEE:
            if not self.employment_info:
                raise InvariantViolation("Client employees must have employment info")

        if self.person_type == PersonType.PLATFORM_STAFF:
            if not self.staff_info:
                raise InvariantViolation("Platform staff must have staff info")

        # Secondary role invariants
        if self.is_dual_role and self.secondary_person_type:
            if self.secondary_person_type == PersonType.CLIENT_EMPLOYEE:
                if not self.employment_info:
                    raise InvariantViolation(
                        "Secondary CLIENT_EMPLOYEE role requires employment info"
                    )
            elif self.secondary_person_type == PersonType.SERVICE_PROVIDER:
                if not self.license_info:
                    raise InvariantViolation(
                        "Secondary SERVICE_PROVIDER role requires license info"
                    )
            elif self.secondary_person_type == PersonType.PLATFORM_STAFF:
                if not self.staff_info:
                    raise InvariantViolation("Secondary PLATFORM_STAFF role requires staff info")

    # === Public Properties ===

    def clear_events(self) -> None:
        self.events.clear()
