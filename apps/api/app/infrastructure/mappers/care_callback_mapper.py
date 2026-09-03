"""Care Callback campaign + outreach mapper (Phase 3 #D-CareCallback)."""

from app.domain.entities.care_callback_campaign import CareCallbackCampaign
from app.domain.entities.outreach_record import OutreachRecord
from app.domain.enums import (
    CareCallbackCampaignStatus,
    OutreachStatus,
    TriageRiskLevel,
)
from app.domain.value_objects.core import (
    CareCallbackCampaignId,
    ClientId,
    OutreachRecordId,
    PersonId,
    TenantId,
    UserId,
)
from app.infrastructure.models.care_callback_model import (
    CareCallbackCampaignModel,
    OutreachRecordModel,
)
from app.shared.utils.datetime import ensure_utc


class CareCallbackCampaignMapper:
    @staticmethod
    def to_entity(model: CareCallbackCampaignModel) -> CareCallbackCampaign:
        entity = CareCallbackCampaign(
            id=CareCallbackCampaignId(model.id),
            tenant_id=TenantId(model.tenant_id),
            client_id=ClientId(model.client_id),
            name=model.name,
            period_start=model.period_start,
            period_end=model.period_end,
            target_count=model.target_count,
            counsellor_pool=tuple(PersonId(pid) for pid in (model.counsellor_pool or [])),
            status=CareCallbackCampaignStatus(model.status),
            sampling_notes=model.sampling_notes,
            created_by=UserId(model.created_by),
            activated_at=ensure_utc(model.activated_at) if model.activated_at else None,
            completed_at=ensure_utc(model.completed_at) if model.completed_at else None,
            completed_count=model.completed_count,
            created_at=ensure_utc(model.created_at),
            updated_at=ensure_utc(model.updated_at),
        )
        entity.events.clear()
        return entity

    @staticmethod
    def to_model(entity: CareCallbackCampaign) -> CareCallbackCampaignModel:
        return CareCallbackCampaignModel(
            id=entity.id.value,
            tenant_id=entity.tenant_id.value,
            client_id=entity.client_id.value,
            name=entity.name,
            period_start=entity.period_start,
            period_end=entity.period_end,
            target_count=entity.target_count,
            completed_count=entity.completed_count,
            counsellor_pool=[pid.value for pid in entity.counsellor_pool],
            status=entity.status,
            sampling_notes=entity.sampling_notes,
            created_by=entity.created_by.value,
            activated_at=ensure_utc(entity.activated_at) if entity.activated_at else None,
            completed_at=ensure_utc(entity.completed_at) if entity.completed_at else None,
            created_at=ensure_utc(entity.created_at),
            updated_at=ensure_utc(entity.updated_at),
        )


class OutreachRecordMapper:
    @staticmethod
    def to_entity(model: OutreachRecordModel) -> OutreachRecord:
        risk = TriageRiskLevel(model.triage_risk_level) if model.triage_risk_level else None
        entity = OutreachRecord(
            id=OutreachRecordId(model.id),
            tenant_id=TenantId(model.tenant_id),
            campaign_id=CareCallbackCampaignId(model.campaign_id),
            person_id=PersonId(model.person_id),
            counsellor_id=PersonId(model.counsellor_id) if model.counsellor_id else None,
            status=OutreachStatus(model.status),
            contact_attempts=model.contact_attempts,
            assigned_at=ensure_utc(model.assigned_at) if model.assigned_at else None,
            last_attempted_at=ensure_utc(model.last_attempted_at)
            if model.last_attempted_at
            else None,
            completed_at=ensure_utc(model.completed_at) if model.completed_at else None,
            triage_instrument_code=model.triage_instrument_code,
            triage_responses=model.triage_responses,
            triage_scores=model.triage_scores,
            triage_risk_level=risk,
            crisis_flag=model.crisis_flag,
            notes=model.notes,
            created_at=ensure_utc(model.created_at),
            updated_at=ensure_utc(model.updated_at),
        )
        entity.events.clear()
        return entity

    @staticmethod
    def to_model(entity: OutreachRecord) -> OutreachRecordModel:
        return OutreachRecordModel(
            id=entity.id.value,
            tenant_id=entity.tenant_id.value,
            campaign_id=entity.campaign_id.value,
            person_id=entity.person_id.value,
            counsellor_id=entity.counsellor_id.value if entity.counsellor_id else None,
            status=entity.status,
            contact_attempts=entity.contact_attempts,
            assigned_at=ensure_utc(entity.assigned_at) if entity.assigned_at else None,
            last_attempted_at=ensure_utc(entity.last_attempted_at)
            if entity.last_attempted_at
            else None,
            completed_at=ensure_utc(entity.completed_at) if entity.completed_at else None,
            triage_instrument_code=entity.triage_instrument_code,
            triage_responses=entity.triage_responses,
            triage_scores=entity.triage_scores,
            triage_risk_level=entity.triage_risk_level,
            crisis_flag=entity.crisis_flag,
            notes=entity.notes,
            created_at=ensure_utc(entity.created_at),
            updated_at=ensure_utc(entity.updated_at),
        )
