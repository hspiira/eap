"""
Unit tests for UserEntity domain entity.

Tests domain logic and invariants without database dependencies.
"""

import pytest
from datetime import datetime, UTC

from app.domain.entities.user import UserEntity
from app.domain.enums import UserStatus, Language
from app.domain.exceptions import DomainError, InvariantViolation
from app.domain.value_objects.core import UserId, TenantId, Email
from app.domain.events import (
    UserActivated,
    UserSuspended,
    UserBanned,
    UserDeactivated,
    UserTerminated,
    UserEmailVerified,
)


# =============================================================================
# FIXTURES
# =============================================================================


@pytest.fixture
def user_id() -> UserId:
    return UserId("user-123")


@pytest.fixture
def tenant_id() -> TenantId:
    return TenantId("tenant-456")


@pytest.fixture
def email() -> Email:
    return Email("test@example.com")


@pytest.fixture
def now() -> datetime:
    return datetime.now(UTC)


@pytest.fixture
def pending_user(user_id, tenant_id, email, now) -> UserEntity:
    """Create a user in pending verification status."""
    return UserEntity(
        _id=user_id,
        _tenant_id=tenant_id,
        _email=email,
        _status=UserStatus.PENDING_VERIFICATION,
        _is_two_factor_enabled=False,
        _created_at=now,
        _updated_at=now,
    )


@pytest.fixture
def active_user(user_id, tenant_id, email, now) -> UserEntity:
    """Create an active user."""
    return UserEntity(
        _id=user_id,
        _tenant_id=tenant_id,
        _email=email,
        _status=UserStatus.ACTIVE,
        _is_two_factor_enabled=False,
        _created_at=now,
        _updated_at=now,
    )


@pytest.fixture
def banned_user(user_id, tenant_id, email, now) -> UserEntity:
    """Create a banned user."""
    return UserEntity(
        _id=user_id,
        _tenant_id=tenant_id,
        _email=email,
        _status=UserStatus.BANNED,
        _is_two_factor_enabled=False,
        _created_at=now,
        _updated_at=now,
    )


# =============================================================================
# CREATION TESTS
# =============================================================================


class TestUserCreation:
    """Tests for user entity creation."""

    def test_create_user_success(self, user_id, tenant_id, email, now):
        """Test successful user creation."""
        user = UserEntity(
            _id=user_id,
            _tenant_id=tenant_id,
            _email=email,
            _status=UserStatus.PENDING_VERIFICATION,
            _is_two_factor_enabled=False,
            _created_at=now,
            _updated_at=now,
        )

        assert user._id == user_id
        assert user._tenant_id == tenant_id
        assert user._email == email
        assert user._status == UserStatus.PENDING_VERIFICATION
        assert user._is_two_factor_enabled is False

    def test_create_user_without_email_raises_invariant_violation(
        self, user_id, tenant_id, now
    ):
        """Test that creating user without email raises InvariantViolation."""
        with pytest.raises(InvariantViolation, match="User must have an email"):
            UserEntity(
                _id=user_id,
                _tenant_id=tenant_id,
                _email=None,
                _status=UserStatus.PENDING_VERIFICATION,
                _is_two_factor_enabled=False,
                _created_at=now,
                _updated_at=now,
            )


# =============================================================================
# ACTIVATION TESTS
# =============================================================================


class TestUserActivation:
    """Tests for user activation behavior."""

    def test_activate_pending_user(self, pending_user):
        """Test activating a pending user."""
        pending_user.activate()

        assert pending_user._status == UserStatus.ACTIVE
        assert pending_user._status_changed_at is not None
        assert any(isinstance(e, UserActivated) for e in pending_user._events)

    def test_activate_banned_user_raises_error(self, banned_user):
        """Test that activating a banned user raises DomainError."""
        with pytest.raises(DomainError, match="Cannot activate banned user"):
            banned_user.activate()


# =============================================================================
# SUSPENSION TESTS
# =============================================================================


class TestUserSuspension:
    """Tests for user suspension behavior."""

    def test_suspend_active_user(self, active_user):
        """Test suspending an active user."""
        active_user.suspend("Policy violation")

        assert active_user._status == UserStatus.SUSPENDED
        assert active_user._status_changed_at is not None
        assert any(isinstance(e, UserSuspended) for e in active_user._events)

    def test_suspend_without_reason_raises_error(self, active_user):
        """Test that suspending without reason raises DomainError."""
        with pytest.raises(DomainError, match="Suspension requires reason"):
            active_user.suspend("")


# =============================================================================
# BAN TESTS
# =============================================================================


class TestUserBan:
    """Tests for user ban behavior."""

    def test_ban_user(self, active_user):
        """Test banning a user."""
        active_user.ban("Security violation")

        assert active_user._status == UserStatus.BANNED
        assert active_user._status_changed_at is not None
        assert any(isinstance(e, UserBanned) for e in active_user._events)

    def test_ban_without_reason_raises_error(self, active_user):
        """Test that banning without reason raises DomainError."""
        with pytest.raises(DomainError, match="Ban requires reason"):
            active_user.ban("")


# =============================================================================
# DEACTIVATION TESTS
# =============================================================================


