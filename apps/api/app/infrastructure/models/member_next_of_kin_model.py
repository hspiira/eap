"""Database model for restricted member next-of-kin contacts."""

from sqlalchemy import Boolean, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.domain.enums import NextOfKinRelationship
from app.infrastructure.models.base import (
    Base,
    CuidMixin,
    EnumValueType,
    TenantMixin,
    TimestampMixin,
)


class MemberNextOfKinModel(CuidMixin, TenantMixin, Base, TimestampMixin):
    __tablename__ = "member_next_of_kin"

    member_id: Mapped[str] = mapped_column(
        ForeignKey("eligible_members.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    relationship: Mapped[NextOfKinRelationship] = mapped_column(
        EnumValueType(NextOfKinRelationship), nullable=False
    )
    phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_primary: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, index=True)
