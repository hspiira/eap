"""Historical session import CLI (Phase 4 #D-Import).

Usage:
    uv run python scripts/import_historical_sessions.py \\
        --csv path/to/sessions.csv \\
        --mappings path/to/mappings.json \\
        --tenant-id <tid> \\
        [--dry-run]

CSV columns (header required):
    source_id, client_code, service_code, provider_code,
    member_code, status_text, scheduled_at_text, notes (optional)

mappings.json shape::

    {
        "client_codes":   {"ABSA": "<canonical-client-id>", ...},
        "service_codes":  {...},
        "provider_codes": {...},
        "member_codes":   {"<canonical-client-id>": {"<company-member-code>": "<member-id>"}},
        "status_text":    {"COMPLETED": "Completed", ...}
    }

Idempotency: rows whose ``source_id`` already exists in the DB are reported
as duplicates and skipped. Re-running after a partial failure is safe.

Dry-run mode prints the report without writing to the database.
"""

from __future__ import annotations

import argparse
import asyncio
import csv
import json
import sys
from pathlib import Path

# Running as a script puts scripts/ on sys.path, not the repo root.
_project_root = Path(__file__).resolve().parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine

from app.application.services.historical_import import (
    CanonicalMappings,
    HistoricalSessionRow,
    validate_rows,
)
from app.core.config import settings
from app.domain.enums import SessionStatus


def _load_mappings(path: Path) -> CanonicalMappings:
    raw = json.loads(path.read_text())
    return CanonicalMappings(
        client_codes=dict(raw.get("client_codes", {})),
        service_codes=dict(raw.get("service_codes", {})),
        provider_codes=dict(raw.get("provider_codes", {})),
        member_codes=dict(raw.get("member_codes", {})),
        status_text={k: SessionStatus(v) for k, v in raw.get("status_text", {}).items()},
    )


def _load_rows(csv_path: Path) -> list[HistoricalSessionRow]:
    rows: list[HistoricalSessionRow] = []
    with csv_path.open(newline="") as f:
        reader = csv.DictReader(f)
        for r in reader:
            rows.append(
                HistoricalSessionRow(
                    source_id=r.get("source_id", "").strip(),
                    client_code=r.get("client_code", "").strip(),
                    service_code=r.get("service_code", "").strip(),
                    provider_code=r.get("provider_code", "").strip(),
                    member_code=r.get("member_code", "").strip(),
                    status_text=r.get("status_text", "").strip(),
                    scheduled_at_text=r.get("scheduled_at_text", "").strip(),
                    notes=r.get("notes") or None,
                )
            )
    return rows


async def _existing_source_ids(tenant_id: str) -> set[str]:
    from app.infrastructure.models.service_session_model import ServiceSessionModel

    engine = create_async_engine(settings.DATABASE_URL)
    async with engine.connect() as conn:
        rows = await conn.execute(
            select(ServiceSessionModel.import_source_id).where(
                ServiceSessionModel.tenant_id == tenant_id,
                ServiceSessionModel.import_source_id.is_not(None),
            )
        )
        return {r[0] for r in rows.all()}


async def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--csv", type=Path, required=True)
    parser.add_argument("--mappings", type=Path, required=True)
    parser.add_argument("--tenant-id", required=True)
    parser.add_argument("--dry-run", action="store_true", default=False)
    args = parser.parse_args()

    if not args.csv.exists():
        print(f"CSV not found: {args.csv}", file=sys.stderr)
        return 2
    if not args.mappings.exists():
        print(f"Mappings not found: {args.mappings}", file=sys.stderr)
        return 2

    mappings = _load_mappings(args.mappings)
    rows = _load_rows(args.csv)
    existing = await _existing_source_ids(args.tenant_id)
    report = validate_rows(rows, mappings, existing_source_ids=existing)

    print(json.dumps(report.to_summary(), indent=2))

    if args.dry_run:
        print("[dry-run] No rows written.")
        return 0

    # NOTE: The actual write path is intentionally out of scope for the v1 CLI.
    # The validator is the engineering artefact; persistence wires through the
    # existing CreateServiceSessionUseCase once the operator has reviewed the
    # report. This keeps the CLI single-responsibility and auditable.
    print(
        "[note] Write path not yet wired in CLI. "
        "Use the validator output to drive batch inserts via the API."
    )
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
