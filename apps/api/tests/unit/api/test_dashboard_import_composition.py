"""The backlog counts every row staging held, not only unresolved identities.

It once summed the six identity outcomes alone, so a batch stuck entirely on
conflicting or undated rows reported nothing blocked.
"""

from types import SimpleNamespace
from unittest.mock import AsyncMock

from app.api.routes.dashboard import HELD_OUTCOMES, _import_backlog
from app.domain.enums.provider_network import ImportBatchStatus, ImportRowOutcome

TENANT = "t-1"


def _runner(by_outcome: dict[ImportRowOutcome, int]):
    runner = AsyncMock()
    runner.latest_import_batch.return_value = SimpleNamespace(
        id="batch-1",
        file_name="sessions.csv",
        status=ImportBatchStatus.STAGED,
        row_count=sum(by_outcome.values()),
        applied_at=None,
    )
    runner.import_row_outcomes.return_value = by_outcome
    return runner


class TestHeldOutcomes:
    def test_every_outcome_staging_can_hold_is_counted(self):
        """Accepted and Duplicate are not held; Failed is an apply-time refusal."""
        staging_holds = set(ImportRowOutcome) - {
            ImportRowOutcome.ACCEPTED,
            ImportRowOutcome.DUPLICATE,
            ImportRowOutcome.FAILED,
        }
        assert set(HELD_OUTCOMES) == staging_holds

    async def test_a_conflicting_row_is_counted_not_invisible(self):
        assert await _import_backlog(_runner({ImportRowOutcome.CONFLICTING: 4}), TENANT) == 4

    async def test_an_undated_row_is_counted_not_invisible(self):
        assert await _import_backlog(_runner({ImportRowOutcome.REJECTED: 2}), TENANT) == 2

    async def test_the_queues_are_summed_together(self):
        runner = _runner(
            {
                ImportRowOutcome.UNRESOLVED_MEMBER: 3,
                ImportRowOutcome.CONFLICTING: 1,
                ImportRowOutcome.REJECTED: 1,
            }
        )
        assert await _import_backlog(runner, TENANT) == 5

    async def test_written_and_duplicate_rows_are_not_backlog(self):
        runner = _runner({ImportRowOutcome.ACCEPTED: 9, ImportRowOutcome.DUPLICATE: 3})
        assert await _import_backlog(runner, TENANT) == 0

    async def test_an_apply_time_failure_is_not_a_queue_to_work_through(self):
        runner = _runner({ImportRowOutcome.ACCEPTED: 1, ImportRowOutcome.FAILED: 3})
        assert await _import_backlog(runner, TENANT) == 0

    async def test_no_batch_is_no_backlog(self):
        runner = AsyncMock()
        runner.latest_import_batch.return_value = None
        assert await _import_backlog(runner, TENANT) == 0
