"""
Document API Routes

FastAPI routes for Document operations.
Refactored to use @transactional decorator to eliminate try/except boilerplate.
"""

from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import (
    PageParams,
    get_audit_event_handler,
    get_document_repository,
    pagination,
)
from app.api.schemas.document_schemas import (
    DocumentCreate,
    DocumentCreateVersion,
    DocumentListResponse,
    DocumentResponse,
    DocumentSetConfidentiality,
    DocumentSetExpiry,
    DocumentUpdate,
    DocumentVersionResponse,
)
from app.application.use_cases.document_use_cases import (
    CreateDocumentUseCase,
    CreateDocumentVersionUseCase,
    SetDocumentConfidentialityUseCase,
    SetDocumentExpiryUseCase,
    UpdateDocumentMetadataUseCase,
)
from app.application.use_cases.transitions import (
    DocumentTransition,
    TransitionUseCase,
)
from app.core.authorization import (
    get_document_for_current_tenant,
    require_same_tenant,
)
from app.core.database import get_db
from app.core.security import TokenData, get_current_user
from app.domain.entities.document import DocumentEntity
from app.domain.enums import DocumentStatus, DocumentType
from app.domain.repositories.document_repository import DocumentRepository
from app.domain.value_objects.core import DocumentId, TenantId, UserId
from app.shared.decorators import readonly, transactional
from app.shared.utils.generators import generate_cuid
from app.shared.utils.route_audit_helper import audit_change

router = APIRouter(prefix="/documents", tags=["documents"])


def _to_document_response(document: DocumentEntity) -> DocumentResponse:
    """Map DocumentEntity to API response using public properties."""
    return DocumentResponse(
        id=document.id.value,
        tenant_id=document.tenant_id.value,
        name=document.name,
        description=document.description,
        document_type=document.document_type,
        status=document.status,
        version=document.version,
        is_latest=document.is_latest,
        file_path=document.file_path,
        file_url=document.file_url,
        file_size=document.file_size,
        mime_type=document.mime_type,
        previous_version_id=(
            document.previous_version_id.value
            if document.previous_version_id
            else None
        ),
        uploaded_by=document.uploaded_by.value if document.uploaded_by else None,
        client_id=document.client_id,
        contract_id=document.contract_id,
        person_id=document.person_id,
        expires_at=document.expires_at,
        is_confidential=document.is_confidential,
        published_at=document.published_at,
        archived_at=document.archived_at,
        is_active=document.is_active(),
        created_at=document.created_at,
        updated_at=document.updated_at,
    )


# ==================== COMMANDS (Use Cases) ====================


@router.post(
    "/",
    response_model=DocumentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new document",
)
@transactional()
async def create_document(
    data: DocumentCreate,
    request: Request,
    tenant_id: str = Query(..., description="Tenant identifier"),
    uploaded_by: str | None = Query(None, description="User ID who uploaded"),
    current_user: TokenData = Depends(require_same_tenant),
    document_repo: DocumentRepository = Depends(get_document_repository),
    audit_handler=Depends(get_audit_event_handler),
    db: AsyncSession = Depends(get_db),
):
    """Create a new document."""
    document = await CreateDocumentUseCase(document_repo).execute(
        document_id=DocumentId(generate_cuid()),
        tenant_id=TenantId(tenant_id),
        name=data.name,
        document_type=data.document_type,
        file_path=data.file_path,
        file_url=data.file_url,
        file_size=data.file_size,
        mime_type=data.mime_type,
        description=data.description,
        uploaded_by=UserId(uploaded_by) if uploaded_by else None,
        client_id=data.client_id,
        contract_id=data.contract_id,
        person_id=data.person_id,
        expires_at=data.expires_at,
        is_confidential=data.is_confidential,
    )
    await audit_change(document, audit_handler, current_user, request, tenant_id=tenant_id)
    return _to_document_response(document)


