"""SQL implementations of the eligible-member + clinical-subject repositories."""

import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.clinical_subject import ClinicalSubject
from app.domain.entities.eligible_member import EligibleMember
from app.domain.repositories.eligible_member_repository import (
    ClinicalSubjectRepository,
    EligibleMemberClinicalLinkRepository,
    EligibleMemberRepository,
)
from app.domain.value_objects.core import (
    ClientId,
    ClinicalSubjectId,
    EligibleMemberId,
    TenantId,
)
from app.infrastructure.mappers.eligible_member_mapper import (
    ClinicalSubjectMapper,
    EligibleMemberMapper,
)
from app.infrastructure.models.eligible_member_model import (
    ClinicalSubjectModel,
    EligibleMemberClinicalLinkModel,
    EligibleMemberModel,
)

_link_audit_logger = logging.getLogger("evexia.privacy.subject_link")


class EligibleMemberRepositoryImpl(EligibleMemberRepository):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_by_id(
        self, entity_id: EligibleMemberId
    ) -> EligibleMember | None:
        row = await self._session.get(EligibleMemberModel, entity_id.value)
        return EligibleMemberMapper.to_entity(row) if row else None

    async def save(self, entity: EligibleMember) -> None:
        existing = await self._session.get(EligibleMemberModel, entity.id.value)
        new_model = EligibleMemberMapper.to_model(entity)
        if existing is None:
            self._session.add(new_model)
        else:
            existing.client_id = new_model.client_id
            existing.employer_member_id = new_model.employer_member_id
            existing.relation = new_model.relation
            existing.status = new_model.status
            existing.primary_employee_member_id = new_model.primary_employee_member_id
            existing.coverage_start = new_model.coverage_start
            existing.coverage_end = new_model.coverage_end
            existing.work_email = new_model.work_email
            existing.personal_email = new_model.personal_email
            existing.display_label = new_model.display_label
            existing.last_imported_at = new_model.last_imported_at
            existing.suspended_at = new_model.suspended_at
            existing.terminated_at = new_model.terminated_at
            existing.updated_at = new_model.updated_at
        await self._session.flush()

    async def delete(self, entity_id: EligibleMemberId) -> None:
        existing = await self._session.get(EligibleMemberModel, entity_id.value)
        if existing is not None:
            await self._session.delete(existing)
            await self._session.flush()

    async def exists(self, entity_id: EligibleMemberId) -> bool:
        existing = await self._session.get(EligibleMemberModel, entity_id.value)
        return existing is not None

    async def list_for_client(
        self,
        tenant_id: TenantId,
        client_id: ClientId,
        *,
        limit: int = 200,
        offset: int = 0,
    ) -> list[EligibleMember]:
        stmt = (
            select(EligibleMemberModel)
            .where(
                EligibleMemberModel.tenant_id == tenant_id.value,
                EligibleMemberModel.client_id == client_id.value,
            )
            .order_by(EligibleMemberModel.employer_member_id)
            .limit(limit)
            .offset(offset)
        )
        rows = (await self._session.execute(stmt)).scalars().all()
        return [EligibleMemberMapper.to_entity(r) for r in rows]

    async def find_by_employer_member_id(
        self,
        tenant_id: TenantId,
        client_id: ClientId,
        employer_member_id: str,
    ) -> EligibleMember | None:
        stmt = select(EligibleMemberModel).where(
            EligibleMemberModel.tenant_id == tenant_id.value,
            EligibleMemberModel.client_id == client_id.value,
            EligibleMemberModel.employer_member_id == employer_member_id,
        )
        row = (await self._session.execute(stmt)).scalar_one_or_none()
        return EligibleMemberMapper.to_entity(row) if row else None


