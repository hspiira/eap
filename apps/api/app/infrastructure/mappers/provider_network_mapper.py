"""Persistence mappers for the provider network aggregates."""

from app.core.encryption import decrypt, encrypt
from app.domain.entities.provider_affiliation import ProviderAffiliationEntity
from app.domain.entities.provider_organisation import ProviderOrganisationEntity
from app.domain.entities.provider_specialty import (
    ProviderSpecialtyEntity,
    ProviderSpecialtyLinkEntity,
)
from app.domain.entities.session_import import (
    SessionImportBatchEntity,
    SessionImportRowEntity,
)
from app.domain.enums import (
    ClientType,
    SessionAttendance,
    SessionCategory,
    SessionClinicalStatus,
    SessionStatus,
    SessionType,
)
from app.domain.enums.provider_network import (
    DeliveryContext,
    ImportBatchStatus,
    ImportRowOutcome,
    OrganisationApprovalStatus,
)
from app.domain.value_objects.core import ProviderId, TenantId, UserId
from app.domain.value_objects.provider_network import (
    ProviderAffiliationId,
    ProviderOrganisationId,
    ProviderSpecialtyId,
    ProviderSpecialtyLinkId,
    SessionImportBatchId,
    SessionImportRowId,
)
from app.infrastructure.models.provider_affiliation_model import ProviderAffiliationModel
from app.infrastructure.models.provider_organisation_model import ProviderOrganisationModel
from app.infrastructure.models.provider_specialty_model import (
    ProviderSpecialtyLinkModel,
    ProviderSpecialtyModel,
)
from app.infrastructure.models.session_import_model import (
    SessionImportBatchModel,
    SessionImportRowModel,
)
from app.shared.utils.datetime import ensure_utc


class ProviderOrganisationMapper:
    @staticmethod
    def to_entity(model: ProviderOrganisationModel) -> ProviderOrganisationEntity:
        return ProviderOrganisationEntity(
            id=ProviderOrganisationId(model.id),
            tenant_id=TenantId(model.tenant_id),
            name=model.name,
            registration_number=model.registration_number,
            contact_email=model.contact_email,
            contact_phone=model.contact_phone,
            is_active=model.is_active,
            approval_status=OrganisationApprovalStatus(model.approval_status),
            created_at=ensure_utc(model.created_at),
            updated_at=ensure_utc(model.updated_at),
            deleted_at=ensure_utc(model.deleted_at),
        )

    @staticmethod
    def to_model(entity: ProviderOrganisationEntity) -> ProviderOrganisationModel:
        return ProviderOrganisationModel(
            id=entity.id.value,
            tenant_id=entity.tenant_id.value,
            name=entity.name,
            registration_number=entity.registration_number,
            contact_email=entity.contact_email,
            contact_phone=entity.contact_phone,
            is_active=entity.is_active,
            approval_status=entity.approval_status,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
            deleted_at=entity.deleted_at,
        )


class ProviderAffiliationMapper:
    @staticmethod
    def to_entity(model: ProviderAffiliationModel) -> ProviderAffiliationEntity:
        return ProviderAffiliationEntity(
            id=ProviderAffiliationId(model.id),
            tenant_id=TenantId(model.tenant_id),
            provider_id=ProviderId(model.provider_id),
            organisation_id=ProviderOrganisationId(model.organisation_id),
            valid_from=model.valid_from,
            valid_until=model.valid_until,
            created_at=ensure_utc(model.created_at),
            updated_at=ensure_utc(model.updated_at),
        )

    @staticmethod
    def to_model(entity: ProviderAffiliationEntity) -> ProviderAffiliationModel:
        return ProviderAffiliationModel(
            id=entity.id.value,
            tenant_id=entity.tenant_id.value,
            provider_id=entity.provider_id.value,
            organisation_id=entity.organisation_id.value,
            valid_from=entity.valid_from,
            valid_until=entity.valid_until,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )


class ProviderSpecialtyMapper:
    @staticmethod
    def to_entity(model: ProviderSpecialtyModel) -> ProviderSpecialtyEntity:
        return ProviderSpecialtyEntity(
            id=ProviderSpecialtyId(model.id),
            code=model.code,
            label=model.label,
            is_active=model.is_active,
            created_at=ensure_utc(model.created_at),
            updated_at=ensure_utc(model.updated_at),
        )

    @staticmethod
    def to_model(entity: ProviderSpecialtyEntity) -> ProviderSpecialtyModel:
        return ProviderSpecialtyModel(
            id=entity.id.value,
            code=entity.code,
            label=entity.label,
            is_active=entity.is_active,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )

    @staticmethod
    def link_to_entity(model: ProviderSpecialtyLinkModel) -> ProviderSpecialtyLinkEntity:
        return ProviderSpecialtyLinkEntity(
            id=ProviderSpecialtyLinkId(model.id),
            tenant_id=TenantId(model.tenant_id),
            provider_id=ProviderId(model.provider_id),
            specialty_id=ProviderSpecialtyId(model.specialty_id),
            created_at=ensure_utc(model.created_at),
        )

    @staticmethod
    def link_to_model(entity: ProviderSpecialtyLinkEntity) -> ProviderSpecialtyLinkModel:
        return ProviderSpecialtyLinkModel(
            id=entity.id.value,
            tenant_id=entity.tenant_id.value,
            provider_id=entity.provider_id.value,
            specialty_id=entity.specialty_id.value,
            created_at=entity.created_at,
        )


