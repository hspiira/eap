"""Admin-only staged historical session import.

Staging only. Applying a batch needs the historical write entry point agent 1
owns; calling the live session use case here would merge the booking rules with
historical acceptance, which decision 7 keeps apart.
"""

import csv
import hashlib
import io
import logging
from collections.abc import Sequence
from datetime import datetime

from fastapi import APIRouter, Depends, Query, Request, UploadFile, status
from fastapi.responses import StreamingResponse
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import (
    get_audit_event_handler,
    get_client_repository,
    get_eligible_member_repository,
    get_service_repository,
)
from app.api.dependencies.pagination import PageParams, pagination
from app.api.dependencies.provider_network import (
    get_historical_session_writer,
    get_provider_affiliation_repository,
    get_provider_alias_repository,
    get_session_import_repository,
)
from app.api.schemas.provider_network_schemas import (
    SessionImportAbandonRequest,
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
    SourceRow,
    preflight_source_keys,
)
from app.application.use_cases.apply_session_import import ApplyImportBatchUseCase
from app.core.authorization import require_same_tenant, require_tenant_role
from app.core.database import get_db
from app.core.query_metrics import measure_queries
from app.core.security import TokenData, get_current_user
from app.domain.entities.session_import import (
    SessionImportBatchEntity,
    SessionImportRowEntity,
)
from app.domain.enums.provider_network import ImportRowOutcome
from app.domain.enums.tenancy import TenantRole
from app.domain.exceptions import DomainError, NotFoundError
from app.domain.repositories.client_repository import ClientRepository
from app.domain.repositories.eligible_member_repository import EligibleMemberRepository
from app.domain.repositories.provider_network_repository import (
    ProviderAffiliationRepository,
    ProviderAliasRepository,
    SessionImportRepository,
)
from app.domain.repositories.service_repository import ServiceRepository
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

logger = logging.getLogger(__name__)

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


async def _require_batch(
    imports: SessionImportRepository, tenant_id: str, batch_id: str
) -> SessionImportBatchEntity:
    batch = await imports.get_batch(TenantId(tenant_id), SessionImportBatchId(batch_id))
    if batch is None:
        raise NotFoundError(
            "Import batch not found", resource_type="SessionImportBatch", resource_id=batch_id
        )
    return batch