class TestUserDeactivation:
    """Tests for user deactivation behavior."""

    def test_deactivate_active_user(self, active_user):
        """Test deactivating an active user."""
        active_user.deactivate("User requested")

        assert active_user._status == UserStatus.INACTIVE
        assert any(isinstance(e, UserDeactivated) for e in active_user._events)

    def test_deactivate_banned_user_raises_error(self, banned_user):
        """Test that deactivating a banned user raises DomainError."""
        with pytest.raises(DomainError, match="Cannot deactivate banned user"):
            banned_user.deactivate()

    def test_deactivate_already_inactive_raises_error(self, user_id, tenant_id, email, now):
        """Test that deactivating already inactive user raises DomainError."""
        inactive_user = UserEntity(
            _id=user_id,
            _tenant_id=tenant_id,
            _email=email,
            _status=UserStatus.INACTIVE,
            _is_two_factor_enabled=False,
            _created_at=now,
            _updated_at=now,
        )

        with pytest.raises(DomainError, match="User is already inactive"):
            inactive_user.deactivate()


# =============================================================================
# TERMINATION TESTS
# =============================================================================


class TestUserTermination:
    """Tests for user termination behavior."""

    def test_terminate_user(self, active_user):
        """Test terminating a user."""
        active_user.terminate("Account closed")

        assert active_user._status == UserStatus.TERMINATED
        assert active_user._deleted_at is not None
        assert any(isinstance(e, UserTerminated) for e in active_user._events)

    def test_terminate_without_reason_raises_error(self, active_user):
        """Test that terminating without reason raises DomainError."""
        with pytest.raises(DomainError, match="Termination requires reason"):
            active_user.terminate("")

    def test_terminate_terminated_user_raises_error(self, active_user):
        """Test that terminating already terminated user raises DomainError."""
        active_user.terminate("First termination")
        with pytest.raises(DomainError, match="User is already terminated"):
            active_user.terminate("Double termination attempt")


# =============================================================================
# EMAIL VERIFICATION TESTS
# =============================================================================


class TestEmailVerification:
    """Tests for email verification behavior."""

    def test_verify_email(self, pending_user):
        """Test verifying user email."""
        pending_user.verify_email()

        assert pending_user._email_verified_at is not None
        assert any(isinstance(e, UserEmailVerified) for e in pending_user._events)

    def test_verify_email_auto_activates_pending_user(self, pending_user):
        """Test that verifying email auto-activates pending user."""
        pending_user.verify_email()

        assert pending_user._status == UserStatus.ACTIVE


# =============================================================================
# PASSWORD TESTS
# =============================================================================


class TestPasswordUpdate:
    """Tests for password update behavior."""

    def test_update_password(self, active_user):
        """Test updating user password."""
        active_user.update_password("new-hash-123")

        assert active_user._password_hash == "new-hash-123"

    def test_update_password_empty_raises_error(self, active_user):
        """Test that updating with empty password raises DomainError."""
        with pytest.raises(DomainError, match="Password hash cannot be empty"):
            active_user.update_password("")

    def test_update_password_deleted_user_raises_error(self, active_user):
        """Test that updating password for deleted user raises DomainError."""
        active_user._deleted_at = datetime.now(UTC)

        with pytest.raises(DomainError, match="Cannot update password for deleted user"):
            active_user.update_password("new-hash")


# =============================================================================
# PREFERENCES TESTS
# =============================================================================


class TestPreferencesUpdate:
    """Tests for preferences update behavior."""

    def test_update_language_preference(self, active_user):
        """Test updating language preference."""
        active_user.update_preferences(preferred_language=Language.SPANISH)

        assert active_user._preferred_language == Language.SPANISH

    def test_update_timezone_preference(self, active_user):
        """Test updating timezone preference."""
        active_user.update_preferences(timezone="America/New_York")

        assert active_user._timezone == "America/New_York"

    def test_update_preferences_deleted_user_raises_error(self, active_user):
        """Test that updating preferences for deleted user raises DomainError."""
        active_user._deleted_at = datetime.now(UTC)

        with pytest.raises(DomainError, match="Cannot update preferences for deleted user"):
            active_user.update_preferences(timezone="UTC")


# =============================================================================
# TWO-FACTOR AUTHENTICATION TESTS
# =============================================================================


class TestTwoFactorAuth:
    """Tests for two-factor authentication behavior."""

    def test_enable_two_factor(self, active_user):
        """Test enabling two-factor authentication."""
        active_user.enable_two_factor()

        assert active_user._is_two_factor_enabled is True

    def test_enable_two_factor_when_already_enabled_raises_error(self, active_user):
        """Test that enabling 2FA when already enabled raises DomainError."""
        active_user._is_two_factor_enabled = True

        with pytest.raises(DomainError, match="Two-factor authentication is already enabled"):
            active_user.enable_two_factor()

    def test_disable_two_factor(self, active_user):
        """Test disabling two-factor authentication."""
        active_user._is_two_factor_enabled = True
        active_user.disable_two_factor()

        assert active_user._is_two_factor_enabled is False

    def test_disable_two_factor_when_not_enabled_raises_error(self, active_user):
        """Test that disabling 2FA when not enabled raises DomainError."""
        with pytest.raises(DomainError, match="Two-factor authentication is not enabled"):
            active_user.disable_two_factor()


# =============================================================================
# HELPER METHOD TESTS
# =============================================================================


class TestHelperMethods:
    """Tests for helper methods."""

    def test_is_active_returns_true_for_active_user(self, active_user):
        """Test is_active returns True for active user."""
        assert active_user.is_active() is True

    def test_is_active_returns_false_for_inactive_user(self, pending_user):
        """Test is_active returns False for non-active user."""
        assert pending_user.is_active() is False

    def test_is_active_returns_false_for_deleted_user(self, active_user):
        """Test is_active returns False for deleted user."""
        active_user._deleted_at = datetime.now(UTC)

        assert active_user.is_active() is False

    def test_record_login(self, active_user):
        """Test recording user login."""
        active_user.record_login()

        assert active_user._last_login_at is not None
