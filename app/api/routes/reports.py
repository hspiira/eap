"""Report routes (Phase 2 #D-Reports)."""

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import (
    get_audit_event_handler,
    get_report_query_runner,
    get_report_run_repository,
    get_report_template_repository,
)
from app.api.schemas.report_schemas import (
    ReportRunRequest,
    ReportRunResponse,
    ReportTemplateCreate,
    ReportTemplateResponse,
    TemplateSectionInput,
)
from app.application.use_cases.report_use_cases import (
    CreateRenewalPackTemplateUseCase,
    CreateReportTemplateUseCase,
    GetReportRunUseCase,
    RunReportTemplateUseCase,
)
from app.core.authorization import require_same_tenant
from app.core.database import get_db
from app.core.security import TokenData
from app.domain.entities.report import (
    ReportRun,
    ReportTemplate,
    TemplateSection,
)
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
from app.shared.decorators import readonly, transactional
from app.shared.utils.generators import generate_cuid
from app.shared.utils.route_audit_helper import audit_change

router = APIRouter(prefix="/reports", tags=["reports"])


def _to_template_response(t: ReportTemplate) -> ReportTemplateResponse:
    return ReportTemplateResponse(
        id=t.id.value,
        tenant_id=t.tenant_id.value,
        code=t.code,
        name=t.name,
        description=t.description,
        sections=[
            TemplateSectionInput(
                title=s.title,
                query_type=s.query_type,
                parameters=s.parameters,
                narrative=s.narrative,
            )
            for s in t.sections
        ],
        is_active=t.is_active,
        created_at=t.created_at,
        updated_at=t.updated_at,
    )


def _to_run_response(r: ReportRun) -> ReportRunResponse:
    return ReportRunResponse(
        id=r.id.value,
        tenant_id=r.tenant_id.value,
        template_id=r.template_id.value,
        requested_by=r.requested_by.value,
        parameters=r.parameters,
        status=r.status,
        started_at=r.started_at,
        completed_at=r.completed_at,
        output=r.output,
        error=r.error,
        created_at=r.created_at,
        updated_at=r.updated_at,
    )


@router.post(
    "/templates/renewal-pack",
    response_model=ReportTemplateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Materialise the v1 renewal-pack template (idempotent)",
)
@transactional()
async def create_renewal_pack_template(
    request: Request,
    tenant_id: str = Query(..., description="Tenant identifier"),
    client_id: str | None = Query(
        default=None,
        description="Optional client scope; omit for tenant-wide variant",
    ),
    current_user: TokenData = Depends(require_same_tenant),
    repo: ReportTemplateRepository = Depends(get_report_template_repository),
    audit_handler=Depends(get_audit_event_handler),
    db: AsyncSession = Depends(get_db),
):
    template = await CreateRenewalPackTemplateUseCase(repo).execute(
        tenant_id=TenantId(tenant_id),
        client_id=client_id,
    )
    await audit_change(template, audit_handler, current_user, request)
    return _to_template_response(template)


@router.post(
    "/templates",
    response_model=ReportTemplateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new report template",
)
@transactional()
async def create_template(
    data: ReportTemplateCreate,
    request: Request,
    tenant_id: str = Query(..., description="Tenant identifier"),
    current_user: TokenData = Depends(require_same_tenant),
    repo: ReportTemplateRepository = Depends(get_report_template_repository),
    audit_handler=Depends(get_audit_event_handler),
    db: AsyncSession = Depends(get_db),
):
    template = await CreateReportTemplateUseCase(repo).execute(
        template_id=ReportTemplateId(generate_cuid()),
        tenant_id=TenantId(tenant_id),
        code=data.code,
        name=data.name,
        description=data.description,
        sections=[
            TemplateSection(
                title=s.title,
                query_type=s.query_type,
                parameters=s.parameters,
                narrative=s.narrative,
            )
            for s in data.sections
        ],
    )
    await audit_change(template, audit_handler, current_user, request)
    return _to_template_response(template)


@router.get(
    "/templates",
    response_model=list[ReportTemplateResponse],
    summary="List report templates",
)
@readonly()
async def list_templates(
    tenant_id: str = Query(..., description="Tenant identifier"),
    active_only: bool = Query(True),
    current_user: TokenData = Depends(require_same_tenant),
    repo: ReportTemplateRepository = Depends(get_report_template_repository),
    db: AsyncSession = Depends(get_db),
):
    templates = await repo.list_for_tenant(TenantId(tenant_id), active_only=active_only)
    return [_to_template_response(t) for t in templates]


@router.get(
    "/templates/{template_id}",
    response_model=ReportTemplateResponse,
    summary="Get a report template by ID",
)
@readonly()
async def get_template(
    template_id: str,
    repo: ReportTemplateRepository = Depends(get_report_template_repository),
    db: AsyncSession = Depends(get_db),
):
    template = await repo.get_by_id(ReportTemplateId(template_id))
    if template is None:
        raise HTTPException(status_code=404, detail="Report template not found")
    return _to_template_response(template)


@router.post(
    "/templates/{template_id}/run",
    response_model=ReportRunResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Run a report template synchronously and persist the output",
)
@transactional()
async def run_template(
    template_id: str,
    body: ReportRunRequest,
    request: Request,
    tenant_id: str = Query(..., description="Tenant identifier"),
    current_user: TokenData = Depends(require_same_tenant),
    template_repo: ReportTemplateRepository = Depends(get_report_template_repository),
    run_repo: ReportRunRepository = Depends(get_report_run_repository),
    runner=Depends(get_report_query_runner),
    audit_handler=Depends(get_audit_event_handler),
    db: AsyncSession = Depends(get_db),
):
    use_case = RunReportTemplateUseCase(template_repo, run_repo, runner)
    run = await use_case.execute(
        template_id=ReportTemplateId(template_id),
        tenant_id=TenantId(tenant_id),
        requested_by=UserId(current_user.user_id),
        parameters=body.parameters,
    )
    await audit_change(run, audit_handler, current_user, request)
    return _to_run_response(run)


@router.get(
    "/runs/{run_id}",
    response_model=ReportRunResponse,
    summary="Get a single report run (with materialised output)",
)
@readonly()
async def get_run(
    run_id: str,
    repo: ReportRunRepository = Depends(get_report_run_repository),
    db: AsyncSession = Depends(get_db),
):
    run = await GetReportRunUseCase(repo).execute(ReportRunId(run_id))
    if run is None:
        raise HTTPException(status_code=404, detail="Report run not found")
    return _to_run_response(run)
