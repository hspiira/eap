"""Provider aggregate persistence mapper."""

from datetime import date

from app.domain.entities.provider import ProviderEntity
from app.domain.enums import (
    AccreditationStatus,
    BaseStatus,
    PanelStatus,
    ProviderTier,
    UgandaRegion,
)
from app.domain.value_objects.core import ProviderId, ProviderProfile, TenantId, UserId
from app.infrastructure.models.provider_model import ProviderModel
from app.shared.utils.datetime import ensure_utc


class ProviderMapper:
    @staticmethod
    def to_entity(model: ProviderModel) -> ProviderEntity:
        return ProviderEntity(
            id=ProviderId(model.id),
            tenant_id=TenantId(model.tenant_id),
            user_id=UserId(model.user_id),
            status=BaseStatus(model.status),
            license_info=model.license_info,
            provider_profile=ProviderMapper.profile_from_dict(model.provider_profile),
            created_at=ensure_utc(model.created_at),
            updated_at=ensure_utc(model.updated_at),
            deleted_at=ensure_utc(model.deleted_at),
        )

    @staticmethod
    def to_model(entity: ProviderEntity) -> ProviderModel:
        return ProviderModel(
            id=entity.id.value,
            tenant_id=entity.tenant_id.value,
            user_id=entity.user_id.value,
            status=entity.status,
            license_info=entity.license_info,
            provider_profile=ProviderMapper.profile_to_dict(entity.provider_profile),
            created_at=entity.created_at,
            updated_at=entity.updated_at,
            deleted_at=entity.deleted_at,
        )

    @staticmethod
    def profile_from_dict(profile: dict[str, object] | None) -> ProviderProfile | None:
        if profile is None:
            return None
        expiry = profile.get("accreditation_expiry")
        if isinstance(expiry, str):
            expiry = date.fromisoformat(expiry)
        if expiry is not None and not isinstance(expiry, date):
            raise ValueError("Provider accreditation expiry must be an ISO date")
        return ProviderProfile(
            tier=ProviderTier(profile["tier"]),
            region=UgandaRegion(profile["region"]),
            accreditation_status=AccreditationStatus(profile["accreditation_status"]),
            panel_status=PanelStatus(profile.get("panel_status", PanelStatus.ACTIVE)),
            accreditation_authority=profile.get("accreditation_authority"),
            accreditation_expiry=expiry,
            specialties=tuple(profile.get("specialties") or ()),
            bio=profile.get("bio"),
        )

    @staticmethod
    def profile_to_dict(profile: ProviderProfile | None) -> dict[str, object] | None:
        if profile is None:
            return None
        return {
            "tier": profile.tier.value,
            "region": profile.region.value,
            "accreditation_status": profile.accreditation_status.value,
            "panel_status": profile.panel_status.value,
            "accreditation_authority": profile.accreditation_authority,
            "accreditation_expiry": profile.accreditation_expiry.isoformat()
            if profile.accreditation_expiry
            else None,
            "specialties": list(profile.specialties),
            "bio": profile.bio,
        }
