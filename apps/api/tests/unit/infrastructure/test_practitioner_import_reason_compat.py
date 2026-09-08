"""Rows staged before reasons carried codes must still read back.

The mapper writes reasons as {code, message} dicts; earlier batches persisted
bare strings. A listing that raised on them would make every old batch
unreadable rather than showing its reasons under a Legacy code.
"""

from datetime import UTC, datetime

from app.domain.enums.provider_network import ImportReasonCode
from app.infrastructure.mappers.practitioner_import_mapper import PractitionerImportMapper
from app.infrastructure.models.practitioner_import_model import PractitionerImportRowModel


def _model(reasons) -> PractitionerImportRowModel:
    return PractitionerImportRowModel(
        id="row-1",
        tenant_id="t-1",
        batch_id="b-1",
        sheet_name="Sheet",
        row_number=2,
        replay_key="file:h:sheet:Sheet:row:2",
        raw_name="Jane Doe",
        organisation_name=None,
        raw_profession=None,
        mapped_profession=None,
        contact_email=None,
        outcome="NeedsReview",
        reasons=reasons,
        provenance={},
        created_at=datetime(2026, 9, 1, tzinfo=UTC),
    )


def test_a_pre_code_string_reason_reads_back_under_the_legacy_code():
    entity = PractitionerImportMapper.row_to_entity(_model(["old plain message"]))

    assert entity.reasons[0].code is ImportReasonCode.LEGACY
    assert entity.reasons[0].message == "old plain message"


def test_a_coded_reason_reads_back_unchanged():
    entity = PractitionerImportMapper.row_to_entity(
        _model([{"code": "MissingName", "message": "no name"}])
    )

    assert entity.reasons[0].code is ImportReasonCode.MISSING_NAME
    assert entity.reasons[0].message == "no name"


def test_a_mixed_list_reads_every_entry():
    entity = PractitionerImportMapper.row_to_entity(
        _model(["legacy", {"code": "ApplyFailed", "message": "boom"}])
    )

    assert [r.code for r in entity.reasons] == [
        ImportReasonCode.LEGACY,
        ImportReasonCode.APPLY_FAILED,
    ]
