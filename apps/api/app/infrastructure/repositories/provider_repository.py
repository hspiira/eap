"""SQLAlchemy provider repository."""

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.repositories.provider_repository import ProviderRepository
from app.domain.value_objects.core import ProviderId, TenantId
from app.infrastructure.models.provider_model import ProviderModel
from app.infrastructure.models.user_model import UserModel
from app.shared.utils.generators import generate_cuid


class ProviderRepositoryImpl(ProviderRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, provider_id: ProviderId):
        result = await self.session.execute(
            select(ProviderModel, UserModel)
            .join(UserModel, UserModel.id == ProviderModel.user_id)
            .where(ProviderModel.id == provider_id.value, ProviderModel.deleted_at.is_(None))
        )
        return result.first()

    async def list_for_tenant(self, tenant_id: TenantId, *, limit: int = 100, offset: int = 0):
        result = await self.session.execute(
            select(ProviderModel, UserModel)
            .join(UserModel, UserModel.id == ProviderModel.user_id)
            .where(
                ProviderModel.tenant_id == tenant_id.value,
                ProviderModel.deleted_at.is_(None),
                UserModel.deleted_at.is_(None),
            )
            .order_by(ProviderModel.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(result.all())

    async def count(self, tenant_id: TenantId) -> int:
        result = await self.session.execute(
            select(func.count())
            .select_from(ProviderModel)
            .where(ProviderModel.tenant_id == tenant_id.value, ProviderModel.deleted_at.is_(None))
        )
        return int(result.scalar_one())

    async def save(self, provider: ProviderModel) -> None:
        self.session.add(provider)
        await self.session.flush()

    async def get_user_in_tenant(self, user_id: str, tenant_id: TenantId) -> UserModel | None:
        user = await self.session.get(UserModel, user_id)
        return user if user is not None and user.tenant_id == tenant_id.value else None

    async def create(
        self,
        *,
        tenant_id: TenantId,
        user_id: str,
        provider_profile: dict,
        license_info,
    ) -> ProviderModel:
        provider = ProviderModel(
            id=generate_cuid(),
            tenant_id=tenant_id.value,
            user_id=user_id,
            provider_profile=provider_profile,
            license_info=license_info,
        )
        await self.save(provider)
        return provider
