"""Applying a batch: chunking, idempotency, row marking, and re-validation.

Agent 1 owns the write itself and left replay protection here, because the
batch and row keys are this module's tables.
"""

from datetime import UTC, date, datetime
from types import SimpleNamespace
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
from app.domain.value_objects.core import (
    ClientId,
    ProviderId,
    TenantId,
    UserId,
)
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


def _row(row_id="r-1", number=1, *, client_id="cli-1", member_id="mem-1", service_id="svc-1"):
    return SessionImportRowEntity(
        id=SessionImportRowId(row_id),
        batch_id=BATCH,
        tenant_id=TENANT,
        row_number=number,
        source_record_key=None,
        raw_practitioner_name="Alice Nakato",
        session_date=date(2025, 4, 2),
        outcome=ImportRowOutcome.ACCEPTED,
        provider_id=ProviderId("prov-1"),
        client_id=client_id,
        member_id=member_id,
        service_id=service_id,
        reasons=(),
        created_at=NOW,
    )


def _use_case(*, batch=None, pending=(), remaining=0, imported_count=None, session_id="sess-1"):
    imports = AsyncMock()
    imports.get_batch.return_value = batch if batch is not None else _batch()
    imports.list_pending_rows.return_value = list(pending)
    imports.count_pending_rows.return_value = remaining
    imports.count_imported_rows.return_value = (
        imported_count if imported_count is not None else len(pending)
    )
    imports.mark_row_imported.return_value = True
    writer = AsyncMock()
    writer.record.return_value = session_id
    clients = AsyncMock()
    clients.get_by_id.return_value = SimpleNamespace(tenant_id=TENANT)
    members = AsyncMock()
    members.get_by_id.return_value = SimpleNamespace(tenant_id=TENANT, client_id=ClientId("cli-1"))
    services = AsyncMock()
    services.get_by_id.return_value = SimpleNamespace(tenant_id=TENANT)
    use_case = ApplyImportBatchUseCase(imports, writer, clients, members, services)
    return use_case, imports, writer, clients, members, services


async def _execute(use_case, *, limit=50, batch_id=BATCH, rollback=None):
    after_row = AsyncMock()
    result, batch = await use_case.execute(
        TENANT,
        batch_id,
        ACTOR,
        now=NOW,
        limit=limit,
        after_row=after_row,
        rollback=rollback or AsyncMock(),
    )
    return result, batch, after_row


class TestBatchIdempotency:
    async def test_an_applied_batch_cannot_be_applied_again(self):
        use_case, _, writer, *_ = _use_case(batch=_batch(ImportBatchStatus.APPLIED))
        with pytest.raises(DomainError) as caught:
            await _execute(use_case)
        assert caught.value.error_code == "import_batch_not_staged"
        assert caught.value.http_status == 409
        writer.record.assert_not_awaited()

    async def test_an_abandoned_batch_cannot_be_applied(self):
        use_case, _, writer, *_ = _use_case(batch=_batch(ImportBatchStatus.ABANDONED))
        with pytest.raises(DomainError):
            await _execute(use_case)
        writer.record.assert_not_awaited()

    async def test_an_unknown_batch_is_a_not_found(self):
        use_case, imports, *_ = _use_case()
        imports.get_batch.return_value = None
        with pytest.raises(NotFoundError):
            await _execute(use_case)

    async def test_a_successful_apply_that_empties_the_batch_marks_it_applied(self):
        use_case, imports, *_ = _use_case(pending=[_row()], remaining=0)
        result, batch, _ = await _execute(use_case)
        assert (result.imported, result.done, batch.status) == (1, True, ImportBatchStatus.APPLIED)
        saved = imports.save_batch.await_args.args[0]
        assert saved.status is ImportBatchStatus.APPLIED
        assert saved.events[0].accepted_count == 1

    async def test_a_chunk_that_leaves_rows_pending_does_not_close_the_batch(self):
        use_case, imports, *_ = _use_case(pending=[_row()], remaining=5)
        result, batch, _ = await _execute(use_case)
        assert (result.done, result.remaining) == (False, 5)
        assert batch.status is ImportBatchStatus.STAGED
        imports.save_batch.assert_not_awaited()


class TestChunking:
    async def test_the_limit_is_passed_through_to_the_pending_query(self):
        use_case, imports, *_ = _use_case(pending=[])
        await _execute(use_case, limit=25)
        assert imports.list_pending_rows.await_args.kwargs == {"limit": 25}

    async def test_after_row_is_awaited_once_per_row_written(self):
        rows = [_row("r-1", 1), _row("r-2", 2)]
        use_case, _, _, *_ = _use_case(pending=rows, remaining=0)
        _, _, after_row = await _execute(use_case)
        # Once per row, plus once more for closing the batch.
        assert after_row.await_count == 3

    async def test_after_row_is_not_called_an_extra_time_when_the_batch_stays_open(self):
        use_case, *_ = _use_case(pending=[_row()], remaining=3)
        _, _, after_row = await _execute(use_case)
        assert after_row.await_count == 1


class TestRowWriting:
    async def test_importing_records_the_session_on_the_row(self):
        use_case, imports, *_ = _use_case(pending=[_row()], session_id="sess-9")
        await _execute(use_case)
        args, _ = imports.mark_row_imported.await_args
        assert args[1] == "r-1"
        assert args[2] == "sess-9"

    async def test_a_batch_of_several_rows_counts_each_write(self):
        rows = [_row("r-1", 1), _row("r-2", 2)]
        use_case, _, writer, *_ = _use_case(pending=rows, remaining=0)
        result, _, _ = await _execute(use_case)
        assert result.imported == 2
        assert writer.record.await_count == 2


