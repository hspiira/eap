"""SQLAlchemy repositories for the provider network."""

from collections.abc import Sequence
from datetime import date, datetime

from sqlalchemy import Select, func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.provider_affiliation import ProviderAffiliationEntity
from app.domain.entities.provider_alias import ProviderAliasEntity
from app.domain.entities.provider_organisation import ProviderOrganisationEntity
from app.domain.entities.provider_specialty import (
    ProviderSpecialtyEntity,
    ProviderSpecialtyLinkEntity,
)
from app.domain.entities.session_import import (
    SessionImportBatchEntity,
    SessionImportRowEntity,
)
from app.domain.enums.provider_network import ImportBatchStatus, ImportRowOutcome
from app.domain.repositories.provider_network_repository import (
    ProviderAffiliationRepository,
    ProviderAliasRepository,
    ProviderOrganisationRepository,
    ProviderSpecialtyRepository,
    SessionImportRepository,
)
from app.domain.services.provider_network_calendar import boundary_day
from app.domain.value_objects.core import ProviderId, TenantId
from app.domain.value_objects.provider_network import (
    ProviderAffiliationId,
    ProviderAliasId,
    ProviderOrganisationId,
    ProviderSpecialtyId,
    SessionImportBatchId,
)
from app.infrastructure.mappers.provider_network_mapper import (
    ProviderAffiliationMapper,
    ProviderAliasMapper,
    ProviderOrganisationMapper,
    ProviderSpecialtyMapper,
    SessionImportMapper,
)
from app.infrastructure.models.provider_affiliation_model import ProviderAffiliationModel
from app.infrastructure.models.provider_alias_model import ProviderAliasModel
from app.infrastructure.models.provider_organisation_model import ProviderOrganisationModel
from app.infrastructure.models.provider_specialty_model import (
    ProviderSpecialtyLinkModel,
    ProviderSpecialtyModel,
)
from app.infrastructure.models.session_import_model import (
    SessionImportBatchModel,
    SessionImportRowModel,
)
from app.shared.utils.replay_key import RELEASED_PREFIX

_ORGANISATION_SORTS = {
    "name": ProviderOrganisationModel.name,
    "created_at": ProviderOrganisationModel.created_at,
    "updated_at": ProviderOrganisationModel.updated_at,
}


async def _count(session: AsyncSession, statement: Select) -> int:
    subquery = statement.order_by(None).subquery()
    return int(await session.scalar(select(func.count()).select_from(subquery)) or 0)


