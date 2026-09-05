"""Report query runner.

Routes the :class:`ReportQueryType` enum to a concrete async runner that
returns a JSON-serialisable result. The Phase 3 v1 renewal pack adds end-to-end
implementations for ``CONTRACT_UTILISATION``, ``CARE_CALLBACK_OUTCOMES``, and
``SATISFACTION_DISTRIBUTION`` and ``DIAGNOSIS_PREVALENCE``.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.report import TemplateSection
from app.domain.enums import ReportQueryType, SessionStatus
from app.domain.services.cell_suppression import (
    DEFAULT_MIN_CELL_SIZE,
    suppress_bucket_list,
    suppress_count,
    suppress_count_dict,
)
from app.infrastructure.models.care_callback_model import (
    CareCallbackCampaignModel,
    OutreachRecordModel,
)
from app.infrastructure.models.contract_model import ContractModel
from app.infrastructure.models.diagnosis_model import DiagnosisTypeModel
from app.infrastructure.models.service_session_model import ServiceSessionModel
from app.infrastructure.models.survey_model import (
    SurveyCampaignModel,
    SurveyResponseModel,
)
from app.infrastructure.models.utilisation_event_model import UtilisationEventModel


def prevalence_payload(
    rows: list[tuple[str, str, int]],
    *,
    unclassified: int,
    floor: int = DEFAULT_MIN_CELL_SIZE,
) -> dict[str, Any]:
    """Shape and suppress a diagnosis-prevalence result.

    ``unclassified`` is reported alongside the buckets so a small total is not
    read as low demand when it is really low recording.
    """
    buckets = [{"code": code, "label": name, "count": count} for code, name, count in rows]
    return {
        "query_type": ReportQueryType.DIAGNOSIS_PREVALENCE.value,
        "status": "ok" if rows else "no_data",
        "buckets": suppress_bucket_list(buckets, floor=floor),
        "total": suppress_count(sum(c for _, _, c in rows), floor=floor),
        "unclassified_sessions": suppress_count(unclassified, floor=floor),
    }


class ReportQueryRunner:
    """Dispatches a :class:`TemplateSection` to its query implementation."""

    def __init__(
        self,
        session: AsyncSession,
        *,
        min_cell_size: int = DEFAULT_MIN_CELL_SIZE,
    ):
        self._session = session
        self._min_cell_size = min_cell_size

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
        if section.query_type == ReportQueryType.CONTRACT_UTILISATION:
            return await self._contract_utilisation(tenant_id=tenant_id, params=params)
        if section.query_type == ReportQueryType.CARE_CALLBACK_OUTCOMES:
            return await self._care_callback_outcomes(tenant_id=tenant_id, params=params)
        if section.query_type == ReportQueryType.SATISFACTION_DISTRIBUTION:
            return await self._satisfaction_distribution(tenant_id=tenant_id, params=params)
        if section.query_type == ReportQueryType.DIAGNOSIS_PREVALENCE:
            return await self._diagnosis_prevalence(tenant_id=tenant_id, params=params)
        return {
            "query_type": section.query_type.value,
            "status": "not_implemented",
            "note": "Implementation lands with the providing aggregate (see SAD §5.2.10).",
        }

    async def _diagnosis_prevalence(
        self, *, tenant_id: str, params: dict[str, Any]
    ) -> dict[str, Any]:
        """Session counts per diagnosis type within an optional date window.

        Grouped at type level rather than by leaf diagnosis. There are 52 leaves
        against the seeded taxonomy, so leaf counts are sparse enough that most
        would fall under the suppression floor and say nothing.
        """
        stmt = (
            select(
                DiagnosisTypeModel.code.label("code"),
                DiagnosisTypeModel.name.label("name"),
                func.count().label("count"),
            )
            .join(
                ServiceSessionModel,
                ServiceSessionModel.diagnosis_type_id == DiagnosisTypeModel.id,
            )
            .where(
                ServiceSessionModel.tenant_id == tenant_id,
                ServiceSessionModel.deleted_at.is_(None),
            )
            .group_by(DiagnosisTypeModel.code, DiagnosisTypeModel.name)
            .order_by(func.count().desc(), DiagnosisTypeModel.name)
        )

        if params.get("status_in"):
            statuses = [SessionStatus(s).value for s in params["status_in"]]
            stmt = stmt.where(ServiceSessionModel.status.in_(statuses))
        else:
            stmt = stmt.where(ServiceSessionModel.status == SessionStatus.COMPLETED.value)

        from_date = _parse_date(params.get("from"))
        to_date = _parse_date(params.get("to"))
        if from_date:
            stmt = stmt.where(ServiceSessionModel.scheduled_at >= from_date)
        if to_date:
            stmt = stmt.where(ServiceSessionModel.scheduled_at <= to_date)

        rows = (await self._session.execute(stmt)).all()
        unclassified = await self._unclassified_session_count(
            tenant_id=tenant_id, params=params, from_date=from_date, to_date=to_date
        )
        return prevalence_payload(
            [(r.code, r.name, int(r.count)) for r in rows],
            unclassified=unclassified,
            floor=self._min_cell_size,
        )

    async def _unclassified_session_count(
        self,
        *,
        tenant_id: str,
        params: dict[str, Any],
        from_date: date | None,
        to_date: date | None,
    ) -> int:
        """Sessions in scope with no diagnosis type recorded.

        Reported alongside the buckets so a small total is not read as low
        demand when it is really low recording.
        """
        stmt = select(func.count()).where(
            ServiceSessionModel.tenant_id == tenant_id,
            ServiceSessionModel.deleted_at.is_(None),
            ServiceSessionModel.diagnosis_type_id.is_(None),
        )
        if params.get("status_in"):
            statuses = [SessionStatus(s).value for s in params["status_in"]]
            stmt = stmt.where(ServiceSessionModel.status.in_(statuses))
        else:
            stmt = stmt.where(ServiceSessionModel.status == SessionStatus.COMPLETED.value)
        if from_date:
            stmt = stmt.where(ServiceSessionModel.scheduled_at >= from_date)
        if to_date:
            stmt = stmt.where(ServiceSessionModel.scheduled_at <= to_date)
        return int((await self._session.execute(stmt)).scalar() or 0)

    async def _sessions_by_month(self, *, tenant_id: str, params: dict[str, Any]) -> dict[str, Any]:
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
            stmt = stmt.where(ServiceSessionModel.status == SessionStatus.COMPLETED.value)

        from_date = _parse_date(params.get("from"))
        to_date = _parse_date(params.get("to"))
        if from_date:
            stmt = stmt.where(ServiceSessionModel.scheduled_at >= from_date)
        if to_date:
            stmt = stmt.where(ServiceSessionModel.scheduled_at <= to_date)

        result = await self._session.execute(stmt)
        rows = [{"month": row.month, "count": row.count} for row in result]
        total = sum(r["count"] for r in rows)
        return {
            "query_type": ReportQueryType.SESSIONS_BY_MONTH.value,
            "buckets": suppress_bucket_list(rows, floor=self._min_cell_size),
            "total": suppress_count(total, floor=self._min_cell_size),
            "min_cell_size": self._min_cell_size,
        }

    async def _contract_utilisation(
        self, *, tenant_id: str, params: dict[str, Any]
    ) -> dict[str, Any]:
        """Sum utilisation units per contract within a date window.

        Optional ``client_id`` filter joins through ``contracts`` so a renewal pack
        can be scoped to one client. Returned buckets are sorted by total units desc.
        """
        stmt = (
            select(
                UtilisationEventModel.contract_id,
                func.sum(UtilisationEventModel.units).label("total_units"),
                func.count().label("event_count"),
            )
            .where(UtilisationEventModel.tenant_id == tenant_id)
            .group_by(UtilisationEventModel.contract_id)
        )
        client_id = params.get("client_id")
        if client_id:
            stmt = stmt.join(
                ContractModel, ContractModel.id == UtilisationEventModel.contract_id
            ).where(ContractModel.client_id == client_id)
        from_date = _parse_date(params.get("from"))
        to_date = _parse_date(params.get("to"))
        if from_date:
            stmt = stmt.where(UtilisationEventModel.occurred_on >= from_date)
        if to_date:
            stmt = stmt.where(UtilisationEventModel.occurred_on <= to_date)
        rows = (await self._session.execute(stmt)).all()
        buckets = [
            {
                "contract_id": r.contract_id,
                "total_units": int(r.total_units or 0),
                "event_count": int(r.event_count or 0),
            }
            for r in rows
        ]
        buckets.sort(key=lambda b: b["total_units"], reverse=True)
        total_units = sum(b["total_units"] for b in buckets)
        return {
            "query_type": ReportQueryType.CONTRACT_UTILISATION.value,
            "buckets": suppress_bucket_list(
                buckets, count_field="event_count", floor=self._min_cell_size
            ),
            "total_units": suppress_count(total_units, floor=self._min_cell_size),
            "min_cell_size": self._min_cell_size,
        }

    async def _care_callback_outcomes(
        self, *, tenant_id: str, params: dict[str, Any]
    ) -> dict[str, Any]:
        """Group outreach-record statuses across the tenant's campaigns.

        Optional ``client_id`` filter joins through ``care_callback_campaigns``;
        ``campaign_id`` narrows further to a single wave. Crisis-flag total is
        included so the renewal pack can headline counsellor-detected risk.
        """
        stmt = (
            select(
                OutreachRecordModel.status,
                func.count().label("count"),
            )
            .where(OutreachRecordModel.tenant_id == tenant_id)
            .group_by(OutreachRecordModel.status)
        )
        if params.get("campaign_id"):
            stmt = stmt.where(OutreachRecordModel.campaign_id == params["campaign_id"])
        elif params.get("client_id"):
            stmt = stmt.join(
                CareCallbackCampaignModel,
                CareCallbackCampaignModel.id == OutreachRecordModel.campaign_id,
            ).where(CareCallbackCampaignModel.client_id == params["client_id"])

        rows = (await self._session.execute(stmt)).all()
        by_status = {r.status: int(r.count) for r in rows}

        crisis_stmt = select(func.count()).where(
            OutreachRecordModel.tenant_id == tenant_id,
            OutreachRecordModel.crisis_flag.is_(True),
        )
        if params.get("campaign_id"):
            crisis_stmt = crisis_stmt.where(
                OutreachRecordModel.campaign_id == params["campaign_id"]
            )
        elif params.get("client_id"):
            crisis_stmt = crisis_stmt.join(
                CareCallbackCampaignModel,
                CareCallbackCampaignModel.id == OutreachRecordModel.campaign_id,
            ).where(CareCallbackCampaignModel.client_id == params["client_id"])
        crisis_flags = int((await self._session.execute(crisis_stmt)).scalar_one() or 0)

        total = sum(by_status.values())
        return {
            "query_type": ReportQueryType.CARE_CALLBACK_OUTCOMES.value,
            "by_status": suppress_count_dict(by_status, floor=self._min_cell_size),
            "total": suppress_count(total, floor=self._min_cell_size),
            "crisis_flags": suppress_count(crisis_flags, floor=self._min_cell_size),
            "min_cell_size": self._min_cell_size,
        }

    async def _satisfaction_distribution(
        self, *, tenant_id: str, params: dict[str, Any]
    ) -> dict[str, Any]:
        """Per-question answer-frequency tables across a tenant's survey responses.

        Reflects the same no-PII contract as ``GetSurveyAggregateUseCase``;
        the runner never returns individual response rows, only counts.
        Optional ``campaign_id`` or ``client_id`` filters scope the slice.
        """
        stmt = select(SurveyResponseModel.payload).where(SurveyResponseModel.tenant_id == tenant_id)
        if params.get("campaign_id"):
            stmt = stmt.where(SurveyResponseModel.campaign_id == params["campaign_id"])
        elif params.get("client_id"):
            stmt = stmt.join(
                SurveyCampaignModel,
                SurveyCampaignModel.id == SurveyResponseModel.campaign_id,
            ).where(SurveyCampaignModel.client_id == params["client_id"])

        per_question: dict[str, dict[str, int]] = {}
        total = 0
        for (payload,) in (await self._session.execute(stmt)).all():
            total += 1
            for k, v in (payload or {}).items():
                bucket = per_question.setdefault(k, {})
                key = str(v)
                bucket[key] = bucket.get(key, 0) + 1
        suppressed_freqs = {
            question: suppress_count_dict(answers, floor=self._min_cell_size)
            for question, answers in per_question.items()
        }
        return {
            "query_type": ReportQueryType.SATISFACTION_DISTRIBUTION.value,
            "answer_frequencies": suppressed_freqs,
            "response_total": suppress_count(total, floor=self._min_cell_size),
            "min_cell_size": self._min_cell_size,
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
