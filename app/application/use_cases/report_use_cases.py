"""Report use cases (Phase 2 #D-Reports).

Bespoke use cases:
- ``CreateReportTemplateUseCase`` — create a template; transitions are dispatched
  through the existing ``TransitionUseCase`` once we add a ``ReportTemplateTransition``.
- ``RunReportTemplateUseCase`` — load the template, create a ``ReportRun``,
  dispatch each section through the runner, save the materialised output.
- ``GetReportRunUseCase`` / ``ListReportRunsUseCase`` — query helpers.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Protocol

from app.application.use_cases.base import BaseUseCase
from app.domain.entities.report import (
    ReportRun,
    ReportTemplate,
    TemplateSection,
)
from app.domain.enums import ReportRunStatus
from app.domain.exceptions import DomainError, NotFoundError
from app.domain.repositories.report_repository import (
    ReportRunRepository,
    ReportTemplateRepository,
)
from app.domain.value_objects.core import (
    ReportRunId,
    ReportTemplateId,
    TenantId,
    UserId,
)
from app.shared.utils.datetime import utc_now
from app.shared.utils.generators import generate_cuid


class _QueryRunnerProtocol(Protocol):
    async def run(
        self,
        section: TemplateSection,
        *,
        tenant_id: str,
        run_parameters: dict[str, Any],
    ) -> dict[str, Any]:
        ...


class CreateReportTemplateUseCase(BaseUseCase[ReportTemplate, ReportTemplateId]):
    def __init__(self, repository: ReportTemplateRepository):
        super().__init__(repository)
        self._repo = repository

    async def execute(
        self,
        *,
        template_id: ReportTemplateId,
        tenant_id: TenantId,
        code: str,
        name: str,
        sections: list[TemplateSection],
        description: str | None = None,
    ) -> ReportTemplate:
        existing = await self._repo.get_by_code(tenant_id, code)
        if existing is not None:
            raise DomainError(f"Report template with code '{code}' already exists")
        now = utc_now()
        template = ReportTemplate(
            id=template_id,
            tenant_id=tenant_id,
            code=code,
            name=name,
            description=description,
            sections=sections,
            is_active=True,
            created_at=now,
            updated_at=now,
        )
        await self._repo.save(template)
        return template


class RunReportTemplateUseCase:
    """Execute a template synchronously and persist the materialised output."""

    def __init__(
        self,
        template_repository: ReportTemplateRepository,
        run_repository: ReportRunRepository,
        query_runner: _QueryRunnerProtocol,
    ):
        self._templates = template_repository
        self._runs = run_repository
        self._runner = query_runner

    async def execute(
        self,
        *,
        template_id: ReportTemplateId,
        tenant_id: TenantId,
        requested_by: UserId,
        parameters: dict[str, Any] | None = None,
    ) -> ReportRun:
        template = await self._templates.get_by_id(template_id)
        if template is None:
            raise NotFoundError(
                f"Report template not found: {template_id.value}",
                resource_type="ReportTemplate",
                resource_id=template_id.value,
            )
        if template.tenant_id != tenant_id:
            raise NotFoundError(
                f"Report template not found: {template_id.value}",
                resource_type="ReportTemplate",
                resource_id=template_id.value,
            )
        if not template.is_active:
            raise DomainError("Cannot run an inactive template")

        now = utc_now()
        run = ReportRun(
            id=ReportRunId(generate_cuid()),
            tenant_id=tenant_id,
            template_id=template_id,
            requested_by=requested_by,
            parameters=parameters or {},
            status=ReportRunStatus.PENDING,
            created_at=now,
            updated_at=now,
        )
        await self._runs.save(run)

        run.mark_running()
        await self._runs.save(run)

        try:
            sections_output: list[dict[str, Any]] = []
            for section in template.sections:
                section_result = await self._runner.run(
                    section,
                    tenant_id=tenant_id.value,
                    run_parameters=run.parameters,
                )
                sections_output.append(
                    {
                        "title": section.title,
                        "narrative": section.narrative,
                        "result": section_result,
                    }
                )
            run.mark_completed(
                {
                    "template_code": template.code,
                    "template_name": template.name,
                    "generated_at": _isoformat(utc_now()),
                    "sections": sections_output,
                }
            )
        except Exception as exc:
            run.mark_failed(str(exc))
            await self._runs.save(run)
            raise

        await self._runs.save(run)
        return run


class GetReportRunUseCase:
    def __init__(self, repository: ReportRunRepository):
        self._repo = repository

    async def execute(self, run_id: ReportRunId) -> ReportRun | None:
        return await self._repo.get_by_id(run_id)


def _isoformat(value: datetime) -> str:
    return value.isoformat()
