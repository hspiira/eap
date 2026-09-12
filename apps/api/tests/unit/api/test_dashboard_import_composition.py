"""The batch summary accounts for every row it describes.

`blocked` once counted only the unresolved identities, so a batch stuck
entirely on conflicting or undated rows reported nothing blocked and the
parts did not sum to the whole.
"""

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.api.routes.dashboard import HELD_OUTCOMES, _import_state
from app.domain.enums.provider_network import ImportBatchStatus, ImportRowOutcome

TENANT = "t-1"


def _runner(by_outcome: dict[ImportRowOutcome, int], row_count: int):
    runner = AsyncMock()
    runner.latest_import_batch.return_value = SimpleNamespace(
        id="batch-1",
        file_name="sessions.csv",
        status=ImportBatchStatus.STAGED,
        row_count=row_count,
        applied_at=None,
    )
    runner.import_row_outcomes.return_value = by_outcome
    return runner


class TestHeldOutcomes:
    def test_every_outcome_staging_can_hold_is_counted(self):
        """Failed is the one exception: the write path refused it, not staging."""
        staging_holds = set(ImportRowOutcome) - {
            ImportRowOutcome.ACCEPTED,
            ImportRowOutcome.DUPLICATE,
            ImportRowOutcome.FAILED,
        }
        assert set(HELD_OUTCOMES) == staging_holds

    async def test_a_conflicting_row_is_blocked_not_invisible(self):
        runner = _runner({ImportRowOutcome.CONFLICTING: 4}, row_count=4)
        summary, queues, backlog = await _import_state(runner, TENANT)
        assert backlog == 4
        assert summary.blocked == 4
        assert [q.outcome for q in queues] == ["Conflicting"]

    async def test_an_undated_row_is_blocked_not_invisible(self):
        runner = _runner({ImportRowOutcome.REJECTED: 2}, row_count=2)
        _, _, backlog = await _import_state(runner, TENANT)
        assert backlog == 2


class TestComposition:
    @pytest.mark.parametrize(
        "by_outcome,row_count",
        [
            ({ImportRowOutcome.ACCEPTED: 10}, 10),
            (
                {
                    ImportRowOutcome.ACCEPTED: 5,
                    ImportRowOutcome.DUPLICATE: 2,
                    ImportRowOutcome.UNRESOLVED_MEMBER: 3,
                    ImportRowOutcome.CONFLICTING: 1,
                    ImportRowOutcome.REJECTED: 1,
                },
                12,
            ),
            (
                {
                    ImportRowOutcome.ACCEPTED: 4,
                    ImportRowOutcome.FAILED: 2,
                    ImportRowOutcome.UNMAPPED_PRACTITIONER: 1,
                },
                7,
            ),
        ],
    )
    async def test_the_parts_sum_to_the_whole(self, by_outcome, row_count):
        runner = _runner(by_outcome, row_count=row_count)
        summary, _, _ = await _import_state(runner, TENANT)
        parts = summary.accepted + summary.duplicate + summary.blocked + summary.failed
        assert parts == summary.row_count

    async def test_an_apply_time_failure_is_reported_apart_from_the_backlog(self):
        """A refused write is not a queue somebody can work through."""
        runner = _runner({ImportRowOutcome.ACCEPTED: 1, ImportRowOutcome.FAILED: 3}, row_count=4)
        summary, _, backlog = await _import_state(runner, TENANT)
        assert summary.failed == 3
        assert backlog == 0

    async def test_no_batch_reports_nothing_rather_than_zeroes(self):
        runner = AsyncMock()
        runner.latest_import_batch.return_value = None
        summary, queues, backlog = await _import_state(runner, TENANT)
        assert (summary, queues, backlog) == (None, [], 0)
