"""Parse a historical session extract into staging rows.

Column names are matched case-insensitively against the reference extract's
headers. Nothing here resolves identity or infers a delivery context; that is
the staging service's job. Both a plain CSV and an Excel (`.xlsx`) workbook are
accepted; the same column-matching logic runs over either, because both are
reduced to the same list-of-dicts shape before it runs.
"""

import csv
import io
from collections.abc import Iterable
from datetime import date, datetime

import openpyxl

from app.application.services.session_import_staging import SourceRow
from app.domain.exceptions import DomainError

_NAME_COLUMNS = ("counselor (clean)", "counselor", "counsellor")
_DATE_COLUMNS = ("date", "session date")
_CLIENT_COLUMNS = ("company (clean)", "client", "company")
_CLIENT_CODE_COLUMNS = ("client code", "company code")
_MEMBER_REF_COLUMNS = ("client-id#", "staff_id", "client id")
_GENDER_COLUMNS = ("gender",)
_AUDIENCE_COLUMNS = ("client type (staff/dep)",)
_SESSION_TYPE_COLUMNS = ("session type",)
_CATEGORY_COLUMNS = ("session category", "category")
_STATUS_COLUMNS = ("status (clean)", "status")
_INTERVENTION_COLUMNS = ("intervention",)
_CLIENT_TYPE_COLUMNS = ("client type",)
_RATE_COLUMNS = ("rate (ugx)",)
_SESSION_NUMBER_COLUMNS = ("session #", "session number")
_ISSUE_TOPIC_COLUMNS = ("issue/topic", "issue topic")
_DIAGNOSIS_COLUMNS = ("diagnosis",)
_DIAGNOSIS_TYPE_COLUMNS = ("diagnosis type",)
_APPROVED_BY_COLUMNS = ("approved by",)
#: No _FEEDBACK_COLUMNS: CLIENT FEEDBACK is free text that PRIV-01 forbids
#: reaching an employer aggregate (session_import_normalisation.py's own
#: docstring). It is deliberately never parsed into a SourceRow field.
#: ISO first, then day-first (`03/04/2026` is 3 April), matching the region
#: this system serves. Month-first exists only for a slash date day-first
#: cannot parse (`13/25/2026`), which a real calendar day never produces, so
#: it is effectively unreachable here. Same policy as, and independent of,
#: `parse_roster_date` in `member_csv.py`: both decide the same ambiguity for
#: their own importer, so a future change to this policy needs updating in
#: both places.
_DATE_FORMATS = ("%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y", "%d-%b-%Y", "%d-%b-%y")

#: The zip local-file-header signature every `.xlsx` starts with (it is a zip
#: container). Sniffed rather than trusted from the filename, since a person
#: renaming a file is more likely than this repo's other format checks assume.
_XLSX_MAGIC = b"PK\x03\x04"


def parse_source_rows(content: bytes, source_record_key_field: str | None) -> list[SourceRow]:
    """Read the extract. Row numbers are 1-based over data rows, not the header."""
    fieldnames, rows = _read_table(content)
    lookup = {(name or "").strip().lower(): name for name in fieldnames}
    name_column = _first_present(lookup, _NAME_COLUMNS)
    date_column = _first_present(lookup, _DATE_COLUMNS)
    if date_column is None:
        raise DomainError("Import file has no recognisable date column", http_status=422)
    key_column = lookup.get((source_record_key_field or "").strip().lower())
    if source_record_key_field and key_column is None:
        raise DomainError(f"Column {source_record_key_field!r} is not in the file", http_status=422)
    columns = {
        "raw_client_name": _first_present(lookup, _CLIENT_COLUMNS),
        "raw_client_code": _first_present(lookup, _CLIENT_CODE_COLUMNS),
        "raw_member_ref": _first_present(lookup, _MEMBER_REF_COLUMNS),
        "raw_gender": _first_present(lookup, _GENDER_COLUMNS),
        "raw_audience": _first_present(lookup, _AUDIENCE_COLUMNS),
        "raw_session_type": _first_present(lookup, _SESSION_TYPE_COLUMNS),
        "raw_category": _first_present(lookup, _CATEGORY_COLUMNS),
        "raw_status": _first_present(lookup, _STATUS_COLUMNS),
        "raw_intervention": _first_present(lookup, _INTERVENTION_COLUMNS),
        "raw_client_type": _first_present(lookup, _CLIENT_TYPE_COLUMNS),
        "raw_rate": _first_present(lookup, _RATE_COLUMNS),
        "raw_session_number": _first_present(lookup, _SESSION_NUMBER_COLUMNS),
        "raw_issue_topic": _first_present(lookup, _ISSUE_TOPIC_COLUMNS),
        "raw_diagnosis": _first_present(lookup, _DIAGNOSIS_COLUMNS),
        "raw_diagnosis_type": _first_present(lookup, _DIAGNOSIS_TYPE_COLUMNS),
        "raw_approved_by": _first_present(lookup, _APPROVED_BY_COLUMNS),
    }
    return [
        SourceRow(
            row_number=index,
            raw_practitioner_name=_value(row, name_column),
            session_date=_parse_date(_value(row, date_column)),
            source_record_key=_value(row, key_column),
            **{field: _value(row, column) for field, column in columns.items()},
        )
        for index, row in enumerate(rows, start=1)
        if any(value is not None for value in row.values())
    ]


