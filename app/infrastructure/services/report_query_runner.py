"""Report query runner (Phase 2 #D-Reports / SAD §5.2.10).

Routes the :class:`ReportQueryType` enum to a concrete async runner that
returns a JSON-serialisable result. v1 ships ``SESSIONS_BY_MONTH`` end-to-end
and stubs the others — those land alongside Care Callback (Phase 3) and the
contract pricing engine (D-Pricing) which provide the source data.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.report import TemplateSection
from app.domain.enums import ReportQueryType, SessionStatus
from app.infrastructure.models.service_session_model import ServiceSessionModel


class ReportQueryRunner:
    """Dispatches a :class:`TemplateSection` to its query implementation."""

    def __init__(self, session: AsyncSession):
        self._session = session

    async def run(
        self,
        section: TemplateSection,
        *,
        tenant_id: str,
        run_parameters: dict[str, Any],
    ) -> dict[str, Any]:
        params = {**section.parameters, **run_parameters}
        if section.query_type == ReportQueryType.SESSIONS_BY_MONTH:
            return await self._sessions_by_month(tenant_id=tenant_id, params=params)
        return {
            "query_type": section.query_type.value,
            "status": "not_implemented",
            "note": "Implementation lands with the providing aggregate (see SAD §5.2.10).",
        }

    async def _sessions_by_month(
        self, *, tenant_id: str, params: dict[str, Any]
    ) -> dict[str, Any]:
        """Count completed sessions per ``YYYY-MM`` within an optional date window."""
        stmt = (
            select(
                func.to_char(ServiceSessionModel.scheduled_at, "YYYY-MM").label("month"),
                func.count().label("count"),
            )
            .where(ServiceSessionModel.tenant_id == tenant_id)
            .group_by("month")
            .order_by("month")
        )

        if params.get("status_in"):
            statuses = [SessionStatus(s).value for s in params["status_in"]]
            stmt = stmt.where(ServiceSessionModel.status.in_(statuses))
        else:
            stmt = stmt.where(
                ServiceSessionModel.status == SessionStatus.COMPLETED.value
            )

        from_date = _parse_date(params.get("from"))
        to_date = _parse_date(params.get("to"))
        if from_date:
            stmt = stmt.where(ServiceSessionModel.scheduled_at >= from_date)
        if to_date:
            stmt = stmt.where(ServiceSessionModel.scheduled_at <= to_date)

        result = await self._session.execute(stmt)
        rows = [{"month": row.month, "count": row.count} for row in result]
        return {
            "query_type": ReportQueryType.SESSIONS_BY_MONTH.value,
            "buckets": rows,
            "total": sum(r["count"] for r in rows),
        }


def _parse_date(value: Any) -> date | datetime | None:
    if value is None or isinstance(value, (date, datetime)):
        return value
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value)
        except ValueError:
            return date.fromisoformat(value)
    return None
