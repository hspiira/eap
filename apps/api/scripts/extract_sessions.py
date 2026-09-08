"""Turn the reference workbook's activity log into a session-import CSV.

The staging endpoint reads a CSV and matches its own column names against the
header, so this writes the sheet out as it stands rather than reshaping it. The
sheet already carries the cleaned columns staging prefers (`COUNSELOR (CLEAN)`,
`COMPANY (CLEAN)`, `STATUS (CLEAN)`), and those are a person's own tidying of
the raw entries, so they are kept alongside the originals and staging chooses.

Only two things are normalised, both of them formatting rather than meaning:
Excel dates become ISO dates, and numbers that are whole become integers so a
staff reference does not arrive as "238002.0".

    uv run --with openpyxl python scripts/extract_sessions.py --workbook <path>
"""

from __future__ import annotations

import argparse
import csv
import io
import sys
from datetime import date, datetime
from pathlib import Path

API_ROOT = Path(__file__).resolve().parent.parent
if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))

OUT = API_ROOT / "data" / "taxonomy" / "sessions.csv"
SHEET = "Activity Logs"


def _cell(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, datetime):
        return value.date().isoformat()
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value).strip()


def extract(workbook: Path, sheet: str) -> tuple[list[str], list[dict[str, str]]]:
    import openpyxl

    rows = openpyxl.load_workbook(workbook, read_only=True, data_only=True)[sheet].iter_rows(
        values_only=True
    )
    header = [_cell(cell) for cell in next(rows)]
    named = [(index, name) for index, name in enumerate(header) if name]
    out = []
    for row in rows:
        values = {name: _cell(row[index]) if index < len(row) else "" for index, name in named}
        if any(values.values()):
            out.append(values)
    return [name for _, name in named], out


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workbook", required=True, type=Path)
    parser.add_argument("--sheet", default=SHEET)
    args = parser.parse_args()

    columns, rows = extract(args.workbook, args.sheet)
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=columns)
    writer.writeheader()
    writer.writerows(rows)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(buffer.getvalue())
    print(f"{OUT.name:16} {len(rows)} rows, {len(columns)} columns")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
