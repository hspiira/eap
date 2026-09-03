"""Benchmark API schemas (Phase 4 #D-Benchmark)."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.api.schemas.base import SanitizedStr
from app.domain.enums import BenchmarkScope, TenantConsentStatus


class GrantConsentRequest(BaseModel):
    scope: BenchmarkScope
    version: SanitizedStr = Field(..., min_length=1, max_length=50)


class WithdrawConsentRequest(BaseModel):
    reason: SanitizedStr = Field(..., min_length=1, max_length=500)


class BenchmarkConsentResponse(BaseModel):
    id: str
    tenant_id: str
    scope: BenchmarkScope
    status: TenantConsentStatus
    version: str
    granted_by: str
    granted_at: datetime
    withdrawn_at: datetime | None
    withdrawn_by: str | None
    withdrawn_reason: str | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class BenchmarkResultResponse(BaseModel):
    metric_code: str
    contributor_count: int
    floor: int
    suppressed: bool
    suppression_reason: str | None
    value: Any | None
