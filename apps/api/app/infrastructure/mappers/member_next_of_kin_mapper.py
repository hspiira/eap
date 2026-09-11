"""Mapper for restricted member next-of-kin contacts."""

from app.core.encryption import decrypt, encrypt
from app.domain.entities.member_next_of_kin import MemberNextOfKin
from app.domain.value_objects.core import EligibleMemberId, Email, MemberNextOfKinId, TenantId
from app.infrastructure.models.member_next_of_kin_model import MemberNextOfKinModel
from app.shared.utils.datetime import ensure_utc


class MemberNextOfKinMapper:
    @staticmethod
    def to_entity(model: MemberNextOfKinModel) -> MemberNextOfKin:
        tenant_id = model.tenant_id
        email = decrypt(model.email, tenant_id=tenant_id)
        return MemberNextOfKin(
            id=MemberNextOfKinId(model.id),
            tenant_id=TenantId(tenant_id),
            member_id=EligibleMemberId(model.member_id),
            name=decrypt(model.name, tenant_id=tenant_id),
            relationship=model.relationship,
            phone=decrypt(model.phone, tenant_id=tenant_id),
            email=Email(email) if email else None,
            is_primary=model.is_primary,
            created_at=ensure_utc(model.created_at),
            updated_at=ensure_utc(model.updated_at),
        )

    @staticmethod
    def to_model(entity: MemberNextOfKin) -> MemberNextOfKinModel:
        tenant_id = entity.tenant_id.value
        return MemberNextOfKinModel(
            id=entity.id.value,
            tenant_id=tenant_id,
            member_id=entity.member_id.value,
            name=encrypt(entity.name, tenant_id=tenant_id),
            relationship=entity.relationship,
            phone=encrypt(entity.phone, tenant_id=tenant_id),
            email=encrypt(entity.email.value if entity.email else None, tenant_id=tenant_id),
            is_primary=entity.is_primary,
            created_at=ensure_utc(entity.created_at),
            updated_at=ensure_utc(entity.updated_at),
        )
