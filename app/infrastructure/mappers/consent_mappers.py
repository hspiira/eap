"""Consent + DataSharingRegister + DPOContact mappers."""

from app.domain.entities.consent import Consent
from app.domain.entities.data_sharing_register import DataSharingRegisterEntry
from app.domain.entities.dpo_contact import DPOContact
from app.domain.enums import (
    ConsentPurpose,
    ConsentScope,
    ConsentStatus,
)
from app.domain.value_objects.core import (
    CaseId,
    ClinicalSubjectId,
    ConsentId,
    DataSharingRegisterEntryId,
    DocumentId,
    DPOContactId,
    Email,
    TenantId,
    UserId,
)
from app.infrastructure.models.consent_models import (
    ConsentModel,
    DataSharingRegisterEntryModel,
    DPOContactModel,
)
from app.shared.utils.datetime import ensure_utc


class ConsentMapper:
    @staticmethod
    def to_entity(model: ConsentModel) -> Consent:
        entity = Consent(
            id=ConsentId(model.id),
            tenant_id=TenantId(model.tenant_id),
            subject_clinical_subject_id=ClinicalSubjectId(
                model.subject_clinical_subject_id
            ),
            case_id=CaseId(model.case_id) if model.case_id else None,
            scope=ConsentScope(model.scope),
            purpose=ConsentPurpose(model.purpose),
            purpose_other_detail=model.purpose_other_detail,
            disclosure_to=model.disclosure_to,
            status=ConsentStatus(model.status),
            requested_at=ensure_utc(model.requested_at),
            requested_by=UserId(model.requested_by),
            expires_on=model.expires_on,
            granted_at=ensure_utc(model.granted_at)
            if model.granted_at
            else None,
            granted_by_subject_reference=model.granted_by_subject_reference,
            signed_artifact_document_id=DocumentId(
                model.signed_artifact_document_id
            )
            if model.signed_artifact_document_id
            else None,
            revoked_at=ensure_utc(model.revoked_at)
            if model.revoked_at
            else None,
            revoked_reason=model.revoked_reason,
            created_at=ensure_utc(model.created_at),
            updated_at=ensure_utc(model.updated_at),
        )
        entity.events.clear()
        return entity

    @staticmethod
    def to_model(entity: Consent) -> ConsentModel:
        return ConsentModel(
            id=entity.id.value,
            tenant_id=entity.tenant_id.value,
            subject_clinical_subject_id=entity.subject_clinical_subject_id.value,
            case_id=entity.case_id.value if entity.case_id else None,
            scope=entity.scope,
            purpose=entity.purpose,
            purpose_other_detail=entity.purpose_other_detail,
            disclosure_to=entity.disclosure_to,
            status=entity.status,
            requested_at=ensure_utc(entity.requested_at),
            requested_by=entity.requested_by.value,
            expires_on=entity.expires_on,
            granted_at=ensure_utc(entity.granted_at)
            if entity.granted_at
            else None,
            granted_by_subject_reference=entity.granted_by_subject_reference,
            signed_artifact_document_id=entity.signed_artifact_document_id.value
            if entity.signed_artifact_document_id
            else None,
            revoked_at=ensure_utc(entity.revoked_at)
            if entity.revoked_at
            else None,
            revoked_reason=entity.revoked_reason,
            created_at=ensure_utc(entity.created_at),
            updated_at=ensure_utc(entity.updated_at),
        )


class DataSharingRegisterMapper:
    @staticmethod
    def to_entity(
        model: DataSharingRegisterEntryModel,
    ) -> DataSharingRegisterEntry:
        return DataSharingRegisterEntry(
            id=DataSharingRegisterEntryId(model.id),
            tenant_id=TenantId(model.tenant_id),
            subject_clinical_subject_id=ClinicalSubjectId(
                model.subject_clinical_subject_id
            ),
            consent_id=ConsentId(model.consent_id) if model.consent_id else None,
            case_id=CaseId(model.case_id) if model.case_id else None,
            shared_with=model.shared_with,
            scope=ConsentScope(model.scope),
            summary_of_data_shared=model.summary_of_data_shared,
            legal_basis=model.legal_basis,
            shared_at=ensure_utc(model.shared_at),
            shared_by=UserId(model.shared_by),
            delivery_channel=model.delivery_channel,
            delivery_reference=model.delivery_reference,
            created_at=ensure_utc(model.created_at),
        )

    @staticmethod
    def to_model(entity: DataSharingRegisterEntry) -> DataSharingRegisterEntryModel:
        return DataSharingRegisterEntryModel(
            id=entity.id.value,
            tenant_id=entity.tenant_id.value,
            subject_clinical_subject_id=entity.subject_clinical_subject_id.value,
            consent_id=entity.consent_id.value if entity.consent_id else None,
            case_id=entity.case_id.value if entity.case_id else None,
            shared_with=entity.shared_with,
            scope=entity.scope,
            summary_of_data_shared=entity.summary_of_data_shared,
            legal_basis=entity.legal_basis,
            shared_at=ensure_utc(entity.shared_at),
            shared_by=entity.shared_by.value,
            delivery_channel=entity.delivery_channel,
            delivery_reference=entity.delivery_reference,
            created_at=ensure_utc(entity.created_at),
            updated_at=ensure_utc(entity.created_at),
        )


class DPOContactMapper:
    @staticmethod
    def to_entity(model: DPOContactModel) -> DPOContact:
        return DPOContact(
            id=DPOContactId(model.id),
            tenant_id=TenantId(model.tenant_id),
            full_name=model.full_name,
            email=Email(model.email),
            phone=model.phone,
            role_title=model.role_title,
            effective_from=model.effective_from,
            effective_until=model.effective_until,
            appointed_by=UserId(model.appointed_by)
            if model.appointed_by
            else None,
            created_at=ensure_utc(model.created_at),
            updated_at=ensure_utc(model.updated_at),
        )

    @staticmethod
    def to_model(entity: DPOContact) -> DPOContactModel:
        return DPOContactModel(
            id=entity.id.value,
            tenant_id=entity.tenant_id.value,
            full_name=entity.full_name,
            email=entity.email.value,
            phone=entity.phone,
            role_title=entity.role_title,
            effective_from=entity.effective_from,
            effective_until=entity.effective_until,
            appointed_by=entity.appointed_by.value
            if entity.appointed_by
            else None,
            created_at=ensure_utc(entity.created_at),
            updated_at=ensure_utc(entity.updated_at),
        )
