"""
Tenant Entity

Represents an isolated organizational boundary within the EAP platform.

Responsibilities:
- Own users and domain data
- Enforce data isolation
- Control tenant lifecycle (active, suspended)
"""

from dataclasses import dataclass, field
from datetime import datetime
from app.domain.value_objects.core import TenantCode, TenantId, TenantSettings
from app.domain.enums import SubscriptionTier, TenantStatus
from app.domain.events import DomainEvent, TenantActivated, TenantSuspended, TenantTerminated
from app.domain.exceptions import DomainError, InvariantViolation
from app.shared.utils.datetime import utc_now


@dataclass
class TenantEntity:
    _id: TenantId
    _name: str
    _code: TenantCode
    _status: TenantStatus
    _settings: TenantSettings
    _subscription_tier: SubscriptionTier
    _deleted_at: datetime | None = None
    _updated_at: datetime | None = None

    # Domain Events
    _events: list[DomainEvent] = field(default_factory=list)

    def __post_init__(self) -> None:
        self._ensure_invariants()

    def activate(self) -> None:
        """Activate tenant for operation"""
        if self._status == TenantStatus.TERMINATED:
            raise DomainError("Cannot activate terminated tenant")
        if self._status == TenantStatus.ACTIVE and self._deleted_at is None:
            raise DomainError("Tenant is already active")
        self._status = TenantStatus.ACTIVE
        if self._deleted_at:
            self._deleted_at = None
        self._updated_at = utc_now()
        self._events.append(TenantActivated(occurred_at=utc_now(), tenant_id=self._id))
    
    def suspend(self, reason: str) -> None:
        """Suspend tenant (e.g., payment issues)"""
        if not reason:
            raise DomainError("Suspension requires reason")
        if self._status == TenantStatus.TERMINATED:
            raise DomainError("Cannot suspend terminated tenant")
        if self._status == TenantStatus.SUSPENDED:
            raise DomainError("Tenant is already suspended")
        self._status = TenantStatus.SUSPENDED
        self._updated_at = utc_now()
        self._events.append(TenantSuspended(occurred_at=utc_now(), tenant_id=self._id, reason=reason))
    
    def terminate(self, reason: str) -> None:
        """Permanently terminate tenant"""
        if not reason:
            raise DomainError("Termination requires reason")
        if self._status == TenantStatus.TERMINATED:
            raise DomainError("Tenant is already terminated")
        self._status = TenantStatus.TERMINATED
        self._deleted_at = utc_now()
        self._updated_at = utc_now()
        self._events.append(TenantTerminated(occurred_at=utc_now(), tenant_id=self._id, reason=reason))
    
    def update_settings(self, settings: TenantSettings) -> None:
        """Update tenant configuration"""
        if self._status == TenantStatus.TERMINATED:
            raise DomainError("Cannot update settings for terminated tenant")
        self._settings = settings
        self._updated_at = utc_now()
    
    def update_name(self, name: str) -> None:
        """Update tenant name"""
        if not name:
            raise DomainError("Tenant name cannot be empty")
        if self._status == TenantStatus.TERMINATED:
            raise DomainError("Cannot update name for terminated tenant")
        self._name = name
        self._updated_at = utc_now()
    
    def update_subscription_tier(self, tier: SubscriptionTier) -> None:
        """Update subscription tier"""
        if self._status == TenantStatus.TERMINATED:
            raise DomainError("Cannot update subscription tier for terminated tenant")
        self._subscription_tier = tier
        self._updated_at = utc_now()
    
    def archive(self) -> None:
        """Archive tenant (softer than terminate)"""
        if self._status == TenantStatus.TERMINATED:
            raise DomainError("Cannot archive terminated tenant")
        if self._status == TenantStatus.ARCHIVED:
            raise DomainError("Tenant is already archived")
        self._status = TenantStatus.ARCHIVED
        self._updated_at = utc_now()
    
    def restore(self) -> None:
        """Restore archived or soft-deleted tenant"""
        if self._status == TenantStatus.TERMINATED:
            raise DomainError("Cannot restore terminated tenant")
        # Check if tenant is already active and not deleted
        if self._status == TenantStatus.ACTIVE and self._deleted_at is None:
            raise DomainError("Tenant is already active and does not need restoration")
        # Restore soft-deleted tenant
        if self._deleted_at:
            self._deleted_at = None
        # Restore archived tenant
        if self._status == TenantStatus.ARCHIVED:
            self._status = TenantStatus.ACTIVE
        self._updated_at = utc_now()
    
    def is_active(self) -> bool:
        """Check if tenant is operational"""
        return self._status == TenantStatus.ACTIVE and self._deleted_at is None
    
    def can_create_users(self, current_user_count: int) -> bool:
        """Check if tenant can create new users based on subscription and settings"""
        return self.is_active() and self._settings.allows_more_users(current_user_count)
    
    # === Invariants ===
    
    def collect_events(self) -> list[DomainEvent]:
        """
        Collect and clear pending domain events.
        
        Returns:
            List of domain events that occurred
        """
        events = self._events.copy()
        self._events.clear()
        return events
    
    def _ensure_invariants(self) -> None:
        """Ensure tenant invariants are met"""
        if not self._code:
            raise InvariantViolation("Tenant must have a code")
        if not self._name:
            raise InvariantViolation("Tenant must have a name")