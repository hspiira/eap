"""Clinical note model; body fields are encrypted at rest."""

from datetime import datetime, timedelta

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.domain.enums import ClinicalNoteType
from app.infrastructure.models.base import (
    Base,
    CuidMixin,
    EnumValueType,
    TenantMixin,
    TimestampMixin,
)


class ClinicalNoteModel(CuidMixin, TenantMixin, Base, TimestampMixin):
    __tablename__ = "clinical_notes"

    case_id: Mapped[str] = mapped_column(
        ForeignKey("cases.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    clinical_subject_id: Mapped[str] = mapped_column(String(25), nullable=False, index=True)
    note_type: Mapped[ClinicalNoteType] = mapped_column(
        EnumValueType(ClinicalNoteType), nullable=False, index=True
    )
    # Encrypted at rest (app/core/encryption.py): stores ciphertext of the
    # JSON-serialised body, not queryable JSON. See ClinicalNoteMapper for
    # the dict <-> ciphertext conversion.
    body: Mapped[str] = mapped_column(Text, nullable=False)
    author_id: Mapped[str] = mapped_column(String(25), nullable=False, index=True)
    session_id: Mapped[str | None] = mapped_column(String(25), nullable=True, index=True)
    signed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    signed_by: Mapped[str | None] = mapped_column(String(25), nullable=True)
    locked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    lock_window_seconds: Mapped[int] = mapped_column(
        Integer, nullable=False, default=int(timedelta(days=7).total_seconds())
    )
    # Encrypted at rest, same as body; no server_default, since a literal
    # "[]" would not be valid ciphertext. The mapper always supplies a value.
    amendments: Mapped[str] = mapped_column(Text, nullable=False)
