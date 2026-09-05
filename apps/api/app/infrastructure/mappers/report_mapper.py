"""Report template + run mapper (Phase 2 #D-Reports)."""

from app.domain.entities.report import (
    ReportRun,
    ReportTemplate,
    TemplateSection,
)
from app.domain.enums import ReportQueryType, ReportRunStatus
from app.domain.value_objects.core import (
    ReportRunId,
    ReportTemplateId,
    TenantId,
    UserId,
)
from app.infrastructure.models.report_model import (
    ReportRunModel,
    ReportTemplateModel,
)
from app.shared.utils.datetime import ensure_utc


class ReportTemplateMapper:
    @staticmethod
    def to_entity(model: ReportTemplateModel) -> ReportTemplate:
        sections = [
            TemplateSection(
                title=s["title"],
                query_type=ReportQueryType(s["query_type"]),
                parameters=s.get("parameters") or {},
                narrative=s.get("narrative"),
            )
            for s in (model.sections or [])
        ]
        return ReportTemplate(
            id=ReportTemplateId(model.id),
            tenant_id=TenantId(model.tenant_id),
            code=model.code,
            name=model.name,
            description=model.description,
            sections=sections,
            is_active=model.is_active,
            created_at=ensure_utc(model.created_at),
            updated_at=ensure_utc(model.updated_at),
        )

    @staticmethod
    def to_model(entity: ReportTemplate) -> ReportTemplateModel:
        return ReportTemplateModel(
            id=entity.id.value,
            tenant_id=entity.tenant_id.value,
            code=entity.code,
            name=entity.name,
            description=entity.description,
            sections=[
                {
                    "title": s.title,
                    "query_type": s.query_type.value,
                    "parameters": s.parameters,
                    "narrative": s.narrative,
                }
                for s in entity.sections
            ],
            is_active=entity.is_active,
            created_at=ensure_utc(entity.created_at),
            updated_at=ensure_utc(entity.updated_at),
        )


class ReportRunMapper:
    @staticmethod
    def to_entity(model: ReportRunModel) -> ReportRun:
        run = ReportRun(
            id=ReportRunId(model.id),
            tenant_id=TenantId(model.tenant_id),
            template_id=ReportTemplateId(model.template_id),
            requested_by=UserId(model.requested_by),
            parameters=model.parameters or {},
            status=ReportRunStatus(model.status),
            started_at=ensure_utc(model.started_at) if model.started_at else None,
            completed_at=ensure_utc(model.completed_at) if model.completed_at else None,
            output=model.output,
            error=model.error,
            created_at=ensure_utc(model.created_at),
            updated_at=ensure_utc(model.updated_at),
        )
        run.events.clear()
        return run

    @staticmethod
    def to_model(entity: ReportRun) -> ReportRunModel:
        return ReportRunModel(
            id=entity.id.value,
            tenant_id=entity.tenant_id.value,
            template_id=entity.template_id.value,
            requested_by=entity.requested_by.value,
            parameters=entity.parameters,
            status=entity.status,
            started_at=ensure_utc(entity.started_at) if entity.started_at else None,
            completed_at=ensure_utc(entity.completed_at) if entity.completed_at else None,
            output=entity.output,
            error=entity.error,
            created_at=ensure_utc(entity.created_at),
            updated_at=ensure_utc(entity.updated_at),
        )
