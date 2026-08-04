"""User use case tests.

Lifecycle/update operations now flow through ``TransitionUseCase`` +
``UserTransition`` (Phase 1 #C3). The detailed FSM behaviour is covered
in ``test_user_entity.py``; here we verify only the application-level
wiring: create-on-creation, query-by-email, and a representative
transition end-to-end.
"""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.application.use_cases.transitions import TransitionUseCase, UserTransition
from app.application.use_cases.user_use_cases import (
    CreateUserUseCase,
    GetUserUseCase,
)
from app.domain.entities.user import UserEntity
from app.domain.enums import UserStatus
from app.domain.value_objects.core import Email, TenantId, UserId


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
    repo = MagicMock()
    repo.get_by_id = AsyncMock()
    repo.get_by_email = AsyncMock()
    repo.save = AsyncMock()
    repo.list_all = AsyncMock()
    repo.count = AsyncMock()
    return repo


@pytest.fixture
def pending_user(user_id, tenant_id, email, now) -> UserEntity:
    return UserEntity(
        id=user_id,
        tenant_id=tenant_id,
        email=email,
        status=UserStatus.PENDING_VERIFICATION,
        is_two_factor_enabled=False,
        created_at=now,
        updated_at=now,
    )


@pytest.fixture
def active_user(user_id, tenant_id, email, now) -> UserEntity:
    return UserEntity(
        id=user_id,
        tenant_id=tenant_id,
        email=email,
        status=UserStatus.ACTIVE,
        is_two_factor_enabled=False,
        created_at=now,
        updated_at=now,
    )


def _transition_use_case(repo) -> TransitionUseCase[UserEntity, UserId, UserTransition]:
    use_case: TransitionUseCase[UserEntity, UserId, UserTransition] = TransitionUseCase(repo)
    use_case.entity_name = "User"
    return use_case


class TestCreateUserUseCase:
    @pytest.mark.asyncio
    async def test_create_user_success(self, mock_user_repo, user_id, tenant_id, email):
        mock_user_repo.get_by_email.return_value = None
        use_case = CreateUserUseCase(mock_user_repo)
        user = await use_case.execute(user_id, tenant_id, email, "hash")
        assert user.email == email
        assert user.status == UserStatus.PENDING_VERIFICATION
        mock_user_repo.save.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_user_duplicate_email_raises_error(
        self, mock_user_repo, user_id, tenant_id, email, active_user
    ):
        mock_user_repo.get_by_email.return_value = active_user
        use_case = CreateUserUseCase(mock_user_repo)
        with pytest.raises(ValueError, match="already exists"):
            await use_case.execute(user_id, tenant_id, email, "hash")


class TestUserTransitions:
    @pytest.mark.asyncio
    async def test_activate(self, mock_user_repo, user_id, pending_user):
        mock_user_repo.get_by_id.return_value = pending_user
        await _transition_use_case(mock_user_repo).execute(user_id, UserTransition.ACTIVATE)
        assert pending_user.status == UserStatus.ACTIVE
        mock_user_repo.save.assert_called_once()

    @pytest.mark.asyncio
    async def test_verify_email(self, mock_user_repo, user_id, pending_user):
        mock_user_repo.get_by_id.return_value = pending_user
        await _transition_use_case(mock_user_repo).execute(user_id, UserTransition.VERIFY_EMAIL)
        assert pending_user.email_verified_at is not None

    @pytest.mark.asyncio
    async def test_suspend_with_reason(self, mock_user_repo, user_id, active_user):
        mock_user_repo.get_by_id.return_value = active_user
        await _transition_use_case(mock_user_repo).execute(
            user_id, UserTransition.SUSPEND, reason="Policy violation"
        )
        assert active_user.status == UserStatus.SUSPENDED

    @pytest.mark.asyncio
    async def test_ban_with_reason(self, mock_user_repo, user_id, active_user):
        mock_user_repo.get_by_id.return_value = active_user
        await _transition_use_case(mock_user_repo).execute(
            user_id, UserTransition.BAN, reason="Fraud"
        )
        assert active_user.status == UserStatus.BANNED

    @pytest.mark.asyncio
    async def test_deactivate(self, mock_user_repo, user_id, active_user):
        mock_user_repo.get_by_id.return_value = active_user
        await _transition_use_case(mock_user_repo).execute(
            user_id, UserTransition.DEACTIVATE, reason="Inactive"
        )
        assert active_user.status == UserStatus.INACTIVE

    @pytest.mark.asyncio
    async def test_terminate(self, mock_user_repo, user_id, active_user):
        mock_user_repo.get_by_id.return_value = active_user
        await _transition_use_case(mock_user_repo).execute(
            user_id, UserTransition.TERMINATE, reason="Account closure"
        )
        assert active_user.status == UserStatus.TERMINATED

    @pytest.mark.asyncio
    async def test_update_password(self, mock_user_repo, user_id, active_user):
        mock_user_repo.get_by_id.return_value = active_user
        await _transition_use_case(mock_user_repo).execute(
            user_id, UserTransition.UPDATE_PASSWORD, password_hash="newhash"
        )
        assert active_user._password_hash == "newhash"

    @pytest.mark.asyncio
    async def test_enable_disable_two_factor(self, mock_user_repo, user_id, active_user):
        mock_user_repo.get_by_id.return_value = active_user
        await _transition_use_case(mock_user_repo).execute(
            user_id, UserTransition.ENABLE_TWO_FACTOR
        )
        assert active_user.is_two_factor_enabled is True
        await _transition_use_case(mock_user_repo).execute(
            user_id, UserTransition.DISABLE_TWO_FACTOR
        )
        assert active_user.is_two_factor_enabled is False


class TestGetUserUseCase:
    @pytest.mark.asyncio
    async def test_by_id(self, mock_user_repo, user_id, active_user):
        mock_user_repo.get_by_id.return_value = active_user
        use_case = GetUserUseCase(mock_user_repo)
        user = await use_case.execute(user_id)
        assert user is active_user

    @pytest.mark.asyncio
    async def test_by_email(self, mock_user_repo, email, tenant_id, active_user):
        mock_user_repo.get_by_email.return_value = active_user
        use_case = GetUserUseCase(mock_user_repo)
        user = await use_case.execute_by_email(email, tenant_id)
        assert user is active_user
