"""Parse the practitioners and organisations workbook into staging rows.

Reads the two practitioner sheets only; the requirement checklist is another
module's concern. Every populated source cell is preserved verbatim in the
row's provenance dict, because rates, contract memos, second phone numbers,
office locations and salutations are deliberately unmodelled (P-03, P-04).
Nothing here resolves identity, splits cells or maps roles; that is the
staging service's job.
"""

import io
from dataclasses import dataclass

from openpyxl import load_workbook

from app.domain.exceptions import DomainError

_INDIVIDUAL = "individual"

Scalar = str | int | float | bool


@dataclass(frozen=True)
class SheetSpec:
    """Where one practitioner sheet keeps its columns."""

    name: str
    header_row: int
    name_column: str
    company_column: str
    profession_column: str
    email_column: str
    contract_column: str | None = None


PARTNER_SHEET = SheetSpec(
    name="Minet EAP Partner list",
    header_row=2,
    name_column="NAME (First/Surname)",
    company_column="INDIVIDUAL/COMPANY NAME",
    profession_column="PROFESSION",
    email_column="CONTACT EMAIL",
)

CONSULTANTS_SHEET = SheetSpec(
    name="EAP Consultants - General",
    header_row=1,
    name_column="NAME",
    company_column="COMPANY",
    profession_column="Speciality",
    email_column="EMAIL",
    contract_column="Contract",
)

SHEETS = (PARTNER_SHEET, CONSULTANTS_SHEET)


@dataclass(frozen=True)
class WorkbookRow:
    """One parsed practitioner row, with every source column kept verbatim."""

    sheet_name: str
    row_number: int
    raw_name: str | None
    company: str | None
    organisation_name: str | None
    profession_column: str
    raw_profession: str | None
    contact_email: str | None
    contract_memo: str | None
    provenance: dict[str, Scalar]


def parse_practitioner_workbook(content: bytes) -> list[WorkbookRow]:
    """Read both practitioner sheets. Row numbers are the worksheet's own."""
    try:
        workbook = load_workbook(io.BytesIO(content), read_only=True, data_only=True)
    except Exception as error:
        raise DomainError("Import file is not a readable xlsx workbook", http_status=422) from error
    try:
        return [row for spec in SHEETS for row in _parse_sheet(workbook, spec)]
    finally:
        workbook.close()


class _Header:
    """Column positions for one sheet: the required ones and every labelled one."""

    def __init__(self, header_cells: tuple, spec: SheetSpec):
        self.labels = [
            (str(cell).strip(), index) for index, cell in enumerate(header_cells) if _text(cell)
        ]
        positions = {_key(label): index for label, index in self.labels}
        self.columns: dict[str, int] = {}
        for column in self._required(spec):
            index = positions.get(_key(column))
            if index is None:
                raise DomainError(
                    f"Sheet {spec.name!r} has no column named {column!r}", http_status=422
                )
            self.columns[column] = index

    @staticmethod
    def _required(spec: SheetSpec) -> list[str]:
        required = [spec.name_column, spec.company_column, spec.profession_column]
        required.append(spec.email_column)
        if spec.contract_column:
            required.append(spec.contract_column)
        return required

    def text(self, cells: tuple, column: str) -> str | None:
        return _text(_cell(cells, self.columns[column]))


def _parse_sheet(workbook, spec: SheetSpec) -> list[WorkbookRow]:
    if spec.name not in workbook.sheetnames:
        raise DomainError(f"Workbook has no sheet named {spec.name!r}", http_status=422)
    rows = list(workbook[spec.name].iter_rows(values_only=True))
    if len(rows) < spec.header_row:
        raise DomainError(f"Sheet {spec.name!r} has no header row", http_status=422)
    header = _Header(rows[spec.header_row - 1], spec)
    return [
        _row(spec, number, cells, header)
        for number, cells in enumerate(rows[spec.header_row :], start=spec.header_row + 1)
        if any(_text(cell) for cell in cells)
    ]


def _row(spec: SheetSpec, number: int, cells: tuple, header: _Header) -> WorkbookRow:
    company = header.text(cells, spec.company_column)
    contract = header.text(cells, spec.contract_column) if spec.contract_column else None
    return WorkbookRow(
        sheet_name=spec.name,
        row_number=number,
        raw_name=header.text(cells, spec.name_column),
        company=company,
        organisation_name=None if _is_individual(company) else company,
        profession_column=spec.profession_column,
        raw_profession=header.text(cells, spec.profession_column),
        contact_email=header.text(cells, spec.email_column),
        contract_memo=contract,
        provenance=_provenance(cells, header),
    )


def _provenance(cells: tuple, header: _Header) -> dict[str, Scalar]:
    """Every populated cell under a header, verbatim, keyed by its header."""
    values: dict[str, Scalar] = {}
    for label, index in header.labels:
        cell = _cell(cells, index)
        if cell is None or _text(cell) is None:
            continue
        values[label] = cell if isinstance(cell, Scalar) else str(cell)
    return values


def _is_individual(company: str | None) -> bool:
    return company is None or company.casefold() == _INDIVIDUAL


def _cell(cells: tuple, index: int):
    return cells[index] if index < len(cells) else None


def _text(value) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _key(value: str) -> str:
    return " ".join(value.split()).casefold()
