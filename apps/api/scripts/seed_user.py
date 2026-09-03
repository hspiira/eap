"""
Add a user to an existing tenant. Use until the Phase 2 user-management UI ships.

For Azure SSO users you do NOT need a password - the BE links the Azure OID on
first sign-in by matching the email. Pass --password only if you also want them
to be able to sign in with the password form.

Examples:

    # SSO-only user (no password - they sign in via Microsoft)
    uv run python scripts/seed_user.py \
        --tenant-code minet \
        --email noreply@minet.co.ug \
        --role Admin

    # Password user with a one-time password
    uv run python scripts/seed_user.py \
        --tenant-code minet \
        --email alice@minet.co.ug \
        --password 'TempP@ss123' \
        --role User
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

_project_root = Path(__file__).resolve().parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from app.application.use_cases.user_use_cases import CreateUserUseCase
from app.core.database import AsyncSessionLocal
from app.core.security import hash_password
from app.domain.enums import TenantRole, UserStatus
from app.domain.value_objects.core import Email, UserId
from app.infrastructure.repositories.tenant_repository import (
    TenantRepositoryImpl,
)
from app.infrastructure.repositories.user_repository import UserRepositoryImpl
from app.shared.utils.generators import generate_cuid


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Add a user to an existing tenant (for SSO or password sign-in).",
    )
    p.add_argument("--tenant-code", required=True, help="Tenant code (e.g. 'minet')")
    p.add_argument("--email", required=True)
    p.add_argument(
        "--role",
        default="User",
        choices=[r.value for r in TenantRole],
    )
    p.add_argument(
        "--password",
        default=None,
        help="Optional one-time password. Omit for SSO-only users.",
    )
    p.add_argument(
        "--status",
        default="Active",
        choices=[s.value for s in UserStatus],
        help="Initial user status (default Active so they can sign in immediately).",
    )
    return p.parse_args()


async def run(args: argparse.Namespace) -> None:
    async with AsyncSessionLocal() as db:
        tenant_repo = TenantRepositoryImpl(db)
        user_repo = UserRepositoryImpl(db)

        tenant = await tenant_repo.get_by_code(args.tenant_code)
        if not tenant:
            print(f"ERROR: no tenant with code '{args.tenant_code}'.", file=sys.stderr)
            sys.exit(1)

        existing = await user_repo.get_by_email(Email(args.email), tenant.id)
        if existing:
            print(
                f"ERROR: user {args.email} already exists in tenant {args.tenant_code}.",
                file=sys.stderr,
            )
            sys.exit(1)

        password_hash = hash_password(args.password) if args.password else None
        try:
            user = await CreateUserUseCase(user_repo, tenant_repo).execute(
                user_id=UserId(generate_cuid()),
                tenant_id=tenant.id,
                email=Email(args.email),
                password_hash=password_hash,
                role=TenantRole(args.role),
            )

            target_status = UserStatus(args.status)
            if user.status != target_status:
                if target_status == UserStatus.ACTIVE:
                    user.activate()
                else:
                    user.status = target_status
                await user_repo.save(user)

            await db.commit()
        except Exception:
            await db.rollback()
            raise

    print()
    print("User created")
    print("------------")
    print(f"  id:       {user.id.value}")
    print(f"  tenant:   {tenant.code.value} ({tenant.id.value})")
    print(f"  email:    {user.email.value}")
    print(f"  role:     {user.role.value}")
    print(f"  status:   {user.status.value}")
    if args.password:
        print(f"  password: {args.password}   (one-time)")
    else:
        print("  password: (not set - SSO-only; OID will link on first Microsoft sign-in)")
    print()


if __name__ == "__main__":
    asyncio.run(run(parse_args()))
