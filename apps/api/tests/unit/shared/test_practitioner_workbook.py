"""The workbook parser: typed fields, verbatim provenance, and the real file."""

import hashlib
import os
from pathlib import Path

import pytest

from app.domain.exceptions import DomainError
from app.shared.utils.practitioner_workbook import (
    CONSULTANTS_SHEET,
    PARTNER_SHEET,
    parse_practitioner_workbook,
)
from tests.unit.shared.practitioner_workbook_builder import (
    consultant_row,
    partner_row,
    workbook_bytes,
)

REFERENCE_ENV = "PRACTITIONERS_REFERENCE_XLSX"
REFERENCE_SHA256 = "ec690c205cbe9172538a6908100cde63353a1cc18652941ffe07c157117e48e9"


def _rows_by_sheet(rows):
    return (
        [r for r in rows if r.sheet_name == PARTNER_SHEET.name],
        [r for r in rows if r.sheet_name == CONSULTANTS_SHEET.name],
    )


class TestParsing:
    def test_reads_both_sheets_with_their_own_header_rows(self):
        rows = parse_practitioner_workbook(workbook_bytes([partner_row()], [consultant_row()]))
        partner, consultants = _rows_by_sheet(rows)
        assert len(partner) == 1 and len(consultants) == 1
        assert partner[0].raw_name == "Jane Doe"
        assert consultants[0].raw_name == "John Okello"

    def test_row_numbers_are_the_worksheet_rows(self):
        """The partner header sits on row 2, so its data starts at row 3."""
        rows = parse_practitioner_workbook(workbook_bytes([partner_row()], [consultant_row()]))
        partner, consultants = _rows_by_sheet(rows)
        assert partner[0].row_number == 3
        assert consultants[0].row_number == 2

    def test_an_organisation_company_cell_names_the_organisation(self):
        rows = parse_practitioner_workbook(
            workbook_bytes([partner_row(company="Safe Places Uganda")])
        )
        assert rows[0].organisation_name == "Safe Places Uganda"
        assert rows[0].company == "Safe Places Uganda"

    def test_individual_names_no_organisation_whatever_its_case(self):
        rows = parse_practitioner_workbook(
            workbook_bytes([partner_row(company="INDIVIDUAL")], [consultant_row()])
        )
        assert all(row.organisation_name is None for row in rows)

    def test_provenance_keeps_unmodelled_columns_verbatim(self):
        """Rates, both phones, location and salutation are kept, not merged."""
        rows = parse_practitioner_workbook(workbook_bytes([partner_row()], [consultant_row()]))
        partner, consultants = _rows_by_sheet(rows)
        assert partner[0].provenance["CONTACT MOBILE 1"] == "0700000001"
        assert partner[0].provenance["MOBILE CONTACT 2"] == "0770000001"
        assert partner[0].provenance["OFFICE LOCATION"] == "Muyenga"
        assert consultants[0].provenance["Saluttion"] == "Mr. Okello"
        assert consultants[0].provenance["Counsel"] == 60000
        assert consultants[0].provenance["Talks"] == 500000
        assert consultants[0].provenance["Contract"] == "Done"

    def test_blank_rows_are_skipped(self):
        rows = parse_practitioner_workbook(
            workbook_bytes([partner_row(), [None] * 9, partner_row(name="Second")])
        )
        assert [r.raw_name for r in rows] == ["Jane Doe", "Second"]
        assert [r.row_number for r in rows] == [3, 5]

    def test_the_consultants_contract_memo_is_read(self):
        rows = parse_practitioner_workbook(
            workbook_bytes((), [consultant_row(contract="Employee")])
        )
        assert rows[0].contract_memo == "Employee"

    def test_a_missing_sheet_is_refused(self):
        import openpyxl

        workbook = openpyxl.Workbook()
        import io

        buffer = io.BytesIO()
        workbook.save(buffer)
        with pytest.raises(DomainError, match="no sheet named"):
            parse_practitioner_workbook(buffer.getvalue())

    def test_a_non_workbook_is_refused(self):
        with pytest.raises(DomainError, match="not a readable xlsx"):
            parse_practitioner_workbook(b"this is not a workbook")


@pytest.fixture(scope="module")
def rows():
    content = Path(os.environ[REFERENCE_ENV]).read_bytes()
    assert hashlib.sha256(content).hexdigest() == REFERENCE_SHA256, (
        "Reference workbook changed; re-derive every count before trusting these tests"
    )
    return parse_practitioner_workbook(content)


@pytest.mark.skipif(REFERENCE_ENV not in os.environ, reason=f"Set {REFERENCE_ENV}")
class TestReferenceFile:
    """Counts re-derived from the reference workbook, keyed to its hash."""

    def test_row_counts(self, rows):
        partner, consultants = _rows_by_sheet(rows)
        assert len(partner) == 100
        assert len(consultants) == 68

    def test_every_row_names_a_practitioner(self, rows):
        assert all(row.raw_name for row in rows)

    def test_individual_rows_per_sheet(self, rows):
        partner, consultants = _rows_by_sheet(rows)
        assert sum(1 for r in partner if r.organisation_name is None) == 22
        assert sum(1 for r in consultants if r.organisation_name is None) == 15

    def test_exactly_one_cell_holds_two_emails(self, rows):
        doubles = [
            r.contact_email for r in rows if r.contact_email and r.contact_email.count("@") > 1
        ]
        assert doubles == ["janetkidda@gmail.com/info@safeplacesUganda.com"]

    def test_exactly_one_employee_contract_memo(self, rows):
        memos = [r for r in rows if (r.contract_memo or "").casefold() == "employee"]
        assert len(memos) == 1
