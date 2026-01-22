"""
Document API Routes

FastAPI routes for Document operations.
Follows hybrid approach: Commands use use cases, Queries use repositories directly.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_document_repository
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
    ArchiveDocumentUseCase,
    CreateDocumentUseCase,
    CreateDocumentVersionUseCase,
    GetDocumentUseCase,
    PublishDocumentUseCase,
    SetDocumentConfidentialityUseCase,
    SetDocumentExpiryUseCase,
    UpdateDocumentMetadataUseCase,
)
from app.core.database import get_db
from app.domain.enums import DocumentStatus, DocumentType
from app.domain.entities.document import DocumentEntity
from app.domain.exceptions import DomainError
from app.domain.repositories.document_repository import DocumentRepository
from app.domain.value_objects.core import DocumentId, TenantId, UserId
from app.shared.utils.generators import generate_cuid
from app.shared.utils.http_errors import get_error_status_code

router = APIRouter(prefix="/documents", tags=["documents"])


def _to_document_response(document: DocumentEntity) -> DocumentResponse:
    """Map DocumentEntity to API response."""
    return DocumentResponse(
        id=document._id.value,
        tenant_id=document._tenant_id.value,
        name=document._name,
        description=document._description,
        document_type=document._document_type,
        status=document._status,
        version=document._version,
        is_latest=document._is_latest,
        file_path=document._file_path,
        file_url=document._file_url,
        file_size=document._file_size,
        mime_type=document._mime_type,
        previous_version_id=(
            document._previous_version_id.value
            if document._previous_version_id
            else None
        ),
        uploaded_by=document._uploaded_by.value if document._uploaded_by else None,
        client_id=document._client_id,
        contract_id=document._contract_id,
        person_id=document._person_id,
        expires_at=document._expires_at,
        is_confidential=document._is_confidential,
        published_at=document._published_at,
        archived_at=document._archived_at,
        is_active=document.is_active(),
        created_at=document._created_at,
        updated_at=document._updated_at,
    )


# ==================== COMMANDS (Use Cases) ====================


@router.post(
    "/",
    response_model=DocumentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new document",
)
async def create_document(
    data: DocumentCreate,
    tenant_id: str = Query(..., description="Tenant identifier"),
    uploaded_by: str | None = Query(None, description="User ID who uploaded"),
    document_repo: DocumentRepository = Depends(get_document_repository),
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new document.

    This is a COMMAND operation, so it uses a use case for orchestration.
    """
    try:
        create_use_case = CreateDocumentUseCase(document_repo)

        document = await create_use_case.execute(
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

        await db.commit()

        return _to_document_response(document)
    except ValueError as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        ) from e
    except DomainError as e:
        await db.rollback()
        status_code = get_error_status_code(str(e))
        raise HTTPException(status_code=status_code, detail=str(e)) from e


@router.post(
    "/{document_id}/publish",
    response_model=DocumentResponse,
    summary="Publish a document",
)
async def publish_document(
    document_id: str,
    document_repo: DocumentRepository = Depends(get_document_repository),
    db: AsyncSession = Depends(get_db),
):
    """
    Publish a document (make it available).

    This is a COMMAND operation, so it uses a use case for orchestration.
    """
    try:
        publish_use_case = PublishDocumentUseCase(document_repo)

        document = await publish_use_case.execute(DocumentId(document_id))

        await db.commit()

        return _to_document_response(document)
    except ValueError as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(e)
        ) from e
    except DomainError as e:
        await db.rollback()
        status_code = get_error_status_code(str(e))
        raise HTTPException(status_code=status_code, detail=str(e)) from e


@router.post(
    "/{document_id}/archive",
    response_model=DocumentResponse,
    summary="Archive a document",
)
async def archive_document(
    document_id: str,
    document_repo: DocumentRepository = Depends(get_document_repository),
    db: AsyncSession = Depends(get_db),
):
    """
    Archive a document.

    This is a COMMAND operation, so it uses a use case for orchestration.
    """
    try:
        archive_use_case = ArchiveDocumentUseCase(document_repo)

        document = await archive_use_case.execute(DocumentId(document_id))

        await db.commit()

        return _to_document_response(document)
    except ValueError as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(e)
        ) from e
    except DomainError as e:
        await db.rollback()
        status_code = get_error_status_code(str(e))
        raise HTTPException(status_code=status_code, detail=str(e)) from e


