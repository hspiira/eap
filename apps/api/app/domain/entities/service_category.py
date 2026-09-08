"""Service category taxonomy entity.

Coarse grouping used by EAP programme caps and authorization rules. Global and
curated centrally, mirroring the diagnosis taxonomy's ``DiagnosisType``:
writes are platform-admin only, and retirement is dated rather than deleted so
a service or authorization already carrying the code is never orphaned.
"""

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class ServiceCategory:
    id: str
    code: str
    name: str
    description: str | None
    sort_order: int
    is_active: bool
    version: int
    effective_until: datetime | None