class SessionImportMapper:
    @staticmethod
    def batch_to_entity(model: SessionImportBatchModel) -> SessionImportBatchEntity:
        return SessionImportBatchEntity(
            id=SessionImportBatchId(model.id),
            tenant_id=TenantId(model.tenant_id),
            source_system=model.source_system,
            file_name=model.file_name,
            file_hash=model.file_hash,
            row_count=model.row_count,
            source_record_key_field=model.source_record_key_field,
            status=ImportBatchStatus(model.status),
            staged_by=UserId(model.staged_by),
            applied_by=UserId(model.applied_by) if model.applied_by else None,
            applied_at=ensure_utc(model.applied_at),
            notes=model.notes,
            created_at=ensure_utc(model.created_at),
            updated_at=ensure_utc(model.updated_at),
        )

    @staticmethod
    def batch_to_model(entity: SessionImportBatchEntity) -> SessionImportBatchModel:
        return SessionImportBatchModel(
            id=entity.id.value,
            tenant_id=entity.tenant_id.value,
            source_system=entity.source_system,
            file_name=entity.file_name,
            file_hash=entity.file_hash,
            row_count=entity.row_count,
            source_record_key_field=entity.source_record_key_field,
            status=entity.status,
            staged_by=entity.staged_by.value,
            applied_by=entity.applied_by.value if entity.applied_by else None,
            applied_at=entity.applied_at,
            notes=entity.notes,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )

    @staticmethod
    def row_to_entity(model: SessionImportRowModel) -> SessionImportRowEntity:
        return SessionImportRowEntity(
            id=SessionImportRowId(model.id),
            batch_id=SessionImportBatchId(model.batch_id),
            tenant_id=TenantId(model.tenant_id),
            row_number=model.row_number,
            source_record_key=model.source_record_key,
            raw_practitioner_name=model.raw_practitioner_name,
            session_date=model.session_date,
            staged_replay_key=model.replay_key,
            outcome=ImportRowOutcome(model.outcome),
            delivery_context=DeliveryContext(model.delivery_context),
            provider_id=ProviderId(model.provider_id) if model.provider_id else None,
            provider_affiliation_id=ProviderAffiliationId(model.provider_affiliation_id)
            if model.provider_affiliation_id
            else None,
            imported_session_id=model.imported_session_id,
            reasons=tuple(model.reasons or ()),
            client_id=model.client_id,
            attendance=SessionAttendance(model.attendance) if model.attendance else None,
            member_id=model.member_id,
            service_id=model.service_id,
            session_type=SessionType(model.session_type) if model.session_type else None,
            category=SessionCategory(model.category) if model.category else None,
            clinical_outcome=(
                SessionClinicalStatus(model.clinical_outcome) if model.clinical_outcome else None
            ),
            session_status=SessionStatus(model.session_status) if model.session_status else None,
            client_type=ClientType(model.client_type) if model.client_type else None,
            rate_ugx=model.rate_ugx,
            session_number=model.session_number,
            issue_topic=decrypt(model.issue_topic, tenant_id=model.tenant_id),
            diagnosis_type_id=model.diagnosis_type_id,
            diagnosis_id=model.diagnosis_id,
            approved_by=model.approved_by,
            created_at=ensure_utc(model.created_at),
        )

    @staticmethod
    def row_to_model(entity: SessionImportRowEntity, *, file_hash: str) -> SessionImportRowModel:
        return SessionImportRowModel(
            id=entity.id.value,
            batch_id=entity.batch_id.value,
            tenant_id=entity.tenant_id.value,
            row_number=entity.row_number,
            replay_key=entity.replay_key(file_hash),
            source_record_key=entity.source_record_key,
            raw_practitioner_name=entity.raw_practitioner_name,
            session_date=entity.session_date,
            outcome=entity.outcome,
            delivery_context=entity.delivery_context,
            provider_id=entity.provider_id.value if entity.provider_id else None,
            provider_affiliation_id=entity.provider_affiliation_id.value
            if entity.provider_affiliation_id
            else None,
            imported_session_id=entity.imported_session_id,
            reasons=list(entity.reasons) or None,
            client_id=entity.client_id,
            attendance=entity.attendance.value if entity.attendance else None,
            member_id=entity.member_id,
            service_id=entity.service_id,
            session_type=entity.session_type.value if entity.session_type else None,
            category=entity.category.value if entity.category else None,
            clinical_outcome=entity.clinical_outcome.value if entity.clinical_outcome else None,
            session_status=entity.session_status.value if entity.session_status else None,
            client_type=entity.client_type.value if entity.client_type else None,
            rate_ugx=entity.rate_ugx,
            session_number=entity.session_number,
            issue_topic=encrypt(entity.issue_topic, tenant_id=entity.tenant_id.value),
            diagnosis_type_id=entity.diagnosis_type_id,
            diagnosis_id=entity.diagnosis_id,
            approved_by=entity.approved_by,
            created_at=entity.created_at,
        )
