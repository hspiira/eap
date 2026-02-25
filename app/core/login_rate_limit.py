"""
Login-specific rate limit to mitigate brute force.

Tracks attempts per client IP (or X-Forwarded-For / X-Real-IP when set).
Limit: 5 attempts per 15 minutes per IP. Returns 429 when exceeded.

Supports pluggable backends: "memory" (per-process) or "redis" (shared across instances).
"""

import time
from collections import deque, defaultdict
from typing import Protocol

from fastapi import HTTPException, Request
from starlette import status

LOGIN_RATE_LIMIT_WINDOW_SEC = 15 * 60  # 15 minutes
LOGIN_RATE_LIMIT_MAX_ATTEMPTS = 5


class LoginRateLimitBackend(Protocol):
    """Protocol for login rate limit backends."""

    def check(self, ip: str) -> None:
        """Raise 429 if the IP has exceeded the attempt limit. Call before record."""
        ...

    def record(self, ip: str) -> None:
        """Record one login attempt for the IP. Call after check."""
        ...


class MemoryLoginRateLimitBackend:
    """In-process backend. State is not shared across app instances."""

    def __init__(
        self,
        window_sec: int = LOGIN_RATE_LIMIT_WINDOW_SEC,
        max_attempts: int = LOGIN_RATE_LIMIT_MAX_ATTEMPTS,
    ) -> None:
        self._window_sec = window_sec
        self._max_attempts = max_attempts
        self._attempts: dict[str, deque[float]] = defaultdict(
            lambda: deque(maxlen=100)
        )

    def check(self, ip: str) -> None:
        now = time.time()
        cutoff = now - self._window_sec
        attempts = self._attempts[ip]
        while attempts and attempts[0] < cutoff:
            attempts.popleft()
        if len(attempts) >= self._max_attempts:
            retry_after = (
                max(
                    1,
                    int(attempts[0] + self._window_sec - now),
                )
                if attempts
                else 900
            )
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many login attempts. Please try again later.",
                headers={"Retry-After": str(retry_after)},
            )

    def record(self, ip: str) -> None:
        self._attempts[ip].append(time.time())


def _redis_backend(redis_url: str) -> LoginRateLimitBackend | None:
    """Build Redis backend if redis is installed and URL is valid."""
    try:
        import redis
    except ImportError:
        return None
    window_sec = LOGIN_RATE_LIMIT_WINDOW_SEC
    max_attempts = LOGIN_RATE_LIMIT_MAX_ATTEMPTS

    class RedisLoginRateLimitBackend:
        """Redis-backed login rate limit (shared across instances)."""

        def __init__(self, url: str) -> None:
            self._client = redis.from_url(url, decode_responses=True)
            self._key_prefix = "login_attempts:"
            self._window_sec = window_sec
            self._max_attempts = max_attempts

        def check(self, ip: str) -> None:
            key = f"{self._key_prefix}{ip}"
            count = self._client.get(key)
            if count is not None and int(count) >= self._max_attempts:
                ttl = self._client.ttl(key)
                retry_after = max(1, ttl) if ttl > 0 else 900
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Too many login attempts. Please try again later.",
                    headers={"Retry-After": str(retry_after)},
                )

        def record(self, ip: str) -> None:
            key = f"{self._key_prefix}{ip}"
            pipe = self._client.pipeline()
            pipe.incr(key)
            pipe.expire(key, self._window_sec)
            pipe.execute()

    return RedisLoginRateLimitBackend(redis_url)


_fallback_backend: LoginRateLimitBackend | None = None


def get_login_rate_limit_backend(
    backend_type: str = "memory",
    redis_url: str = "",
) -> LoginRateLimitBackend:
    """Return the login rate limit backend for the given config."""
    if backend_type == "redis" and (redis_url or "").strip():
        redis_impl = _redis_backend(redis_url.strip())
        if redis_impl is not None:
            return redis_impl
    return MemoryLoginRateLimitBackend()


def _get_backend(request: Request) -> LoginRateLimitBackend:
    """Get backend from app state or fall back to in-memory backend."""
    backend = getattr(
        request.app.state,
        "login_rate_limit_backend",
        None,
    )
    if backend is not None:
        return backend
    global _fallback_backend
    if _fallback_backend is None:
        _fallback_backend = MemoryLoginRateLimitBackend()
    return _fallback_backend


def _get_client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    real_ip = request.headers.get("x-real-ip")
    if real_ip:
        return real_ip
    if request.client:
        return request.client.host
    return "unknown"


def check_login_rate_limit(request: Request) -> None:
    """
    Raise 429 if the client has exceeded login attempt limit (5 per 15 min per IP).
    Call this at the start of the login handler.
    """
    backend = _get_backend(request)
    ip = _get_client_ip(request)
    backend.check(ip)


def record_login_attempt(request: Request) -> None:
    """Record a login attempt (call after checking rate limit, before validating credentials)."""
    backend = _get_backend(request)
    ip = _get_client_ip(request)
    backend.record(ip)
