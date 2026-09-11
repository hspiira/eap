"""Database model for restricted member next-of-kin contacts."""

from sqlalchemy import Boolean, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.models.base import (
    Base,
    CuidMixin,
    TenantMixin,
    TimestampMixin,
)


class MemberNextOfKinModel(CuidMixin, TenantMixin, Base, TimestampMixin):
    __tablename__ = "member_next_of_kin"

    member_id: Mapped[str] = mapped_column(
        ForeignKey("eligible_members.id", ondelete="CASCADE"), nullable=False, index=True
    )
    # Encrypted at rest; no blind index (no exact-match or sort lookup on the
    # raw column, see MemberNextOfKinRepositoryImpl.list_for_member).
    name: Mapped[str] = mapped_column(Text, nullable=False)
    relationship: Mapped[str] = mapped_column(
        String(50), ForeignKey("next_of_kin_relationships.code"), nullable=False
    )
    phone: Mapped[str | None] = mapped_column(Text, nullable=True)
    email: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_primary: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, index=True)
