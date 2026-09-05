# Evexía

Monorepo for the Evexía platform.

| Path | What it is | Stack |
| --- | --- | --- |
| [`apps/api`](apps/api) | Employee Assistance Program API | FastAPI, SQLAlchemy, PostgreSQL, uv |
| [`apps/web`](apps/web) | Web frontend | TanStack Start, React, Tailwind, pnpm |

## Getting started

Install [uv](https://docs.astral.sh/uv/) (Python 3.12), Node 22+ with pnpm 10,
and PostgreSQL 16+. Make sure PostgreSQL is running, then:

```bash
git clone https://github.com/hspiira/eap.git evexia
cd evexia
pnpm setup
```

`pnpm setup` installs both apps' dependencies, then bootstraps the backend:
creates `.env` at the repo root from the committed `.env.example`, creates the
database, applies migrations, and seeds a `dev` tenant with an admin user.
It prints a one-time password for that user at the end.

It is safe to re-run: existing `.env` files, databases and tenants are left
alone.

If your PostgreSQL uses credentials other than `postgres:postgres`, edit
`DATABASE_URL` in `.env` and run `pnpm setup` again.

Then start both dev servers:

```bash
pnpm dev
```

That runs the API on `http://localhost:8000` (Scalar API reference at `/docs`) and the
frontend on `http://localhost:3000` in one terminal, with each line prefixed by
which side it came from. If one crashes the other is stopped too, so you never
end up with half the stack running. `pnpm dev:api` and `pnpm dev:web` still
start them individually.

Sign in at `http://localhost:3000` with tenant code `dev`, the seeded admin
email, and the one-time password.

## Commands

Run from the repository root:

```bash
pnpm setup            # first-run bootstrap; safe to re-run
pnpm bootstrap        # just the env/database/migrate/seed part, no installs
pnpm migrate          # apply pending Alembic migrations to DATABASE_URL
pnpm migrate:make     # autogenerate a revision; pass -m "message"
pnpm migrate:down     # roll back one revision
pnpm migrate:current  # show the database's current migration revision
pnpm migrate:heads    # show every head; more than one means a branch to merge
pnpm migrate:history  # show the migration history

pnpm dev              # both dev servers, one terminal
pnpm dev:api          # uvicorn with reload, port 8000
pnpm dev:web          # vite dev, port 3000

pnpm verify           # everything CI runs, in CI's order
pnpm lint             # ruff + format check + layering, eslint + prettier check
pnpm typecheck        # pyright gate on app/domain, tsc on the frontend
pnpm test             # unit tests with the coverage gate, both apps
pnpm build            # both apps
pnpm format           # apply ruff format and prettier

pnpm contracts        # regenerate the OpenAPI schema and the TS client from it
pnpm contracts:check  # fail if the committed contract or client is stale
```

`lint`, `typecheck`, `test`, `build` and `format` cover both apps and take
`:api` / `:web` variants for one side only.

**`pnpm verify` is the same set of gates CI runs, in the same order.** That is
deliberate: if it passes locally it passes in CI. It is slower than `pnpm lint`
because it includes pyright and the coverage gate, so `lint` and `test` stay
the fast inner loop and `verify` is the pre-push check.

### Production migrations

The migration commands use the `DATABASE_URL` loaded from the repo-root `.env`.
For a production deployment, verify that `.env` targets the production database,
check the current revision, and then apply migrations:

```bash
pnpm migrate:heads
pnpm migrate:current
pnpm migrate
pnpm migrate:current
```

Check `migrate:heads` first. `pnpm migrate` resolves `head`, which fails outright
when the history has more than one, and a branch is easy to create by accident
when several people add revisions in parallel. One line of output means one head
and the upgrade is unambiguous.

`pnpm migrate` only applies committed Alembic migrations; it does not seed data
or modify application configuration. Take the normal database backup and follow
the deployment rollback procedure before applying migrations to a shared or
production database.

Two habits that matter more on a shared database than a local one. Commit a
migration before applying it anywhere others use, so the record of what ran
exists in the history rather than only in one working tree. And never edit a
revision after it has been applied; write a new one instead. Alembic decides
what to run from the version table alone, so a revision that is edited after
running leaves the database marked done for work it never did, and no later
`pnpm migrate` will notice.

### Pre-commit hooks

Optional, and worth it. `.pre-commit-config.yaml` at the root covers both apps
and runs the same formatters and linters:

```bash
uv run --project apps/api pre-commit install     # once, per clone
uv run --project apps/api pre-commit run --all-files
```

A backend-only commit skips the frontend hooks and vice versa. Generated files
are excluded globally: CI compares them byte for byte, so a whitespace hook
"tidying" one would break the build it is there to protect.

Per-app commands still work from inside `apps/api` or `apps/web`; see their own
READMEs.

## Configuration

One file, `.env` at the repo root, configures both apps. `pnpm setup` creates it
from the committed `.env.example`; it is gitignored.

- **`apps/api`** reads it through pydantic-settings, then `apps/api/.env` if
  that exists, so a backend-only override is still possible. Later file wins.
- **`apps/web`** reads it because vite's `envDir` points at the repo root.
  Vite only exposes `VITE_`-prefixed variables to the browser bundle, so the
  backend's `SECRET_KEY` and `DATABASE_URL` sharing the file are not shipped to
  clients. Never rename a secret to start with `VITE_`.

It was two files before. These values appear on both sides and have to agree,
which is the reason for merging them:

| Backend | Frontend | Must agree because |
| --- | --- | --- |
| `CORS_ORIGINS` | the port `pnpm dev:web` serves on | the browser blocks the frontend if its origin is not in the allowlist |
| the port `pnpm dev:api` serves on | `VITE_API_BASE_URL` | the frontend has to call the API where it actually is |
| `PLATFORM_TENANT_ID` | `VITE_PLATFORM_TENANT_ID` | the backend enforces the platform-admin gate, the frontend only shows or hides the UI |
| `AZURE_CLIENT_ID` and friends | `VITE_AZURE_SSO_ENABLED` | the button appears whether or not the backend can complete the flow |

`pnpm bootstrap` warns when the first two disagree, since otherwise the symptom
is a CORS error in the browser console that does not name the file to fix.

Tests ignore all of this: `ENVIRONMENT=test` reads `apps/api/.env.test` and
nothing else, so a local `.env` cannot change what the suite sees.

## Repository layout

`apps/web` is a pnpm workspace package (`@evexia/web`), declared in
`pnpm-workspace.yaml`. There is one lockfile, `pnpm-lock.yaml` at the root, and
`pnpm install` from the root installs everything Node. `apps/api` is a uv
project and is deliberately outside the workspace, since pnpm has nothing to
say about Python.

Everything is stored with LF line endings, enforced by `.gitattributes`. Three
generated files are committed and checked for staleness in CI, so a checkout
that rewrote them with CRLF would fail those gates:

| File | Generated by | Gate |
| --- | --- | --- |
| `apps/api/schema/openapi.json` | `pnpm contracts` | `contract` job |
| `apps/web/src/api/generated/schema.ts` | `pnpm contracts` | `contract` job |
| `apps/web/src/routeTree.gen.ts` | `pnpm build:web` | `web` job |

## Known gaps

- The integration and E2E suite (`pytest tests --ignore=tests/unit`) is
  currently red and runs with `continue-on-error: true` in CI. It does not gate
  merges until that is fixed.
- Backend type coverage is ratcheting. `app/domain` is a strict zero-error
  pyright gate; the rest of the project is reported but not enforced.
- Backend test coverage sits just above the 60% floor (63%), so a moderately
  sized untested addition can fail the gate.
- `apps/web/eslint.config.js` points developers at `docs/CODING_GUIDELINES.md`
  and `docs/IMPLEMENTATION_PLAN.md` in two of its error messages. Neither file
  exists anywhere in the repository.
- `apps/web` depends on `nitro-nightly@latest`, which is unpinned and can change
  under you between installs. The lockfile holds it steady until something
  forces a re-resolve.

## The API contract

`apps/web` does not hand-write its API types. `pnpm contracts` dumps
`apps/api`'s OpenAPI schema to `apps/api/schema/openapi.json`, then generates
`apps/web/src/api/generated/schema.ts` from it. Both are committed, and CI fails
if either drifts from the code.

Run it whenever you change a route, a request model, or a response model.

## Deployment

`pnpm build` produces two plain artifacts, neither tied to a host:

- `apps/web/.output`:  a Nitro **node-server** bundle, started with
  `node .output/server/index.mjs`. Nitro can retarget other platforms with a
  preset, but nothing here sets one.
- `apps/api`:  an ASGI app, served by `uvicorn app.main:app` (see `Dockerfile`
  for the container form).

So either half can run on a VM, in a container, or on a platform. Today both
happen to be wired to Vercel through its GitHub integration, as separate
projects on this one repository, distinguished by **Root Directory**:

| Vercel project | Root Directory |
| --- | --- |
| web | `apps/web` |
| api | `apps/api` |

Only the API keeps a `vercel.json`; the frontend is auto-detected.

One push deploys both from the same commit, so the frontend and the API cannot
drift apart. Point the primary domain at the **web** project: the frontend
serves the landing page at `/`, and the API stays reachable on its own domain.

### The API needs a second, long-running process

Two pieces of work outlive a request and cannot run on a serverless function:

- **The outbox worker** (`scripts/outbox_worker.py`). Every audited mutation
  writes a row to `outbox_events` inside the request transaction; this worker
  drains those rows into `audit_logs` and `entity_changes`. Nothing else does.
  If it is not running, the audit trail stays empty while the API looks
  healthy. Run exactly one replica: the dispatcher is safe under concurrency
  but not yet efficient, as it has no `SKIP LOCKED`.
- **Queued client imports**, handed to FastAPI `BackgroundTasks` by
  `POST /clients/import/jobs`. A function frozen after the response leaves the
  job in `processing`; it becomes retryable again after `STALE_IMPORT_AFTER`.

`docker-compose.yml` defines both worker services (`outbox-worker` and, under
the `production` profile, `outbox-worker-prod`) from the same image as the API.
On a platform without a worker process type, the outbox worker has to run
somewhere else, such as a small VM or a scheduled container. Moving the queued
import onto the outbox worker would remove the second constraint, but that has
not been done.

### Optional: serve the API under the web domain

The frontend reads its API base from `VITE_API_BASE_URL`. If you add a Vercel
rewrite on the web project sending `/api/:path*` to the API's host and set
`VITE_API_BASE_URL=/api`, the browser talks to a single origin. That removes the
need for CORS entirely and lets `VITE_AUTH_USE_COOKIES=true` work in production,
which keeps tokens out of JavaScript.

This needs the API's real deployment host, so it is not configured here.

## History

The backend moved to `apps/api` with `git mv`, so its commit hashes are
unchanged. Use `git log --follow -- apps/api/<path>` to read a file's history
across the move.

The frontend was absorbed from `hspiira/evexia` with its history rewritten under
`apps/web`; per-file `git log` works there without `--follow`, but its commit
hashes differ from the original repository.
