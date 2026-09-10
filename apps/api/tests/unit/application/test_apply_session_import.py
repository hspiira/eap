"""Applying a batch: idempotency, row marking, and the honest zero.

Agent 1 owns the write itself and left replay protection here, because the
batch and row keys are this module's tables.
"""

from datetime import UTC, date, datetime
from unittest.mock import AsyncMock

import pytest

from app.application.use_cases.apply_session_import import ApplyImportBatchUseCase
from app.domain.entities.session_import import (
    SessionImportBatchEntity,
    SessionImportRowEntity,
)
from app.domain.enums.provider_network import (
    ImportBatchStatus,
    ImportRowOutcome,
)
from app.domain.exceptions import DomainError, NotFoundError
from app.domain.value_objects.core import ProviderId, TenantId, UserId
from app.domain.value_objects.provider_network import (
    SessionImportBatchId,
    SessionImportRowId,
)

TENANT = TenantId("t-1")
BATCH = SessionImportBatchId("b-1")
ACTOR = UserId("u-1")
NOW = datetime(2026, 9, 6, 12, 0, tzinfo=UTC)


def _batch(status=ImportBatchStatus.STAGED) -> SessionImportBatchEntity:
    return SessionImportBatchEntity(
        id=BATCH,
        tenant_id=TENANT,
        source_system="sessions-csv",
        file_name="f.csv",
        file_hash="sha256:abc",
        row_count=1,
        status=status,
        staged_by=ACTOR,
        created_at=NOW,
        updated_at=NOW,
    )


def _row(row_id="r-1", outcome=ImportRowOutcome.ACCEPTED, imported=None, number=1):
    return SessionImportRowEntity(
        id=SessionImportRowId(row_id),
        batch_id=BATCH,
        tenant_id=TENANT,
        row_number=number,
        source_record_key=None,
        raw_practitioner_name="Alice Nakato",
        session_date=date(2025, 4, 2),
        outcome=outcome,
        provider_id=ProviderId("prov-1"),
        imported_session_id=imported,
        reasons=() if outcome is ImportRowOutcome.ACCEPTED else ("held",),
        created_at=NOW,
    )


def _use_case(*, batch=None, rows=(), session_id="sess-1"):
    imports = AsyncMock()
    imports.get_batch.return_value = batch if batch is not None else _batch()
    imports.list_rows.return_value = (list(rows), len(rows))
    writer = AsyncMock()
    writer.record.return_value = session_id
    return ApplyImportBatchUseCase(imports, writer), imports, writer


class TestBatchIdempotency:
    async def test_an_applied_batch_cannot_be_applied_again(self):
        use_case, imports, writer = _use_case(batch=_batch(ImportBatchStatus.APPLIED))
        with pytest.raises(DomainError) as caught:
            await use_case.execute(TENANT, BATCH, ACTOR, now=NOW)
        assert caught.value.error_code == "import_batch_not_staged"
        assert caught.value.http_status == 409
        writer.record.assert_not_awaited()

    async def test_an_abandoned_batch_cannot_be_applied(self):
        use_case, _, writer = _use_case(batch=_batch(ImportBatchStatus.ABANDONED))
        with pytest.raises(DomainError):
            await use_case.execute(TENANT, BATCH, ACTOR, now=NOW)
        writer.record.assert_not_awaited()

    async def test_an_unknown_batch_is_a_not_found(self):
        use_case, imports, _ = _use_case()
        imports.get_batch.return_value = None
        with pytest.raises(NotFoundError):
            await use_case.execute(TENANT, BATCH, ACTOR, now=NOW)

    async def test_a_successful_apply_marks_the_batch_with_the_count(self):
        use_case, imports, _ = _use_case(rows=[_row()])
        result, batch = await use_case.execute(TENANT, BATCH, ACTOR, now=NOW)
        assert (result.imported, batch.status) == (1, ImportBatchStatus.APPLIED)
        saved = imports.save_batch.await_args.args[0]
        assert saved.status is ImportBatchStatus.APPLIED
        assert saved.events[0].accepted_count == 1


class TestRowIdempotency:
    async def test_a_row_already_imported_is_skipped_not_rewritten(self):
        use_case, _, writer = _use_case(rows=[_row(imported="sess-old")])
        result, _ = await use_case.execute(TENANT, BATCH, ACTOR, now=NOW)
        assert (result.imported, result.skipped_already_imported) == (0, 1)
        writer.record.assert_not_awaited()

    async def test_importing_records_the_session_on_the_row(self):
        use_case, imports, _ = _use_case(rows=[_row()], session_id="sess-9")
        await use_case.execute(TENANT, BATCH, ACTOR, now=NOW)
        args, _ = imports.mark_row_imported.await_args
        assert args[1] == "r-1"
        assert args[2] == "sess-9"

    async def test_the_row_update_is_not_a_second_insert(self):
        """add_rows inserts; a replay key is unique per tenant, so marking updates."""
        use_case, imports, _ = _use_case(rows=[_row()])
        await use_case.execute(TENANT, BATCH, ACTOR, now=NOW)
        imports.add_rows.assert_not_awaited()
        imports.mark_row_imported.assert_awaited_once()

    async def test_a_mixed_batch_counts_each_outcome(self):
        rows = [
            _row("r-1", number=1),
            _row("r-2", number=2, imported="sess-old"),
            _row("r-3", number=3, outcome=ImportRowOutcome.UNRESOLVED_MEMBER),
        ]
        use_case, _, writer = _use_case(rows=rows)
        result, _ = await use_case.execute(TENANT, BATCH, ACTOR, now=NOW)
        assert (result.imported, result.skipped_already_imported, result.not_importable) == (
            1,
            1,
            1,
        )
        assert result.total_considered == 3
        assert writer.record.await_count == 1


class TestHonestZero:
    @pytest.mark.parametrize(
        "outcome",
        [
            ImportRowOutcome.UNRESOLVED_MEMBER,
            ImportRowOutcome.UNRESOLVED_SERVICE,
            ImportRowOutcome.UNMAPPED_PRACTITIONER,
            ImportRowOutcome.AMBIGUOUS_PRACTITIONER,
            ImportRowOutcome.MISSING_PRACTITIONER,
            ImportRowOutcome.CONFLICTING,
            ImportRowOutcome.DUPLICATE,
            ImportRowOutcome.REJECTED,
        ],
    )
    async def test_no_held_outcome_is_written(self, outcome):
        use_case, _, writer = _use_case(rows=[_row(outcome=outcome)])
        result, _ = await use_case.execute(TENANT, BATCH, ACTOR, now=NOW)
        assert result.imported == 0
        writer.record.assert_not_awaited()

    async def test_a_batch_of_unresolved_rows_applies_with_zero_imported(self):
        """The current real state: staging works, nothing is importable yet."""
        rows = [
            _row("r-1", number=1, outcome=ImportRowOutcome.UNRESOLVED_MEMBER),
            _row("r-2", number=2, outcome=ImportRowOutcome.UNRESOLVED_SERVICE),
        ]
        use_case, imports, writer = _use_case(rows=rows)
        result, _ = await use_case.execute(TENANT, BATCH, ACTOR, now=NOW)
        assert (result.imported, result.not_importable) == (0, 2)
        writer.record.assert_not_awaited()
        assert imports.save_batch.await_args.args[0].events[0].accepted_count == 0
