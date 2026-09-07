"""Admin-only staged historical session import.

Staging only. Applying a batch needs the historical write entry point agent 1
owns; calling the live session use case here would merge the booking rules with
historical acceptance, which decision 7 keeps apart.
"""

import hashlib

from fastapi import APIRouter, Depends, Query, Request, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_audit_event_handler
from app.api.dependencies.pagination import PageParams, pagination
from app.api.dependencies.provider_network import (
    get_historical_session_writer,
    get_provider_affiliation_repository,
    get_provider_alias_repository,
    get_session_import_repository,
)
from app.api.schemas.provider_network_schemas import (
    SessionImportApplyResponse,
    SessionImportBatchResponse,
    SessionImportRowListResponse,
    SessionImportRowPreview,
)
from app.application.services.provider_alias_reconciliation import (
    ProviderAliasReconciliationService,
)
from app.application.services.session_import_staging import (
    SessionImportStagingService,
    preflight_source_keys,
)
from app.application.use_cases.apply_session_import import ApplyImportBatchUseCase
from app.core.authorization import require_same_tenant, require_tenant_role
from app.core.database import get_db
from app.core.security import TokenData
from app.domain.entities.session_import import (
    SessionImportBatchEntity,
    SessionImportRowEntity,
)
from app.domain.enums.provider_network import ImportRowOutcome
from app.domain.enums.tenancy import TenantRole
from app.domain.exceptions import DomainError, NotFoundError
from app.domain.repositories.provider_network_repository import (
    ProviderAffiliationRepository,
    ProviderAliasRepository,
    SessionImportRepository,
)
from app.domain.value_objects.core import TenantId, UserId
from app.domain.value_objects.provider_network import (
    SessionImportBatchId,
    SessionImportRowId,
)
from app.shared.decorators import readonly, transactional
from app.shared.utils.datetime import utc_now
from app.shared.utils.generators import generate_cuid
from app.shared.utils.provider_import_source import parse_source_rows
from app.shared.utils.route_audit_helper import audit_change

router = APIRouter(prefix="/session-imports", tags=["session-imports"])

MAX_IMPORT_BYTES = 10 * 1024 * 1024


def _batch_response(
    batch: SessionImportBatchEntity, counts: dict[str, int]
) -> SessionImportBatchResponse:
    return SessionImportBatchResponse(
        id=batch.id.value,
        tenant_id=batch.tenant_id.value,
        source_system=batch.source_system,
        file_name=batch.file_name,
        file_hash=batch.file_hash,
        row_count=batch.row_count,
        source_record_key_field=batch.source_record_key_field,
        status=batch.status,
        outcome_counts=counts,
        created_at=batch.created_at,
        applied_at=batch.applied_at,
    )


@router.post(
    "",
    response_model=SessionImportBatchResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_tenant_role(TenantRole.ADMIN))],
)
@transactional()
async def stage_import(
    request: Request,
    file: UploadFile,
    tenant_id: str = Query(...),
    source_system: str = Query(..., min_length=1, max_length=100),
    source_record_key_field: str | None = Query(
        None, description="Column holding a stable source id, if the source has one"
    ),
    current_user: TokenData = Depends(require_same_tenant),
    imports: SessionImportRepository = Depends(get_session_import_repository),
    aliases: ProviderAliasRepository = Depends(get_provider_alias_repository),
    affiliations: ProviderAffiliationRepository = Depends(get_provider_affiliation_repository),
    audit_handler=Depends(get_audit_event_handler),
    db: AsyncSession = Depends(get_db),
):
    """Stage rows for review. Writes no sessions and has no billing side effects.

    Restaging the same file in one tenant is a conflict, not a second batch.
    """
    content = await file.read()
    if len(content) > MAX_IMPORT_BYTES:
        raise DomainError("Import file is larger than 10 MB", http_status=413)
    file_hash = "sha256:" + hashlib.sha256(content).hexdigest()
    tenant = TenantId(tenant_id)

    existing = await imports.find_batch_by_hash(tenant, file_hash)
    if existing is not None:
        message = f"This file was already staged as batch {existing.id.value}"
        raise DomainError(
            message,
            error_code="IMPORT_ALREADY_STAGED",
            http_status=409,
            details={"file": message},
        )

    source_rows = parse_source_rows(content, source_record_key_field)
    preflight_source_keys(source_rows, source_record_key_field)
    now = utc_now()
    batch = SessionImportBatchEntity(
        id=SessionImportBatchId(generate_cuid()),
        tenant_id=tenant,
        source_system=source_system,
        file_name=file.filename or "upload",
        file_hash=file_hash,
        row_count=len(source_rows),
        source_record_key_field=source_record_key_field,
        staged_by=UserId(current_user.user_id),
        created_at=now,
        updated_at=now,
    )
    await imports.save_batch(batch)

    service = SessionImportStagingService(
        ProviderAliasReconciliationService(aliases), affiliations, imports
    )
    entities: list[SessionImportRowEntity] = []
    for source_row in source_rows:
        staged = await service.stage_row(tenant, source_system, file_hash, source_row, now=now)
        entities.append(
            SessionImportRowEntity(
                id=SessionImportRowId(generate_cuid()),
                batch_id=batch.id,
                tenant_id=tenant,
                row_number=staged.row_number,
                source_record_key=staged.source_record_key,
                raw_practitioner_name=staged.raw_practitioner_name,
                session_date=staged.session_date,
                outcome=staged.outcome,
                delivery_context=staged.delivery_context,
                provider_id=staged.provider_id,
                provider_affiliation_id=staged.provider_affiliation_id,
                reasons=staged.reasons,
                created_at=now,
            )
        )
    await imports.add_rows(entities, file_hash=file_hash)
    await audit_change(batch, audit_handler, current_user, request)
    return _batch_response(batch, await imports.outcome_counts(tenant, batch.id))


