"""Employment details survive staging and reach the member the import creates.

A roster row is persisted at preview time and rebuilt at confirmation, so a
field missing from either half of that round trip is dropped without an error.
"""

from datetime import UTC, datetime

from app.api.services.member_import import (
    RowCheck,
    build_row_entity,
    csv_row_from_entity,
)
from app.domain.value_objects.ids import MemberImportBatchId, MemberImportRowId, TenantId
from app.shared.utils.member_csv import MemberCsvRow

EMPLOYMENT = {
    "job_title": "Branch Manager",
    "job_classification": "Manager",
    "skill": "Officer",
    "department": "Operations",
    "unit": "Kampala Road branch",
    "employment_type": "Permanent",
}


def _row(**overrides: str | None) -> MemberCsvRow:
    values: dict[str, object] = {
        "row_number": 2,
        "client_code": "ACME",
        "import_source_id": "AC-1",
        "staff_number": "1001",
        "display_label": "Jane Doe",
        "work_email": None,
        "personal_email": None,
        "gender": None,
        "date_of_birth": None,
        "phone": None,
        "national_id": None,
        "passport_number": None,
        "status": "Active",
        "relation": None,
        "primary_import_source_id": None,
        **EMPLOYMENT,
    }
    values.update(overrides)
    return MemberCsvRow(**values)  # type: ignore[arg-type]


def _staged(row: MemberCsvRow):
    return build_row_entity(
        row,
        RowCheck(state="new"),
        row_id=MemberImportRowId("row-1"),
        batch_id=MemberImportBatchId("batch-1"),
        tenant_id=TenantId("t-1"),
        file_hash="hash",
        now=datetime.now(UTC),
    )


def test_staging_persists_every_employment_value():
    staged = _staged(_row())
    for field, expected in EMPLOYMENT.items():
        assert getattr(staged, field) == expected, field


def test_confirmation_rebuilds_every_employment_value():
    rebuilt = csv_row_from_entity(_staged(_row()))
    for field, expected in EMPLOYMENT.items():
        assert getattr(rebuilt, field) == expected, field


def test_a_roster_without_employment_columns_round_trips_as_absent():
    blank = dict.fromkeys(EMPLOYMENT)
    rebuilt = csv_row_from_entity(_staged(_row(**blank)))
    for field in EMPLOYMENT:
        assert getattr(rebuilt, field) is None, field


def test_the_round_trip_preserves_the_whole_row():
    """Guards against a field being added to one half of the round trip only."""
    original = _row()
    assert csv_row_from_entity(_staged(original)) == original
