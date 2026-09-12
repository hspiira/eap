"""
Service Session Repository Interface

Defines the contract for Service Session data access.
Implementation lives in infrastructure layer.
"""

from abc import abstractmethod
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date, datetime

from app.domain.entities.service_session import ServiceSessionEntity
from app.domain.enums import (
    SessionCategory,
    SessionClinicalStatus,
    SessionDeliveryContext,
    SessionStatus,
    SessionType,
)
from app.domain.repositories.base_repository import BaseRepository
from app.domain.value_objects.core import (
    ClientId,
    EligibleMemberId,
    ProviderId,
    ServiceId,
    SessionId,
    TenantId,
)


@dataclass(frozen=True)
class ProviderOrganisationSessionCount:
    """Sessions one practitioner delivered under one organisation."""

    organisation_id: str
    organisation_name: str
    session_count: int


@dataclass(frozen=True)
class ProviderDeliveryStats:
    """Aggregate delivery record for one practitioner within a tenant."""

    total_sessions: int
    first_session_at: datetime | None
    last_session_at: datetime | None
    by_delivery_context: dict[SessionDeliveryContext, int]
    by_organisation: list[ProviderOrganisationSessionCount]


class ServiceSessionRepository(BaseRepository[ServiceSessionEntity, SessionId]):
    """
    Repository interface for Service Session aggregate.

    Repositories are ONLY for aggregate roots.
    This interface is in the domain layer - implementation in infrastructure.
    """

    @abstractmethod
    async def get_by_member_id(
        self, tenant_id: TenantId, member_id: EligibleMemberId
    ) -> list[ServiceSessionEntity]:
        """
        Get all sessions for a member within a tenant.

        Args:
            tenant_id: Tenant identifier
            member_id: Member identifier

        Returns:
            List of ServiceSessionEntity for the member
        """
        pass

    @abstractmethod
    async def get_by_provider_id(
        self, tenant_id: TenantId, provider_id: ProviderId
    ) -> list[ServiceSessionEntity]:
        """
        Get all sessions for a provider within a tenant.

        Args:
            tenant_id: Tenant identifier
            provider_id: Provider identifier

        Returns:
            List of ServiceSessionEntity for the provider
        """
        pass

    @abstractmethod
    async def get_by_service_id(
        self, tenant_id: TenantId, service_id: ServiceId
    ) -> list[ServiceSessionEntity]:
        """
        Get all sessions for a service within a tenant.

        Args:
            tenant_id: Tenant identifier
            service_id: Service identifier

        Returns:
            List of ServiceSessionEntity for the service
        """
        pass

    @abstractmethod
    async def list_all(
        self,
        tenant_id: TenantId,
        member_id: EligibleMemberId | None = None,
        provider_id: ProviderId | None = None,
        service_id: ServiceId | None = None,
        status: SessionStatus | None = None,
        session_type: SessionType | None = None,
        category: SessionCategory | None = None,
        clinical_outcome: SessionClinicalStatus | None = None,
        scheduled_from: datetime | None = None,
        scheduled_to: datetime | None = None,
        limit: int = 100,
        offset: int = 0,
        sort_by: str = "scheduled_at",
        sort_desc: bool = True,
    ) -> Sequence[ServiceSessionEntity]:
        """
        List sessions with filtering, searching, and pagination.

        Args:
            tenant_id: Tenant identifier
            member_id: Filter by member identifier
            provider_id: Filter by provider identifier
            service_id: Filter by service identifier
            status: Filter by session status
            scheduled_from: Only sessions scheduled at or after this instant
            scheduled_to: Only sessions scheduled at or before this instant
            limit: Maximum number of results
            offset: Number of results to skip
            sort_by: Field to sort by
            sort_desc: Sort in descending order

        Returns:
            Sequence of ServiceSessionEntity
        """

    @abstractmethod
    async def count(
        self,
        tenant_id: TenantId,
        member_id: EligibleMemberId | None = None,
        provider_id: ProviderId | None = None,
        service_id: ServiceId | None = None,
        status: SessionStatus | None = None,
        session_type: SessionType | None = None,
        category: SessionCategory | None = None,
        clinical_outcome: SessionClinicalStatus | None = None,
        scheduled_from: datetime | None = None,
        scheduled_to: datetime | None = None,
    ) -> int:
        """
        Count sessions matching filters.

        Must apply exactly the same filters as `list_all`.

        Args:
            tenant_id: Tenant identifier
            member_id: Filter by member identifier
            provider_id: Filter by provider identifier
            service_id: Filter by service identifier
            status: Filter by session status
            scheduled_from: Only sessions scheduled at or after this instant
            scheduled_to: Only sessions scheduled at or before this instant

        Returns:
            Total count
        """

    @abstractmethod
    async def find_clashing_booking(
        self,
        tenant_id: TenantId,
        *,
        provider_id: ProviderId,
        starts_at: datetime,
        ends_at: datetime,
        exclude_session_id: SessionId | None = None,
    ) -> ServiceSessionEntity | None:
        """A live booking for this practitioner overlapping the given span.

        Only Scheduled and Rescheduled hold a practitioner's time. A cancelled
        booking released it, and a completed one is a record of the past, not a
        claim on the future; refusing against those would make it impossible to
        enter a session that has already happened.

        `exclude_session_id` lets a reschedule ignore the booking it is moving,
        which would otherwise always clash with itself.
        """

    @abstractmethod
    async def list_awaiting_confirmation(
        self,
        tenant_id: TenantId,
        *,
        as_of: datetime,
        provider_id: ProviderId | None = None,
        client_id: ClientId | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[Sequence[ServiceSessionEntity], int]:
        """Bookings whose date has passed and which nobody has resolved.

        The system never witnesses delivery, so a booking sits Scheduled until
        a counsellor's month-end log confirms it. Past its date it is no longer
        a plan, it is an open question: did it happen, and was it recorded?
        Oldest first, because the oldest is the one most likely to be forgotten.
        """

    @abstractmethod
    async def find_awaiting_confirmation(
        self,
        tenant_id: TenantId,
        *,
        session_date: date,
        provider_id: ProviderId,
        client_id: ClientId,
        service_id: ServiceId,
        member_id: EligibleMemberId | None,
    ) -> ServiceSessionEntity | None:
        """A session this tenant booked for that day and has not confirmed yet.

        The counsellor's month-end log reports work the system may already be
        expecting. Matched on the finest grain the log supports, which carries
        a date and no time of day. Scheduled and Rescheduled only: a session
        already Completed, Cancelled or marked a no-show has been resolved and
        is not what an incoming line is reporting.
        """

    @abstractmethod
    async def provider_delivery_stats(
        self, tenant_id: TenantId, provider_id: ProviderId
    ) -> ProviderDeliveryStats:
        """
        Aggregate every session attributed to one practitioner.

        The organisation breakdown resolves through the affiliation each session
        stored, not the practitioner's affiliations today, so a later move
        between organisations cannot reattribute past delivery (decision 2).

        Args:
            tenant_id: Tenant identifier
            provider_id: Provider identifier

        Returns:
            ProviderDeliveryStats over the practitioner's non-deleted sessions
        """