@router.post(
    "/{document_id}/publish",
    response_model=DocumentResponse,
    summary="Publish a document",
)
@transactional()
async def publish_document(
    request: Request,
    current_user: TokenData = Depends(get_current_user),
    document: DocumentEntity = Depends(get_document_for_current_tenant),
    document_repo: DocumentRepository = Depends(get_document_repository),
    audit_handler=Depends(get_audit_event_handler),
    db: AsyncSession = Depends(get_db),
):
    """Publish a document (make it available)."""
    use_case = TransitionUseCase(document_repo, "Document")
    updated = await use_case.execute(document.id, DocumentTransition.PUBLISH)
    await audit_change(updated, audit_handler, current_user, request)
    return _to_document_response(updated)


@router.post(
    "/{document_id}/archive",
    response_model=DocumentResponse,
    summary="Archive a document",
)
@transactional()
async def archive_document(
    request: Request,
    current_user: TokenData = Depends(get_current_user),
    document: DocumentEntity = Depends(get_document_for_current_tenant),
    document_repo: DocumentRepository = Depends(get_document_repository),
    audit_handler=Depends(get_audit_event_handler),
    db: AsyncSession = Depends(get_db),
):
    """Archive a document."""
    use_case = TransitionUseCase(document_repo, "Document")
    updated = await use_case.execute(document.id, DocumentTransition.ARCHIVE)
    await audit_change(updated, audit_handler, current_user, request)
    return _to_document_response(updated)


@router.post(
    "/{document_id}/versions",
    response_model=DocumentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new document version",
)
@transactional()
async def create_document_version(
    data: DocumentCreateVersion,
    request: Request,
    current_user: TokenData = Depends(get_current_user),
    document: DocumentEntity = Depends(get_document_for_current_tenant),
    document_repo: DocumentRepository = Depends(get_document_repository),
    audit_handler=Depends(get_audit_event_handler),
    db: AsyncSession = Depends(get_db),
):
    """Create a new version of a document."""
    updated = await CreateDocumentVersionUseCase(document_repo).execute(
        document_id=document.id,
        new_version_id=DocumentId(generate_cuid()),
        name=data.name,
        description=data.description,
        file_path=data.file_path,
        file_url=data.file_url,
        file_size=data.file_size,
        mime_type=data.mime_type,
    )
    await audit_change(updated, audit_handler, current_user, request)
    return _to_document_response(updated)


@router.patch(
    "/{document_id}",
    response_model=DocumentResponse,
    summary="Update document metadata",
)
@transactional()
async def update_document(
    data: DocumentUpdate,
    request: Request,
    current_user: TokenData = Depends(get_current_user),
    document: DocumentEntity = Depends(get_document_for_current_tenant),
    document_repo: DocumentRepository = Depends(get_document_repository),
    audit_handler=Depends(get_audit_event_handler),
    db: AsyncSession = Depends(get_db),
):
    """Update document metadata."""
    updated = await UpdateDocumentMetadataUseCase(document_repo).execute(
        document.id,
        name=data.name,
        description=data.description,
    )
    await audit_change(updated, audit_handler, current_user, request)
    return _to_document_response(updated)


@router.patch(
    "/{document_id}/confidentiality",
    response_model=DocumentResponse,
    summary="Set document confidentiality",
)
@transactional()
async def set_document_confidentiality(
    data: DocumentSetConfidentiality,
    request: Request,
    current_user: TokenData = Depends(get_current_user),
    document: DocumentEntity = Depends(get_document_for_current_tenant),
    document_repo: DocumentRepository = Depends(get_document_repository),
    audit_handler=Depends(get_audit_event_handler),
    db: AsyncSession = Depends(get_db),
):
    """Set document confidentiality."""
    updated = await SetDocumentConfidentialityUseCase(document_repo).execute(
        document.id, data.is_confidential
    )
    await audit_change(updated, audit_handler, current_user, request)
    return _to_document_response(updated)


