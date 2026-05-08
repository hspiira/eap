"""Diagnosis taxonomy entities (Phase 2 #D-Tax)."""

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class DiagnosisType:
    """Top-level category in the diagnosis taxonomy."""

    id: str
    code: str
    name: str
    description: str | None
    sort_order: int
    is_active: bool
    version: int
    effective_until: datetime | None


@dataclass(frozen=True)
class Diagnosis:
    """Specific diagnosis under a :class:`DiagnosisType`."""

    id: str
    type_id: str
    code: str
    name: str
    description: str | None
    sort_order: int
    is_active: bool
    version: int
    effective_until: datetime | None
