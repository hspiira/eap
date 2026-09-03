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
creates `apps/api/.env` and `apps/web/.env` from the committed samples, creates
the database, applies migrations, and seeds a `dev` tenant with an admin user.
It prints a one-time password for that user at the end.

It is safe to re-run: existing `.env` files, databases and tenants are left
alone.

If your PostgreSQL uses credentials other than `postgres:postgres`, edit
`DATABASE_URL` in `apps/api/.env` and run `pnpm setup` again.

Then start the two dev servers in separate terminals:

```bash
pnpm dev:api    # http://localhost:8000, API docs at /scalar
pnpm dev:web    # http://localhost:3000
```

Sign in at `http://localhost:3000` with tenant code `dev`, the seeded admin
email, and the one-time password.

## Commands

Run from the repository root:

```bash
pnpm setup            # first-run bootstrap; safe to re-run
pnpm bootstrap        # just the env/database/migrate/seed part, no installs

pnpm dev:api          # uvicorn with reload, port 8000
pnpm dev:web          # vite dev, port 3000

pnpm build            # both apps
pnpm test             # unit tests, both apps
pnpm lint             # lint + typecheck, both apps
pnpm contracts        # regenerate the OpenAPI schema and the TS client from it
pnpm contracts:check  # fail if the committed contract or client is stale
```

The two dev servers are separate long-running processes, so they get their own
commands and two terminals. `build`, `test` and `lint` cover both apps and take
`:api` / `:web` variants for one side only.

Per-app commands still work from inside `apps/api` or `apps/web`; see their own
READMEs.

## The API contract

`apps/web` does not hand-write its API types. `pnpm contracts` dumps
`apps/api`'s OpenAPI schema to `apps/api/schema/openapi.json`, then generates
`apps/web/src/api/generated/schema.ts` from it. Both are committed, and CI fails
if either drifts from the code.

Run it whenever you change a route, a request model, or a response model.

## Deployment

`pnpm build` produces two plain artifacts, neither tied to a host:

- `apps/web/.output` — a Nitro **node-server** bundle, started with
  `node .output/server/index.mjs`. Nitro can retarget other platforms with a
  preset, but nothing here sets one.
- `apps/api` — an ASGI app, served by `uvicorn app.main:app` (see `Dockerfile`
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
