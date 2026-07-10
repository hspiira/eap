"""DSAR aggregate + retention VO tests (Phase 4 #DSAR)."""

from datetime import UTC, datetime, timedelta

import pytest

from app.domain.entities.dsar_request import DSARRequest
from app.domain.enums import (
    DSARRequestStatus,
    DSARRequestType,
    RetentionDataClass,
)
from app.domain.events import (
    DSARRequestCompleted,
    DSARRequestSubmitted,
)
from app.domain.exceptions import DomainError, InvalidStateError
from app.domain.value_objects.core import (
    DSARRequestId,
    PersonId,
    TenantId,
    UserId,
)
from app.domain.value_objects.retention import (
    DEFAULT_RETENTION_POLICIES,
    RetentionPolicy,
    policy_for,
)


def _request(
    *,
    request_type: DSARRequestType = DSARRequestType.EXPORT,
    status: DSARRequestStatus = DSARRequestStatus.REQUESTED,
    erasure_executes_at: datetime | None = None,
) -> DSARRequest:
    now = datetime.now(UTC)
    return DSARRequest(
        id=DSARRequestId("dsar-1"),
        tenant_id=TenantId("t-1"),
        subject_person_id=PersonId("p-1"),
        request_type=request_type,
        status=status,
        requested_by=UserId("u-1"),
        erasure_executes_at=erasure_executes_at,
        created_at=now,
        updated_at=now,
    )


# ---------- Lifecycle ----------


class TestDSARLifecycle:
    def test_creation_emits_event(self):
        r = _request()
        assert any(isinstance(e, DSARRequestSubmitted) for e in r.events)

    def test_export_happy_path(self):
        r = _request()
        r.start()
        assert r.status == DSARRequestStatus.PROCESSING
        r.complete({"some": "bundle"})
        assert r.status == DSARRequestStatus.COMPLETED
        assert r.output == {"some": "bundle"}
        assert any(isinstance(e, DSARRequestCompleted) for e in r.events)

    def test_cannot_complete_before_start(self):
        r = _request()
        with pytest.raises(InvalidStateError):
            r.complete({})

    def test_cannot_start_completed(self):
        r = _request()
        r.start()
        r.complete({})
        with pytest.raises(InvalidStateError):
            r.start()

    def test_fail_requires_reason(self):
        r = _request()
        with pytest.raises(DomainError, match="reason"):
            r.fail("")

    def test_fail_from_processing(self):
        r = _request()
        r.start()
        r.fail("Data store unavailable")
        assert r.status == DSARRequestStatus.FAILED


# ---------- Erasure cancellation window ----------


class TestErasureCancelWindow:
    def test_cancel_succeeds_within_window(self):
        future = datetime.now(UTC) + timedelta(days=10)
        r = _request(
            request_type=DSARRequestType.ERASURE,
            erasure_executes_at=future,
        )
        r.cancel()
        assert r.status == DSARRequestStatus.CANCELLED

    def test_cannot_cancel_after_window(self):
        past = datetime.now(UTC) - timedelta(days=1)
        r = _request(
            request_type=DSARRequestType.ERASURE,
            erasure_executes_at=past,
        )
        with pytest.raises(DomainError, match="window has elapsed"):
            r.cancel()

    def test_cannot_cancel_export(self):
        r = _request()
        with pytest.raises(DomainError, match="Only erasure"):
            r.cancel()

    def test_is_within_reversible_window(self):
        future = datetime.now(UTC) + timedelta(days=5)
        r = _request(
            request_type=DSARRequestType.ERASURE,
            erasure_executes_at=future,
        )
        assert r.is_within_reversible_window() is True
        past = datetime.now(UTC) - timedelta(days=1)
        r2 = _request(
            request_type=DSARRequestType.ERASURE,
            erasure_executes_at=past,
        )
        assert r2.is_within_reversible_window() is False

    def test_no_window_means_not_reversible(self):
        r = _request(request_type=DSARRequestType.ERASURE)
        assert r.is_within_reversible_window() is False


# ---------- Retention policy ----------


class TestRetentionPolicy:
    def test_default_policies_cover_every_class(self):
        defined = {p.data_class for p in DEFAULT_RETENTION_POLICIES}
        assert defined == set(RetentionDataClass)

    def test_lookup_returns_matching_policy(self):
        p = policy_for(RetentionDataClass.AUDIT)
        assert p.data_class == RetentionDataClass.AUDIT
        assert p.days >= 1825  # ≥ 5 years

    def test_negative_days_rejected(self):
        with pytest.raises(DomainError):
            RetentionPolicy(
                data_class=RetentionDataClass.SESSIONS,
                days=-1,
                rationale="x",
            )

    def test_blank_rationale_rejected(self):
        with pytest.raises(DomainError):
            RetentionPolicy(
                data_class=RetentionDataClass.SESSIONS,
                days=10,
                rationale="",
            )
