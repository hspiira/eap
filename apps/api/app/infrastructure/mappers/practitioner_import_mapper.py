"""Mapping between practitioner import entities and their models."""

from app.domain.entities.practitioner_import import (
    ImportReviewReason,
    PractitionerImportBatchEntity,
    PractitionerImportRowEntity,
)
from app.domain.enums.provider_network import (
    ImportBatchStatus,
    ImportReasonCode,
    PractitionerImportOutcome,
)
from app.domain.value_objects.core import TenantId, UserId
from app.domain.value_objects.provider_network import (
    PractitionerImportBatchId,
    PractitionerImportRowId,
)
from app.infrastructure.models.practitioner_import_model import (
    PractitionerImportBatchModel,
    PractitionerImportRowModel,
)
from app.shared.utils.datetime import ensure_utc


class PractitionerImportMapper:
    @staticmethod
    def batch_to_entity(model: PractitionerImportBatchModel) -> PractitionerImportBatchEntity:
        return PractitionerImportBatchEntity(
            id=PractitionerImportBatchId(model.id),
            tenant_id=TenantId(model.tenant_id),
            source_system=model.source_system,
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
    def batch_to_model(entity: PractitionerImportBatchEntity) -> PractitionerImportBatchModel:
        return PractitionerImportBatchModel(
            id=entity.id.value,
            tenant_id=entity.tenant_id.value,
            source_system=entity.source_system,
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
    def row_to_entity(model: PractitionerImportRowModel) -> PractitionerImportRowEntity:
        return PractitionerImportRowEntity(
            id=PractitionerImportRowId(model.id),
            batch_id=PractitionerImportBatchId(model.batch_id),
            tenant_id=TenantId(model.tenant_id),
            sheet_name=model.sheet_name,
            row_number=model.row_number,
            raw_name=model.raw_name,
            normalized_name=model.normalized_name,
            organisation_name=model.organisation_name,
            raw_profession=model.raw_profession,
            mapped_profession=model.mapped_profession,
            contact_email=model.contact_email,
            outcome=PractitionerImportOutcome(model.outcome),
            reasons=tuple(_reason(item) for item in (model.reasons or ())),
            provenance=dict(model.provenance or {}),
            created_at=ensure_utc(model.created_at),
            imported_provider_id=model.imported_provider_id,
            imported_organisation_id=model.imported_organisation_id,
            imported_affiliation_id=model.imported_affiliation_id,
        )

    @staticmethod
    def row_to_model(
        entity: PractitionerImportRowEntity, *, file_hash: str
    ) -> PractitionerImportRowModel:
        return PractitionerImportRowModel(
            id=entity.id.value,
            tenant_id=entity.tenant_id.value,
            batch_id=entity.batch_id.value,
            sheet_name=entity.sheet_name,
            row_number=entity.row_number,
            replay_key=entity.replay_key(file_hash),
            raw_name=entity.raw_name,
            normalized_name=entity.normalized_name,
            organisation_name=entity.organisation_name,
            raw_profession=entity.raw_profession,
            mapped_profession=entity.mapped_profession,
            contact_email=entity.contact_email,
            outcome=entity.outcome,
            reasons=[{"code": r.code.value, "message": r.message} for r in entity.reasons],
            provenance=entity.provenance,
            imported_provider_id=entity.imported_provider_id,
            imported_organisation_id=entity.imported_organisation_id,
            imported_affiliation_id=entity.imported_affiliation_id,
            created_at=entity.created_at,
        )


def _reason(item: object) -> ImportReviewReason:
    """Read a stored reason, tolerating the pre-code format.

    Rows staged before reasons carried codes persisted bare strings; a listing
    that raised on them would make every old batch unreadable.
    """
    if isinstance(item, dict):
        return ImportReviewReason(ImportReasonCode(item["code"]), item["message"])
    return ImportReviewReason(ImportReasonCode.LEGACY, str(item))