@router.patch(
    "/{document_id}/expiry",
    response_model=DocumentResponse,
    summary="Set document expiry",
)
@transactional()
async def set_document_expiry(
    data: DocumentSetExpiry,
    request: Request,
    current_user: TokenData = Depends(get_current_user),
    document: DocumentEntity = Depends(get_document_for_current_tenant),
    document_repo: DocumentRepository = Depends(get_document_repository),
    audit_handler=Depends(get_audit_event_handler),
    db: AsyncSession = Depends(get_db),
):
    """Set document expiry date."""
    updated = await SetDocumentExpiryUseCase(document_repo).execute(
        document.id, data.expires_at
    )
    await audit_change(updated, audit_handler, current_user, request)
    return _to_document_response(updated)


# ==================== QUERIES (Direct Repository) ====================


@router.get(
    "/",
    response_model=DocumentListResponse,
    summary="List documents with filtering and pagination",
)
@readonly()
async def list_documents(
    tenant_id: str = Query(..., description="Tenant identifier"),
    current_user: TokenData = Depends(require_same_tenant),
    document_type: DocumentType | None = Query(None, description="Filter by document type"),
    status: DocumentStatus | None = Query(None, description="Filter by document status"),
    client_id: str | None = Query(None, description="Filter by associated client"),
    contract_id: str | None = Query(None, description="Filter by associated contract"),
    person_id: str | None = Query(None, description="Filter by associated person"),
    is_confidential: bool | None = Query(None, description="Filter by confidentiality"),
    search: str | None = Query(None, description="Search in document name or description"),
    pg: PageParams = Depends(pagination()),
    sort_by: str = Query("created_at", description="Field to sort by"),
    sort_desc: bool = Query(True, description="Sort in descending order"),
    document_repo: DocumentRepository = Depends(get_document_repository),
    db: AsyncSession = Depends(get_db),
):
    """List documents with filtering, searching, and pagination."""

    documents = await document_repo.list_all(
        tenant_id=TenantId(tenant_id),
        document_type=document_type,
        status=status,
        client_id=client_id,
        contract_id=contract_id,
        person_id=person_id,
        is_confidential=is_confidential,
        search=search,
        limit=pg.limit,
        offset=pg.offset,
        sort_by=sort_by,
        sort_desc=sort_desc,
    )

    total = await document_repo.count(
        tenant_id=TenantId(tenant_id),
        document_type=document_type,
        status=status,
        client_id=client_id,
        contract_id=contract_id,
        person_id=person_id,
        is_confidential=is_confidential,
        search=search,
    )

    return DocumentListResponse(
        items=[_to_document_response(doc) for doc in documents],
        total=total,
        page=pg.page,
        limit=pg.limit,
        has_more=(pg.offset + pg.limit) < total,
    )


@router.get(
    "/{document_id}",
    response_model=DocumentResponse,
    summary="Get document by ID",
)
@readonly()
async def get_document(
    document: DocumentEntity = Depends(get_document_for_current_tenant),
    db: AsyncSession = Depends(get_db),
):
    """Get document by ID."""
    return _to_document_response(document)


@router.get(
    "/{document_id}/versions",
    response_model=DocumentVersionResponse,
    summary="Get document version history",
)
@readonly()
async def get_document_versions(
    document_id: str,
    tenant_id: str = Query(..., description="Tenant identifier"),
    current_user: TokenData = Depends(require_same_tenant),
    document_repo: DocumentRepository = Depends(get_document_repository),
    db: AsyncSession = Depends(get_db),
):
    """Get all versions of a document."""
    versions = await document_repo.get_versions(
        DocumentId(document_id), TenantId(tenant_id)
    )
    return DocumentVersionResponse(
        versions=[_to_document_response(version) for version in versions],
        total=len(versions),
    )


@router.get(
    "/{document_id}/latest",
    response_model=DocumentResponse,
    summary="Get latest version of a document",
)
@readonly()
async def get_latest_document_version(
    document_id: str,
    tenant_id: str = Query(..., description="Tenant identifier"),
    current_user: TokenData = Depends(require_same_tenant),
    document_repo: DocumentRepository = Depends(get_document_repository),
    db: AsyncSession = Depends(get_db),
):
    """Get the latest version of a document."""
    latest = await document_repo.get_latest_version(
        DocumentId(document_id), TenantId(tenant_id)
    )
    if not latest:
        raise ValueError("Document not found")
    return _to_document_response(latest)
