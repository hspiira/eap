"""
One-time script: delete the bootstrapped Minet platform tenant and recreate it
via the live API so that azure_tenant_id is set at creation time.

Usage:
    uv run scripts/recreate_platform_tenant.py \
        --api-url https://eap-ten.vercel.app \
        --azure-tenant-id <minet-azure-directory-id> \
        --admin-email henry.ssekibo@minet.co.ug

The script:
  1. Connects to the DATABASE_URL in .env to hard-delete the existing tenant row
     (and its admin user) — bypassing the soft-delete to avoid code conflicts.
  2. Calls POST /tenants/ (no auth required when
     REQUIRE_PLATFORM_ADMIN_FOR_TENANT_CREATION=false) to create a fresh tenant
     with azure_tenant_id already set.
  3. Prints the new tenant ID and set_password_url (if SET_PASSWORD_BASE_URL is
     configured on the server).

Set REQUIRE_PLATFORM_ADMIN_FOR_TENANT_CREATION=false on Vercel temporarily,
run this script, then set it back to true.
"""

import argparse
import asyncio
import os
import sys

import httpx
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

TENANT_ID = "tgl8bu9a7jvdioajnb01ttjf"
TENANT_CODE = "minet"


def _engine(db_url: str):
    url = db_url
    for old in ("postgres://", "postgresql://"):
        if url.startswith(old):
            url = "postgresql+asyncpg://" + url[len(old):]
    for old in ("sslmode=require", "channel_binding=require"):
        url = url.replace(old, "ssl=require")
    return create_async_engine(url, echo=False)


async def hard_delete(db_url: str) -> None:
    engine = _engine(db_url)
    async with engine.begin() as conn:
        # Delete admin users for this tenant first (FK constraint)
        result = await conn.execute(
            text("DELETE FROM users WHERE tenant_id = :tid RETURNING id"),
            {"tid": TENANT_ID},
        )
        deleted_users = result.rowcount
        # Delete the tenant
        result = await conn.execute(
            text("DELETE FROM tenants WHERE id = :tid RETURNING id"),
            {"tid": TENANT_ID},
        )
        deleted_tenants = result.rowcount
    await engine.dispose()
    print(f"Deleted {deleted_tenants} tenant row(s) and {deleted_users} user row(s).")


def create_via_api(api_url: str, azure_tenant_id: str, admin_email: str) -> dict:
    payload = {
        "name": "Minet",
        "code": TENANT_CODE,
        "admin_email": admin_email,
        "azure_tenant_id": azure_tenant_id,
        "azure_sso_enabled": True,
        "subscription_tier": "Enterprise",
        "settings": {
            "max_users": 500,
            "max_clients": 1000,
            "features_enabled": [],
            "custom_branding": True,
        },
    }
    url = api_url.rstrip("/") + "/tenants/"
    print(f"POST {url}")
    with httpx.Client(timeout=30) as client:
        resp = client.post(url, json=payload)
    if resp.status_code not in (200, 201):
        print(f"Error {resp.status_code}: {resp.text}", file=sys.stderr)
        sys.exit(1)
    return resp.json()


def main() -> None:
    parser = argparse.ArgumentParser(description="Recreate Minet platform tenant")
    parser.add_argument("--api-url", required=True, help="BE base URL, e.g. https://eap-ten.vercel.app")
    parser.add_argument("--azure-tenant-id", required=True, help="Minet's Azure directory (tenant) ID")
    parser.add_argument("--admin-email", default="henry.ssekibo@minet.co.ug")
    parser.add_argument(
        "--db-url",
        default=os.environ.get("DATABASE_URL", ""),
        help="Database URL (defaults to DATABASE_URL env var from .env)",
    )
    args = parser.parse_args()

    if not args.db_url:
        print("ERROR: --db-url or DATABASE_URL env var required for hard-delete step.", file=sys.stderr)
        sys.exit(1)

    print("Step 1: hard-delete existing tenant from database...")
    asyncio.run(hard_delete(args.db_url))

    print("Step 2: recreate tenant via API...")
    tenant = create_via_api(args.api_url, args.azure_tenant_id, args.admin_email)

    print("\nDone.")
    print(f"  Tenant ID     : {tenant.get('id')}")
    print(f"  Admin email   : {tenant.get('admin_email')}")
    if tenant.get("set_password_url"):
        print(f"  Set-password  : {tenant['set_password_url']}")
    else:
        print(f"  Admin password: {tenant.get('admin_password')}")
    print(f"  Azure SSO     : enabled={tenant.get('azure_sso_enabled')}, tid={tenant.get('azure_tenant_id')}")
    print(f"\nUpdate PLATFORM_TENANT_ID={tenant.get('id')} in Vercel BE env vars.")


if __name__ == "__main__":
    main()
