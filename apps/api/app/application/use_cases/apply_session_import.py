"""Apply a staged import batch through the historical write path.

Idempotency and row marking live here because the batch and replay keys are
this module's tables. The write itself is agent 1's
`RecordHistoricalSessionUseCase`, which does not consult the booking gate, so
a session delivered by a practitioner who is off the panel today still records.

Writes at most `limit` still-pending rows per call, one at a time, so a large
batch does not have to write everything in a single request or a single
transaction. A caller keeps calling while the result's `remaining` is above
zero; the batch only closes once a call finds nothing left. See the member
importer's chunked apply for the same reason, and the ninth defect in
docs/migrations/MEMBERS_MIGRATION.md for the incident that motivated it: a
batch large enough to write for minutes exceeds a platform request timeout,
and writing everything in one transaction loses every row already written in
that same call the moment it does.
"""

from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from datetime import datetime
from typing import Protocol

from sqlalchemy.exc import IntegrityError

from app.domain.entities.client import ClientEntity
from app.domain.entities.eligible_member import EligibleMember
from app.domain.entities.service import ServiceEntity
from app.domain.entities.session_import import (
    SessionImportBatchEntity,
    SessionImportRowEntity,
)
from app.domain.enums.provider_network import ImportBatchStatus
from app.domain.exceptions import DomainError, NotFoundError
from app.domain.repositories.client_repository import ClientRepository
from app.domain.repositories.eligible_member_repository import EligibleMemberRepository
from app.domain.repositories.provider_network_repository import SessionImportRepository
from app.domain.repositories.service_repository import ServiceRepository
from app.domain.value_objects.core import ClientId, EligibleMemberId, ServiceId, TenantId, UserId
from app.domain.value_objects.provider_network import SessionImportBatchId


class HistoricalSessionWriter(Protocol):
    """The seam onto agent 1's Admin-only historical write path."""

    async def record(self, row: SessionImportRowEntity, tenant_id: TenantId) -> str:
        """Write one past session and return its id."""
        ...


class ImportRowNotConvertible(DomainError):
    """An accepted row cannot be turned into a session record.

    Unreachable while nothing resolves a member or a service. It fails loudly
    rather than skipping, so a row that somehow reached Accepted without the
    fields the write path needs cannot be silently dropped from a batch that
    then reports itself applied.
    """

    def __init__(self, row_number: int, detail: str):
        super().__init__(
            f"Staged row {row_number} cannot be imported: {detail}",
            error_code="import_row_not_convertible",
            http_status=422,
        )


@dataclass(frozen=True)
class ApplyResult:
    """What one chunked apply call wrote. Call again while `remaining` is above zero."""

    imported: int
    failed: int
    remaining: int
    done: bool


