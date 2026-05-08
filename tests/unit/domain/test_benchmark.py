"""Benchmark consent + k-anonymity tests (Phase 4 #D-Benchmark)."""

from datetime import UTC, datetime

import pytest

from app.domain.entities.benchmark_consent import BenchmarkConsent
from app.domain.enums import BenchmarkScope, TenantConsentStatus
from app.domain.exceptions import DomainError, InvalidStateError
from app.domain.services.k_anonymity import (
    K_ANON_FLOOR,
    enforce_k_anonymity,
)
from app.domain.value_objects.core import (
    BenchmarkConsentId,
    TenantId,
    UserId,
)


def _consent(
    *, status: TenantConsentStatus = TenantConsentStatus.ACTIVE
) -> BenchmarkConsent:
    now = datetime.now(UTC)
    return BenchmarkConsent(
        id=BenchmarkConsentId("c-1"),
        tenant_id=TenantId("t-1"),
        scope=BenchmarkScope.SESSION_VOLUME,
        status=status,
        version="2026-05",
        granted_by=UserId("u-admin"),
        granted_at=now,
        created_at=now,
        updated_at=now,
        withdrawn_at=now if status == TenantConsentStatus.WITHDRAWN else None,
    )


# ---------- Consent FSM ----------


class TestConsentFSM:
    def test_currently_consented(self):
        c = _consent()
        assert c.is_currently_consented() is True

    def test_withdraw(self):
        c = _consent()
        c.withdraw(actor=UserId("u-admin"), reason="audit complete")
        assert c.status == TenantConsentStatus.WITHDRAWN
        assert c.withdrawn_at is not None
        assert c.is_currently_consented() is False

    def test_cannot_double_withdraw(self):
        c = _consent(status=TenantConsentStatus.WITHDRAWN)
        with pytest.raises(InvalidStateError):
            c.withdraw(actor=UserId("u-admin"), reason="x")

    def test_withdraw_requires_reason(self):
        c = _consent()
        with pytest.raises(DomainError, match="reason"):
            c.withdraw(actor=UserId("u-admin"), reason="")

    def test_version_required(self):
        now = datetime.now(UTC)
        with pytest.raises(DomainError, match="version"):
            BenchmarkConsent(
                id=BenchmarkConsentId("c-1"),
                tenant_id=TenantId("t-1"),
                scope=BenchmarkScope.SESSION_VOLUME,
                status=TenantConsentStatus.ACTIVE,
                version="",
                granted_by=UserId("u-admin"),
                granted_at=now,
                created_at=now,
                updated_at=now,
            )

    def test_withdrawn_status_requires_timestamp(self):
        now = datetime.now(UTC)
        with pytest.raises(DomainError, match="withdrawn_at"):
            BenchmarkConsent(
                id=BenchmarkConsentId("c-1"),
                tenant_id=TenantId("t-1"),
                scope=BenchmarkScope.SESSION_VOLUME,
                status=TenantConsentStatus.WITHDRAWN,
                version="v1",
                granted_by=UserId("u-admin"),
                granted_at=now,
                created_at=now,
                updated_at=now,
            )


# ---------- K-anonymity ----------


class TestKAnonymity:
    def test_default_floor_is_ten(self):
        assert K_ANON_FLOOR == 10

    def test_suppresses_below_floor(self):
        out = enforce_k_anonymity(
            metric_code="x", contributor_count=5, value={"mean": 7}
        )
        assert out.suppressed is True
        assert out.is_disclosed() is False
        assert out.value is None
        assert "5" in (out.suppression_reason or "")

    def test_discloses_at_floor(self):
        out = enforce_k_anonymity(
            metric_code="x", contributor_count=10, value={"mean": 7}
        )
        assert out.suppressed is False
        assert out.value == {"mean": 7}

    def test_above_floor(self):
        out = enforce_k_anonymity(
            metric_code="x", contributor_count=42, value={"mean": 9}
        )
        assert out.is_disclosed() is True
        assert out.contributor_count == 42

    def test_zero_contributors_suppressed(self):
        out = enforce_k_anonymity(
            metric_code="x", contributor_count=0, value=None
        )
        assert out.suppressed is True

    def test_floor_override_for_testing(self):
        out = enforce_k_anonymity(
            metric_code="x",
            contributor_count=2,
            value={"mean": 1},
            floor=2,
        )
        assert out.suppressed is False
