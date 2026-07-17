"""
Bootstrap a tenant + admin user + (optional) Azure SSO config in one shot.

Use this until the Phase 2 tenant onboarding UI lands. The script wraps
`CreateTenantUseCase` so it follows the same domain rules as the API.

Two modes:

  Create a new tenant + admin user (+ optional Azure SSO):
    uv run python scripts/seed_tenant.py \
        --name "Minet Uganda" \
        --code minet \
        --admin-email fred@minet.co.ug \
        --azure-tenant-id b3c1e2f4-1234-5678-90ab-cdef01234567

  Wire SSO onto an existing tenant (by code):
    uv run python scripts/seed_tenant.py \
        --existing --code minet \
        --azure-tenant-id b3c1e2f4-1234-5678-90ab-cdef01234567

Flags:
    --existing          Skip create; configure SSO on the tenant matched by --code
    --name              Tenant display name (required unless --existing)
    --code              Short tenant code (3-15 chars, lowercase) (required)
    --admin-email       Email of the initial admin user (required unless --existing)
    --tier              Subscription tier (Free|Basic|Professional|Enterprise)
    --max-users         User cap (default 100)
    --max-clients       Client cap (default 50)
    --azure-tenant-id   Azure AD directory ID; when set enables SSO
    --no-sso            With --azure-tenant-id, store the ID but leave SSO disabled
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

_project_root = Path(__file__).resolve().parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from app.application.use_cases.tenant_use_cases import CreateTenantUseCase
from app.core.config import settings
from app.core.database import AsyncSessionLocal
from app.domain.enums import SubscriptionTier
from app.domain.value_objects.core import TenantId
from app.infrastructure.repositories.industry_repository import (
    IndustryRepositoryImpl,
)
from app.infrastructure.repositories.password_set_token_repository import (
    PasswordSetTokenRepository,
)
from app.infrastructure.repositories.tenant_repository import (
    TenantRepositoryImpl,
)
from app.infrastructure.repositories.user_repository import UserRepositoryImpl
from app.shared.utils.generators import generate_cuid


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Create a tenant + admin user (+ optional Azure SSO), or wire SSO onto an existing tenant.",
    )
    p.add_argument(
        "--existing",
        action="store_true",
        help="Skip create; just configure SSO on the tenant matched by --code.",
    )
    p.add_argument("--name", default=None)
    p.add_argument("--code", required=True)
    p.add_argument("--admin-email", default=None)
    p.add_argument(
        "--tier",
        default="Enterprise",
        choices=[t.value for t in SubscriptionTier],
    )
    p.add_argument("--max-users", type=int, default=100)
    p.add_argument("--max-clients", type=int, default=50)
    p.add_argument(
        "--azure-tenant-id",
        default=None,
        help="Azure AD directory ID (tid claim). Enables SSO unless --no-sso.",
    )
    p.add_argument(
        "--no-sso",
        action="store_true",
        help="With --azure-tenant-id, store it but leave azure_sso_enabled=False.",
    )
    args = p.parse_args()

    if args.existing:
        if not args.azure_tenant_id:
            p.error("--existing requires --azure-tenant-id (nothing else to do otherwise)")
    else:
        missing = [
            f for f, v in {"--name": args.name, "--admin-email": args.admin_email}.items() if not v
        ]
        if missing:
            p.error(f"create mode requires: {', '.join(missing)}")

    return args


async def run(args: argparse.Namespace) -> None:
    set_password_base = (settings.SET_PASSWORD_BASE_URL or "").strip()
    admin_email: str | None = None
    admin_password: str | None = None
    set_password_token: str | None = None
    set_password_expires_at = None

    async with AsyncSessionLocal() as db:
        tenant_repo = TenantRepositoryImpl(db)
        user_repo = UserRepositoryImpl(db)
        industry_repo = IndustryRepositoryImpl(db)
        token_repo: PasswordSetTokenRepository | None = (
            PasswordSetTokenRepository(db) if set_password_base else None
        )

        try:
            if args.existing:
                tenant = await tenant_repo.get_by_code(args.code)
                if not tenant:
                    print(
                        f"ERROR: no tenant with code '{args.code}'. "
                        "Drop --existing to create it, or check the code.",
                        file=sys.stderr,
                    )
                    sys.exit(1)
            else:
                (
                    tenant,
                    admin_email,
                    admin_password,
                    set_password_token,
                    set_password_expires_at,
                ) = await CreateTenantUseCase(
                    tenant_repo,
                    user_repo,
                    industry_repo,
                    password_set_token_repository=token_repo,
                ).execute(
                    tenant_id=TenantId(generate_cuid()),
                    name=args.name,
                    code=args.code,
                    subscription_tier=SubscriptionTier(args.tier),
                    max_users=args.max_users,
                    max_clients=args.max_clients,
                    features_enabled=(),
                    custom_branding=False,
                )

            if args.azure_tenant_id:
                tenant.configure_azure_sso(
                    args.azure_tenant_id,
                    enabled=not args.no_sso,
                )
                await tenant_repo.save(tenant)

            await db.commit()
        except Exception:
            await db.rollback()
            raise

    set_password_url = (
        f"{set_password_base.rstrip('/')}/auth/set-password?token={set_password_token}"
        if set_password_token and set_password_base
        else None
    )

    header = "Tenant updated" if args.existing else "Tenant created"
    print()
    print(header)
    print("-" * len(header))
    print(f"  id:           {tenant.id.value}")
    print(f"  name:         {tenant.name}")
    print(f"  code:         {tenant.code.value}")
    print(f"  status:       {tenant.status.value}")
    print(f"  tier:         {tenant.subscription_tier.value}")
    if args.azure_tenant_id:
        print(f"  azure_tid:    {tenant.azure_tenant_id}")
        print(f"  sso_enabled:  {tenant.azure_sso_enabled}")

    if admin_email:
        print()
        print("Admin user")
        print("----------")
        print(f"  email:        {admin_email}")
        if admin_password:
            print(f"  password:     {admin_password}   (one-time, change after login)")
        if set_password_url:
            print(f"  set-pwd URL:  {set_password_url}")
            print(f"  expires at:   {set_password_expires_at}")

    print()
    if args.azure_tenant_id and not args.no_sso:
        print("Sign-in: visit /auth/login and click 'Continue with Microsoft'.")
    else:
        print("Sign-in: visit /auth/login → use 'tenant code + email + password' form.")
    print()


if __name__ == "__main__":
    asyncio.run(run(parse_args()))