class TestWriterFailureIsolation:
    """One row's write path raising must not cost every row after it."""

    async def test_a_row_the_writer_refuses_is_marked_failed_and_the_batch_continues(self):
        rows = [_row("r-1", 1), _row("r-2", 2)]
        use_case, imports, writer, *_ = _use_case(pending=rows, remaining=0)
        writer.record.side_effect = [DomainError("no such thing", error_code="x"), "sess-2"]
        result, _, _ = await _execute(use_case)
        assert (result.imported, result.failed) == (1, 1)
        reason = imports.mark_row_failed.await_args.args[2]
        assert reason == "no such thing"

    async def test_a_failed_row_is_not_also_marked_imported(self):
        use_case, imports, writer, *_ = _use_case(pending=[_row()], remaining=0)
        writer.record.side_effect = DomainError("boom", error_code="x")
        await _execute(use_case)
        imports.mark_row_imported.assert_not_awaited()
        imports.mark_row_failed.assert_awaited_once()


class TestRevalidation:
    """Staging resolved these ids; a batch can sit staged for days before apply."""

    async def test_a_client_that_no_longer_exists_fails_the_row_without_writing(self):
        use_case, imports, writer, clients, _, _ = _use_case(pending=[_row()], remaining=0)
        clients.get_by_id.return_value = None
        result, _, _ = await _execute(use_case)
        assert (result.imported, result.failed) == (0, 1)
        writer.record.assert_not_awaited()
        reason = imports.mark_row_failed.await_args.args[2]
        assert "Client" in reason

    async def test_a_member_moved_to_another_client_fails_the_row(self):
        use_case, imports, writer, _, members, _ = _use_case(pending=[_row()], remaining=0)
        members.get_by_id.return_value = SimpleNamespace(
            tenant_id=TENANT, client_id=ClientId("cli-2")
        )
        result, _, _ = await _execute(use_case)
        assert (result.imported, result.failed) == (0, 1)
        writer.record.assert_not_awaited()
        reason = imports.mark_row_failed.await_args.args[2]
        assert "no longer belongs to client" in reason

    async def test_a_service_removed_from_the_catalogue_fails_the_row(self):
        use_case, imports, writer, _, _, services = _use_case(pending=[_row()], remaining=0)
        services.get_by_id.return_value = None
        result, _, _ = await _execute(use_case)
        assert (result.imported, result.failed) == (0, 1)
        writer.record.assert_not_awaited()

    async def test_a_member_from_another_tenant_fails_the_row(self):
        use_case, imports, writer, _, members, _ = _use_case(pending=[_row()], remaining=0)
        members.get_by_id.return_value = SimpleNamespace(
            tenant_id=TenantId("other-tenant"), client_id=ClientId("cli-1")
        )
        result, _, _ = await _execute(use_case)
        assert (result.imported, result.failed) == (0, 1)
        writer.record.assert_not_awaited()

    async def test_a_row_with_no_client_or_member_skips_that_check(self):
        """A company-wide row with no member must not be failed for lacking one."""
        row = _row(member_id=None)
        use_case, _, writer, *_ = _use_case(pending=[row], remaining=0)
        result, _, _ = await _execute(use_case)
        assert result.imported == 1
        writer.record.assert_awaited_once()


class TestConcurrentApply:
    """Two applies of one batch both read it as Staged; claiming the row decides."""

    async def test_a_row_another_apply_already_claimed_is_not_counted_as_imported(self):
        use_case, imports, writer, *_ = _use_case(pending=[_row()], remaining=0)
        imports.mark_row_imported.return_value = False
        rollback = AsyncMock()

        result, _, _ = await _execute(use_case, rollback=rollback)

        assert (result.imported, result.failed) == (0, 1)
        rollback.assert_awaited_once()

    async def test_a_lost_claim_does_not_mark_the_row_failed(self):
        """The winner's write stands; the row is imported, not broken."""
        use_case, imports, _, *_ = _use_case(pending=[_row()], remaining=0)
        imports.mark_row_imported.return_value = False

        await _execute(use_case, rollback=AsyncMock())

        imports.mark_row_failed.assert_not_awaited()

    async def test_the_batch_still_closes_when_nothing_is_left(self):
        use_case, imports, *_ = _use_case(pending=[_row()], remaining=0)
        imports.mark_row_imported.return_value = False

        result, batch, _ = await _execute(use_case, rollback=AsyncMock())

        assert result.done is True
        assert batch.status is ImportBatchStatus.APPLIED


class TestReferenceDataIsReadOncePerChunk:
    async def test_rows_sharing_a_client_member_and_service_cost_one_read_each(self):
        rows = [_row(f"r-{n}", n) for n in range(1, 11)]
        use_case, _, _, clients, members, services = _use_case(pending=rows, remaining=0)

        result, _, _ = await _execute(use_case)

        assert result.imported == 10
        assert clients.get_by_id.await_count == 1
        assert members.get_by_id.await_count == 1
        assert services.get_by_id.await_count == 1

    async def test_a_stale_reference_still_fails_every_row_that_names_it(self):
        """Caching must not let a row through on a second look."""
        rows = [_row(f"r-{n}", n) for n in range(1, 4)]
        use_case, imports, writer, clients, _, _ = _use_case(pending=rows, remaining=0)
        clients.get_by_id.return_value = None

        result, _, _ = await _execute(use_case)

        assert (result.imported, result.failed) == (0, 3)
        writer.record.assert_not_awaited()
        assert imports.mark_row_failed.await_count == 3
