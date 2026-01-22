"""
Document Repository Implementation

SQLAlchemy implementation of DocumentRepository interface.
Uses TenantScopedRepositoryImpl base class to eliminate boilerplate.
"""

from typing import Any, Sequence

from sqlalchemy import func, or_, select

from app.domain.entities.document import DocumentEntity
from app.domain.enums import DocumentStatus, DocumentType
from app.domain.repositories.document_repository import DocumentRepository
from app.domain.value_objects.core import DocumentId, TenantId
from app.infrastructure.mappers.document_mapper import DocumentMapper
from app.infrastructure.models.document_model import DocumentModel
from app.infrastructure.repositories.base import TenantScopedRepositoryImpl


class DocumentRepositoryImpl(TenantScopedRepositoryImpl[DocumentEntity, DocumentModel, DocumentId], DocumentRepository):
    """
    SQLAlchemy implementation of DocumentRepository.

    Inherits common CRUD operations from TenantScopedRepositoryImpl.
    Only implements domain-specific queries.
    """

    model_class = DocumentModel
    id_column = "id"

    def _to_entity(self, model: DocumentModel) -> DocumentEntity:
        """Convert model to entity."""
        return DocumentMapper.to_entity(model)

    def _to_model(self, entity: DocumentEntity) -> DocumentModel:
        """Convert entity to model."""
        return DocumentMapper.to_model(entity)

    def _get_id_value(self, entity_id: DocumentId) -> Any:
        """Extract raw ID value."""
        return entity_id.value

    # Domain-specific queries (not in base class)

    async def get_versions(
        self, document_id: DocumentId, tenant_id: TenantId
    ) -> Sequence[DocumentEntity]:
        """Get all versions of a document."""
        # Find the original document (version 1 or the one without previous_version_id)
        original = await self.get_by_id(document_id)
        if not original:
            return []

        # Get all versions by following the version chain
        versions = []
        current_id = document_id

        while current_id:
            doc = await self.get_by_id(current_id)
            if not doc or doc.tenant_id != tenant_id:
                break
            versions.append(doc)
            # Find next version (where previous_version_id == current_id)
            stmt = select(DocumentModel).where(
                DocumentModel.previous_version_id == current_id.value,
                DocumentModel.tenant_id == tenant_id.value,
                DocumentModel.deleted_at.is_(None),
            )
            result = await self.session.execute(stmt)
            next_model = result.scalar_one_or_none()
            if next_model:
                current_id = DocumentId(next_model.id)
            else:
                current_id = None

        # Also get previous versions (where current_id is previous_version_id)
        current_id = document_id
        while current_id:
            stmt = select(DocumentModel).where(
                DocumentModel.id == current_id.value,
                DocumentModel.tenant_id == tenant_id.value,
                DocumentModel.deleted_at.is_(None),
            )
            result = await self.session.execute(stmt)
            model = result.scalar_one_or_none()
            if not model or not model.previous_version_id:
                break
            prev_id = DocumentId(model.previous_version_id)
            prev_doc = await self.get_by_id(prev_id)
            if prev_doc:
                versions.insert(0, prev_doc)
            current_id = prev_id

        # Sort by version number
        versions.sort(key=lambda d: d.version)
        return versions

    async def get_latest_version(
        self, document_id: DocumentId, tenant_id: TenantId
    ) -> DocumentEntity | None:
        """Get the latest version of a document."""
        # Start with the given document ID
        current = await self.get_by_id(document_id)
        if not current or current.tenant_id != tenant_id:
            return None

        # Follow the version chain to find the latest
        while True:
            stmt = select(DocumentModel).where(
                DocumentModel.previous_version_id == current.id.value,
                DocumentModel.tenant_id == tenant_id.value,
                DocumentModel.deleted_at.is_(None),
            )
            result = await self.session.execute(stmt)
            next_model = result.scalar_one_or_none()
            if next_model:
                current = self._to_entity(next_model)
            else:
                break

        return current

    async def list_all(
        self,
        tenant_id: TenantId,
        document_type: DocumentType | None = None,
        status: DocumentStatus | None = None,
        client_id: str | None = None,
        contract_id: str | None = None,
        person_id: str | None = None,
        is_confidential: bool | None = None,
        search: str | None = None,
        limit: int = 100,
        offset: int = 0,
        sort_by: str = "created_at",
        sort_desc: bool = True,
    ) -> Sequence[DocumentEntity]:
        """List documents with filtering, searching, and pagination."""
        stmt = select(DocumentModel).where(
            DocumentModel.tenant_id == tenant_id.value,
            DocumentModel.deleted_at.is_(None),
            DocumentModel.is_latest == True,  # Only latest versions
        )

        # Apply filters
        if document_type:
            stmt = stmt.where(DocumentModel.document_type == document_type)
        if status:
            stmt = stmt.where(DocumentModel.status == status)
        if client_id:
            stmt = stmt.where(DocumentModel.client_id == client_id)
        if contract_id:
            stmt = stmt.where(DocumentModel.contract_id == contract_id)
        if person_id:
            stmt = stmt.where(DocumentModel.person_id == person_id)
        if is_confidential is not None:
            stmt = stmt.where(DocumentModel.is_confidential == is_confidential)
        if search:
            search_pattern = f"%{search.lower()}%"
            stmt = stmt.where(
                or_(
                    DocumentModel.name.ilike(search_pattern),
                    DocumentModel.description.ilike(search_pattern),
                )
            )

        # Apply sorting
        sort_column = getattr(DocumentModel, sort_by, DocumentModel.created_at)
        if sort_desc:
            stmt = stmt.order_by(sort_column.desc())
        else:
            stmt = stmt.order_by(sort_column.asc())

        # Apply pagination
        stmt = stmt.limit(limit).offset(offset)

        result = await self.session.execute(stmt)
        models = result.scalars().all()

        return [self._to_entity(model) for model in models]

    async def count(
        self,
        tenant_id: TenantId,
        document_type: DocumentType | None = None,
        status: DocumentStatus | None = None,
        client_id: str | None = None,
        contract_id: str | None = None,
        person_id: str | None = None,
        is_confidential: bool | None = None,
        search: str | None = None,
    ) -> int:
        """Count documents matching filters."""
        stmt = select(func.count(DocumentModel.id)).where(
            DocumentModel.tenant_id == tenant_id.value,
            DocumentModel.deleted_at.is_(None),
            DocumentModel.is_latest == True,  # Only latest versions
        )

        # Apply filters
        if document_type:
            stmt = stmt.where(DocumentModel.document_type == document_type)
        if status:
            stmt = stmt.where(DocumentModel.status == status)
        if client_id:
            stmt = stmt.where(DocumentModel.client_id == client_id)
        if contract_id:
            stmt = stmt.where(DocumentModel.contract_id == contract_id)
        if person_id:
            stmt = stmt.where(DocumentModel.person_id == person_id)
        if is_confidential is not None:
            stmt = stmt.where(DocumentModel.is_confidential == is_confidential)
        if search:
            search_pattern = f"%{search.lower()}%"
            stmt = stmt.where(
                or_(
                    DocumentModel.name.ilike(search_pattern),
                    DocumentModel.description.ilike(search_pattern),
                )
            )

        result = await self.session.execute(stmt)
        return int(result.scalar() or 0)
