from enum import Enum


class ProviderTier(str, Enum):
    """Provider panel tier, drives routing and rate cards (Joseph's framework)."""

    T1 = "T1"
    T2 = "T2"
    T3 = "T3"


class UgandaRegion(str, Enum):
    """The 8 empanelment regions used for provider geo-distribution."""

    CENTRAL = "Central"
    KAMPALA_METRO = "KampalaMetro"
    EASTERN = "Eastern"
    NORTHERN = "Northern"
    WEST_NILE = "WestNile"
    WESTERN = "Western"
    SOUTH_WESTERN = "SouthWestern"
    KARAMOJA = "Karamoja"


class AccreditationStatus(str, Enum):
    """Where the provider sits in the accreditation pipeline."""

    PENDING = "Pending"
    ACCREDITED = "Accredited"
    LAPSED = "Lapsed"
    SUSPENDED = "Suspended"
    REJECTED = "Rejected"


class PanelStatus(str, Enum):
    """Whether the provider is currently on the active panel."""

    PENDING = "Pending"
    ACTIVE = "Active"
    SUSPENDED = "Suspended"
    REMOVED = "Removed"


class NonCompeteStatus(str, Enum):
    """Lifecycle of a non-compete clause."""

    DRAFT = "Draft"
    ACTIVE = "Active"
    REVOKED = "Revoked"
    EXPIRED = "Expired"


class ProviderIdentityProvenance(str, Enum):
    """Where a practitioner's owned name and contact details came from."""

    OWNED = "Owned"
    BACKFILLED_FROM_USER = "BackfilledFromUser"


class ProviderGender(str, Enum):
    """Practitioner gender. Restricted to Male/Female by product decision."""

    FEMALE = "Female"
    MALE = "Male"
