"""
Unit tests for User use cases.

Tests application logic with mocked repositories.
"""

import pytest
from datetime import datetime, UTC
from unittest.mock import AsyncMock, MagicMock

from app.application.use_cases.user_use_cases import (
    CreateUserUseCase,
    ActivateUserUseCase,
    VerifyUserEmailUseCase,
    SuspendUserUseCase,
    BanUserUseCase,
    DeactivateUserUseCase,
    TerminateUserUseCase,
    UpdateUserPasswordUseCase,
    UpdateUserPreferencesUseCase,
    EnableTwoFactorUseCase,
    DisableTwoFactorUseCase,
    RecordUserLoginUseCase,
    GetUserUseCase,
)
from app.domain.entities.user import UserEntity
from app.domain.enums import UserStatus, Language
from app.domain.exceptions import DomainError
from app.domain.value_objects.core import UserId, TenantId, Email


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
def mock_user_repo():
    """Create a mock user repository."""
    repo = MagicMock()
    repo.get_by_id = AsyncMock()
    repo.get_by_email = AsyncMock()
    repo.save = AsyncMock()
    repo.list_all = AsyncMock()
    repo.count = AsyncMock()
    return repo


@pytest.fixture
def active_user(user_id, tenant_id, email, now) -> UserEntity:
    """Create an active user entity."""
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
def pending_user(user_id, tenant_id, email, now) -> UserEntity:
    """Create a pending user entity."""
    return UserEntity(
        _id=user_id,
        _tenant_id=tenant_id,
        _email=email,
        _status=UserStatus.PENDING_VERIFICATION,
        _is_two_factor_enabled=False,
        _created_at=now,
        _updated_at=now,
    )


# =============================================================================
# CREATE USER USE CASE TESTS
# =============================================================================


class TestCreateUserUseCase:
    """Tests for CreateUserUseCase."""

    @pytest.mark.asyncio
    async def test_create_user_success(self, mock_user_repo, user_id, tenant_id, email):
        """Test successful user creation."""
        mock_user_repo.get_by_email.return_value = None

        use_case = CreateUserUseCase(mock_user_repo)
        user = await use_case.execute(
            user_id=user_id,
            tenant_id=tenant_id,
            email=email,
            password_hash="hashed-password",
        )

        assert user._id == user_id
        assert user._email == email
        assert user._status == UserStatus.PENDING_VERIFICATION
        mock_user_repo.save.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_user_duplicate_email_raises_error(
        self, mock_user_repo, user_id, tenant_id, email, active_user
    ):
        """Test that creating user with existing email raises ValueError."""
        mock_user_repo.get_by_email.return_value = active_user

        use_case = CreateUserUseCase(mock_user_repo)

        with pytest.raises(ValueError, match="already exists"):
            await use_case.execute(
                user_id=user_id,
                tenant_id=tenant_id,
                email=email,
            )


# =============================================================================
# ACTIVATE USER USE CASE TESTS
# =============================================================================


class TestActivateUserUseCase:
    """Tests for ActivateUserUseCase."""

    @pytest.mark.asyncio
    async def test_activate_user_success(self, mock_user_repo, user_id, pending_user):
        """Test successful user activation."""
        mock_user_repo.get_by_id.return_value = pending_user

        use_case = ActivateUserUseCase(mock_user_repo)
        user = await use_case.execute(user_id)

        assert user._status == UserStatus.ACTIVE
        mock_user_repo.save.assert_called_once()

    @pytest.mark.asyncio
    async def test_activate_user_not_found_raises_error(self, mock_user_repo, user_id):
        """Test that activating non-existent user raises ValueError."""
        mock_user_repo.get_by_id.return_value = None

        use_case = ActivateUserUseCase(mock_user_repo)

        with pytest.raises(ValueError, match="not found"):
            await use_case.execute(user_id)


# =============================================================================
# VERIFY EMAIL USE CASE TESTS
# =============================================================================


