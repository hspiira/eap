"""Which completed sessions a narrowed affiliation interval would orphan.

Decision 2 forbids letting a date change silently invalidate the attribution
of a session that has already been delivered. The interval lives on the
affiliation, but the attribution lives on the session, so the check is
implemented here and injected into the affiliation use case.

Widening never orphans anything, and is answered without a query.
"""

from collections.abc import Sequence
from datetime import date

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.enums import SessionStatus
from app.domain.services.provider_calendar import PROVIDER_BOUNDARY_TIMEZONE
from app.domain.value_objects.core import TenantId
from app.domain.value_objects.provider_network import ProviderAffiliationId
from app.infrastructure.models.provider_affiliation_model import ProviderAffiliationModel
from app.infrastructure.models.service_session_model import ServiceSessionModel


class SqlAffiliationAttributionGuard:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def sessions_orphaned_by(
        self,
        tenant_id: TenantId,
        affiliation_id: ProviderAffiliationId,
        *,
        new_valid_until: date | None,
    ) -> Sequence[str]:
        if new_valid_until is None:
            return []
        current = await self._current_end(tenant_id, affiliation_id)
        if current is not None and new_valid_until >= current:
            return []
        return await self._completed_after(tenant_id, affiliation_id, new_valid_until)

    async def _current_end(
        self, tenant_id: TenantId, affiliation_id: ProviderAffiliationId
    ) -> date | None:
        result = await self.session.execute(
            select(ProviderAffiliationModel.valid_until).where(
                ProviderAffiliationModel.id == affiliation_id.value,
                ProviderAffiliationModel.tenant_id == tenant_id.value,
            )
        )
        return result.scalar_one_or_none()

    async def _completed_after(
        self,
        tenant_id: TenantId,
        affiliation_id: ProviderAffiliationId,
        new_valid_until: date,
    ) -> Sequence[str]:
        """Completed sessions scheduled on or after the new end date.

        The interval is end-exclusive, so a session on the new end date is
        already outside it. The scheduled instant is resolved to a day in the
        provider boundary timezone, the same way eligibility resolves it, so
        the two cannot disagree about which day a session falls on.
        """
        scheduled_day = ServiceSessionModel.scheduled_at.op("AT TIME ZONE")(
            PROVIDER_BOUNDARY_TIMEZONE.key
        )
        result = await self.session.execute(
            select(ServiceSessionModel.id)
            .where(
                ServiceSessionModel.tenant_id == tenant_id.value,
                ServiceSessionModel.provider_affiliation_id == affiliation_id.value,
                ServiceSessionModel.status == SessionStatus.COMPLETED,
                ServiceSessionModel.deleted_at.is_(None),
                scheduled_day >= new_valid_until,
            )
            .order_by(ServiceSessionModel.scheduled_at)
        )
        return [row for row in result.scalars().all()]