class ApplyImportBatchUseCase:
    def __init__(
        self,
        imports: SessionImportRepository,
        writer: HistoricalSessionWriter,
        clients: ClientRepository,
        members: EligibleMemberRepository,
        services: ServiceRepository,
    ):
        self._imports = imports
        self._writer = writer
        self._clients = clients
        self._members = members
        self._services = services

    async def execute(
        self,
        tenant_id: TenantId,
        batch_id: SessionImportBatchId,
        actor: UserId,
        *,
        now: datetime,
        limit: int,
        after_row: Callable[[], Awaitable[None]],
        rollback: Callable[[], Awaitable[None]],
    ) -> tuple[ApplyResult, SessionImportBatchEntity]:
        """Write up to `limit` still-pending rows, then close the batch if none remain.

        `after_row` is awaited once per row (and once more if the batch
        closes), and is the caller's commit: each row's write survives on its
        own, independent of whether a later row in this same call raises or
        the call itself never finishes responding. `rollback` discards a row
        whose write cannot stand.

        A batch that is not Staged is refused, so applying twice, or a
        replayed request, cannot write twice.
        """
        batch = await self._imports.get_batch(tenant_id, batch_id)
        if batch is None:
            raise NotFoundError(
                "Import batch not found",
                resource_type="SessionImportBatch",
                resource_id=batch_id.value,
            )
        if batch.status is not ImportBatchStatus.STAGED:
            raise DomainError(
                f"Batch {batch_id.value} is {batch.status.value} and cannot be applied again",
                error_code="import_batch_not_staged",
                http_status=409,
            )

        imported = failed = 0
        rows = await self._imports.list_pending_rows(tenant_id, batch_id, limit=limit)
        reference = _ReferenceData(self._clients, self._members, self._services)
        for row in rows:
            if await self._write_row(tenant_id, row, reference, rollback):
                imported += 1
            else:
                failed += 1
            await after_row()

        remaining = await self._imports.count_pending_rows(tenant_id, batch_id)
        done = remaining == 0
        if done:
            accepted_count = await self._imports.count_imported_rows(tenant_id, batch_id)
            batch.mark_applied(actor, at=now, accepted_count=accepted_count)
            await self._imports.save_batch(batch)
            await after_row()
        return ApplyResult(imported=imported, failed=failed, remaining=remaining, done=done), batch

    async def _write_row(
        self,
        tenant_id: TenantId,
        row: SessionImportRowEntity,
        reference: "_ReferenceData",
        rollback: Callable[[], Awaitable[None]],
    ) -> bool:
        """Re-validate, then write one row. True on success, False on a recorded failure.

        A batch can sit staged for days waiting on reference data (see
        docs/operations/DEV_DATA_LOAD.md), so the member, client and service
        staging resolved are re-checked here rather than trusted: any of them
        can have been merged, deleted, or moved to another client since. The
        practitioner is already re-checked inside the write path itself.

        Never raises: every failure this can reach is recorded on the row and
        the batch's apply loop moves on, the same way the member importer's
        `_write_row` does, and for the same reason -- one bad row must not
        cost every row after it in the same call.
        """
        stale = await reference.stale_reason(tenant_id, row)
        if stale is not None:
            return await self._fail_row(tenant_id, row, stale)
        try:
            session_id = await self._writer.record(row, tenant_id)
        except DomainError as exc:
            return await self._fail_row(tenant_id, row, str(exc))
        except IntegrityError as exc:
            await rollback()
            return await self._fail_row(tenant_id, row, str(exc).split("\n", 1)[-1])
        if not await self._imports.mark_row_imported(tenant_id, row.id.value, session_id):
            # Another apply claimed the row first; discard the session this call wrote.
            await rollback()
            return False
        row.mark_imported(session_id)
        return True

    async def _fail_row(self, tenant_id: TenantId, row: SessionImportRowEntity, why: str) -> bool:
        row.mark_failed(why)
        await self._imports.mark_row_failed(tenant_id, row.id.value, why)
        return False


class _ReferenceData:
    """The clients, members and services a chunk's rows are re-validated against.

    Each is read once and remembered for the rest of the chunk.
    """

    def __init__(
        self,
        clients: ClientRepository,
        members: EligibleMemberRepository,
        services: ServiceRepository,
    ) -> None:
        self._clients = clients
        self._members = members
        self._services = services
        self._client_cache: dict[str, ClientEntity | None] = {}
        self._member_cache: dict[str, EligibleMember | None] = {}
        self._service_cache: dict[str, ServiceEntity | None] = {}

    async def stale_reason(self, tenant_id: TenantId, row: SessionImportRowEntity) -> str | None:
        """A reason the row can no longer be written, or None if everything still resolves."""
        if row.client_id is not None:
            client = await self._client(row.client_id)
            if client is None or client.tenant_id.value != tenant_id.value:
                return f"Client {row.client_id} no longer exists in this tenant"
        if row.member_id is not None:
            member = await self._member(row.member_id)
            if member is None or member.tenant_id.value != tenant_id.value:
                return f"Member {row.member_id} no longer exists in this tenant"
            if row.client_id is not None and member.client_id.value != row.client_id:
                return f"Member {row.member_id} no longer belongs to client {row.client_id}"
        if row.service_id is not None:
            service = await self._service(row.service_id)
            if service is None or service.tenant_id.value != tenant_id.value:
                return f"Service {row.service_id} no longer exists in this tenant"
        return None

    async def _client(self, client_id: str) -> ClientEntity | None:
        if client_id not in self._client_cache:
            self._client_cache[client_id] = await self._clients.get_by_id(ClientId(client_id))
        return self._client_cache[client_id]

    async def _member(self, member_id: str) -> EligibleMember | None:
        if member_id not in self._member_cache:
            self._member_cache[member_id] = await self._members.get_by_id(
                EligibleMemberId(member_id)
            )
        return self._member_cache[member_id]

    async def _service(self, service_id: str) -> ServiceEntity | None:
        if service_id not in self._service_cache:
            self._service_cache[service_id] = await self._services.get_by_id(ServiceId(service_id))
        return self._service_cache[service_id]
