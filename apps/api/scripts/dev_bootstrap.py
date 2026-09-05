"""
Take a fresh clone to a working dev environment.

    uv run python scripts/dev_bootstrap.py

Idempotent: safe to re-run. Creates the repo-root .env if missing, creates the
database if missing, applies migrations, and seeds a tenant with an admin user
so there is something to log in with.

Invoked by `pnpm setup` from the repo root, which also installs dependencies.
"""

from __future__ import annotations

import getpass
import re
import subprocess
import sys
from pathlib import Path
from urllib.parse import urlsplit

API_DIR = Path(__file__).resolve().parent.parent
REPO_ROOT = API_DIR.parents[1]

# Ports `pnpm dev` uses. Kept here so the consistency check below has something
# to compare the .env against.
API_PORT = 8000
WEB_PORT = 3000

DEV_TENANT_NAME = "Dev Tenant"
DEV_TENANT_CODE = "dev"
DEV_ADMIN_EMAIL = "admin@example.com"


def step(msg: str) -> None:
    print(f"\n==> {msg}")


def warn(msg: str) -> None:
    print(f"    ! {msg}", flush=True)


def copy_if_missing(target: Path, source: Path) -> bool:
    """Return True if the file already existed, so we never clobber real config."""
    if target.exists():
        print(f"    {target.name} already present, left alone", flush=True)
        return True
    if not source.exists():
        warn(f"{source} is missing, cannot create {target.name}")
        return False
    target.write_text(source.read_text(encoding="utf-8"), encoding="utf-8")
    try:
        shown = target.relative_to(REPO_ROOT)
    except ValueError:
        shown = target
    print(f"    created {shown} from {source.name}", flush=True)
    return False


def read_env(name: str) -> str | None:
    """Read a key from the root .env, letting apps/api/.env override it.

    Mirrors the precedence in app.core.config: root first, app-local last.
    """
    value = None
    for env in (REPO_ROOT / ".env", API_DIR / ".env"):
        if not env.exists():
            continue
        for line in env.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line.startswith(f"{name}="):
                value = line.split("=", 1)[1].strip()
    return value


def check_paired_origins() -> None:
    """Warn when CORS_ORIGINS does not admit the frontend's own origin.

    A mismatch is invisible until the browser blocks the first request, and the
    error it prints then points at CORS rather than at this file.
    """
    api_base = read_env("VITE_API_BASE_URL") or ""
    cors = read_env("CORS_ORIGINS") or ""
    origins = [o.strip() for o in cors.split(",") if o.strip()]
    web_origin = f"http://localhost:{WEB_PORT}"
    if web_origin not in origins:
        warn(f"CORS_ORIGINS does not list {web_origin}; the browser will block the frontend")
        warn(f"    add it to CORS_ORIGINS in {REPO_ROOT / '.env'}")
    if api_base and api_base.rstrip("/") != f"http://localhost:{API_PORT}":
        warn(f"VITE_API_BASE_URL is {api_base}, but `pnpm dev` serves the API on :{API_PORT}")


def ensure_database(url: str) -> bool:
    """Create the target database if it is absent. Needs CREATEDB on the role."""
    parts = urlsplit(re.sub(r"^postgresql\+\w+://", "postgresql://", url))
    dbname = parts.path.lstrip("/")
    if not dbname:
        warn("DATABASE_URL has no database name")
        return False

    try:
        import asyncio

        import asyncpg
    except ImportError:
        warn("asyncpg is not installed; run `uv sync --group dev` first")
        return False

    admin_dsn = parts._replace(path="/postgres").geturl()

    async def go() -> bool:
        try:
            conn = await asyncpg.connect(admin_dsn)
        except Exception as exc:
            warn(f"cannot reach PostgreSQL at {parts.hostname}:{parts.port or 5432} - {exc}")
            if "does not exist" in str(exc) and "role" in str(exc):
                warn(
                    f"the server is up but the role is not; try your OS user, e.g. {getpass.getuser()!r}"
                )
                warn(
                    f"    edit DATABASE_URL in {REPO_ROOT / '.env'}, or: createuser -s {parts.username or 'postgres'}"
                )
            else:
                warn(
                    "start PostgreSQL, or point DATABASE_URL in the repo-root .env at a reachable one"
                )
            return False
        try:
            exists = await conn.fetchval("SELECT 1 FROM pg_database WHERE datname = $1", dbname)
            if exists:
                print(f"    database {dbname!r} already exists", flush=True)
                return True
            await conn.execute(f'CREATE DATABASE "{dbname}"')
            print(f"    created database {dbname!r}", flush=True)
            return True
        except Exception as exc:
            warn(f"could not create {dbname!r}: {exc}")
            return False
        finally:
            await conn.close()

    return asyncio.run(go())


def run(args: list[str], *, cwd: Path = API_DIR) -> bool:
    result = subprocess.run(args, cwd=cwd)
    return result.returncode == 0


def tenant_exists(url: str, code: str) -> bool:
    import asyncio

    import asyncpg

    dsn = re.sub(r"^postgresql\+\w+://", "postgresql://", url)

    async def go() -> bool:
        conn = await asyncpg.connect(dsn)
        try:
            return bool(await conn.fetchval("SELECT 1 FROM tenants WHERE code = $1", code))
        except asyncpg.UndefinedTableError:
            return False
        finally:
            await conn.close()

    return asyncio.run(go())


def main() -> int:
    step("Environment file")
    copy_if_missing(REPO_ROOT / ".env", REPO_ROOT / ".env.example")
    check_paired_origins()

    url = read_env("DATABASE_URL")
    if not url:
        warn(f"no DATABASE_URL found in {REPO_ROOT / '.env'}")
        return 1

    step(f"Database ({urlsplit(url).path.lstrip('/') or '?'})")
    if not ensure_database(url):
        return 1

    step("Migrations")
    if not run(["uv", "run", "alembic", "upgrade", "head"]):
        warn("alembic failed; see the output above")
        return 1

    step(f"Seed tenant {DEV_TENANT_CODE!r} with an admin user")
    already_seeded = tenant_exists(url, DEV_TENANT_CODE)
    if already_seeded:
        print(f"    tenant {DEV_TENANT_CODE!r} already exists, skipping", flush=True)
    elif not run(
        [
            "uv",
            "run",
            "python",
            "scripts/seed_tenant.py",
            "--name",
            DEV_TENANT_NAME,
            "--code",
            DEV_TENANT_CODE,
            "--admin-email",
            DEV_ADMIN_EMAIL,
        ]
    ):
        warn("seeding failed; see the output above")
        return 1

    print("\nReady. Start both dev servers with one command:")
    print("    pnpm dev        # api on :8000 (docs at /docs), web on :3000")
    if already_seeded:
        print(f"\nSign in with tenant code {DEV_TENANT_CODE!r} and {DEV_ADMIN_EMAIL}.")
        print("To reset the password: uv run python scripts/seed_user.py --help")
    else:
        print(f"\nSign in with tenant code {DEV_TENANT_CODE!r} and {DEV_ADMIN_EMAIL},")
        print("using the one-time password printed above.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
