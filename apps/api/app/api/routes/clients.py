"""
Client API Routes

FastAPI routes for Client operations.
Follows hybrid approach: Commands use use cases, Queries use repositories directly.
Refactored to use @transactional decorator to eliminate try/except boilerplate.
"""

import csv
import difflib
import io
from dataclasses import replace

from fastapi import APIRouter, Depends, File, HTTPException, Query, Request, UploadFile, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import StreamingResponse

from app.api.dependencies import (
    PageParams,
    get_audit_event_handler,
    get_client_alias_repository,
    get_client_repository,
    get_contract_repository,
    get_industry_repository,
    get_tenant_repository,
    get_user_repository,
    pagination,
)
from app.api.schemas.client_schemas import (
    AddressSchema,
    ClientAliasMergeRequest,
    ClientCreate,
    ClientDeactivateRequest,
    ClientImportCreated,
    ClientImportIssue,
    ClientImportResponse,
    ClientListResponse,
    ClientResponse,
    ClientStatsResponse,
    ClientSuspendRequest,
    ClientTerminateRequest,
    ClientUpdate,
    ClientUpdateAliases,
    ClientUpdateBillingAddress,
    ClientUpdateContactInfo,
    ClientUpdateTier,
    ContactInfoSchema,
)
from app.application.use_cases.client_use_cases import (
    UNSET,
    CreateClientUseCase,
    UpdateClientUseCase,
)
from app.application.use_cases.transitions import (
    ClientTransition,
    TransitionUseCase,
)
from app.core.authorization import (
    get_client_for_current_tenant,
    require_not_viewer,
    require_same_tenant,
    require_tenant_role,
)
from app.core.database import get_db
from app.core.security import TokenData
from app.domain.entities.client import ClientEntity
from app.domain.enums import BaseStatus, ClientTier, ContactMethod, ContractStatus, TenantRole
from app.domain.exceptions import EvexiaException
from app.domain.repositories.client_alias_repository import ClientAliasRepository
from app.domain.repositories.client_repository import ClientRepository
from app.domain.repositories.contract_repository import ContractRepository
from app.domain.repositories.industry_repository import IndustryRepository
from app.domain.repositories.tenant_repository import TenantRepository
from app.domain.repositories.user_repository import UserRepository
from app.domain.value_objects.core import (
    Address,
    ClientId,
    ContactInfo,
    Email,
    IndustryId,
    TenantId,
    UserId,
)
from app.infrastructure.mappers.client_mapper import ClientMapper
from app.infrastructure.models.client_model import ClientModel
from app.shared.decorators import readonly, transactional
from app.shared.utils.client_alias import normalize_client_alias
from app.shared.utils.client_csv import (
    CLIENT_EXPORT_HEADERS,
    CLIENT_IMPORT_HEADERS,
    ClientCsvRow,
    generated_client_code,
    parse_client_csv,
)
from app.shared.utils.generators import generate_cuid
from app.shared.utils.route_audit_helper import audit_change

router = APIRouter(prefix="/clients", tags=["clients"])


def _to_client_response(client: ClientEntity) -> ClientResponse:
    """Map ClientEntity to API response using public properties."""
    contact_info = ContactInfoSchema(
        phone=client.contact_info.phone,
        email=client.contact_info.email.value if client.contact_info.email else None,
        address=client.contact_info.address,
    )

    billing_address = None
    if client.billing_address:
        billing_address = AddressSchema(
            street=client.billing_address.street,
            city=client.billing_address.city,
            country=client.billing_address.country,
            postal_code=client.billing_address.postal_code,
        )

    return ClientResponse(
        id=client.id.value,
        tenant_id=client.tenant_id.value,
        name=client.name,
        code=client.code,
        status=client.status,
        is_verified=client.is_verified,
        contact_info=contact_info,
        billing_address=billing_address,
        industry_id=client.industry_id.value if client.industry_id else None,
        parent_client_id=client.parent_client_id.value if client.parent_client_id else None,
        preferred_contact_method=client.preferred_contact_method,
        tier=client.tier,
        suspension_reason=client.suspension_reason,
        is_active=client.is_active(),
        aliases=client.aliases,
    )


# ==================== COMMANDS (Use Cases) ====================


