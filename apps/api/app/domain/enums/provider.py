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


class ProviderTitle(str, Enum):
    """An honorific held by a practitioner.

    Stored apart from the name so the name stays the name. Source extracts
    write the two together (`DR. JANE ACHIENG`), and the alias normaliser
    strips exactly this vocabulary before matching, so a title never has to be
    guessed back out of a stored name.
    """

    DR = "Dr"
    PROF = "Prof"
    REV = "Rev"
    SR = "Sr"
    MR = "Mr"
    MRS = "Mrs"
    MS = "Ms"
    MISS = "Miss"

    @property
    def written(self) -> str:
        """How the title is written before a name.

        `Miss` is a whole word and takes no stop; the rest are shortened and do.
        """
        return self.value if self is ProviderTitle.MISS else f"{self.value}."


class EngagementDocumentKind(str, Enum):
    """The seven engagement documents tracked per practitioner (P-02)."""

    CONTRACT = "Contract"
    KYC = "KYC"
    CERTIFICATE_OF_REGISTRATION = "CertificateOfRegistration"
    MEMORANDUM_OF_ASSOCIATION = "MoA"
    UCA_LICENCE = "UcaLicence"
    DECLARATION_FORM = "DeclarationForm"
    LEAD_CONSULTANT_CV = "LeadConsultantCV"


class EngagementDocumentState(str, Enum):
    """Whether an engagement document is on file, absent, or being chased."""

    PRESENT = "Present"
    MISSING = "Missing"
    OPEN = "Open"
