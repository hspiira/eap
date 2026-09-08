"""Load a member-import CSV through the roster importer.

Uses the same two-step path the UI uses: the server previews every row, then
each confirmed row is committed on its own, so one bad row cannot undo the rest.
Nothing is invented here; rows the preview refuses are reported with the
server's own reason.

    uv run python scripts/import_members.py --tenant-id <id> --csv <path>
    uv run python scripts/import_members.py --tenant-id <id> --csv <path> --apply
"""

from __future__ import annotations

import argparse
import asyncio
import os
import sys
from collections import Counter
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

API_ROOT = SCRIPTS_DIR.parent
if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))

from import_support import send  # noqa: E402

BATCH = 100


async def run(tenant_id: str, content: bytes, name: str, apply: bool) -> int:
    from httpx import ASGITransport, AsyncClient

    from app.core.security import TokenData, get_current_user, get_current_user_optional
    from app.main import app

    actor = TokenData(user_id="member-import", tenant_id=tenant_id, role="Admin")
    app.dependency_overrides[get_current_user] = lambda: actor
    app.dependency_overrides[get_current_user_optional] = lambda: actor

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://import", timeout=600
    ) as http:
        preview = await send(
            http,
            "POST",
            f"/members/import?dry_run=true&tenant_id={tenant_id}",
            files={"file": (name, content, "text/csv")},
        )
        if preview.status_code != 200:
            print(f"preview failed: {preview.status_code} {preview.text[:300]}")
            return 1
        body = preview.json()
        rows = body.get("rows", [])
        states = Counter(row["state"] for row in rows)
        print(
            f"previewed {len(rows)} rows: " + ", ".join(f"{n} {s}" for s, n in states.most_common())
        )
        for row in rows:
            if row.get("message"):
                states[f"reason:{row['message'][:70]}"] += 0
        reasons = Counter(row["message"][:70] for row in rows if row.get("message"))
        for reason, count in reasons.most_common(8):
            print(f"    {count:5}  {reason}")

        ready = [row for row in rows if row["state"] == "new" and row.get("values")]
        if not apply:
            print(f"\nPLAN ONLY, nothing written. {len(ready)} rows would be imported.")
            return 0

        imported = Counter()
        for start in range(0, len(ready), BATCH):
            slice_ = ready[start : start + BATCH]
            response = await send(
                http,
                "POST",
                f"/members/import/commit?tenant_id={tenant_id}",
                json={"rows": [{"row": r["row"], "values": r["values"]} for r in slice_]},
            )
            if response.status_code != 200:
                print(f"commit failed at row {slice_[0]['row']}: {response.status_code}")
                return 1
            for result in response.json()["results"]:
                imported[result["state"]] += 1
            print(f"    committed {min(start + BATCH, len(ready))}/{len(ready)}", flush=True)

        print("\nAPPLIED: " + ", ".join(f"{n} {s}" for s, n in imported.most_common()))
        return 0 if not imported.get("failed") else 1


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tenant-id", required=True)
    parser.add_argument("--csv", required=True, type=Path)
    parser.add_argument("--apply", action="store_true", help="Write. Without it, plan only.")
    args = parser.parse_args()
    if not args.csv.exists():
        sys.exit(f"{args.csv} is missing. Run scripts/extract_staff.py first.")
    os.environ.setdefault("PYTHONWARNINGS", "ignore")
    return asyncio.run(run(args.tenant_id, args.csv.read_bytes(), args.csv.name, args.apply))


if __name__ == "__main__":
    raise SystemExit(main())
