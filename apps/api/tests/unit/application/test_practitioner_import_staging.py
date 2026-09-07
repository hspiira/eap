"""Staging rules: organisations, identity candidates, quarantine, no guessing."""

from dataclasses import fields
from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock

from app.application.services.practitioner_import_staging import (
    WORKBOOK_SOURCE_SYSTEM,
    PractitionerImportStagingService,
    StagedPractitionerRow,
)
from app.domain.enums.provider_network import PractitionerImportOutcome
from app.domain.value_objects.core import TenantId
from app.shared.utils.practitioner_workbook import WorkbookRow

TENANT = TenantId("t-1")
HASH = "sha256:abc"
NOW = datetime(2026, 9, 7, 12, 0, tzinfo=UTC)


def _service(*, alias=None, existing_row=None):
    aliases = AsyncMock()
    aliases.find_alias.return_value = alias
    imports = AsyncMock()
    imports.find_row_by_replay_key.return_value = existing_row
    return PractitionerImportStagingService(aliases, imports), aliases, imports


def _row(**overrides) -> WorkbookRow:
    defaults = {
        "sheet_name": "Minet EAP Partner list",
        "row_number": 3,
        "raw_name": "Jane Doe",
        "company": "Individual",
        "organisation_name": None,
        "profession_column": "PROFESSION",
        "raw_profession": "Clinical Psychology",
        "contact_email": "jane@example.com",
        "contract_memo": None,
        "provenance": {"Saluttion": "Mrs.", "OFFICE LOCATION": "Muyenga"},
    }
    return WorkbookRow(**{**defaults, **overrides})


async def _stage_one(service, row):
    staged = await service.stage_rows(TENANT, HASH, [row], now=NOW)
    return staged[0]


class TestAcceptedRows:
    async def test_a_clean_individual_row_is_accepted(self):
        service, _, _ = _service()
        staged = await _stage_one(service, _row())
        assert staged.outcome is PractitionerImportOutcome.ACCEPTED
        assert staged.normalized_name == "jane doe"
        assert staged.mapped_profession == "Clinical Psychologist"
        assert staged.organisation_name is None
        assert staged.reasons == ()

    async def test_the_replay_key_carries_the_sheet_name(self):
        """Two sheets share row numbers, so the sheet is part of row identity."""
        service, _, _ = _service()
        staged = await _stage_one(service, _row())
        assert staged.replay_key == f"file:{HASH}:sheet:Minet EAP Partner list:row:3"

    async def test_provenance_travels_with_the_staged_row(self):
        service, _, _ = _service()
        staged = await _stage_one(service, _row())
        assert staged.provenance["Saluttion"] == "Mrs."
        assert staged.provenance["OFFICE LOCATION"] == "Muyenga"

    async def test_nothing_is_guessed_from_the_source(self):
        """No tier, region, panel or gender field exists to be guessed (P-05)."""
        field_names = {field.name for field in fields(StagedPractitionerRow)}
        assert not field_names & {"tier", "region", "panel_status", "gender", "salutation"}


class TestOrganisationRows:
    async def test_a_company_row_stages_the_organisation_by_name(self):
        service, _, _ = _service()
        staged = await _stage_one(
            service, _row(company="Safe Places Uganda", organisation_name="Safe Places Uganda")
        )
        assert staged.outcome is PractitionerImportOutcome.ACCEPTED
        assert staged.organisation_name == "Safe Places Uganda"