class ClinicalSubjectRepositoryImpl(ClinicalSubjectRepository):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_by_id(
        self, entity_id: ClinicalSubjectId
    ) -> ClinicalSubject | None:
        row = await self._session.get(ClinicalSubjectModel, entity_id.value)
        return ClinicalSubjectMapper.to_entity(row) if row else None

    async def save(self, entity: ClinicalSubject) -> None:
        existing = await self._session.get(ClinicalSubjectModel, entity.id.value)
        new_model = ClinicalSubjectMapper.to_model(entity)
        if existing is None:
            self._session.add(new_model)
        else:
            existing.preferred_language = new_model.preferred_language
            existing.preferred_pronouns = new_model.preferred_pronouns
            existing.preferred_contact_method = new_model.preferred_contact_method
            existing.notes_for_continuity = new_model.notes_for_continuity
            existing.is_active = new_model.is_active
            existing.deactivated_at = new_model.deactivated_at
            existing.updated_at = new_model.updated_at
        await self._session.flush()

    async def delete(self, entity_id: ClinicalSubjectId) -> None:
        existing = await self._session.get(ClinicalSubjectModel, entity_id.value)
        if existing is not None:
            await self._session.delete(existing)
            await self._session.flush()

    async def exists(self, entity_id: ClinicalSubjectId) -> bool:
        existing = await self._session.get(ClinicalSubjectModel, entity_id.value)
        return existing is not None

    async def find_by_pseudonym(
        self, tenant_id: TenantId, pseudonym: str
    ) -> ClinicalSubject | None:
        stmt = select(ClinicalSubjectModel).where(
            ClinicalSubjectModel.tenant_id == tenant_id.value,
            ClinicalSubjectModel.pseudonym == pseudonym,
        )
        row = (await self._session.execute(stmt)).scalar_one_or_none()
        return ClinicalSubjectMapper.to_entity(row) if row else None


class EligibleMemberClinicalLinkRepositoryImpl(
    EligibleMemberClinicalLinkRepository
):
    """Every read here emits a structured ``subject-identity-disclosure`` log line.

    The DPO uses this stream to demonstrate that re-identification accesses are
    discoverable and bounded to declared purposes.
    """

    def __init__(self, session: AsyncSession):
        self._session = session

    async def link(
        self,
        *,
        tenant_id: TenantId,
        member_id: EligibleMemberId,
        subject_id: ClinicalSubjectId,
    ) -> None:
        self._session.add(
            EligibleMemberClinicalLinkModel(
                tenant_id=tenant_id.value,
                member_id=member_id.value,
                subject_id=subject_id.value,
            )
        )
        await self._session.flush()

    async def subject_for_member(
        self,
        tenant_id: TenantId,
        member_id: EligibleMemberId,
        *,
        requester_id: str,
        purpose: str,
    ) -> ClinicalSubjectId | None:
        stmt = select(EligibleMemberClinicalLinkModel.subject_id).where(
            EligibleMemberClinicalLinkModel.tenant_id == tenant_id.value,
            EligibleMemberClinicalLinkModel.member_id == member_id.value,
        )
        result = (await self._session.execute(stmt)).scalar_one_or_none()
        _link_audit_logger.info(
            "subject-identity-disclosure",
            extra={
                "tenant_id": tenant_id.value,
                "direction": "member_to_subject",
                "member_id": member_id.value,
                "found": result is not None,
                "requester_id": requester_id,
                "purpose": purpose,
            },
        )
        return ClinicalSubjectId(result) if result else None

    async def member_for_subject(
        self,
        tenant_id: TenantId,
        subject_id: ClinicalSubjectId,
        *,
        requester_id: str,
        purpose: str,
    ) -> EligibleMemberId | None:
        stmt = select(EligibleMemberClinicalLinkModel.member_id).where(
            EligibleMemberClinicalLinkModel.tenant_id == tenant_id.value,
            EligibleMemberClinicalLinkModel.subject_id == subject_id.value,
        )
        result = (await self._session.execute(stmt)).scalar_one_or_none()
        _link_audit_logger.info(
            "subject-identity-disclosure",
            extra={
                "tenant_id": tenant_id.value,
                "direction": "subject_to_member",
                "subject_id": subject_id.value,
                "found": result is not None,
                "requester_id": requester_id,
                "purpose": purpose,
            },
        )
        return EligibleMemberId(result) if result else None
