"""Identifiers for the provider network aggregates."""

from dataclasses import dataclass

from app.domain.value_objects.ids import Id


@dataclass(frozen=True)
class ProviderOrganisationId(Id):
    pass


@dataclass(frozen=True)
class ProviderAffiliationId(Id):
    pass


@dataclass(frozen=True)
class ProviderSpecialtyId(Id):
    pass


@dataclass(frozen=True)
class ProviderSpecialtyLinkId(Id):
    pass


@dataclass(frozen=True)
class SessionImportBatchId(Id):
    pass


@dataclass(frozen=True)
class SessionImportRowId(Id):
    pass


@dataclass(frozen=True)
class PractitionerImportBatchId(Id):
    pass


@dataclass(frozen=True)
class PractitionerImportRowId(Id):
    pass
