"""
KPI Entity (Aggregate Root)

Represents a Key Performance Indicator definition.
KPIs can be assigned to clients or contracts for tracking.
"""

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal

from app.domain.enums import KPICategory, KPIMeasurementUnit
from app.domain.exceptions import DomainError, InvariantViolation
from app.domain.value_objects.core import KPIId, KPIAssignmentId, TenantId
from app.shared.utils.datetime import utc_now


@dataclass
class KPIEntity:
    # Required fields
    _id: KPIId
    _tenant_id: TenantId
    _name: str
    _category: KPICategory
    _measurement_unit: KPIMeasurementUnit
    _created_at: datetime
    _updated_at: datetime
    
    # Optional fields
    _description: str | None = None
    _target_value: Decimal | None = None  # Target value for the KPI
    _threshold_min: Decimal | None = None  # Minimum acceptable value
    _threshold_max: Decimal | None = None  # Maximum acceptable value
    _formula: str | None = None  # Calculation formula (optional)
    _is_active: bool = True
    _deleted_at: datetime | None = None
    _events: list = field(default_factory=list)  # Domain events
    
    def __post_init__(self) -> None:
        """Validate invariants immediately after construction."""
        self._ensure_invariants()
    
    # === Behaviors ===
    
    def update_definition(
        self,
        name: str | None = None,
        description: str | None = None,
        target_value: Decimal | None = None,
        threshold_min: Decimal | None = None,
        threshold_max: Decimal | None = None,
        formula: str | None = None,
    ) -> None:
        """Update KPI definition."""
        if self._deleted_at:
            raise DomainError("Cannot update deleted KPI")
        
        if name:
            self._name = name
        if description is not None:
            self._description = description
        if target_value is not None:
            self._target_value = target_value
        if threshold_min is not None:
            self._threshold_min = threshold_min
        if threshold_max is not None:
            self._threshold_max = threshold_max
        if formula is not None:
            self._formula = formula
        
        self._updated_at = utc_now()
        
        # Validate thresholds after update
        self._ensure_invariants()
    
    def activate(self) -> None:
        """Activate KPI."""
        if self._deleted_at:
            raise DomainError("Cannot activate deleted KPI")
        if self._is_active:
            raise DomainError("KPI is already active")
        self._is_active = True
        self._updated_at = utc_now()
    
    def deactivate(self) -> None:
        """Deactivate KPI."""
        if self._deleted_at:
            raise DomainError("Cannot deactivate deleted KPI")
        if not self._is_active:
            raise DomainError("KPI is already inactive")
        self._is_active = False
        self._updated_at = utc_now()
    
    def is_active(self) -> bool:
        """Check if KPI is active."""
        return self._is_active and self._deleted_at is None
    
    # === Invariants ===
    
    def _ensure_invariants(self) -> None:
        """Ensure KPI invariants are met."""
        if not self._name:
            raise InvariantViolation("KPI must have a name")
        if self._threshold_min is not None and self._threshold_max is not None:
            if self._threshold_min > self._threshold_max:
                raise InvariantViolation(
                    "Minimum threshold cannot be greater than maximum threshold"
                )
        if self._target_value is not None:
            if self._threshold_min is not None and self._target_value < self._threshold_min:
                raise InvariantViolation(
                    "Target value cannot be less than minimum threshold"
                )
            if self._threshold_max is not None and self._target_value > self._threshold_max:
                raise InvariantViolation(
                    "Target value cannot be greater than maximum threshold"
                )

    # === Public Properties ===

    @property
    def id(self) -> KPIId:
        return self._id

    @property
    def tenant_id(self) -> TenantId:
        return self._tenant_id

    @property
    def name(self) -> str:
        return self._name

    @property
    def category(self) -> KPICategory:
        return self._category

    @property
    def measurement_unit(self) -> KPIMeasurementUnit:
        return self._measurement_unit

    @property
    def description(self) -> str | None:
        return self._description

    @property
    def target_value(self) -> Decimal | None:
        return self._target_value

    @property
    def threshold_min(self) -> Decimal | None:
        return self._threshold_min

    @property
    def threshold_max(self) -> Decimal | None:
        return self._threshold_max

    @property
    def formula(self) -> str | None:
        return self._formula

    @property
    def created_at(self) -> datetime:
        return self._created_at

    @property
    def updated_at(self) -> datetime:
        return self._updated_at

    @property
    def deleted_at(self) -> datetime | None:
        return self._deleted_at


@dataclass
class KPIAssignmentEntity:
    """
    KPI Assignment Entity
    
    Links a KPI to a client or contract for tracking.
    This is a separate entity to allow multiple assignments of the same KPI.
    """
    # Required fields
    _id: KPIAssignmentId
    _kpi_id: KPIId
    _tenant_id: TenantId
    _created_at: datetime
    _updated_at: datetime
    
    # Optional fields - one of client_id or contract_id must be provided
    _client_id: str | None = None
    _contract_id: str | None = None
    _target_value: Decimal | None = None  # Override KPI target for this assignment
    _is_active: bool = True
    _deleted_at: datetime | None = None
    _events: list = field(default_factory=list)
    
    def __post_init__(self) -> None:
        """Validate invariants immediately after construction."""
        self._ensure_invariants()
    
    # === Behaviors ===
    
    def update_target(self, target_value: Decimal | None) -> None:
        """Update assignment-specific target value."""
        if self._deleted_at:
            raise DomainError("Cannot update deleted assignment")
        self._target_value = target_value
        self._updated_at = utc_now()
    
    def activate(self) -> None:
        """Activate assignment."""
        if self._deleted_at:
            raise DomainError("Cannot activate deleted assignment")
        if self._is_active:
            raise DomainError("Assignment is already active")
        self._is_active = True
        self._updated_at = utc_now()
    
    def deactivate(self) -> None:
        """Deactivate assignment."""
        if self._deleted_at:
            raise DomainError("Cannot deactivate deleted assignment")
        if not self._is_active:
            raise DomainError("Assignment is already inactive")
        self._is_active = False
        self._updated_at = utc_now()
    
    def is_active(self) -> bool:
        """Check if assignment is active."""
        return self._is_active and self._deleted_at is None
    
    # === Invariants ===
    
    def _ensure_invariants(self) -> None:
        """Ensure assignment invariants are met."""
        if not self._client_id and not self._contract_id:
            raise InvariantViolation(
                "Assignment must be associated with either a client or contract"
            )
        if self._client_id and self._contract_id:
            raise InvariantViolation(
                "Assignment cannot be associated with both client and contract"
            )

    # === Public Properties ===

    @property
    def id(self) -> KPIAssignmentId:
        return self._id

    @property
    def kpi_id(self) -> KPIId:
        return self._kpi_id

    @property
    def tenant_id(self) -> TenantId:
        return self._tenant_id

    @property
    def client_id(self) -> str | None:
        return self._client_id

    @property
    def contract_id(self) -> str | None:
        return self._contract_id

    @property
    def target_value(self) -> Decimal | None:
        return self._target_value

    @property
    def created_at(self) -> datetime:
        return self._created_at

    @property
    def updated_at(self) -> datetime:
        return self._updated_at

    @property
    def deleted_at(self) -> datetime | None:
        return self._deleted_at
