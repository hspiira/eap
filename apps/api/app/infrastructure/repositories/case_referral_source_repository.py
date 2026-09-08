"""SQLAlchemy implementation of the case referral source repository."""

from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.case_referral_source import CaseReferralSource
from app.domain.repositories.case_referral_source_repository import (
    CaseReferralSourceRepository,
)
from app.infrastructure.models.case_referral_source_model import (
    CaseReferralSourceModel,
)
from app.shared.utils.generators import generate_cuid


def _apply(model, **fields) -> bool:
    changed = False
    for key, value in fields.items():
        if value is not None and getattr(model, key) != value:
            setattr(model, key, value)
            changed = True
    return changed


def _to_entity(model: CaseReferralSourceModel) -> CaseReferralSource:
    return CaseReferralSource(
        id=model.id,
        code=model.code,
        name=model.name,
        description=model.description,
        sort_order=model.sort_order,
        is_active=model.is_active,
        version=model.version,
        effective_until=model.effective_until,
    )


class CaseReferralSourceRepositoryImpl(CaseReferralSourceRepository):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def list_all(self, *, active_only: bool = True) -> list[CaseReferralSource]:
        stmt = select(CaseReferralSourceModel).order_by(
            CaseReferralSourceModel.sort_order, CaseReferralSourceModel.name
        )
        if active_only:
            stmt = stmt.where(
                CaseReferralSourceModel.is_active.is_(True),
                CaseReferralSourceModel.effective_until.is_(None),
            )
        result = await self._session.execute(stmt)
        return [_to_entity(row) for row in result.scalars()]

    async def get_by_code(self, code: str) -> CaseReferralSource | None:
        stmt = select(CaseReferralSourceModel).where(CaseReferralSourceModel.code == code)
        row = (await self._session.execute(stmt)).scalar_one_or_none()
        return _to_entity(row) if row else None

    async def get_by_id(self, source_id: str) -> CaseReferralSource | None:
        model = await self._session.get(CaseReferralSourceModel, source_id)
        return _to_entity(model) if model else None

    async def create(
        self, *, code: str, name: str, description: str | None, sort_order: int
    ) -> CaseReferralSource:
        model = CaseReferralSourceModel(
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
    ) -> CaseReferralSource | None:
        model = await self._session.get(CaseReferralSourceModel, source_id)
        if model is None:
            return None
        if _apply(model, name=name, description=description, sort_order=sort_order):
            model.version += 1
        await self._session.flush()
        return _to_entity(model)

    async def set_active(self, source_id: str, *, is_active: bool) -> CaseReferralSource | None:
        model = await self._session.get(CaseReferralSourceModel, source_id)
        if model is None:
            return None
        model.is_active = is_active
        model.effective_until = None if is_active else datetime.now(UTC)
        await self._session.flush()
        return _to_entity(model)
