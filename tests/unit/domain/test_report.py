"""Report template + run entity tests (Phase 2 #D-Reports)."""

from datetime import UTC, datetime

import pytest

from app.domain.entities.report import (
    ReportRun,
    ReportTemplate,
    TemplateSection,
)
from app.domain.enums import ReportQueryType, ReportRunStatus
from app.domain.exceptions import DomainError
from app.domain.value_objects.core import (
    ReportRunId,
    ReportTemplateId,
    TenantId,
    UserId,
)


def _section(
    *,
    title: str = "Sessions",
    query_type: ReportQueryType = ReportQueryType.SESSIONS_BY_MONTH,
) -> TemplateSection:
    return TemplateSection(title=title, query_type=query_type)


_UNSET: object = object()


def _template(
    *, sections: list[TemplateSection] | object = _UNSET
) -> ReportTemplate:
    now = datetime.now(UTC)
    if sections is _UNSET:
        sections = [_section()]
    return ReportTemplate(
        id=ReportTemplateId("rt-1"),
        tenant_id=TenantId("t-1"),
        code="RENEWAL_PACK",
        name="Renewal Pack",
        sections=sections,  # type: ignore[arg-type]
        is_active=True,
        created_at=now,
        updated_at=now,
    )


def _run(
    *,
    status: ReportRunStatus = ReportRunStatus.PENDING,
) -> ReportRun:
    now = datetime.now(UTC)
    return ReportRun(
        id=ReportRunId("rr-1"),
        tenant_id=TenantId("t-1"),
        template_id=ReportTemplateId("rt-1"),
        requested_by=UserId("u-1"),
        parameters={},
        status=status,
        created_at=now,
        updated_at=now,
    )


class TestReportTemplate:
    def test_must_have_at_least_one_section(self):
        with pytest.raises(DomainError):
            _template(sections=[])

    def test_section_title_required(self):
        with pytest.raises(DomainError):
            TemplateSection(title="", query_type=ReportQueryType.SESSIONS_BY_MONTH)

    def test_deactivate_then_activate(self):
        t = _template()
        t.deactivate()
        assert t.is_active is False
        t.activate()
        assert t.is_active is True

    def test_double_deactivate_rejected(self):
        t = _template()
        t.deactivate()
        with pytest.raises(DomainError):
            t.deactivate()


class TestReportRun:
    def test_pending_to_running_to_completed(self):
        run = _run()
        run.mark_running()
        assert run.status == ReportRunStatus.RUNNING
        assert run.started_at is not None
        run.mark_completed({"sections": []})
        assert run.status == ReportRunStatus.COMPLETED
        assert run.output == {"sections": []}
        assert run.completed_at is not None

    def test_cannot_complete_if_not_running(self):
        run = _run()
        with pytest.raises(DomainError):
            run.mark_completed({})

    def test_failure_records_error(self):
        run = _run()
        run.mark_running()
        run.mark_failed("query timeout")
        assert run.status == ReportRunStatus.FAILED
        assert run.error == "query timeout"

    def test_failure_requires_error_message(self):
        run = _run()
        run.mark_running()
        with pytest.raises(DomainError):
            run.mark_failed("")

    def test_cannot_run_twice(self):
        run = _run()
        run.mark_running()
        with pytest.raises(DomainError):
            run.mark_running()
