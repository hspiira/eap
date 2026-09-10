"""Maps staged member import batches/rows between entities and models."""

from app.domain.entities.member_import import MemberImportBatchEntity, MemberImportRowEntity
from app.domain.enums.person import MemberImportRowOutcome
from app.domain.enums.provider_network import ImportBatchStatus
from app.domain.value_objects.core import ClientId, EligibleMemberId, TenantId, UserId
from app.domain.value_objects.ids import MemberImportBatchId, MemberImportRowId
from app.infrastructure.models.member_import_model import (
    MemberImportBatchModel,
    MemberImportRowModel,
)
from app.shared.utils.datetime import ensure_utc


class MemberImportMapper:
    @staticmethod
    def batch_to_entity(model: MemberImportBatchModel) -> MemberImportBatchEntity:
        return MemberImportBatchEntity(
            id=MemberImportBatchId(model.id),
            tenant_id=TenantId(model.tenant_id),
            file_name=model.file_name,
            file_hash=model.file_hash,
            row_count=model.row_count,
            status=ImportBatchStatus(model.status),
            staged_by=UserId(model.staged_by),
            applied_by=UserId(model.applied_by) if model.applied_by else None,
            applied_at=ensure_utc(model.applied_at),
            notes=model.notes,
            created_at=ensure_utc(model.created_at),
            updated_at=ensure_utc(model.updated_at),
        )

    @staticmethod
    def batch_to_model(entity: MemberImportBatchEntity) -> MemberImportBatchModel:
        return MemberImportBatchModel(
            id=entity.id.value,
            tenant_id=entity.tenant_id.value,
            file_name=entity.file_name,
            file_hash=entity.file_hash,
            row_count=entity.row_count,
            status=entity.status,
            staged_by=entity.staged_by.value,
            applied_by=entity.applied_by.value if entity.applied_by else None,
            applied_at=entity.applied_at,
            notes=entity.notes,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )

    @staticmethod
    def row_to_entity(model: MemberImportRowModel) -> MemberImportRowEntity:
        return MemberImportRowEntity(
            id=MemberImportRowId(model.id),
            batch_id=MemberImportBatchId(model.batch_id),
            tenant_id=TenantId(model.tenant_id),
            row_number=model.row_number,
            replay_key=model.replay_key,
            outcome=MemberImportRowOutcome(model.outcome),
            decision=model.decision,
            created_at=model.created_at,
            client_code=model.client_code,
            client_id=ClientId(model.client_id) if model.client_id else None,
            import_source_id=model.import_source_id,
            staff_number=model.staff_number,
            display_label=model.display_label,
            work_email=model.work_email,
            personal_email=model.personal_email,
            gender=model.gender,
            date_of_birth=model.date_of_birth,
            date_joined=model.date_joined,
            phone=model.phone,
            national_id=model.national_id,
            passport_number=model.passport_number,
            job_title=model.job_title,
            job_classification=model.job_classification,
            skill=model.skill,
            department=model.department,
            unit=model.unit,
            employment_type=model.employment_type,
            status=model.status,
            relation=model.relation,
            primary_import_source_id=model.primary_import_source_id,
            message=model.message,
            imported_member_id=(
                EligibleMemberId(model.imported_member_id) if model.imported_member_id else None
            ),
        )

    @staticmethod
    def row_to_model(entity: MemberImportRowEntity) -> MemberImportRowModel:
        return MemberImportRowModel(
            id=entity.id.value,
            tenant_id=entity.tenant_id.value,
            batch_id=entity.batch_id.value,
            row_number=entity.row_number,
            replay_key=entity.replay_key,
            outcome=entity.outcome,
            decision=entity.decision,
            client_code=entity.client_code,
            client_id=entity.client_id.value if entity.client_id else None,
            import_source_id=entity.import_source_id,
            staff_number=entity.staff_number,
            display_label=entity.display_label,
            work_email=entity.work_email,
            personal_email=entity.personal_email,
            gender=entity.gender,
            date_of_birth=entity.date_of_birth,
            date_joined=entity.date_joined,
            phone=entity.phone,
            national_id=entity.national_id,
            passport_number=entity.passport_number,
            job_title=entity.job_title,
            job_classification=entity.job_classification,
            skill=entity.skill,
            department=entity.department,
            unit=entity.unit,
            employment_type=entity.employment_type,
            status=entity.status,
            relation=entity.relation,
            primary_import_source_id=entity.primary_import_source_id,
            message=entity.message,
            imported_member_id=(
                entity.imported_member_id.value if entity.imported_member_id else None
            ),
            created_at=entity.created_at,
        )
