"""
Cover for the login rate limiter: the attempt window, the 429 response, and
which header the client IP is read from.

The limiter is the only brute-force control in front of password login, and it
keys entirely on a client-supplied header when one is present, so the IP
resolution order is as much a part of its behaviour as the counting is.
"""

from typing import Any

import pytest
from fastapi import HTTPException

from app.core.login_rate_limit import (
    LOGIN_RATE_LIMIT_MAX_ATTEMPTS,
    LOGIN_RATE_LIMIT_WINDOW_SEC,
    MemoryLoginRateLimitBackend,
    _get_backend,
    _get_client_ip,
    check_login_rate_limit,
    get_login_rate_limit_backend,
    record_login_attempt,
)

IP = "203.0.113.7"


class _Client:
    def __init__(self, host: str) -> None:
        self.host = host


class _AppState:
    pass


class _App:
    def __init__(self) -> None:
        self.state = _AppState()


class _Request:
    """The attributes the limiter reads off a Request, and nothing else."""

    def __init__(
        self,
        headers: dict[str, str] | None = None,
        client_host: str | None = None,
        backend: Any = None,
    ) -> None:
        self.headers = headers or {}
        self.client = _Client(client_host) if client_host else None
        self.app = _App()
        if backend is not None:
            self.app.state.login_rate_limit_backend = backend


@pytest.fixture
def backend() -> MemoryLoginRateLimitBackend:
    return MemoryLoginRateLimitBackend()


class TestMemoryBackendCounting:
    def test_attempts_up_to_the_limit_are_allowed(
        self, backend: MemoryLoginRateLimitBackend
    ) -> None:
        for _ in range(LOGIN_RATE_LIMIT_MAX_ATTEMPTS):
            backend.check(IP)
            backend.record(IP)

    def test_the_attempt_after_the_limit_is_refused(
        self, backend: MemoryLoginRateLimitBackend
    ) -> None:
        for _ in range(LOGIN_RATE_LIMIT_MAX_ATTEMPTS):
            backend.check(IP)
            backend.record(IP)
        with pytest.raises(HTTPException) as exc:
            backend.check(IP)
        assert exc.value.status_code == 429

    def test_refusal_carries_a_retry_after_within_the_window(
        self, backend: MemoryLoginRateLimitBackend
    ) -> None:
        for _ in range(LOGIN_RATE_LIMIT_MAX_ATTEMPTS):
            backend.record(IP)
        with pytest.raises(HTTPException) as exc:
            backend.check(IP)
        retry_after = int(exc.value.headers["Retry-After"])
        assert 1 <= retry_after <= LOGIN_RATE_LIMIT_WINDOW_SEC

    def test_refusal_detail_names_no_account(self, backend: MemoryLoginRateLimitBackend) -> None:
        """The message must not confirm whether the email or tenant exists."""
        for _ in range(LOGIN_RATE_LIMIT_MAX_ATTEMPTS):
            backend.record(IP)
        with pytest.raises(HTTPException) as exc:
            backend.check(IP)
        assert exc.value.detail == "Too many login attempts. Please try again later."

    def test_counting_is_per_ip(self, backend: MemoryLoginRateLimitBackend) -> None:
        for _ in range(LOGIN_RATE_LIMIT_MAX_ATTEMPTS):
            backend.record(IP)
        with pytest.raises(HTTPException):
            backend.check(IP)
        backend.check("198.51.100.4")


class TestMemoryBackendWindow:
    def test_attempts_older_than_the_window_stop_counting(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        clock = {"now": 1_000_000.0}
        monkeypatch.setattr("app.core.login_rate_limit.time.time", lambda: clock["now"])
        backend = MemoryLoginRateLimitBackend()

        for _ in range(LOGIN_RATE_LIMIT_MAX_ATTEMPTS):
            backend.record(IP)
        with pytest.raises(HTTPException):
            backend.check(IP)

        clock["now"] += LOGIN_RATE_LIMIT_WINDOW_SEC + 1
        backend.check(IP)

    def test_a_partial_window_still_refuses(self, monkeypatch: pytest.MonkeyPatch) -> None:
        clock = {"now": 2_000_000.0}
        monkeypatch.setattr("app.core.login_rate_limit.time.time", lambda: clock["now"])
        backend = MemoryLoginRateLimitBackend()

        for _ in range(LOGIN_RATE_LIMIT_MAX_ATTEMPTS):
            backend.record(IP)
        clock["now"] += LOGIN_RATE_LIMIT_WINDOW_SEC // 2
        with pytest.raises(HTTPException):
            backend.check(IP)

    def test_custom_window_and_limit_are_honoured(self) -> None:
        backend = MemoryLoginRateLimitBackend(window_sec=60, max_attempts=2)
        backend.record(IP)
        backend.check(IP)
        backend.record(IP)
        with pytest.raises(HTTPException):
            backend.check(IP)


class TestClientIpResolution:
    def test_forwarded_for_wins_and_only_the_first_hop_is_used(self) -> None:
        request = _Request(headers={"x-forwarded-for": "  1.2.3.4 , 5.6.7.8 "})
        assert _get_client_ip(request) == "1.2.3.4"

    def test_real_ip_is_used_when_forwarded_for_is_absent(self) -> None:
        request = _Request(headers={"x-real-ip": "9.9.9.9"})
        assert _get_client_ip(request) == "9.9.9.9"

    def test_forwarded_for_takes_precedence_over_real_ip(self) -> None:
        request = _Request(headers={"x-forwarded-for": "1.2.3.4", "x-real-ip": "9.9.9.9"})
        assert _get_client_ip(request) == "1.2.3.4"

    def test_peer_address_is_the_fallback(self) -> None:
        request = _Request(client_host="7.7.7.7")
        assert _get_client_ip(request) == "7.7.7.7"

    def test_unknown_when_there_is_no_peer(self) -> None:
        assert _get_client_ip(_Request()) == "unknown"

    def test_two_forwarded_values_are_counted_separately(self) -> None:
        """Distinct header values are distinct buckets, so the header is trusted."""
        backend = MemoryLoginRateLimitBackend(window_sec=60, max_attempts=1)
        first = _Request(headers={"x-forwarded-for": "1.1.1.1"}, backend=backend)
        second = _Request(headers={"x-forwarded-for": "2.2.2.2"}, backend=backend)

        check_login_rate_limit(first)
        record_login_attempt(first)
        with pytest.raises(HTTPException):
            check_login_rate_limit(first)

        check_login_rate_limit(second)


class TestBackendSelection:
    def test_memory_is_the_default(self) -> None:
        assert isinstance(get_login_rate_limit_backend(), MemoryLoginRateLimitBackend)

    @pytest.mark.parametrize("redis_url", ["", "   "])
    def test_redis_without_a_url_falls_back_to_memory(self, redis_url: str) -> None:
        chosen = get_login_rate_limit_backend(backend_type="redis", redis_url=redis_url)
        assert isinstance(chosen, MemoryLoginRateLimitBackend)

    def test_unknown_backend_type_falls_back_to_memory(self) -> None:
        chosen = get_login_rate_limit_backend(backend_type="memcached")
        assert isinstance(chosen, MemoryLoginRateLimitBackend)

    def test_app_state_backend_is_preferred(self) -> None:
        configured = MemoryLoginRateLimitBackend()
        assert _get_backend(_Request(backend=configured)) is configured

    def test_a_request_without_app_state_still_gets_a_backend(self) -> None:
        resolved = _get_backend(_Request())
        assert isinstance(resolved, MemoryLoginRateLimitBackend)
