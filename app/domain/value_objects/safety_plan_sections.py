"""Stanley-Brown safety-plan section value objects.

The six structured sections of a Stanley-Brown safety plan, each modelled as a
frozen value object so a plan is reconstructed from its persisted JSON without
ambiguity about which list is which.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.domain.exceptions import DomainError


@dataclass(frozen=True)
class WarningSigns:
    items: tuple[str, ...]

    def __post_init__(self) -> None:
        if not self.items:
            raise DomainError("warning_signs requires at least one item")


@dataclass(frozen=True)
class InternalCopingStrategies:
    items: tuple[str, ...]

    def __post_init__(self) -> None:
        if not self.items:
            raise DomainError(
                "internal_coping_strategies requires at least one item"
            )


@dataclass(frozen=True)
class SocialDistractions:
    people_or_places: tuple[str, ...]

    def __post_init__(self) -> None:
        if not self.people_or_places:
            raise DomainError(
                "social_distractions requires at least one entry"
            )


@dataclass(frozen=True)
class SocialContact:
    name: str
    relation: str | None = None
    phone: str | None = None

    def __post_init__(self) -> None:
        if not self.name:
            raise DomainError("SocialContact.name is required")


@dataclass(frozen=True)
class SocialContactsForHelp:
    contacts: tuple[SocialContact, ...]

    def __post_init__(self) -> None:
        if not self.contacts:
            raise DomainError(
                "social_contacts_for_help requires at least one contact"
            )


@dataclass(frozen=True)
class ProfessionalContact:
    label: str
    phone: str | None = None
    after_hours: str | None = None

    def __post_init__(self) -> None:
        if not self.label:
            raise DomainError("ProfessionalContact.label is required")


@dataclass(frozen=True)
class ProfessionalHelpResources:
    contacts: tuple[ProfessionalContact, ...]

    def __post_init__(self) -> None:
        if not self.contacts:
            raise DomainError(
                "professional_help_resources requires at least one contact"
            )


@dataclass(frozen=True)
class MeansRestrictionPlan:
    steps: tuple[str, ...]

    def __post_init__(self) -> None:
        if not self.steps:
            raise DomainError("means_restriction_plan requires at least one step")
