"""Mapper for restricted member next-of-kin contacts."""

from app.domain.entities.member_next_of_kin import MemberNextOfKin
from app.domain.enums import NextOfKinRelationship
from app.domain.value_objects.core import EligibleMemberId, Email, MemberNextOfKinId, TenantId
from app.infrastructure.models.member_next_of_kin_model import MemberNextOfKinModel
from app.shared.utils.datetime import ensure_utc


class MemberNextOfKinMapper:
    @staticmethod
    def to_entity(model: MemberNextOfKinModel) -> MemberNextOfKin:
        return MemberNextOfKin(
            id=MemberNextOfKinId(model.id),
            tenant_id=TenantId(model.tenant_id),
            member_id=EligibleMemberId(model.member_id),
            name=model.name,
            relationship=NextOfKinRelationship(model.relationship),
            phone=model.phone,
            email=Email(model.email) if model.email else None,
            is_primary=model.is_primary,
            created_at=ensure_utc(model.created_at),
            updated_at=ensure_utc(model.updated_at),
        )

    @staticmethod
    def to_model(entity: MemberNextOfKin) -> MemberNextOfKinModel:
        return MemberNextOfKinModel(
            id=entity.id.value,
            tenant_id=entity.tenant_id.value,
            member_id=entity.member_id.value,
            name=entity.name,
            relationship=entity.relationship,
            phone=entity.phone,
            email=entity.email.value if entity.email else None,
            is_primary=entity.is_primary,
            created_at=ensure_utc(entity.created_at),
            updated_at=ensure_utc(entity.updated_at),
        )
