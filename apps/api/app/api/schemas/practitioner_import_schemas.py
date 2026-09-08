"""Schemas for the staged practitioner workbook import."""

from datetime import datetime

from pydantic import BaseModel

from app.domain.enums.provider_network import (
    ImportBatchStatus,
    ImportReasonCode,
    PractitionerImportOutcome,
)


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


class ImportReasonSchema(BaseModel):
    """Why one row needs review, applied or apply failed (P-10).

    `code` is stable and machine-readable; match on it, never on `message`.
    """

    code: ImportReasonCode
    message: str


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
    reasons: list[ImportReasonSchema]
    provenance: dict
    #: What applying the batch created from this row. Null until it is applied,
    #: and null for a row the apply passed over.
    imported_provider_id: str | None = None
    imported_organisation_id: str | None = None
    imported_affiliation_id: str | None = None


class PractitionerImportRowListResponse(BaseModel):
    items: list[PractitionerImportRowPreview]
    total: int
    page: int
    limit: int
    has_more: bool


class PractitionerImportApplyRowResult(BaseModel):
    """One Accepted row's apply result. Untouched rows appear only in counts."""

    sheet_name: str
    row_number: int
    status: str
    provider_id: str | None = None
    organisation_id: str | None = None
    affiliation_id: str | None = None
    error: str | None = None


class PractitionerImportApplyResponse(BaseModel):
    """Outcome of applying a batch.

    `reused_organisations` counts distinct firms that already existed;
    `not_applicable` counts rows left untouched because a person has not
    accepted them.
    """

    batch: PractitionerImportBatchResponse
    created_providers: int
    created_organisations: int
    reused_organisations: int
    created_affiliations: int
    skipped_already_applied: int
    failed: int
    not_applicable: int
    rows: list[PractitionerImportApplyRowResult]