@router.post(
    "/",
    response_model=ClientResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new client",
)
@transactional()
async def create_client(
    data: ClientCreate,
    request: Request,
    tenant_id: str = Query(..., description="Tenant identifier"),
    current_user: TokenData = Depends(require_same_tenant),
    _write_access: TokenData = Depends(require_not_viewer),
    client_repo: ClientRepository = Depends(get_client_repository),
    tenant_repo: TenantRepository = Depends(get_tenant_repository),
    industry_repo: IndustryRepository = Depends(get_industry_repository),
    audit_handler=Depends(get_audit_event_handler),
    db: AsyncSession = Depends(get_db),
):
    """Create a new client."""
    contact_info = ContactInfo(
        phone=data.contact_info.phone,
        email=Email(data.contact_info.email) if data.contact_info.email else None,
        address=data.contact_info.address,
    )

    billing_address = None
    if data.billing_address:
        billing_address = Address(
            street=data.billing_address.street,
            city=data.billing_address.city,
            country=data.billing_address.country,
            postal_code=data.billing_address.postal_code,
        )

    try:
        client = await CreateClientUseCase(client_repo, tenant_repo, industry_repo).execute(
            client_id=ClientId(generate_cuid()),
            tenant_id=TenantId(tenant_id),
            name=data.name,
            code=data.code,
            contact_info=contact_info,
            billing_address=billing_address,
            industry_id=IndustryId(data.industry_id) if data.industry_id else None,
            parent_client_id=ClientId(data.parent_client_id) if data.parent_client_id else None,
            preferred_contact_method=data.preferred_contact_method,
        )
    except EvexiaException as e:
        raise HTTPException(status_code=e.http_status, detail=e.message) from e

    await audit_change(client, audit_handler, current_user, request, tenant_id=tenant_id)
    return _to_client_response(client)


@router.post(
    "/{client_id}/verify",
    response_model=ClientResponse,
    summary="Verify a client",
)
@transactional()
async def verify_client(
    request: Request,
    verified_by: str = Query(..., description="User ID who verified the client"),
    current_user: TokenData = Depends(require_not_viewer),
    client: ClientEntity = Depends(get_client_for_current_tenant),
    client_repo: ClientRepository = Depends(get_client_repository),
    user_repo: UserRepository = Depends(get_user_repository),
    audit_handler=Depends(get_audit_event_handler),
    db: AsyncSession = Depends(get_db),
):
    """Verify a client."""
    verifier = await user_repo.get_by_id(UserId(verified_by))
    if not verifier or verifier.tenant_id != client.tenant_id:
        raise HTTPException(status_code=404, detail="Verifier user not found")

    use_case = TransitionUseCase(client_repo, "Client")
    client = await use_case.execute(
        client.id, ClientTransition.VERIFY, verified_by=UserId(verified_by)
    )
    await audit_change(client, audit_handler, current_user, request)
    return _to_client_response(client)


@router.post(
    "/{client_id}/activate",
    response_model=ClientResponse,
    summary="Activate a client",
)
@transactional()
async def activate_client(
    request: Request,
    current_user: TokenData = Depends(require_not_viewer),
    client: ClientEntity = Depends(get_client_for_current_tenant),
    client_repo: ClientRepository = Depends(get_client_repository),
    audit_handler=Depends(get_audit_event_handler),
    db: AsyncSession = Depends(get_db),
):
    """Activate a client."""
    use_case = TransitionUseCase(client_repo, "Client")
    client = await use_case.execute(client.id, ClientTransition.ACTIVATE)
    await audit_change(client, audit_handler, current_user, request)
    return _to_client_response(client)


@router.post(
    "/{client_id}/deactivate",
    response_model=ClientResponse,
    summary="Deactivate a client",
)
@transactional()
async def deactivate_client(
    request: Request,
    body: ClientDeactivateRequest,
    current_user: TokenData = Depends(require_not_viewer),
    client: ClientEntity = Depends(get_client_for_current_tenant),
    client_repo: ClientRepository = Depends(get_client_repository),
    audit_handler=Depends(get_audit_event_handler),
    db: AsyncSession = Depends(get_db),
):
    """Deactivate a client."""
    use_case = TransitionUseCase(client_repo, "Client")
    client = await use_case.execute(client.id, ClientTransition.DEACTIVATE, reason=body.reason)
    await audit_change(client, audit_handler, current_user, request)
    return _to_client_response(client)


@router.post(
    "/{client_id}/suspend",
    response_model=ClientResponse,
    summary="Suspend a client",
)
@transactional()
async def suspend_client(
    request: Request,
    body: ClientSuspendRequest,
    current_user: TokenData = Depends(require_not_viewer),
    client: ClientEntity = Depends(get_client_for_current_tenant),
    client_repo: ClientRepository = Depends(get_client_repository),
    audit_handler=Depends(get_audit_event_handler),
    db: AsyncSession = Depends(get_db),
):
    """Suspend a client."""
    use_case = TransitionUseCase(client_repo, "Client")
    client = await use_case.execute(client.id, ClientTransition.SUSPEND, reason=body.reason)
    await audit_change(client, audit_handler, current_user, request)
    return _to_client_response(client)


@router.post(
    "/{client_id}/terminate",
    response_model=ClientResponse,
    summary="Terminate a client",
)
@transactional()
async def terminate_client(
    request: Request,
    body: ClientTerminateRequest,
    current_user: TokenData = Depends(require_not_viewer),
    _admin: None = Depends(require_tenant_role(TenantRole.ADMIN)),
    client: ClientEntity = Depends(get_client_for_current_tenant),
    client_repo: ClientRepository = Depends(get_client_repository),
    audit_handler=Depends(get_audit_event_handler),
    db: AsyncSession = Depends(get_db),
):
    """Terminate a client."""
    use_case = TransitionUseCase(client_repo, "Client")
    client = await use_case.execute(client.id, ClientTransition.TERMINATE, reason=body.reason)
    await audit_change(client, audit_handler, current_user, request)
    return _to_client_response(client)


