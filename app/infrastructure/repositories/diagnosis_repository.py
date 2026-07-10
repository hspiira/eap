"""SQLAlchemy implementation of the diagnosis repository (Phase 2 #D-Tax)."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.diagnosis import Diagnosis, DiagnosisType
from app.domain.repositories.diagnosis_repository import DiagnosisRepository
from app.infrastructure.models.diagnosis_model import (
    DiagnosisModel,
    DiagnosisTypeModel,
)


def _to_type(model: DiagnosisTypeModel) -> DiagnosisType:
    return DiagnosisType(
        id=model.id,
        code=model.code,
        name=model.name,
        description=model.description,
        sort_order=model.sort_order,
        is_active=model.is_active,
        version=model.version,
        effective_until=model.effective_until,
    )


def _to_diagnosis(model: DiagnosisModel) -> Diagnosis:
    return Diagnosis(
        id=model.id,
        type_id=model.type_id,
        code=model.code,
        name=model.name,
        description=model.description,
        sort_order=model.sort_order,
        is_active=model.is_active,
        version=model.version,
        effective_until=model.effective_until,
    )


class DiagnosisRepositoryImpl(DiagnosisRepository):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def list_types(self, *, active_only: bool = True) -> list[DiagnosisType]:
        stmt = select(DiagnosisTypeModel).order_by(DiagnosisTypeModel.sort_order, DiagnosisTypeModel.name)
        if active_only:
            stmt = stmt.where(
                DiagnosisTypeModel.is_active.is_(True),
                DiagnosisTypeModel.effective_until.is_(None),
            )
        result = await self._session.execute(stmt)
        return [_to_type(row) for row in result.scalars()]

    async def get_type_by_code(self, code: str) -> DiagnosisType | None:
        stmt = select(DiagnosisTypeModel).where(DiagnosisTypeModel.code == code)
        row = (await self._session.execute(stmt)).scalar_one_or_none()
        return _to_type(row) if row else None

    async def list_diagnoses(
        self,
        *,
        type_code: str | None = None,
        active_only: bool = True,
    ) -> list[Diagnosis]:
        stmt = select(DiagnosisModel).order_by(DiagnosisModel.sort_order, DiagnosisModel.name)
        if active_only:
            stmt = stmt.where(
                DiagnosisModel.is_active.is_(True),
                DiagnosisModel.effective_until.is_(None),
            )
        if type_code is not None:
            type_row = await self.get_type_by_code(type_code)
            if type_row is None:
                return []
            stmt = stmt.where(DiagnosisModel.type_id == type_row.id)
        result = await self._session.execute(stmt)
        return [_to_diagnosis(row) for row in result.scalars()]

    async def get_diagnosis_by_code(self, code: str) -> Diagnosis | None:
        stmt = select(DiagnosisModel).where(DiagnosisModel.code == code)
        row = (await self._session.execute(stmt)).scalar_one_or_none()
        return _to_diagnosis(row) if row else None
