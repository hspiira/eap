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
from typing import Optional
from app.domain.value_objects.core import TenantCode, TenantId, TenantSettings
from app.domain.enums import SubscriptionTier, TenantStatus
from app.domain.events import DomainEvent, TenantActivated, TenantSuspended, TenantTerminated
from app.domain.exceptions import DomainError, InvariantViolation
from app.shared.utils.datetime import utc_now


@dataclass
class TenantEntity:
    _id: TenantId
    _name: str
    _slug: str
    _code: TenantCode
    _status: TenantStatus
    _settings: TenantSettings
    _subscription_tier: SubscriptionTier
    _deleted_at: Optional[datetime] = None
    _updated_at: Optional[datetime] = None

    # Domain Events
    _events: list[DomainEvent] = field(default_factory=list)

    def activate(self) -> None:
        """Activate tenant for operation"""
        if self._status == TenantStatus.TERMINATED:
            raise DomainError("Cannot activate terminated tenant")
        self._status = TenantStatus.ACTIVE
        self._events.append(TenantActivated(occurred_at=utc_now(), tenant_id=self._id))
    
    def suspend(self, reason: str) -> None:
        """Suspend tenant (e.g., payment issues)"""
        if not reason:
            raise DomainError("Suspension requires reason")
        self._status = TenantStatus.SUSPENDED
        self._events.append(TenantSuspended(occurred_at=utc_now(), tenant_id=self._id, reason=reason))
    
    def terminate(self, reason: str) -> None:
        """Permanently terminate tenant"""
        self._status = TenantStatus.TERMINATED
        self._deleted_at = utc_now()
        self._events.append(TenantTerminated(occurred_at=utc_now(), tenant_id=self._id, reason=reason))
    
    def update_settings(self, settings: TenantSettings) -> None:
        """Update tenant configuration"""
        self._settings = settings
        self._updated_at = utc_now()
    
    def is_active(self) -> bool:
        """Check if tenant is operational"""
        return self._status == TenantStatus.ACTIVE and self._deleted_at is None
    
    def can_create_users(self, current_user_count: int) -> bool:
        """Check if tenant can create new users based on subscription and settings"""
        return self.is_active() and self._settings.allows_more_users(current_user_count)
    
    # === Invariants ===
    
    def _ensure_invariants(self) -> None:
        if not self._name:
            raise InvariantViolation("Tenant must have a name")
        if not self._slug:
            raise InvariantViolation("Tenant must have a slug")
        if not self._slug.islower() or ' ' in self._slug:
            raise InvariantViolation("Slug must be lowercase with no spaces")