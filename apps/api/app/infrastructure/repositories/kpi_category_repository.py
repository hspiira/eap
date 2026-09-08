"""SQLAlchemy implementation of the KPI category repository."""

from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.kpi_category import KPICategory
from app.domain.repositories.kpi_category_repository import KPICategoryRepository
from app.infrastructure.models.kpi_category_model import KPICategoryModel
from app.shared.utils.generators import generate_cuid


def _apply(model, **fields) -> bool:
    changed = False
    for key, value in fields.items():
        if value is not None and getattr(model, key) != value:
            setattr(model, key, value)
            changed = True
    return changed


def _to_entity(model: KPICategoryModel) -> KPICategory:
    return KPICategory(
        id=model.id,
        code=model.code,
        name=model.name,
        description=model.description,
        sort_order=model.sort_order,
        is_active=model.is_active,
        version=model.version,
        effective_until=model.effective_until,
    )


class KPICategoryRepositoryImpl(KPICategoryRepository):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def list_all(self, *, active_only: bool = True) -> list[KPICategory]:
        stmt = select(KPICategoryModel).order_by(KPICategoryModel.sort_order, KPICategoryModel.name)
        if active_only:
            stmt = stmt.where(
                KPICategoryModel.is_active.is_(True),
                KPICategoryModel.effective_until.is_(None),
            )
        result = await self._session.execute(stmt)
        return [_to_entity(row) for row in result.scalars()]

    async def get_by_code(self, code: str) -> KPICategory | None:
        stmt = select(KPICategoryModel).where(KPICategoryModel.code == code)
        row = (await self._session.execute(stmt)).scalar_one_or_none()
        return _to_entity(row) if row else None

    async def get_by_id(self, category_id: str) -> KPICategory | None:
        model = await self._session.get(KPICategoryModel, category_id)
        return _to_entity(model) if model else None

    async def create(
        self, *, code: str, name: str, description: str | None, sort_order: int
    ) -> KPICategory:
        model = KPICategoryModel(
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
        category_id: str,
        *,
        name: str | None = None,
        description: str | None = None,
        sort_order: int | None = None,
    ) -> KPICategory | None:
        model = await self._session.get(KPICategoryModel, category_id)
        if model is None:
            return None
        if _apply(model, name=name, description=description, sort_order=sort_order):
            model.version += 1
        await self._session.flush()
        return _to_entity(model)

    async def set_active(self, category_id: str, *, is_active: bool) -> KPICategory | None:
        model = await self._session.get(KPICategoryModel, category_id)
        if model is None:
            return None
        model.is_active = is_active
        model.effective_until = None if is_active else datetime.now(UTC)
        await self._session.flush()
        return _to_entity(model)
