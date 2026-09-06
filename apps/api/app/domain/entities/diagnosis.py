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


@dataclass(frozen=True)
class TenantOverlay:
    """One tenant's preference for a taxonomy row.

    A missing overlay means enabled at the taxonomy's own sort order.
    """

    tenant_id: str
    diagnosis_type_id: str
    diagnosis_id: str | None
    is_enabled: bool
    sort_order: int | None
    local_label: str | None


@dataclass(frozen=True)
class DiagnosisAlias:
    """A legacy spelling and the taxonomy row it resolves to.

    ``diagnosis_id`` is None when the source only named a type.
    """

    id: str
    raw_value: str
    normalised_key: str
    diagnosis_type_id: str
    diagnosis_id: str | None
    source: str
    confidence: str
