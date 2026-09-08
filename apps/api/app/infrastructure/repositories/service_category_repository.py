"""SQLAlchemy implementation of the service category repository."""

from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.service_category import ServiceCategory
from app.domain.repositories.service_category_repository import (
    ServiceCategoryRepository,
)
from app.infrastructure.models.service_category_model import ServiceCategoryModel
from app.shared.utils.generators import generate_cuid


def _apply(model, **fields) -> bool:
    """Set the fields that were supplied, and report whether any value changed."""
    changed = False
    for key, value in fields.items():
        if value is not None and getattr(model, key) != value:
            setattr(model, key, value)
            changed = True
    return changed


def _to_entity(model: ServiceCategoryModel) -> ServiceCategory:
    return ServiceCategory(
        id=model.id,
        code=model.code,
        name=model.name,
        description=model.description,
        sort_order=model.sort_order,
        is_active=model.is_active,
        version=model.version,
        effective_until=model.effective_until,
    )


class ServiceCategoryRepositoryImpl(ServiceCategoryRepository):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def list_all(self, *, active_only: bool = True) -> list[ServiceCategory]:
        stmt = select(ServiceCategoryModel).order_by(
            ServiceCategoryModel.sort_order, ServiceCategoryModel.name
        )
        if active_only:
            stmt = stmt.where(
                ServiceCategoryModel.is_active.is_(True),
                ServiceCategoryModel.effective_until.is_(None),
            )
        result = await self._session.execute(stmt)
        return [_to_entity(row) for row in result.scalars()]

    async def get_by_code(self, code: str) -> ServiceCategory | None:
        stmt = select(ServiceCategoryModel).where(ServiceCategoryModel.code == code)
        row = (await self._session.execute(stmt)).scalar_one_or_none()
        return _to_entity(row) if row else None

    async def get_by_id(self, category_id: str) -> ServiceCategory | None:
        model = await self._session.get(ServiceCategoryModel, category_id)
        return _to_entity(model) if model else None

    async def create(
        self, *, code: str, name: str, description: str | None, sort_order: int
    ) -> ServiceCategory:
        model = ServiceCategoryModel(
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
    ) -> ServiceCategory | None:
        model = await self._session.get(ServiceCategoryModel, category_id)
        if model is None:
            return None
        if _apply(model, name=name, description=description, sort_order=sort_order):
            model.version += 1
        await self._session.flush()
        return _to_entity(model)

    async def set_active(self, category_id: str, *, is_active: bool) -> ServiceCategory | None:
        model = await self._session.get(ServiceCategoryModel, category_id)
        if model is None:
            return None
        model.is_active = is_active
        model.effective_until = None if is_active else datetime.now(UTC)
        await self._session.flush()
        return _to_entity(model)
