"""Per-tenant metric collector for cross-tenant benchmarking (Phase 4 #D-Benchmark)."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.enums import BenchmarkScope, SessionStatus
from app.domain.value_objects.core import TenantId
from app.infrastructure.models.care_callback_model import OutreachRecordModel
from app.infrastructure.models.service_session_model import ServiceSessionModel
from app.infrastructure.models.survey_model import SurveyResponseModel


class SqlBenchmarkCollector:
    """Computes one numeric value per consenting tenant for the requested scope.

    The shape is deliberately simple — one number per tenant — so the cross-tenant
    aggregator and the k-anon gate stay focused on disclosure rules rather than
    metric semantics. New metrics extend the dispatch table below.
    """

    def __init__(self, session: AsyncSession):
        self._session = session

    async def per_tenant_values(
        self,
        *,
        tenant_ids: list[TenantId],
        scope: BenchmarkScope,
        from_date: datetime | None,
        to_date: datetime | None,
    ) -> dict[str, float]:
        if not tenant_ids:
            return {}
        ids = [t.value for t in tenant_ids]
        if scope == BenchmarkScope.SESSION_VOLUME:
            return await self._session_volume(ids, from_date, to_date)
        if scope == BenchmarkScope.CARE_CALLBACK_OUTCOMES:
            return await self._callback_completion(ids)
        if scope == BenchmarkScope.SATISFACTION:
            return await self._satisfaction(ids)
        # UTILISATION_RATES requires per-tenant client/contract joins that aren't
        # in the v1 contract scope; return empty so the cross-tenant aggregator
        # surfaces a "no contributors" suppression rather than a false zero.
        return {}

    async def _session_volume(
        self,
        tenant_ids: list[str],
        from_date: datetime | None,
        to_date: datetime | None,
    ) -> dict[str, float]:
        stmt = (
            select(
                ServiceSessionModel.tenant_id,
                func.count().label("count"),
            )
            .where(
                ServiceSessionModel.tenant_id.in_(tenant_ids),
                ServiceSessionModel.status == SessionStatus.COMPLETED.value,
            )
            .group_by(ServiceSessionModel.tenant_id)
        )
        if from_date is not None:
            stmt = stmt.where(ServiceSessionModel.scheduled_at >= from_date)
        if to_date is not None:
            stmt = stmt.where(ServiceSessionModel.scheduled_at <= to_date)
        rows = (await self._session.execute(stmt)).all()
        return {r.tenant_id: float(r.count or 0) for r in rows}

    async def _callback_completion(
        self, tenant_ids: list[str]
    ) -> dict[str, float]:
        # Per-tenant completion rate: completed / (total - pending).
        # Tenants with no callback activity are omitted (excluded from k-anon count).
        stmt = (
            select(
                OutreachRecordModel.tenant_id,
                OutreachRecordModel.status,
                func.count().label("count"),
            )
            .where(OutreachRecordModel.tenant_id.in_(tenant_ids))
            .group_by(
                OutreachRecordModel.tenant_id, OutreachRecordModel.status
            )
        )
        rows = (await self._session.execute(stmt)).all()
        per_tenant: dict[str, dict[str, int]] = {}
        for r in rows:
            per_tenant.setdefault(r.tenant_id, {})[r.status] = int(r.count)
        out: dict[str, float] = {}
        for tid, status_counts in per_tenant.items():
            terminal = sum(
                v for k, v in status_counts.items() if k != "Pending"
            )
            if terminal == 0:
                continue
            completed = status_counts.get("Completed", 0)
            out[tid] = completed / terminal
        return out

    async def _satisfaction(self, tenant_ids: list[str]) -> dict[str, float]:
        # v1 satisfaction score: count of survey responses per tenant. A future
        # iteration can compute a numeric score once instruments standardise.
        stmt = (
            select(
                SurveyResponseModel.tenant_id,
                func.count().label("count"),
            )
            .where(SurveyResponseModel.tenant_id.in_(tenant_ids))
            .group_by(SurveyResponseModel.tenant_id)
        )
        rows = (await self._session.execute(stmt)).all()
        return {r.tenant_id: float(r.count or 0) for r in rows}