@router.post(
    "/{client_id}/archive",
    response_model=ClientResponse,
    summary="Archive a client",
)
@transactional()
async def archive_client(
    request: Request,
    current_user: TokenData = Depends(require_not_viewer),
    _admin: None = Depends(require_tenant_role(TenantRole.ADMIN)),
    client: ClientEntity = Depends(get_client_for_current_tenant),
    client_repo: ClientRepository = Depends(get_client_repository),
    audit_handler=Depends(get_audit_event_handler),
    db: AsyncSession = Depends(get_db),
):
    """Archive a client."""
    use_case = TransitionUseCase(client_repo, "Client")
    client = await use_case.execute(client.id, ClientTransition.ARCHIVE)
    await audit_change(client, audit_handler, current_user, request)
    return _to_client_response(client)


@router.post(
    "/{client_id}/restore",
    response_model=ClientResponse,
    summary="Restore a client",
)
@transactional()
async def restore_client(
    request: Request,
    current_user: TokenData = Depends(require_not_viewer),
    client: ClientEntity = Depends(get_client_for_current_tenant),
    client_repo: ClientRepository = Depends(get_client_repository),
    audit_handler=Depends(get_audit_event_handler),
    db: AsyncSession = Depends(get_db),
):
    """Restore an archived or soft-deleted client."""
    use_case = TransitionUseCase(client_repo, "Client")
    client = await use_case.execute(client.id, ClientTransition.RESTORE)
    await audit_change(client, audit_handler, current_user, request)
    return _to_client_response(client)


@router.patch(
    "/{client_id}",
    response_model=ClientResponse,
    summary="Update client basic information",
)
@transactional()
async def update_client(
    data: ClientUpdate,
    request: Request,
    current_user: TokenData = Depends(require_not_viewer),
    client: ClientEntity = Depends(get_client_for_current_tenant),
    client_repo: ClientRepository = Depends(get_client_repository),
    industry_repo: IndustryRepository = Depends(get_industry_repository),
    audit_handler=Depends(get_audit_event_handler),
    db: AsyncSession = Depends(get_db),
):
    """Update client basic information."""
    contact_info = None
    if data.contact_info is not None:
        contact_info = ContactInfo(
            phone=data.contact_info.phone,
            email=Email(data.contact_info.email) if data.contact_info.email else None,
            address=data.contact_info.address,
        )
    elif "contact_info" in data.model_fields_set:
        contact_info = ContactInfo()

    billing_address = None
    if data.billing_address is not None:
        billing_address = Address(
            street=data.billing_address.street,
            city=data.billing_address.city,
            country=data.billing_address.country,
            postal_code=data.billing_address.postal_code,
        )

    fields = data.model_fields_set
    client = await UpdateClientUseCase(client_repo).execute(
        client.id,
        name=data.name,
        preferred_contact_method=(
            data.preferred_contact_method if "preferred_contact_method" in fields else UNSET
        ),
        tier=data.tier if "tier" in fields else UNSET,
        contact_info=contact_info if "contact_info" in fields else UNSET,
        billing_address=billing_address if "billing_address" in fields else UNSET,
        industry_id=(IndustryId(data.industry_id) if data.industry_id else None)
        if "industry_id" in fields
        else UNSET,
        industry_repository=industry_repo,
    )
    await audit_change(client, audit_handler, current_user, request)
    return _to_client_response(client)


@router.patch(
    "/{client_id}/contact-info",
    response_model=ClientResponse,
    summary="Update client contact information",
)
@transactional()
async def update_client_contact_info(
    data: ClientUpdateContactInfo,
    request: Request,
    current_user: TokenData = Depends(require_not_viewer),
    client: ClientEntity = Depends(get_client_for_current_tenant),
    client_repo: ClientRepository = Depends(get_client_repository),
    audit_handler=Depends(get_audit_event_handler),
    db: AsyncSession = Depends(get_db),
):
    """Update client contact information."""
    contact_info = ContactInfo(
        phone=data.contact_info.phone,
        email=Email(data.contact_info.email) if data.contact_info.email else None,
        address=data.contact_info.address,
    )

    use_case = TransitionUseCase(client_repo, "Client")
    client = await use_case.execute(
        client.id, ClientTransition.UPDATE_CONTACT_INFO, contact_info=contact_info
    )
    await audit_change(client, audit_handler, current_user, request)
    return _to_client_response(client)


@router.patch(
    "/{client_id}/billing-address",
    response_model=ClientResponse,
    summary="Update client billing address",
)
@transactional()
async def update_client_billing_address(
    data: ClientUpdateBillingAddress,
    request: Request,
    current_user: TokenData = Depends(require_not_viewer),
    client: ClientEntity = Depends(get_client_for_current_tenant),
    client_repo: ClientRepository = Depends(get_client_repository),
    audit_handler=Depends(get_audit_event_handler),
    db: AsyncSession = Depends(get_db),
):
    """Update client billing address."""
    billing_address = None
    if data.billing_address:
        billing_address = Address(
            street=data.billing_address.street,
            city=data.billing_address.city,
            country=data.billing_address.country,
            postal_code=data.billing_address.postal_code,
        )

    use_case = TransitionUseCase(client_repo, "Client")
    client = await use_case.execute(
        client.id, ClientTransition.UPDATE_BILLING_ADDRESS, billing_address=billing_address
    )
    await audit_change(client, audit_handler, current_user, request)
    return _to_client_response(client)