@router.post(
    "/{document_id}/versions",
    response_model=DocumentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new document version",
)
async def create_document_version(
    document_id: str,
    data: DocumentCreateVersion,
    document_repo: DocumentRepository = Depends(get_document_repository),
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new version of a document.

    This is a COMMAND operation, so it uses a use case for orchestration.
    """
    try:
        create_version_use_case = CreateDocumentVersionUseCase(document_repo)

        document = await create_version_use_case.execute(
            document_id=DocumentId(document_id),
            new_version_id=DocumentId(generate_cuid()),
            name=data.name,
            description=data.description,
            file_path=data.file_path,
            file_url=data.file_url,
            file_size=data.file_size,
            mime_type=data.mime_type,
        )

        await db.commit()

        return _to_document_response(document)
    except ValueError as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        ) from e
    except DomainError as e:
        await db.rollback()
        status_code = get_error_status_code(str(e))
        raise HTTPException(status_code=status_code, detail=str(e)) from e


@router.patch(
    "/{document_id}",
    response_model=DocumentResponse,
    summary="Update document metadata",
)
async def update_document(
    document_id: str,
    data: DocumentUpdate,
    document_repo: DocumentRepository = Depends(get_document_repository),
    db: AsyncSession = Depends(get_db),
):
    """
    Update document metadata.

    This is a COMMAND operation, so it uses a use case for orchestration.
    """
    try:
        update_use_case = UpdateDocumentMetadataUseCase(document_repo)

        document = await update_use_case.execute(
            DocumentId(document_id),
            name=data.name,
            description=data.description,
        )

        await db.commit()

        return _to_document_response(document)
    except ValueError as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(e)
        ) from e
    except DomainError as e:
        await db.rollback()
        status_code = get_error_status_code(str(e))
        raise HTTPException(status_code=status_code, detail=str(e)) from e


@router.patch(
    "/{document_id}/confidentiality",
    response_model=DocumentResponse,
    summary="Set document confidentiality",
)
async def set_document_confidentiality(
    document_id: str,
    data: DocumentSetConfidentiality,
    document_repo: DocumentRepository = Depends(get_document_repository),
    db: AsyncSession = Depends(get_db),
):
    """
    Set document confidentiality.

    This is a COMMAND operation, so it uses a use case for orchestration.
    """
    try:
        set_confidentiality_use_case = SetDocumentConfidentialityUseCase(document_repo)

        document = await set_confidentiality_use_case.execute(
            DocumentId(document_id), data.is_confidential
        )

        await db.commit()

        return _to_document_response(document)
    except ValueError as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(e)
        ) from e
    except DomainError as e:
        await db.rollback()
        status_code = get_error_status_code(str(e))
        raise HTTPException(status_code=status_code, detail=str(e)) from e


@router.patch(
    "/{document_id}/expiry",
    response_model=DocumentResponse,
    summary="Set document expiry",
)
async def set_document_expiry(
    document_id: str,
    data: DocumentSetExpiry,
    document_repo: DocumentRepository = Depends(get_document_repository),
    db: AsyncSession = Depends(get_db),
):
    """
    Set document expiry date.

    This is a COMMAND operation, so it uses a use case for orchestration.
    """
    try:
        set_expiry_use_case = SetDocumentExpiryUseCase(document_repo)

        document = await set_expiry_use_case.execute(
            DocumentId(document_id), data.expires_at
        )

        await db.commit()

        return _to_document_response(document)
    except ValueError as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(e)
        ) from e
    except DomainError as e:
        await db.rollback()
        status_code = get_error_status_code(str(e))
        raise HTTPException(status_code=status_code, detail=str(e)) from e


# ==================== QUERIES (Direct Repository) ====================


@router.get(
    "/",
    response_model=DocumentListResponse,
    summary="List documents with filtering and pagination",
)
async def list_documents(
    tenant_id: str = Query(..., description="Tenant identifier"),
    document_type: DocumentType | None = Query(None, description="Filter by document type"),
    status: DocumentStatus | None = Query(None, description="Filter by document status"),
    client_id: str | None = Query(None, description="Filter by associated client"),
    contract_id: str | None = Query(None, description="Filter by associated contract"),
    person_id: str | None = Query(None, description="Filter by associated person"),
    is_confidential: bool | None = Query(None, description="Filter by confidentiality"),
    search: str | None = Query(None, description="Search in document name or description"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    sort_by: str = Query("created_at", description="Field to sort by"),
    sort_desc: bool = Query(True, description="Sort in descending order"),
    document_repo: DocumentRepository = Depends(get_document_repository),
):
    """
    List documents with filtering, searching, and pagination.

    This is a QUERY operation, so it calls the repository directly.
    Only latest versions are returned.
    """
    offset = (page - 1) * limit

    documents = await document_repo.list_all(
        tenant_id=TenantId(tenant_id),
        document_type=document_type,
        status=status,
        client_id=client_id,
        contract_id=contract_id,
        person_id=person_id,
        is_confidential=is_confidential,
        search=search,
        limit=limit,
        offset=offset,
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

    document_responses = [_to_document_response(doc) for doc in documents]

    return DocumentListResponse(
        items=document_responses,
        total=total,
        page=page,
        limit=limit,
        has_more=(offset + limit) < total,
    )


@router.get(
    "/{document_id}",
    response_model=DocumentResponse,
    summary="Get document by ID",
)
async def get_document(
    document_id: str,
    document_repo: DocumentRepository = Depends(get_document_repository),
):
    """
    Get document by ID.

    This is a QUERY operation, so it calls the repository directly.
    """
    get_use_case = GetDocumentUseCase(document_repo)

    document = await get_use_case.execute(DocumentId(document_id))

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Document not found"
        )

    return _to_document_response(document)


@router.get(
    "/{document_id}/versions",
    response_model=DocumentVersionResponse,
    summary="Get document version history",
)
async def get_document_versions(
    document_id: str,
    tenant_id: str = Query(..., description="Tenant identifier"),
    document_repo: DocumentRepository = Depends(get_document_repository),
):
    """
    Get all versions of a document.

    This is a QUERY operation, so it calls the repository directly.
    """
    versions = await document_repo.get_versions(
        DocumentId(document_id), TenantId(tenant_id)
    )

    version_responses = [_to_document_response(version) for version in versions]

    return DocumentVersionResponse(
        versions=version_responses, total=len(version_responses)
    )


@router.get(
    "/{document_id}/latest",
    response_model=DocumentResponse,
    summary="Get latest version of a document",
)
async def get_latest_document_version(
    document_id: str,
    tenant_id: str = Query(..., description="Tenant identifier"),
    document_repo: DocumentRepository = Depends(get_document_repository),
):
    """
    Get the latest version of a document.

    This is a QUERY operation, so it calls the repository directly.
    """
    latest = await document_repo.get_latest_version(
        DocumentId(document_id), TenantId(tenant_id)
    )

    if not latest:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Document not found"
        )

    return _to_document_response(latest)
