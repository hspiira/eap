"""SQLAlchemy provider repository."""

from collections.abc import Sequence
from typing import Any

from sqlalchemy import ColumnElement, Select, func, or_, select

from app.domain.entities.provider import ProviderEntity
from app.domain.entities.user import UserEntity
from app.domain.repositories.provider_repository import (
    SORTABLE_FIELDS,
    ProviderListQuery,
    ProviderRepository,
)
from app.domain.value_objects.core import ProviderId, TenantId, UserId
from app.infrastructure.mappers.provider_mapper import ProviderMapper
from app.infrastructure.mappers.user_mapper import UserMapper
from app.infrastructure.models.provider_model import ProviderModel
from app.infrastructure.models.user_model import UserModel
from app.infrastructure.repositories.base import TenantScopedRepositoryImpl


def _profile_field(name: str) -> ColumnElement[str]:
    """Read one profile attribute as text.

    Tier, region and the two statuses still live in the provider_profile JSON
    column. Phase 4 promotes them to typed columns; this is the only place the
    filters reach into the JSON, so that promotion changes one function.
    """
    return ProviderModel.provider_profile[name].as_string()


class ProviderRepositoryImpl(
    TenantScopedRepositoryImpl[ProviderEntity, ProviderModel, ProviderId], ProviderRepository
):
    model_class = ProviderModel
    id_column = "id"

    def _to_entity(self, model: ProviderModel) -> ProviderEntity:
        return ProviderMapper.to_entity(model)

    def _to_model(self, entity: ProviderEntity) -> ProviderModel:
        return ProviderMapper.to_model(entity)

    def _get_id_value(self, entity_id: ProviderId) -> str:
        return entity_id.value

    async def list_for_tenant(
        self, tenant_id: TenantId, *, limit: int = 100, offset: int = 0
    ) -> Sequence[ProviderEntity]:
        result = await self.session.execute(
            select(ProviderModel)
            .where(ProviderModel.tenant_id == tenant_id.value, ProviderModel.deleted_at.is_(None))
            .order_by(ProviderModel.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return [self._to_entity(model) for model in result.scalars().all()]

    async def count(self, tenant_id: TenantId) -> int:
        result = await self.session.execute(
            select(func.count())
            .select_from(ProviderModel)
            .where(ProviderModel.tenant_id == tenant_id.value, ProviderModel.deleted_at.is_(None))
        )
        return int(result.scalar_one())

    async def search(
        self, tenant_id: TenantId, query: ProviderListQuery
    ) -> Sequence[ProviderEntity]:
        statement = self._apply_filters(select(ProviderModel), tenant_id, query)
        statement = statement.order_by(*_ordering(query)).limit(query.limit).offset(query.offset)
        result = await self.session.execute(statement)
        return [self._to_entity(model) for model in result.scalars().all()]

    async def count_matching(self, tenant_id: TenantId, query: ProviderListQuery) -> int:
        statement = self._apply_filters(
            select(func.count()).select_from(ProviderModel), tenant_id, query
        )
        result = await self.session.execute(statement)
        return int(result.scalar_one())

    def _apply_filters(
        self, statement: Select[Any], tenant_id: TenantId, query: ProviderListQuery
    ) -> Select[Any]:
        return statement.where(
            ProviderModel.tenant_id == tenant_id.value,
            ProviderModel.deleted_at.is_(None),
            *_conditions(query),
        )

    async def get_for_booking(
        self, tenant_id: TenantId, provider_id: ProviderId
    ) -> ProviderEntity | None:
        result = await self.session.execute(
            select(ProviderModel)
            .where(
                ProviderModel.id == provider_id.value,
                ProviderModel.tenant_id == tenant_id.value,
            )
            .with_for_update()
        )
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def get_by_user_id(self, tenant_id: TenantId, user_id: UserId) -> ProviderEntity | None:
        result = await self.session.execute(
            select(ProviderModel).where(
                ProviderModel.tenant_id == tenant_id.value,
                ProviderModel.user_id == user_id.value,
                ProviderModel.deleted_at.is_(None),
            )
        )
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def save(self, provider: ProviderEntity) -> None:
        await super().save(provider)
        await self.session.flush()

    async def get_user_in_tenant(self, user_id: UserId, tenant_id: TenantId) -> UserEntity | None:
        result = await self.session.execute(
            select(UserModel).where(
                UserModel.id == user_id.value,
                UserModel.tenant_id == tenant_id.value,
                UserModel.deleted_at.is_(None),
            )
        )
        user = result.scalar_one_or_none()
        return UserMapper.to_entity(user) if user else None

    async def get_users_in_tenant(
        self, user_ids: Sequence[UserId], tenant_id: TenantId
    ) -> dict[str, UserEntity]:
        if not user_ids:
            return {}
        result = await self.session.execute(
            select(UserModel).where(
                UserModel.id.in_([user_id.value for user_id in user_ids]),
                UserModel.tenant_id == tenant_id.value,
                UserModel.deleted_at.is_(None),
            )
        )
        users = (UserMapper.to_entity(user) for user in result.scalars())
        return {user.id.value: user for user in users}


def _conditions(query: ProviderListQuery) -> list[ColumnElement[bool]]:
    conditions: list[ColumnElement[bool]] = []
    if query.search:
        pattern = f"%{query.search.strip()}%"
        conditions.append(
            or_(
                ProviderModel.display_name.ilike(pattern),
                ProviderModel.contact_email.ilike(pattern),
            )
        )
    if query.statuses:
        conditions.append(ProviderModel.status.in_([s.value for s in query.statuses]))
    if query.has_account is True:
        conditions.append(ProviderModel.user_id.isnot(None))
    elif query.has_account is False:
        conditions.append(ProviderModel.user_id.is_(None))
    for name, values in (
        ("tier", query.tiers),
        ("region", query.regions),
        ("panel_status", query.panel_statuses),
        ("accreditation_status", query.accreditation_statuses),
    ):
        if values:
            conditions.append(_profile_field(name).in_([v.value for v in values]))
    return conditions


def _ordering(query: ProviderListQuery) -> list[Any]:
    column = getattr(
        ProviderModel, query.sort_by if query.sort_by in SORTABLE_FIELDS else "display_name"
    )
    primary = column.desc() if query.sort_desc else column.asc()
    return [primary, ProviderModel.id.asc()]
