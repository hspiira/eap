"""Case referral source taxonomy entity.

Replaces the ``CaseReferralSource`` enum. Mirrors ``ServiceCategory``/
``DiagnosisType``: global, curated centrally, writes are platform-admin only,
retirement is dated rather than deleted.
"""

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class CaseReferralSource:
    id: str
    code: str
    name: str
    description: str | None
    sort_order: int
    is_active: bool
    version: int
    effective_until: datetime | None
