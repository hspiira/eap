"""SQLAlchemy repositories for the provider network."""

from collections.abc import Sequence
from datetime import date, datetime

from sqlalchemy import Select, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.provider_affiliation import ProviderAffiliationEntity
from app.domain.entities.provider_organisation import ProviderOrganisationEntity
from app.domain.repositories.provider_network_repository import (
    ProviderAffiliationRepository,
    ProviderOrganisationRepository,
)
from app.domain.services.provider_network_calendar import boundary_day
from app.domain.value_objects.core import ProviderId, TenantId
from app.domain.value_objects.provider_network import (
    ProviderAffiliationId,
    ProviderOrganisationId,
)
from app.infrastructure.mappers.provider_network_mapper import (
    ProviderAffiliationMapper,
    ProviderOrganisationMapper,
)
from app.infrastructure.models.provider_affiliation_model import ProviderAffiliationModel
from app.infrastructure.models.provider_organisation_model import ProviderOrganisationModel

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

    async def save_organisation(self, organisation: ProviderOrganisationEntity) -> None:
        await self.session.merge(ProviderOrganisationMapper.to_model(organisation))
        await self.session.flush()

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
