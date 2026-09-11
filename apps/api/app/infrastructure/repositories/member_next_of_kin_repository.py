"""SQL implementation of restricted member next-of-kin contacts."""

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.member_next_of_kin import MemberNextOfKin
from app.domain.repositories.member_next_of_kin_repository import MemberNextOfKinRepository
from app.domain.value_objects.core import EligibleMemberId, MemberNextOfKinId, TenantId
from app.infrastructure.mappers.member_next_of_kin_mapper import MemberNextOfKinMapper
from app.infrastructure.models.eligible_member_model import EligibleMemberModel
from app.infrastructure.models.member_next_of_kin_model import MemberNextOfKinModel


class MemberNextOfKinRepositoryImpl(MemberNextOfKinRepository):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_by_id(self, entity_id: MemberNextOfKinId) -> MemberNextOfKin | None:
        model = await self._session.get(MemberNextOfKinModel, entity_id.value)
        return MemberNextOfKinMapper.to_entity(model) if model else None

    async def save(self, entity: MemberNextOfKin) -> None:
        await self._session.execute(
            select(EligibleMemberModel.id)
            .where(
                EligibleMemberModel.id == entity.member_id.value,
                EligibleMemberModel.tenant_id == entity.tenant_id.value,
            )
            .with_for_update()
        )
        if entity.is_primary:
            await self._session.execute(
                update(MemberNextOfKinModel)
                .where(
                    MemberNextOfKinModel.tenant_id == entity.tenant_id.value,
                    MemberNextOfKinModel.member_id == entity.member_id.value,
                )
                .values(is_primary=False)
            )
        model = MemberNextOfKinMapper.to_model(entity)
        existing = await self._session.get(MemberNextOfKinModel, entity.id.value)
        if existing is None:
            self._session.add(model)
        else:
            existing.name = model.name
            existing.relationship = model.relationship
            existing.phone = model.phone
            existing.email = model.email
            existing.is_primary = model.is_primary
            existing.updated_at = model.updated_at
        await self._session.flush()

    async def delete(self, entity_id: MemberNextOfKinId) -> None:
        model = await self._session.get(MemberNextOfKinModel, entity_id.value)
        if model:
            await self._session.delete(model)
            await self._session.flush()

    async def exists(self, entity_id: MemberNextOfKinId) -> bool:
        return await self.get_by_id(entity_id) is not None

    async def list_for_member(
        self, tenant_id: TenantId, member_id: EligibleMemberId
    ) -> list[MemberNextOfKin]:
        # name is encrypted, so alphabetical order can only be applied after
        # decryption; is_primary stays a SQL-level sort since it is plaintext.
        result = await self._session.execute(
            select(MemberNextOfKinModel)
            .where(
                MemberNextOfKinModel.tenant_id == tenant_id.value,
                MemberNextOfKinModel.member_id == member_id.value,
            )
            .order_by(MemberNextOfKinModel.is_primary.desc())
        )
        entities = [MemberNextOfKinMapper.to_entity(model) for model in result.scalars().all()]
        entities.sort(key=lambda kin: kin.name.lower())
        entities.sort(key=lambda kin: kin.is_primary, reverse=True)
        return entities
