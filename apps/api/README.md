# Evexía

A multi-tenant Employee Assistance Program (EAP) management platform.

## Features

- **Multi-tenancy** - Isolated data for each organization
- **Client Management** - Organizational clients with hierarchy support
- **Member Management** - Client employees and beneficiaries covered by a wellness programme
- **Contract Management** - Service agreements with billing and renewals
- **Service Delivery** - Service catalog, sessions, and scheduling
- **Document Management** - File storage with versioning
- **KPI Tracking** - Performance metrics and reporting
- **Audit Logging** - Complete audit trail for compliance

## Getting Started

### Requirements

- Python 3.12+

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd eap

# Install dependencies
uv sync

# Configure environment
cp ../../.env.example ../../.env   # one file at the repo root feeds both apps
# Edit .env with your settings

# Initialize database (see "Database and migrations" below)
uv run alembic upgrade head

# Start the server
uv run uvicorn app.main:app --reload
```

### Database and migrations

- **Alembic** lives at the **project root** (`alembic/`, `alembic.ini`). This is the usual layout; migrations are a top-level concern and stay out of `app/` so they can run against any environment.
- **PostgreSQL** is recommended (database name: `evexia_db`). Set `DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/evexia_db` in `.env`.

From the repository root, the preferred commands are:

```bash
pnpm migrate:current  # inspect the applied revision
pnpm migrate:heads    # every head; more than one means a branch to merge
pnpm migrate          # apply pending migrations
pnpm migrate:make     # autogenerate a revision; pass -m "message"
pnpm migrate:down     # roll back one revision
pnpm migrate:history  # inspect the migration history
```

These commands operate on the database in `DATABASE_URL`. Verify that the
environment file points to the intended database before running them, especially
for production. The direct `uv run alembic ...` commands below remain available
when working inside `apps/api`.

To **drop and recreate** the database and run migrations:

```bash
# Drop existing DB (if any), create evexia_db, then migrate
dropdb evexia_db 2>/dev/null || true
createdb evexia_db

# Ensure .env has DATABASE_URL=postgresql+asyncpg://USER:PASSWORD@localhost:5432/evexia_db
uv run alembic upgrade head
```

Replace `USER` and `PASSWORD` with your PostgreSQL user. Tests run against PostgreSQL too; set
`TEST_DATABASE_URL` (see `.env.test`); CI provisions a `postgres:16` service for this.

### Seed data (testing)

To load seed data (10+ records per table) for local testing:

```bash
uv run python scripts/load_seed_data.py          # load data
uv run python scripts/load_seed_data.py --clear  # clear seed tables then load
```

Data lives in `data/seed_data.json`. See `data/README.md` for details.

### Access the API

Once running, the API is available at:

- **API**: <http://localhost:8000>
- **Landing**: <http://localhost:8000> · **API docs (Scalar)**: <http://localhost:8000/docs>

## API Overview

| Endpoint | Description |
|----------|-------------|
| `/tenants` | Organization management |
| `/users` | User accounts |
| `/clients` | Client companies |
| `/members` | Client employees and beneficiaries |
| `/members/{id}/next-of-kin` | Restricted emergency contacts for a member |
| `/persons` | Legacy people/provider compatibility API |
| `/contracts` | Service agreements |
| `/services` | Service catalog |
| `/service-sessions` | Session scheduling |
| `/documents` | Document storage |
| `/kpis` | Performance metrics |

## Limits

- **Request body:** Maximum 10MB (requests with `Content-Length` above this return 413).

## Platform admin

When `REQUIRE_PLATFORM_ADMIN_FOR_TENANT_CREATION` is enabled, only platform admins can create tenants. Platform admins are users whose tenant ID equals `PLATFORM_TENANT_ID`. To create the first platform admin:

1. Create a dedicated tenant (e.g. ID `platform` or a UUID) via your database or a one-off script.
2. Set `PLATFORM_TENANT_ID` in the environment to that tenant’s ID.
3. Create a user in that tenant; that user is a platform admin and can create other tenants when the flag is set.

## Testing and linting

Run the same checks as CI locally:

```bash
uv sync --group dev
uv run ruff check app tests
uv run pytest tests -v
```

## Next steps

See the roadmap and deployment docs for production rollout and future features.

## Documentation

Module and review documents for this app are in `docs/`:

- [Members module](docs/MEMBERS_MODULE.md) - roster aggregate and import
- [Services module](docs/SERVICES_MODULE.md) - service catalogue and diagnoses
- [Taxonomy catalogue](docs/TAXONOMY_CATALOGUE.md) - reference data by table
- [Taxonomy findings](docs/TAXONOMY_FINDINGS.md) - open taxonomy questions
- [Contract attachments](docs/CONTRACT_ATTACHMENTS.md) - upload and storage
- [Code quality](docs/code-quality/README.md) - correctness, coverage, structure

Repository-wide migration, review and design records are in the root
[`docs/`](../../docs/README.md) folder.

## License

See [LICENSE](LICENSE) for details.
