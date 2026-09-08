"""SQLAlchemy implementation of the client tier repository."""

from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.client_tier import ClientTier
from app.domain.repositories.client_tier_repository import ClientTierRepository
from app.infrastructure.models.client_tier_model import ClientTierModel
from app.shared.utils.generators import generate_cuid


def _apply(model, **fields) -> bool:
    changed = False
    for key, value in fields.items():
        if value is not None and getattr(model, key) != value:
            setattr(model, key, value)
            changed = True
    return changed


def _to_entity(model: ClientTierModel) -> ClientTier:
    return ClientTier(
        id=model.id,
        code=model.code,
        name=model.name,
        description=model.description,
        sort_order=model.sort_order,
        is_active=model.is_active,
        version=model.version,
        effective_until=model.effective_until,
    )


class ClientTierRepositoryImpl(ClientTierRepository):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def list_all(self, *, active_only: bool = True) -> list[ClientTier]:
        stmt = select(ClientTierModel).order_by(ClientTierModel.sort_order, ClientTierModel.name)
        if active_only:
            stmt = stmt.where(
                ClientTierModel.is_active.is_(True),
                ClientTierModel.effective_until.is_(None),
            )
        result = await self._session.execute(stmt)
        return [_to_entity(row) for row in result.scalars()]

    async def get_by_code(self, code: str) -> ClientTier | None:
        stmt = select(ClientTierModel).where(ClientTierModel.code == code)
        row = (await self._session.execute(stmt)).scalar_one_or_none()
        return _to_entity(row) if row else None

    async def get_by_id(self, tier_id: str) -> ClientTier | None:
        model = await self._session.get(ClientTierModel, tier_id)
        return _to_entity(model) if model else None

    async def create(
        self, *, code: str, name: str, description: str | None, sort_order: int
    ) -> ClientTier:
        model = ClientTierModel(
            id=generate_cuid(),
            code=code,
            name=name,
            description=description,
            sort_order=sort_order,
        )
        self._session.add(model)
        await self._session.flush()
        return _to_entity(model)

    async def update(
        self,
        tier_id: str,
        *,
        name: str | None = None,
        description: str | None = None,
        sort_order: int | None = None,
    ) -> ClientTier | None:
        model = await self._session.get(ClientTierModel, tier_id)
        if model is None:
            return None
        if _apply(model, name=name, description=description, sort_order=sort_order):
            model.version += 1
        await self._session.flush()
        return _to_entity(model)

    async def set_active(self, tier_id: str, *, is_active: bool) -> ClientTier | None:
        model = await self._session.get(ClientTierModel, tier_id)
        if model is None:
            return None
        model.is_active = is_active
        model.effective_until = None if is_active else datetime.now(UTC)
        await self._session.flush()
        return _to_entity(model)
