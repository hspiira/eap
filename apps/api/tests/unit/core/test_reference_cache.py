"""
Cover for the reference cache: a cache hit skips the wrapped call, distinct
query params get distinct entries, dependency-injected params (db, repo, the
current user) never fragment the key, invalidation clears exactly the resource
it names, and a backend that is down costs a miss rather than the request.
"""

import pytest

from app.core.reference_cache import (
    InProcessBackend,
    RedisBackend,
    cached_lookup,
    invalidate_reference_cache,
    set_backend,
)


@pytest.fixture(autouse=True)
def _fresh_backend():
    set_backend(InProcessBackend())
    yield
    set_backend(None)


@pytest.mark.asyncio
async def test_second_call_with_same_params_is_a_cache_hit():
    calls = []

    @cached_lookup("widgets")
    async def list_widgets(active_only: bool = True, repo=None, db=None):
        calls.append(active_only)
        return [active_only]

    first = await list_widgets(active_only=True, repo="repo-a", db="db-a")
    second = await list_widgets(active_only=True, repo="repo-b", db="db-b")

    assert first == second == [True]
    assert calls == [True]


@pytest.mark.asyncio
async def test_different_query_params_get_different_entries():
    calls = []

    @cached_lookup("widgets")
    async def list_widgets(active_only: bool = True):
        calls.append(active_only)
        return active_only

    assert await list_widgets(active_only=True) is True
    assert await list_widgets(active_only=False) is False
    assert calls == [True, False]


@pytest.mark.asyncio
async def test_expired_entry_is_recomputed():
    calls = []

    @cached_lookup("widgets", ttl_seconds=-1)
    async def list_widgets():
        calls.append(1)
        return "value"

    await list_widgets()
    await list_widgets()

    assert calls == [1, 1]


@pytest.mark.asyncio
async def test_invalidate_clears_only_the_named_resource():
    widget_calls = []
    gadget_calls = []

    @cached_lookup("widgets")
    async def list_widgets():
        widget_calls.append(1)
        return "widgets"

    @cached_lookup("gadgets")
    async def list_gadgets():
        gadget_calls.append(1)
        return "gadgets"

    await list_widgets()
    await list_gadgets()
    await invalidate_reference_cache("widgets")
    await list_widgets()
    await list_gadgets()

    assert widget_calls == [1, 1]
    assert gadget_calls == [1]


@pytest.mark.asyncio
async def test_a_resource_whose_name_prefixes_another_is_not_cleared_with_it():
    """ "widgets" and "widgets_archive" are different resources."""
    archive_calls = []

    @cached_lookup("widgets")
    async def list_widgets():
        return "widgets"

    @cached_lookup("widgets_archive")
    async def list_archive():
        archive_calls.append(1)
        return "archive"

    await list_widgets()
    await list_archive()
    await invalidate_reference_cache("widgets")
    await list_archive()

    assert archive_calls == [1]


class _BrokenRedis:
    """Every call fails, the way an unreachable Redis does."""

    def __init__(self) -> None:
        self.reads = 0

    async def get(self, key):
        self.reads += 1
        raise ConnectionError("no route to host")

    async def set(self, key, value, ex=None):
        raise ConnectionError("no route to host")

    def scan_iter(self, match=None):
        raise ConnectionError("no route to host")


class TestBackendFailureIsNotRequestFailure:
    """A cache is an optimisation. Losing it must not cost the response."""

    @pytest.mark.asyncio
    async def test_a_failing_read_runs_the_route_instead(self):
        broken = _BrokenRedis()
        set_backend(RedisBackend(broken))
        calls = []

        @cached_lookup("widgets")
        async def list_widgets():
            calls.append(1)
            return "widgets"

        assert await list_widgets() == "widgets"
        assert await list_widgets() == "widgets"
        assert calls == [1, 1]
        assert broken.reads == 2

    @pytest.mark.asyncio
    async def test_a_failing_invalidation_is_recorded_not_raised(self, caplog):
        set_backend(RedisBackend(_BrokenRedis()))

        await invalidate_reference_cache("widgets")

        assert any("invalidation failed" in r.getMessage() for r in caplog.records)


class TestRedisBackendRoundTrip:
    """The wire format has to survive the trip, since Redis holds text."""

    @pytest.mark.asyncio
    async def test_a_cached_value_comes_back_as_the_same_json_shape(self):
        store: dict[str, str] = {}

        class _Fake:
            async def get(self, key):
                return store.get(key)

            async def set(self, key, value, ex=None):
                store[key] = value

            async def scan_iter(self, match=None):
                for key in list(store):
                    yield key

            async def delete(self, *keys):
                for key in keys:
                    store.pop(key, None)

        set_backend(RedisBackend(_Fake()))
        calls = []

        @cached_lookup("widgets")
        async def list_widgets():
            calls.append(1)
            return [{"code": "A", "active": True}]

        first = await list_widgets()
        second = await list_widgets()

        assert first == [{"code": "A", "active": True}]
        assert second == first
        assert calls == [1]


class TestBackendSelection:
    """Which backend gets built, and what happens when Redis is unavailable."""

    def test_no_redis_url_caches_in_process(self, monkeypatch):
        from app.core import reference_cache

        monkeypatch.setattr(reference_cache.settings, "REDIS_URL", "")
        set_backend(None)
        assert isinstance(reference_cache.get_backend(), InProcessBackend)

    def test_a_redis_url_without_the_package_falls_back_rather_than_failing(
        self, monkeypatch, caplog
    ):
        """`redis` is an optional dependency, so a URL alone cannot be trusted."""
        from app.core import reference_cache

        monkeypatch.setattr(reference_cache.settings, "REDIS_URL", "redis://localhost:6379/0")
        set_backend(None)

        backend = reference_cache.get_backend()

        assert isinstance(backend, InProcessBackend)
        assert any("not installed" in r.getMessage() for r in caplog.records)

    def test_the_backend_is_built_once_and_reused(self, monkeypatch):
        from app.core import reference_cache

        monkeypatch.setattr(reference_cache.settings, "REDIS_URL", "")
        set_backend(None)
        assert reference_cache.get_backend() is reference_cache.get_backend()
