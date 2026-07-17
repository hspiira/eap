"""
Document Mapper

Converts between DocumentEntity (domain) and DocumentModel (persistence).
"""

from app.domain.entities.document import DocumentEntity
from app.domain.value_objects.core import DocumentId, TenantId, UserId
from app.infrastructure.models.document_model import DocumentModel
from app.shared.utils.datetime import ensure_utc


class DocumentMapper:
    """Mapper for DocumentEntity ↔ DocumentModel conversion"""

    @staticmethod
    def to_entity(model: DocumentModel) -> DocumentEntity:
        """
        Convert database model to domain entity.

        Args:
            model: DocumentModel from database

        Returns:
            DocumentEntity with business logic
        """
        # Reconstruct value objects
        document_id = DocumentId(model.id)
        tenant_id = TenantId(model.tenant_id)
        uploaded_by = UserId(model.uploaded_by) if model.uploaded_by else None
        previous_version_id = (
            DocumentId(model.previous_version_id) if model.previous_version_id else None
        )

        return DocumentEntity(
            id=document_id,
            tenant_id=tenant_id,
            name=model.name,
            document_type=model.document_type,
            status=model.status,
            version=model.version,
            is_latest=model.is_latest,
            description=model.description,
            file_path=model.file_path,
            file_url=model.file_url,
            file_size=model.file_size,
            mime_type=model.mime_type,
            previous_version_id=previous_version_id,
            uploaded_by=uploaded_by,
            client_id=model.client_id,
            contract_id=model.contract_id,
            person_id=model.person_id,
            expires_at=ensure_utc(model.expires_at) if model.expires_at else None,
            is_confidential=model.is_confidential,
            published_at=ensure_utc(model.published_at) if model.published_at else None,
            archived_at=ensure_utc(model.archived_at) if model.archived_at else None,
            created_at=ensure_utc(model.created_at),
            updated_at=ensure_utc(model.updated_at),
            deleted_at=ensure_utc(model.deleted_at) if model.deleted_at else None,
        )

    @staticmethod
    def to_model(entity: DocumentEntity) -> DocumentModel:
        """
        Convert domain entity to database model.

        Args:
            entity: DocumentEntity from domain

        Returns:
            DocumentModel for persistence
        """
        model = DocumentModel(
            id=entity.id.value,
            tenant_id=entity.tenant_id.value,
            name=entity.name,
            description=entity.description,
            document_type=entity.document_type,
            status=entity.status,
            version=entity.version,
            is_latest=entity.is_latest,
            file_path=entity.file_path,
            file_url=entity.file_url,
            file_size=entity.file_size,
            mime_type=entity.mime_type,
            previous_version_id=(
                entity.previous_version_id.value if entity.previous_version_id else None
            ),
            uploaded_by=entity.uploaded_by.value if entity.uploaded_by else None,
            client_id=entity.client_id,
            contract_id=entity.contract_id,
            person_id=entity.person_id,
            expires_at=ensure_utc(entity.expires_at) if entity.expires_at else None,
            is_confidential=entity.is_confidential,
            published_at=(ensure_utc(entity.published_at) if entity.published_at else None),
            archived_at=(ensure_utc(entity.archived_at) if entity.archived_at else None),
            created_at=ensure_utc(entity.created_at),
            updated_at=ensure_utc(entity.updated_at),
            deleted_at=ensure_utc(entity.deleted_at) if entity.deleted_at else None,
        )

        return model
