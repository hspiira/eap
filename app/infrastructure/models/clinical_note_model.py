"""Clinical note model — body fields are encrypted at rest."""

from datetime import datetime, timedelta
from typing import Any

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import JSONB
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
    clinical_subject_id: Mapped[str] = mapped_column(
        String(25), nullable=False, index=True
    )
    note_type: Mapped[ClinicalNoteType] = mapped_column(
        EnumValueType(ClinicalNoteType), nullable=False, index=True
    )
    body: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    author_id: Mapped[str] = mapped_column(
        String(25), nullable=False, index=True
    )
    session_id: Mapped[str | None] = mapped_column(
        String(25), nullable=True, index=True
    )
    signed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    signed_by: Mapped[str | None] = mapped_column(String(25), nullable=True)
    locked_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    lock_window_seconds: Mapped[int] = mapped_column(
        Integer, nullable=False, default=int(timedelta(days=7).total_seconds())
    )
    amendments: Mapped[list[dict[str, Any]]] = mapped_column(
        JSONB, nullable=False, server_default="[]"
    )
