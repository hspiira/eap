"""Commit an import every few rows instead of once per row."""

from collections.abc import Awaitable, Callable

#: Rows per commit. Each commit is a WAL flush, which is the expensive part of
#: writing a row; a row that is written but not yet committed is still pending,
#: so the cost of crossing fewer boundaries is redoing at most this many rows.
COMMIT_EVERY_ROWS = 10


class BatchedCommit:
    """Commits every `every` rows, and on `flush`.

    A row still writes inside its own savepoint, so one bad row costs only
    itself. What changes is when the write becomes durable: a call that dies
    mid-chunk leaves up to `every - 1` rows for the next call to write again.
    Nothing is lost, because a row that never committed never claimed itself
    and is still pending.
    """

    def __init__(
        self, commit: Callable[[], Awaitable[None]], *, every: int = COMMIT_EVERY_ROWS
    ) -> None:
        self._commit = commit
        self._every = max(1, every)
        self._pending = 0
        self.commits = 0

    async def after_row(self) -> None:
        """Count a written row, committing once the batch is full."""
        self._pending += 1
        if self._pending >= self._every:
            await self.flush()

    async def flush(self) -> None:
        """Commit whatever rows are still uncommitted."""
        if self._pending == 0:
            return
        self._pending = 0
        self.commits += 1
        await self._commit()
