"""Survey campaign + response mapper (Phase 3 #D-Survey)."""

from typing import Any

from app.domain.entities.survey_campaign import ApprovedQuestion, SurveyCampaign
from app.domain.entities.survey_response import SurveyResponse
from app.domain.enums import SurveyCampaignStatus
from app.domain.value_objects.core import (
    ClientId,
    SurveyCampaignId,
    SurveyResponseId,
    TenantId,
    UserId,
)
from app.infrastructure.models.survey_model import (
    SurveyCampaignModel,
    SurveyResponseModel,
)
from app.shared.utils.datetime import ensure_utc


def approved_questions_from_json(rows: list[dict[str, Any]] | None) -> list[ApprovedQuestion]:
    return [
        ApprovedQuestion(
            key=row["key"],
            label=row["label"],
            choices=tuple(row["choices"]),
        )
        for row in rows or []
    ]


def approved_questions_to_json(questions: list[ApprovedQuestion]) -> list[dict[str, Any]]:
    return [{"key": q.key, "label": q.label, "choices": list(q.choices)} for q in questions]


class SurveyCampaignMapper:
    @staticmethod
    def to_entity(model: SurveyCampaignModel) -> SurveyCampaign:
        entity = SurveyCampaign(
            id=SurveyCampaignId(model.id),
            tenant_id=TenantId(model.tenant_id),
            client_id=ClientId(model.client_id),
            name=model.name,
            source=model.source,
            external_form_id=model.external_form_id,
            webhook_secret=model.webhook_secret,
            status=SurveyCampaignStatus(model.status),
            period_start=model.period_start,
            period_end=model.period_end,
            anonymous=model.anonymous,
            approved_questions=approved_questions_from_json(model.approved_questions),
            response_count=model.response_count,
            created_by=UserId(model.created_by),
            activated_at=ensure_utc(model.activated_at) if model.activated_at else None,
            closed_at=ensure_utc(model.closed_at) if model.closed_at else None,
            created_at=ensure_utc(model.created_at),
            updated_at=ensure_utc(model.updated_at),
        )
        entity.events.clear()
        return entity

    @staticmethod
    def to_model(entity: SurveyCampaign) -> SurveyCampaignModel:
        return SurveyCampaignModel(
            id=entity.id.value,
            tenant_id=entity.tenant_id.value,
            client_id=entity.client_id.value,
            name=entity.name,
            source=entity.source,
            external_form_id=entity.external_form_id,
            webhook_secret=entity.webhook_secret,
            status=entity.status,
            period_start=entity.period_start,
            period_end=entity.period_end,
            anonymous=entity.anonymous,
            approved_questions=approved_questions_to_json(entity.approved_questions),
            response_count=entity.response_count,
            created_by=entity.created_by.value,
            activated_at=ensure_utc(entity.activated_at) if entity.activated_at else None,
            closed_at=ensure_utc(entity.closed_at) if entity.closed_at else None,
            created_at=ensure_utc(entity.created_at),
            updated_at=ensure_utc(entity.updated_at),
        )


class SurveyResponseMapper:
    @staticmethod
    def to_entity(model: SurveyResponseModel) -> SurveyResponse:
        entity = SurveyResponse(
            id=SurveyResponseId(model.id),
            tenant_id=TenantId(model.tenant_id),
            campaign_id=SurveyCampaignId(model.campaign_id),
            external_response_id=model.external_response_id,
            submitted_at=ensure_utc(model.submitted_at),
            received_at=ensure_utc(model.received_at),
            payload=model.payload,
            metrics=model.metrics,
        )
        entity.events.clear()
        return entity

    @staticmethod
    def to_model(entity: SurveyResponse) -> SurveyResponseModel:
        return SurveyResponseModel(
            id=entity.id.value,
            tenant_id=entity.tenant_id.value,
            campaign_id=entity.campaign_id.value,
            external_response_id=entity.external_response_id,
            submitted_at=ensure_utc(entity.submitted_at),
            received_at=ensure_utc(entity.received_at),
            payload=entity.payload,
            metrics=entity.metrics,
        )
