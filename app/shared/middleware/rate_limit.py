"""
Rate Limiting Middleware

Simple in-memory rate limiter for API endpoints.
For production, consider using Redis-based rate limiting.
"""

import time
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Callable

from fastapi import Request, Response, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp


@dataclass
class RateLimitConfig:
    """Configuration for rate limiting."""

    requests_per_minute: int = 60
    requests_per_hour: int = 1000
    burst_size: int = 10  # Allow short bursts
    
    # Paths to exclude from rate limiting
    excluded_paths: list[str] = field(default_factory=lambda: [
        "/",
        "/health",
        "/docs",
        "/openapi.json",
        "/redoc",
    ])


@dataclass
class RateLimitEntry:
    """Track rate limit state for a client."""

    minute_count: int = 0
    hour_count: int = 0
    minute_reset: float = 0.0
    hour_reset: float = 0.0
    burst_tokens: float = 0.0
    last_request: float = 0.0


class RateLimiter:
    """
    In-memory rate limiter using token bucket algorithm.
    
    For production deployments with multiple instances,
    use Redis or another distributed store.
    """

    def __init__(self, config: RateLimitConfig | None = None):
        self.config = config or RateLimitConfig()
        self._clients: dict[str, RateLimitEntry] = defaultdict(RateLimitEntry)

    def _get_client_key(self, request: Request) -> str:
        """
        Get unique identifier for the client.
        
        Uses X-Forwarded-For header if available, otherwise client IP.
        Can be extended to use API keys or user IDs.
        """
        # Check for forwarded IP (load balancer/proxy)
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            return forwarded.split(",")[0].strip()

        # Check for real IP header
        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip

        # Fall back to client host
        if request.client:
            return request.client.host

        return "unknown"

    def is_allowed(self, request: Request) -> tuple[bool, dict[str, str]]:
        """
        Check if request is allowed under rate limits.
        
        Returns:
            Tuple of (is_allowed, headers_dict)
        """
        # Skip excluded paths
        if request.url.path in self.config.excluded_paths:
            return True, {}

        client_key = self._get_client_key(request)
        now = time.time()
        entry = self._clients[client_key]

        # Reset minute counter if needed
        if now > entry.minute_reset:
            entry.minute_count = 0
            entry.minute_reset = now + 60

        # Reset hour counter if needed
        if now > entry.hour_reset:
            entry.hour_count = 0
            entry.hour_reset = now + 3600

        # Refill burst tokens (token bucket)
        time_passed = now - entry.last_request if entry.last_request > 0 else 0
        entry.burst_tokens = min(
            self.config.burst_size,
            entry.burst_tokens + (time_passed * self.config.requests_per_minute / 60),
        )
        entry.last_request = now

        # Check limits
        headers = {
            "X-RateLimit-Limit": str(self.config.requests_per_minute),
            "X-RateLimit-Remaining": str(
                max(0, self.config.requests_per_minute - entry.minute_count)
            ),
            "X-RateLimit-Reset": str(int(entry.minute_reset)),
        }

        # Check hour limit
        if entry.hour_count >= self.config.requests_per_hour:
            headers["Retry-After"] = str(int(entry.hour_reset - now))
            return False, headers

        # Check minute limit
        if entry.minute_count >= self.config.requests_per_minute:
            # Allow burst if tokens available
            if entry.burst_tokens >= 1:
                entry.burst_tokens -= 1
            else:
                headers["Retry-After"] = str(int(entry.minute_reset - now))
                return False, headers

        # Request allowed - increment counters
        entry.minute_count += 1
        entry.hour_count += 1
        headers["X-RateLimit-Remaining"] = str(
            max(0, self.config.requests_per_minute - entry.minute_count)
        )

        return True, headers

    def cleanup_old_entries(self, max_age: float = 7200) -> int:
        """
        Remove stale entries to prevent memory growth.
        
        Args:
            max_age: Maximum age in seconds before entry is removed
            
        Returns:
            Number of entries removed
        """
        now = time.time()
        stale_keys = [
            key
            for key, entry in self._clients.items()
            if now - entry.last_request > max_age
        ]
        for key in stale_keys:
            del self._clients[key]
        return len(stale_keys)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    FastAPI middleware for rate limiting.
    
    Usage:
        app.add_middleware(
            RateLimitMiddleware,
            config=RateLimitConfig(requests_per_minute=100)
        )
    """

    def __init__(
        self,
        app: ASGIApp,
        config: RateLimitConfig | None = None,
    ):
        super().__init__(app)
        self.limiter = RateLimiter(config)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request with rate limiting."""
        is_allowed, headers = self.limiter.is_allowed(request)

        if not is_allowed:
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "error": "RATE_LIMIT_EXCEEDED",
                    "message": "Too many requests. Please slow down.",
                    "retry_after": headers.get("Retry-After"),
                },
                headers=headers,
            )

        # Process request
        response = await call_next(request)

        # Add rate limit headers to response
        for key, value in headers.items():
            response.headers[key] = value

        return response


# Convenience function for creating configured middleware
def create_rate_limit_middleware(
    requests_per_minute: int = 60,
    requests_per_hour: int = 1000,
    burst_size: int = 10,
    excluded_paths: list[str] | None = None,
) -> tuple[type, dict]:
    """
    Create rate limit middleware with configuration.
    
    Usage:
        middleware_class, kwargs = create_rate_limit_middleware(
            requests_per_minute=100
        )
        app.add_middleware(middleware_class, **kwargs)
    
    Returns:
        Tuple of (middleware_class, config_kwargs)
    """
    config = RateLimitConfig(
        requests_per_minute=requests_per_minute,
        requests_per_hour=requests_per_hour,
        burst_size=burst_size,
        excluded_paths=excluded_paths or RateLimitConfig().excluded_paths,
    )
    return RateLimitMiddleware, {"config": config}
