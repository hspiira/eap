"""SQLAlchemy provider repository."""

from collections.abc import Sequence

from sqlalchemy import func, select

from app.domain.entities.provider import ProviderEntity
from app.domain.entities.user import UserEntity
from app.domain.repositories.provider_repository import ProviderRepository
from app.domain.value_objects.core import ProviderId, TenantId, UserId
from app.infrastructure.mappers.provider_mapper import ProviderMapper
from app.infrastructure.mappers.user_mapper import UserMapper
from app.infrastructure.models.provider_model import ProviderModel
from app.infrastructure.models.user_model import UserModel
from app.infrastructure.repositories.base import TenantScopedRepositoryImpl


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