@router.patch(
    "/{client_id}/tier",
    response_model=ClientResponse,
    summary="Set client engagement tier (A/B/C)",
)
@transactional()
async def update_client_tier(
    data: ClientUpdateTier,
    request: Request,
    current_user: TokenData = Depends(require_not_viewer),
    client: ClientEntity = Depends(get_client_for_current_tenant),
    client_repo: ClientRepository = Depends(get_client_repository),
    audit_handler=Depends(get_audit_event_handler),
    db: AsyncSession = Depends(get_db),
):
    """Set the client's engagement tier."""
    use_case = TransitionUseCase(client_repo, "Client")
    client = await use_case.execute(client.id, ClientTransition.UPDATE_TIER, tier=data.tier)
    await audit_change(client, audit_handler, current_user, request)
    return _to_client_response(client)


# ==================== QUERIES (Direct Repository) ====================


@router.get(
    "/",
    response_model=ClientListResponse,
    summary="List clients with filtering and pagination",
)
@readonly()
async def list_clients(
    tenant_id: str = Query(..., description="Tenant identifier"),
    status: BaseStatus | None = Query(None, description="Filter by client status"),
    is_verified: bool | None = Query(None, description="Filter by verification status"),
    tier: ClientTier | None = Query(None, description="Filter by engagement tier (A/B/C)"),
    parent_client_id: str | None = Query(None, description="Filter by parent client"),
    include_archived: bool = Query(False, description="Include archived clients"),
    search: str | None = Query(None, description="Search in client name"),
    pg: PageParams = Depends(pagination()),
    sort_by: str = Query("created_at", description="Field to sort by"),
    sort_desc: bool = Query(True, description="Sort in descending order"),
    current_user: TokenData = Depends(require_same_tenant),
    client_repo: ClientRepository = Depends(get_client_repository),
    db: AsyncSession = Depends(get_db),
):
    """List clients with filtering, searching, and pagination."""

    clients = await client_repo.list_all(
        tenant_id=TenantId(tenant_id),
        status=status,
        is_verified=is_verified,
        tier=tier,
        parent_client_id=ClientId(parent_client_id) if parent_client_id else None,
        include_archived=include_archived,
        search=search,
        limit=pg.limit,
        offset=pg.offset,
        sort_by=sort_by,
        sort_desc=sort_desc,
    )

    total = await client_repo.count(
        tenant_id=TenantId(tenant_id),
        status=status,
        is_verified=is_verified,
        tier=tier,
        parent_client_id=ClientId(parent_client_id) if parent_client_id else None,
        include_archived=include_archived,
        search=search,
    )

    return ClientListResponse(
        items=[_to_client_response(client) for client in clients],
        total=total,
        page=pg.page,
        limit=pg.limit,
        has_more=(pg.offset + pg.limit) < total,
    )


@router.get(
    "/import/template",
    summary="Download the client CSV import template",
)
async def client_import_template() -> StreamingResponse:
    """Return the supported client import columns as an Excel-compatible CSV."""
    output = io.StringIO(newline="")
    writer = csv.writer(output)
    writer.writerow(CLIENT_IMPORT_HEADERS)
    writer.writerow(
        ["Example Company", "EXM", "+256700000000", "", "", "", "", "", "", "", "", "", ""]
    )
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="clients-import-template.csv"'},
    )


def _client_export_row(client: ClientEntity) -> dict[str, str | bool | None]:
    """Flatten a client response into the import-compatible CSV shape."""
    contact = client.contact_info
    billing = client.billing_address
    return {
        "id": client.id.value,
        "name": client.name,
        "code": client.code,
        "phone": contact.phone,
        "email": contact.email.value if contact.email else None,
        "address": contact.address,
        "billing_street": billing.street if billing else None,
        "billing_city": billing.city if billing else None,
        "billing_country": billing.country if billing else None,
        "billing_postal_code": billing.postal_code if billing else None,
        "industry": None,
        "industry_id": client.industry_id.value if client.industry_id else None,
        "parent_client_name": None,
        "parent_client_id": client.parent_client_id.value if client.parent_client_id else None,
        "preferred_contact_method": client.preferred_contact_method.value
        if client.preferred_contact_method
        else None,
        "aliases": "; ".join(client.aliases),
        "status": client.status.value,
        "tier": client.tier.value if client.tier else None,
        "is_verified": client.is_verified,
    }


