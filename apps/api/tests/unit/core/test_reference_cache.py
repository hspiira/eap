"""
Cover for the in-process reference cache: a cache hit skips the wrapped
call, distinct query params get distinct entries, dependency-injected
params (db, repo, the current user) never fragment the key, and
invalidation clears exactly the resource it names.
"""

import pytest

from app.core.reference_cache import _store, cached_lookup, invalidate_reference_cache


@pytest.fixture(autouse=True)
def _clear_store():
    _store.clear()
    yield
    _store.clear()


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
    invalidate_reference_cache("widgets")
    await list_widgets()
    await list_gadgets()

    assert widget_calls == [1, 1]
    assert gadget_calls == [1]
