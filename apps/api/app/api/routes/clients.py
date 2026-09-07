"""
Client API Routes

FastAPI routes for Client operations.
Follows hybrid approach: Commands use use cases, Queries use repositories directly.
Refactored to use @transactional decorator to eliminate try/except boilerplate.
"""

import csv
import difflib
import io
import json
from datetime import timedelta

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    File,
    Form,
    HTTPException,
    Query,
    Request,
    UploadFile,
    status,
)
from sqlalchemy import delete, func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import StreamingResponse

from app.api.dependencies import (
    PageParams,
    get_audit_event_handler,
    get_client_alias_repository,
    get_client_repository,
    get_contact_repository,
    get_contract_repository,
    get_industry_repository,
    get_tenant_repository,
    get_user_repository,
    pagination,
)
from app.api.schemas.client_schemas import (
    AddressSchema,
    ClientAliasMergeRequest,
    ClientBulkTagRequest,
    ClientCreate,
    ClientDeactivateRequest,
    ClientDuplicateCandidate,
    ClientDuplicateClient,
    ClientDuplicateListResponse,
    ClientImportCreated,
    ClientImportIssue,
    ClientImportJobListResponse,
    ClientImportJobResponse,
    ClientImportResponse,
    ClientImportRowPreview,
    ClientListResponse,
    ClientMergeRequest,
    ClientMergeResponse,
    ClientResponse,
    ClientSavedViewCreate,
    ClientSavedViewFilters,
    ClientSavedViewListResponse,
    ClientSavedViewResponse,
    ClientStatsResponse,
    ClientSuspendRequest,
    ClientTagAssignmentRequest,
    ClientTerminateRequest,
    ClientUpdate,
    ClientUpdateAliases,
    ClientUpdateBillingAddress,
    ClientUpdateContactInfo,
    ClientUpdateTier,
    ContactInfoSchema,
)
from app.application.services import client_import
from app.application.services.client_import import CreatedClient, ImportRepositories
from app.application.services.client_import_job import run_import_job
from app.application.use_cases.client_use_cases import (
    UNSET,
    CreateClientUseCase,
    UpdateClientUseCase,
)
from app.application.use_cases.contact_use_cases import CreateContactUseCase, UpdateContactUseCase
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
from app.core.database import AsyncSessionLocal, get_db
from app.core.security import TokenData, get_current_user
from app.domain.entities.client import ClientEntity
from app.domain.enums import (
    BaseStatus,
    ClientTier,
    ContractStatus,
    MemberRelation,
    TenantRole,
)
from app.domain.exceptions import EvexiaException
from app.domain.repositories.client_alias_repository import ClientAliasRepository
from app.domain.repositories.client_repository import ClientRepository
from app.domain.repositories.contact_repository import ContactRepository
from app.domain.repositories.contract_repository import ContractRepository
from app.domain.repositories.industry_repository import IndustryRepository
from app.domain.repositories.tenant_repository import TenantRepository
from app.domain.repositories.user_repository import UserRepository
from app.domain.value_objects.core import (
    Address,
    ClientId,
    ContactId,
    ContactInfo,
    Email,
    IndustryId,
    TenantId,
    UserId,
)
from app.infrastructure.mappers.client_mapper import ClientMapper
from app.infrastructure.models.client_alias_model import ClientAliasModel
from app.infrastructure.models.client_import_job_model import ClientImportJobModel
from app.infrastructure.models.client_model import ClientModel
from app.infrastructure.models.client_saved_view_model import ClientSavedViewModel
from app.infrastructure.models.client_tag_assignment_model import ClientTagAssignmentModel
from app.infrastructure.models.client_tag_model import ClientTagModel
from app.infrastructure.models.contact_model import ContactModel
from app.infrastructure.models.person_model import PersonModel
from app.shared.decorators import readonly, transactional
from app.shared.utils.client_alias import normalize_client_alias
from app.shared.utils.client_csv import (
    CLIENT_EXPORT_HEADERS,
    CLIENT_IMPORT_HEADERS,
    ClientCsvRow,
    Issue,
    parse_client_csv,
)
from app.shared.utils.datetime import ensure_utc, utc_now
from app.shared.utils.generators import generate_cuid
from app.shared.utils.route_audit_helper import audit_change

router = APIRouter(prefix="/clients", tags=["clients"])

# A job still marked processing after this long has lost its worker.
STALE_IMPORT_AFTER = timedelta(hours=1)


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


