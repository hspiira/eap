"""
User Entity (Aggregate Root)

Represents an authenticated user account.
Scoped to a Tenant for multi-tenancy.
"""

from dataclasses import dataclass, field
from datetime import datetime
from app.domain.value_objects.core import Email, TenantId, UserId
from app.domain.enums import UserStatus, Language
from app.domain.events import DomainEvent, UserActivated, UserSuspended, UserBanned, UserEmailVerified, UserDeactivated, UserTerminated
from app.domain.exceptions import DomainError, InvariantViolation
from app.shared.utils.datetime import utc_now

@dataclass
class UserEntity:
    # Identity
    _id: UserId
    _tenant_id: TenantId  # Multi-tenancy scope
    
    # Authentication
    _email: Email  # Value Object
    _password_hash: str | None = None
    _email_verified_at: datetime | None = None
    
    # Status
    _status: UserStatus
    _status_changed_at: datetime | None = None
    
    # Preferences
    _preferred_language: Language | None = None
    _timezone: str | None = None
    
    # Security
    _is_two_factor_enabled: bool
    _last_login_at: datetime | None = None
    
    # Audit
    _created_at: datetime
    _updated_at: datetime
    _deleted_at: datetime | None = None
    
    # Events
    _events: list[DomainEvent] = field(default_factory=list)
    
    # === Behaviors ===
    
    def verify_email(self) -> None:
        self._email_verified_at = utc_now()
        if self._status == UserStatus.PENDING_VERIFICATION:
            self.activate()
        self._events.append(UserEmailVerified(occurred_at=utc_now(), user_id=self._id))
    
    def activate(self) -> None:
        if self._status == UserStatus.BANNED:
            raise DomainError("Cannot activate banned user")
        self._status = UserStatus.ACTIVE
        self._status_changed_at = utc_now()
        self._events.append(UserActivated(occurred_at=utc_now(), user_id=self._id))
    
    def suspend(self, reason: str) -> None:
        if not reason:
            raise DomainError("Suspension requires reason")
        self._status = UserStatus.SUSPENDED
        self._status_changed_at = utc_now()
        self._events.append(UserSuspended(occurred_at=utc_now(), user_id=self._id, reason=reason))
    
    def ban(self, reason: str) -> None:
        if not reason:
            raise DomainError("Ban requires reason")
        self._status = UserStatus.BANNED
        self._status_changed_at = utc_now()
        self._events.append(UserBanned(occurred_at=utc_now(), user_id=self._id, reason=reason))
    
    def record_login(self) -> None:
        self._last_login_at = utc_now()
    
    def is_active(self) -> bool:
        return self._status == UserStatus.ACTIVE and self._deleted_at is None
    
    # === Invariants ===
    
    def _ensure_invariants(self) -> None:
        """Ensure user invariants are met"""
        if not self._email:
            raise InvariantViolation("User must have an email")
        # Note: password_hash may be None for OAuth users or pending users