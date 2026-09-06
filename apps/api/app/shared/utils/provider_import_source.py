"""Parse a historical session extract into staging rows.

Column names are matched case-insensitively against the reference extract's
headers. Nothing here resolves identity or infers a delivery context; that is
the staging service's job.
"""

import csv
import io
from datetime import date, datetime

from app.application.services.session_import_staging import SourceRow
from app.domain.exceptions import DomainError

_NAME_COLUMNS = ("counselor (clean)", "counselor", "counsellor")
_DATE_COLUMNS = ("date", "session date")
_DATE_FORMATS = ("%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y", "%d-%b-%Y")


def parse_source_rows(content: bytes, source_record_key_field: str | None) -> list[SourceRow]:
    """Read the extract. Row numbers are 1-based over data rows, not the header."""
    try:
        text = content.decode("utf-8-sig")
    except UnicodeDecodeError as error:
        raise DomainError("Import file must be UTF-8 encoded", http_status=422) from error
    reader = csv.DictReader(io.StringIO(text))
    if reader.fieldnames is None:
        raise DomainError("Import file has no header row", http_status=422)
    lookup = {(name or "").strip().lower(): name for name in reader.fieldnames}
    name_column = _first_present(lookup, _NAME_COLUMNS)
    date_column = _first_present(lookup, _DATE_COLUMNS)
    if date_column is None:
        raise DomainError("Import file has no recognisable date column", http_status=422)
    key_column = lookup.get((source_record_key_field or "").strip().lower())
    if source_record_key_field and key_column is None:
        raise DomainError(f"Column {source_record_key_field!r} is not in the file", http_status=422)
    return [
        SourceRow(
            row_number=index,
            raw_practitioner_name=_value(row, name_column),
            session_date=_parse_date(_value(row, date_column)),
            source_record_key=_value(row, key_column),
        )
        for index, row in enumerate(reader, start=1)
    ]


def _first_present(lookup: dict[str, str], candidates: tuple[str, ...]) -> str | None:
    for candidate in candidates:
        if candidate in lookup:
            return lookup[candidate]
    return None


def _value(row: dict[str, str], column: str | None) -> str | None:
    if column is None:
        return None
    value = (row.get(column) or "").strip()
    return value or None


def _parse_date(raw: str | None) -> date | None:
    """Returns None for an unparseable date; the staging service rejects the row."""
    if not raw:
        return None
    for pattern in _DATE_FORMATS:
        try:
            return datetime.strptime(raw, pattern).date()
        except ValueError:
            continue
    return None
