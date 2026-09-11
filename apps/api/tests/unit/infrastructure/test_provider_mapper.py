from datetime import UTC, date, datetime

from app.domain.enums import (
    AccreditationStatus,
    BaseStatus,
    PanelStatus,
    ProviderIdentityProvenance,
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
        display_name="Amina Okello",
        contact_email="amina@example.com",
        contact_phone=None,
        identity_provenance=ProviderIdentityProvenance.BACKFILLED_FROM_USER,
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
    assert entity.display_name == "Amina Okello"
    assert entity.contact_email == "amina@example.com"
    assert entity.identity_provenance is ProviderIdentityProvenance.BACKFILLED_FROM_USER
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
        "gender": None,
        "title": None,
    }


def test_provider_without_an_account_round_trips() -> None:
    """A practitioner with no login keeps their own name and contact details."""
    model = _model()
    model.user_id = None
    model.identity_provenance = ProviderIdentityProvenance.OWNED

    entity = ProviderMapper.to_entity(model)

    assert entity.user_id is None
    assert entity.display_name == "Amina Okello"
    assert ProviderMapper.to_model(entity).user_id is None


def test_missing_panel_status_reads_as_pending_not_active() -> None:
    """A malformed legacy row must not be granted standing the data lacks."""
    model = _model()
    del model.provider_profile["panel_status"]
    del model.provider_profile["accreditation_status"]

    profile = ProviderMapper.to_entity(model).provider_profile

    assert profile.panel_status is PanelStatus.PENDING
    assert profile.accreditation_status is AccreditationStatus.PENDING


def test_missing_tier_reads_as_unassessed() -> None:
    """Tier and region are None until a person assesses the practitioner.

    Imported records arrive without either, so absence is a modelled state,
    not a malformed row. It grants no standing: the booking gate still
    requires an Active panel and accreditation.
    """
    model = _model()
    del model.provider_profile["tier"]

    profile = ProviderMapper.to_entity(model).provider_profile

    assert profile.tier is None
