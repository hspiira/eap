"""SQLAlchemy implementation of the diagnosis repository (Phase 2 #D-Tax)."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.diagnosis import (
    Diagnosis,
    DiagnosisAlias,
    DiagnosisType,
    TenantOverlay,
)
from app.domain.repositories.diagnosis_repository import DiagnosisRepository
from app.domain.services.diagnosis_alias import normalise_diagnosis_value
from app.infrastructure.models.diagnosis_model import (
    DiagnosisAliasModel,
    DiagnosisModel,
    DiagnosisTypeModel,
    TenantDiagnosisSettingModel,
)
from app.shared.utils.generators import generate_cuid


def _to_alias(model: DiagnosisAliasModel) -> DiagnosisAlias:
    return DiagnosisAlias(
        id=model.id,
        raw_value=model.raw_value,
        normalised_key=model.normalised_key,
        diagnosis_type_id=model.diagnosis_type_id,
        diagnosis_id=model.diagnosis_id,
        source=model.source,
        confidence=model.confidence,
    )


def _to_overlay(model: TenantDiagnosisSettingModel) -> TenantOverlay:
    return TenantOverlay(
        tenant_id=model.tenant_id,
        diagnosis_type_id=model.diagnosis_type_id,
        diagnosis_id=model.diagnosis_id,
        is_enabled=model.is_enabled,
        sort_order=model.sort_order,
        local_label=model.local_label,
    )


def _apply(model, **fields) -> None:
    for key, value in fields.items():
        if value is not None:
            setattr(model, key, value)


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
        stmt = select(DiagnosisTypeModel).order_by(
            DiagnosisTypeModel.sort_order, DiagnosisTypeModel.name
        )
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

    # === Writes (platform admin only) ===

    async def create_type(
        self, *, code: str, name: str, description: str | None, sort_order: int
    ) -> DiagnosisType:
        model = DiagnosisTypeModel(
            id=generate_cuid(),
            code=code,
            name=name,
            description=description,
            sort_order=sort_order,
        )
        self._session.add(model)
        await self._session.flush()
        return _to_type(model)

    async def update_type(
        self,
        type_id: str,
        *,
        name: str | None = None,
        description: str | None = None,
        sort_order: int | None = None,
    ) -> DiagnosisType | None:
        model = await self._session.get(DiagnosisTypeModel, type_id)
        if model is None:
            return None
        _apply(model, name=name, description=description, sort_order=sort_order)
        await self._session.flush()
        return _to_type(model)

    async def set_type_active(self, type_id: str, *, is_active: bool) -> DiagnosisType | None:
        model = await self._session.get(DiagnosisTypeModel, type_id)
        if model is None:
            return None
        model.is_active = is_active
        await self._session.flush()
        return _to_type(model)

    async def create_diagnosis(
        self, *, type_id: str, code: str, name: str, description: str | None, sort_order: int
    ) -> Diagnosis:
        model = DiagnosisModel(
            id=generate_cuid(),
            type_id=type_id,
            code=code,
            name=name,
            description=description,
            sort_order=sort_order,
        )
        self._session.add(model)
        await self._session.flush()
        return _to_diagnosis(model)

    async def update_diagnosis(
        self,
        diagnosis_id: str,
        *,
        name: str | None = None,
        description: str | None = None,
        sort_order: int | None = None,
    ) -> Diagnosis | None:
        model = await self._session.get(DiagnosisModel, diagnosis_id)
        if model is None:
            return None
        _apply(model, name=name, description=description, sort_order=sort_order)
        await self._session.flush()
        return _to_diagnosis(model)

    async def set_diagnosis_active(self, diagnosis_id: str, *, is_active: bool) -> Diagnosis | None:
        model = await self._session.get(DiagnosisModel, diagnosis_id)
        if model is None:
            return None
        model.is_active = is_active
        await self._session.flush()
        return _to_diagnosis(model)

    # === Tenant overlay ===

    async def tenant_overlay(self, tenant_id: str) -> dict[tuple[str, str | None], TenantOverlay]:
        stmt = select(TenantDiagnosisSettingModel).where(
            TenantDiagnosisSettingModel.tenant_id == tenant_id
        )
        rows = (await self._session.execute(stmt)).scalars()
        return {(r.diagnosis_type_id, r.diagnosis_id): _to_overlay(r) for r in rows}

    async def set_tenant_overlay(
        self,
        tenant_id: str,
        *,
        diagnosis_type_id: str,
        diagnosis_id: str | None,
        is_enabled: bool | None = None,
        sort_order: int | None = None,
        local_label: str | None = None,
    ) -> TenantOverlay:
        stmt = select(TenantDiagnosisSettingModel).where(
            TenantDiagnosisSettingModel.tenant_id == tenant_id,
            TenantDiagnosisSettingModel.diagnosis_type_id == diagnosis_type_id,
            TenantDiagnosisSettingModel.diagnosis_id.is_(diagnosis_id)
            if diagnosis_id is None
            else TenantDiagnosisSettingModel.diagnosis_id == diagnosis_id,
        )
        model = (await self._session.execute(stmt)).scalar_one_or_none()
        if model is None:
            model = TenantDiagnosisSettingModel(
                id=generate_cuid(),
                tenant_id=tenant_id,
                diagnosis_type_id=diagnosis_type_id,
                diagnosis_id=diagnosis_id,
                is_enabled=True if is_enabled is None else is_enabled,
                sort_order=sort_order,
                local_label=local_label,
            )
            self._session.add(model)
        else:
            _apply(model, sort_order=sort_order, local_label=local_label)
            if is_enabled is not None:
                model.is_enabled = is_enabled
        await self._session.flush()
        return _to_overlay(model)

    # === Legacy aliases ===

    async def list_aliases(self, *, confidence: str | None = None) -> list[DiagnosisAlias]:
        stmt = select(DiagnosisAliasModel).order_by(DiagnosisAliasModel.normalised_key)
        if confidence is not None:
            stmt = stmt.where(DiagnosisAliasModel.confidence == confidence)
        return [_to_alias(r) for r in (await self._session.execute(stmt)).scalars()]

    async def upsert_alias(
        self,
        *,
        raw_value: str,
        diagnosis_type_id: str,
        diagnosis_id: str | None,
        source: str,
        confidence: str,
    ) -> DiagnosisAlias:
        key = normalise_diagnosis_value(raw_value)
        stmt = select(DiagnosisAliasModel).where(DiagnosisAliasModel.normalised_key == key)
        model = (await self._session.execute(stmt)).scalar_one_or_none()
        if model is None:
            model = DiagnosisAliasModel(
                id=generate_cuid(),
                raw_value=raw_value,
                normalised_key=key,
                diagnosis_type_id=diagnosis_type_id,
                diagnosis_id=diagnosis_id,
                source=source,
                confidence=confidence,
            )
            self._session.add(model)
        else:
            model.raw_value = raw_value
            model.diagnosis_type_id = diagnosis_type_id
            model.diagnosis_id = diagnosis_id
            model.source = source
            model.confidence = confidence
        await self._session.flush()
        return _to_alias(model)

    async def alias_lookup(self) -> dict[str, tuple[str, str | None]]:
        rows = (await self._session.execute(select(DiagnosisAliasModel))).scalars()
        return {r.normalised_key: (r.diagnosis_type_id, r.diagnosis_id) for r in rows}
