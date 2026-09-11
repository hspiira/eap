"""SQLAlchemy repository for staged member roster imports."""

from collections.abc import Sequence

from sqlalchemy import and_ as sa_and
from sqlalchemy import func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.member_import import MemberImportBatchEntity, MemberImportRowEntity
from app.domain.enums.provider_network import ImportBatchStatus
from app.domain.repositories.member_import_repository import MemberImportRepository
from app.domain.value_objects.core import TenantId
from app.domain.value_objects.ids import MemberImportBatchId, MemberImportRowId
from app.infrastructure.mappers.member_import_mapper import MemberImportMapper
from app.infrastructure.models.member_import_model import (
    MemberImportBatchModel,
    MemberImportRowModel,
)
from app.shared.utils.replay_key import FILE_PREFIX, RELEASED_PREFIX


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
        """The Staged batch holding this hash, if any.

        A hash can belong to several historical batches (an old one abandoned
        or applied, a newer one staged), since only a Staged batch holds the
        hash's partial unique index. Filtering by status here, rather than
        fetching an arbitrary match and checking it in Python, is required:
        an unfiltered query has no ORDER BY and can return the wrong one,
        letting a second stage attempt reach the INSERT and fail on the
        index instead of the clean 409 this check exists to raise.
        """
        model = await self.session.scalar(
            select(MemberImportBatchModel).where(
                MemberImportBatchModel.tenant_id == tenant_id.value,
                MemberImportBatchModel.file_hash == file_hash,
                MemberImportBatchModel.status == ImportBatchStatus.STAGED.value,
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
                MemberImportRowModel.outcome.in_(("New", "Duplicate")),
            )
            .values(decision=decision)
        )
        await self.session.flush()

    async def mark_row_imported(
        self,
        tenant_id: TenantId,
        row_id: MemberImportRowId,
        member_id: str,
        message: str | None = None,
    ) -> bool:
        values: dict[str, str] = {"imported_member_id": member_id}
        if message is not None:
            values["message"] = message
        result = await self.session.execute(
            update(MemberImportRowModel)
            .where(
                MemberImportRowModel.id == row_id.value,
                MemberImportRowModel.tenant_id == tenant_id.value,
                MemberImportRowModel.imported_member_id.is_(None),
            )
            .values(**values)
        )
        await self.session.flush()
        return result.rowcount > 0

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
        """Give up the keys of rows in `scope` that hold no identity claim.

        Two kinds qualify. A row that produced no member never claimed
        anything. So did a row keyed `file:{hash}:row:{n}`, whatever it went
        on to write: that form names one row of one file rather than a
        Staff_ID, and staging the same file again recomputes the identical
        string, so a row still holding one collides with its own successor on
        the (tenant_id, replay_key) index. Only the identity form,
        `key:{client}:{staff_id}`, is a claim worth keeping past a write.
        """
        result = await self.session.execute(
            update(MemberImportRowModel)
            .where(
                MemberImportRowModel.tenant_id == tenant_id.value,
                scope,
                or_(
                    MemberImportRowModel.imported_member_id.is_(None),
                    MemberImportRowModel.replay_key.like(f"{FILE_PREFIX}%"),
                ),
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

    async def find_rows_by_replay_keys(
        self, tenant_id: TenantId, replay_keys: list[str]
    ) -> dict[str, MemberImportRowEntity]:
        if not replay_keys:
            return {}
        models = await self.session.scalars(
            select(MemberImportRowModel).where(
                MemberImportRowModel.tenant_id == tenant_id.value,
                MemberImportRowModel.replay_key.in_(replay_keys),
            )
        )
        return {model.replay_key: MemberImportMapper.row_to_entity(model) for model in models}

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

    def _pending_rows_filter(self, tenant_id: TenantId, batch_id: MemberImportBatchId):
        return (
            MemberImportRowModel.tenant_id == tenant_id.value,
            MemberImportRowModel.batch_id == batch_id.value,
            MemberImportRowModel.imported_member_id.is_(None),
            or_(
                sa_and(
                    MemberImportRowModel.outcome == "New",
                    MemberImportRowModel.decision == "import",
                ),
                sa_and(
                    MemberImportRowModel.outcome == "Duplicate",
                    MemberImportRowModel.decision == "update",
                    MemberImportRowModel.matched_member_id.is_not(None),
                ),
            ),
        )

    async def list_pending_rows(
        self, tenant_id: TenantId, batch_id: MemberImportBatchId, *, limit: int
    ) -> Sequence[MemberImportRowEntity]:
        models = await self.session.scalars(
            select(MemberImportRowModel)
            .where(*self._pending_rows_filter(tenant_id, batch_id))
            .order_by(MemberImportRowModel.row_number)
            .limit(limit)
        )
        return [MemberImportMapper.row_to_entity(model) for model in models]

    async def count_pending_rows(self, tenant_id: TenantId, batch_id: MemberImportBatchId) -> int:
        return int(
            await self.session.scalar(
                select(func.count())
                .select_from(MemberImportRowModel)
                .where(*self._pending_rows_filter(tenant_id, batch_id))
            )
            or 0
        )

    async def count_imported_rows(self, tenant_id: TenantId, batch_id: MemberImportBatchId) -> int:
        return int(
            await self.session.scalar(
                select(func.count())
                .select_from(MemberImportRowModel)
                .where(
                    MemberImportRowModel.tenant_id == tenant_id.value,
                    MemberImportRowModel.batch_id == batch_id.value,
                    MemberImportRowModel.imported_member_id.is_not(None),
                )
            )
            or 0
        )
