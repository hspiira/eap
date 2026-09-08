"""Report query runner.

Routes the :class:`ReportQueryType` enum to a concrete async runner that
returns a JSON-serialisable result.

Every section is scoped by the same :class:`ReportContext`: tenant, optional
client, period and timezone, plus the soft-deletion predicate where the table
has one. Each result carries the scope it applied, including any parameter the
section could not use, so the reader sees the server's scope rather than the
one the page asked for.
"""

from __future__ import annotations

from typing import Any

from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.report import TemplateSection
from app.domain.entities.survey_campaign import ApprovedQuestion
from app.domain.enums import ReportQueryType, SessionStatus
from app.domain.exceptions import DomainError
from app.domain.services.cell_suppression import (
    DEFAULT_MIN_CELL_SIZE,
    suppress_bucket_list,
    suppress_count,
    suppress_count_dict,
)
from app.domain.services.report_context import ReportContext, build_report_context
from app.domain.services.survey_disclosure import AnswerTally, aggregate_payload
from app.infrastructure.mappers.survey_mapper import approved_questions_from_json
from app.infrastructure.models.care_callback_model import (
    CareCallbackCampaignModel,
    OutreachRecordModel,
)
from app.infrastructure.models.contract_model import ContractModel
from app.infrastructure.models.diagnosis_model import DiagnosisTypeModel
from app.infrastructure.models.eligible_member_model import EligibleMemberModel
from app.infrastructure.models.service_session_model import ServiceSessionModel
from app.infrastructure.models.survey_model import SurveyCampaignModel
from app.infrastructure.models.utilisation_event_model import UtilisationEventModel
from app.infrastructure.services.survey_aggregation import SurveyAnswerTallyReaderImpl