@router.get(
    "/template",
    summary="Download the session import CSV template",
)
async def session_import_template(
    current_user: TokenData = Depends(get_current_user),
) -> StreamingResponse:
    """Return the supported extract columns with one Individual and one CompanyWide example row.

    Column names match `provider_import_source.py`'s accepted spellings, using
    the same "(CLEAN)" form the reference extract itself uses for the columns
    that have one. "Client Type (Staff/Dep)" says who attended (an
    individual, or the client at large); "Client Type" is unrelated and says
    whether this is a new or repeat client engagement -- the two are easy to
    conflate and both belong in a real extract.
    """
    output = io.StringIO(newline="")
    writer = csv.writer(output)
    writer.writerow(
        [
            "Date",
            "Company (CLEAN)",
            "Client-ID#",
            "Counselor (CLEAN)",
            "Client Type (Staff/Dep)",
            "Gender",
            "Session Type",
            "Session Category",
            "Client Type",
            "Intervention",
            "Status (CLEAN)",
            "Rate (UGX)",
            "Session #",
        ]
    )
    writer.writerow(
        [
            "2026-01-15",
            "Example Client",
            "EXM-001",
            "Example Counsellor",
            "Staff",
            "Female",
            "Physical",
            "Individual",
            "New",
            "Individual Counselling",
            "Completed",
            "50000",
            "1",
        ]
    )
    writer.writerow(
        [
            "2026-01-16",
            "Example Client",
            "",
            "Example Counsellor",
            "Group/Event",
            "",
            "Physical",
            "Group",
            "",
            "Health Talk",
            "Completed",
            "",
            "",
        ]
    )
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="session-import-template.csv"'},
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
    clients: ClientRepository = Depends(get_client_repository),
    members: EligibleMemberRepository = Depends(get_eligible_member_repository),
    services: ServiceRepository = Depends(get_service_repository),
    db: AsyncSession = Depends(get_db),
):
    """Stage rows for review. Writes no sessions and has no billing side effects.

    Restaging a file whose batch is still awaiting a decision is a conflict,
    not a second batch. Restaging one that has been applied or abandoned is how
    rows re-judge against reference data that has since improved.
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
            details={"file": message, "batch_id": existing.id.value},
        )

    # An earlier judging of this same file gives up every row it never
    # imported, so those source rows can be judged again against reference data
    # that has since improved. Rows that did import keep their keys and come
    # back as duplicates.
    await imports.release_superseded_rows(tenant, file_hash)
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
    try:
        await imports.save_batch(batch)
    except IntegrityError as exc:
        # The pre-check above is read-then-write, not atomic: two concurrent
        # stagings of the same file can both pass it and race to this insert.
        # The partial unique index on (tenant_id, file_hash) WHERE Staged
        # stops the second one at the database, so translate that into the
        # same clean conflict the sequential path already returns instead of
        # letting it surface as an unhandled 500.
        # No batch_id here: the session is unusable for a further query until
        # it rolls back, and this path is rare enough (a genuine race, not a
        # sequential restage) that adding a rollback-then-requery is not
        # worth it for a "discard and retry" shortcut this one case would
        # skip; the client still gets a clean, actionable 409.
        message = "This file was already staged as another batch"
        raise DomainError(
            message,
            error_code="IMPORT_ALREADY_STAGED",
            http_status=409,
            details={"file": message},
        ) from exc

    service = SessionImportStagingService(
        ProviderAliasReconciliationService(aliases),
        affiliations,
        imports,
        clients,
        members,
        services,
    )
    with measure_queries() as measured:
        await _stage_rows(
            service, imports, tenant, source_system, file_hash, source_rows, batch, now
        )
    logger.info(
        "session import staged",
        extra={
            "import_kind": "sessions",
            "import_phase": "stage",
            "batch_id": batch.id.value,
            "rows": len(source_rows),
            **measured.as_log_fields(len(source_rows)),
        },
    )
    await audit_change(batch, audit_handler, current_user, request)
    return _batch_response(batch, await imports.outcome_counts(tenant, batch.id))


async def _stage_rows(
    service: SessionImportStagingService,
    imports: SessionImportRepository,
    tenant: TenantId,
    source_system: str,
    file_hash: str,
    source_rows: Sequence[SourceRow],
    batch: SessionImportBatchEntity,
    now: datetime,
) -> None:
    """Judge every source row and persist the outcomes."""
    await service.preload(tenant, source_rows, file_hash)
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
                staged_replay_key=staged.replay_key,
                outcome=staged.outcome,
                delivery_context=staged.delivery_context,
                provider_id=staged.provider_id,
                provider_affiliation_id=staged.provider_affiliation_id,
                reasons=staged.reasons,
                client_id=staged.client_id,
                attendance=staged.attendance,
                member_id=staged.member_id,
                service_id=staged.service_id,
                session_type=staged.normalised.session_type,
                category=staged.normalised.category,
                clinical_outcome=staged.normalised.clinical_status,
                session_status=staged.normalised.session_status,
                client_type=staged.normalised.client_type,
                rate_ugx=staged.normalised.rate_ugx,
                session_number=staged.normalised.session_number,
                created_at=now,
            )
        )
    await imports.add_rows(entities, file_hash=file_hash)


@router.get("/{batch_id}", response_model=SessionImportBatchResponse)
@readonly()
async def get_batch(
    batch_id: str,
    tenant_id: str = Query(...),
    current_user: TokenData = Depends(require_same_tenant),
    imports: SessionImportRepository = Depends(get_session_import_repository),
):
    batch = await _require_batch(imports, tenant_id, batch_id)
    return _batch_response(batch, await imports.outcome_counts(TenantId(tenant_id), batch.id))


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
    "/{batch_id}/abandon",
    response_model=SessionImportBatchResponse,
    dependencies=[Depends(require_tenant_role(TenantRole.ADMIN))],
)
@transactional()
async def abandon_batch(
    batch_id: str,
    data: SessionImportAbandonRequest,
    request: Request,
    tenant_id: str = Query(...),
    current_user: TokenData = Depends(require_same_tenant),
    imports: SessionImportRepository = Depends(get_session_import_repository),
    audit_handler=Depends(get_audit_event_handler),
    db: AsyncSession = Depends(get_db),
):
    """Close a batch nobody will apply, with the reason on the record.

    A batch stages what the review data said at the time. One staged before
    the practitioner aliases or the member roster were loaded holds outcomes
    that are now wrong, and a staged row keeps no copy of the source values it
    was judged from, so its rows cannot be re-judged in place. Abandoning the
    batch says so and frees the extract to be staged again: neither the file's
    hash nor its rows' replay keys go on claiming a source nobody will import.
    """
    batch = await _require_batch(imports, tenant_id, batch_id)
    batch.abandon(UserId(current_user.user_id), data.reason, at=utc_now())
    await imports.save_batch(batch)
    await imports.release_replay_keys(TenantId(tenant_id), batch.id)
    await audit_change(batch, audit_handler, current_user, request)
    return _batch_response(batch, await imports.outcome_counts(TenantId(tenant_id), batch.id))


@router.post(
    "/{batch_id}/apply",
    response_model=SessionImportApplyResponse,
    dependencies=[Depends(require_tenant_role(TenantRole.ADMIN))],
)
@readonly()
async def apply_batch(
    batch_id: str,
    request: Request,
    tenant_id: str = Query(...),
    limit: int = Query(
        50,
        ge=1,
        le=200,
        description="Max rows to write in this call. Keep calling while the response's "
        "remaining is above zero; the batch only closes once nothing is left.",
    ),
    current_user: TokenData = Depends(require_same_tenant),
    imports: SessionImportRepository = Depends(get_session_import_repository),
    writer=Depends(get_historical_session_writer),
    clients: ClientRepository = Depends(get_client_repository),
    members: EligibleMemberRepository = Depends(get_eligible_member_repository),
    services: ServiceRepository = Depends(get_service_repository),
    audit_handler=Depends(get_audit_event_handler),
    db: AsyncSession = Depends(get_db),
):
    """Write up to `limit` still-pending rows, one at a time, in their own commit.

    A batch large enough to write for minutes cannot be written in a single
    request without risking a platform timeout, and a single transaction
    around all of it loses every row already written the moment any later
    row fails or the call times out. Call this repeatedly while `remaining`
    in the response is above zero; a client that stops calling (a closed
    tab, a timeout) leaves the batch safely Staged for the next call to
    continue from exactly where the last one left off. The batch only closes
    -- flips to Applied, fires its audit event -- once a call finds nothing
    left to write. Applying an already-Applied batch is refused, so a
    replayed request cannot write twice.
    """
    tenant = TenantId(tenant_id)
    with measure_queries() as measured:
        result, batch = await ApplyImportBatchUseCase(
            imports, writer, clients, members, services
        ).execute(
            tenant,
            SessionImportBatchId(batch_id),
            UserId(current_user.user_id),
            now=utc_now(),
            limit=limit,
            after_row=db.commit,
            rollback=db.rollback,
        )
    written = result.imported + result.failed
    logger.info(
        "session import chunk applied",
        extra={
            "import_kind": "sessions",
            "import_phase": "apply",
            "batch_id": batch_id,
            "rows": written,
            "imported": result.imported,
            "failed": result.failed,
            "remaining": result.remaining,
            **measured.as_log_fields(written),
        },
    )
    if result.done:
        await audit_change(batch, audit_handler, current_user, request)
        await db.commit()
    return SessionImportApplyResponse(
        batch_id=batch_id,
        imported=result.imported,
        failed=result.failed,
        remaining=result.remaining,
        done=result.done,
    )
