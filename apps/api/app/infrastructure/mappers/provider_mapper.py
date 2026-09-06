"""Provider aggregate persistence mapper."""

from datetime import date

from app.domain.entities.provider import ProviderEntity
from app.domain.enums import (
    AccreditationStatus,
    BaseStatus,
    PanelStatus,
    ProviderIdentityProvenance,
    ProviderTier,
    UgandaRegion,
)
from app.domain.value_objects.core import ProviderId, ProviderProfile, TenantId, UserId
from app.infrastructure.models.provider_model import ProviderModel
from app.shared.utils.datetime import ensure_utc


def _required(profile: dict[str, object], name: str) -> object:
    value = profile.get(name)
    if value is None:
        raise ValueError(f"Stored provider profile is missing required field {name!r}")
    return value


class ProviderMapper:
    @staticmethod
    def to_entity(model: ProviderModel) -> ProviderEntity:
        return ProviderEntity(
            id=ProviderId(model.id),
            tenant_id=TenantId(model.tenant_id),
            user_id=UserId(model.user_id) if model.user_id else None,
            display_name=model.display_name,
            contact_email=model.contact_email,
            contact_phone=model.contact_phone,
            identity_provenance=ProviderIdentityProvenance(model.identity_provenance),
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
            user_id=entity.user_id.value if entity.user_id else None,
            display_name=entity.display_name,
            contact_email=entity.contact_email,
            contact_phone=entity.contact_phone,
            identity_provenance=entity.identity_provenance,
            status=entity.status,
            license_info=entity.license_info,
            provider_profile=ProviderMapper.profile_to_dict(entity.provider_profile),
            created_at=entity.created_at,
            updated_at=entity.updated_at,
            deleted_at=entity.deleted_at,
        )

    @staticmethod
    def profile_from_dict(profile: dict[str, object] | None) -> ProviderProfile | None:
        """Read a stored profile.

        A missing panel or accreditation value reads as Pending, never as
        Active or Accredited: a malformed legacy row must not grant a
        practitioner standing the data does not evidence.
        """
        if profile is None:
            return None
        expiry = profile.get("accreditation_expiry")
        if isinstance(expiry, str):
            expiry = date.fromisoformat(expiry)
        if expiry is not None and not isinstance(expiry, date):
            raise ValueError("Provider accreditation expiry must be an ISO date")
        return ProviderProfile(
            tier=ProviderTier(_required(profile, "tier")),
            region=UgandaRegion(_required(profile, "region")),
            accreditation_status=AccreditationStatus(
                profile.get("accreditation_status") or AccreditationStatus.PENDING
            ),
            panel_status=PanelStatus(profile.get("panel_status") or PanelStatus.PENDING),
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