class ProviderOrganisationRepositoryImpl(ProviderOrganisationRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_organisation(
        self, tenant_id: TenantId, organisation_id: ProviderOrganisationId
    ) -> ProviderOrganisationEntity | None:
        model = await self.session.scalar(
            select(ProviderOrganisationModel).where(
                ProviderOrganisationModel.id == organisation_id.value,
                ProviderOrganisationModel.tenant_id == tenant_id.value,
                ProviderOrganisationModel.deleted_at.is_(None),
            )
        )
        return ProviderOrganisationMapper.to_entity(model) if model else None

    async def list_organisations(
        self,
        tenant_id: TenantId,
        *,
        search: str | None = None,
        is_active: bool | None = None,
        approval_status: str | None = None,
        sort_by: str = "name",
        sort_desc: bool = False,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[Sequence[ProviderOrganisationEntity], int]:
        statement = select(ProviderOrganisationModel).where(
            ProviderOrganisationModel.tenant_id == tenant_id.value,
            ProviderOrganisationModel.deleted_at.is_(None),
        )
        if search:
            pattern = f"%{search.strip()}%"
            statement = statement.where(
                or_(
                    ProviderOrganisationModel.name.ilike(pattern),
                    ProviderOrganisationModel.registration_number.ilike(pattern),
                )
            )
        if is_active is not None:
            statement = statement.where(ProviderOrganisationModel.is_active.is_(is_active))
        if approval_status:
            statement = statement.where(
                ProviderOrganisationModel.approval_status == approval_status
            )
        total = await _count(self.session, statement)
        column = _ORGANISATION_SORTS.get(sort_by, ProviderOrganisationModel.name)
        statement = statement.order_by(
            column.desc() if sort_desc else column.asc(), ProviderOrganisationModel.id
        )
        rows = await self.session.scalars(statement.limit(limit).offset(offset))
        return [ProviderOrganisationMapper.to_entity(m) for m in rows], total

    async def get_organisations_by_ids(
        self, tenant_id: TenantId, organisation_ids: Sequence[ProviderOrganisationId]
    ) -> dict[str, ProviderOrganisationEntity]:
        values = [o.value for o in organisation_ids]
        if not values:
            return {}
        rows = await self.session.scalars(
            select(ProviderOrganisationModel).where(
                ProviderOrganisationModel.tenant_id == tenant_id.value,
                ProviderOrganisationModel.id.in_(values),
            )
        )
        return {m.id: ProviderOrganisationMapper.to_entity(m) for m in rows}

    async def save_organisation(self, organisation: ProviderOrganisationEntity) -> None:
        await self.session.merge(ProviderOrganisationMapper.to_model(organisation))
        await self.session.flush()

    async def find_organisation_by_name(
        self, tenant_id: TenantId, name: str
    ) -> ProviderOrganisationEntity | None:
        model = await self.session.scalar(
            select(ProviderOrganisationModel)
            .where(
                ProviderOrganisationModel.tenant_id == tenant_id.value,
                func.lower(ProviderOrganisationModel.name) == name.strip().lower(),
                ProviderOrganisationModel.deleted_at.is_(None),
            )
            .limit(1)
        )
        return ProviderOrganisationMapper.to_entity(model) if model else None

    async def name_exists(
        self,
        tenant_id: TenantId,
        name: str,
        *,
        exclude_id: ProviderOrganisationId | None = None,
    ) -> bool:
        statement = select(ProviderOrganisationModel.id).where(
            ProviderOrganisationModel.tenant_id == tenant_id.value,
            func.lower(ProviderOrganisationModel.name) == name.strip().lower(),
            ProviderOrganisationModel.deleted_at.is_(None),
        )
        if exclude_id is not None:
            statement = statement.where(ProviderOrganisationModel.id != exclude_id.value)
        return await self.session.scalar(statement.limit(1)) is not None


class ProviderAffiliationRepositoryImpl(ProviderAffiliationRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_valid_affiliation(
        self,
        tenant_id: TenantId,
        affiliation_id: ProviderAffiliationId,
        *,
        provider_id: ProviderId,
        at: datetime,
    ) -> ProviderAffiliationEntity | None:
        day = boundary_day(at)
        model = await self.session.scalar(
            select(ProviderAffiliationModel).where(
                ProviderAffiliationModel.id == affiliation_id.value,
                ProviderAffiliationModel.tenant_id == tenant_id.value,
                ProviderAffiliationModel.provider_id == provider_id.value,
                ProviderAffiliationModel.valid_from <= day,
                or_(
                    ProviderAffiliationModel.valid_until.is_(None),
                    ProviderAffiliationModel.valid_until > day,
                ),
            )
        )
        return ProviderAffiliationMapper.to_entity(model) if model else None

    async def get_affiliation(
        self, tenant_id: TenantId, affiliation_id: ProviderAffiliationId
    ) -> ProviderAffiliationEntity | None:
        model = await self.session.scalar(
            select(ProviderAffiliationModel).where(
                ProviderAffiliationModel.id == affiliation_id.value,
                ProviderAffiliationModel.tenant_id == tenant_id.value,
            )
        )
        return ProviderAffiliationMapper.to_entity(model) if model else None

    async def find_overlapping(
        self,
        tenant_id: TenantId,
        provider_id: ProviderId,
        organisation_id: ProviderOrganisationId,
        *,
        valid_from: date,
        valid_until: date | None,
        exclude_id: ProviderAffiliationId | None = None,
    ) -> Sequence[ProviderAffiliationEntity]:
        statement = select(ProviderAffiliationModel).where(
            ProviderAffiliationModel.tenant_id == tenant_id.value,
            ProviderAffiliationModel.provider_id == provider_id.value,
            ProviderAffiliationModel.organisation_id == organisation_id.value,
            or_(
                ProviderAffiliationModel.valid_until.is_(None),
                ProviderAffiliationModel.valid_until > valid_from,
            ),
        )
        if valid_until is not None:
            statement = statement.where(ProviderAffiliationModel.valid_from < valid_until)
        if exclude_id is not None:
            statement = statement.where(ProviderAffiliationModel.id != exclude_id.value)
        rows = await self.session.scalars(statement.order_by(ProviderAffiliationModel.valid_from))
        return [ProviderAffiliationMapper.to_entity(m) for m in rows]

    async def list_affiliations(
        self,
        tenant_id: TenantId,
        *,
        provider_id: ProviderId | None = None,
        organisation_id: ProviderOrganisationId | None = None,
        valid_at: date | None = None,
        include_ended: bool = False,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[Sequence[ProviderAffiliationEntity], int]:
        statement = select(ProviderAffiliationModel).where(
            ProviderAffiliationModel.tenant_id == tenant_id.value
        )
        if provider_id is not None:
            statement = statement.where(ProviderAffiliationModel.provider_id == provider_id.value)
        if organisation_id is not None:
            statement = statement.where(
                ProviderAffiliationModel.organisation_id == organisation_id.value
            )
        if valid_at is not None:
            statement = statement.where(
                ProviderAffiliationModel.valid_from <= valid_at,
                or_(
                    ProviderAffiliationModel.valid_until.is_(None),
                    ProviderAffiliationModel.valid_until > valid_at,
                ),
            )
        elif not include_ended:
            statement = statement.where(
                or_(
                    ProviderAffiliationModel.valid_until.is_(None),
                    ProviderAffiliationModel.valid_until > func.current_date(),
                )
            )
        total = await _count(self.session, statement)
        rows = await self.session.scalars(
            statement.order_by(
                ProviderAffiliationModel.valid_from.desc(), ProviderAffiliationModel.id
            )
            .limit(limit)
            .offset(offset)
        )
        return [ProviderAffiliationMapper.to_entity(m) for m in rows], total

    async def save_affiliation(self, affiliation: ProviderAffiliationEntity) -> None:
        await self.session.merge(ProviderAffiliationMapper.to_model(affiliation))
        await self.session.flush()


class ProviderSpecialtyRepositoryImpl(ProviderSpecialtyRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_specialty(
        self, specialty_id: ProviderSpecialtyId
    ) -> ProviderSpecialtyEntity | None:
        model = await self.session.scalar(
            select(ProviderSpecialtyModel).where(ProviderSpecialtyModel.id == specialty_id.value)
        )
        return ProviderSpecialtyMapper.to_entity(model) if model else None

    async def list_specialties(
        self, *, include_inactive: bool = False
    ) -> Sequence[ProviderSpecialtyEntity]:
        statement = select(ProviderSpecialtyModel)
        if not include_inactive:
            statement = statement.where(ProviderSpecialtyModel.is_active.is_(True))
        rows = await self.session.scalars(statement.order_by(ProviderSpecialtyModel.label))
        return [ProviderSpecialtyMapper.to_entity(m) for m in rows]

    async def save_specialty(self, specialty: ProviderSpecialtyEntity) -> None:
        await self.session.merge(ProviderSpecialtyMapper.to_model(specialty))
        await self.session.flush()

    async def list_links_for_provider(
        self, tenant_id: TenantId, provider_id: ProviderId
    ) -> Sequence[ProviderSpecialtyLinkEntity]:
        rows = await self.session.scalars(
            select(ProviderSpecialtyLinkModel).where(
                ProviderSpecialtyLinkModel.tenant_id == tenant_id.value,
                ProviderSpecialtyLinkModel.provider_id == provider_id.value,
            )
        )
        return [ProviderSpecialtyMapper.link_to_entity(m) for m in rows]

    async def add_link(self, link: ProviderSpecialtyLinkEntity) -> None:
        self.session.add(ProviderSpecialtyMapper.link_to_model(link))
        await self.session.flush()

    async def remove_link(self, tenant_id: TenantId, link_id: str) -> bool:
        model = await self.session.scalar(
            select(ProviderSpecialtyLinkModel).where(
                ProviderSpecialtyLinkModel.id == link_id,
                ProviderSpecialtyLinkModel.tenant_id == tenant_id.value,
            )
        )
        if model is None:
            return False
        await self.session.delete(model)
        await self.session.flush()
        return True


class ProviderAliasRepositoryImpl(ProviderAliasRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def find_alias(
        self, tenant_id: TenantId, source_system: str, normalized_value: str
    ) -> ProviderAliasEntity | None:
        model = await self.session.scalar(
            select(ProviderAliasModel).where(
                ProviderAliasModel.tenant_id == tenant_id.value,
                ProviderAliasModel.source_system == source_system,
                ProviderAliasModel.normalized_value == normalized_value,
            )
        )
        return ProviderAliasMapper.to_entity(model) if model else None

    async def get_alias(
        self, tenant_id: TenantId, alias_id: ProviderAliasId
    ) -> ProviderAliasEntity | None:
        model = await self.session.scalar(
            select(ProviderAliasModel).where(
                ProviderAliasModel.id == alias_id.value,
                ProviderAliasModel.tenant_id == tenant_id.value,
            )
        )
        return ProviderAliasMapper.to_entity(model) if model else None

    async def list_aliases(
        self,
        tenant_id: TenantId,
        *,
        source_system: str | None = None,
        state: str | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[Sequence[ProviderAliasEntity], int]:
        statement = select(ProviderAliasModel).where(
            ProviderAliasModel.tenant_id == tenant_id.value
        )
        if source_system:
            statement = statement.where(ProviderAliasModel.source_system == source_system)
        if state:
            statement = statement.where(ProviderAliasModel.state == state)
        total = await _count(self.session, statement)
        rows = await self.session.scalars(
            statement.order_by(ProviderAliasModel.normalized_value).limit(limit).offset(offset)
        )
        return [ProviderAliasMapper.to_entity(m) for m in rows], total

    async def save_alias(self, alias: ProviderAliasEntity) -> None:
        await self.session.merge(ProviderAliasMapper.to_model(alias))
        await self.session.flush()


class SessionImportRepositoryImpl(SessionImportRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_batch(
        self, tenant_id: TenantId, batch_id: SessionImportBatchId
    ) -> SessionImportBatchEntity | None:
        model = await self.session.scalar(
            select(SessionImportBatchModel).where(
                SessionImportBatchModel.id == batch_id.value,
                SessionImportBatchModel.tenant_id == tenant_id.value,
            )
        )
        return SessionImportMapper.batch_to_entity(model) if model else None

    async def find_batch_by_hash(
        self, tenant_id: TenantId, file_hash: str
    ) -> SessionImportBatchEntity | None:
        """The Staged batch holding this hash, if any.

        A hash can belong to several historical batches once a file has been
        staged, applied or abandoned, and staged again to re-judge against
        improved reference data: this tenant's session_import_batches can
        (and in practice does) hold more than one row for the same hash.
        Filtering by status here, rather than fetching an arbitrary match and
        checking it in Python, is required: an unfiltered query has no
        ORDER BY and `scalar()` returns whichever row the database happens to
        put first, which can silently be the wrong one and let a genuine
        conflict through to the unique-index violation this check exists to
        turn into a clean 409 instead.
        """
        model = await self.session.scalar(
            select(SessionImportBatchModel).where(
                SessionImportBatchModel.tenant_id == tenant_id.value,
                SessionImportBatchModel.file_hash == file_hash,
                SessionImportBatchModel.status == ImportBatchStatus.STAGED.value,
            )
        )
        return SessionImportMapper.batch_to_entity(model) if model else None

    async def save_batch(self, batch: SessionImportBatchEntity) -> None:
        await self.session.merge(SessionImportMapper.batch_to_model(batch))
        await self.session.flush()

    async def release_replay_keys(self, tenant_id: TenantId, batch_id: SessionImportBatchId) -> int:
        return await self._release(tenant_id, SessionImportRowModel.batch_id == batch_id.value)

    async def release_superseded_rows(self, tenant_id: TenantId, file_hash: str) -> int:
        return await self._release(
            tenant_id,
            SessionImportRowModel.batch_id.in_(
                select(SessionImportBatchModel.id).where(
                    SessionImportBatchModel.tenant_id == tenant_id.value,
                    SessionImportBatchModel.file_hash == file_hash,
                )
            ),
        )

    async def _release(self, tenant_id: TenantId, scope) -> int:
        """Give up the keys of rows in `scope` that never produced a session."""
        result = await self.session.execute(
            update(SessionImportRowModel)
            .where(
                SessionImportRowModel.tenant_id == tenant_id.value,
                scope,
                SessionImportRowModel.imported_session_id.is_(None),
                SessionImportRowModel.replay_key.not_like(f"{RELEASED_PREFIX}%"),
            )
            .values(
                replay_key=RELEASED_PREFIX
                + SessionImportRowModel.batch_id
                + ":"
                + SessionImportRowModel.replay_key
            )
        )
        await self.session.flush()
        return result.rowcount or 0

    async def add_rows(self, rows: Sequence[SessionImportRowEntity], *, file_hash: str) -> None:
        for row in rows:
            self.session.add(SessionImportMapper.row_to_model(row, file_hash=file_hash))
        await self.session.flush()

    async def list_rows(
        self,
        tenant_id: TenantId,
        batch_id: SessionImportBatchId,
        *,
        outcome: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[Sequence[SessionImportRowEntity], int]:
        statement = select(SessionImportRowModel).where(
            SessionImportRowModel.tenant_id == tenant_id.value,
            SessionImportRowModel.batch_id == batch_id.value,
        )
        if outcome:
            statement = statement.where(SessionImportRowModel.outcome == outcome)
        total = await _count(self.session, statement)
        rows = await self.session.scalars(
            statement.order_by(SessionImportRowModel.row_number).limit(limit).offset(offset)
        )
        return [SessionImportMapper.row_to_entity(m) for m in rows], total

    async def mark_row_imported(self, tenant_id: TenantId, row_id: str, session_id: str) -> None:
        await self.session.execute(
            update(SessionImportRowModel)
            .where(
                SessionImportRowModel.id == row_id,
                SessionImportRowModel.tenant_id == tenant_id.value,
                SessionImportRowModel.imported_session_id.is_(None),
            )
            .values(imported_session_id=session_id)
        )
        await self.session.flush()

    async def find_row_by_replay_key(
        self, tenant_id: TenantId, replay_key: str
    ) -> SessionImportRowEntity | None:
        model = await self.session.scalar(
            select(SessionImportRowModel).where(
                SessionImportRowModel.tenant_id == tenant_id.value,
                SessionImportRowModel.replay_key == replay_key,
            )
        )
        return SessionImportMapper.row_to_entity(model) if model else None

    async def outcome_counts(
        self, tenant_id: TenantId, batch_id: SessionImportBatchId
    ) -> dict[str, int]:
        rows = await self.session.execute(
            select(SessionImportRowModel.outcome, func.count())
            .where(
                SessionImportRowModel.tenant_id == tenant_id.value,
                SessionImportRowModel.batch_id == batch_id.value,
            )
            .group_by(SessionImportRowModel.outcome)
        )
        return {str(outcome): int(count) for outcome, count in rows}

    async def mark_row_failed(self, tenant_id: TenantId, row_id: str, reason: str) -> None:
        await self.session.execute(
            update(SessionImportRowModel)
            .where(
                SessionImportRowModel.id == row_id,
                SessionImportRowModel.tenant_id == tenant_id.value,
                SessionImportRowModel.imported_session_id.is_(None),
            )
            .values(outcome=ImportRowOutcome.FAILED.value, reasons=[reason])
        )
        await self.session.flush()

    def _pending_rows_filter(self, tenant_id: TenantId, batch_id: SessionImportBatchId):
        return (
            SessionImportRowModel.tenant_id == tenant_id.value,
            SessionImportRowModel.batch_id == batch_id.value,
            SessionImportRowModel.outcome == ImportRowOutcome.ACCEPTED.value,
            SessionImportRowModel.imported_session_id.is_(None),
        )

    async def list_pending_rows(
        self, tenant_id: TenantId, batch_id: SessionImportBatchId, *, limit: int
    ) -> Sequence[SessionImportRowEntity]:
        models = await self.session.scalars(
            select(SessionImportRowModel)
            .where(*self._pending_rows_filter(tenant_id, batch_id))
            .order_by(SessionImportRowModel.row_number)
            .limit(limit)
        )
        return [SessionImportMapper.row_to_entity(model) for model in models]

    async def count_pending_rows(self, tenant_id: TenantId, batch_id: SessionImportBatchId) -> int:
        return int(
            await self.session.scalar(
                select(func.count())
                .select_from(SessionImportRowModel)
                .where(*self._pending_rows_filter(tenant_id, batch_id))
            )
            or 0
        )

    async def count_imported_rows(self, tenant_id: TenantId, batch_id: SessionImportBatchId) -> int:
        return int(
            await self.session.scalar(
                select(func.count())
                .select_from(SessionImportRowModel)
                .where(
                    SessionImportRowModel.tenant_id == tenant_id.value,
                    SessionImportRowModel.batch_id == batch_id.value,
                    SessionImportRowModel.imported_session_id.is_not(None),
                )
            )
            or 0
        )

    async def find_imported_row_matching(
        self,
        tenant_id: TenantId,
        *,
        session_date: date,
        provider_id: ProviderId,
        client_id: str,
        service_id: str,
        member_id: str | None,
    ) -> SessionImportRowEntity | None:
        member_condition = (
            SessionImportRowModel.member_id == member_id
            if member_id is not None
            else SessionImportRowModel.member_id.is_(None)
        )
        model = await self.session.scalar(
            select(SessionImportRowModel)
            .where(
                SessionImportRowModel.tenant_id == tenant_id.value,
                SessionImportRowModel.imported_session_id.is_not(None),
                SessionImportRowModel.session_date == session_date,
                SessionImportRowModel.provider_id == provider_id.value,
                SessionImportRowModel.client_id == client_id,
                SessionImportRowModel.service_id == service_id,
                member_condition,
            )
            .limit(1)
        )
        return SessionImportMapper.row_to_entity(model) if model else None
