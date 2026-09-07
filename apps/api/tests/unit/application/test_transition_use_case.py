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
from app.domain.exceptions import DomainError, NotFoundError, PermissionDeniedError
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


def _make_use_case(
    user: UserEntity | None,
) -> TransitionUseCase[UserEntity, UserId, UserTransition]:
    use_case: TransitionUseCase[UserEntity, UserId, UserTransition] = TransitionUseCase(
        _FakeUserRepo(user)
    )
    use_case.entity_name = "User"
    return use_case


@pytest.mark.asyncio
async def test_activate_dispatches_to_entity_method():
    user = _user()
    use_case = _make_use_case(user)
    out = await use_case.execute(user.id, UserTransition.ACTIVATE, tenant_id="t-1")
    assert out.status == UserStatus.ACTIVE
    assert any(isinstance(e, UserActivated) for e in user.events)


@pytest.mark.asyncio
async def test_kwargs_passed_through_to_entity_method():
    user = _user(UserStatus.ACTIVE)
    use_case = _make_use_case(user)
    await use_case.execute(
        user.id, UserTransition.SUSPEND, tenant_id="t-1", reason="security review"
    )
    assert user.status == UserStatus.SUSPENDED
    suspended = [e for e in user.events if isinstance(e, UserSuspended)]
    assert suspended and suspended[0].reason == "security review"


@pytest.mark.asyncio
async def test_missing_entity_raises_not_found():
    use_case = _make_use_case(None)
    with pytest.raises(NotFoundError):
        await use_case.execute(UserId("nope"), UserTransition.ACTIVATE, tenant_id="t-1")


@pytest.mark.asyncio
async def test_invalid_state_raises_domain_error():
    user = _user(UserStatus.BANNED)
    use_case = _make_use_case(user)
    with pytest.raises(DomainError):
        await use_case.execute(user.id, UserTransition.ACTIVATE, tenant_id="t-1")


@pytest.mark.asyncio
async def test_unsupported_transition_rejected():
    class BogusTransition:
        value = "fly_to_the_moon"

    user = _user(UserStatus.ACTIVE)
    use_case = _make_use_case(user)
    with pytest.raises(DomainError):
        await use_case.execute(user.id, BogusTransition(), tenant_id="t-1")  # type: ignore[arg-type]


@pytest.mark.asyncio
async def test_save_called_after_successful_transition():
    user = _user()
    repo = _FakeUserRepo(user)
    use_case: TransitionUseCase[UserEntity, UserId, UserTransition] = TransitionUseCase(repo)
    use_case.entity_name = "User"
    await use_case.execute(user.id, UserTransition.ACTIVATE, tenant_id="t-1")
    assert repo.saved == [user]


@pytest.mark.asyncio
async def test_updated_at_refreshed():
    user = _user()
    original = user.updated_at
    use_case = _make_use_case(user)
    await use_case.execute(user.id, UserTransition.ACTIVATE, tenant_id="t-1")
    assert user.updated_at >= original


# --- SEC-03: the dispatcher is the ownership gate for 82 mutation routes -------


@pytest.mark.asyncio
async def test_another_tenants_aggregate_cannot_be_transitioned():
    """The reproduced defect: a tenant-A Viewer activated tenant-B's survey.

    The dispatcher loaded by id and mutated whatever it found, so authenticating
    at the route could not supply the missing ownership check.
    """
    user = _user()
    use_case = _make_use_case(user)

    with pytest.raises(PermissionDeniedError):
        await use_case.execute(user.id, UserTransition.ACTIVATE, tenant_id="someone-else")

    assert user.status is UserStatus.PENDING_VERIFICATION
    assert use_case.repository.saved == []  # type: ignore[attr-defined]


@pytest.mark.asyncio
async def test_a_tenant_scoped_aggregate_refuses_a_missing_tenant():
    """`tenant_id=None` is not a way to opt out of the check."""
    user = _user()
    use_case = _make_use_case(user)

    with pytest.raises(DomainError, match="tenant_id is required"):
        await use_case.execute(user.id, UserTransition.ACTIVATE, tenant_id=None)

    assert user.status is UserStatus.PENDING_VERIFICATION


@pytest.mark.asyncio
async def test_an_aggregate_with_no_owning_tenant_refuses_a_supplied_tenant():
    """Tenant itself has no tenant_id; passing one is a wiring mistake."""

    class _Global:
        status = "new"
        events: list = []

        def activate(self) -> None:
            self.status = "active"

    class _Repo:
        def __init__(self, entity):
            self._entity = entity
            self.saved: list = []

        async def get_by_id(self, _id):
            return self._entity

        async def save(self, entity):
            self.saved.append(entity)

    entity = _Global()
    use_case: TransitionUseCase = TransitionUseCase(_Repo(entity), "Tenant")

    with pytest.raises(DomainError, match="not tenant-scoped"):
        await use_case.execute("id-1", UserTransition.ACTIVATE, tenant_id="t-1")

    assert entity.status == "new"
    assert await use_case.execute("id-1", UserTransition.ACTIVATE, tenant_id=None) is entity