@router.get(
    "/export",
    summary="Export clients as CSV",
)
@readonly()
async def export_clients(
    tenant_id: str = Query(..., description="Tenant identifier"),
    status: BaseStatus | None = Query(None, description="Filter by client status"),
    tier: ClientTier | None = Query(None, description="Filter by engagement tier (A/B/C)"),
    parent_client_id: str | None = Query(None, description="Filter by parent client"),
    include_archived: bool = Query(False, description="Include archived clients"),
    search: str | None = Query(None, description="Search in client name"),
    sort_by: str = Query("created_at", description="Field to sort by"),
    sort_desc: bool = Query(True, description="Sort in descending order"),
    _current_user: TokenData = Depends(require_same_tenant),
    client_repo: ClientRepository = Depends(get_client_repository),
    db: AsyncSession = Depends(get_db),
) -> StreamingResponse:
    """Export the tenant's matching clients without exposing other tenants."""
    clients = await client_repo.list_all(
        tenant_id=TenantId(tenant_id),
        status=status,
        tier=tier,
        parent_client_id=ClientId(parent_client_id) if parent_client_id else None,
        include_archived=include_archived,
        search=search,
        limit=10_000,
        sort_by=sort_by,
        sort_desc=sort_desc,
    )
    output = io.StringIO(newline="")
    writer = csv.DictWriter(output, fieldnames=CLIENT_EXPORT_HEADERS)
    writer.writeheader()
    writer.writerows(_client_export_row(client) for client in clients)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="clients.csv"'},
    )


def _import_issue(
    row: ClientCsvRow, field: str | None, message: str, severity: str = "error"
) -> dict[str, str | int]:
    return {"row": row.row_number, "field": field, "message": message, "severity": severity}


def _prepare_import_rows(
    rows: list[ClientCsvRow], issues: list[dict[str, str | int]]
) -> tuple[list[tuple[ClientCsvRow, str]], int]:
    """Validate row-local fields and collapse duplicate names."""
    normalized_names: set[str] = set()
    used_codes: set[str] = set()
    candidates: list[tuple[ClientCsvRow, str]] = []
    skipped = 0
    for row in rows:
        name_key = row.name.casefold()
        if name_key in normalized_names:
            issues.append(_import_issue(row, "name", "Duplicate name in file; skipped", "skipped"))
            for index, (candidate, code) in enumerate(candidates):
                if candidate.name.casefold() == name_key:
                    candidates[index] = (
                        replace(
                            candidate, aliases=tuple(dict.fromkeys(candidate.aliases + row.aliases))
                        ),
                        code,
                    )
                    break
            skipped += 1
            continue
        normalized_names.add(name_key)

        if row.preferred_contact_method and not _valid_contact_method(row):
            issues.append(
                _import_issue(
                    row,
                    "preferred_contact_method",
                    "Must be email, phone, sms, whatsapp, or wechat",
                )
            )
            continue

        code = row.code.upper() if row.code else generated_client_code(row.name, used_codes)
        if not _valid_client_code(code):
            issues.append(_import_issue(row, "code", "Must be 3-5 alphanumeric characters"))
            continue
        if code in used_codes:
            issues.append(_import_issue(row, "code", f"Duplicate code '{code}' in file"))
            continue
        used_codes.add(code)
        candidates.append((row, code))
    return candidates, skipped


def _valid_contact_method(row: ClientCsvRow) -> bool:
    method = row.preferred_contact_method
    if method is None:
        return True
    try:
        ContactMethod(method.lower())
    except ValueError:
        return False
    return True


def _valid_client_code(code: str) -> bool:
    return 3 <= len(code) <= 5 and code.isalnum()


def _validate_file_aliases(
    candidates: list[tuple[ClientCsvRow, str]], issues: list[dict[str, str | int]]
) -> None:
    """Reject aliases that collide with another row before any writes begin."""
    canonical_names = {normalize_client_alias(row.name): row for row, _ in candidates}
    owners: dict[str, ClientCsvRow] = {}
    for row, _ in candidates:
        for alias in row.aliases:
            normalized = normalize_client_alias(alias)
            if normalized in canonical_names and canonical_names[normalized] is not row:
                issues.append(
                    _import_issue(
                        row,
                        "aliases",
                        f"Alias '{alias}' conflicts with another row's canonical name",
                    )
                )
            previous = owners.get(normalized)
            if previous is not None and previous is not row:
                issues.append(
                    _import_issue(row, "aliases", f"Alias '{alias}' is repeated for another row")
                )
            owners[normalized] = row


