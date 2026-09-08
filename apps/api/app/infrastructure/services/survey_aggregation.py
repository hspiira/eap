"""Counts survey answers in PostgreSQL, one grouped query per approved question.

Aggregating in the database keeps the result exact for a campaign of any size
and keeps the raw payloads, free text included, out of the application process.
Only the approved choices are selected, so the number of returned rows is
bounded by the campaign's own configuration rather than by its response count.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.survey_campaign import ApprovedQuestion
from app.domain.services.survey_disclosure import AnswerTally
from app.infrastructure.models.survey_model import SurveyResponseModel


class SurveyAnswerTallyReaderImpl:
    """SQL implementation of :class:`SurveyAnswerTallyReader`."""

    def __init__(self, session: AsyncSession):
        self._session = session

    async def count_responses(
        self,
        *,
        tenant_id: str,
        campaign_id: str,
        since: datetime | None = None,
        until: datetime | None = None,
    ) -> int:
        stmt = self._scoped(
            select(func.count()).select_from(SurveyResponseModel),
            tenant_id=tenant_id,
            campaign_id=campaign_id,
            since=since,
            until=until,
        )
        return int((await self._session.execute(stmt)).scalar_one() or 0)

    async def tally(
        self,
        *,
        tenant_id: str,
        campaign_id: str,
        question: ApprovedQuestion,
        since: datetime | None = None,
        until: datetime | None = None,
    ) -> AnswerTally:
        answer = SurveyResponseModel.payload[question.key].astext
        choices = list(question.choices)

        grouped = self._scoped(
            select(answer.label("answer"), func.count().label("count")).select_from(
                SurveyResponseModel
            ),
            tenant_id=tenant_id,
            campaign_id=campaign_id,
            since=since,
            until=until,
        ).where(answer.in_(choices))
        rows = (await self._session.execute(grouped.group_by(answer))).all()

        off_list = self._scoped(
            select(func.count()).select_from(SurveyResponseModel),
            tenant_id=tenant_id,
            campaign_id=campaign_id,
            since=since,
            until=until,
        ).where(answer.is_not(None), answer.notin_(choices))
        unapproved = int((await self._session.execute(off_list)).scalar_one() or 0)

        return AnswerTally(
            counts={row.answer: int(row.count) for row in rows},
            unapproved=unapproved,
        )

    def _scoped(
        self,
        stmt: Select[Any],
        *,
        tenant_id: str,
        campaign_id: str,
        since: datetime | None,
        until: datetime | None,
    ) -> Select[Any]:
        stmt = stmt.where(
            SurveyResponseModel.tenant_id == tenant_id,
            SurveyResponseModel.campaign_id == campaign_id,
        )
        if since is not None:
            stmt = stmt.where(SurveyResponseModel.submitted_at >= since)
        if until is not None:
            stmt = stmt.where(SurveyResponseModel.submitted_at < until)
        return stmt
