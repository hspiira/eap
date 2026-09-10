"""SQLAlchemy repository for staged member roster imports."""

from collections.abc import Sequence

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.member_import import MemberImportBatchEntity, MemberImportRowEntity
from app.domain.repositories.member_import_repository import MemberImportRepository
from app.domain.value_objects.core import TenantId
from app.domain.value_objects.ids import MemberImportBatchId, MemberImportRowId
from app.infrastructure.mappers.member_import_mapper import MemberImportMapper
from app.infrastructure.models.member_import_model import (
    MemberImportBatchModel,
    MemberImportRowModel,
)
from app.shared.utils.replay_key import RELEASED_PREFIX


async def _count(session: AsyncSession, statement) -> int:
    subquery = statement.order_by(None).subquery()
    return int(await session.scalar(select(func.count()).select_from(subquery)) or 0)


class MemberImportRepositoryImpl(MemberImportRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_batch(
        self, tenant_id: TenantId, batch_id: MemberImportBatchId
    ) -> MemberImportBatchEntity | None:
        model = await self.session.scalar(
            select(MemberImportBatchModel).where(
                MemberImportBatchModel.id == batch_id.value,
                MemberImportBatchModel.tenant_id == tenant_id.value,
            )
        )
        return MemberImportMapper.batch_to_entity(model) if model else None

    async def find_batch_by_hash(
        self, tenant_id: TenantId, file_hash: str
    ) -> MemberImportBatchEntity | None:
        model = await self.session.scalar(
            select(MemberImportBatchModel).where(
                MemberImportBatchModel.tenant_id == tenant_id.value,
                MemberImportBatchModel.file_hash == file_hash,
            )
        )
        return MemberImportMapper.batch_to_entity(model) if model else None

    async def save_batch(self, batch: MemberImportBatchEntity) -> None:
        await self.session.merge(MemberImportMapper.batch_to_model(batch))
        await self.session.flush()

    async def add_rows(self, rows: Sequence[MemberImportRowEntity]) -> None:
        for row in rows:
            self.session.add(MemberImportMapper.row_to_model(row))
        await self.session.flush()

    async def get_row(
        self, tenant_id: TenantId, batch_id: MemberImportBatchId, row_id: MemberImportRowId
    ) -> MemberImportRowEntity | None:
        model = await self.session.scalar(
            select(MemberImportRowModel).where(
                MemberImportRowModel.id == row_id.value,
                MemberImportRowModel.tenant_id == tenant_id.value,
                MemberImportRowModel.batch_id == batch_id.value,
            )
        )
        return MemberImportMapper.row_to_entity(model) if model else None

    async def list_rows(
        self,
        tenant_id: TenantId,
        batch_id: MemberImportBatchId,
        *,
        outcome: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[Sequence[MemberImportRowEntity], int]:
        statement = select(MemberImportRowModel).where(
            MemberImportRowModel.tenant_id == tenant_id.value,
            MemberImportRowModel.batch_id == batch_id.value,
        )
        if outcome:
            statement = statement.where(MemberImportRowModel.outcome == outcome)
        total = await _count(self.session, statement)
        rows = await self.session.scalars(
            statement.order_by(MemberImportRowModel.row_number).limit(limit).offset(offset)
        )
        return [MemberImportMapper.row_to_entity(m) for m in rows], total

    async def set_row_decision(
        self, tenant_id: TenantId, row_id: MemberImportRowId, decision: str
    ) -> None:
        await self.session.execute(
            update(MemberImportRowModel)
            .where(
                MemberImportRowModel.id == row_id.value,
                MemberImportRowModel.tenant_id == tenant_id.value,
                MemberImportRowModel.outcome == "New",
            )
            .values(decision=decision)
        )
        await self.session.flush()

    async def mark_row_imported(
        self, tenant_id: TenantId, row_id: MemberImportRowId, member_id: str
    ) -> None:
        await self.session.execute(
            update(MemberImportRowModel)
            .where(
                MemberImportRowModel.id == row_id.value,
                MemberImportRowModel.tenant_id == tenant_id.value,
                MemberImportRowModel.imported_member_id.is_(None),
            )
            .values(imported_member_id=member_id)
        )
        await self.session.flush()

    async def mark_row_failed(
        self, tenant_id: TenantId, row_id: MemberImportRowId, message: str
    ) -> None:
        await self.session.execute(
            update(MemberImportRowModel)
            .where(
                MemberImportRowModel.id == row_id.value,
                MemberImportRowModel.tenant_id == tenant_id.value,
                MemberImportRowModel.imported_member_id.is_(None),
            )
            .values(outcome="Failed", message=message)
        )
        await self.session.flush()

    async def release_replay_keys(self, tenant_id: TenantId, batch_id: MemberImportBatchId) -> int:
        return await self._release(tenant_id, MemberImportRowModel.batch_id == batch_id.value)

    async def release_superseded_rows(self, tenant_id: TenantId, file_hash: str) -> int:
        return await self._release(
            tenant_id,
            MemberImportRowModel.batch_id.in_(
                select(MemberImportBatchModel.id).where(
                    MemberImportBatchModel.tenant_id == tenant_id.value,
                    MemberImportBatchModel.file_hash == file_hash,
                )
            ),
        )

    async def _release(self, tenant_id: TenantId, scope) -> int:
        """Give up the keys of rows in `scope` that never produced a member."""
        result = await self.session.execute(
            update(MemberImportRowModel)
            .where(
                MemberImportRowModel.tenant_id == tenant_id.value,
                scope,
                MemberImportRowModel.imported_member_id.is_(None),
                MemberImportRowModel.replay_key.not_like(f"{RELEASED_PREFIX}%"),
            )
            .values(
                replay_key=RELEASED_PREFIX
                + MemberImportRowModel.batch_id
                + ":"
                + MemberImportRowModel.replay_key
            )
        )
        await self.session.flush()
        return result.rowcount or 0

    async def find_row_by_replay_key(
        self, tenant_id: TenantId, replay_key: str
    ) -> MemberImportRowEntity | None:
        model = await self.session.scalar(
            select(MemberImportRowModel).where(
                MemberImportRowModel.tenant_id == tenant_id.value,
                MemberImportRowModel.replay_key == replay_key,
            )
        )
        return MemberImportMapper.row_to_entity(model) if model else None

    async def outcome_counts(
        self, tenant_id: TenantId, batch_id: MemberImportBatchId
    ) -> dict[str, int]:
        rows = await self.session.execute(
            select(MemberImportRowModel.outcome, func.count())
            .where(
                MemberImportRowModel.tenant_id == tenant_id.value,
                MemberImportRowModel.batch_id == batch_id.value,
            )
            .group_by(MemberImportRowModel.outcome)
        )
        return {str(outcome): int(count) for outcome, count in rows}