def _read_table(content: bytes) -> tuple[list[str], Iterable[dict[str, str | None]]]:
    """Sniff the format and return (header names, rows as dicts of normalised strings).

    Everything downstream of this only ever sees strings, so a CSV date column
    and an Excel date cell that Excel already parsed to a real date both reach
    `_parse_date` the same way.
    """
    if content.startswith(_XLSX_MAGIC):
        return _read_xlsx_table(content)
    return _read_csv_table(content)


def _read_csv_table(content: bytes) -> tuple[list[str], Iterable[dict[str, str | None]]]:
    try:
        text = content.decode("utf-8-sig")
    except UnicodeDecodeError as error:
        raise DomainError("Import file must be UTF-8 encoded", http_status=422) from error
    reader = csv.DictReader(io.StringIO(text))
    if reader.fieldnames is None:
        raise DomainError("Import file has no header row", http_status=422)
    fieldnames = list(reader.fieldnames)
    rows = ({key: _normalise_cell(value) for key, value in row.items()} for row in reader)
    return fieldnames, rows


def _read_xlsx_table(content: bytes) -> tuple[list[str], Iterable[dict[str, str | None]]]:
    """Read the first sheet. A hidden reference sheet for dropdowns is not data."""
    try:
        workbook = openpyxl.load_workbook(io.BytesIO(content), read_only=True, data_only=True)
    except Exception as error:  # openpyxl raises several distinct types for a bad file
        raise DomainError(
            "Import file is not a readable .xlsx workbook", http_status=422
        ) from error
    sheet = workbook.worksheets[0]
    rows = sheet.iter_rows(values_only=True)
    try:
        header = next(rows)
    except StopIteration as error:
        raise DomainError("Import file has no header row", http_status=422) from error
    fieldnames = [_normalise_cell(cell) or "" for cell in header]
    return fieldnames, (
        {
            fieldnames[i]: _normalise_cell(value)
            for i, value in enumerate(row)
            if i < len(fieldnames)
        }
        for row in rows
    )


def _normalise_cell(value: object) -> str | None:
    """Reduce any cell type to the string shape the rest of this module expects."""
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.date().isoformat()
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    text = str(value).strip()
    return text or None


def _first_present(lookup: dict[str, str], candidates: tuple[str, ...]) -> str | None:
    for candidate in candidates:
        if candidate in lookup:
            return lookup[candidate]
    return None


def _value(row: dict[str, str | None], column: str | None) -> str | None:
    if column is None:
        return None
    value = row.get(column)
    return value.strip() or None if value else None


def _parse_date(raw: str | None) -> date | None:
    """Returns None for an unparseable date; the staging service rejects the row."""
    if not raw:
        return None
    try:
        return date.fromisoformat(raw)
    except ValueError:
        pass
    for pattern in _DATE_FORMATS:
        try:
            return datetime.strptime(raw, pattern).date()
        except ValueError:
            continue
    return None
