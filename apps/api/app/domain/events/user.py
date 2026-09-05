"""Domain events for the user bounded context."""

from dataclasses import dataclass
from datetime import datetime

from app.domain.events.base import DomainEvent
from app.domain.value_objects.core import UserId


@dataclass(frozen=True)
class UserActivated(DomainEvent):
    """Event raised when a user is activated."""

    user_id: UserId


@dataclass(frozen=True)
class UserSuspended(DomainEvent):
    """Event raised when a user is suspended."""

    user_id: UserId
    reason: str


@dataclass(frozen=True)
class UserBanned(DomainEvent):
    """Event raised when a user is banned."""

    user_id: UserId
    reason: str


@dataclass(frozen=True)
class UserEmailVerified(DomainEvent):
    """Event raised when a user's email is verified."""

    user_id: UserId


@dataclass(frozen=True)
class UserDeactivated(DomainEvent):
    """Event raised when a user is deactivated."""

    user_id: UserId
    reason: str | None = None


@dataclass(frozen=True)
class UserTerminated(DomainEvent):
    """Event raised when a user is terminated."""

    user_id: UserId
    reason: str


@dataclass(frozen=True)
class UserLoginFailed(DomainEvent):
    """Raised on every failed login attempt; carries the running counter."""

    user_id: UserId
    failed_count: int


@dataclass(frozen=True)
class UserLockedOut(DomainEvent):
    """Raised when the failed-login counter crosses the lockout threshold."""

    user_id: UserId
    locked_until: datetime
    failed_count: int


@dataclass(frozen=True)
class UserLockoutCleared(DomainEvent):
    """Raised when a previously-locked account logs in successfully."""

    user_id: UserId


# === Contract Events ===
