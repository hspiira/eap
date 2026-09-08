"""Domain events for the eligible member (roster) bounded context."""

from dataclasses import dataclass

from app.domain.events.base import DomainEvent
from app.domain.value_objects.core import ClientId, EligibleMemberId


@dataclass(frozen=True)
class EligibleMemberCreated(DomainEvent):
    """Event raised when a person is added to a client's roster."""

    member_id: EligibleMemberId
    client_id: ClientId
    employer_member_id: str


@dataclass(frozen=True)
class EligibleMemberStatusChanged(DomainEvent):
    """Event raised when a member is suspended, reinstated or terminated."""

    member_id: EligibleMemberId
    from_status: str
    to_status: str


@dataclass(frozen=True)
class EligibleMemberUpdated(DomainEvent):
    """Event raised when a member's roster details change.

    `field` names what was touched; the values reach `entity_changes` through
    the handler's diff.
    """

    member_id: EligibleMemberId
    field: str


@dataclass(frozen=True)
class EligibleMemberAccountLinked(DomainEvent):
    """Event raised when a member is joined to a user account.

    Emitted by the route rather than the entity: linkage is an association
    between two aggregates, and the member's own state barely moves.
    """

    member_id: EligibleMemberId
    user_id: str


@dataclass(frozen=True)
class EligibleMemberAccountUnlinked(DomainEvent):
    """Event raised when a member's user account is detached."""

    member_id: EligibleMemberId


@dataclass(frozen=True)
class EligibleMemberMerged(DomainEvent):
    """Event raised on the member that absorbed another."""

    member_id: EligibleMemberId
    merged_from: str


@dataclass(frozen=True)
class EligibleMemberMergedIntoMember(DomainEvent):
    """Event raised on the member that was absorbed."""

    member_id: EligibleMemberId
    merged_into: str


@dataclass(frozen=True)
class MemberNextOfKinCreated(DomainEvent):
    """Event raised when a next-of-kin contact is added to a member.

    Three events rather than one carrying the operation: the audit action is
    mapped from the event's name, so one name cannot produce a create, an
    update and a delete.
    """

    member_id: EligibleMemberId


@dataclass(frozen=True)
class MemberNextOfKinUpdated(DomainEvent):
    """Event raised when a next-of-kin contact's details change."""

    member_id: EligibleMemberId


@dataclass(frozen=True)
class MemberNextOfKinDeleted(DomainEvent):
    """Event raised when a next-of-kin contact is removed."""

    member_id: EligibleMemberId