async def _remove_existing_import_rows(
    candidates: list[tuple[ClientCsvRow, str]],
    tenant_id: TenantId,
    client_repo: ClientRepository,
    alias_repo: ClientAliasRepository,
    issues: list[dict[str, str | int]],
) -> tuple[list[tuple[ClientCsvRow, str]], int]:
    """Skip existing names and reject codes that would collide with the tenant."""
    ready: list[tuple[ClientCsvRow, str]] = []
    skipped = 0
    for row, code in candidates:
        existing = await client_repo.get_by_name_or_alias(tenant_id, row.name)
        if existing:
            detail = (
                "Client name or alias already exists; skipped"
                if existing.name.casefold() == row.name.casefold()
                else f"Matches existing client '{existing.name}' through its name or alias; skipped"
            )
            issues.append(_import_issue(row, "name", detail, "skipped"))
            skipped += 1
            continue
        if await client_repo.get_by_code(tenant_id, code):
            issues.append(_import_issue(row, "code", f"Client code '{code}' already exists"))
            continue
        alias_conflict = False
        for alias in row.aliases:
            normalized = normalize_client_alias(alias)
            owner = await alias_repo.find_by_normalized(tenant_id, normalized)
            canonical_owner = await client_repo.get_by_name(tenant_id, alias)
            if owner or canonical_owner:
                owner_name = canonical_owner.name if canonical_owner else "another client"
                issues.append(
                    _import_issue(
                        row,
                        "aliases",
                        f"Alias '{alias}' conflicts with {owner_name}; resolve before importing",
                    )
                )
                alias_conflict = True
        if alias_conflict:
            continue
        ready.append((row, code))
    return ready, skipped


async def _add_similarity_warnings(
    rows: list[tuple[ClientCsvRow, str]],
    tenant_id: TenantId,
    client_repo: ClientRepository,
    issues: list[dict[str, str | int]],
) -> None:
    """Flag close names for review without blocking a valid import."""
    existing = await client_repo.list_all(tenant_id, limit=10_000, include_archived=True)
    existing_names = {client.name.casefold(): client.name for client in existing}
    for row, _code in rows:
        matches = difflib.get_close_matches(row.name.casefold(), existing_names, n=1, cutoff=0.86)
        if matches and matches[0] != row.name.casefold():
            issues.append(
                _import_issue(
                    row,
                    "name",
                    f"Similar existing client: '{existing_names[matches[0]]}'. Review before importing.",
                    "warning",
                )
            )


async def _resolve_import_references(
    rows: list[tuple[ClientCsvRow, str]],
    tenant_id: TenantId,
    client_repo: ClientRepository,
    industry_repo: IndustryRepository,
    issues: list[dict[str, str | int]],
) -> list[tuple[ClientCsvRow, str, IndustryId | None, ClientId | None]]:
    """Resolve optional human-readable industry and parent-client references."""
    resolved: list[tuple[ClientCsvRow, str, IndustryId | None, ClientId | None]] = []
    for row, code in rows:
        industry_id = IndustryId(row.industry_id) if row.industry_id else None
        if row.industry:
            industry = await industry_repo.get_by_name(row.industry, tenant_id)
            if not industry:
                issues.append(
                    _import_issue(row, "industry", f"Industry '{row.industry}' not found")
                )
                continue
            industry_id = industry.id

        parent_client_id = ClientId(row.parent_client_id) if row.parent_client_id else None
        if row.parent_client_name:
            parent = await client_repo.get_by_name(tenant_id, row.parent_client_name)
            if not parent:
                issues.append(
                    _import_issue(
                        row,
                        "parent_client_name",
                        f"Parent client '{row.parent_client_name}' not found",
                    )
                )
                continue
            parent_client_id = parent.id
        resolved.append((row, code, industry_id, parent_client_id))
    return resolved


def _import_contact_info(row: ClientCsvRow) -> ContactInfo:
    return ContactInfo(
        phone=row.phone,
        email=Email(row.email) if row.email else None,
        address=row.address,
    )


def _import_billing_address(row: ClientCsvRow) -> Address | None:
    if not row.billing_street:
        return None
    return Address(
        street=row.billing_street,
        city=row.billing_city or "",
        country=row.billing_country or "",
        postal_code=row.billing_postal_code,
    )


async def _create_imported_clients(
    rows: list[tuple[ClientCsvRow, str, IndustryId | None, ClientId | None]],
    tenant_id: TenantId,
    request: Request,
    current_user: TokenData,
    client_repo: ClientRepository,
    tenant_repo: TenantRepository,
    industry_repo: IndustryRepository,
    alias_repo: ClientAliasRepository,
    audit_handler,
) -> list[ClientImportCreated]:
    """Create and audit the prevalidated rows."""
    created: list[ClientImportCreated] = []
    use_case = CreateClientUseCase(client_repo, tenant_repo, industry_repo)
    for row, code, industry_id, parent_client_id in rows:
        client = await use_case.execute(
            client_id=ClientId(generate_cuid()),
            tenant_id=tenant_id,
            name=row.name,
            code=code,
            contact_info=_import_contact_info(row),
            billing_address=_import_billing_address(row),
            industry_id=industry_id,
            parent_client_id=parent_client_id,
            preferred_contact_method=ContactMethod(row.preferred_contact_method.lower())
            if row.preferred_contact_method
            else None,
        )
        client.aliases = list(row.aliases)
        await alias_repo.replace_for_client(client.id, tenant_id, row.aliases)
        await audit_change(client, audit_handler, current_user, request, tenant_id=tenant_id)
        created.append(ClientImportCreated(name=client.name, code=client.code))
    return created


