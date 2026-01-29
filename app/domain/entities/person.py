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
from datetime import datetime, date
from typing import Union
from app.domain.value_objects.core import PersonId, TenantId, UserId, ClientId, EmploymentInfo, LicenseInfo, StaffInfo, DependentInfo, EmergencyContact
from app.domain.entities.user import UserEntity
from app.domain.enums import PersonType, BaseStatus
from app.domain.events import (
    DomainEvent,
    PersonActivated,
    PersonDeactivated,
    PersonTerminated,
    PersonSecondaryRoleAdded,
    PersonSecondaryRoleRemoved,
)
from app.domain.exceptions import DomainError, InvariantViolation
from app.shared.utils.datetime import utc_now

# Error messages
_DEPENDENT_DUAL_ROLE_ERROR = "Dependents cannot have dual roles"

@dataclass
class PersonEntity:
    # Required fields (no defaults)
    _id: PersonId
    _tenant_id: TenantId
    _person_type: PersonType
    _is_dual_role: bool
    _user_id: UserId
    _profile: UserEntity  # Entity inside aggregate
    _status: BaseStatus
    _created_at: datetime
    _updated_at: datetime

    # Optional fields with defaults
    _secondary_person_type: PersonType | None = None
    _employment_info: EmploymentInfo | None = None  # CLIENT_EMPLOYEE
    _license_info: LicenseInfo | None = None  # SERVICE_PROVIDER
    _staff_info: StaffInfo | None = None  # PLATFORM_STAFF
    _dependent_info: DependentInfo | None = None  # DEPENDENT
    _emergency_contact: EmergencyContact | None = None
    _family_id: PersonId | None = None  # Points to primary employee in family (for family code grouping)
    _last_service_date: date | None = None
    _deleted_at: datetime | None = None
    _events: list[DomainEvent] = field(default_factory=list)
    
    # === Behaviors ===
    
    def activate(self) -> None:
        """Activate person for operation"""
        if self._status == BaseStatus.DELETED:
            raise DomainError("Cannot activate deleted person")
        if self._status == BaseStatus.ACTIVE:
            raise DomainError("Person is already active")
        self._status = BaseStatus.ACTIVE
        now = utc_now()
        self._updated_at = now
        self._events.append(PersonActivated(occurred_at=now, person_id=self._id, person_type=self._person_type))
    
    def deactivate(self, reason: str | None = None) -> None:
        """Deactivate person"""
        if self._status == BaseStatus.DELETED:
            raise DomainError("Cannot deactivate deleted person")
        if self._status == BaseStatus.INACTIVE:
            raise DomainError("Person is already inactive")
        self._status = BaseStatus.INACTIVE
        now = utc_now()
        self._updated_at = now
        self._events.append(PersonDeactivated(occurred_at=now, person_id=self._id, reason=reason))
    
    def terminate(self, reason: str) -> None:
        """Permanently terminate person"""
        if not reason:
            raise DomainError("Termination requires reason")
        if self._status == BaseStatus.DELETED:
            raise DomainError("Person is already terminated")
        self._status = BaseStatus.DELETED
        now = utc_now()
        self._deleted_at = now
        self._updated_at = now
        self._events.append(PersonTerminated(occurred_at=now, person_id=self._id, reason=reason))
    
    def is_eligible_for_services(self) -> bool:
        """Complex eligibility based on person type"""
        if self._status != BaseStatus.ACTIVE:
            return False
        
        if self._person_type == PersonType.CLIENT_EMPLOYEE:
            return self._employment_info is not None and self._employment_info.is_active()
        
        if self._person_type == PersonType.DEPENDENT:
            # Dependent eligibility via primary employee
            return self._dependent_info is not None and self._dependent_info.is_eligible()
        
        if self._person_type == PersonType.SERVICE_PROVIDER:
            return self._license_info is not None and self._license_info.is_valid()
        
        return True  # PLATFORM_STAFF
    
    def add_secondary_role(
        self, 
        role: PersonType, 
        info: Union[EmploymentInfo, LicenseInfo, StaffInfo]
    ) -> None:
        """Add a secondary role to the person with role-specific information.
        
        Args:
            role: The secondary person type to add
            info: The role-specific value object (EmploymentInfo, LicenseInfo, or StaffInfo)
            
        Raises:
            DomainError: If the person is a dependent, role matches primary, or role/info mismatch
        """
        if self._person_type == PersonType.DEPENDENT:
            raise DomainError(_DEPENDENT_DUAL_ROLE_ERROR)
        
        if role == PersonType.DEPENDENT:
            raise DomainError("Cannot add dependent as secondary role")
        
        if role == self._person_type:
            raise DomainError(f"Cannot add {role.value} as secondary role when it is already the primary role")
        
        # Check max 2 clients rule for CLIENT_EMPLOYEE roles
        if role == PersonType.CLIENT_EMPLOYEE:
            if not isinstance(info, EmploymentInfo):
                raise DomainError(f"CLIENT_EMPLOYEE role requires EmploymentInfo, got {type(info).__name__}")
            self._check_max_clients_rule(info.client_id)
            self._employment_info = info
        elif role == PersonType.SERVICE_PROVIDER:
            if not isinstance(info, LicenseInfo):
                raise DomainError(f"SERVICE_PROVIDER role requires LicenseInfo, got {type(info).__name__}")
            self._license_info = info
        elif role == PersonType.PLATFORM_STAFF:
            if not isinstance(info, StaffInfo):
                raise DomainError(f"PLATFORM_STAFF role requires StaffInfo, got {type(info).__name__}")
            self._staff_info = info
        else:
            raise DomainError(f"Invalid secondary role: {role}")
        
        self._is_dual_role = True
        self._secondary_person_type = role
        now = utc_now()
        self._updated_at = now
        self._ensure_invariants()
        self._events.append(PersonSecondaryRoleAdded(occurred_at=now, person_id=self._id, role=role))
    
    def remove_secondary_role(self) -> None:
        """Remove the secondary role from the person.
        
        Raises:
            DomainError: If the person doesn't have a secondary role
        """
        if not self._is_dual_role or not self._secondary_person_type:
            raise DomainError("Person does not have a secondary role to remove")
        
        # Clear role-specific info based on secondary role
        if self._secondary_person_type == PersonType.CLIENT_EMPLOYEE:
            # Only clear if it's not the primary role
            if self._person_type != PersonType.CLIENT_EMPLOYEE:
                self._employment_info = None
        elif self._secondary_person_type == PersonType.SERVICE_PROVIDER:
            if self._person_type != PersonType.SERVICE_PROVIDER:
                self._license_info = None
        elif self._secondary_person_type == PersonType.PLATFORM_STAFF:
            if self._person_type != PersonType.PLATFORM_STAFF:
                self._staff_info = None
        
        removed_role = self._secondary_person_type
        self._is_dual_role = False
        self._secondary_person_type = None
        now = utc_now()
        self._updated_at = now
        self._ensure_invariants()
        self._events.append(PersonSecondaryRoleRemoved(occurred_at=now, person_id=self._id, role=removed_role))
    
    def update_emergency_contact(self, contact: EmergencyContact) -> None:
        """Update emergency contact information."""
        if self._status == BaseStatus.DELETED:
            raise DomainError("Cannot update emergency contact for deleted person")
        self._emergency_contact = contact
        now = utc_now()
        self._updated_at = now
    
    def update_employment_info(self, info: EmploymentInfo) -> None:
        """Update employment information."""
        if self._status == BaseStatus.DELETED:
            raise DomainError("Cannot update employment info for deleted person")
        if self._employment_info and self._employment_info.client_id != info.client_id:
            self._check_max_clients_rule(info.client_id)
        self._employment_info = info
        self._updated_at = utc_now()
        self._ensure_invariants()
    
    def _check_max_clients_rule(self, new_client_id: ClientId) -> None:
        """Check that person is not already employee/dependent for more than 1 client."""
        clients = set()
        
        if self._person_type == PersonType.CLIENT_EMPLOYEE and self._employment_info:
            clients.add(self._employment_info.client_id)
        elif self._person_type == PersonType.DEPENDENT and self._dependent_info:
            pass
        
        if self._secondary_person_type == PersonType.CLIENT_EMPLOYEE and self._employment_info:
            clients.add(self._employment_info.client_id)
        
        if new_client_id in clients:
            return
        
        if len(clients) >= 2:
            raise DomainError("Person cannot be employee or dependent for more than 2 clients")
    
    def update_license_info(self, info: LicenseInfo) -> None:
        """Update license information."""
        if self._status == BaseStatus.DELETED:
            raise DomainError("Cannot update license info for deleted person")
        self._license_info = info
        self._updated_at = utc_now()
        self._ensure_invariants()
    
    def update_staff_info(self, info: StaffInfo) -> None:
        """Update staff information."""
        if self._status == BaseStatus.DELETED:
            raise DomainError("Cannot update staff info for deleted person")
        self._staff_info = info
        self._updated_at = utc_now()
        self._ensure_invariants()
    
    def archive(self) -> None:
        """Archive person (softer than terminate).
        
        Sets status to ARCHIVED. This is reversible via restore().
        Note: archive() does NOT set _deleted_at; only terminate() does.
        """
        if self._status == BaseStatus.DELETED:
            raise DomainError("Cannot archive deleted person")
        if self._status == BaseStatus.ARCHIVED:
            raise DomainError("Person is already archived")
        self._status = BaseStatus.ARCHIVED
        self._updated_at = utc_now()
    
    def restore(self) -> None:
        """Restore archived person to active status.
        
        Only restores from ARCHIVED to ACTIVE. Terminated persons (DELETED status)
        cannot be restored as termination is permanent.
        """
        if self._status == BaseStatus.DELETED:
            raise DomainError("Cannot restore deleted person")
        if self._status == BaseStatus.ACTIVE:
            raise DomainError("Person is already active")
        if self._status != BaseStatus.ARCHIVED:
            raise DomainError("Person must be archived to restore")
        self._status = BaseStatus.ACTIVE
        self._updated_at = utc_now()
    
    # === Factory Methods ===
    
    @classmethod
    def create_client_employee(cls, id: PersonId, tenant_id: TenantId, user_id: UserId, profile: UserEntity, employment_info: EmploymentInfo, family_id: PersonId | None = None) -> 'PersonEntity':
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
            _id=id,
            _tenant_id=tenant_id,
            _person_type=PersonType.CLIENT_EMPLOYEE,
            _is_dual_role=False,
            _user_id=user_id,
            _profile=profile,
            _employment_info=employment_info,
            _family_id=family_id,  # Set family_id if part of existing family
            _status=BaseStatus.PENDING,
            _created_at=now,
            _updated_at=now
        )
        person._ensure_invariants()
        return person
    
    @classmethod
    def create_service_provider(cls, id: PersonId, tenant_id: TenantId, user_id: UserId, profile: UserEntity, license_info: LicenseInfo) -> 'PersonEntity':
        """Factory for SERVICE_PROVIDER type"""
        now = utc_now()
        person = cls(
            _id=id,
            _tenant_id=tenant_id,
            _person_type=PersonType.SERVICE_PROVIDER,
            _is_dual_role=False,
            _user_id=user_id,
            _profile=profile,
            _license_info=license_info,
            _status=BaseStatus.PENDING,
            _created_at=now,
            _updated_at=now
        )
        person._ensure_invariants()
        return person
    
    @classmethod
    def create_dependent(cls, id: PersonId, tenant_id: TenantId, user_id: UserId, profile: UserEntity, dependent_info: DependentInfo, primary_employee: 'PersonEntity') -> 'PersonEntity':
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
        if primary_employee._person_type != PersonType.CLIENT_EMPLOYEE:
            raise DomainError("Primary employee must be a CLIENT_EMPLOYEE")
        
        if not primary_employee._employment_info:
            raise DomainError("Primary employee must have employment info")
        
        if dependent_info.primary_employee_id != primary_employee._id:
            raise DomainError("Dependent info primary_employee_id must match provided primary_employee")
        
        now = utc_now()
        person = cls(
            _id=id,
            _tenant_id=tenant_id,
            _person_type=PersonType.DEPENDENT,
            _is_dual_role=False,
            _user_id=user_id,
            _profile=profile,
            _dependent_info=dependent_info,
            _family_id=primary_employee._family_id or primary_employee._id,
            _status=BaseStatus.PENDING,
            _created_at=now,
            _updated_at=now
        )
        person._ensure_invariants()
        return person
    
    
    def _ensure_invariants(self) -> None:
        """Ensure person invariants are met"""
        if not self._id:
            raise InvariantViolation("Person must have an ID")
        if not self._tenant_id:
            raise InvariantViolation("Person must have a tenant ID")
        if not self._user_id:
            raise InvariantViolation("Person must have a user ID")
        
        if self._person_type == PersonType.DEPENDENT:
            if not self._dependent_info:
                raise InvariantViolation("Dependents must have dependent info")
            if self._is_dual_role:
                raise InvariantViolation("Dependents cannot have dual roles")
            if not self._family_id:
                raise InvariantViolation("Dependents must have a family_id (primary employee)")
        
        if self._person_type == PersonType.SERVICE_PROVIDER:
            if not self._license_info:
                raise InvariantViolation("Service providers must have license info")
        
        if self._person_type == PersonType.CLIENT_EMPLOYEE:
            if not self._employment_info:
                raise InvariantViolation("Client employees must have employment info")
        
        if self._person_type == PersonType.PLATFORM_STAFF:
            if not self._staff_info:
                raise InvariantViolation("Platform staff must have staff info")
        
        # Secondary role invariants
        if self._is_dual_role and self._secondary_person_type:
            if self._secondary_person_type == PersonType.CLIENT_EMPLOYEE:
                if not self._employment_info:
                    raise InvariantViolation("Secondary CLIENT_EMPLOYEE role requires employment info")
            elif self._secondary_person_type == PersonType.SERVICE_PROVIDER:
                if not self._license_info:
                    raise InvariantViolation("Secondary SERVICE_PROVIDER role requires license info")
            elif self._secondary_person_type == PersonType.PLATFORM_STAFF:
                if not self._staff_info:
                    raise InvariantViolation("Secondary PLATFORM_STAFF role requires staff info")

    # === Public Properties ===

    @property
    def id(self) -> PersonId:
        return self._id

    @property
    def tenant_id(self) -> TenantId:
        return self._tenant_id

    @property
    def person_type(self) -> PersonType:
        return self._person_type

    @property
    def is_dual_role(self) -> bool:
        return self._is_dual_role

    @property
    def user_id(self) -> UserId:
        return self._user_id

    @property
    def profile(self) -> UserEntity:
        return self._profile

    @property
    def status(self) -> BaseStatus:
        return self._status

    @property
    def secondary_person_type(self) -> PersonType | None:
        return self._secondary_person_type

    @property
    def employment_info(self) -> EmploymentInfo | None:
        return self._employment_info

    @property
    def license_info(self) -> LicenseInfo | None:
        return self._license_info

    @property
    def staff_info(self) -> StaffInfo | None:
        return self._staff_info

    @property
    def dependent_info(self) -> DependentInfo | None:
        return self._dependent_info

    @property
    def emergency_contact(self) -> EmergencyContact | None:
        return self._emergency_contact

    @property
    def last_service_date(self) -> date | None:
        return self._last_service_date

    @property
    def family_id(self) -> PersonId | None:
        return self._family_id

    @property
    def created_at(self) -> datetime:
        return self._created_at

    @property
    def updated_at(self) -> datetime:
        return self._updated_at

    @property
    def deleted_at(self) -> datetime | None:
        return self._deleted_at

    @property
    def events(self) -> list[DomainEvent]:
        return list(self._events)

    def clear_events(self) -> None:
        self._events.clear()