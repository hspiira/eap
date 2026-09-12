"""Dashboard aggregate queries.

Every figure the dashboard route needs, grouped counts against the ORM
models, kept out of the API layer so a route file never imports
infrastructure directly. Window math and response shaping stay in the route;
this runner only knows how to ask the database.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.enums import BaseStatus, EligibilityStatus, SessionStatus, SessionType
from app.domain.enums.clinical import CaseStatus
from app.domain.enums.contract import ContractStatus
from app.domain.enums.crisis import CriticalIncidentStatus
from app.domain.enums.outreach import OutreachStatus
from app.domain.enums.provider_network import ImportBatchStatus
from app.infrastructure.models.care_callback_model import OutreachRecordModel
from app.infrastructure.models.case_model import CaseModel
from app.infrastructure.models.client_model import ClientModel
from app.infrastructure.models.contract_model import ContractModel
from app.infrastructure.models.critical_incident_model import CriticalIncidentModel
from app.infrastructure.models.eligible_member_model import EligibleMemberModel
from app.infrastructure.models.provider_model import ProviderModel
from app.infrastructure.models.service_model import ServiceModel
from app.infrastructure.models.service_session_model import ServiceSessionModel
from app.infrastructure.models.session_import_model import (
    SessionImportBatchModel,
    SessionImportRowModel,
)
from app.shared.utils.datetime import utc_now

if TYPE_CHECKING:
    from app.api.schemas.dashboard_schemas import Granularity


OPEN_OUTREACH = (
    OutreachStatus.PENDING,
    OutreachStatus.ASSIGNED,
    OutreachStatus.CONTACTED,
    OutreachStatus.ESCALATED,
)
"""A flagged crisis stays on the board until its outreach reaches a terminal state."""

OPEN_CASE_STATUSES = (CaseStatus.INTAKE, CaseStatus.ASSESSMENT, CaseStatus.ACTIVE)


def _completed_sessions(tenant_id: str):
    return (
        ServiceSessionModel.tenant_id == tenant_id,
        ServiceSessionModel.deleted_at.is_(None),
        ServiceSessionModel.status == SessionStatus.COMPLETED,
    )


def _within(start: datetime, end: datetime):
    return (
        ServiceSessionModel.scheduled_at >= start,
        ServiceSessionModel.scheduled_at < end,
    )


def _utc_scheduled_at():
    """Normalize before truncating.

    date_trunc on a timestamptz buckets by the connection's timezone, which
    moves a boundary session into the wrong bucket depending on server
    configuration.
    """
    return func.timezone("UTC", ServiceSessionModel.scheduled_at)


class DashboardQueryRunner:
    """Every grouped count the dashboard aggregate needs, for one tenant."""

    def __init__(self, session: AsyncSession):
        self._session = session

    async def _count(self, stmt) -> int:
        return int((await self._session.execute(stmt)).scalar_one() or 0)

    async def session_kpis(
        self,
        tenant_id: str,
        start: datetime,
        end: datetime,
        prior_start: datetime,
        prior_end: datetime,
    ) -> tuple[int, int, int]:
        current = await self._count(
            select(func.count(ServiceSessionModel.id)).where(
                *_completed_sessions(tenant_id), *_within(start, end)
            )
        )
        prior = await self._count(
            select(func.count(ServiceSessionModel.id)).where(
                *_completed_sessions(tenant_id), *_within(prior_start, prior_end)
            )
        )
        clients_served = await self._count(
            select(func.count(func.distinct(ServiceSessionModel.client_id))).where(
                *_completed_sessions(tenant_id), *_within(start, end)
            )
        )
        return current, prior, clients_served

    async def sessions_awaiting_confirmation(self, tenant_id: str) -> int:
        """Bookings past their date that nobody has resolved.

        Not a data-quality gap in the usual sense: nothing was recorded wrongly.
        It counts deliveries the system expected and has not been told the
        outcome of, which is the queue the month-end cross-check works through.
        """
        return await self._count(
            select(func.count(ServiceSessionModel.id)).where(
                ServiceSessionModel.tenant_id == tenant_id,
                ServiceSessionModel.deleted_at.is_(None),
                ServiceSessionModel.status.in_(
                    (SessionStatus.SCHEDULED.value, SessionStatus.RESCHEDULED.value)
                ),
                ServiceSessionModel.scheduled_at < utc_now(),
            )
        )

    async def earliest_session(self, tenant_id: str) -> datetime | None:
        """When this tenant first delivered anything. None when it never has.

        The floor for "all time", and the first year the year picker offers.
        Without it an all-time window has no honest start, and the series
        back-fills empty buckets from whatever date it was handed.
        """
        return await self._session.scalar(
            select(func.min(ServiceSessionModel.scheduled_at)).where(
                *_completed_sessions(tenant_id)
            )
        )

    async def coverage(self, tenant_id: str) -> tuple[int, int, int]:
        covered = await self._count(
            select(func.count(EligibleMemberModel.id)).where(
                EligibleMemberModel.tenant_id == tenant_id,
                EligibleMemberModel.status == EligibilityStatus.ACTIVE,
            )
        )
        with_roster = await self._count(
            select(func.count(func.distinct(EligibleMemberModel.client_id))).where(
                EligibleMemberModel.tenant_id == tenant_id
            )
        )
        clients_total = await self._count(
            select(func.count(ClientModel.id)).where(
                ClientModel.tenant_id == tenant_id, ClientModel.deleted_at.is_(None)
            )
        )
        return covered, with_roster, clients_total

    async def sessions_series(
        self,
        tenant_id: str,
        start: datetime,
        end: datetime,
        granularity: Granularity,
    ) -> list[tuple[date, SessionType | None, int]]:
        bucket = func.date_trunc(granularity, _utc_scheduled_at())
        rows = await self._session.execute(
            select(bucket, ServiceSessionModel.session_type, func.count(ServiceSessionModel.id))
            .where(*_completed_sessions(tenant_id), *_within(start, end))
            .group_by(bucket, ServiceSessionModel.session_type)
        )
        return [
            (bucket_at.date(), session_type, int(total)) for bucket_at, session_type, total in rows
        ]

    async def category_split(
        self, tenant_id: str, start: datetime, end: datetime
    ) -> list[tuple[str, int]]:
        rows = await self._session.execute(
            select(ServiceSessionModel.category, func.count(ServiceSessionModel.id))
            .where(
                *_completed_sessions(tenant_id),
                *_within(start, end),
                ServiceSessionModel.category.is_not(None),
            )
            .group_by(ServiceSessionModel.category)
            .order_by(func.count(ServiceSessionModel.id).desc())
        )
        return [(category.value, int(total)) for category, total in rows]

    async def top_clients(
        self, tenant_id: str, start: datetime, end: datetime, limit: int
    ) -> list[tuple[str, str, int]]:
        rows = await self._session.execute(
            select(ClientModel.id, ClientModel.name, func.count(ServiceSessionModel.id))
            .join(ClientModel, ClientModel.id == ServiceSessionModel.client_id)
            .where(*_completed_sessions(tenant_id), *_within(start, end))
            .group_by(ClientModel.id, ClientModel.name)
            .order_by(func.count(ServiceSessionModel.id).desc())
            .limit(limit)
        )
        return [(client_id, name, int(total)) for client_id, name, total in rows]

    async def service_counts(
        self, tenant_id: str, start: datetime, end: datetime
    ) -> dict[str, tuple[str, int]]:
        rows = await self._session.execute(
            select(ServiceModel.id, ServiceModel.name, func.count(ServiceSessionModel.id))
            .join(ServiceModel, ServiceModel.id == ServiceSessionModel.service_id)
            .where(*_completed_sessions(tenant_id), *_within(start, end))
            .group_by(ServiceModel.id, ServiceModel.name)
        )
        return {service_id: (name, int(total)) for service_id, name, total in rows}

    async def latest_import_batch(self, tenant_id: str) -> SessionImportBatchModel | None:
        return (
            await self._session.execute(
                select(SessionImportBatchModel)
                .where(
                    SessionImportBatchModel.tenant_id == tenant_id,
                    SessionImportBatchModel.status != ImportBatchStatus.ABANDONED,
                )
                .order_by(SessionImportBatchModel.created_at.desc())
                .limit(1)
            )
        ).scalar_one_or_none()

    async def import_row_outcomes(self, batch_id: str) -> dict:
        rows = await self._session.execute(
            select(SessionImportRowModel.outcome, func.count(SessionImportRowModel.id))
            .where(SessionImportRowModel.batch_id == batch_id)
            .group_by(SessionImportRowModel.outcome)
        )
        return {outcome: int(total) for outcome, total in rows}

    async def data_quality_counts(self, tenant_id: str) -> tuple[int, int, int]:
        missing_outcome = await self._count(
            select(func.count(ServiceSessionModel.id)).where(
                *_completed_sessions(tenant_id), ServiceSessionModel.clinical_outcome.is_(None)
            )
        )
        missing_rate = await self._count(
            select(func.count(ServiceSessionModel.id)).where(
                *_completed_sessions(tenant_id), ServiceSessionModel.rate_ugx.is_(None)
            )
        )
        providers_pending = await self._count(
            select(func.count(ProviderModel.id)).where(
                ProviderModel.tenant_id == tenant_id,
                ProviderModel.deleted_at.is_(None),
                ProviderModel.status == BaseStatus.PENDING,
            )
        )
        return missing_outcome, missing_rate, providers_pending

    async def value_delivered(
        self, tenant_id: str, start: datetime, end: datetime
    ) -> tuple[int, int]:
        """Summed rates of priced completed sessions in range, and the unpriced count."""
        priced_sum, unpriced = (
            await self._session.execute(
                select(
                    func.coalesce(func.sum(ServiceSessionModel.rate_ugx), 0),
                    func.count(ServiceSessionModel.id).filter(
                        ServiceSessionModel.rate_ugx.is_(None)
                    ),
                ).where(*_completed_sessions(tenant_id), *_within(start, end))
            )
        ).one()
        return int(priced_sum or 0), int(unpriced or 0)

    async def outcome_mix(
        self, tenant_id: str, start: datetime, end: datetime
    ) -> list[tuple[str | None, int]]:
        rows = await self._session.execute(
            select(ServiceSessionModel.clinical_outcome, func.count(ServiceSessionModel.id))
            .where(*_completed_sessions(tenant_id), *_within(start, end))
            .group_by(ServiceSessionModel.clinical_outcome)
            .order_by(func.count(ServiceSessionModel.id).desc())
        )
        return [
            (outcome.value if outcome is not None else None, int(total))
            for outcome, total in rows.all()
        ]

    async def upcoming_bookings(
        self, tenant_id: str, start: datetime, end: datetime
    ) -> list[tuple[date, int]]:
        """Open bookings per day between start and end."""
        day = func.date_trunc("day", _utc_scheduled_at())
        rows = await self._session.execute(
            select(day, func.count(ServiceSessionModel.id))
            .where(
                ServiceSessionModel.tenant_id == tenant_id,
                ServiceSessionModel.deleted_at.is_(None),
                ServiceSessionModel.status.in_(
                    (SessionStatus.SCHEDULED.value, SessionStatus.RESCHEDULED.value)
                ),
                ServiceSessionModel.scheduled_at >= start,
                ServiceSessionModel.scheduled_at < end,
            )
            .group_by(day)
            .order_by(day)
        )
        return [(bucket.date(), int(total)) for bucket, total in rows.all()]

    async def risk_counts(self, tenant_id: str) -> tuple[int, int, int]:
        """Open crisis flags, open critical incidents, open clinical cases."""
        crisis = await self._count(
            select(func.count(OutreachRecordModel.id)).where(
                OutreachRecordModel.tenant_id == tenant_id,
                OutreachRecordModel.crisis_flag.is_(True),
                OutreachRecordModel.status.in_(tuple(s.value for s in OPEN_OUTREACH)),
            )
        )
        incidents = await self._count(
            select(func.count(CriticalIncidentModel.id)).where(
                CriticalIncidentModel.tenant_id == tenant_id,
                CriticalIncidentModel.status != CriticalIncidentStatus.CLOSED,
            )
        )
        cases = await self._count(
            select(func.count(CaseModel.id)).where(
                CaseModel.tenant_id == tenant_id,
                CaseModel.status.in_(tuple(s.value for s in OPEN_CASE_STATUSES)),
            )
        )
        return crisis, incidents, cases

    async def contracts_ending_soon(self, tenant_id: str, today: date, horizon: date) -> int:
        return await self._count(
            select(func.count(ContractModel.id)).where(
                ContractModel.tenant_id == tenant_id,
                ContractModel.deleted_at.is_(None),
                ContractModel.status == ContractStatus.ACTIVE,
                ContractModel.end_date >= today,
                ContractModel.end_date <= horizon,
            )
        )