class TestAliases:
    async def test_a_new_name_is_staged_as_an_unmapped_alias(self):
        service, aliases, _ = _service()
        await _stage_one(service, _row())
        aliases.find_alias.assert_awaited_once_with(TENANT, WORKBOOK_SOURCE_SYSTEM, "jane doe")
        saved = aliases.save_alias.await_args.args[0]
        assert saved.source_value == "Jane Doe"
        assert saved.normalized_value == "jane doe"
        assert saved.provider_id is None
        assert saved.candidate_provider_ids == ()

    async def test_an_existing_alias_is_left_untouched(self):
        service, aliases, _ = _service(alias=SimpleNamespace(state="Resolved"))
        await _stage_one(service, _row())
        aliases.save_alias.assert_not_awaited()

    async def test_one_alias_per_name_within_a_batch(self):
        service, aliases, _ = _service()
        rows = [_row(), _row(sheet_name="EAP Consultants - General", row_number=2)]
        await service.stage_rows(TENANT, HASH, rows, now=NOW)
        assert aliases.save_alias.await_count == 1


class TestIdentityCandidates:
    async def test_the_same_name_on_both_sheets_needs_review_on_both_rows(self):
        service, _, _ = _service()
        rows = [
            _row(),
            _row(
                sheet_name="EAP Consultants - General",
                row_number=9,
                raw_name="Dr. Jane Doe",
                profession_column="Speciality",
                raw_profession="Counselling",
            ),
        ]
        first, second = await service.stage_rows(TENANT, HASH, rows, now=NOW)
        assert first.outcome is PractitionerImportOutcome.NEEDS_REVIEW
        assert second.outcome is PractitionerImportOutcome.NEEDS_REVIEW
        assert "'EAP Consultants - General' row 9" in first.reasons[0]
        assert "reconciled by a person" in first.reasons[0]

    async def test_a_repeated_name_within_one_sheet_needs_review_too(self):
        service, _, _ = _service()
        rows = [_row(), _row(row_number=58)]
        first, second = await service.stage_rows(TENANT, HASH, rows, now=NOW)
        assert first.outcome is PractitionerImportOutcome.NEEDS_REVIEW
        assert second.outcome is PractitionerImportOutcome.NEEDS_REVIEW


class TestQuarantine:
    async def test_a_double_email_cell_is_never_split(self):
        cell = "janetkidda@gmail.com/info@safeplacesUganda.com"
        service, _, _ = _service()
        staged = await _stage_one(service, _row(contact_email=cell))
        assert staged.outcome is PractitionerImportOutcome.NEEDS_REVIEW
        assert staged.contact_email is None
        assert cell in staged.reasons[0]
        assert "by hand" in staged.reasons[0]
        assert staged.provenance is not None

    async def test_the_employee_contract_memo_is_not_enrolled(self):
        service, _, _ = _service()
        staged = await _stage_one(
            service,
            _row(
                sheet_name="EAP Consultants - General",
                row_number=30,
                profession_column="Speciality",
                raw_profession="Counselling",
                contract_memo="Employee",
            ),
        )
        assert staged.outcome is PractitionerImportOutcome.NEEDS_REVIEW
        assert any("Employee" in reason for reason in staged.reasons)

    async def test_an_unmapped_role_needs_review(self):
        service, _, _ = _service()
        staged = await _stage_one(service, _row(raw_profession="Yoga/mindfulness"))
        assert staged.outcome is PractitionerImportOutcome.NEEDS_REVIEW
        assert staged.mapped_profession is None
        assert "'Yoga/mindfulness'" in staged.reasons[0]

    async def test_a_row_with_no_usable_name_is_rejected(self):
        service, aliases, _ = _service()
        staged = await _stage_one(service, _row(raw_name="  . "))
        assert staged.outcome is PractitionerImportOutcome.REJECTED
        aliases.save_alias.assert_not_awaited()


class TestReplaySafety:
    async def test_an_already_staged_row_is_a_duplicate(self):
        existing = SimpleNamespace(
            sheet_name="Minet EAP Partner list",
            row_number=3,
            batch_id=SimpleNamespace(value="b-0"),
        )
        service, aliases, _ = _service(existing_row=existing)
        staged = await _stage_one(service, _row())
        assert staged.outcome is PractitionerImportOutcome.DUPLICATE
        assert "batch b-0" in staged.reasons[0]
        aliases.save_alias.assert_not_awaited()
