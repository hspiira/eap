"""
Service Session Repository Implementation

SQLAlchemy implementation of ServiceSessionRepository interface.
Uses TenantScopedRepositoryImpl base class to eliminate boilerplate.
"""

from collections.abc import Sequence
from datetime import date, datetime
from typing import Any

from sqlalchemy import Date as SADate
from sqlalchemy import and_, cast, func, or_, select, text

from app.domain.entities.service_session import ServiceSessionEntity
from app.domain.enums import (
    SessionCategory,
    SessionClinicalStatus,
    SessionDeliveryContext,
    SessionStatus,
    SessionType,
)
from app.domain.repositories.service_session_repository import (
    ProviderDeliveryStats,
    ProviderOrganisationSessionCount,
    ServiceSessionRepository,
)
from app.domain.services.session_scheduling import DEFAULT_SESSION_MINUTES
from app.domain.value_objects.core import (
    ClientId,
    EligibleMemberId,
    ProviderId,
    ServiceId,
    SessionId,
    TenantId,
)
from app.infrastructure.mappers.service_session_mapper import ServiceSessionMapper
from app.infrastructure.models.client_model import ClientModel
from app.infrastructure.models.provider_affiliation_model import ProviderAffiliationModel
from app.infrastructure.models.provider_model import ProviderModel
from app.infrastructure.models.provider_organisation_model import ProviderOrganisationModel
from app.infrastructure.models.service_model import ServiceModel
from app.infrastructure.models.service_session_model import ServiceSessionModel
from app.infrastructure.repositories.base import TenantScopedRepositoryImpl

#: Bound on ids resolved per entity kind for a search term. A tenant with more
#: matches than this on one search word has a naming problem, not a paging one.
_SEARCH_MATCH_LIMIT = 500


def _escape_like(value: str) -> str:
    """Backslash-escape LIKE/ILIKE wildcards so a literal `%` or `_` searches literally."""
    return value.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