class TestVerifyUserEmailUseCase:
    """Tests for VerifyUserEmailUseCase."""

    @pytest.mark.asyncio
    async def test_verify_email_success(self, mock_user_repo, user_id, pending_user):
        """Test successful email verification."""
        mock_user_repo.get_by_id.return_value = pending_user

        use_case = VerifyUserEmailUseCase(mock_user_repo)
        user = await use_case.execute(user_id)

        assert user._email_verified_at is not None
        mock_user_repo.save.assert_called_once()

    @pytest.mark.asyncio
    async def test_verify_email_not_found_raises_error(self, mock_user_repo, user_id):
        """Test that verifying non-existent user raises ValueError."""
        mock_user_repo.get_by_id.return_value = None

        use_case = VerifyUserEmailUseCase(mock_user_repo)

        with pytest.raises(ValueError, match="not found"):
            await use_case.execute(user_id)


# =============================================================================
# SUSPEND USER USE CASE TESTS
# =============================================================================


class TestSuspendUserUseCase:
    """Tests for SuspendUserUseCase."""

    @pytest.mark.asyncio
    async def test_suspend_user_success(self, mock_user_repo, user_id, active_user):
        """Test successful user suspension."""
        mock_user_repo.get_by_id.return_value = active_user

        use_case = SuspendUserUseCase(mock_user_repo)
        user = await use_case.execute(user_id, "Policy violation")

        assert user._status == UserStatus.SUSPENDED
        mock_user_repo.save.assert_called_once()

    @pytest.mark.asyncio
    async def test_suspend_user_not_found_raises_error(self, mock_user_repo, user_id):
        """Test that suspending non-existent user raises ValueError."""
        mock_user_repo.get_by_id.return_value = None

        use_case = SuspendUserUseCase(mock_user_repo)

        with pytest.raises(ValueError, match="not found"):
            await use_case.execute(user_id, "reason")


# =============================================================================
# BAN USER USE CASE TESTS
# =============================================================================


class TestBanUserUseCase:
    """Tests for BanUserUseCase."""

    @pytest.mark.asyncio
    async def test_ban_user_success(self, mock_user_repo, user_id, active_user):
        """Test successful user ban."""
        mock_user_repo.get_by_id.return_value = active_user

        use_case = BanUserUseCase(mock_user_repo)
        user = await use_case.execute(user_id, "Security violation")

        assert user._status == UserStatus.BANNED
        mock_user_repo.save.assert_called_once()

    @pytest.mark.asyncio
    async def test_ban_user_not_found_raises_error(self, mock_user_repo, user_id):
        """Test that banning non-existent user raises ValueError."""
        mock_user_repo.get_by_id.return_value = None

        use_case = BanUserUseCase(mock_user_repo)

        with pytest.raises(ValueError, match="not found"):
            await use_case.execute(user_id, "reason")


# =============================================================================
# DEACTIVATE USER USE CASE TESTS
# =============================================================================


class TestDeactivateUserUseCase:
    """Tests for DeactivateUserUseCase."""

    @pytest.mark.asyncio
    async def test_deactivate_user_success(self, mock_user_repo, user_id, active_user):
        """Test successful user deactivation."""
        mock_user_repo.get_by_id.return_value = active_user

        use_case = DeactivateUserUseCase(mock_user_repo)
        user = await use_case.execute(user_id, "User requested")

        assert user._status == UserStatus.INACTIVE
        mock_user_repo.save.assert_called_once()


# =============================================================================
# TERMINATE USER USE CASE TESTS
# =============================================================================


class TestTerminateUserUseCase:
    """Tests for TerminateUserUseCase."""

    @pytest.mark.asyncio
    async def test_terminate_user_success(self, mock_user_repo, user_id, active_user):
        """Test successful user termination."""
        mock_user_repo.get_by_id.return_value = active_user

        use_case = TerminateUserUseCase(mock_user_repo)
        user = await use_case.execute(user_id, "Account closed")

        assert user._status == UserStatus.TERMINATED
        assert user._deleted_at is not None
        mock_user_repo.save.assert_called_once()


# =============================================================================
# UPDATE PASSWORD USE CASE TESTS
# =============================================================================


