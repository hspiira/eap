"""Survey source taxonomy entity.

Replaces the ``SurveySource`` enum, whose docstring already called it
"extensible". Mirrors ``ServiceCategory``/``DiagnosisType``: global, curated
centrally, writes are platform-admin only, retirement is dated rather than
deleted.
"""

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class SurveySource:
    id: str
    code: str
    name: str
    description: str | None
    sort_order: int
    is_active: bool
    version: int
    effective_until: datetime | None
