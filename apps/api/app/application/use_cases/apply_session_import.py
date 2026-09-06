"""Apply a staged import batch through the historical write path.

Idempotency and row marking live here because the batch and replay keys are
this module's tables. The write itself is agent 1's
`RecordHistoricalSessionUseCase`, which does not consult the booking gate, so
a session delivered by a practitioner who is off the panel today still records.

Today this imports zero rows. No staged row can reach Accepted, because the
write path requires a member and a service and nothing resolves either yet.
That is the honest result rather than a defect in this use case: see the
UnresolvedMember and UnresolvedService outcomes in the staging service.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol

from app.domain.entities.session_import import SessionImportRowEntity
from app.domain.enums.provider_network import ImportBatchStatus
from app.domain.exceptions import DomainError, NotFoundError
from app.domain.repositories.provider_network_repository import SessionImportRepository
from app.domain.value_objects.core import TenantId, UserId
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
    imported: int
    skipped_already_imported: int
    not_importable: int

    @property
    def total_considered(self) -> int:
        return self.imported + self.skipped_already_imported + self.not_importable


class ApplyImportBatchUseCase:
    def __init__(self, imports: SessionImportRepository, writer: HistoricalSessionWriter):
        self._imports = imports
        self._writer = writer

    async def execute(
        self,
        tenant_id: TenantId,
        batch_id: SessionImportBatchId,
        actor: UserId,
        *,
        now: datetime,
    ) -> tuple[ApplyResult, int]:
        """Write every importable row, then mark the batch applied.

        A batch that is not Staged is refused by the aggregate, so applying
        twice cannot write twice even if the first attempt is replayed.
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

        result = await self._apply_rows(tenant_id, batch_id)
        batch.mark_applied(actor, at=now, accepted_count=result.imported)
        await self._imports.save_batch(batch)
        return result, result.imported

    async def _apply_rows(self, tenant_id: TenantId, batch_id: SessionImportBatchId) -> ApplyResult:
        imported = skipped = not_importable = 0
        offset = 0
        while True:
            rows, total = await self._imports.list_rows(
                tenant_id, batch_id, limit=200, offset=offset
            )
            if not rows:
                break
            for row in rows:
                if row.imported_session_id is not None:
                    skipped += 1
                elif not row.is_importable:
                    not_importable += 1
                else:
                    session_id = await self._writer.record(row, tenant_id)
                    row.mark_imported(session_id)
                    await self._imports.mark_row_imported(tenant_id, row.id.value, session_id)
                    imported += 1
            offset += len(rows)
            if offset >= total:
                break
        return ApplyResult(
            imported=imported,
            skipped_already_imported=skipped,
            not_importable=not_importable,
        )
