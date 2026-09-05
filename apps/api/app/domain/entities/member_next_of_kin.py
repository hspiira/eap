"""Restricted next-of-kin contact for a covered member."""

from dataclasses import dataclass
from datetime import datetime

from app.domain.enums import NextOfKinRelationship
from app.domain.exceptions import DomainError
from app.domain.value_objects.core import EligibleMemberId, Email, MemberNextOfKinId, TenantId


@dataclass
class MemberNextOfKin:
    id: MemberNextOfKinId
    tenant_id: TenantId
    member_id: EligibleMemberId
    name: str
    relationship: NextOfKinRelationship
    phone: str | None
    email: Email | None
    is_primary: bool
    created_at: datetime
    updated_at: datetime

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise DomainError("Next-of-kin name is required")
        if not self.phone and not self.email:
            raise DomainError("Next-of-kin needs phone or email")

    def update(
        self,
        *,
        name: str,
        relationship: NextOfKinRelationship,
        phone: str | None,
        email: Email | None,
        is_primary: bool,
        now: datetime,
    ) -> None:
        if not name.strip():
            raise DomainError("Next-of-kin name is required")
        if not phone and not email:
            raise DomainError("Next-of-kin needs phone or email")
        self.name = name
        self.relationship = relationship
        self.phone = phone
        self.email = email
        self.is_primary = is_primary
        self.updated_at = now