@router.post(
    "/import",
    response_model=ClientImportResponse,
    summary="Import clients from CSV",
)
@transactional()
async def import_clients(
    request: Request,
    file: UploadFile = File(..., description="UTF-8 CSV using the client import template"),
    tenant_id: str = Query(..., description="Tenant identifier"),
    dry_run: bool = Query(False, description="Validate without creating clients"),
    current_user: TokenData = Depends(require_same_tenant),
    _write_access: TokenData = Depends(require_not_viewer),
    client_repo: ClientRepository = Depends(get_client_repository),
    alias_repo: ClientAliasRepository = Depends(get_client_alias_repository),
    tenant_repo: TenantRepository = Depends(get_tenant_repository),
    industry_repo: IndustryRepository = Depends(get_industry_repository),
    audit_handler=Depends(get_audit_event_handler),
    db: AsyncSession = Depends(get_db),
) -> ClientImportResponse:
    """Validate and create a batch of clients in one transaction."""
    if file.filename and not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=415, detail="Only CSV files are supported")

    content = await file.read()
    if len(content) > 5 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="CSV file must be 5 MB or smaller")

    try:
        rows, issues = parse_client_csv(content)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    # Existing names are idempotently skipped. Explicit code conflicts and invalid
    # references remain errors, so a bad file never creates a partial batch.
    candidates, skipped = _prepare_import_rows(rows, issues)
    _validate_file_aliases(candidates, issues)
    ready, existing_skipped = await _remove_existing_import_rows(
        candidates, TenantId(tenant_id), client_repo, alias_repo, issues
    )
    skipped += existing_skipped
    ready_with_references = await _resolve_import_references(
        ready, TenantId(tenant_id), client_repo, industry_repo, issues
    )
    await _add_similarity_warnings(ready, TenantId(tenant_id), client_repo, issues)

    errors = [issue for issue in issues if issue.get("severity", "error") == "error"]
    if errors:
        return ClientImportResponse(
            imported=0,
            skipped=skipped,
            failed=len(errors),
            clients=[],
            issues=[ClientImportIssue(**issue) for issue in issues],
        )

    if dry_run:
        return ClientImportResponse(
            imported=len(ready_with_references),
            skipped=skipped,
            failed=0,
            clients=[
                ClientImportCreated(name=row.name, code=code)
                for row, code, _, _ in ready_with_references
            ],
            issues=[ClientImportIssue(**issue) for issue in issues],
        )

    created = await _create_imported_clients(
        ready_with_references,
        TenantId(tenant_id),
        request,
        current_user,
        client_repo,
        tenant_repo,
        industry_repo,
        alias_repo,
        audit_handler,
    )

    return ClientImportResponse(
        imported=len(created),
        skipped=skipped,
        failed=0,
        clients=created,
        issues=[ClientImportIssue(**issue) for issue in issues],
    )


@router.patch(
    "/{client_id}/aliases",
    response_model=ClientResponse,
    summary="Replace client aliases",
)
@transactional()
async def update_client_aliases(
    payload: ClientUpdateAliases,
    request: Request,
    current_user: TokenData = Depends(require_same_tenant),
    client: ClientEntity = Depends(get_client_for_current_tenant),
    client_repo: ClientRepository = Depends(get_client_repository),
    alias_repo: ClientAliasRepository = Depends(get_client_alias_repository),
    _write_access: TokenData = Depends(require_not_viewer),
    audit_handler=Depends(get_audit_event_handler),
    db: AsyncSession = Depends(get_db),
) -> ClientResponse:
    """Replace aliases while keeping them tenant-scoped and deduplicated."""
    aliases = list(dict.fromkeys(alias.strip() for alias in payload.aliases if alias.strip()))
    for alias in aliases:
        normalized = normalize_client_alias(alias)
        if normalize_client_alias(client.name) == normalized:
            raise HTTPException(
                status_code=409, detail=f"Alias '{alias}' is the canonical client name"
            )
        owner = await alias_repo.find_by_normalized(client.tenant_id, normalized)
        canonical_owner = await client_repo.get_by_name(client.tenant_id, alias)
        if owner and owner.client_id != client.id:
            raise HTTPException(
                status_code=409, detail=f"Alias '{alias}' belongs to another client"
            )
        if canonical_owner and canonical_owner.id != client.id:
            raise HTTPException(
                status_code=409, detail=f"Alias '{alias}' is another client's canonical name"
            )
    await alias_repo.replace_for_client(client.id, client.tenant_id, aliases)
    client.aliases = aliases
    await audit_change(client, audit_handler, current_user, request)
    return _to_client_response(client)


@router.post(
    "/{client_id}/aliases/merge",
    response_model=ClientResponse,
    summary="Merge aliases from another client",
)
@transactional()
async def merge_client_aliases(
    payload: ClientAliasMergeRequest,
    request: Request,
    current_user: TokenData = Depends(require_same_tenant),
    client: ClientEntity = Depends(get_client_for_current_tenant),
    client_repo: ClientRepository = Depends(get_client_repository),
    alias_repo: ClientAliasRepository = Depends(get_client_alias_repository),
    _write_access: TokenData = Depends(require_not_viewer),
    audit_handler=Depends(get_audit_event_handler),
    db: AsyncSession = Depends(get_db),
) -> ClientResponse:
    """Move aliases between clients without merging their operational records."""
    source = await client_repo.get_by_id(ClientId(payload.source_client_id))
    if not source or source.tenant_id != client.tenant_id:
        raise HTTPException(status_code=404, detail="Source client not found")
    aliases = await alias_repo.merge_into(client.id, source.id, client.tenant_id)
    client.aliases = [alias.alias for alias in aliases]
    await audit_change(client, audit_handler, current_user, request)
    return _to_client_response(client)


