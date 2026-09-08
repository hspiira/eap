"""EAP programme + Authorization mappers."""

from app.domain.entities.authorization import Authorization
from app.domain.entities.eap_programme import EAPProgramme
from app.domain.enums import (
    AuthorizationStatus,
    RelationType,
)
from app.domain.value_objects.core import (
    AuthorizationId,
    CaseId,
    ClinicalSubjectId,
    ContractId,
    EAPProgrammeId,
    TenantId,
    UserId,
)
from app.domain.value_objects.programme import ProgrammeSessionCap
from app.infrastructure.models.eap_programme_model import (
    AuthorizationModel,
    EAPProgrammeModel,
)
from app.shared.utils.datetime import ensure_utc


def _cap_from_dict(raw: dict) -> ProgrammeSessionCap:
    return ProgrammeSessionCap(
        service_category=raw["service_category"],
        per_issue_per_year=int(raw["per_issue_per_year"]),
        per_year=raw.get("per_year"),
        per_household_per_year=raw.get("per_household_per_year"),
    )


class EAPProgrammeMapper:
    @staticmethod
    def to_entity(model: EAPProgrammeModel) -> EAPProgramme:
        entity = EAPProgramme(
            id=EAPProgrammeId(model.id),
            tenant_id=TenantId(model.tenant_id),
            contract_id=ContractId(model.contract_id),
            name=model.name,
            effective_from=model.effective_from,
            effective_until=model.effective_until,
            geographic_scope=model.geographic_scope,
            description=model.description,
            caps=tuple(_cap_from_dict(c) for c in (model.caps or [])),
            eligible_dependent_relations=tuple(
                RelationType(r) for r in (model.eligible_dependent_relations or [])
            ),
            is_active=model.is_active,
            created_by=UserId(model.created_by) if model.created_by else None,
            created_at=ensure_utc(model.created_at),
            updated_at=ensure_utc(model.updated_at),
        )
        entity.events.clear()
        return entity

    @staticmethod
    def to_model(entity: EAPProgramme) -> EAPProgrammeModel:
        return EAPProgrammeModel(
            id=entity.id.value,
            tenant_id=entity.tenant_id.value,
            contract_id=entity.contract_id.value,
            name=entity.name,
            effective_from=entity.effective_from,
            effective_until=entity.effective_until,
            geographic_scope=entity.geographic_scope,
            description=entity.description,
            caps=[c.as_dict() for c in entity.caps],
            eligible_dependent_relations=[r.value for r in entity.eligible_dependent_relations],
            is_active=entity.is_active,
            created_by=entity.created_by.value if entity.created_by else None,
            created_at=ensure_utc(entity.created_at),
            updated_at=ensure_utc(entity.updated_at),
        )


class AuthorizationMapper:
    @staticmethod
    def to_entity(model: AuthorizationModel) -> Authorization:
        entity = Authorization(
            id=AuthorizationId(model.id),
            tenant_id=TenantId(model.tenant_id),
            case_id=CaseId(model.case_id),
            clinical_subject_id=ClinicalSubjectId(model.clinical_subject_id),
            programme_id=EAPProgrammeId(model.programme_id),
            service_category=model.service_category,
            sessions_granted=model.sessions_granted,
            sessions_used=model.sessions_used,
            status=AuthorizationStatus(model.status),
            granted_at=ensure_utc(model.granted_at),
            expires_on=model.expires_on,
            extension_requested_sessions=model.extension_requested_sessions,
            extension_requested_by=UserId(model.extension_requested_by)
            if model.extension_requested_by
            else None,
            extension_requested_at=ensure_utc(model.extension_requested_at)
            if model.extension_requested_at
            else None,
            extension_clinician_signoff=UserId(model.extension_clinician_signoff)
            if model.extension_clinician_signoff
            else None,
            extension_admin_signoff=UserId(model.extension_admin_signoff)
            if model.extension_admin_signoff
            else None,
            extended_at=ensure_utc(model.extended_at) if model.extended_at else None,
            closed_at=ensure_utc(model.closed_at) if model.closed_at else None,
            created_at=ensure_utc(model.created_at),
            updated_at=ensure_utc(model.updated_at),
        )
        entity.events.clear()
        return entity

    @staticmethod
    def to_model(entity: Authorization) -> AuthorizationModel:
        return AuthorizationModel(
            id=entity.id.value,
            tenant_id=entity.tenant_id.value,
            case_id=entity.case_id.value,
            clinical_subject_id=entity.clinical_subject_id.value,
            programme_id=entity.programme_id.value,
            service_category=entity.service_category,
            sessions_granted=entity.sessions_granted,
            sessions_used=entity.sessions_used,
            status=entity.status,
            granted_at=ensure_utc(entity.granted_at),
            expires_on=entity.expires_on,
            extension_requested_sessions=entity.extension_requested_sessions,
            extension_requested_by=entity.extension_requested_by.value
            if entity.extension_requested_by
            else None,
            extension_requested_at=ensure_utc(entity.extension_requested_at)
            if entity.extension_requested_at
            else None,
            extension_clinician_signoff=entity.extension_clinician_signoff.value
            if entity.extension_clinician_signoff
            else None,
            extension_admin_signoff=entity.extension_admin_signoff.value
            if entity.extension_admin_signoff
            else None,
            extended_at=ensure_utc(entity.extended_at) if entity.extended_at else None,
            closed_at=ensure_utc(entity.closed_at) if entity.closed_at else None,
            created_at=ensure_utc(entity.created_at),
            updated_at=ensure_utc(entity.updated_at),
        )
