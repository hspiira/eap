"""Schemas for the staged practitioner workbook import."""

from datetime import datetime

from pydantic import BaseModel

from app.domain.enums.provider_network import ImportBatchStatus, PractitionerImportOutcome


class PractitionerImportBatchResponse(BaseModel):
    id: str
    tenant_id: str
    source_system: str
    file_name: str
    file_hash: str
    row_count: int
    status: ImportBatchStatus
    outcome_counts: dict[str, int]
    created_at: datetime
    applied_at: datetime | None


class PractitionerImportRowPreview(BaseModel):
    sheet_name: str
    row_number: int
    outcome: PractitionerImportOutcome
    raw_name: str | None
    normalized_name: str | None
    organisation_name: str | None
    raw_profession: str | None
    mapped_profession: str | None
    contact_email: str | None
    reasons: list[str]
    provenance: dict


class PractitionerImportRowListResponse(BaseModel):
    items: list[PractitionerImportRowPreview]
    total: int
    page: int
    limit: int
    has_more: bool