@router.get("/{batch_id}", response_model=SessionImportBatchResponse)
@readonly()
async def get_batch(
    batch_id: str,
    tenant_id: str = Query(...),
    current_user: TokenData = Depends(require_same_tenant),
    imports: SessionImportRepository = Depends(get_session_import_repository),
):
    tenant = TenantId(tenant_id)
    batch = await imports.get_batch(tenant, SessionImportBatchId(batch_id))
    if batch is None:
        raise NotFoundError(
            "Import batch not found", resource_type="SessionImportBatch", resource_id=batch_id
        )
    return _batch_response(batch, await imports.outcome_counts(tenant, batch.id))


@router.get("/{batch_id}/rows", response_model=SessionImportRowListResponse)
@readonly()
async def list_rows(
    batch_id: str,
    tenant_id: str = Query(...),
    outcome: ImportRowOutcome | None = Query(None, description="Filter the review queue"),
    pg: PageParams = Depends(pagination(default_limit=50)),
    current_user: TokenData = Depends(require_same_tenant),
    imports: SessionImportRepository = Depends(get_session_import_repository),
):
    items, total = await imports.list_rows(
        TenantId(tenant_id),
        SessionImportBatchId(batch_id),
        outcome=outcome.value if outcome else None,
        limit=pg.limit,
        offset=pg.offset,
    )
    return SessionImportRowListResponse(
        items=[
            SessionImportRowPreview(
                row_number=row.row_number,
                outcome=row.outcome,
                delivery_context=row.delivery_context,
                provider_id=row.provider_id.value if row.provider_id else None,
                provider_affiliation_id=(
                    row.provider_affiliation_id.value if row.provider_affiliation_id else None
                ),
                raw_practitioner_name=row.raw_practitioner_name,
                session_date=row.session_date,
                reasons=list(row.reasons),
            )
            for row in items
        ],
        total=total,
        page=pg.page,
        limit=pg.limit,
        has_more=(pg.offset + len(items)) < total,
    )


@router.post(
    "/{batch_id}/apply",
    response_model=SessionImportApplyResponse,
    dependencies=[Depends(require_tenant_role(TenantRole.ADMIN))],
)
@transactional()
async def apply_batch(
    batch_id: str,
    tenant_id: str = Query(...),
    current_user: TokenData = Depends(require_same_tenant),
    imports: SessionImportRepository = Depends(get_session_import_repository),
    writer=Depends(get_historical_session_writer),
    db: AsyncSession = Depends(get_db),
):
    """Write every importable row through the historical path, then close the batch.

    Applying a second time is refused, so a replayed request cannot write
    twice. `imported` is zero today for every batch: no staged row can reach
    Accepted while member and service resolution does not exist, which the
    row outcomes state per row rather than leaving to be discovered here.
    """
    result, _ = await ApplyImportBatchUseCase(imports, writer).execute(
        TenantId(tenant_id),
        SessionImportBatchId(batch_id),
        UserId(current_user.user_id),
        now=utc_now(),
    )
    return SessionImportApplyResponse(
        batch_id=batch_id,
        imported=result.imported,
        skipped_already_imported=result.skipped_already_imported,
        not_importable=result.not_importable,
    )
