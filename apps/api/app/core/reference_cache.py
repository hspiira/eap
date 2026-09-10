"""
In-process TTL cache for small, platform-wide vocabulary/taxonomy endpoints
(service categories, KPI categories, case referral sources, and similar
lookup tables an operator edits rarely compared to how often they are read).

Single API process only: state lives in a module-level dict and is not
shared across replicas or workers. Do not reach for this once the API runs
with more than one process; that needs a shared backend (e.g. the Redis
instance already wired for login rate limiting in login_rate_limit.py).
"""

import functools
import time
from collections.abc import Awaitable, Callable
from typing import Any, TypeVar

T = TypeVar("T")

DEFAULT_TTL_SECONDS = 300.0

# FastAPI dependency-injected values: not part of what a lookup's result
# depends on, and not safe to build a cache key from (unhashable, or would
# fragment the cache per caller for data that does not vary by caller).
_NOT_CACHE_KEY_PARAMS = frozenset(
    {"db", "repo", "request", "audit_handler", "_user", "user", "current_user"}
)

_store: dict[str, tuple[float, Any]] = {}


def _cache_key(resource: str, kwargs: dict[str, Any]) -> str:
    parts = [
        f"{name}={kwargs[name]!r}" for name in sorted(kwargs) if name not in _NOT_CACHE_KEY_PARAMS
    ]
    return resource + "?" + "&".join(parts)


def invalidate_reference_cache(resource: str) -> None:
    """Drop every cached entry for a resource. Call from every route that writes it."""
    prefix = f"{resource}?"
    for key in [k for k in _store if k == resource or k.startswith(prefix)]:
        del _store[key]


def cached_lookup(resource: str, ttl_seconds: float = DEFAULT_TTL_SECONDS):
    """
    Cache a read-only route's result in-process, keyed by resource name and
    its non-dependency query parameters.

    Only for small, rarely-written, platform-wide vocabulary endpoints. Pair
    with invalidate_reference_cache(resource) in every route that writes the
    same table, so an edit is visible immediately rather than after the TTL.
    """

    def decorator(func: Callable[..., Awaitable[T]]) -> Callable[..., Awaitable[T]]:
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> T:
            key = _cache_key(resource, kwargs)
            hit = _store.get(key)
            if hit is not None:
                expires_at, value = hit
                if expires_at >= time.monotonic():
                    return value
                del _store[key]
            result = await func(*args, **kwargs)
            _store[key] = (time.monotonic() + ttl_seconds, result)
            return result

        return wrapper

    return decorator