class TestUpdateUserPasswordUseCase:
    """Tests for UpdateUserPasswordUseCase."""

    @pytest.mark.asyncio
    async def test_update_password_success(self, mock_user_repo, user_id, active_user):
        """Test successful password update."""
        mock_user_repo.get_by_id.return_value = active_user

        use_case = UpdateUserPasswordUseCase(mock_user_repo)
        user = await use_case.execute(user_id, "new-hash-123")

        assert user._password_hash == "new-hash-123"
        mock_user_repo.save.assert_called_once()


# =============================================================================
# UPDATE PREFERENCES USE CASE TESTS
# =============================================================================


class TestUpdateUserPreferencesUseCase:
    """Tests for UpdateUserPreferencesUseCase."""

    @pytest.mark.asyncio
    async def test_update_preferences_success(self, mock_user_repo, user_id, active_user):
        """Test successful preferences update."""
        mock_user_repo.get_by_id.return_value = active_user

        use_case = UpdateUserPreferencesUseCase(mock_user_repo)
        user = await use_case.execute(
            user_id,
            preferred_language=Language.SPANISH,
            timezone="America/New_York",
        )

        assert user._preferred_language == Language.SPANISH
        assert user._timezone == "America/New_York"
        mock_user_repo.save.assert_called_once()


# =============================================================================
# TWO-FACTOR USE CASE TESTS
# =============================================================================


class TestEnableTwoFactorUseCase:
    """Tests for EnableTwoFactorUseCase."""

    @pytest.mark.asyncio
    async def test_enable_2fa_success(self, mock_user_repo, user_id, active_user):
        """Test successful 2FA enable."""
        mock_user_repo.get_by_id.return_value = active_user

        use_case = EnableTwoFactorUseCase(mock_user_repo)
        user = await use_case.execute(user_id)

        assert user._is_two_factor_enabled is True
        mock_user_repo.save.assert_called_once()


class TestDisableTwoFactorUseCase:
    """Tests for DisableTwoFactorUseCase."""

    @pytest.mark.asyncio
    async def test_disable_2fa_success(self, mock_user_repo, user_id, active_user):
        """Test successful 2FA disable."""
        active_user._is_two_factor_enabled = True
        mock_user_repo.get_by_id.return_value = active_user

        use_case = DisableTwoFactorUseCase(mock_user_repo)
        user = await use_case.execute(user_id)

        assert user._is_two_factor_enabled is False
        mock_user_repo.save.assert_called_once()


# =============================================================================
# RECORD LOGIN USE CASE TESTS
# =============================================================================


class TestRecordUserLoginUseCase:
    """Tests for RecordUserLoginUseCase."""

    @pytest.mark.asyncio
    async def test_record_login_success(self, mock_user_repo, user_id, active_user):
        """Test successful login recording."""
        mock_user_repo.get_by_id.return_value = active_user

        use_case = RecordUserLoginUseCase(mock_user_repo)
        user = await use_case.execute(user_id)

        assert user._last_login_at is not None
        mock_user_repo.save.assert_called_once()


# =============================================================================
# GET USER USE CASE TESTS
# =============================================================================


class TestGetUserUseCase:
    """Tests for GetUserUseCase."""

    @pytest.mark.asyncio
    async def test_get_user_by_id_success(self, mock_user_repo, user_id, active_user):
        """Test successful user retrieval by ID."""
        mock_user_repo.get_by_id.return_value = active_user

        use_case = GetUserUseCase(mock_user_repo)
        user = await use_case.execute(user_id)

        assert user == active_user

    @pytest.mark.asyncio
    async def test_get_user_by_id_not_found(self, mock_user_repo, user_id):
        """Test user retrieval when not found."""
        mock_user_repo.get_by_id.return_value = None

        use_case = GetUserUseCase(mock_user_repo)
        user = await use_case.execute(user_id)

        assert user is None

    @pytest.mark.asyncio
    async def test_get_user_by_email_success(
        self, mock_user_repo, email, tenant_id, active_user
    ):
        """Test successful user retrieval by email."""
        mock_user_repo.get_by_email.return_value = active_user

        use_case = GetUserUseCase(mock_user_repo)
        user = await use_case.execute_by_email(email, tenant_id)

        assert user == active_user
