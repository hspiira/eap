"""
Audit API Routes

FastAPI routes for Audit operations.

Note: Audit logs are immutable - only read operations via API.
Write operations (logging) are handled by use cases called from middleware/decorators.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.dependencies import get_audit_repository
from app.api.schemas.audit_schemas import (
    AuditLogListResponse,
    AuditLogResponse,
    EntityChangeListResponse,
    EntityChangeResponse,
    FieldChangeSchema,
)
from app.application.use_cases.audit_use_cases import GetAuditLogUseCase
from app.domain.enums import AuditActionType
from app.domain.entities.audit import AuditLog, EntityChange
from app.domain.repositories.audit_repository import AuditRepository
from app.domain.value_objects.core import AuditLogId, TenantId, UserId

router = APIRouter(prefix="/audit", tags=["audit"])


def _to_audit_log_response(audit_log: AuditLog) -> AuditLogResponse:
    """Map AuditLog entity to API response."""
    return AuditLogResponse(
        id=audit_log._id.value,
        tenant_id=audit_log._tenant_id.value,
        user_id=audit_log._user_id.value if audit_log._user_id else None,
        action_type=audit_log._action_type,
        resource_type=audit_log._resource_type,
        resource_id=audit_log._resource_id,
        description=audit_log._description,
        ip_address=audit_log._ip_address,
        user_agent=audit_log._user_agent,
        occurred_at=audit_log._occurred_at,
        metadata=audit_log._metadata,
    )


def _to_entity_change_response(
    entity_change: EntityChange,
) -> EntityChangeResponse:
    """Map EntityChange entity to API response."""
    return EntityChangeResponse(
        id=entity_change._id.value,
        audit_log_id=entity_change._audit_log_id.value,
        entity_type=entity_change._entity_type,
        entity_id=entity_change._entity_id,
        field_changes=[
            FieldChangeSchema(
                field_name=fc.field_name,
                old_value=fc.old_value,
                new_value=fc.new_value,
            )
            for fc in entity_change._field_changes
        ],
    )


# ==================== QUERIES (Read-Only) ====================


@router.get(
    "/logs",
    response_model=AuditLogListResponse,
    summary="List audit logs with filtering and pagination",
)
async def list_audit_logs(
    tenant_id: str = Query(..., description="Tenant identifier"),
    user_id: str | None = Query(None, description="Filter by user identifier"),
    action_type: AuditActionType | None = Query(None, description="Filter by action type"),
    resource_type: str | None = Query(None, description="Filter by resource type"),
    resource_id: str | None = Query(None, description="Filter by resource identifier"),
    start_date: str | None = Query(None, description="Filter by start date (ISO format)"),
    end_date: str | None = Query(None, description="Filter by end date (ISO format)"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    sort_by: str = Query("occurred_at", description="Field to sort by"),
    sort_desc: bool = Query(True, description="Sort in descending order"),
    audit_repo: AuditRepository = Depends(get_audit_repository),
):
    """
    List audit logs with filtering, searching, and pagination.

    This is a QUERY operation - audit logs are immutable.
    """
    offset = (page - 1) * limit

    audit_logs = await audit_repo.list_audit_logs(
        tenant_id=TenantId(tenant_id),
        user_id=UserId(user_id) if user_id else None,
        action_type=action_type,
        resource_type=resource_type,
        resource_id=resource_id,
        start_date=start_date,
        end_date=end_date,
        limit=limit,
        offset=offset,
        sort_by=sort_by,
        sort_desc=sort_desc,
    )

    total = await audit_repo.count_audit_logs(
        tenant_id=TenantId(tenant_id),
        user_id=UserId(user_id) if user_id else None,
        action_type=action_type,
        resource_type=resource_type,
        resource_id=resource_id,
        start_date=start_date,
        end_date=end_date,
    )

    audit_log_responses = [
        _to_audit_log_response(audit_log) for audit_log in audit_logs
    ]

    return AuditLogListResponse(
        items=audit_log_responses,
        total=total,
        page=page,
        limit=limit,
        has_more=(offset + limit) < total,
    )


@router.get(
    "/logs/{audit_log_id}",
    response_model=AuditLogResponse,
    summary="Get audit log by ID",
)
async def get_audit_log(
    audit_log_id: str,
    audit_repo: AuditRepository = Depends(get_audit_repository),
):
    """
    Get audit log by ID.

    This is a QUERY operation - audit logs are immutable.
    """
    get_use_case = GetAuditLogUseCase(audit_repo)

    audit_log = await get_use_case.execute(AuditLogId(audit_log_id))

    if not audit_log:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Audit log not found"
        )

    return _to_audit_log_response(audit_log)


@router.get(
    "/logs/{audit_log_id}/changes",
    response_model=list[EntityChangeResponse],
    summary="Get entity changes for an audit log",
)
async def get_audit_log_changes(
    audit_log_id: str,
    audit_repo: AuditRepository = Depends(get_audit_repository),
):
    """
    Get all entity changes associated with an audit log.

    This is a QUERY operation - entity changes are immutable.
    """
    get_use_case = GetAuditLogUseCase(audit_repo)

    entity_changes = await get_use_case.execute_entity_changes(
        AuditLogId(audit_log_id)
    )

    return [_to_entity_change_response(ec) for ec in entity_changes]


@router.get(
    "/entity/{entity_type}/{entity_id}/changes",
    response_model=EntityChangeListResponse,
    summary="Get change history for a specific entity",
)
async def get_entity_changes(
    entity_type: str,
    entity_id: str,
    tenant_id: str = Query(..., description="Tenant identifier"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    audit_repo: AuditRepository = Depends(get_audit_repository),
):
    """
    Get change history for a specific entity.

    This is a QUERY operation - entity changes are immutable.
    """
    offset = (page - 1) * limit

    get_use_case = GetAuditLogUseCase(audit_repo)

    entity_changes = await get_use_case.execute_entity_history(
        TenantId(tenant_id), entity_type, entity_id, limit, offset
    )

    # Get total count (simplified - in production might want separate count method)
    total = len(entity_changes)  # This is approximate for pagination

    entity_change_responses = [
        _to_entity_change_response(ec) for ec in entity_changes
    ]

    return EntityChangeListResponse(
        items=entity_change_responses,
        total=total,
        page=page,
        limit=limit,
        has_more=(offset + limit) < total,
    )
