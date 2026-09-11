"""TTL cache for small, platform-wide vocabulary/taxonomy endpoints.

Service categories, KPI categories, case referral sources and similar lookup
tables an operator edits rarely compared to how often they are read.

The backend is shared when ``REDIS_URL`` is set and in-process otherwise. The
distinction matters on more than one instance, which serverless always is: an
in-process cache is invalidated only on the instance that served the write,
so every other instance keeps serving the old vocabulary until its entry
expires. A shared backend invalidates for all of them at once.

A cache failure is never a request failure. Redis being unreachable reads as a
miss, and the route runs as if there were no cache at all.
"""

import functools
import json
import logging
import time
from collections.abc import Awaitable, Callable
from typing import Any, Protocol, TypeVar

from fastapi.encoders import jsonable_encoder

from app.core.config import settings

T = TypeVar("T")

logger = logging.getLogger(__name__)

DEFAULT_TTL_SECONDS = 300.0
KEY_PREFIX = "refcache"

# FastAPI dependency-injected values: not part of what a lookup's result
# depends on, and not safe to build a cache key from (unhashable, or would
# fragment the cache per caller for data that does not vary by caller).
_NOT_CACHE_KEY_PARAMS = frozenset(
    {"db", "repo", "request", "audit_handler", "_user", "user", "current_user"}
)


def _cache_key(resource: str, kwargs: dict[str, Any]) -> str:
    parts = [
        f"{name}={kwargs[name]!r}" for name in sorted(kwargs) if name not in _NOT_CACHE_KEY_PARAMS
    ]
    return f"{KEY_PREFIX}:{resource}:" + "&".join(parts)


class CacheBackend(Protocol):
    """Where cached lookups live. Values are already JSON-able."""

    async def get(self, key: str) -> Any | None: ...

    async def set(self, key: str, value: Any, ttl_seconds: float) -> None: ...

    async def invalidate(self, resource: str) -> None: ...


class InProcessBackend:
    """Module-level dict. Correct only while there is one instance."""

    def __init__(self) -> None:
        self._store: dict[str, tuple[float, Any]] = {}

    async def get(self, key: str) -> Any | None:
        hit = self._store.get(key)
        if hit is None:
            return None
        expires_at, value = hit
        if expires_at < time.monotonic():
            del self._store[key]
            return None
        return value

    async def set(self, key: str, value: Any, ttl_seconds: float) -> None:
        self._store[key] = (time.monotonic() + ttl_seconds, value)

    async def invalidate(self, resource: str) -> None:
        prefix = f"{KEY_PREFIX}:{resource}:"
        for key in [k for k in self._store if k.startswith(prefix)]:
            del self._store[key]

    def clear(self) -> None:
        self._store.clear()


class RedisBackend:
    """Shared across instances, so an edit invalidates everywhere at once.

    Uses the async client: these run inside request handlers, and the
    synchronous client would block the event loop for every lookup.
    """

    def __init__(self, client: Any) -> None:
        self._client = client

    async def get(self, key: str) -> Any | None:
        try:
            raw = await self._client.get(key)
        except Exception as exc:
            logger.warning("reference cache read failed, treating as a miss: %s", exc)
            return None
        return json.loads(raw) if raw is not None else None

    async def set(self, key: str, value: Any, ttl_seconds: float) -> None:
        try:
            await self._client.set(key, json.dumps(value), ex=max(1, int(ttl_seconds)))
        except Exception as exc:
            logger.warning("reference cache write failed, leaving it uncached: %s", exc)

    async def invalidate(self, resource: str) -> None:
        """Drop this resource's entries everywhere.

        Scans rather than versioning the key, so a read stays one round trip.
        Vocabulary is written rarely and read constantly, and the keyspace for
        one resource is a handful of entries.
        """
        pattern = f"{KEY_PREFIX}:{resource}:*"
        try:
            keys = [key async for key in self._client.scan_iter(match=pattern)]
            if keys:
                await self._client.delete(*keys)
        except Exception as exc:
            # Worth an error, not a warning: the cache is now serving a value
            # the database no longer holds, until the entry expires.
            logger.error("reference cache invalidation failed for %s: %s", resource, exc)


_backend: CacheBackend | None = None


def _build_backend() -> CacheBackend:
    url = (settings.REDIS_URL or "").strip()
    if not url:
        return InProcessBackend()
    try:
        from redis.asyncio import Redis
    except ImportError:
        logger.warning(
            "REDIS_URL is set but the redis package is not installed; caching in-process"
        )
        return InProcessBackend()
    try:
        client = Redis.from_url(url, decode_responses=True)
    except Exception as exc:
        logger.error("REDIS_URL is set but unusable, caching in-process instead: %s", exc)
        return InProcessBackend()
    logger.info("reference cache is using the shared Redis backend")
    return RedisBackend(client)


def get_backend() -> CacheBackend:
    """The active backend, built on first use so settings are final."""
    global _backend
    if _backend is None:
        _backend = _build_backend()
    return _backend


def set_backend(backend: CacheBackend | None) -> None:
    """Replace the active backend. For tests and startup wiring."""
    global _backend
    _backend = backend


async def invalidate_reference_cache(resource: str) -> None:
    """Drop every cached entry for a resource. Call from every route that writes it."""
    await get_backend().invalidate(resource)


def cached_lookup(resource: str, ttl_seconds: float = DEFAULT_TTL_SECONDS):
    """
    Cache a read-only route's result, keyed by resource name and its
    non-dependency query parameters.

    Only for small, rarely-written, platform-wide vocabulary endpoints. Pair
    with invalidate_reference_cache(resource) in every route that writes the
    same table, so an edit is visible immediately rather than after the TTL.

    The cached value is the JSON-able form of what the route returned, so a
    hit and a miss put the same shape through the route's response_model
    whichever backend is active.
    """

    def decorator(func: Callable[..., Awaitable[T]]) -> Callable[..., Awaitable[T]]:
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> T:
            backend = get_backend()
            key = _cache_key(resource, kwargs)
            hit = await backend.get(key)
            if hit is not None:
                return hit
            result = await func(*args, **kwargs)
            await backend.set(key, jsonable_encoder(result), ttl_seconds)
            return result

        return wrapper

    return decorator
