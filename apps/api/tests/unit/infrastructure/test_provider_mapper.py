from datetime import UTC, date, datetime

from app.domain.enums import (
    AccreditationStatus,
    BaseStatus,
    PanelStatus,
    ProviderTier,
    UgandaRegion,
)
from app.infrastructure.mappers.provider_mapper import ProviderMapper
from app.infrastructure.models.provider_model import ProviderModel


def _model() -> ProviderModel:
    now = datetime.now(UTC)
    return ProviderModel(
        id="provider-1",
        tenant_id="tenant-1",
        user_id="user-1",
        status=BaseStatus.ACTIVE,
        license_info={"number": "LIC-1"},
        provider_profile={
            "tier": ProviderTier.T1.value,
            "region": UgandaRegion.KAMPALA_METRO.value,
            "accreditation_status": AccreditationStatus.ACCREDITED.value,
            "panel_status": PanelStatus.ACTIVE.value,
            "accreditation_authority": "UCC",
            "accreditation_expiry": "2027-06-30",
            "specialties": ["Counselling"],
            "bio": "Trauma-informed practitioner",
        },
        created_at=now,
        updated_at=now,
    )


def test_provider_mapper_rehydrates_typed_profile() -> None:
    entity = ProviderMapper.to_entity(_model())

    assert entity.id.value == "provider-1"
    assert entity.provider_profile is not None
    assert entity.provider_profile.accreditation_expiry == date(2027, 6, 30)
    assert entity.provider_profile.specialties == ("Counselling",)


def test_provider_mapper_persists_json_safe_profile() -> None:
    model = ProviderMapper.to_model(ProviderMapper.to_entity(_model()))

    assert model.provider_profile == {
        "tier": ProviderTier.T1.value,
        "region": UgandaRegion.KAMPALA_METRO.value,
        "accreditation_status": AccreditationStatus.ACCREDITED.value,
        "panel_status": PanelStatus.ACTIVE.value,
        "accreditation_authority": "UCC",
        "accreditation_expiry": "2027-06-30",
        "specialties": ["Counselling"],
        "bio": "Trauma-informed practitioner",
    }
