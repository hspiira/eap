"""Load the service catalogue and diagnosis taxonomy into an environment.

Runs against the real API through ASGI rather than writing SQL, so every row
passes the same validation, authorisation and audit path a human would use.
Only authentication is stubbed, as it is for any CLI importer; the platform
admin gate on the taxonomy routes stays real and is satisfied by configuration.

Idempotent by identity: diagnosis types and diagnoses by `code`, services by
name. It creates what is missing and patches what differs. It never deletes,
never deactivates, and never renames a row it did not recognise.

    uv run python scripts/import_taxonomy.py --tenant-id <id>            # plan
    uv run python scripts/import_taxonomy.py --tenant-id <id> --apply    # write
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

API_ROOT = Path(__file__).resolve().parent.parent
if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))

from import_support import Plan, report, send  # noqa: E402

DATA = API_ROOT / "data" / "taxonomy"

#: Dev seed rows that are the catalogue's services under an older spelling.
#: Explicit rather than fuzzy-matched: a rename is a decision about identity,
#: and two services differing by one letter must not be reconciled by a string
#: distance. Anything not listed here is left exactly as it is.
SEED_RENAMES: dict[str, str] = {
    "Individual Counseling": "Individual Counselling",
    "Coaching & Mentorship": "Coaching/Mentorship",
    "Group Therapy": "Group Counselling",
}


def _load(name: str) -> list[dict]:
    path = DATA / f"{name}.json"
    if not path.exists():
        sys.exit(f"{path} is missing. Run: uv run python scripts/taxonomy_catalogue.py")
    return json.loads(path.read_text())


def _differs(current: dict, wanted: dict, fields: tuple[str, ...]) -> dict:
    return {
        f: wanted[f] for f in fields if wanted.get(f) is not None and current.get(f) != wanted[f]
    }


async def run(tenant_id: str, apply: bool) -> int:
    from httpx import ASGITransport, AsyncClient

    from app.core.config import settings
    from app.core.security import TokenData, get_current_user, get_current_user_optional
    from app.main import app

    platform = (settings.PLATFORM_TENANT_ID or "").strip()
    if not platform:
        sys.exit(
            "PLATFORM_TENANT_ID is unset, so the taxonomy routes refuse every caller.\n"
            "Set it for this run, e.g. PLATFORM_TENANT_ID=<tenant> uv run python "
            "scripts/import_taxonomy.py ..."
        )

    actor = TokenData(user_id="taxonomy-import", tenant_id=platform, role="Admin")
    app.dependency_overrides[get_current_user] = lambda: actor
    app.dependency_overrides[get_current_user_optional] = lambda: actor

    types_plan, diags_plan, services_plan = Plan(), Plan(), Plan()
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://import", timeout=120
    ) as http:
        type_ids = await _types(http, types_plan, apply)
        await _diagnoses(http, type_ids, diags_plan, apply)
        await _services(http, tenant_id, services_plan, apply)

    return report(
        apply,
        [
            ("diagnosis types", types_plan),
            ("diagnoses", diags_plan),
            ("services", services_plan),
        ],
    )


async def _types(http, plan: Plan, apply: bool) -> dict[str, str]:
    """Upsert every type by code, and return code -> id for the diagnoses pass."""
    existing = {t["code"]: t for t in (await send(http, "GET", "/diagnoses/types")).json()}
    ids: dict[str, str] = {}
    for row in _load("diagnosis_types"):
        current = existing.get(row["code"])
        if current is None:
            if not apply:
                plan.created.append(row["code"])
                continue
            response = await send(http, "POST", "/diagnoses/types", json=row)
            if response.status_code != 201:
                plan.failed.append(f"{row['code']}: {response.status_code} {response.text[:120]}")
                continue
            ids[row["code"]] = response.json()["id"]
            plan.created.append(row["code"])
            continue
        ids[row["code"]] = current["id"]
        changes = _differs(current, row, ("name", "description", "sort_order"))
        if not changes:
            plan.unchanged.append(row["code"])
        elif not apply:
            plan.updated.append(f"{row['code']} ({', '.join(changes)})")
        else:
            response = await send(http, "PATCH", f"/diagnoses/types/{current['id']}", json=changes)
            (plan.updated if response.status_code == 200 else plan.failed).append(row["code"])
    return ids


async def _diagnoses(http, type_ids: dict[str, str], plan: Plan, apply: bool) -> None:
    tree = (await send(http, "GET", "/diagnoses/types")).json()
    by_id = {t["id"]: t["code"] for t in tree}
    existing: dict[str, dict] = {}
    for item in (await send(http, "GET", "/diagnoses")).json():
        existing[item["code"]] = item
    for row in _load("diagnoses"):
        type_id = type_ids.get(row["type_code"])
        if type_id is None:
            plan.skipped.append(f"{row['code']}: type {row['type_code']} not present")
            continue
        current = existing.get(row["code"])
        payload = {
            "type_id": type_id,
            "code": row["code"],
            "name": row["name"],
            "description": row["description"],
            "sort_order": row["sort_order"],
        }
        if current is None:
            if not apply:
                plan.created.append(row["code"])
                continue
            response = await send(http, "POST", "/diagnoses", json=payload)
            if response.status_code == 409:
                # The tree lists only available rows, so a retired diagnosis
                # reads as missing. Its code is still taken, and recreating it
                # would be a second row for one condition.
                plan.skipped.append(
                    f"{row['code']}: code exists but is not in the tree; it is retired, "
                    "reactivate it rather than creating a duplicate"
                )
                continue
            if response.status_code != 201:
                plan.failed.append(f"{row['code']}: {response.status_code} {response.text[:120]}")
                continue
            if not row.get("is_active", True):
                await send(
                    http, "POST", f"/diagnoses/{response.json()['id']}/active?is_active=false"
                )
            plan.created.append(row["code"])
            continue
        changes = _differs(current, payload, ("name", "description", "sort_order"))
        if by_id.get(current.get("type_id")) != row["type_code"]:
            changes["type_id"] = type_id
        wanted_active = row.get("is_active", True)
        retire = current.get("is_active", True) != wanted_active
        if not changes and not retire:
            plan.unchanged.append(row["code"])
            continue
        note = ", ".join(list(changes) + (["is_active"] if retire else []))
        if not apply:
            plan.updated.append(f"{row['code']} ({note})")
            continue
        if changes:
            response = await send(http, "PATCH", f"/diagnoses/{current['id']}", json=changes)
            if response.status_code != 200:
                plan.failed.append(f"{row['code']}: {response.status_code}")
                continue
        if retire:
            # Availability moves through its own endpoint, which keeps
            # effective_until in step; a PATCH cannot set it.
            response = await send(
                http,
                "POST",
                f"/diagnoses/{current['id']}/active?is_active={str(wanted_active).lower()}",
            )
            if response.status_code != 200:
                plan.failed.append(f"{row['code']}: activity {response.status_code}")
                continue
        plan.updated.append(row["code"])


async def _services(http, tenant_id: str, plan: Plan, apply: bool) -> None:
    """Upsert by name, after applying the explicit seed renames.

    Services carry no code, so name is the only identity available. A row whose
    name is not in the catalogue and not in SEED_RENAMES is left alone and
    reported, never renamed or retired by guesswork.
    """
    listed = (await send(http, "GET", f"/services/?tenant_id={tenant_id}&limit=100")).json()
    if not isinstance(listed, dict) or "items" not in listed:
        raise SystemExit(f"Unexpected services listing: {str(listed)[:200]}")
    existing = {row["name"]: row for row in listed["items"]}

    for old, new in SEED_RENAMES.items():
        row = existing.get(old)
        if row is None or new in existing:
            continue
        if not apply:
            plan.updated.append(f"{old} -> {new} (seed rename)")
            existing[new] = row
            continue
        response = await send(
            http, "PATCH", f"/services/{row['id']}?tenant_id={tenant_id}", json={"name": new}
        )
        if response.status_code == 200:
            plan.updated.append(f"{old} -> {new}")
            existing[new] = response.json()
        else:
            plan.failed.append(f"{old}: rename {response.status_code} {response.text[:120]}")

    wanted = {row["name"] for row in _load("services")}
    for name in sorted(set(existing) - wanted - set(SEED_RENAMES)):
        plan.skipped.append(f"{name}: in the environment, not in the catalogue; left untouched")

    for row in _load("services"):
        current = existing.get(row["name"])
        payload = {k: v for k, v in row.items() if v is not None}
        if current is None:
            if not apply:
                plan.created.append(row["name"])
                continue
            response = await send(http, "POST", f"/services/?tenant_id={tenant_id}", json=payload)
            (plan.created if response.status_code == 201 else plan.failed).append(
                row["name"]
                if response.status_code == 201
                else f"{row['name']}: {response.status_code} {response.text[:120]}"
            )
            continue
        changes = _differs(
            current,
            payload,
            ("description", "category", "duration_minutes", "is_group_service", "max_participants"),
        )
        if not changes:
            plan.unchanged.append(row["name"])
        elif not apply:
            plan.updated.append(f"{row['name']} ({', '.join(changes)})")
        else:
            response = await send(
                http, "PATCH", f"/services/{current['id']}?tenant_id={tenant_id}", json=changes
            )
            (plan.updated if response.status_code == 200 else plan.failed).append(row["name"])


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tenant-id", required=True, help="Tenant that owns the services")
    parser.add_argument("--apply", action="store_true", help="Write. Without it, plan only.")
    args = parser.parse_args()
    os.environ.setdefault("PYTHONWARNINGS", "ignore")
    return asyncio.run(run(args.tenant_id, args.apply))


if __name__ == "__main__":
    raise SystemExit(main())
