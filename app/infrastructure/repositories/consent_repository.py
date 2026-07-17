"""SQL implementations of the consent / DataSharingRegister / DPOContact repositories."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.consent import Consent
from app.domain.entities.data_sharing_register import DataSharingRegisterEntry
from app.domain.entities.dpo_contact import DPOContact
from app.domain.enums import ConsentPurpose, ConsentScope, ConsentStatus
from app.domain.repositories.consent_repository import (
    ConsentRepository,
    DataSharingRegisterRepository,
    DPOContactRepository,
)
from app.domain.value_objects.core import (
    ClinicalSubjectId,
    ConsentId,
    DataSharingRegisterEntryId,
    DPOContactId,
    TenantId,
)
from app.infrastructure.mappers.consent_mappers import (
    ConsentMapper,
    DataSharingRegisterMapper,
    DPOContactMapper,
)
from app.infrastructure.models.consent_models import (
    ConsentModel,
    DataSharingRegisterEntryModel,
    DPOContactModel,
)


class ConsentRepositoryImpl(ConsentRepository):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_by_id(self, entity_id: ConsentId) -> Consent | None:
        row = await self._session.get(ConsentModel, entity_id.value)
        return ConsentMapper.to_entity(row) if row else None

    async def save(self, entity: Consent) -> None:
        existing = await self._session.get(ConsentModel, entity.id.value)
        new_model = ConsentMapper.to_model(entity)
        if existing is None:
            self._session.add(new_model)
        else:
            existing.status = new_model.status
            existing.expires_on = new_model.expires_on
            existing.granted_at = new_model.granted_at
            existing.granted_by_subject_reference = (
                new_model.granted_by_subject_reference
            )
            existing.signed_artifact_document_id = (
                new_model.signed_artifact_document_id
            )
            existing.revoked_at = new_model.revoked_at
            existing.revoked_reason = new_model.revoked_reason
            existing.updated_at = new_model.updated_at
        await self._session.flush()

    async def delete(self, entity_id: ConsentId) -> None:
        existing = await self._session.get(ConsentModel, entity_id.value)
        if existing is not None:
            await self._session.delete(existing)
            await self._session.flush()

    async def exists(self, entity_id: ConsentId) -> bool:
        existing = await self._session.get(ConsentModel, entity_id.value)
        return existing is not None

    async def list_for_subject(
        self, tenant_id: TenantId, subject_id: ClinicalSubjectId
    ) -> list[Consent]:
        stmt = (
            select(ConsentModel)
            .where(
                ConsentModel.tenant_id == tenant_id.value,
                ConsentModel.subject_clinical_subject_id == subject_id.value,
            )
            .order_by(ConsentModel.requested_at.desc())
        )
        rows = (await self._session.execute(stmt)).scalars().all()
        return [ConsentMapper.to_entity(r) for r in rows]

    async def find_active_for_disclosure(
        self,
        tenant_id: TenantId,
        subject_id: ClinicalSubjectId,
        *,
        scope: ConsentScope,
        purpose: ConsentPurpose,
        disclosure_to: str,
    ) -> Consent | None:
        stmt = select(ConsentModel).where(
            ConsentModel.tenant_id == tenant_id.value,
            ConsentModel.subject_clinical_subject_id == subject_id.value,
            ConsentModel.scope == scope.value,
            ConsentModel.purpose == purpose.value,
            ConsentModel.disclosure_to == disclosure_to,
            ConsentModel.status == ConsentStatus.ACTIVE.value,
        )
        row = (await self._session.execute(stmt)).scalars().first()
        if row is None:
            return None
        entity = ConsentMapper.to_entity(row)
        return entity if entity.is_active() else None


class DataSharingRegisterRepositoryImpl(DataSharingRegisterRepository):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_by_id(
        self, entity_id: DataSharingRegisterEntryId
    ) -> DataSharingRegisterEntry | None:
        row = await self._session.get(
            DataSharingRegisterEntryModel, entity_id.value
        )
        return DataSharingRegisterMapper.to_entity(row) if row else None

    async def save(self, entity: DataSharingRegisterEntry) -> None:
        existing = await self._session.get(
            DataSharingRegisterEntryModel, entity.id.value
        )
        if existing is None:
            self._session.add(DataSharingRegisterMapper.to_model(entity))
        await self._session.flush()

    async def delete(self, entity_id: DataSharingRegisterEntryId) -> None:
        existing = await self._session.get(
            DataSharingRegisterEntryModel, entity_id.value
        )
        if existing is not None:
            await self._session.delete(existing)
            await self._session.flush()

    async def exists(self, entity_id: DataSharingRegisterEntryId) -> bool:
        existing = await self._session.get(
            DataSharingRegisterEntryModel, entity_id.value
        )
        return existing is not None

    async def list_for_tenant(
        self, tenant_id: TenantId, *, limit: int = 200
    ) -> list[DataSharingRegisterEntry]:
        stmt = (
            select(DataSharingRegisterEntryModel)
            .where(DataSharingRegisterEntryModel.tenant_id == tenant_id.value)
            .order_by(DataSharingRegisterEntryModel.shared_at.desc())
            .limit(limit)
        )
        rows = (await self._session.execute(stmt)).scalars().all()
        return [DataSharingRegisterMapper.to_entity(r) for r in rows]

    async def list_for_subject(
        self, tenant_id: TenantId, subject_id: ClinicalSubjectId
    ) -> list[DataSharingRegisterEntry]:
        stmt = (
            select(DataSharingRegisterEntryModel)
            .where(
                DataSharingRegisterEntryModel.tenant_id == tenant_id.value,
                DataSharingRegisterEntryModel.subject_clinical_subject_id
                == subject_id.value,
            )
            .order_by(DataSharingRegisterEntryModel.shared_at.desc())
        )
        rows = (await self._session.execute(stmt)).scalars().all()
        return [DataSharingRegisterMapper.to_entity(r) for r in rows]


class DPOContactRepositoryImpl(DPOContactRepository):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_by_id(self, entity_id: DPOContactId) -> DPOContact | None:
        row = await self._session.get(DPOContactModel, entity_id.value)
        return DPOContactMapper.to_entity(row) if row else None

    async def save(self, entity: DPOContact) -> None:
        existing = await self._session.get(DPOContactModel, entity.id.value)
        new_model = DPOContactMapper.to_model(entity)
        if existing is None:
            self._session.add(new_model)
        else:
            existing.full_name = new_model.full_name
            existing.email = new_model.email
            existing.phone = new_model.phone
            existing.role_title = new_model.role_title
            existing.effective_from = new_model.effective_from
            existing.effective_until = new_model.effective_until
            existing.appointed_by = new_model.appointed_by
            existing.updated_at = new_model.updated_at
        await self._session.flush()

    async def delete(self, entity_id: DPOContactId) -> None:
        existing = await self._session.get(DPOContactModel, entity_id.value)
        if existing is not None:
            await self._session.delete(existing)
            await self._session.flush()

    async def exists(self, entity_id: DPOContactId) -> bool:
        existing = await self._session.get(DPOContactModel, entity_id.value)
        return existing is not None

    async def current_for_tenant(
        self, tenant_id: TenantId
    ) -> DPOContact | None:
        stmt = (
            select(DPOContactModel)
            .where(
                DPOContactModel.tenant_id == tenant_id.value,
                DPOContactModel.effective_until.is_(None),
            )
            .order_by(DPOContactModel.effective_from.desc())
        )
        row = (await self._session.execute(stmt)).scalars().first()
        return DPOContactMapper.to_entity(row) if row else None

    async def list_for_tenant(
        self, tenant_id: TenantId
    ) -> list[DPOContact]:
        stmt = (
            select(DPOContactModel)
            .where(DPOContactModel.tenant_id == tenant_id.value)
            .order_by(DPOContactModel.effective_from.desc())
        )
        rows = (await self._session.execute(stmt)).scalars().all()
        return [DPOContactMapper.to_entity(r) for r in rows]
