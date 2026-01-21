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
from app.domain.value_objects.core import PersonId, TenantId, UserId, EmploymentInfo, LicenseInfo, StaffInfo, DependentInfo, EmergencyContact
from app.domain.entities.user import UserEntity
from app.domain.enums import PersonType, BaseStatus
from app.domain.events import DomainEvent, PersonActivated, PersonDeactivated, PersonTerminated
from app.domain.exceptions import DomainError, InvariantViolation
from app.shared.utils.datetime import utc_now

@dataclass
class PersonEntity:
    # Identity
    _id: PersonId
    _tenant_id: TenantId
    
    # Type discriminator
    _person_type: PersonType
    _is_dual_role: bool
    _secondary_person_type: PersonType | None = None
    
    # Core relationships
    _user_id: UserId
    _profile: UserEntity  # Entity inside aggregate
    
    # Type-specific (use Value Objects)
    _employment_info: EmploymentInfo | None = None  # CLIENT_EMPLOYEE
    _license_info: LicenseInfo | None = None  # SERVICE_PROVIDER
    _staff_info: StaffInfo | None = None  # PLATFORM_STAFF
    _dependent_info: DependentInfo | None = None  # DEPENDENT
    
    # Shared
    _status: BaseStatus
    _emergency_contact: EmergencyContact | None = None
    _last_service_date: date | None = None
    
    # Audit
    _created_at: datetime
    _updated_at: datetime
    _deleted_at: datetime | None = None
    
    _events: list[DomainEvent] = field(default_factory=list)
    
    # === Behaviors ===
    
    def activate(self) -> None:
        self._ensure_can_activate()
        self._status = BaseStatus.ACTIVE
        self._events.append(PersonActivated(occurred_at=utc_now(), person_id=self._id, person_type=self._person_type))
    
    def is_eligible_for_services(self) -> bool:
        """Complex eligibility based on person type"""
        if self._status != BaseStatus.ACTIVE:
            return False
        
        if self._person_type == PersonType.CLIENT_EMPLOYEE:
            return self._employment_info and self._employment_info.is_active()
        
        if self._person_type == PersonType.DEPENDENT:
            # Dependent eligibility via primary employee
            return self._dependent_info and self._dependent_info.is_eligible()
        
        if self._person_type == PersonType.SERVICE_PROVIDER:
            return self._license_info and self._license_info.is_valid()
        
        return True  # PLATFORM_STAFF
    
    def add_secondary_role(self, role: PersonType, **fields) -> None:
        if self._person_type == PersonType.DEPENDENT:
            raise DomainError("Dependents cannot have dual roles")
        self._is_dual_role = True
        self._secondary_person_type = role
        self._ensure_invariants()
    
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
    
    def _ensure_can_activate(self) -> None:
        """Ensure person can be activated"""
        if self._status == BaseStatus.DELETED:
            raise DomainError("Cannot activate deleted person")
    
    def _ensure_invariants(self) -> None:
        """Ensure person invariants are met"""
        if not self._id:
            raise InvariantViolation("Person must have an ID")
        if not self._tenant_id:
            raise InvariantViolation("Person must have a tenant ID")
        if not self._user_id:
            raise InvariantViolation("Person must have a user ID")
        
        # Type-specific invariants
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