"""SQL implementations of the eligible-member + clinical-subject repositories."""

import logging

from sqlalchemy import delete, func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.clinical_subject import ClinicalSubject
from app.domain.entities.eligible_member import EligibleMember
from app.domain.enums import EligibilityStatus, MemberRelation
from app.domain.exceptions import ConflictError
from app.domain.repositories.eligible_member_repository import (
    ClinicalSubjectRepository,
    EligibleMemberClinicalLinkRepository,
    EligibleMemberRepository,
    MemberMergeResult,
    MemberRosterStats,
)
from app.domain.value_objects.core import (
    ClientId,
    ClinicalSubjectId,
    EligibleMemberId,
    TenantId,
    UserId,
)
from app.infrastructure.mappers.eligible_member_mapper import (
    ClinicalSubjectMapper,
    EligibleMemberMapper,
)
from app.infrastructure.models.case_model import CaseModel
from app.infrastructure.models.clinical_note_model import ClinicalNoteModel
from app.infrastructure.models.eap_programme_model import AuthorizationModel
from app.infrastructure.models.eligible_member_model import (
    ClinicalSubjectModel,
    EligibleMemberClinicalLinkModel,
    EligibleMemberModel,
)
from app.infrastructure.models.member_next_of_kin_model import MemberNextOfKinModel
from app.infrastructure.models.service_session_model import ServiceSessionModel
from app.shared.utils.datetime import utc_now

_link_audit_logger = logging.getLogger("evexia.privacy.subject_link")


