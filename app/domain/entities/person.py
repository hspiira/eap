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
from app.domain.value_objects.core import PersonId, TenantId, UserId, EmploymentInfo, LicenseInfo, StaffInfo, DependentInfo, EmergencyContact
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
        self._updated_at = utc_now()
        self._events.append(PersonActivated(occurred_at=utc_now(), person_id=self._id, person_type=self._person_type))
    
    def deactivate(self, reason: str | None = None) -> None:
        """Deactivate person"""
        if self._status == BaseStatus.DELETED:
            raise DomainError("Cannot deactivate deleted person")
        if self._status == BaseStatus.INACTIVE:
            raise DomainError("Person is already inactive")
        self._status = BaseStatus.INACTIVE
        self._updated_at = utc_now()
        self._events.append(PersonDeactivated(occurred_at=utc_now(), person_id=self._id, reason=reason))
    
    def terminate(self, reason: str) -> None:
        """Permanently terminate person"""
        if not reason:
            raise DomainError("Termination requires reason")
        if self._status == BaseStatus.DELETED:
            raise DomainError("Person is already terminated")
        self._status = BaseStatus.DELETED
        self._deleted_at = utc_now()
        self._updated_at = utc_now()
        self._events.append(PersonTerminated(occurred_at=utc_now(), person_id=self._id, reason=reason))
    
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
        
        # Map role to appropriate info attribute
        if role == PersonType.CLIENT_EMPLOYEE:
            if not isinstance(info, EmploymentInfo):
                raise DomainError(f"CLIENT_EMPLOYEE role requires EmploymentInfo, got {type(info).__name__}")
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
        self._updated_at = utc_now()
        self._ensure_invariants()
        self._events.append(PersonSecondaryRoleAdded(occurred_at=utc_now(), person_id=self._id, role=role))
    
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
        self._updated_at = utc_now()
        self._ensure_invariants()
        self._events.append(PersonSecondaryRoleRemoved(occurred_at=utc_now(), person_id=self._id, role=removed_role))
    
    def update_emergency_contact(self, contact: EmergencyContact) -> None:
        """Update emergency contact information."""
        self._emergency_contact = contact
        self._updated_at = utc_now()
    
    def update_employment_info(self, info: EmploymentInfo) -> None:
        """Update employment information."""
        if self._status == BaseStatus.DELETED:
            raise DomainError("Cannot update employment info for deleted person")
        self._employment_info = info
        self._updated_at = utc_now()
        self._ensure_invariants()
    
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
        """Archive person (softer than terminate)"""
        if self._status == BaseStatus.DELETED:
            raise DomainError("Cannot archive deleted person")
        if self._status == BaseStatus.ARCHIVED:
            raise DomainError("Person is already archived")
        self._status = BaseStatus.ARCHIVED
        self._updated_at = utc_now()
    
    def restore(self) -> None:
        """Restore archived or soft-deleted person"""
        if self._status == BaseStatus.DELETED:
            raise DomainError("Cannot restore deleted person")
        # Check if person is already active and not deleted
        if self._status == BaseStatus.ACTIVE and self._deleted_at is None:
            raise DomainError("Person is already active and does not need restoration")
        # Restore soft-deleted person
        if self._deleted_at:
            self._deleted_at = None
        # Restore archived person
        if self._status == BaseStatus.ARCHIVED:
            self._status = BaseStatus.ACTIVE
        self._updated_at = utc_now()
    
    # === Factory Methods ===
    
    @classmethod
    def create_client_employee(cls, id: PersonId, tenant_id: TenantId, user_id: UserId, profile: UserEntity, employment_info: EmploymentInfo) -> 'PersonEntity':
        """Factory for CLIENT_EMPLOYEE type"""
        now = utc_now()
        person = cls(
            _id=id,
            _tenant_id=tenant_id,
            _person_type=PersonType.CLIENT_EMPLOYEE,
            _is_dual_role=False,
            _user_id=user_id,
            _profile=profile,
            _employment_info=employment_info,
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
    
    
    def _ensure_invariants(self) -> None:
        """Ensure person invariants are met"""
        if not self._id:
            raise InvariantViolation("Person must have an ID")
        if not self._tenant_id:
            raise InvariantViolation("Person must have a tenant ID")
        if not self._user_id:
            raise InvariantViolation("Person must have a user ID")
        
        # Type-specific invariants for primary role
        if self._person_type == PersonType.DEPENDENT:
            if not self._dependent_info:
                raise InvariantViolation("Dependents must have dependent info")
            if self._is_dual_role:
                raise InvariantViolation("Dependents cannot have dual roles")
        
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