async def _client_list_metrics(
    db: AsyncSession, tenant_id: str, client_ids: list[str]
) -> dict[str, dict[str, int | str | None]]:
    """Load list-card metrics in a fixed number of queries for the current page."""
    metrics = {
        client_id: {
            "active_contracts_count": 0,
            "staff_count": 0,
            "last_activity_at": None,
            "next_renewal_date": None,
        }
        for client_id in client_ids
    }
    if not client_ids:
        return metrics

    contract_table = ClientModel.metadata.tables.get("contracts")
    if contract_table is not None:
        contract_rows = await db.execute(
            select(
                contract_table.c.client_id,
                func.count(contract_table.c.id),
                func.min(contract_table.c.end_date),
            )
            .where(
                contract_table.c.tenant_id == tenant_id,
                contract_table.c.client_id.in_(client_ids),
                contract_table.c.deleted_at.is_(None),
                contract_table.c.status.in_(
                    [ContractStatus.ACTIVE.value, ContractStatus.RENEWED.value]
                ),
            )
            .group_by(contract_table.c.client_id)
        )
        for client_id, count, renewal_date in contract_rows:
            metrics[client_id]["active_contracts_count"] = int(count)
            metrics[client_id]["next_renewal_date"] = (
                renewal_date.isoformat() if renewal_date else None
            )

    activity_table = ClientModel.metadata.tables.get("activities")
    if activity_table is not None:
        activity_rows = await db.execute(
            select(activity_table.c.client_id, func.max(activity_table.c.occurred_at))
            .where(
                activity_table.c.tenant_id == tenant_id,
                activity_table.c.client_id.in_(client_ids),
                activity_table.c.deleted_at.is_(None),
            )
            .group_by(activity_table.c.client_id)
        )
        for client_id, occurred_at in activity_rows:
            metrics[client_id]["last_activity_at"] = (
                occurred_at.isoformat() if occurred_at else None
            )

    member_table = ClientModel.metadata.tables["eligible_members"]
    employees = await db.execute(
        select(member_table.c.client_id, func.count(member_table.c.id))
        .where(
            member_table.c.tenant_id == tenant_id,
            member_table.c.client_id.in_(client_ids),
            member_table.c.relation == MemberRelation.EMPLOYEE,
        )
        .group_by(member_table.c.client_id)
    )
    for client_id, count in employees:
        metrics[client_id]["staff_count"] = int(count)
    return metrics


def _saved_view_response(view: ClientSavedViewModel) -> ClientSavedViewResponse:
    return ClientSavedViewResponse(
        id=view.id,
        tenant_id=view.tenant_id,
        name=view.name,
        filters=ClientSavedViewFilters.model_validate(view.filters),
        created_by=view.created_by,
        is_shared=view.is_shared,
        created_at=view.created_at.isoformat(),
        updated_at=view.updated_at.isoformat(),
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
    contact_repo: ContactRepository = Depends(get_contact_repository),
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
    if data.contact_person_name:
        await CreateContactUseCase(contact_repo).execute(
            contact_id=ContactId(generate_cuid()),
            tenant_id=TenantId(tenant_id),
            client_id=client.id.value,
            name=data.contact_person_name,
            email=data.contact_info.email,
            phone=data.contact_info.phone,
            is_primary=True,
        )
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
    contact_repo: ContactRepository = Depends(get_contact_repository),
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
    if "contact_person_name" in fields and data.contact_person_name:
        contacts = await contact_repo.get_by_client_id(client.id.value, client.tenant_id)
        primary = next((contact for contact in contacts if contact.is_primary), None)
        if primary:
            await UpdateContactUseCase(contact_repo).execute(
                primary.id, name=data.contact_person_name
            )
        else:
            await CreateContactUseCase(contact_repo).execute(
                contact_id=ContactId(generate_cuid()),
                tenant_id=client.tenant_id,
                client_id=client.id.value,
                name=data.contact_person_name,
                email=client.contact_info.email.value if client.contact_info.email else None,
                phone=client.contact_info.phone,
                is_primary=True,
            )
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
    "/views",
    response_model=ClientSavedViewListResponse,
    summary="List client views visible to the current user",
)
@readonly()
async def list_client_views(
    current_user: TokenData = Depends(require_same_tenant),
    db: AsyncSession = Depends(get_db),
) -> ClientSavedViewListResponse:
    """Return the user's views and views shared by other users in the tenant."""
    stmt = (
        select(ClientSavedViewModel)
        .where(
            ClientSavedViewModel.tenant_id == current_user.tenant_id,
            or_(
                ClientSavedViewModel.created_by == current_user.user_id,
                ClientSavedViewModel.is_shared.is_(True),
            ),
        )
        .order_by(ClientSavedViewModel.name.asc())
    )
    result = await db.execute(stmt)
    items = [_saved_view_response(view) for view in result.scalars().all()]
    return ClientSavedViewListResponse(items=items, total=len(items))


