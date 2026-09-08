"""Load a demo contract history for Stanbic Bank into an environment.

Everything in this file is invented for demonstration: the terms, the fees, the
payment frequencies and the service mix. None of it comes from a real Stanbic
agreement, and it must not be loaded into an environment that holds real data.

Runs against the real API through ASGI, so every row passes the same
validation, authorisation and audit a human write would. Only authentication is
stubbed, as it is for any CLI script here.

Identity is the contract term (start and end date) on the client, so a rerun
recognises what it wrote rather than duplicating it. Service assignments are
matched by service, so a service removed in the UI is not silently restored.

    uv run python scripts/seed_stanbic_contracts.py --tenant-id <id>          # plan
    uv run python scripts/seed_stanbic_contracts.py --tenant-id <id> --apply  # write
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from datetime import date
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

API_ROOT = SCRIPTS_DIR.parent
if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))

from import_support import Plan, report, send  # noqa: E402

CLIENT_NAME = "Stanbic Bank"
SIGNED_BY = "Head of Human Capital"

# Five financial years, each its own contract. The service mix widens with each
# renewal, which is what gives the services rail something to show per term.
TERMS = [
    {
        "start_date": "2021-10-01",
        "end_date": "2022-09-30",
        "amount": "96000000",
        "payment_frequency": "Quarterly",
        "is_auto_renew": False,
        "services": {
            "Individual Counselling": "Face to face and telephone, head office and branches.",
            "Crisis Intervention": "24 hour line, response within 2 hours.",
            "Health Talk": "Four talks a year, one per quarter.",
        },
    },
    {
        "start_date": "2022-10-01",
        "end_date": "2023-09-30",
        "amount": "108000000",
        "payment_frequency": "Quarterly",
        "is_auto_renew": False,
        "services": {
            "Individual Counselling": "Six sessions per employee per year.",
            "Crisis Intervention": "24 hour line, response within 2 hours.",
            "Health Talk": "Four talks a year, one per quarter.",
            "Group Counselling": "Branch teams, on request.",
            "Mental Health Talk": "Added after the 2022 wellbeing survey.",
        },
    },
    {
        "start_date": "2023-10-01",
        "end_date": "2024-09-30",
        "amount": "126000000",
        "payment_frequency": "Quarterly",
        "is_auto_renew": True,
        "services": {
            "Individual Counselling": "Six sessions per employee per year.",
            "Crisis Intervention": "24 hour line, response within 2 hours.",
            "Health Talk": "Four talks a year, one per quarter.",
            "Group Counselling": "Branch teams, on request.",
            "Mental Health Talk": "Two talks a year.",
            "Trauma Group Counselling": "Critical incident cover for branch robberies.",
            "Training": "Manager referral training, two cohorts.",
        },
    },
    {
        "start_date": "2024-10-01",
        "end_date": "2025-09-30",
        "amount": "148000000",
        "payment_frequency": "Quarterly",
        "is_auto_renew": True,
        "services": {
            "Individual Counselling": "Eight sessions per employee per year.",
            "Crisis Intervention": "24 hour line, response within 2 hours.",
            "Health Talk": "Four talks a year, one per quarter.",
            "Group Counselling": "Branch teams, on request.",
            "Mental Health Talk": "Two talks a year.",
            "Trauma Group Counselling": "Critical incident cover for branch robberies.",
            "Training": "Manager referral training, two cohorts.",
            "Coaching/Mentorship": "Ten places for first line managers.",
            "Family Therapy": "Extended to spouses and dependants.",
            "Individual Assessment": "Pre-placement and fitness for duty referrals.",
        },
    },
    {
        "start_date": "2025-10-01",
        "end_date": "2026-09-30",
        "amount": "172000000",
        "payment_frequency": "Quarterly",
        "is_auto_renew": True,
        "services": {
            "Individual Counselling": "Eight sessions per employee per year.",
            "Crisis Intervention": "24 hour line, response within 2 hours.",
            "Health Talk": "Four talks a year, one per quarter.",
            "Group Counselling": "Branch teams, on request.",
            "Mental Health Talk": "Two talks a year.",
            "Trauma Group Counselling": "Critical incident cover for branch robberies.",
            "Training": "Manager referral training, three cohorts.",
            "Coaching/Mentorship": "Twenty places, managers and team leads.",
            "Family Therapy": "Extended to spouses and dependants.",
            "Individual Assessment": "Pre-placement and fitness for duty referrals.",
            "Couple Counselling": "Added at the 2025 renewal.",
            "Psychotherapy": "Referral only, capped at 12 sessions.",
            "Physical Wellness": "Quarterly clinics with the medical scheme.",
            "Change Management Talk": "Support for the core banking migration.",
        },
    },
]


async def run(tenant_id: str, apply: bool) -> int:
    from httpx import ASGITransport, AsyncClient

    from app.core.security import TokenData, get_current_user, get_current_user_optional
    from app.main import app

    actor = TokenData(user_id="stanbic-demo-seed", tenant_id=tenant_id, role="Admin")
    app.dependency_overrides[get_current_user] = lambda: actor
    app.dependency_overrides[get_current_user_optional] = lambda: actor

    contracts_plan, assignments_plan = Plan(), Plan()
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://seed", timeout=120
    ) as http:
        client = await _client(http, tenant_id)
        if client is None:
            sys.exit(f"No client named {CLIENT_NAME!r} in tenant {tenant_id}")
        services = await _services(http, tenant_id)
        existing = await _contracts(http, tenant_id, client["id"])
        for term in TERMS:
            await _term(
                http,
                tenant_id,
                client,
                term,
                services,
                existing,
                contracts_plan,
                assignments_plan,
                apply,
            )

    return report(apply, [("contracts", contracts_plan), ("assignments", assignments_plan)])


async def _paged(http, path: str, tenant_id: str, extra: str = "") -> list[dict]:
    """Every page of a list endpoint, flattened."""
    items: list[dict] = []
    page = 1
    while True:
        response = await send(
            http, "GET", f"{path}?tenant_id={tenant_id}&page={page}&limit=100{extra}"
        )
        body = response.json()
        if not isinstance(body, dict):
            return items
        items.extend(body.get("items", []))
        if not body.get("has_more"):
            return items
        page += 1


async def _client(http, tenant_id: str) -> dict | None:
    for row in await _paged(http, "/clients/", tenant_id):
        if row["name"].strip().lower() == CLIENT_NAME.lower():
            return row
    return None


async def _services(http, tenant_id: str) -> dict[str, str]:
    return {row["name"]: row["id"] for row in await _paged(http, "/services/", tenant_id)}


async def _contracts(http, tenant_id: str, client_id: str) -> dict[tuple[str, str], dict]:
    rows = await _paged(http, "/contracts/", tenant_id, f"&client_id={client_id}")
    return {(row["period"]["start_date"], row["period"]["end_date"]): row for row in rows}


async def _term(
    http, tenant_id, client, term, services, existing, contracts_plan, assignments_plan, apply
) -> None:
    key = (term["start_date"], term["end_date"])
    label = f"{term['start_date']} to {term['end_date']}"
    contract = existing.get(key)
    if contract:
        contracts_plan.unchanged.append(label)
    elif not apply:
        contracts_plan.created.append(label)
        assignments_plan.created.extend(f"{label} {name}" for name in term["services"])
        return
    else:
        contract = await _create(http, tenant_id, client["id"], term, label, contracts_plan)
        if contract is None:
            return

    await _assignments(
        http, tenant_id, contract["id"], term, services, label, assignments_plan, apply
    )


async def _create(http, tenant_id, client_id, term, label, plan) -> dict | None:
    """Create the term, sign it so it activates, and expire it if it has run out."""
    payload = {
        "client_id": client_id,
        "start_date": term["start_date"],
        "end_date": term["end_date"],
        "billing_rate": {"amount": term["amount"], "currency": "UGX"},
        "payment_frequency": term["payment_frequency"],
        "is_auto_renew": term["is_auto_renew"],
    }
    response = await send(http, "POST", f"/contracts/?tenant_id={tenant_id}", json=payload)
    if response.status_code != 201:
        plan.failed.append(f"{label}: create returned {response.status_code} {response.text[:120]}")
        return None
    contract = response.json()
    signed = await send(
        http, "POST", f"/contracts/{contract['id']}/sign", json={"signed_by": SIGNED_BY}
    )
    if signed.status_code != 200:
        plan.failed.append(f"{label}: sign returned {signed.status_code}")
        return contract
    if date.fromisoformat(term["end_date"]) < date.today():
        # Archive is what marks a run-out term Expired; there is no other path.
        expired = await send(http, "POST", f"/contracts/{contract['id']}/archive")
        if expired.status_code != 200:
            plan.failed.append(f"{label}: archive returned {expired.status_code}")
    plan.created.append(label)
    return contract


async def _assignments(http, tenant_id, contract_id, term, services, label, plan, apply) -> None:
    assigned = {
        row["service_id"]
        for row in await _paged(
            http, "/service-assignments/", tenant_id, f"&contract_id={contract_id}"
        )
    }
    for name, notes in term["services"].items():
        service_id = services.get(name)
        if service_id is None:
            plan.skipped.append(f"{label} {name}: no such service in this tenant")
            continue
        if service_id in assigned:
            plan.unchanged.append(f"{label} {name}")
            continue
        if not apply:
            plan.created.append(f"{label} {name}")
            continue
        response = await send(
            http,
            "POST",
            f"/service-assignments/?tenant_id={tenant_id}",
            json={"service_id": service_id, "contract_id": contract_id, "notes": notes},
        )
        if response.status_code != 201:
            plan.failed.append(f"{label} {name}: {response.status_code} {response.text[:120]}")
        else:
            plan.created.append(f"{label} {name}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tenant-id", required=True)
    parser.add_argument("--apply", action="store_true", help="write; otherwise plan only")
    args = parser.parse_args()
    raise SystemExit(asyncio.run(run(args.tenant_id, args.apply)))


if __name__ == "__main__":
    main()
