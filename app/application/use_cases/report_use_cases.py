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
from app.domain.enums import ReportQueryType, ReportRunStatus
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


RENEWAL_PACK_CODE = "renewal_pack_v1"


def build_renewal_pack_sections(
    *, client_id: str | None = None
) -> list[TemplateSection]:
    """Canonical 4-section renewal pack (Phase 3 #D-Reports v1 / SAD §15).

    Each section names the concrete query the runner executes; the optional
    ``client_id`` parameter scopes utilisation, callback outcomes, and survey
    responses to a single client. Sessions-by-month stays tenant-wide for v1.
    """
    callback_params: dict[str, Any] = {}
    utilisation_params: dict[str, Any] = {}
    satisfaction_params: dict[str, Any] = {}
    if client_id:
        callback_params["client_id"] = client_id
        utilisation_params["client_id"] = client_id
        satisfaction_params["client_id"] = client_id
    return [
        TemplateSection(
            title="Sessions delivered per month",
            query_type=ReportQueryType.SESSIONS_BY_MONTH,
            parameters={},
            narrative=(
                "Counselling delivery cadence: completed sessions per "
                "calendar month within the renewal window."
            ),
        ),
        TemplateSection(
            title="Diagnosis prevalence",
            query_type=ReportQueryType.DIAGNOSIS_PREVALENCE,
            parameters={},
            narrative=(
                "Distribution of presenting concerns across the period. "
                "Underlying source data lands with the session/diagnosis "
                "association in a follow-up phase."
            ),
        ),
        TemplateSection(
            title="Care callback outcomes",
            query_type=ReportQueryType.CARE_CALLBACK_OUTCOMES,
            parameters=callback_params,
            narrative=(
                "Outreach status mix across the wave plus the count of "
                "counsellor-detected crisis flags."
            ),
        ),
        TemplateSection(
            title="Satisfaction distribution",
            query_type=ReportQueryType.SATISFACTION_DISTRIBUTION,
            parameters=satisfaction_params,
            narrative=(
                "Per-question response frequencies from the satisfaction "
                "survey waves; aggregate-only — no individual answers."
            ),
        ),
        TemplateSection(
            title="Contract utilisation",
            query_type=ReportQueryType.CONTRACT_UTILISATION,
            parameters=utilisation_params,
            narrative=(
                "Total billable units logged per contract for the period — "
                "renewal-conversation input for retainer / FFS sizing."
            ),
        ),
    ]


class CreateRenewalPackTemplateUseCase:
    """One-shot seeder that materialises the canonical v1 renewal pack template.

    Idempotent: if a template with the v1 code already exists for the tenant, the
    existing row is returned untouched. Use distinct ``client_id`` values to keep
    per-client variants (each gets its own ``code`` suffix); pass ``None`` for the
    tenant-wide default.
    """

    def __init__(self, repository: ReportTemplateRepository):
        self._repo = repository

    async def execute(
        self,
        *,
        tenant_id: TenantId,
        client_id: str | None = None,
        name: str | None = None,
    ) -> ReportTemplate:
        suffix = f":{client_id}" if client_id else ""
        code = f"{RENEWAL_PACK_CODE}{suffix}"
        existing = await self._repo.get_by_code(tenant_id, code)
        if existing is not None:
            return existing
        now = utc_now()
        template = ReportTemplate(
            id=ReportTemplateId(generate_cuid()),
            tenant_id=tenant_id,
            code=code,
            name=name or f"Renewal pack v1{(' for ' + client_id) if client_id else ''}",
            description=(
                "Per-client renewal-pack v1: sessions, diagnoses (placeholder), "
                "care-callback outcomes, satisfaction, contract utilisation."
            ),
            sections=build_renewal_pack_sections(client_id=client_id),
            is_active=True,
            created_at=now,
            updated_at=now,
        )
        await self._repo.save(template)
        return template


def _isoformat(value: datetime) -> str:
    return value.isoformat()
