"""Admin-only staged practitioner workbook import.

Review comes first: staging creates nothing, and applying a batch turns only
its Accepted rows into organisations, practitioners and affiliations. No
created practitioner is bookable and no catalogue entry is invented.
"""

import hashlib

from fastapi import APIRouter, Depends, Query, Request, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_audit_event_handler, get_provider_repository
from app.api.dependencies.pagination import PageParams, pagination
from app.api.dependencies.provider_network import (
    get_practitioner_import_repository,
    get_provider_affiliation_repository,
    get_provider_alias_repository,
    get_provider_organisation_repository,
)
from app.api.schemas.practitioner_import_schemas import (
    PractitionerImportApplyResponse,
    PractitionerImportApplyRowResult,
    PractitionerImportBatchResponse,
    PractitionerImportRowListResponse,
    PractitionerImportRowPreview,
)
from app.application.services.practitioner_import_staging import (
    WORKBOOK_SOURCE_SYSTEM,
    PractitionerImportStagingService,
    new_batch_id,
    new_row_id,
)
from app.application.use_cases.apply_practitioner_import import (
    ApplyPractitionerImportUseCase,
)
from app.core.authorization import require_same_tenant, require_tenant_role
from app.core.database import get_db
from app.core.security import TokenData
from app.domain.entities.practitioner_import import (
    PractitionerImportBatchEntity,
    PractitionerImportRowEntity,
)
from app.domain.enums.provider_network import PractitionerImportOutcome
from app.domain.enums.tenancy import TenantRole
from app.domain.exceptions import DomainError, NotFoundError
from app.domain.repositories.practitioner_import_repository import PractitionerImportRepository
from app.domain.repositories.provider_network_repository import (
    ProviderAffiliationRepository,
    ProviderAliasRepository,
    ProviderOrganisationRepository,
)
from app.domain.repositories.provider_repository import ProviderRepository
from app.domain.value_objects.core import TenantId, UserId
from app.domain.value_objects.provider_network import PractitionerImportBatchId
from app.shared.decorators import readonly, transactional
from app.shared.utils.datetime import utc_now
from app.shared.utils.practitioner_workbook import parse_practitioner_workbook
from app.shared.utils.route_audit_helper import audit_change

router = APIRouter(prefix="/practitioner-imports", tags=["practitioner-imports"])

MAX_IMPORT_BYTES = 10 * 1024 * 1024


def _batch_response(
    batch: PractitionerImportBatchEntity, counts: dict[str, int]
) -> PractitionerImportBatchResponse:
    return PractitionerImportBatchResponse(
        id=batch.id.value,
        tenant_id=batch.tenant_id.value,
        source_system=batch.source_system,
        file_name=batch.file_name,
        file_hash=batch.file_hash,
        row_count=batch.row_count,
        status=batch.status,
        outcome_counts=counts,
        created_at=batch.created_at,
        applied_at=batch.applied_at,
    )


