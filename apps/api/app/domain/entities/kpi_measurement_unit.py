"""KPI measurement unit taxonomy entity.

Replaces the ``KPIMeasurementUnit`` enum. Mirrors ``ServiceCategory``/
``DiagnosisType``: global, curated centrally, writes are platform-admin only,
retirement is dated rather than deleted.
"""

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class KPIMeasurementUnit:
    id: str
    code: str
    name: str
    description: str | None
    sort_order: int
    is_active: bool
    version: int
    effective_until: datetime | None