def prevalence_payload(
    rows: list[tuple[str, str, int]],
    *,
    unclassified: int,
    floor: int = DEFAULT_MIN_CELL_SIZE,
    scope: dict[str, Any] | None = None,
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
        "min_cell_size": floor,
        "scope": scope or {},
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
        context = build_report_context(
            tenant_id=tenant_id,
            parameters={**section.parameters, **run_parameters},
        )
        runners = {
            ReportQueryType.SESSIONS_BY_MONTH: self._sessions_by_month,
            ReportQueryType.CONTRACT_UTILISATION: self._contract_utilisation,
            ReportQueryType.CARE_CALLBACK_OUTCOMES: self._care_callback_outcomes,
            ReportQueryType.SATISFACTION_DISTRIBUTION: self._satisfaction_distribution,
            ReportQueryType.DIAGNOSIS_PREVALENCE: self._diagnosis_prevalence,
        }
        runner = runners.get(section.query_type)
        if runner is None:
            return {
                "query_type": section.query_type.value,
                "status": "not_implemented",
                "note": "Implementation lands with the providing aggregate (see SAD §5.2.10).",
                "scope": context.scope(),
            }
        return await runner(context)

    # ------------------------------------------------------------------
    # Sessions
    # ------------------------------------------------------------------

    def _scoped_sessions(self, stmt: Select[Any], context: ReportContext) -> Select[Any]:
        """Tenant, client, live rows and the period, applied the same way everywhere."""
        stmt = stmt.where(
            ServiceSessionModel.tenant_id == context.tenant_id,
            ServiceSessionModel.deleted_at.is_(None),
        )
        if context.client_id:
            stmt = stmt.join(
                EligibleMemberModel,
                EligibleMemberModel.id == ServiceSessionModel.member_id,
            ).where(
                EligibleMemberModel.tenant_id == context.tenant_id,
                EligibleMemberModel.client_id == context.client_id,
            )
        statuses = (
            [SessionStatus(s).value for s in context.status_in]
            if context.status_in
            else [SessionStatus.COMPLETED.value]
        )
        stmt = stmt.where(ServiceSessionModel.status.in_(statuses))
        start, end = context.start_at(), context.end_before()
        if start is not None:
            stmt = stmt.where(ServiceSessionModel.scheduled_at >= start)
        if end is not None:
            stmt = stmt.where(ServiceSessionModel.scheduled_at < end)
        return stmt

    async def _sessions_by_month(self, context: ReportContext) -> dict[str, Any]:
        """Count sessions per ``YYYY-MM`` in the report timezone."""
        month = func.to_char(
            func.timezone(context.timezone, ServiceSessionModel.scheduled_at), "YYYY-MM"
        )
        stmt = self._scoped_sessions(
            select(month.label("month"), func.count().label("count")).select_from(
                ServiceSessionModel
            ),
            context,
        )
        rows = (await self._session.execute(stmt.group_by(month).order_by(month))).all()
        buckets = [{"month": row.month, "count": int(row.count)} for row in rows]
        total = sum(b["count"] for b in buckets)
        return {
            "query_type": ReportQueryType.SESSIONS_BY_MONTH.value,
            "status": "ok" if buckets else "no_data",
            "buckets": suppress_bucket_list(buckets, floor=self._min_cell_size),
            "total": suppress_count(total, floor=self._min_cell_size),
            "min_cell_size": self._min_cell_size,
            "scope": context.scope(ignored=_ignored(context, supports_campaign=False)),
        }

    async def _diagnosis_prevalence(self, context: ReportContext) -> dict[str, Any]:
        """Session counts per diagnosis type within the report scope.

        Grouped at type level rather than by leaf diagnosis. There are 52 leaves
        against the seeded taxonomy, so leaf counts are sparse enough that most
        would fall under the suppression floor and say nothing.
        """
        stmt = self._scoped_sessions(
            select(
                DiagnosisTypeModel.code.label("code"),
                DiagnosisTypeModel.name.label("name"),
                func.count().label("count"),
            )
            .select_from(ServiceSessionModel)
            .join(
                DiagnosisTypeModel,
                DiagnosisTypeModel.id == ServiceSessionModel.diagnosis_type_id,
            ),
            context,
        )
        stmt = stmt.group_by(DiagnosisTypeModel.code, DiagnosisTypeModel.name).order_by(
            func.count().desc(), DiagnosisTypeModel.name
        )
        rows = (await self._session.execute(stmt)).all()
        unclassified = await self._unclassified_session_count(context)
        return prevalence_payload(
            [(r.code, r.name, int(r.count)) for r in rows],
            unclassified=unclassified,
            floor=self._min_cell_size,
            scope=context.scope(ignored=_ignored(context, supports_campaign=False)),
        )

    async def _unclassified_session_count(self, context: ReportContext) -> int:
        """Sessions in scope with no diagnosis type recorded."""
        stmt = self._scoped_sessions(
            select(func.count()).select_from(ServiceSessionModel), context
        ).where(ServiceSessionModel.diagnosis_type_id.is_(None))
        return int((await self._session.execute(stmt)).scalar() or 0)

    # ------------------------------------------------------------------
    # Commercial
    # ------------------------------------------------------------------

    async def _contract_utilisation(self, context: ReportContext) -> dict[str, Any]:
        """Sum utilisation units per live contract within the period.

        Always joined to ``contracts`` so a retired contract's units cannot
        appear, and so the client scope is the contract's own client.
        """
        stmt = (
            select(
                UtilisationEventModel.contract_id,
                func.sum(UtilisationEventModel.units).label("total_units"),
                func.count().label("event_count"),
            )
            .select_from(UtilisationEventModel)
            .join(ContractModel, ContractModel.id == UtilisationEventModel.contract_id)
            .where(
                UtilisationEventModel.tenant_id == context.tenant_id,
                ContractModel.tenant_id == context.tenant_id,
                ContractModel.deleted_at.is_(None),
            )
            .group_by(UtilisationEventModel.contract_id)
        )
        if context.client_id:
            stmt = stmt.where(ContractModel.client_id == context.client_id)
        if context.date_from is not None:
            stmt = stmt.where(UtilisationEventModel.occurred_on >= context.date_from)
        if context.date_to is not None:
            stmt = stmt.where(UtilisationEventModel.occurred_on <= context.date_to)

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
            "status": "ok" if buckets else "no_data",
            "buckets": suppress_bucket_list(
                buckets, count_field="event_count", floor=self._min_cell_size
            ),
            "total_units": suppress_count(total_units, floor=self._min_cell_size),
            "min_cell_size": self._min_cell_size,
            "scope": context.scope(ignored=_ignored(context, supports_campaign=False)),
        }

    # ------------------------------------------------------------------
    # Care callbacks
    # ------------------------------------------------------------------

    def _scoped_outreach(self, stmt: Select[Any], context: ReportContext) -> Select[Any]:
        """Records of the tenant's campaigns for this client, within the period.

        The period selects the waves that opened inside it: an outreach record
        has no business date of its own, and its campaign's ``period_start``
        places the wave without double-counting one that straddles the window.
        """
        stmt = (
            stmt.select_from(OutreachRecordModel)
            .join(
                CareCallbackCampaignModel,
                CareCallbackCampaignModel.id == OutreachRecordModel.campaign_id,
            )
            .where(
                OutreachRecordModel.tenant_id == context.tenant_id,
                CareCallbackCampaignModel.tenant_id == context.tenant_id,
            )
        )
        if context.client_id:
            stmt = stmt.where(CareCallbackCampaignModel.client_id == context.client_id)
        if context.campaign_id:
            stmt = stmt.where(OutreachRecordModel.campaign_id == context.campaign_id)
        if context.date_from is not None:
            stmt = stmt.where(CareCallbackCampaignModel.period_start >= context.date_from)
        if context.date_to is not None:
            stmt = stmt.where(CareCallbackCampaignModel.period_start <= context.date_to)
        return stmt

    async def _care_callback_outcomes(self, context: ReportContext) -> dict[str, Any]:
        """Group outreach-record statuses, with the crisis-flag count alongside."""
        await self._require_campaign_in_scope(
            CareCallbackCampaignModel, context, label="care callback campaign"
        )
        grouped = self._scoped_outreach(
            select(OutreachRecordModel.status, func.count().label("count")), context
        ).group_by(OutreachRecordModel.status)
        rows = (await self._session.execute(grouped)).all()
        by_status = {r.status: int(r.count) for r in rows}

        crisis_stmt = self._scoped_outreach(select(func.count()), context).where(
            OutreachRecordModel.crisis_flag.is_(True)
        )
        crisis_flags = int((await self._session.execute(crisis_stmt)).scalar() or 0)

        total = sum(by_status.values())
        return {
            "query_type": ReportQueryType.CARE_CALLBACK_OUTCOMES.value,
            "status": "ok" if by_status else "no_data",
            "by_status": suppress_count_dict(by_status, floor=self._min_cell_size),
            "total": suppress_count(total, floor=self._min_cell_size),
            "crisis_flags": suppress_count(crisis_flags, floor=self._min_cell_size),
            "min_cell_size": self._min_cell_size,
            "scope": context.scope(ignored=_ignored(context, supports_campaign=True)),
        }

    # ------------------------------------------------------------------
    # Surveys
    # ------------------------------------------------------------------

    async def _satisfaction_distribution(self, context: ReportContext) -> dict[str, Any]:
        """Answer frequencies over the approved questions of the campaigns in scope.

        Same disclosure policy as the campaign aggregate endpoint: approved
        questions only, approved choices only, every cell and total suppressed.
        """
        await self._require_campaign_in_scope(SurveyCampaignModel, context, label="survey campaign")
        campaigns = await self._campaigns_in_scope(context)
        reader = SurveyAnswerTallyReaderImpl(self._session)
        since, until = context.start_at(), context.end_before()

        questions: dict[str, ApprovedQuestion] = {}
        tallies: dict[str, AnswerTally] = {}
        response_total = 0
        for campaign_id, approved in campaigns:
            response_total += await reader.count_responses(
                tenant_id=context.tenant_id,
                campaign_id=campaign_id,
                since=since,
                until=until,
            )
            for question in approved:
                questions.setdefault(question.key, question)
                tally = await reader.tally(
                    tenant_id=context.tenant_id,
                    campaign_id=campaign_id,
                    question=question,
                    since=since,
                    until=until,
                )
                tallies[question.key] = tallies.get(question.key, AnswerTally()).merged_with(tally)

        payload = aggregate_payload(
            questions=list(questions.values()),
            tallies=tallies,
            response_total=response_total,
            floor=self._min_cell_size,
        )
        return {
            "query_type": ReportQueryType.SATISFACTION_DISTRIBUTION.value,
            "status": "ok" if campaigns else "no_data",
            **payload,
            "scope": context.scope(ignored=_ignored(context, supports_campaign=True)),
        }

    async def _campaigns_in_scope(
        self, context: ReportContext
    ) -> list[tuple[str, list[ApprovedQuestion]]]:
        stmt = select(SurveyCampaignModel.id, SurveyCampaignModel.approved_questions).where(
            SurveyCampaignModel.tenant_id == context.tenant_id
        )
        if context.client_id:
            stmt = stmt.where(SurveyCampaignModel.client_id == context.client_id)
        if context.campaign_id:
            stmt = stmt.where(SurveyCampaignModel.id == context.campaign_id)
        rows = (await self._session.execute(stmt)).all()
        return [(row.id, approved_questions_from_json(row.approved_questions)) for row in rows]

    # ------------------------------------------------------------------

    async def _require_campaign_in_scope(
        self,
        model: type[CareCallbackCampaignModel] | type[SurveyCampaignModel],
        context: ReportContext,
        *,
        label: str,
    ) -> None:
        """A named campaign must belong to the requested tenant and client."""
        if not context.campaign_id:
            return
        stmt = (
            select(func.count())
            .select_from(model)
            .where(
                model.id == context.campaign_id,
                model.tenant_id == context.tenant_id,
            )
        )
        if context.client_id:
            stmt = stmt.where(model.client_id == context.client_id)
        if int((await self._session.execute(stmt)).scalar() or 0) == 0:
            raise DomainError(
                f"Report parameter 'campaign_id' does not name a {label} "
                "in the requested tenant and client"
            )


def _ignored(context: ReportContext, *, supports_campaign: bool) -> list[str]:
    if context.campaign_id and not supports_campaign:
        return ["campaign_id"]
    return []
