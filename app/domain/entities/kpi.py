"""
KPI Entity (Aggregate Root)

Represents a Key Performance Indicator definition.
KPIs can be assigned to clients or contracts for tracking.
"""

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal

from app.domain.enums import KPICategory, KPIMeasurementUnit
from app.domain.events import DomainEvent
from app.domain.exceptions import DomainError, InvariantViolation
from app.domain.value_objects.core import ClientId, ContractId, KPIId, KPIAssignmentId, TenantId
from app.shared.utils.datetime import utc_now


@dataclass
class KPIEntity:
    # Required fields
    id: KPIId
    tenant_id: TenantId
    name: str
    category: KPICategory
    measurement_unit: KPIMeasurementUnit
    created_at: datetime
    updated_at: datetime
    
    # Optional fields
    description: str | None = None
    target_value: Decimal | None = None  # Target value for the KPI
    threshold_min: Decimal | None = None  # Minimum acceptable value
    threshold_max: Decimal | None = None  # Maximum acceptable value
    formula: str | None = None  # Calculation formula (optional)
    _is_active: bool = True
    deleted_at: datetime | None = None
    _events: list[DomainEvent] = field(default_factory=list)  # Domain events
    
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
        if self.deleted_at:
            raise DomainError("Cannot update deleted KPI")
        
        if name:
            self.name = name
        if description is not None:
            self.description = description
        if target_value is not None:
            self.target_value = target_value
        if threshold_min is not None:
            self.threshold_min = threshold_min
        if threshold_max is not None:
            self.threshold_max = threshold_max
        if formula is not None:
            self.formula = formula
        
        self.updated_at = utc_now()
        
        # Validate thresholds after update
        self._ensure_invariants()
    
    def activate(self) -> None:
        """Activate KPI."""
        if self.deleted_at:
            raise DomainError("Cannot activate deleted KPI")
        if self._is_active:
            raise DomainError("KPI is already active")
        self._is_active = True
        self.updated_at = utc_now()
    
    def deactivate(self) -> None:
        """Deactivate KPI."""
        if self.deleted_at:
            raise DomainError("Cannot deactivate deleted KPI")
        if not self._is_active:
            raise DomainError("KPI is already inactive")
        self._is_active = False
        self.updated_at = utc_now()
    
    def is_active(self) -> bool:
        """Check if KPI is active."""
        return self._is_active and self.deleted_at is None
    
    # === Invariants ===
    
    def _ensure_invariants(self) -> None:
        """Ensure KPI invariants are met."""
        if not self.name:
            raise InvariantViolation("KPI must have a name")
        if self.threshold_min is not None and self.threshold_max is not None:
            if self.threshold_min > self.threshold_max:
                raise InvariantViolation(
                    "Minimum threshold cannot be greater than maximum threshold"
                )
        if self.target_value is not None:
            if self.threshold_min is not None and self.target_value < self.threshold_min:
                raise InvariantViolation(
                    "Target value cannot be less than minimum threshold"
                )
            if self.threshold_max is not None and self.target_value > self.threshold_max:
                raise InvariantViolation(
                    "Target value cannot be greater than maximum threshold"
                )

    # === Public Properties ===

@dataclass
class KPIAssignmentEntity:
    """
    KPI Assignment Entity
    
    Links a KPI to a client or contract for tracking.
    This is a separate entity to allow multiple assignments of the same KPI.
    """
    # Required fields
    id: KPIAssignmentId
    kpi_id: KPIId
    tenant_id: TenantId
    created_at: datetime
    updated_at: datetime
    
    # Optional fields - one of client_id or contract_id must be provided
    client_id: ClientId | None = None
    contract_id: ContractId | None = None
    target_value: Decimal | None = None  # Override KPI target for this assignment
    _is_active: bool = True
    deleted_at: datetime | None = None
    _events: list[DomainEvent] = field(default_factory=list)
    
    def __post_init__(self) -> None:
        """Validate invariants immediately after construction."""
        self._ensure_invariants()
    
    # === Behaviors ===
    
    def update_target(self, target_value: Decimal | None) -> None:
        """Update assignment-specific target value."""
        if self.deleted_at:
            raise DomainError("Cannot update deleted assignment")
        self.target_value = target_value
        self.updated_at = utc_now()
    
    def activate(self) -> None:
        """Activate assignment."""
        if self.deleted_at:
            raise DomainError("Cannot activate deleted assignment")
        if self._is_active:
            raise DomainError("Assignment is already active")
        self._is_active = True
        self.updated_at = utc_now()
    
    def deactivate(self) -> None:
        """Deactivate assignment."""
        if self.deleted_at:
            raise DomainError("Cannot deactivate deleted assignment")
        if not self._is_active:
            raise DomainError("Assignment is already inactive")
        self._is_active = False
        self.updated_at = utc_now()
    
    def is_active(self) -> bool:
        """Check if assignment is active."""
        return self._is_active and self.deleted_at is None
    
    # === Invariants ===
    
    def _ensure_invariants(self) -> None:
        """Ensure assignment invariants are met."""
        if not self.client_id and not self.contract_id:
            raise InvariantViolation(
                "Assignment must be associated with either a client or contract"
            )
        if self.client_id and self.contract_id:
            raise InvariantViolation(
                "Assignment cannot be associated with both client and contract"
            )

    # === Public Properties ===