class ServiceSessionRepositoryImpl(
    TenantScopedRepositoryImpl[ServiceSessionEntity, ServiceSessionModel, SessionId],
    ServiceSessionRepository,
):
    """
    SQLAlchemy implementation of ServiceSessionRepository.

    Inherits common CRUD operations from TenantScopedRepositoryImpl.
    Only implements domain-specific queries.
    """

    model_class = ServiceSessionModel
    id_column = "id"

    def _to_entity(self, model: ServiceSessionModel) -> ServiceSessionEntity:
        """Convert model to entity."""
        return ServiceSessionMapper.to_entity(model)

    def _to_model(self, entity: ServiceSessionEntity) -> ServiceSessionModel:
        """Convert entity to model."""
        return ServiceSessionMapper.to_model(entity)

    def _get_id_value(self, entity_id: SessionId) -> Any:
        """Extract raw ID value."""
        return entity_id.value

    # Domain-specific queries (not in base class)

    async def get_by_member_id(
        self, tenant_id: TenantId, member_id: EligibleMemberId
    ) -> list[ServiceSessionEntity]:
        """Get all sessions for a member within tenant, excluding soft-deleted."""
        stmt = select(ServiceSessionModel).where(
            ServiceSessionModel.tenant_id == tenant_id.value,
            ServiceSessionModel.member_id == member_id.value,
            ServiceSessionModel.deleted_at.is_(None),
        )
        result = await self.session.execute(stmt)
        models = result.scalars().all()

        return [self._to_entity(model) for model in models]

    async def get_by_provider_id(
        self, tenant_id: TenantId, provider_id: ProviderId
    ) -> list[ServiceSessionEntity]:
        """Get all sessions for a provider within tenant, excluding soft-deleted."""
        stmt = select(ServiceSessionModel).where(
            ServiceSessionModel.tenant_id == tenant_id.value,
            ServiceSessionModel.provider_id == provider_id.value,
            ServiceSessionModel.deleted_at.is_(None),
        )
        result = await self.session.execute(stmt)
        models = result.scalars().all()

        return [self._to_entity(model) for model in models]

    async def get_by_service_id(
        self, tenant_id: TenantId, service_id: ServiceId
    ) -> list[ServiceSessionEntity]:
        """Get all sessions for a service within tenant, excluding soft-deleted."""
        stmt = select(ServiceSessionModel).where(
            ServiceSessionModel.tenant_id == tenant_id.value,
            ServiceSessionModel.service_id == service_id.value,
            ServiceSessionModel.deleted_at.is_(None),
        )
        result = await self.session.execute(stmt)
        models = result.scalars().all()

        return [self._to_entity(model) for model in models]

    def _base_filters(
        self,
        member_id: EligibleMemberId | None,
        provider_id: ProviderId | None,
        service_id: ServiceId | None,
        session_type: SessionType | None = None,
        category: SessionCategory | None = None,
        clinical_outcome: SessionClinicalStatus | None = None,
        client_id: ClientId | None = None,
    ) -> dict[str, Any]:
        filters: dict[str, Any] = {}
        if client_id:
            filters["client_id"] = client_id.value
        if member_id:
            filters["member_id"] = member_id.value
        if provider_id:
            filters["provider_id"] = provider_id.value
        if service_id:
            filters["service_id"] = service_id.value
        if session_type:
            filters["session_type"] = session_type
        if category:
            filters["category"] = category
        if clinical_outcome:
            filters["clinical_outcome"] = clinical_outcome
        return filters

    @staticmethod
    def _status_condition(status: SessionStatus | Sequence[SessionStatus] | None) -> list[Any]:
        """`status` as one or several values, via IN rather than equality."""
        if status is None:
            return []
        values = [status] if isinstance(status, SessionStatus) else list(status)
        if not values:
            return []
        return [ServiceSessionModel.status.in_([s.value for s in values])]

    async def _search_condition(self, tenant_id: str, search: str | None) -> list[Any]:
        """Sessions whose service, client or practitioner name matches.

        Resolved from each table separately rather than joined onto the
        session query, so a session naming one of each is never duplicated
        and the sessions table itself carries no denormalised name to scan.
        Wildcard characters in `search` are escaped, so a literal `%` or `_`
        searches literally rather than as a LIKE wildcard.
        """
        if search is None or not search.strip():
            return []
        pattern = f"%{_escape_like(search.strip())}%"

        async def _ids(model: Any, name_column: Any) -> list[str]:
            rows = await self.session.scalars(
                select(model.id)
                .where(model.tenant_id == tenant_id, name_column.ilike(pattern, escape="\\"))
                .limit(_SEARCH_MATCH_LIMIT)
            )
            return list(rows.all())

        service_ids = await _ids(ServiceModel, ServiceModel.name)
        client_ids = await _ids(ClientModel, ClientModel.name)
        provider_ids = await _ids(ProviderModel, ProviderModel.display_name)

        matched = [
            condition
            for ids, column in (
                (service_ids, ServiceSessionModel.service_id),
                (client_ids, ServiceSessionModel.client_id),
                (provider_ids, ServiceSessionModel.provider_id),
            )
            if ids
            for condition in [column.in_(ids)]
        ]
        return [or_(*matched)] if matched else [ServiceSessionModel.id.in_([])]

    @staticmethod
    def _scheduled_conditions(
        scheduled_from: datetime | None, scheduled_to: datetime | None
    ) -> list[Any]:
        """
        Half-open-ish window on scheduled_at, inclusive at both ends.

        Callers send absolute instants rather than a named window ("today", "next
        7 days"), so the caller's timezone decides the boundaries and the server
        stays timezone-agnostic.
        """
        conditions: list[Any] = []
        if scheduled_from is not None:
            conditions.append(ServiceSessionModel.scheduled_at >= scheduled_from)
        if scheduled_to is not None:
            conditions.append(ServiceSessionModel.scheduled_at <= scheduled_to)
        return conditions

    async def list_all(
        self,
        tenant_id: TenantId,
        member_id: EligibleMemberId | None = None,
        provider_id: ProviderId | None = None,
        service_id: ServiceId | None = None,
        status: SessionStatus | Sequence[SessionStatus] | None = None,
        session_type: SessionType | None = None,
        category: SessionCategory | None = None,
        clinical_outcome: SessionClinicalStatus | None = None,
        client_id: ClientId | None = None,
        scheduled_from: datetime | None = None,
        scheduled_to: datetime | None = None,
        search: str | None = None,
        limit: int = 100,
        offset: int = 0,
        sort_by: str = "scheduled_at",
        sort_desc: bool = True,
    ) -> Sequence[ServiceSessionEntity]:
        """List sessions with filtering, searching, and pagination."""
        return await self._query_all(
            tenant_id=tenant_id.value,
            limit=limit,
            offset=offset,
            sort_by=sort_by,
            sort_desc=sort_desc,
            filters=self._base_filters(
                member_id,
                provider_id,
                service_id,
                session_type,
                category,
                clinical_outcome,
                client_id,
            ),
            search=None,
            search_fields=None,
            extra_conditions=(
                self._status_condition(status)
                + self._scheduled_conditions(scheduled_from, scheduled_to)
                + await self._search_condition(tenant_id.value, search)
            ),
        )

    async def count(
        self,
        tenant_id: TenantId,
        member_id: EligibleMemberId | None = None,
        provider_id: ProviderId | None = None,
        service_id: ServiceId | None = None,
        status: SessionStatus | Sequence[SessionStatus] | None = None,
        session_type: SessionType | None = None,
        category: SessionCategory | None = None,
        clinical_outcome: SessionClinicalStatus | None = None,
        client_id: ClientId | None = None,
        scheduled_from: datetime | None = None,
        scheduled_to: datetime | None = None,
        search: str | None = None,
    ) -> int:
        """Count sessions matching filters. Must mirror list_all exactly."""
        return await self._count_all(
            tenant_id=tenant_id.value,
            filters=self._base_filters(
                member_id,
                provider_id,
                service_id,
                session_type,
                category,
                clinical_outcome,
                client_id,
            ),
            extra_conditions=(
                self._status_condition(status)
                + self._scheduled_conditions(scheduled_from, scheduled_to)
                + await self._search_condition(tenant_id.value, search)
            ),
            search=None,
            search_fields=None,
        )

    @staticmethod
    def _provider_scope(tenant_id: TenantId, provider_id: ProviderId) -> list[Any]:
        return [
            ServiceSessionModel.tenant_id == tenant_id.value,
            ServiceSessionModel.provider_id == provider_id.value,
            ServiceSessionModel.deleted_at.is_(None),
        ]

    async def list_follow_ups(
        self, tenant_id: TenantId, session_id: SessionId
    ) -> Sequence[ServiceSessionEntity]:
        models = await self.session.scalars(
            select(ServiceSessionModel)
            .where(
                ServiceSessionModel.tenant_id == tenant_id.value,
                ServiceSessionModel.deleted_at.is_(None),
                ServiceSessionModel.follow_up_of_session_id == session_id.value,
            )
            .order_by(ServiceSessionModel.scheduled_at)
        )
        return [ServiceSessionMapper.to_entity(m) for m in models]

    async def session_ordinals(
        self, tenant_id: TenantId, session_ids: Sequence[str]
    ) -> dict[str, int]:
        """One window query for the whole page, not one per row.

        Ranks every session of each member involved, then keeps only the rows
        asked about. Cancelled sessions are left out of the count: a booking
        nobody attended is not a session in a person's course of care.
        """
        if not session_ids:
            return {}
        members = select(ServiceSessionModel.member_id).where(
            ServiceSessionModel.tenant_id == tenant_id.value,
            ServiceSessionModel.id.in_(session_ids),
            ServiceSessionModel.member_id.is_not(None),
        )
        counted = (
            select(
                ServiceSessionModel.id.label("id"),
                func.row_number()
                .over(
                    partition_by=ServiceSessionModel.member_id,
                    order_by=(ServiceSessionModel.scheduled_at, ServiceSessionModel.id),
                )
                .label("ordinal"),
            )
            .where(
                ServiceSessionModel.tenant_id == tenant_id.value,
                ServiceSessionModel.deleted_at.is_(None),
                ServiceSessionModel.status != SessionStatus.CANCELLED.value,
                ServiceSessionModel.member_id.in_(members),
            )
            .subquery()
        )
        rows = await self.session.execute(
            select(counted.c.id, counted.c.ordinal).where(counted.c.id.in_(session_ids))
        )
        return {row.id: int(row.ordinal) for row in rows}

    async def find_clashing_booking(
        self,
        tenant_id: TenantId,
        *,
        provider_id: ProviderId,
        starts_at: datetime,
        ends_at: datetime,
        exclude_session_id: SessionId | None = None,
    ) -> ServiceSessionEntity | None:
        """The earliest live booking of this practitioner overlapping the span.

        A booking carries no length of its own, so each one is measured by the
        service it delivers, falling back to the nominal hour. The overlap is
        half-open at both ends, so back-to-back bookings do not clash.
        """
        minutes = func.coalesce(ServiceModel.duration_minutes, DEFAULT_SESSION_MINUTES)
        existing_end = ServiceSessionModel.scheduled_at + minutes * text("interval '1 minute'")
        conditions: list[Any] = [
            ServiceSessionModel.tenant_id == tenant_id.value,
            ServiceSessionModel.deleted_at.is_(None),
            ServiceSessionModel.provider_id == provider_id.value,
            ServiceSessionModel.status.in_(
                (SessionStatus.SCHEDULED.value, SessionStatus.RESCHEDULED.value)
            ),
            ServiceSessionModel.scheduled_at < ends_at,
            existing_end > starts_at,
        ]
        if exclude_session_id is not None:
            conditions.append(ServiceSessionModel.id != exclude_session_id.value)
        model = await self.session.scalar(
            select(ServiceSessionModel)
            .join(ServiceModel, ServiceModel.id == ServiceSessionModel.service_id)
            .where(*conditions)
            .order_by(ServiceSessionModel.scheduled_at)
            .limit(1)
        )
        return ServiceSessionMapper.to_entity(model) if model else None

    def _awaiting_confirmation_filter(
        self,
        tenant_id: TenantId,
        as_of: datetime,
        provider_id: ProviderId | None,
        client_id: ClientId | None,
    ) -> list[Any]:
        conditions: list[Any] = [
            ServiceSessionModel.tenant_id == tenant_id.value,
            ServiceSessionModel.deleted_at.is_(None),
            ServiceSessionModel.status.in_(
                (SessionStatus.SCHEDULED.value, SessionStatus.RESCHEDULED.value)
            ),
            ServiceSessionModel.scheduled_at < as_of,
        ]
        if provider_id is not None:
            conditions.append(ServiceSessionModel.provider_id == provider_id.value)
        if client_id is not None:
            conditions.append(ServiceSessionModel.client_id == client_id.value)
        return conditions

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
        conditions = self._awaiting_confirmation_filter(tenant_id, as_of, provider_id, client_id)
        total = await self.session.scalar(
            select(func.count(ServiceSessionModel.id)).where(*conditions)
        )
        models = await self.session.scalars(
            select(ServiceSessionModel)
            .where(*conditions)
            .order_by(ServiceSessionModel.scheduled_at)
            .limit(limit)
            .offset(offset)
        )
        return [ServiceSessionMapper.to_entity(m) for m in models], int(total or 0)

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
        """The oldest unresolved booking matching this line of a counsellor's log.

        Compares the calendar day rather than the instant: the log carries a
        date and the booking carries a time nobody promised to keep.
        """
        member_match = (
            ServiceSessionModel.member_id == member_id.value
            if member_id is not None
            else ServiceSessionModel.member_id.is_(None)
        )
        model = await self.session.scalar(
            select(ServiceSessionModel)
            .where(
                ServiceSessionModel.tenant_id == tenant_id.value,
                ServiceSessionModel.deleted_at.is_(None),
                ServiceSessionModel.status.in_(
                    (SessionStatus.SCHEDULED.value, SessionStatus.RESCHEDULED.value)
                ),
                cast(ServiceSessionModel.scheduled_at, SADate) == session_date,
                ServiceSessionModel.provider_id == provider_id.value,
                ServiceSessionModel.client_id == client_id.value,
                ServiceSessionModel.service_id == service_id.value,
                member_match,
            )
            .order_by(ServiceSessionModel.scheduled_at)
            .limit(1)
        )
        return ServiceSessionMapper.to_entity(model) if model else None

    async def provider_delivery_stats(
        self, tenant_id: TenantId, provider_id: ProviderId
    ) -> ProviderDeliveryStats:
        """Aggregate a practitioner's delivery record in two grouped queries."""
        scope = self._provider_scope(tenant_id, provider_id)
        rows = await self._context_rows(scope)
        return ProviderDeliveryStats(
            total_sessions=sum(count for _, count, _, _ in rows),
            first_session_at=min((first for _, _, first, _ in rows), default=None),
            last_session_at=max((last for _, _, _, last in rows), default=None),
            by_delivery_context={context: count for context, count, _, _ in rows},
            by_organisation=await self._organisation_totals(scope),
        )

    async def _context_rows(
        self, scope: list[Any]
    ) -> list[tuple[SessionDeliveryContext, int, datetime, datetime]]:
        rows = (
            await self.session.execute(
                select(
                    ServiceSessionModel.delivery_context,
                    func.count(ServiceSessionModel.id),
                    func.min(ServiceSessionModel.scheduled_at),
                    func.max(ServiceSessionModel.scheduled_at),
                )
                .where(*scope)
                .group_by(ServiceSessionModel.delivery_context)
            )
        ).all()
        return [
            (SessionDeliveryContext(context), int(count), first, last)
            for context, count, first, last in rows
        ]

    async def _organisation_totals(
        self, scope: list[Any]
    ) -> list[ProviderOrganisationSessionCount]:
        """Group by the organisation the session's own affiliation named.

        A soft-deleted organisation is not excluded: the delivery still happened
        under it, and dropping it would leave the breakdown short of the total.
        """
        count = func.count(ServiceSessionModel.id)
        rows = (
            await self.session.execute(
                select(ProviderOrganisationModel.id, ProviderOrganisationModel.name, count)
                .select_from(ServiceSessionModel)
                .join(
                    ProviderAffiliationModel,
                    and_(
                        ProviderAffiliationModel.tenant_id == ServiceSessionModel.tenant_id,
                        ProviderAffiliationModel.id == ServiceSessionModel.provider_affiliation_id,
                    ),
                )
                .join(
                    ProviderOrganisationModel,
                    and_(
                        ProviderOrganisationModel.tenant_id == ProviderAffiliationModel.tenant_id,
                        ProviderOrganisationModel.id == ProviderAffiliationModel.organisation_id,
                    ),
                )
                .where(*scope)
                .group_by(ProviderOrganisationModel.id, ProviderOrganisationModel.name)
                .order_by(count.desc(), ProviderOrganisationModel.name)
            )
        ).all()
        return [
            ProviderOrganisationSessionCount(
                organisation_id=row[0], organisation_name=row[1], session_count=int(row[2])
            )
            for row in rows
        ]
