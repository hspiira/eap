"""
User Entity (Aggregate Root)

Represents an authenticated user account.
Scoped to a Tenant for multi-tenancy.
"""

from dataclasses import dataclass, field
from datetime import datetime
from app.domain.value_objects.core import Email, TenantId, UserId
from app.domain.enums import UserStatus, Language, TenantRole
from app.domain.events import DomainEvent, UserActivated, UserSuspended, UserBanned, UserEmailVerified, UserDeactivated, UserTerminated
from app.domain.exceptions import DomainError, InvariantViolation
from app.shared.utils.datetime import utc_now

@dataclass
class UserEntity:
    # Required fields (no defaults)
    _id: UserId
    _tenant_id: TenantId  # Multi-tenancy scope
    _email: Email  # Value Object
    _status: UserStatus
    _is_two_factor_enabled: bool
    _created_at: datetime
    _updated_at: datetime
    
    # Optional fields (with defaults)
    _password_hash: str | None = None
    _email_verified_at: datetime | None = None
    _status_changed_at: datetime | None = None
    _preferred_language: Language | None = None
    _timezone: str | None = None
    _last_login_at: datetime | None = None
    _deleted_at: datetime | None = None
    _role: TenantRole = TenantRole.USER
    _events: list[DomainEvent] = field(default_factory=list)
    
    def __post_init__(self) -> None:
        """Validate invariants immediately after construction."""
        self._ensure_invariants()
    
    # === Behaviors ===
    
    def verify_email(self) -> None:
        now = utc_now()
        self._email_verified_at = now
        if self._status == UserStatus.PENDING_VERIFICATION:
            self.activate()
        self._events.append(UserEmailVerified(occurred_at=now, user_id=self._id))
    
    def activate(self) -> None:
        if self._status in (UserStatus.BANNED, UserStatus.TERMINATED):
            raise DomainError("Cannot activate banned or terminated user")
        self._status = UserStatus.ACTIVE
        now = utc_now()
        self._status_changed_at = now
        self._updated_at = now
        self._events.append(UserActivated(occurred_at=now, user_id=self._id))
    
    def suspend(self, reason: str) -> None:
        if not reason:
            raise DomainError("Suspension requires reason")
        self._status = UserStatus.SUSPENDED
        now = utc_now()
        self._status_changed_at = now
        self._updated_at = now
        self._events.append(UserSuspended(occurred_at=now, user_id=self._id, reason=reason))
    
    def ban(self, reason: str) -> None:
        if not reason:
            raise DomainError("Ban requires reason")
        if self._status == UserStatus.TERMINATED:
            raise DomainError("Cannot ban terminated user")
        self._status = UserStatus.BANNED
        now = utc_now()
        self._status_changed_at = now
        self._updated_at = now
        self._events.append(UserBanned(occurred_at=now, user_id=self._id, reason=reason))
    
    def deactivate(self, reason: str | None = None) -> None:
        """Deactivate user"""
        if self._status in (UserStatus.BANNED, UserStatus.TERMINATED):
            raise DomainError("Cannot deactivate banned or terminated user")
        if self._status == UserStatus.INACTIVE:
            raise DomainError("User is already inactive")
        self._status = UserStatus.INACTIVE
        now = utc_now()
        self._status_changed_at = now
        self._updated_at = now
        self._events.append(UserDeactivated(occurred_at=now, user_id=self._id, reason=reason))
    
    def terminate(self, reason: str) -> None:
        """Permanently terminate user"""
        if not reason:
            raise DomainError("Termination requires reason")
        if self._status == UserStatus.TERMINATED:
            raise DomainError("User is already terminated")
        self._status = UserStatus.TERMINATED
        now = utc_now()
        self._status_changed_at = now
        self._updated_at = now
        self._deleted_at = now
        self._events.append(UserTerminated(occurred_at=now, user_id=self._id, reason=reason))
    
    def update_password(self, password_hash: str) -> None:
        """Update user password"""
        if not password_hash:
            raise DomainError("Password hash cannot be empty")
        if self._deleted_at:
            raise DomainError("Cannot update password for deleted user")
        self._password_hash = password_hash
        self._updated_at = utc_now()
    
    def update_preferences(
        self,
        preferred_language: Language | None = None,
        timezone: str | None = None,
    ) -> None:
        """Update user preferences"""
        if self._deleted_at:
            raise DomainError("Cannot update preferences for deleted user")
        if preferred_language is not None:
            self._preferred_language = preferred_language
        if timezone is not None:
            self._timezone = timezone
        self._updated_at = utc_now()
    
    def enable_two_factor(self) -> None:
        """Enable two-factor authentication"""
        if self._deleted_at:
            raise DomainError("Cannot enable 2FA for deleted user")
        if self._is_two_factor_enabled:
            raise DomainError("Two-factor authentication is already enabled")
        self._is_two_factor_enabled = True
        self._updated_at = utc_now()
    
    def disable_two_factor(self) -> None:
        """Disable two-factor authentication"""
        if self._deleted_at:
            raise DomainError("Cannot disable 2FA for deleted user")
        if not self._is_two_factor_enabled:
            raise DomainError("Two-factor authentication is not enabled")
        self._is_two_factor_enabled = False
        self._updated_at = utc_now()
    
    def record_login(self) -> None:
        """Record user login"""
        self._last_login_at = utc_now()
        self._updated_at = utc_now()
    
    def is_active(self) -> bool:
        """Check if user is active"""
        return self._status == UserStatus.ACTIVE and self._deleted_at is None
    
    # === Public Properties ===
    
    @property
    def id(self) -> UserId:
        """Get user ID."""
        return self._id
    
    @property
    def tenant_id(self) -> TenantId:
        """Get tenant ID."""
        return self._tenant_id
    
    @property
    def email(self) -> Email:
        """Get user email."""
        return self._email
    
    @property
    def status(self) -> UserStatus:
        """Get user status."""
        return self._status
    
    @property
    def is_two_factor_enabled(self) -> bool:
        """Check if two-factor authentication is enabled."""
        return self._is_two_factor_enabled
    
    @property
    def email_verified_at(self) -> datetime | None:
        """Get email verification timestamp."""
        return self._email_verified_at
    
    @property
    def is_email_verified(self) -> bool:
        """Check if email is verified."""
        return self._email_verified_at is not None
    
    @property
    def preferred_language(self) -> Language | None:
        """Get preferred language."""
        return self._preferred_language
    
    @property
    def timezone(self) -> str | None:
        """Get timezone."""
        return self._timezone
    
    @property
    def last_login_at(self) -> datetime | None:
        """Get last login timestamp."""
        return self._last_login_at
    
    @property
    def status_changed_at(self) -> datetime | None:
        """Get status change timestamp."""
        return self._status_changed_at
    
    @property
    def created_at(self) -> datetime:
        """Get creation timestamp."""
        return self._created_at
    
    @property
    def updated_at(self) -> datetime:
        """Get last update timestamp."""
        return self._updated_at
    
    @property
    def deleted_at(self) -> datetime | None:
        """Get deletion timestamp."""
        return self._deleted_at

    @property
    def role(self) -> TenantRole:
        """Get tenant role for RBAC."""
        return self._role

    @property
    def events(self) -> list[DomainEvent]:
        """Get domain events (read-only copy)."""
        return list(self._events)
    
    def clear_events(self) -> None:
        """Clear collected domain events after publishing."""
        self._events.clear()
    
    # === Invariants ===
    
    def _ensure_invariants(self) -> None:
        """Ensure user invariants are met"""
        if not self._email:
            raise InvariantViolation("User must have an email")