@router.post(
    "/views",
    response_model=ClientSavedViewResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Save a client list view",
)
@transactional()
async def create_client_view(
    data: ClientSavedViewCreate,
    current_user: TokenData = Depends(require_not_viewer),
    db: AsyncSession = Depends(get_db),
) -> ClientSavedViewResponse:
    """Create a tenant-scoped saved view."""
    existing = await db.execute(
        select(ClientSavedViewModel).where(
            ClientSavedViewModel.tenant_id == current_user.tenant_id,
            ClientSavedViewModel.created_by == current_user.user_id,
            func.lower(ClientSavedViewModel.name) == data.name.lower(),
        )
    )
    view = existing.scalar_one_or_none()
    if view:
        view.filters = data.filters.model_dump()
        view.is_shared = data.is_shared
    else:
        view = ClientSavedViewModel(
            id=generate_cuid(),
            tenant_id=current_user.tenant_id,
            name=data.name,
            filters=data.filters.model_dump(),
            created_by=current_user.user_id,
            is_shared=data.is_shared,
        )
        db.add(view)
    await db.flush()
    return _saved_view_response(view)


@router.delete(
    "/views/{view_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a client list view",
)
@transactional()
async def delete_client_view(
    view_id: str,
    current_user: TokenData = Depends(require_not_viewer),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete a view owned by the current user."""
    result = await db.execute(
        select(ClientSavedViewModel).where(
            ClientSavedViewModel.id == view_id,
            ClientSavedViewModel.tenant_id == current_user.tenant_id,
            ClientSavedViewModel.created_by == current_user.user_id,
        )
    )
    view = result.scalar_one_or_none()
    if not view:
        raise HTTPException(status_code=404, detail="Saved view not found")
    await db.delete(view)


@router.get(
    "/duplicates",
    response_model=ClientDuplicateListResponse,
    summary="Scan the tenant client list for likely duplicates",
)
@readonly()
async def scan_client_duplicates(
    current_user: TokenData = Depends(require_same_tenant),
    db: AsyncSession = Depends(get_db),
) -> ClientDuplicateListResponse:
    """Find close names and repeated contact emails for an explicit review."""
    result = await db.execute(
        select(ClientModel).where(
            ClientModel.tenant_id == current_user.tenant_id,
            ClientModel.status != BaseStatus.ARCHIVED,
            ClientModel.deleted_at.is_(None),
        )
    )
    clients = result.scalars().all()
    candidates: list[ClientDuplicateCandidate] = []
    for index, first in enumerate(clients):
        first_name = normalize_client_alias(first.name)
        first_email = (first.contact_info or {}).get("email")
        for second in clients[index + 1 :]:
            second_name = normalize_client_alias(second.name)
            second_email = (second.contact_info or {}).get("email")
            similarity = difflib.SequenceMatcher(None, first_name, second_name).ratio()
            same_email = bool(
                first_email and second_email and first_email.casefold() == second_email.casefold()
            )
            if not same_email and (len(first_name) < 4 or similarity < 0.84):
                continue
            candidates.append(
                ClientDuplicateCandidate(
                    first=ClientDuplicateClient(
                        id=first.id,
                        name=first.name,
                        code=first.code,
                        contact_email=first_email,
                    ),
                    second=ClientDuplicateClient(
                        id=second.id,
                        name=second.name,
                        code=second.code,
                        contact_email=second_email,
                    ),
                    reason="Matching contact email" if same_email else "Very similar client names",
                    similarity=round(max(similarity, 1.0 if same_email else similarity), 3),
                )
            )
    candidates.sort(key=lambda candidate: candidate.similarity, reverse=True)
    return ClientDuplicateListResponse(items=candidates[:100], scanned=len(clients))


@router.post(
    "/{client_id}/merge",
    response_model=ClientMergeResponse,
    summary="Merge a duplicate client into this client",
)
@transactional()
async def merge_client(
    payload: ClientMergeRequest,
    request: Request,
    current_user: TokenData = Depends(require_not_viewer),
    target: ClientEntity = Depends(get_client_for_current_tenant),
    client_repo: ClientRepository = Depends(get_client_repository),
    audit_handler=Depends(get_audit_event_handler),
    db: AsyncSession = Depends(get_db),
) -> ClientMergeResponse:
    """Move operational records to the target and archive the source client."""
    if payload.source_client_id == target.id.value:
        raise HTTPException(status_code=400, detail="A client cannot be merged into itself")
    if target.status == BaseStatus.ARCHIVED:
        raise HTTPException(status_code=400, detail="An archived client cannot be a merge target")
    source_result = await db.execute(
        select(ClientModel).where(
            ClientModel.id == payload.source_client_id,
            ClientModel.tenant_id == target.tenant_id.value,
            ClientModel.status != BaseStatus.ARCHIVED,
            ClientModel.deleted_at.is_(None),
        )
    )
    source = source_result.scalar_one_or_none()
    if not source:
        raise HTTPException(status_code=404, detail="Source client not found")

    transferred: dict[str, int] = {}
    conflicts: list[str] = []
    target_aliases = await db.execute(
        select(ClientAliasModel).where(ClientAliasModel.client_id == target.id.value)
    )
    alias_norms = {alias.normalized_alias for alias in target_aliases.scalars().all()}
    source_aliases = await db.execute(
        select(ClientAliasModel).where(ClientAliasModel.client_id == source.id)
    )
    for alias in source_aliases.scalars().all():
        if alias.normalized_alias in alias_norms:
            conflicts.append(f"Alias '{alias.alias}' already exists on the target")
            await db.delete(alias)
        else:
            alias.client_id = target.id.value
            alias_norms.add(alias.normalized_alias)
            transferred["aliases"] = transferred.get("aliases", 0) + 1

    target_contacts = await db.execute(
        select(ContactModel).where(
            ContactModel.client_id == target.id.value,
            ContactModel.deleted_at.is_(None),
        )
    )
    target_contact_models = target_contacts.scalars().all()
    has_primary = any(contact.is_primary for contact in target_contact_models)
    has_legacy_contact = bool(
        target.contact_info.email or target.contact_info.phone or target.contact_info.address
    )
    source_contacts = await db.execute(
        select(ContactModel).where(
            ContactModel.client_id == source.id,
            ContactModel.deleted_at.is_(None),
        )
    )
    contact_count = 0
    for contact in source_contacts.scalars().all():
        contact.client_id = target.id.value
        contact.is_primary = contact.is_primary and not has_primary and not has_legacy_contact
        has_primary = has_primary or contact.is_primary
        contact_count += 1
    if contact_count:
        transferred["contacts"] = contact_count

    # The legacy profile contact fields are not represented by ContactModel.
    # Preserve them when the target has a blank field so a merge cannot lose
    # the source client's only phone, email, or address.
    target_model_result = await db.execute(
        select(ClientModel).where(ClientModel.id == target.id.value)
    )
    target_model = target_model_result.scalar_one()
    target_contact_info = dict(target_model.contact_info or {})
    source_contact_info = source.contact_info or {}
    contact_info_changed = False
    for field in ("phone", "email", "address"):
        if not target_contact_info.get(field) and source_contact_info.get(field):
            target_contact_info[field] = source_contact_info[field]
            contact_info_changed = True
    if contact_info_changed:
        target_model.contact_info = target_contact_info
        transferred["profile_contact_fields"] = sum(
            1
            for field in ("phone", "email", "address")
            if target_contact_info.get(field) == source_contact_info.get(field)
        )
    if target_model.billing_address is None and source.billing_address is not None:
        target_model.billing_address = source.billing_address
        transferred["billing_address"] = 1

    target_tags = await db.execute(
        select(ClientTagAssignmentModel.tag_id).where(
            ClientTagAssignmentModel.client_id == target.id.value
        )
    )
    tag_ids = set(target_tags.scalars().all())
    source_tags = await db.execute(
        select(ClientTagAssignmentModel).where(ClientTagAssignmentModel.client_id == source.id)
    )
    tag_count = 0
    for assignment in source_tags.scalars().all():
        if assignment.tag_id in tag_ids:
            await db.delete(assignment)
        else:
            assignment.client_id = target.id.value
            tag_ids.add(assignment.tag_id)
            tag_count += 1
    if tag_count:
        transferred["tags"] = tag_count

    related_tables = (
        "contracts",
        "activities",
        "documents",
        "kpi_assignments",
        "care_callback_campaigns",
        "cases",
        "critical_incidents",
        "eligible_members",
        "engagements",
        "survey_campaigns",
    )
    for table_name in related_tables:
        table = ClientModel.metadata.tables.get(table_name)
        if table is None or "client_id" not in table.c:
            continue
        result = await db.execute(
            update(table)
            .where(table.c.client_id == source.id, table.c.tenant_id == target.tenant_id.value)
            .values(client_id=target.id.value)
        )
        if result.rowcount:
            transferred[table_name] = int(result.rowcount)

    # Preserve client associations on legacy person profiles.
    people_result = await db.execute(
        select(PersonModel).where(
            PersonModel.tenant_id == target.tenant_id.value,
            PersonModel.deleted_at.is_(None),
            or_(
                PersonModel.employment_info["client_id"].as_string() == source.id,
                PersonModel.staff_info["client_id"].as_string() == source.id,
            ),
        )
    )
    people_transferred = 0
    for person in people_result.scalars().all():
        person_changed = False
        for field in ("employment_info", "staff_info"):
            profile = getattr(person, field)
            if isinstance(profile, dict) and profile.get("client_id") == source.id:
                setattr(person, field, {**profile, "client_id": target.id.value})
                person_changed = True
        if person_changed:
            people_transferred += 1
    if people_transferred:
        transferred["staff"] = people_transferred

    await db.execute(
        update(ClientModel)
        .where(
            ClientModel.tenant_id == target.tenant_id.value,
            ClientModel.parent_client_id == source.id,
            ClientModel.deleted_at.is_(None),
        )
        .values(parent_client_id=target.id.value)
    )
    if normalize_client_alias(source.name) != normalize_client_alias(target.name):
        source_name_norm = normalize_client_alias(source.name)
        existing_alias = await db.execute(
            select(ClientAliasModel).where(
                ClientAliasModel.tenant_id == target.tenant_id.value,
                ClientAliasModel.normalized_alias == source_name_norm,
            )
        )
        if source_name_norm not in alias_norms and existing_alias.scalar_one_or_none() is None:
            db.add(
                ClientAliasModel(
                    id=generate_cuid(),
                    tenant_id=target.tenant_id.value,
                    client_id=target.id.value,
                    alias=source.name,
                    normalized_alias=source_name_norm,
                    created_at=utc_now(),
                    updated_at=utc_now(),
                )
            )
            transferred["aliases"] = transferred.get("aliases", 0) + 1
        else:
            conflicts.append(f"Canonical name '{source.name}' already exists as an alias")

    source.status = BaseStatus.ARCHIVED
    source.updated_at = utc_now()
    await db.flush()
    merged = await client_repo.get_by_id(target.id)
    if not merged:
        raise HTTPException(status_code=404, detail="Merged client could not be reloaded")
    merged_aliases = await db.execute(
        select(ClientAliasModel.alias).where(
            ClientAliasModel.tenant_id == target.tenant_id.value,
            ClientAliasModel.client_id == target.id.value,
        )
    )
    merged.aliases = list(merged_aliases.scalars().all())
    await audit_change(merged, audit_handler, current_user, request)
    return ClientMergeResponse(
        client=_to_client_response(merged),
        source_client_id=source.id,
        transferred=transferred,
        conflicts=conflicts,
    )


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

    metrics = await _client_list_metrics(db, tenant_id, [client.id.value for client in clients])
    response_items = [
        _to_client_response(client).model_copy(update=metrics[client.id.value])
        for client in clients
    ]

    return ClientListResponse(
        items=response_items,
        total=total,
        page=pg.page,
        limit=pg.limit,
        has_more=(pg.offset + pg.limit) < total,
    )


@router.get(
    "/import/template",
    summary="Download the client CSV import template",
)
async def client_import_template(
    current_user: TokenData = Depends(get_current_user),
) -> StreamingResponse:
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
    client_ids: list[str] | None = Query(None, description="Export only selected client IDs"),
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
    if client_ids:
        selected = await db.execute(
            select(ClientModel).where(
                ClientModel.tenant_id == tenant_id,
                ClientModel.id.in_(set(client_ids)),
                ClientModel.deleted_at.is_(None),
            )
        )
        clients = [ClientMapper.to_entity(model) for model in selected.scalars().all()]
    else:
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


def _import_row_previews(
    rows: list[ClientCsvRow],
    candidates: list[tuple[ClientCsvRow, str]],
    issues: list[Issue],
    matches: dict[int, ClientEntity],
    similar_matches: dict[int, ClientEntity],
) -> list[ClientImportRowPreview]:
    """Build the server-authoritative preview shown before confirmation."""
    codes = {row.row_number: code for row, code in candidates}
    error_rows = {
        issue["row"] for issue in issues if issue["severity"] == "error" and issue["row"] > 0
    }
    previews: list[ClientImportRowPreview] = []
    for row in rows:
        matched = matches.get(row.row_number) or similar_matches.get(row.row_number)
        state = "duplicate" if row.row_number in matches else "similar" if matched else "new"
        if row.row_number in error_rows:
            state = "invalid"
        previews.append(
            ClientImportRowPreview(
                row=row.row_number,
                name=row.name,
                code=codes.get(row.row_number),
                aliases=list(row.aliases),
                contact=" \u00b7 ".join(value for value in (row.email, row.phone) if value) or None,
                state=state,
                default_action="skip" if matched or state == "invalid" else "create",
                matched_client_id=matched.id.value if matched else None,
                matched_client_name=matched.name if matched else None,
            )
        )
    return previews


def _to_import_job_response(job: ClientImportJobModel) -> ClientImportJobResponse:
    """Map a persisted import job to its public progress response."""
    return ClientImportJobResponse(
        id=job.id,
        filename=job.filename,
        status=job.status,
        file_size=job.file_size,
        total_rows=job.total_rows,
        processed_rows=job.processed_rows,
        imported=job.imported,
        skipped=job.skipped,
        failed=job.failed,
        retry_count=job.retry_count,
        issues=[ClientImportIssue(**issue) for issue in (job.issues or [])],
        error_message=job.error_message,
        created_at=job.created_at.isoformat(),
        started_at=job.started_at.isoformat() if job.started_at else None,
        completed_at=job.completed_at.isoformat() if job.completed_at else None,
    )


def _import_repositories(
    client_repo: ClientRepository,
    alias_repo: ClientAliasRepository,
    industry_repo: IndustryRepository,
    tenant_repo: TenantRepository,
) -> ImportRepositories:
    return ImportRepositories(
        client=client_repo, alias=alias_repo, industry=industry_repo, tenant=tenant_repo
    )


def _created_response(created: list[CreatedClient]) -> list[ClientImportCreated]:
    return [ClientImportCreated(name=item.name, code=item.code) for item in created]


async def _read_import_file(file: UploadFile, *, limit_bytes: int) -> bytes:
    """Read an uploaded CSV, rejecting the wrong type or an oversized body."""
    if file.filename and not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=415, detail="Only CSV files are supported")
    content = await file.read()
    if len(content) > limit_bytes:
        megabytes = limit_bytes // (1024 * 1024)
        raise HTTPException(status_code=413, detail=f"CSV file must be {megabytes} MB or smaller")
    return content


class _ImportJobGateway:
    """Binds the import runner to this application's infrastructure.

    The runner is in the application layer and must not import infrastructure;
    the route is the composition root, so the wiring lives here.
    """

    def session(self):
        return AsyncSessionLocal()

    async def load(self, session, job_id: str):
        return await session.get(ClientImportJobModel, job_id)

    def repositories(self, session) -> ImportRepositories:
        from app.infrastructure.repositories.client_alias_repository import (
            ClientAliasRepositoryImpl,
        )
        from app.infrastructure.repositories.client_repository import ClientRepositoryImpl
        from app.infrastructure.repositories.industry_repository import IndustryRepositoryImpl
        from app.infrastructure.repositories.tenant_repository import TenantRepositoryImpl

        return ImportRepositories(
            client=ClientRepositoryImpl(session),
            alias=ClientAliasRepositoryImpl(session),
            industry=IndustryRepositoryImpl(session),
            tenant=TenantRepositoryImpl(session),
        )

    def audit_handler(self, session):
        from app.infrastructure.repositories.outbox_repository import OutboxRepositoryImpl
        from app.shared.handlers.audit_event_handler import AuditEventHandler

        return AuditEventHandler(OutboxRepositoryImpl(session))


async def _run_client_import_job(job_id: str) -> None:
    """Run a queued import against a fresh session, outside the request."""
    await run_import_job(job_id, _ImportJobGateway())


@router.post(
    "/import",
    response_model=ClientImportResponse,
    summary="Import clients from CSV",
)
@transactional()
async def import_clients(
    request: Request,
    file: UploadFile = File(..., description="UTF-8 CSV using the client import template"),
    decisions_json: str = Form("", description="JSON row actions from the server preview"),
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
    content = await _read_import_file(file, limit_bytes=5 * 1024 * 1024)
    try:
        rows, issues = parse_client_csv(content)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    repos = _import_repositories(client_repo, alias_repo, industry_repo, tenant_repo)
    decisions = client_import.parse_decisions(decisions_json, issues)
    result = await client_import.validate(rows, TenantId(tenant_id), repos, decisions, issues)
    previews = _import_row_previews(
        rows, result.candidates, issues, result.matches, result.similar_matches
    )

    if result.errors:
        return ClientImportResponse(
            imported=0,
            skipped=result.skipped,
            failed=len(result.errors),
            clients=[],
            issues=[ClientImportIssue(**issue) for issue in issues],
            rows=previews,
        )

    if dry_run:
        return ClientImportResponse(
            imported=len(result.ready),
            skipped=result.skipped,
            failed=0,
            clients=[
                ClientImportCreated(name=row.name, code=code) for row, code, _, _ in result.ready
            ],
            issues=[ClientImportIssue(**issue) for issue in issues],
            rows=previews,
        )

    created, failed = await client_import.create_clients(
        result.ready,
        TenantId(tenant_id),
        repos,
        current_user,
        decisions,
        result.all_matches,
        issues,
        audit_handler,
        request=request,
    )

    return ClientImportResponse(
        imported=len(created),
        skipped=result.skipped,
        failed=failed,
        clients=_created_response(created),
        issues=[ClientImportIssue(**issue) for issue in issues],
        rows=previews,
    )


@router.post(
    "/import/jobs",
    response_model=ClientImportJobResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Queue a background client import",
)
@transactional()
async def queue_client_import(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(..., description="UTF-8 CSV using the client import template"),
    decisions_json: str = Form("", description="JSON row actions from the server preview"),
    tenant_id: str = Query(..., description="Tenant identifier"),
    current_user: TokenData = Depends(require_same_tenant),
    _write_access: TokenData = Depends(require_not_viewer),
    db: AsyncSession = Depends(get_db),
) -> ClientImportJobResponse:
    """Queue imports larger than the synchronous request limit."""
    content = await _read_import_file(file, limit_bytes=50 * 1024 * 1024)
    try:
        parsed_rows, _ = parse_client_csv(content)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    decisions: dict[str, object] = {}
    if decisions_json:
        try:
            decisions = json.loads(decisions_json)
        except json.JSONDecodeError as exc:
            raise HTTPException(status_code=422, detail="Invalid import decisions") from exc
    job = ClientImportJobModel(
        id=generate_cuid(),
        tenant_id=tenant_id,
        requested_by=current_user.user_id,
        filename=file.filename or "clients.csv",
        file_size=len(content),
        file_content=content,
        decisions=decisions,
        status="queued",
        total_rows=len(parsed_rows),
        issues=[],
    )
    db.add(job)
    await db.flush()
    background_tasks.add_task(_run_client_import_job, job.id)
    return _to_import_job_response(job)


@router.get(
    "/import/jobs",
    response_model=ClientImportJobListResponse,
    summary="List client import history",
)
@readonly()
async def list_client_import_jobs(
    tenant_id: str = Query(..., description="Tenant identifier"),
    limit: int = Query(50, ge=1, le=100),
    current_user: TokenData = Depends(require_same_tenant),
    db: AsyncSession = Depends(get_db),
) -> ClientImportJobListResponse:
    """Return recent imports for the current tenant."""
    result = await db.execute(
        select(ClientImportJobModel)
        .where(ClientImportJobModel.tenant_id == tenant_id)
        .order_by(ClientImportJobModel.created_at.desc())
        .limit(limit)
    )
    count_result = await db.execute(
        select(func.count(ClientImportJobModel.id)).where(
            ClientImportJobModel.tenant_id == tenant_id
        )
    )
    return ClientImportJobListResponse(
        items=[_to_import_job_response(job) for job in result.scalars().all()],
        total=count_result.scalar_one(),
    )


@router.get(
    "/import/jobs/{job_id}",
    response_model=ClientImportJobResponse,
    summary="Get client import progress",
)
@readonly()
async def get_client_import_job(
    job_id: str,
    tenant_id: str = Query(..., description="Tenant identifier"),
    current_user: TokenData = Depends(require_same_tenant),
    db: AsyncSession = Depends(get_db),
) -> ClientImportJobResponse:
    """Return one tenant-scoped import job."""
    job = await db.get(ClientImportJobModel, job_id)
    if not job or job.tenant_id != tenant_id:
        raise HTTPException(status_code=404, detail="Import job not found")
    return _to_import_job_response(job)


def _is_retryable(job: ClientImportJobModel) -> bool:
    """A job is retryable once it failed, or once it was abandoned mid-run.

    A worker killed between claiming a job and recording its outcome leaves the
    row in `processing` with nothing left to advance it. Without the staleness
    window such a job can never be retried.
    """
    if job.status == "failed":
        return True
    if job.status != "processing":
        return False
    started = job.started_at
    if started is None:
        return True
    return utc_now() - ensure_utc(started) > STALE_IMPORT_AFTER


@router.post(
    "/import/jobs/{job_id}/retry",
    response_model=ClientImportJobResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Retry a failed client import",
)
@transactional()
async def retry_client_import_job(
    job_id: str,
    background_tasks: BackgroundTasks,
    tenant_id: str = Query(..., description="Tenant identifier"),
    current_user: TokenData = Depends(require_same_tenant),
    _write_access: TokenData = Depends(require_not_viewer),
    db: AsyncSession = Depends(get_db),
) -> ClientImportJobResponse:
    """Requeue a failed or abandoned import using its file and decisions."""
    job = await db.get(ClientImportJobModel, job_id)
    if not job or job.tenant_id != tenant_id:
        raise HTTPException(status_code=404, detail="Import job not found")
    if not _is_retryable(job):
        raise HTTPException(
            status_code=409, detail="Only failed or abandoned imports can be retried"
        )
    job.status = "queued"
    job.error_message = None
    job.completed_at = None
    job.retry_count += 1
    await db.flush()
    background_tasks.add_task(_run_client_import_job, job.id)
    return _to_import_job_response(job)


def _tag_response(tag: ClientTagModel) -> dict[str, object]:
    """Map a client tag model to the lightweight detail/list representation."""
    return {
        "id": tag.id,
        "tenant_id": tag.tenant_id,
        "name": tag.name,
        "description": tag.description,
        "color": tag.color,
        "is_active": tag.is_active,
        "created_at": tag.created_at.isoformat(),
        "updated_at": tag.updated_at.isoformat(),
    }


@router.get("/{client_id}/tags", summary="Get tags assigned to a client")
@readonly()
async def get_client_tags(
    client: ClientEntity = Depends(get_client_for_current_tenant),
    db: AsyncSession = Depends(get_db),
) -> list[dict[str, object]]:
    """Return the tenant-scoped tags assigned to a client."""
    tag_ids = select(ClientTagAssignmentModel.tag_id).where(
        ClientTagAssignmentModel.client_id == client.id.value,
        ClientTagAssignmentModel.tenant_id == client.tenant_id.value,
    )
    result = await db.execute(
        select(ClientTagModel)
        .where(ClientTagModel.id.in_(tag_ids), ClientTagModel.deleted_at.is_(None))
        .order_by(ClientTagModel.name.asc())
    )
    return [_tag_response(tag) for tag in result.scalars().all()]


@router.put("/{client_id}/tags", summary="Update tags assigned to a client")
@transactional()
async def update_client_tags(
    payload: ClientTagAssignmentRequest,
    request: Request,
    client: ClientEntity = Depends(get_client_for_current_tenant),
    current_user: TokenData = Depends(require_not_viewer),
    db: AsyncSession = Depends(get_db),
) -> list[dict[str, object]]:
    """Replace, add, or remove tags for one client."""
    tag_ids = set(payload.tag_ids)
    valid_tags = await db.execute(
        select(ClientTagModel.id).where(
            ClientTagModel.tenant_id == client.tenant_id.value,
            ClientTagModel.id.in_(tag_ids),
            ClientTagModel.deleted_at.is_(None),
        )
    )
    valid_ids = set(valid_tags.scalars().all())
    if valid_ids != tag_ids:
        raise HTTPException(status_code=400, detail="One or more tags were not found")
    assignment_filter = (
        ClientTagAssignmentModel.client_id == client.id.value,
        ClientTagAssignmentModel.tenant_id == client.tenant_id.value,
    )
    if payload.mode == "replace":
        await db.execute(delete(ClientTagAssignmentModel).where(*assignment_filter))
    elif payload.mode == "remove" and tag_ids:
        await db.execute(
            delete(ClientTagAssignmentModel).where(
                *assignment_filter, ClientTagAssignmentModel.tag_id.in_(tag_ids)
            )
        )
    if payload.mode in {"add", "replace"}:
        existing = await db.execute(
            select(ClientTagAssignmentModel.tag_id).where(*assignment_filter)
        )
        existing_ids = set(existing.scalars().all())
        now = utc_now()
        db.add_all(
            ClientTagAssignmentModel(
                id=generate_cuid(),
                tenant_id=client.tenant_id.value,
                client_id=client.id.value,
                tag_id=tag_id,
                created_at=now,
                updated_at=now,
            )
            for tag_id in sorted(tag_ids - existing_ids)
        )
    await db.flush()
    return await get_client_tags(client, db)


@router.post("/bulk/tags", summary="Apply tags to selected clients")
@transactional()
async def bulk_update_client_tags(
    payload: ClientBulkTagRequest,
    request: Request,
    tenant_id: str = Query(..., description="Tenant identifier"),
    current_user: TokenData = Depends(require_same_tenant),
    _write_access: TokenData = Depends(require_not_viewer),
    db: AsyncSession = Depends(get_db),
) -> dict[str, int]:
    """Apply one tag operation atomically across selected clients."""
    client_ids = set(payload.client_ids)
    tag_ids = set(payload.tag_ids)
    found_clients = await db.execute(
        select(ClientModel.id).where(
            ClientModel.tenant_id == tenant_id, ClientModel.id.in_(client_ids)
        )
    )
    if set(found_clients.scalars().all()) != client_ids:
        raise HTTPException(status_code=400, detail="One or more clients were not found")
    found_tags = await db.execute(
        select(ClientTagModel.id).where(
            ClientTagModel.tenant_id == tenant_id,
            ClientTagModel.id.in_(tag_ids),
            ClientTagModel.deleted_at.is_(None),
        )
    )
    if set(found_tags.scalars().all()) != tag_ids:
        raise HTTPException(status_code=400, detail="One or more tags were not found")
    assignment_filter = (
        ClientTagAssignmentModel.tenant_id == tenant_id,
        ClientTagAssignmentModel.client_id.in_(client_ids),
    )
    if payload.mode in {"remove", "replace"}:
        remove_filter = assignment_filter
        if payload.mode == "remove":
            remove_filter = (*assignment_filter, ClientTagAssignmentModel.tag_id.in_(tag_ids))
        await db.execute(delete(ClientTagAssignmentModel).where(*remove_filter))
    if payload.mode in {"add", "replace"}:
        existing = await db.execute(
            select(ClientTagAssignmentModel.client_id, ClientTagAssignmentModel.tag_id).where(
                *assignment_filter
            )
        )
        existing_pairs = set(existing.all())
        now = utc_now()
        db.add_all(
            ClientTagAssignmentModel(
                id=generate_cuid(),
                tenant_id=tenant_id,
                client_id=client_id,
                tag_id=tag_id,
                created_at=now,
                updated_at=now,
            )
            for client_id in client_ids
            for tag_id in tag_ids
            if (client_id, tag_id) not in existing_pairs
        )
    await db.flush()
    return {"clients_updated": len(client_ids), "tags_applied": len(tag_ids)}


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
