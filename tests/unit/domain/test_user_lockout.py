"""Unit tests for UserEntity account-lockout behaviour (Phase 1 #C9)."""

from datetime import UTC, datetime, timedelta

import pytest

from app.domain.entities.user import UserEntity
from app.domain.enums import UserStatus
from app.domain.events import UserLockedOut, UserLockoutCleared, UserLoginFailed
from app.domain.exceptions import DomainError
from app.domain.value_objects.core import Email, TenantId, UserId


def _make_user() -> UserEntity:
    now = datetime.now(UTC)
    return UserEntity(
        _id=UserId("usr-1"),
        _tenant_id=TenantId("tenant-1"),
        _email=Email("user@example.com"),
        _status=UserStatus.ACTIVE,
        _is_two_factor_enabled=False,
        _created_at=now,
        _updated_at=now,
    )


THRESHOLD = 5
WINDOW = timedelta(minutes=30)


class TestLockoutCounter:
    def test_starts_unlocked_with_zero_count(self):
        user = _make_user()
        assert user.failed_login_count == 0
        assert user.locked_until is None
        assert user.is_locked() is False

    def test_failed_login_increments_counter_and_emits_event(self):
        user = _make_user()
        user.record_failed_login(threshold=THRESHOLD, lock_duration=WINDOW)

        assert user.failed_login_count == 1
        assert user.is_locked() is False
        events = [e for e in user.events if isinstance(e, UserLoginFailed)]
        assert len(events) == 1
        assert events[0].failed_count == 1

    def test_threshold_triggers_lockout_event_and_window(self):
        user = _make_user()
        now = datetime.now(UTC)
        for _ in range(THRESHOLD):
            user.record_failed_login(
                threshold=THRESHOLD, lock_duration=WINDOW, now=now
            )

        assert user.failed_login_count == THRESHOLD
        assert user.locked_until == now + WINDOW
        assert user.is_locked(now=now) is True

        login_failed = [e for e in user.events if isinstance(e, UserLoginFailed)]
        locked = [e for e in user.events if isinstance(e, UserLockedOut)]
        assert len(login_failed) == THRESHOLD
        assert len(locked) == 1
        assert locked[0].locked_until == now + WINDOW

    def test_is_locked_false_after_window_expires(self):
        user = _make_user()
        now = datetime.now(UTC)
        for _ in range(THRESHOLD):
            user.record_failed_login(
                threshold=THRESHOLD, lock_duration=WINDOW, now=now
            )
        future = now + WINDOW + timedelta(seconds=1)
        assert user.is_locked(now=future) is False


class TestLockoutCleared:
    def test_successful_login_resets_counter_when_unlocked(self):
        user = _make_user()
        user.record_failed_login(threshold=THRESHOLD, lock_duration=WINDOW)
        user.record_failed_login(threshold=THRESHOLD, lock_duration=WINDOW)
        user.record_successful_login()

        assert user.failed_login_count == 0
        assert user.locked_until is None
        assert not any(isinstance(e, UserLockoutCleared) for e in user.events)

    def test_successful_login_emits_cleared_when_previously_locked(self):
        user = _make_user()
        for _ in range(THRESHOLD):
            user.record_failed_login(threshold=THRESHOLD, lock_duration=WINDOW)
        user.record_successful_login()

        assert user.failed_login_count == 0
        assert user.locked_until is None
        cleared = [e for e in user.events if isinstance(e, UserLockoutCleared)]
        assert len(cleared) == 1


class TestPolicyValidation:
    def test_threshold_must_be_positive(self):
        user = _make_user()
        with pytest.raises(DomainError):
            user.record_failed_login(threshold=0, lock_duration=WINDOW)

    def test_duration_must_be_positive(self):
        user = _make_user()
        with pytest.raises(DomainError):
            user.record_failed_login(threshold=THRESHOLD, lock_duration=timedelta(0))
