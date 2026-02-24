"""
Login-specific rate limit to mitigate brute force.

Tracks attempts per client IP (or X-Forwarded-For / X-Real-IP when set).
Limit: 5 attempts per 15 minutes per IP. Returns 429 when exceeded.
"""

import time
from collections import deque, defaultdict

from fastapi import HTTPException, Request
from starlette import status

# Per-IP deque of attempt timestamps (oldest first). Prune entries older than window.
_LOGIN_ATTEMPTS: dict[str, deque[float]] = defaultdict(lambda: deque(maxlen=100))

LOGIN_RATE_LIMIT_WINDOW_SEC = 15 * 60  # 15 minutes
LOGIN_RATE_LIMIT_MAX_ATTEMPTS = 5


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
    ip = _get_client_ip(request)
    now = time.time()
    cutoff = now - LOGIN_RATE_LIMIT_WINDOW_SEC
    attempts = _LOGIN_ATTEMPTS[ip]
    while attempts and attempts[0] < cutoff:
        attempts.popleft()
    if len(attempts) >= LOGIN_RATE_LIMIT_MAX_ATTEMPTS:
        retry_after = max(1, int(attempts[0] + LOGIN_RATE_LIMIT_WINDOW_SEC - now)) if attempts else 900
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many login attempts. Please try again later.",
            headers={"Retry-After": str(retry_after)},
        )


def record_login_attempt(request: Request) -> None:
    """Record a login attempt (call after checking rate limit, before validating credentials)."""
    ip = _get_client_ip(request)
    _LOGIN_ATTEMPTS[ip].append(time.time())
