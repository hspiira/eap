"""SQLAlchemy persistence for the staged practitioner workbook import."""

from collections.abc import Sequence

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.practitioner_import import (
    PractitionerImportBatchEntity,
    PractitionerImportRowEntity,
)
from app.domain.repositories.practitioner_import_repository import PractitionerImportRepository
from app.domain.value_objects.core import TenantId
from app.domain.value_objects.provider_network import PractitionerImportBatchId
from app.infrastructure.mappers.practitioner_import_mapper import PractitionerImportMapper
from app.infrastructure.models.practitioner_import_model import (
    PractitionerImportBatchModel,
    PractitionerImportRowModel,
)


class PractitionerImportRepositoryImpl(PractitionerImportRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_batch(
        self, tenant_id: TenantId, batch_id: PractitionerImportBatchId
    ) -> PractitionerImportBatchEntity | None:
        model = await self.session.scalar(
            select(PractitionerImportBatchModel).where(
                PractitionerImportBatchModel.id == batch_id.value,
                PractitionerImportBatchModel.tenant_id == tenant_id.value,
            )
        )
        return PractitionerImportMapper.batch_to_entity(model) if model else None

    async def find_batch_by_hash(
        self, tenant_id: TenantId, file_hash: str
    ) -> PractitionerImportBatchEntity | None:
        model = await self.session.scalar(
            select(PractitionerImportBatchModel).where(
                PractitionerImportBatchModel.tenant_id == tenant_id.value,
                PractitionerImportBatchModel.file_hash == file_hash,
            )
        )
        return PractitionerImportMapper.batch_to_entity(model) if model else None

    async def save_batch(self, batch: PractitionerImportBatchEntity) -> None:
        await self.session.merge(PractitionerImportMapper.batch_to_model(batch))
        await self.session.flush()

    async def add_rows(
        self, rows: Sequence[PractitionerImportRowEntity], *, file_hash: str
    ) -> None:
        for row in rows:
            self.session.add(PractitionerImportMapper.row_to_model(row, file_hash=file_hash))
        await self.session.flush()

    async def list_rows(
        self,
        tenant_id: TenantId,
        batch_id: PractitionerImportBatchId,
        *,
        outcome: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[Sequence[PractitionerImportRowEntity], int]:
        statement = select(PractitionerImportRowModel).where(
            PractitionerImportRowModel.tenant_id == tenant_id.value,
            PractitionerImportRowModel.batch_id == batch_id.value,
        )
        if outcome:
            statement = statement.where(PractitionerImportRowModel.outcome == outcome)
        total = await self.session.scalar(select(func.count()).select_from(statement.subquery()))
        models = await self.session.scalars(
            statement.order_by(
                PractitionerImportRowModel.sheet_name, PractitionerImportRowModel.row_number
            )
            .limit(limit)
            .offset(offset)
        )
        return [PractitionerImportMapper.row_to_entity(m) for m in models], int(total or 0)

    async def find_row_by_replay_key(
        self, tenant_id: TenantId, replay_key: str
    ) -> PractitionerImportRowEntity | None:
        model = await self.session.scalar(
            select(PractitionerImportRowModel).where(
                PractitionerImportRowModel.tenant_id == tenant_id.value,
                PractitionerImportRowModel.replay_key == replay_key,
            )
        )
        return PractitionerImportMapper.row_to_entity(model) if model else None

    async def record_row_apply(self, row: PractitionerImportRowEntity) -> None:
        await self.session.execute(
            update(PractitionerImportRowModel)
            .where(
                PractitionerImportRowModel.tenant_id == row.tenant_id.value,
                PractitionerImportRowModel.id == row.id.value,
            )
            .values(
                outcome=row.outcome.value,
                reasons=list(row.reasons),
                imported_provider_id=row.imported_provider_id,
                imported_organisation_id=row.imported_organisation_id,
                imported_affiliation_id=row.imported_affiliation_id,
            )
        )
        await self.session.flush()

    async def outcome_counts(
        self, tenant_id: TenantId, batch_id: PractitionerImportBatchId
    ) -> dict[str, int]:
        rows = await self.session.execute(
            select(PractitionerImportRowModel.outcome, func.count())
            .where(
                PractitionerImportRowModel.tenant_id == tenant_id.value,
                PractitionerImportRowModel.batch_id == batch_id.value,
            )
            .group_by(PractitionerImportRowModel.outcome)
        )
        return {str(outcome): int(count) for outcome, count in rows}
