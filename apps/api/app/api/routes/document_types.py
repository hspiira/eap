"""Document type taxonomy routes.

Replaces the ``DocumentType`` enum, whose explicit ``OTHER`` member was
already evidence the fixed list was insufficient: a new type is now a row an
operator adds through this API, not a code deploy.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_document_type_repository
from app.api.schemas.document_type_schemas import (
    DocumentTypeCreate,
    DocumentTypeResponse,
    DocumentTypeUpdate,
)
from app.core.authorization import require_platform_admin
from app.core.database import get_db
from app.core.security import TokenData, get_current_user
from app.domain.repositories.document_type_repository import DocumentTypeRepository
from app.shared.decorators import readonly, transactional

router = APIRouter(prefix="/document-types", tags=["document-types"])


@router.get("", response_model=list[DocumentTypeResponse], summary="List document types")
@readonly()
async def list_document_types(
    active_only: bool = Query(True, description="Return only active types"),
    _user: TokenData = Depends(get_current_user),
    repo: DocumentTypeRepository = Depends(get_document_type_repository),
    db: AsyncSession = Depends(get_db),
):
    types = await repo.list_all(active_only=active_only)
    return [DocumentTypeResponse.model_validate(t) for t in types]


@router.post("", response_model=DocumentTypeResponse, status_code=status.HTTP_201_CREATED)
@transactional()
async def create_document_type(
    data: DocumentTypeCreate,
    _user: TokenData = Depends(require_platform_admin),
    repo: DocumentTypeRepository = Depends(get_document_type_repository),
    db: AsyncSession = Depends(get_db),
):
    if await repo.get_by_code(data.code):
        raise HTTPException(status.HTTP_409_CONFLICT, detail="Type code already exists")
    created = await repo.create(
        code=data.code, name=data.name, description=data.description, sort_order=data.sort_order
    )
    return DocumentTypeResponse.model_validate(created)


@router.patch("/{type_id}", response_model=DocumentTypeResponse)
@transactional()
async def update_document_type(
    type_id: str,
    data: DocumentTypeUpdate,
    _user: TokenData = Depends(require_platform_admin),
    repo: DocumentTypeRepository = Depends(get_document_type_repository),
    db: AsyncSession = Depends(get_db),
):
    updated = await repo.update(
        type_id, name=data.name, description=data.description, sort_order=data.sort_order
    )
    if updated is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Document type not found")
    return DocumentTypeResponse.model_validate(updated)


@router.post("/{type_id}/active", response_model=DocumentTypeResponse)
@transactional()
async def set_document_type_active(
    type_id: str,
    is_active: bool = Query(..., description="Activate or retire the type"),
    _user: TokenData = Depends(require_platform_admin),
    repo: DocumentTypeRepository = Depends(get_document_type_repository),
    db: AsyncSession = Depends(get_db),
):
    updated = await repo.set_active(type_id, is_active=is_active)
    if updated is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Document type not found")
    return DocumentTypeResponse.model_validate(updated)
