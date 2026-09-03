"""Historical-session import validator tests (Phase 4 #D-Import)."""

from app.application.services.historical_import import (
    AcceptedRow,
    CanonicalMappings,
    HistoricalSessionRow,
    ImportClassification,
    RejectedRow,
    validate_row,
    validate_rows,
)
from app.domain.enums import SessionStatus


def _mappings() -> CanonicalMappings:
    return CanonicalMappings(
        client_codes={"ABSA": "client-absa", "STANBIC": "client-stanbic"},
        service_codes={"COUNSEL": "svc-1"},
        provider_codes={"DR-A": "prov-1"},
        person_codes={"E1234": "person-1"},
        status_text={
            "COMPLETED": SessionStatus.COMPLETED,
            "CANCELLED": SessionStatus.CANCELLED,
        },
    )


def _row(**overrides) -> HistoricalSessionRow:
    base = dict(
        source_id="excel-1",
        client_code="ABSA",
        service_code="COUNSEL",
        provider_code="DR-A",
        person_code="E1234",
        status_text="COMPLETED",
        scheduled_at_text="2024-09-15T10:00:00",
    )
    base.update(overrides)
    return HistoricalSessionRow(**base)


# ---------- Per-row classification ----------


class TestValidateRow:
    def test_happy_path(self):
        out = validate_row(_row(), _mappings(), existing_source_ids=set())
        assert isinstance(out, AcceptedRow)
        assert out.client_id == "client-absa"
        assert out.status == SessionStatus.COMPLETED

    def test_unmapped_client(self):
        out = validate_row(_row(client_code="UNKNOWN"), _mappings(), existing_source_ids=set())
        assert isinstance(out, RejectedRow)
        assert out.classification == ImportClassification.REJECTED_UNMAPPED_CLIENT

    def test_unmapped_service(self):
        out = validate_row(_row(service_code="HUNGRY"), _mappings(), existing_source_ids=set())
        assert isinstance(out, RejectedRow)
        assert out.classification == ImportClassification.REJECTED_UNMAPPED_SERVICE

    def test_unmapped_status(self):
        out = validate_row(_row(status_text="QUEUED"), _mappings(), existing_source_ids=set())
        assert isinstance(out, RejectedRow)
        assert out.classification == ImportClassification.REJECTED_UNMAPPED_STATUS

    def test_invalid_date(self):
        out = validate_row(
            _row(scheduled_at_text="not-a-date"),
            _mappings(),
            existing_source_ids=set(),
        )
        assert isinstance(out, RejectedRow)
        assert out.classification == ImportClassification.REJECTED_INVALID_DATE

    def test_date_only_accepted(self):
        out = validate_row(
            _row(scheduled_at_text="2024-09-15"),
            _mappings(),
            existing_source_ids=set(),
        )
        assert isinstance(out, AcceptedRow)
        assert out.scheduled_at.year == 2024

    def test_duplicate_source_id_rejected(self):
        out = validate_row(
            _row(),
            _mappings(),
            existing_source_ids={"excel-1"},
        )
        assert isinstance(out, RejectedRow)
        assert out.classification == ImportClassification.REJECTED_DUPLICATE

    def test_missing_source_id(self):
        out = validate_row(_row(source_id=""), _mappings(), existing_source_ids=set())
        assert isinstance(out, RejectedRow)
        assert out.classification == ImportClassification.REJECTED_MISSING_FIELD

    def test_missing_required_field(self):
        out = validate_row(_row(client_code=""), _mappings(), existing_source_ids=set())
        assert isinstance(out, RejectedRow)
        assert out.classification == ImportClassification.REJECTED_MISSING_FIELD


# ---------- Batch-level invariants ----------


class TestValidateRows:
    def test_within_batch_dedup(self):
        rows = [
            _row(source_id="excel-1"),
            _row(source_id="excel-1"),  # duplicate within the same file
            _row(source_id="excel-2"),
        ]
        report = validate_rows(rows, _mappings())
        assert report.accepted_count == 2
        assert report.rejected_count == 1
        summary = report.rejection_summary()
        assert summary["RejectedDuplicate"] == 1

    def test_existing_db_ids_take_precedence(self):
        rows = [
            _row(source_id="excel-1"),
            _row(source_id="excel-2"),
        ]
        report = validate_rows(rows, _mappings(), existing_source_ids={"excel-1"})
        assert report.accepted_count == 1
        assert report.rejected[0].source_id == "excel-1"
        assert report.rejected[0].classification == ImportClassification.REJECTED_DUPLICATE

    def test_summary_shape(self):
        rows = [
            _row(source_id="ok-1"),
            _row(source_id="bad-1", client_code="UNKNOWN"),
            _row(source_id="bad-2", scheduled_at_text="oops"),
        ]
        report = validate_rows(rows, _mappings())
        out = report.to_summary()
        assert out["accepted_count"] == 1
        assert out["rejected_count"] == 2
        assert out["total"] == 3
        assert out["rejection_summary"]["RejectedUnmappedClient"] == 1
        assert out["rejection_summary"]["RejectedInvalidDate"] == 1

    def test_empty_input_yields_empty_report(self):
        report = validate_rows([], _mappings())
        assert report.accepted_count == 0
        assert report.rejected_count == 0
        assert report.to_summary()["total"] == 0
