"""Commit cadence: fewer WAL flushes, and never a row left uncommitted."""

from unittest.mock import AsyncMock

from app.shared.utils.batched_commit import BatchedCommit


class TestCadence:
    async def test_it_commits_once_the_batch_is_full(self):
        commit = AsyncMock()
        batched = BatchedCommit(commit, every=3)

        for _ in range(3):
            await batched.after_row()

        commit.assert_awaited_once()

    async def test_rows_short_of_a_full_batch_do_not_commit_yet(self):
        commit = AsyncMock()
        batched = BatchedCommit(commit, every=3)

        for _ in range(2):
            await batched.after_row()

        commit.assert_not_awaited()

    async def test_flush_commits_the_remainder(self):
        commit = AsyncMock()
        batched = BatchedCommit(commit, every=10)

        for _ in range(4):
            await batched.after_row()
        await batched.flush()

        commit.assert_awaited_once()
        assert batched.commits == 1

    async def test_a_hundred_rows_cost_ten_commits_not_a_hundred(self):
        commit = AsyncMock()
        batched = BatchedCommit(commit, every=10)

        for _ in range(100):
            await batched.after_row()
        await batched.flush()

        assert commit.await_count == 10
        assert batched.commits == 10

    async def test_flushing_with_nothing_pending_does_not_commit(self):
        """An empty chunk must not open a transaction just to close it."""
        commit = AsyncMock()
        batched = BatchedCommit(commit, every=10)

        await batched.flush()
        await batched.flush()

        commit.assert_not_awaited()
        assert batched.commits == 0

    async def test_flushing_twice_commits_the_remainder_once(self):
        commit = AsyncMock()
        batched = BatchedCommit(commit, every=10)

        await batched.after_row()
        await batched.flush()
        await batched.flush()

        commit.assert_awaited_once()

    async def test_a_batch_of_one_commits_every_row(self):
        """The old per-row behaviour is still reachable by configuration."""
        commit = AsyncMock()
        batched = BatchedCommit(commit, every=1)

        for _ in range(5):
            await batched.after_row()

        assert commit.await_count == 5

    async def test_a_nonsense_batch_size_still_commits(self):
        commit = AsyncMock()
        batched = BatchedCommit(commit, every=0)

        await batched.after_row()

        commit.assert_awaited_once()