class EligibleMemberRepositoryImpl(EligibleMemberRepository):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_by_id(self, entity_id: EligibleMemberId) -> EligibleMember | None:
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
            existing.date_of_birth = new_model.date_of_birth
            existing.gender = new_model.gender
            existing.phone = new_model.phone
            existing.staff_number = new_model.staff_number
            existing.import_source_id = new_model.import_source_id
            existing.national_id = new_model.national_id
            existing.passport_number = new_model.passport_number
            existing.last_imported_at = new_model.last_imported_at
            existing.suspended_at = new_model.suspended_at
            existing.terminated_at = new_model.terminated_at
            existing.user_id = new_model.user_id
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

    async def list_for_primary(
        self,
        tenant_id: TenantId,
        client_id: ClientId,
        primary_employee_member_id: EligibleMemberId,
        *,
        limit: int = 100,
    ) -> list[EligibleMember]:
        stmt = (
            select(EligibleMemberModel)
            .where(
                EligibleMemberModel.tenant_id == tenant_id.value,
                EligibleMemberModel.client_id == client_id.value,
                EligibleMemberModel.primary_employee_member_id == primary_employee_member_id.value,
            )
            .order_by(EligibleMemberModel.employer_member_id, EligibleMemberModel.id)
            .limit(limit)
        )
        rows = (await self._session.execute(stmt)).scalars().all()
        return [EligibleMemberMapper.to_entity(r) for r in rows]

    @staticmethod
    def _filters(
        stmt,
        *,
        tenant_id: TenantId,
        client_id: ClientId | None,
        status: EligibilityStatus | None,
        relation: MemberRelation | None,
        search: str | None,
    ):
        stmt = stmt.where(EligibleMemberModel.tenant_id == tenant_id.value)
        if client_id:
            stmt = stmt.where(EligibleMemberModel.client_id == client_id.value)
        if status:
            stmt = stmt.where(EligibleMemberModel.status == status)
        if relation:
            stmt = stmt.where(EligibleMemberModel.relation == relation)
        if search:
            pattern = f"%{search.strip()}%"
            stmt = stmt.where(
                or_(
                    EligibleMemberModel.employer_member_id.ilike(pattern),
                    EligibleMemberModel.display_label.ilike(pattern),
                    EligibleMemberModel.work_email.ilike(pattern),
                    EligibleMemberModel.personal_email.ilike(pattern),
                    EligibleMemberModel.phone.ilike(pattern),
                    EligibleMemberModel.staff_number.ilike(pattern),
                )
            )
        return stmt

    async def list_all(
        self,
        tenant_id: TenantId,
        *,
        client_id: ClientId | None = None,
        status: EligibilityStatus | None = None,
        relation: MemberRelation | None = None,
        search: str | None = None,
        limit: int = 100,
        offset: int = 0,
        sort_by: str = "created_at",
        sort_desc: bool = True,
    ) -> list[EligibleMember]:
        allowed = {
            "created_at",
            "updated_at",
            "employer_member_id",
            "display_label",
            "status",
            "relation",
        }
        if sort_by not in allowed:
            raise ValueError(f"Invalid member sort column: {sort_by}")
        stmt = self._filters(
            select(EligibleMemberModel),
            tenant_id=tenant_id,
            client_id=client_id,
            status=status,
            relation=relation,
            search=search,
        )
        column = getattr(EligibleMemberModel, sort_by)
        order = column.desc() if sort_desc else column.asc()
        rows = (
            (
                await self._session.execute(
                    stmt.order_by(order, EligibleMemberModel.id.asc()).limit(limit).offset(offset)
                )
            )
            .scalars()
            .all()
        )
        return [EligibleMemberMapper.to_entity(r) for r in rows]

    async def count(
        self,
        tenant_id: TenantId,
        *,
        client_id: ClientId | None = None,
        status: EligibilityStatus | None = None,
        relation: MemberRelation | None = None,
        search: str | None = None,
    ) -> int:
        stmt = self._filters(
            select(func.count(EligibleMemberModel.id)),
            tenant_id=tenant_id,
            client_id=client_id,
            status=status,
            relation=relation,
            search=search,
        )
        return int((await self._session.execute(stmt)).scalar_one())

    async def count_by_status(
        self,
        tenant_id: TenantId,
        *,
        client_id: ClientId | None = None,
        status: EligibilityStatus | None = None,
        relation: MemberRelation | None = None,
        search: str | None = None,
    ) -> MemberRosterStats:
        filters = {
            "tenant_id": tenant_id,
            "client_id": client_id,
            "status": status,
            "relation": relation,
            "search": search,
        }
        grouped = self._filters(
            select(EligibleMemberModel.status, func.count(EligibleMemberModel.id)).group_by(
                EligibleMemberModel.status
            ),
            **filters,
        )
        by_status = {
            EligibilityStatus(value): int(count)
            for value, count in (await self._session.execute(grouped)).all()
        }
        with_account_stmt = self._filters(
            select(func.count(EligibleMemberModel.id)).where(
                EligibleMemberModel.user_id.is_not(None)
            ),
            **filters,
        )
        with_account = int((await self._session.execute(with_account_stmt)).scalar_one())
        return MemberRosterStats(by_status=by_status, with_account=with_account)

    async def next_member_sequence(
        self,
        tenant_id: TenantId,
        client_id: ClientId,
        prefix: str,
    ) -> int:
        """Highest numeric suffix already issued under ``prefix``, plus one.

        Reads existing ids rather than a counter table so a client whose members
        were imported with hand-written ids still continues from the top.
        """
        stmt = select(EligibleMemberModel.employer_member_id).where(
            EligibleMemberModel.tenant_id == tenant_id.value,
            EligibleMemberModel.client_id == client_id.value,
            EligibleMemberModel.employer_member_id.like(f"{prefix}-%"),
        )
        rows = (await self._session.execute(stmt)).scalars().all()
        highest = 0
        for value in rows:
            suffix = value[len(prefix) + 1 :]
            if suffix.isdigit():
                highest = max(highest, int(suffix))
        return highest + 1

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

    async def find_by_import_source_id(
        self,
        tenant_id: TenantId,
        client_id: ClientId,
        import_source_id: str,
    ) -> EligibleMember | None:
        stmt = select(EligibleMemberModel).where(
            EligibleMemberModel.tenant_id == tenant_id.value,
            EligibleMemberModel.client_id == client_id.value,
            EligibleMemberModel.import_source_id == import_source_id,
        )
        row = (await self._session.execute(stmt)).scalar_one_or_none()
        return EligibleMemberMapper.to_entity(row) if row else None

    async def find_by_user_id(self, tenant_id: TenantId, user_id: UserId) -> EligibleMember | None:
        row = (
            await self._session.execute(
                select(EligibleMemberModel).where(
                    EligibleMemberModel.tenant_id == tenant_id.value,
                    EligibleMemberModel.user_id == user_id.value,
                )
            )
        ).scalar_one_or_none()
        return EligibleMemberMapper.to_entity(row) if row else None

    async def merge_into(
        self, tenant_id: TenantId, source_id: EligibleMemberId, target_id: EligibleMemberId
    ) -> MemberMergeResult:
        ids = [source_id.value, target_id.value]
        rows = (
            (
                await self._session.execute(
                    select(EligibleMemberModel)
                    .where(
                        EligibleMemberModel.tenant_id == tenant_id.value,
                        EligibleMemberModel.id.in_(ids),
                    )
                    .with_for_update()
                )
            )
            .scalars()
            .all()
        )
        members = {row.id: row for row in rows}
        source, target = members.get(source_id.value), members.get(target_id.value)
        if source is None or target is None:
            raise ConflictError("Both members must exist in the current tenant")
        if source.client_id != target.client_id:
            raise ConflictError("Members must belong to the same client")
        if source.relation != target.relation or (
            source.relation != MemberRelation.EMPLOYEE
            and source.primary_employee_member_id != target.primary_employee_member_id
        ):
            raise ConflictError("Members must have the same relationship context")
        if source.user_id and target.user_id:
            raise ConflictError("Unlink one member account before merging")

        contacts = (
            await self._session.execute(
                select(MemberNextOfKinModel.member_id, MemberNextOfKinModel.is_primary).where(
                    MemberNextOfKinModel.tenant_id == tenant_id.value,
                    MemberNextOfKinModel.member_id.in_(ids),
                    MemberNextOfKinModel.is_primary.is_(True),
                )
            )
        ).all()
        if {member_id for member_id, _ in contacts} == set(ids):
            raise ConflictError("Choose one primary next-of-kin contact before merging")

        links = (
            (
                await self._session.execute(
                    select(EligibleMemberClinicalLinkModel).where(
                        EligibleMemberClinicalLinkModel.tenant_id == tenant_id.value,
                        EligibleMemberClinicalLinkModel.member_id.in_(ids),
                    )
                )
            )
            .scalars()
            .all()
        )
        subjects = {link.member_id: link.subject_id for link in links}
        if set(subjects) != set(ids):
            raise ConflictError("Both members need a clinical continuity link before merging")
        source_subject, target_subject = subjects[source_id.value], subjects[target_id.value]

        operations = {
            "sessions": update(ServiceSessionModel)
            .where(
                ServiceSessionModel.tenant_id == tenant_id.value,
                ServiceSessionModel.member_id == source_id.value,
            )
            .values(member_id=target_id.value),
            "beneficiaries": update(EligibleMemberModel)
            .where(
                EligibleMemberModel.tenant_id == tenant_id.value,
                EligibleMemberModel.primary_employee_member_id == source_id.value,
            )
            .values(primary_employee_member_id=target_id.value),
            "next_of_kin": update(MemberNextOfKinModel)
            .where(
                MemberNextOfKinModel.tenant_id == tenant_id.value,
                MemberNextOfKinModel.member_id == source_id.value,
            )
            .values(member_id=target_id.value),
            "cases": update(CaseModel)
            .where(
                CaseModel.tenant_id == tenant_id.value,
                CaseModel.clinical_subject_id == source_subject,
            )
            .values(clinical_subject_id=target_subject),
            "clinical_notes": update(ClinicalNoteModel)
            .where(
                ClinicalNoteModel.tenant_id == tenant_id.value,
                ClinicalNoteModel.clinical_subject_id == source_subject,
            )
            .values(clinical_subject_id=target_subject),
            "authorizations": update(AuthorizationModel)
            .where(
                AuthorizationModel.tenant_id == tenant_id.value,
                AuthorizationModel.clinical_subject_id == source_subject,
            )
            .values(clinical_subject_id=target_subject),
        }
        counts: MemberMergeResult = {}
        for name, statement in operations.items():
            counts[name] = (await self._session.execute(statement)).rowcount or 0
        if source.user_id and not target.user_id:
            linked_user_id = source.user_id
            source.user_id = None
            await self._session.flush()
            target.user_id = linked_user_id
            counts["account_links"] = 1
        else:
            counts["account_links"] = 0
        await self._session.execute(
            delete(EligibleMemberClinicalLinkModel).where(
                EligibleMemberClinicalLinkModel.tenant_id == tenant_id.value,
                EligibleMemberClinicalLinkModel.member_id == source_id.value,
            )
        )
        await self._session.execute(
            delete(ClinicalSubjectModel).where(
                ClinicalSubjectModel.tenant_id == tenant_id.value,
                ClinicalSubjectModel.id == source_subject,
            )
        )
        await self._session.delete(source)
        await self._session.flush()
        return counts


class ClinicalSubjectRepositoryImpl(ClinicalSubjectRepository):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_by_id(self, entity_id: ClinicalSubjectId) -> ClinicalSubject | None:
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


class EligibleMemberClinicalLinkRepositoryImpl(EligibleMemberClinicalLinkRepository):
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
        now = utc_now()
        self._session.add(
            EligibleMemberClinicalLinkModel(
                tenant_id=tenant_id.value,
                member_id=member_id.value,
                subject_id=subject_id.value,
                created_at=now,
                updated_at=now,
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
