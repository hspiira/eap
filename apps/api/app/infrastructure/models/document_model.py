"""
Document SQLAlchemy Model

Database representation of Document aggregate.
This is a data container only - no business logic.
"""

from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.domain.enums import DocumentStatus
from app.infrastructure.models.base import (
    Base,
    CuidMixin,
    EnumValueType,
    SoftDeleteMixin,
    TenantMixin,
    TimestampMixin,
)


class DocumentModel(CuidMixin, TenantMixin, Base, TimestampMixin, SoftDeleteMixin):
    """
    SQLAlchemy Model for Document aggregate.

    This is a data container for persistence only.
    Business logic lives in DocumentEntity.
    """

    __tablename__ = "documents"
    __table_args__ = (
        CheckConstraint(
            "status IN (" + ", ".join(f"'{e.value}'" for e in DocumentStatus) + ")",
            name="document_status_check",
        ),
        CheckConstraint(
            "(file_path IS NOT NULL) OR (file_url IS NOT NULL)",
            name="document_file_or_url_check",
        ),
    )

    # Core attributes
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    document_type: Mapped[str] = mapped_column(
        String(50), ForeignKey("document_types.code"), nullable=False, index=True
    )
    status: Mapped[DocumentStatus] = mapped_column(
        EnumValueType(DocumentStatus), nullable=False, default=DocumentStatus.DRAFT
    )

    # File information
    file_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    file_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    file_size: Mapped[int | None] = mapped_column(Integer, nullable=True)
    mime_type: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # Versioning
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    is_latest: Mapped[bool] = mapped_column(default=True, nullable=False, index=True)
    previous_version_id: Mapped[str | None] = mapped_column(
        ForeignKey("documents.id"), nullable=True
    )

    # Associations
    uploaded_by: Mapped[str | None] = mapped_column(
        ForeignKey("users.id"), nullable=True, index=True
    )
    client_id: Mapped[str | None] = mapped_column(
        ForeignKey("clients.id"), nullable=True, index=True
    )
    contract_id: Mapped[str | None] = mapped_column(
        ForeignKey("contracts.id"), nullable=True, index=True
    )
    person_id: Mapped[str | None] = mapped_column(
        ForeignKey("persons.id"), nullable=True, index=True
    )

    # Lifecycle
    expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, index=True
    )
    is_confidential: Mapped[bool] = mapped_column(default=False, nullable=False)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    archived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    def __repr__(self) -> str:
        return f"<DocumentModel(id={self.id}, name={self.name}, version={self.version})>"