@router.post(
    "",
    response_model=PractitionerImportBatchResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_tenant_role(TenantRole.ADMIN))],
)
@transactional()
async def stage_import(
    request: Request,
    file: UploadFile,
    tenant_id: str = Query(...),
    current_user: TokenData = Depends(require_same_tenant),
    imports: PractitionerImportRepository = Depends(get_practitioner_import_repository),
    aliases: ProviderAliasRepository = Depends(get_provider_alias_repository),
    audit_handler=Depends(get_audit_event_handler),
    db: AsyncSession = Depends(get_db),
):
    """Stage the workbook's rows for review. Nothing is applied.

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

    workbook_rows = parse_practitioner_workbook(content)
    now = utc_now()
    batch = PractitionerImportBatchEntity(
        id=new_batch_id(),
        tenant_id=tenant,
        source_system=WORKBOOK_SOURCE_SYSTEM,
        file_name=file.filename or "upload",
        file_hash=file_hash,
        row_count=len(workbook_rows),
        staged_by=UserId(current_user.user_id),
        created_at=now,
        updated_at=now,
    )
    await imports.save_batch(batch)

    service = PractitionerImportStagingService(aliases, imports)
    staged_rows = await service.stage_rows(tenant, file_hash, workbook_rows, now=now)
    entities = [
        PractitionerImportRowEntity(
            id=new_row_id(),
            batch_id=batch.id,
            tenant_id=tenant,
            sheet_name=staged.sheet_name,
            row_number=staged.row_number,
            raw_name=staged.raw_name,
            normalized_name=staged.normalized_name,
            organisation_name=staged.organisation_name,
            raw_profession=staged.raw_profession,
            mapped_profession=staged.mapped_profession,
            contact_email=staged.contact_email,
            outcome=staged.outcome,
            reasons=staged.reasons,
            provenance=staged.provenance,
            created_at=now,
        )
        for staged in staged_rows
    ]
    await imports.add_rows(entities, file_hash=file_hash)
    batch.record_staged(UserId(current_user.user_id))
    await audit_change(batch, audit_handler, current_user, request)
    return _batch_response(batch, await imports.outcome_counts(tenant, batch.id))


@router.get("/{batch_id}", response_model=PractitionerImportBatchResponse)
@readonly()
async def get_batch(
    batch_id: str,
    tenant_id: str = Query(...),
    current_user: TokenData = Depends(require_same_tenant),
    imports: PractitionerImportRepository = Depends(get_practitioner_import_repository),
):
    tenant = TenantId(tenant_id)
    batch = await imports.get_batch(tenant, PractitionerImportBatchId(batch_id))
    if batch is None:
        raise NotFoundError(
            "Import batch not found",
            resource_type="PractitionerImportBatch",
            resource_id=batch_id,
        )
    return _batch_response(batch, await imports.outcome_counts(tenant, batch.id))


@router.get("/{batch_id}/rows", response_model=PractitionerImportRowListResponse)
@readonly()
async def list_rows(
    batch_id: str,
    tenant_id: str = Query(...),
    outcome: PractitionerImportOutcome | None = Query(None, description="Filter the review queue"),
    pg: PageParams = Depends(pagination(default_limit=50)),
    current_user: TokenData = Depends(require_same_tenant),
    imports: PractitionerImportRepository = Depends(get_practitioner_import_repository),
):
    items, total = await imports.list_rows(
        TenantId(tenant_id),
        PractitionerImportBatchId(batch_id),
        outcome=outcome.value if outcome else None,
        limit=pg.limit,
        offset=pg.offset,
    )
    return PractitionerImportRowListResponse(
        items=[
            PractitionerImportRowPreview(
                sheet_name=row.sheet_name,
                row_number=row.row_number,
                outcome=row.outcome,
                raw_name=row.raw_name,
                normalized_name=row.normalized_name,
                organisation_name=row.organisation_name,
                raw_profession=row.raw_profession,
                mapped_profession=row.mapped_profession,
                contact_email=row.contact_email,
                reasons=list(row.reasons),
                provenance=row.provenance,
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
    response_model=PractitionerImportApplyResponse,
    dependencies=[Depends(require_tenant_role(TenantRole.ADMIN))],
)
@transactional()
async def apply_batch(
    batch_id: str,
    request: Request,
    tenant_id: str = Query(...),
    current_user: TokenData = Depends(require_same_tenant),
    imports: PractitionerImportRepository = Depends(get_practitioner_import_repository),
    providers: ProviderRepository = Depends(get_provider_repository),
    organisations: ProviderOrganisationRepository = Depends(get_provider_organisation_repository),
    affiliations: ProviderAffiliationRepository = Depends(get_provider_affiliation_repository),
    audit_handler=Depends(get_audit_event_handler),
    db: AsyncSession = Depends(get_db),
):
    """Create records from the batch's Accepted rows, then close the batch.

    Applying a second time is refused, so a replayed request cannot create
    twice. A failing row is quarantined for review without sinking the batch.
    """

    async def _audit(entity) -> None:
        await audit_change(entity, audit_handler, current_user, request)

    use_case = ApplyPractitionerImportUseCase(
        imports,
        providers,
        organisations,
        affiliations,
        savepoint=db.begin_nested,
        audit=_audit,
    )
    tenant = TenantId(tenant_id)
    result = await use_case.execute(
        tenant,
        PractitionerImportBatchId(batch_id),
        UserId(current_user.user_id),
        now=utc_now(),
    )
    batch = await imports.get_batch(tenant, PractitionerImportBatchId(batch_id))
    if batch is None:
        raise NotFoundError(
            "Import batch not found",
            resource_type="PractitionerImportBatch",
            resource_id=batch_id,
        )
    return PractitionerImportApplyResponse(
        batch=_batch_response(batch, await imports.outcome_counts(tenant, batch.id)),
        created_providers=result.created_providers,
        created_organisations=result.created_organisations,
        reused_organisations=result.reused_organisations,
        created_affiliations=result.created_affiliations,
        skipped_already_applied=result.skipped_already_applied,
        failed=result.failed,
        not_applicable=result.not_applicable,
        rows=[
            PractitionerImportApplyRowResult(
                sheet_name=row.sheet_name,
                row_number=row.row_number,
                status=row.status,
                provider_id=row.provider_id,
                organisation_id=row.organisation_id,
                affiliation_id=row.affiliation_id,
                error=row.error,
            )
            for row in result.rows
        ],
    )
