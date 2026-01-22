"""
Document Mapper

Converts between DocumentEntity (domain) and DocumentModel (persistence).
"""

from app.domain.entities.document import DocumentEntity
from app.domain.enums import DocumentStatus, DocumentType
from app.domain.value_objects.core import DocumentId, TenantId, UserId
from app.infrastructure.models.document_model import DocumentModel
from app.shared.utils.datetime import ensure_utc, utc_now


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
            _id=document_id,
            _tenant_id=tenant_id,
            _name=model.name,
            _document_type=model.document_type,
            _status=model.status,
            _version=model.version,
            _is_latest=model.is_latest,
            _description=model.description,
            _file_path=model.file_path,
            _file_url=model.file_url,
            _file_size=model.file_size,
            _mime_type=model.mime_type,
            _previous_version_id=previous_version_id,
            _uploaded_by=uploaded_by,
            _client_id=model.client_id,
            _contract_id=model.contract_id,
            _person_id=model.person_id,
            _expires_at=ensure_utc(model.expires_at) if model.expires_at else None,
            _is_confidential=model.is_confidential,
            _published_at=ensure_utc(model.published_at) if model.published_at else None,
            _archived_at=ensure_utc(model.archived_at) if model.archived_at else None,
            _created_at=ensure_utc(model.created_at),
            _updated_at=ensure_utc(model.updated_at),
            _deleted_at=ensure_utc(model.deleted_at) if model.deleted_at else None,
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
            id=entity._id.value,
            tenant_id=entity._tenant_id.value,
            name=entity._name,
            description=entity._description,
            document_type=entity._document_type,
            status=entity._status,
            version=entity._version,
            is_latest=entity._is_latest,
            file_path=entity._file_path,
            file_url=entity._file_url,
            file_size=entity._file_size,
            mime_type=entity._mime_type,
            previous_version_id=(
                entity._previous_version_id.value
                if entity._previous_version_id
                else None
            ),
            uploaded_by=entity._uploaded_by.value if entity._uploaded_by else None,
            client_id=entity._client_id,
            contract_id=entity._contract_id,
            person_id=entity._person_id,
            expires_at=ensure_utc(entity._expires_at) if entity._expires_at else None,
            is_confidential=entity._is_confidential,
            published_at=(
                ensure_utc(entity._published_at) if entity._published_at else None
            ),
            archived_at=(
                ensure_utc(entity._archived_at) if entity._archived_at else None
            ),
            created_at=ensure_utc(entity._created_at),
            updated_at=ensure_utc(entity._updated_at),
            deleted_at=ensure_utc(entity._deleted_at) if entity._deleted_at else None,
        )

        return model
