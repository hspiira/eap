"""Domain events for the person bounded context."""

from dataclasses import dataclass

from app.domain.enums import PersonType
from app.domain.events.base import DomainEvent
from app.domain.value_objects.core import PersonId


@dataclass(frozen=True)
class PersonActivated(DomainEvent):
    """Event raised when a person is activated."""

    person_id: PersonId
    person_type: PersonType


@dataclass(frozen=True)
class PersonDeactivated(DomainEvent):
    """Event raised when a person is deactivated."""

    person_id: PersonId
    reason: str | None = None


@dataclass(frozen=True)
class PersonTerminated(DomainEvent):
    """Event raised when a person is terminated."""

    person_id: PersonId
    reason: str


@dataclass(frozen=True)
class PersonSecondaryRoleAdded(DomainEvent):
    """Event raised when a person's secondary role is added."""

    person_id: PersonId
    role: PersonType


@dataclass(frozen=True)
class PersonSecondaryRoleRemoved(DomainEvent):
    """Event raised when a person's secondary role is removed."""

    person_id: PersonId
    role: PersonType


# === User Events ===
