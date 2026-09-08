"""SQLAlchemy implementation of the survey source repository."""

from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.survey_source import SurveySource
from app.domain.repositories.survey_source_repository import SurveySourceRepository
from app.infrastructure.models.survey_source_model import SurveySourceModel
from app.shared.utils.generators import generate_cuid


def _apply(model, **fields) -> bool:
    changed = False
    for key, value in fields.items():
        if value is not None and getattr(model, key) != value:
            setattr(model, key, value)
            changed = True
    return changed


def _to_entity(model: SurveySourceModel) -> SurveySource:
    return SurveySource(
        id=model.id,
        code=model.code,
        name=model.name,
        description=model.description,
        sort_order=model.sort_order,
        is_active=model.is_active,
        version=model.version,
        effective_until=model.effective_until,
    )


class SurveySourceRepositoryImpl(SurveySourceRepository):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def list_all(self, *, active_only: bool = True) -> list[SurveySource]:
        stmt = select(SurveySourceModel).order_by(
            SurveySourceModel.sort_order, SurveySourceModel.name
        )
        if active_only:
            stmt = stmt.where(
                SurveySourceModel.is_active.is_(True),
                SurveySourceModel.effective_until.is_(None),
            )
        result = await self._session.execute(stmt)
        return [_to_entity(row) for row in result.scalars()]

    async def get_by_code(self, code: str) -> SurveySource | None:
        stmt = select(SurveySourceModel).where(SurveySourceModel.code == code)
        row = (await self._session.execute(stmt)).scalar_one_or_none()
        return _to_entity(row) if row else None

    async def get_by_id(self, source_id: str) -> SurveySource | None:
        model = await self._session.get(SurveySourceModel, source_id)
        return _to_entity(model) if model else None

    async def create(
        self, *, code: str, name: str, description: str | None, sort_order: int
    ) -> SurveySource:
        model = SurveySourceModel(
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
        source_id: str,
        *,
        name: str | None = None,
        description: str | None = None,
        sort_order: int | None = None,
    ) -> SurveySource | None:
        model = await self._session.get(SurveySourceModel, source_id)
        if model is None:
            return None
        if _apply(model, name=name, description=description, sort_order=sort_order):
            model.version += 1
        await self._session.flush()
        return _to_entity(model)

    async def set_active(self, source_id: str, *, is_active: bool) -> SurveySource | None:
        model = await self._session.get(SurveySourceModel, source_id)
        if model is None:
            return None
        model.is_active = is_active
        model.effective_until = None if is_active else datetime.now(UTC)
        await self._session.flush()
        return _to_entity(model)
