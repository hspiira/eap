"""Critical Incident routes (Phase 2 #D-CISM)."""

from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import (
    PageParams,
    get_audit_event_handler,
    get_critical_incident_repository,
    pagination,
)
from app.api.schemas.critical_incident_schemas import (
    CriticalIncidentCreate,
    CriticalIncidentListResponse,
    CriticalIncidentResponse,
    IncidentClose,
    IncidentPhaseEntryResponse,
    IncidentPhaseRecord,
)
from app.application.use_cases.critical_incident_use_cases import (
    CreateCriticalIncidentUseCase,
)
from app.application.use_cases.transitions import (
    CriticalIncidentTransition,
    TransitionUseCase,
)
from app.core.authorization import require_same_tenant
from app.core.database import get_db
from app.core.security import TokenData, get_current_user
from app.domain.entities.critical_incident import CriticalIncidentEntity
from app.domain.repositories.critical_incident_repository import (
    CriticalIncidentRepository,
)
from app.domain.value_objects.core import (
    ClientId,
    CriticalIncidentId,
    TenantId,
    UserId,
)
from app.shared.decorators import readonly, transactional
from app.shared.utils.generators import generate_cuid
from app.shared.utils.route_audit_helper import audit_change

router = APIRouter(prefix="/critical-incidents", tags=["critical-incidents"])


def _to_response(incident: CriticalIncidentEntity) -> CriticalIncidentResponse:
    return CriticalIncidentResponse(
        id=incident.id.value,
        tenant_id=incident.tenant_id.value,
        client_id=incident.client_id.value,
        event_description=incident.event_description,
        severity=incident.severity,
        affected_population_size=incident.affected_population_size,
        occurred_at=incident.occurred_at,
        logged_by=incident.logged_by.value,
        status=incident.status,
        phases=[
            IncidentPhaseEntryResponse(
                phase=p.phase, occurred_at=p.occurred_at, notes=p.notes
            )
            for p in incident.phases
        ],
        after_action_summary=incident.after_action_summary,
        closed_at=incident.closed_at,
        created_at=incident.created_at,
        updated_at=incident.updated_at,
    )


@router.post(
    "",
    response_model=CriticalIncidentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Log a new critical incident",
)
@transactional()
async def create_critical_incident(
    data: CriticalIncidentCreate,
    request: Request,
    tenant_id: str = Query(..., description="Tenant identifier"),
    current_user: TokenData = Depends(require_same_tenant),
    repo: CriticalIncidentRepository = Depends(get_critical_incident_repository),
    audit_handler=Depends(get_audit_event_handler),
    db: AsyncSession = Depends(get_db),
):
    incident = await CreateCriticalIncidentUseCase(repo).execute(
        incident_id=CriticalIncidentId(generate_cuid()),
        tenant_id=TenantId(tenant_id),
        client_id=ClientId(data.client_id),
        event_description=data.event_description,
        severity=data.severity,
        affected_population_size=data.affected_population_size,
        occurred_at=data.occurred_at,
        logged_by=UserId(current_user.user_id),
    )
    await audit_change(incident, audit_handler, current_user, request)
    return _to_response(incident)


@router.post(
    "/{incident_id}/phases",
    response_model=CriticalIncidentResponse,
    summary="Record a CISM phase on the response timeline",
)
@transactional()
async def record_phase(
    incident_id: str,
    body: IncidentPhaseRecord,
    request: Request,
    current_user: TokenData = Depends(get_current_user),
    repo: CriticalIncidentRepository = Depends(get_critical_incident_repository),
    audit_handler=Depends(get_audit_event_handler),
    db: AsyncSession = Depends(get_db),
):
    use_case = TransitionUseCase(repo, "CriticalIncident")
    incident = await use_case.execute(
        CriticalIncidentId(incident_id),
        CriticalIncidentTransition.RECORD_PHASE,
        phase=body.phase,
        notes=body.notes,
    )
    await audit_change(incident, audit_handler, current_user, request)
    return _to_response(incident)


@router.post(
    "/{incident_id}/close",
    response_model=CriticalIncidentResponse,
    summary="Close the incident response and capture the after-action summary",
)
@transactional()
async def close_incident(
    incident_id: str,
    body: IncidentClose,
    request: Request,
    current_user: TokenData = Depends(get_current_user),
    repo: CriticalIncidentRepository = Depends(get_critical_incident_repository),
    audit_handler=Depends(get_audit_event_handler),
    db: AsyncSession = Depends(get_db),
):
    use_case = TransitionUseCase(repo, "CriticalIncident")
    incident = await use_case.execute(
        CriticalIncidentId(incident_id),
        CriticalIncidentTransition.CLOSE,
        after_action_summary=body.after_action_summary,
    )
    await audit_change(incident, audit_handler, current_user, request)
    return _to_response(incident)


@router.get(
    "/{incident_id}",
    response_model=CriticalIncidentResponse,
    summary="Get a critical incident by ID",
)
@readonly()
async def get_incident(
    incident_id: str,
    _user: TokenData = Depends(get_current_user),
    repo: CriticalIncidentRepository = Depends(get_critical_incident_repository),
    db: AsyncSession = Depends(get_db),
):
    from fastapi import HTTPException

    incident = await repo.get_by_id(CriticalIncidentId(incident_id))
    if incident is None:
        raise HTTPException(status_code=404, detail="Critical incident not found")
    return _to_response(incident)


@router.get(
    "/{incident_id}/after-action",
    summary="After-action JSON for an incident",
)
@readonly()
async def after_action(
    incident_id: str,
    _user: TokenData = Depends(get_current_user),
    repo: CriticalIncidentRepository = Depends(get_critical_incident_repository),
    db: AsyncSession = Depends(get_db),
):
    from fastapi import HTTPException

    incident = await repo.get_by_id(CriticalIncidentId(incident_id))
    if incident is None:
        raise HTTPException(status_code=404, detail="Critical incident not found")
    return incident.after_action_report()


@router.get(
    "",
    response_model=CriticalIncidentListResponse,
    summary="List critical incidents for the current tenant",
)
@readonly()
async def list_incidents(
    tenant_id: str = Query(..., description="Tenant identifier"),
    pg: PageParams = Depends(pagination()),
    current_user: TokenData = Depends(require_same_tenant),
    repo: CriticalIncidentRepository = Depends(get_critical_incident_repository),
    db: AsyncSession = Depends(get_db),
):
    incidents = await repo.list_for_tenant(
        TenantId(tenant_id), limit=pg.limit, offset=pg.offset
    )
    return CriticalIncidentListResponse(
        items=[_to_response(i) for i in incidents],
        total=len(incidents),
    )