@router.get(
    "/{client_id}",
    response_model=ClientResponse,
    summary="Get client by ID",
)
@readonly()
async def get_client(
    client: ClientEntity = Depends(get_client_for_current_tenant),
    db: AsyncSession = Depends(get_db),
):
    """Get client by ID."""
    return _to_client_response(client)


@router.get(
    "/name/{name}",
    response_model=ClientResponse,
    summary="Get client by name",
)
@readonly()
async def get_client_by_name(
    name: str,
    tenant_id: str = Query(..., description="Tenant identifier"),
    current_user: TokenData = Depends(require_same_tenant),
    client_repo: ClientRepository = Depends(get_client_repository),
    db: AsyncSession = Depends(get_db),
):
    """Get client by name within a tenant."""
    client = await client_repo.get_by_name(TenantId(tenant_id), name)
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    return _to_client_response(client)


@router.get(
    "/check-name/{name}",
    summary="Check if client name is available",
)
@readonly()
async def check_name_availability(
    name: str,
    tenant_id: str = Query(..., description="Tenant identifier"),
    current_user: TokenData = Depends(require_same_tenant),
    client_repo: ClientRepository = Depends(get_client_repository),
    db: AsyncSession = Depends(get_db),
):
    """Check if a client name is available within a tenant."""
    client = await client_repo.get_by_name(TenantId(tenant_id), name)
    return {"available": client is None, "name": name, "tenant_id": tenant_id}


@router.get(
    "/{client_id}/stats",
    response_model=ClientStatsResponse,
    summary="Get client statistics",
)
@readonly()
async def get_client_stats(
    client: ClientEntity = Depends(get_client_for_current_tenant),
    client_repo: ClientRepository = Depends(get_client_repository),
    contract_repo: ContractRepository = Depends(get_contract_repository),
    db: AsyncSession = Depends(get_db),
):
    """Get client statistics including child clients and contracts."""
    tenant_id = client.tenant_id.value
    client_id = client.id.value

    # Count child clients
    child_clients_stmt = select(func.count(ClientModel.id)).where(
        ClientModel.tenant_id == tenant_id,
        ClientModel.parent_client_id == client_id,
        ClientModel.deleted_at.is_(None),
    )
    child_result = await db.execute(child_clients_stmt)
    child_clients_count = int(child_result.scalar() or 0)

    total_contracts_count = await contract_repo.count(
        client.tenant_id,
        client_id=client.id,
    )
    active_contracts_count = await contract_repo.count(
        client.tenant_id,
        client_id=client.id,
        status=ContractStatus.ACTIVE,
    ) + await contract_repo.count(
        client.tenant_id,
        client_id=client.id,
        status=ContractStatus.RENEWED,
    )

    return ClientStatsResponse(
        client_id=client_id,
        child_clients_count=child_clients_count,
        total_contracts_count=total_contracts_count,
        active_contracts_count=active_contracts_count,
        is_verified=client.is_verified,
        status=client.status,
    )


@router.get(
    "/{client_id}/children",
    response_model=ClientListResponse,
    summary="Get child clients of a parent client",
)
@readonly()
async def get_child_clients(
    parent: ClientEntity = Depends(get_client_for_current_tenant),
    pg: PageParams = Depends(pagination()),
    client_repo: ClientRepository = Depends(get_client_repository),
    db: AsyncSession = Depends(get_db),
):
    """Get all child clients of a parent client."""
    tenant_id = parent.tenant_id.value
    client_id = parent.id.value

    # Get child clients
    stmt = select(ClientModel).where(
        ClientModel.tenant_id == tenant_id,
        ClientModel.parent_client_id == client_id,
        ClientModel.deleted_at.is_(None),
    )
    stmt = (
        stmt.order_by(ClientModel.created_at.desc(), ClientModel.id.desc())
        .limit(pg.limit)
        .offset(pg.offset)
    )

    result = await db.execute(stmt)
    models = result.scalars().all()

    # Count total
    count_stmt = select(func.count(ClientModel.id)).where(
        ClientModel.tenant_id == tenant_id,
        ClientModel.parent_client_id == client_id,
        ClientModel.deleted_at.is_(None),
    )
    count_result = await db.execute(count_stmt)
    total = int(count_result.scalar() or 0)

    clients = [ClientMapper.to_entity(model) for model in models]

    return ClientListResponse(
        items=[_to_client_response(c) for c in clients],
        total=total,
        page=pg.page,
        limit=pg.limit,
        has_more=(pg.offset + pg.limit) < total,
    )
