"""Retry eligibility for client import jobs."""

from datetime import UTC, datetime, timedelta

from app.api.routes.clients import STALE_IMPORT_AFTER, _is_retryable
from app.infrastructure.models.client_import_job_model import ClientImportJobModel
from app.shared.utils.datetime import utc_now


def _job(status: str, started_at: datetime | None = None) -> ClientImportJobModel:
    return ClientImportJobModel(
        id="job-1",
        tenant_id="tenant-1",
        requested_by="user-1",
        filename="clients.csv",
        file_size=10,
        file_content=b"name\n",
        decisions={},
        status=status,
        started_at=started_at,
        issues=[],
    )


class TestRetryEligibility:
    def test_a_failed_job_can_be_retried(self):
        assert _is_retryable(_job("failed")) is True

    def test_a_completed_job_cannot_be_retried(self):
        assert _is_retryable(_job("completed")) is False

    def test_a_queued_job_cannot_be_retried(self):
        assert _is_retryable(_job("queued")) is False

    def test_a_job_still_running_cannot_be_retried(self):
        recent = utc_now() - (STALE_IMPORT_AFTER / 2)
        assert _is_retryable(_job("processing", recent)) is False

    def test_a_job_abandoned_mid_run_can_be_retried(self):
        stale = utc_now() - (STALE_IMPORT_AFTER + timedelta(minutes=1))
        assert _is_retryable(_job("processing", stale)) is True

    def test_a_processing_job_without_a_start_time_can_be_retried(self):
        assert _is_retryable(_job("processing", None)) is True

    def test_a_naive_start_time_is_treated_as_utc(self):
        stale_naive = (utc_now() - (STALE_IMPORT_AFTER + timedelta(minutes=1))).replace(tzinfo=None)
        assert _is_retryable(_job("processing", stale_naive)) is True

        fresh_naive = datetime.now(UTC).replace(tzinfo=None)
        assert _is_retryable(_job("processing", fresh_naive)) is False
