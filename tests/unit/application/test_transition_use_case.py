"""Tests for the generic TransitionUseCase (Phase 1 #C3)."""

from datetime import UTC, datetime

import pytest

from app.application.use_cases.transitions import (
    TransitionUseCase,
    UserTransition,
)
from app.domain.entities.user import UserEntity
from app.domain.enums import UserStatus
from app.domain.events import UserActivated, UserSuspended
from app.domain.exceptions import DomainError, NotFoundError
from app.domain.value_objects.core import Email, TenantId, UserId


class _FakeUserRepo:
    def __init__(self, user: UserEntity | None) -> None:
        self._user = user
        self.saved: list[UserEntity] = []

    async def get_by_id(self, user_id: UserId) -> UserEntity | None:
        return self._user

    async def save(self, entity: UserEntity) -> None:
        self.saved.append(entity)


def _user(status: UserStatus = UserStatus.PENDING_VERIFICATION) -> UserEntity:
    now = datetime.now(UTC)
    return UserEntity(
        id=UserId("u-1"),
        tenant_id=TenantId("t-1"),
        email=Email("u@example.com"),
        status=status,
        is_two_factor_enabled=False,
        created_at=now,
        updated_at=now,
    )


def _make_use_case(user: UserEntity | None) -> TransitionUseCase[UserEntity, UserId, UserTransition]:
    use_case: TransitionUseCase[UserEntity, UserId, UserTransition] = TransitionUseCase(_FakeUserRepo(user))
    use_case.entity_name = "User"
    return use_case


@pytest.mark.asyncio
async def test_activate_dispatches_to_entity_method():
    user = _user()
    use_case = _make_use_case(user)
    out = await use_case.execute(user.id, UserTransition.ACTIVATE)
    assert out.status == UserStatus.ACTIVE
    assert any(isinstance(e, UserActivated) for e in user.events)


@pytest.mark.asyncio
async def test_kwargs_passed_through_to_entity_method():
    user = _user(UserStatus.ACTIVE)
    use_case = _make_use_case(user)
    await use_case.execute(user.id, UserTransition.SUSPEND, reason="security review")
    assert user.status == UserStatus.SUSPENDED
    suspended = [e for e in user.events if isinstance(e, UserSuspended)]
    assert suspended and suspended[0].reason == "security review"


@pytest.mark.asyncio
async def test_missing_entity_raises_not_found():
    use_case = _make_use_case(None)
    with pytest.raises(NotFoundError):
        await use_case.execute(UserId("nope"), UserTransition.ACTIVATE)


@pytest.mark.asyncio
async def test_invalid_state_raises_domain_error():
    user = _user(UserStatus.BANNED)
    use_case = _make_use_case(user)
    with pytest.raises(DomainError):
        await use_case.execute(user.id, UserTransition.ACTIVATE)


@pytest.mark.asyncio
async def test_unsupported_transition_rejected():
    class BogusTransition:
        value = "fly_to_the_moon"

    user = _user(UserStatus.ACTIVE)
    use_case = _make_use_case(user)
    with pytest.raises(DomainError):
        await use_case.execute(user.id, BogusTransition())  # type: ignore[arg-type]


@pytest.mark.asyncio
async def test_save_called_after_successful_transition():
    user = _user()
    repo = _FakeUserRepo(user)
    use_case: TransitionUseCase[UserEntity, UserId, UserTransition] = TransitionUseCase(repo)
    use_case.entity_name = "User"
    await use_case.execute(user.id, UserTransition.ACTIVATE)
    assert repo.saved == [user]


@pytest.mark.asyncio
async def test_updated_at_refreshed():
    user = _user()
    original = user.updated_at
    use_case = _make_use_case(user)
    await use_case.execute(user.id, UserTransition.ACTIVATE)
    assert user.updated_at >= original
