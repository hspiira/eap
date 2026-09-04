"""
User Entity (Aggregate Root)

Represents an authenticated user account.
Scoped to a Tenant for multi-tenancy.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta

from app.domain.enums import AccessScope, AuthProvider, Language, TenantRole, UserStatus
from app.domain.events import (
    DomainEvent,
    UserActivated,
    UserBanned,
    UserDeactivated,
    UserEmailVerified,
    UserLockedOut,
    UserLockoutCleared,
    UserLoginFailed,
    UserSuspended,
    UserTerminated,
)
from app.domain.exceptions import DomainError, InvariantViolation
from app.domain.value_objects.core import Email, TenantId, UserId
from app.shared.utils.datetime import utc_now


@dataclass
class UserEntity:
    # Required fields (no defaults)
    id: UserId
    tenant_id: TenantId  # Multi-tenancy scope
    email: Email  # Value Object
    status: UserStatus
    is_two_factor_enabled: bool
    created_at: datetime
    updated_at: datetime

    # Optional fields (with defaults)
    _password_hash: str | None = None
    email_verified_at: datetime | None = None
    status_changed_at: datetime | None = None
    preferred_language: Language | None = None
    timezone: str | None = None
    last_login_at: datetime | None = None
    deleted_at: datetime | None = None
    role: TenantRole = TenantRole.USER
    failed_login_count: int = 0
    locked_until: datetime | None = None
    azure_oid: str | None = None
    auth_provider: AuthProvider = AuthProvider.PASSWORD
    display_name: str | None = None
    access_scopes: list[AccessScope] = field(default_factory=list[AccessScope])
    events: list[DomainEvent] = field(default_factory=list[DomainEvent])

    def __post_init__(self) -> None:
        """Validate invariants immediately after construction."""
        self._ensure_invariants()

    # === Behaviors ===

    def verify_email(self) -> None:
        now = utc_now()
        self.email_verified_at = now
        if self.status == UserStatus.PENDING_VERIFICATION:
            self.activate()
        self.events.append(UserEmailVerified(occurred_at=now, user_id=self.id))

    def activate(self) -> None:
        if self.status in (UserStatus.BANNED, UserStatus.TERMINATED):
            raise DomainError("Cannot activate banned or terminated user")
        self.status = UserStatus.ACTIVE
        now = utc_now()
        self.status_changed_at = now
        self.updated_at = now
        self.events.append(UserActivated(occurred_at=now, user_id=self.id))

    def suspend(self, reason: str) -> None:
        if not reason:
            raise DomainError("Suspension requires reason")
        self.status = UserStatus.SUSPENDED
        now = utc_now()
        self.status_changed_at = now
        self.updated_at = now
        self.events.append(UserSuspended(occurred_at=now, user_id=self.id, reason=reason))

    def ban(self, reason: str) -> None:
        if not reason:
            raise DomainError("Ban requires reason")
        if self.status == UserStatus.TERMINATED:
            raise DomainError("Cannot ban terminated user")
        self.status = UserStatus.BANNED
        now = utc_now()
        self.status_changed_at = now
        self.updated_at = now
        self.events.append(UserBanned(occurred_at=now, user_id=self.id, reason=reason))

    def deactivate(self, reason: str | None = None) -> None:
        """Deactivate user"""
        if self.status in (UserStatus.BANNED, UserStatus.TERMINATED):
            raise DomainError("Cannot deactivate banned or terminated user")
        if self.status == UserStatus.INACTIVE:
            raise DomainError("User is already inactive")
        self.status = UserStatus.INACTIVE
        now = utc_now()
        self.status_changed_at = now
        self.updated_at = now
        self.events.append(UserDeactivated(occurred_at=now, user_id=self.id, reason=reason))

    def terminate(self, reason: str) -> None:
        """Permanently terminate user"""
        if not reason:
            raise DomainError("Termination requires reason")
        if self.status == UserStatus.TERMINATED:
            raise DomainError("User is already terminated")
        self.status = UserStatus.TERMINATED
        now = utc_now()
        self.status_changed_at = now
        self.updated_at = now
        self.deleted_at = now
        self.events.append(UserTerminated(occurred_at=now, user_id=self.id, reason=reason))

    def update_password(self, password_hash: str) -> None:
        """Update user password"""
        if not password_hash:
            raise DomainError("Password hash cannot be empty")
        if self.deleted_at:
            raise DomainError("Cannot update password for deleted user")
        self._password_hash = password_hash
        self.updated_at = utc_now()

    def update_preferences(
        self,
        preferred_language: Language | None = None,
        timezone: str | None = None,
    ) -> None:
        """Update user preferences"""
        if self.deleted_at:
            raise DomainError("Cannot update preferences for deleted user")
        if preferred_language is not None:
            self.preferred_language = preferred_language
        if timezone is not None:
            self.timezone = timezone
        self.updated_at = utc_now()

    def enable_two_factor(self) -> None:
        """Enable two-factor authentication"""
        if self.deleted_at:
            raise DomainError("Cannot enable 2FA for deleted user")
        if self.is_two_factor_enabled:
            raise DomainError("Two-factor authentication is already enabled")
        self.is_two_factor_enabled = True
        self.updated_at = utc_now()

    def disable_two_factor(self) -> None:
        """Disable two-factor authentication"""
        if self.deleted_at:
            raise DomainError("Cannot disable 2FA for deleted user")
        if not self.is_two_factor_enabled:
            raise DomainError("Two-factor authentication is not enabled")
        self.is_two_factor_enabled = False
        self.updated_at = utc_now()

    def record_login(self) -> None:
        """Record user login"""
        self.last_login_at = utc_now()
        self.updated_at = utc_now()

    def is_locked(self, now: datetime | None = None) -> bool:
        """Whether the account is in an active lockout window."""
        if self.locked_until is None:
            return False
        return (now or utc_now()) < self.locked_until

    def record_failed_login(
        self,
        threshold: int,
        lock_duration: timedelta,
        now: datetime | None = None,
    ) -> None:
        """Increment the failed-login counter; lock when the threshold is met.

        Emits ``UserLoginFailed`` on every call and ``UserLockedOut`` when the
        counter reaches ``threshold``. The caller passes policy explicitly so
        the entity stays configuration-free.
        """
        if threshold < 1:
            raise DomainError("Lockout threshold must be >= 1")
        if lock_duration <= timedelta(0):
            raise DomainError("Lockout duration must be positive")

        now = now or utc_now()
        self.failed_login_count += 1
        self.updated_at = now
        self.events.append(
            UserLoginFailed(
                occurred_at=now,
                user_id=self.id,
                failed_count=self.failed_login_count,
            )
        )
        if self.failed_login_count >= threshold:
            self.locked_until = now + lock_duration
            self.events.append(
                UserLockedOut(
                    occurred_at=now,
                    user_id=self.id,
                    locked_until=self.locked_until,
                    failed_count=self.failed_login_count,
                )
            )

    def record_successful_login(self, now: datetime | None = None) -> None:
        """Reset the failed-login counter and clear any lockout.

        A successful login is proof of email ownership, so the email is
        automatically verified here if it has not been already.

        Emits ``UserLockoutCleared`` if the account had been locked.
        """
        now = now or utc_now()
        was_locked = self.locked_until is not None
        self.failed_login_count = 0
        self.locked_until = None
        self.last_login_at = now
        self.updated_at = now
        if not self.email_verified_at:
            self.verify_email()
        if was_locked:
            self.events.append(UserLockoutCleared(occurred_at=now, user_id=self.id))

    def set_access_scopes(self, scopes: list[AccessScope]) -> None:
        """Replace the user's access-scope grants (deduplicated, order-stable)."""
        seen: set[AccessScope] = set()
        deduped: list[AccessScope] = []
        for s in scopes:
            if s not in seen:
                seen.add(s)
                deduped.append(s)
        self.access_scopes = deduped
        self.updated_at = utc_now()

    def link_azure_identity(self, azure_oid: str) -> None:
        """
        Link this user to an Azure AD identity (called on first SSO login).

        Refuses to re-point an account that is already linked to a DIFFERENT
        Azure identity. The SSO callback resolves users by OID first and falls
        back to email; without this guard, an email address recycled by the
        customer's IT department (offboard A, later assign the same address to
        new hire B, routine in most organisations) would silently hand B
        control of A's account: A's role, access scopes, case history and audit
        identity. Re-linking is a deliberate admin action, not something a
        login should perform.

        Re-linking the SAME oid is a no-op and stays allowed, so retried or
        concurrent logins do not fail.
        """
        if not azure_oid or not azure_oid.strip():
            raise DomainError("Azure OID cannot be empty")
        if self.deleted_at:
            raise DomainError("Cannot link Azure identity to deleted user")
        cleaned = azure_oid.strip()
        if self.azure_oid and self.azure_oid != cleaned:
            raise DomainError(
                "User is already linked to a different Azure identity; an administrator must unlink it before re-linking"
            )
        self.azure_oid = cleaned
        self.auth_provider = AuthProvider.AZURE_AD
        self.updated_at = utc_now()

    def update_display_name(self, name: str | None) -> None:
        """Refresh the display name sourced from an external identity provider."""
        if self.deleted_at:
            raise DomainError("Cannot update display name for deleted user")
        cleaned = name.strip() if name else None
        if cleaned == self.display_name:
            return
        self.display_name = cleaned or None
        self.updated_at = utc_now()

    def is_active(self) -> bool:
        """Check if user is active"""
        return self.status == UserStatus.ACTIVE and self.deleted_at is None

    # === Public Properties ===

    @property
    def is_email_verified(self) -> bool:
        """Check if email is verified."""
        return self.email_verified_at is not None

    def clear_events(self) -> None:
        """Clear collected domain events after publishing."""
        self.events.clear()

    # === Invariants ===

    def _ensure_invariants(self) -> None:
        """Ensure user invariants are met"""
        if not self.email:
            raise InvariantViolation("User must have an email")
