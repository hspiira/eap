# Evexía

A multi-tenant Employee Assistance Program (EAP) management platform.

## Features

- **Multi-tenancy** - Isolated data for each organization
- **Client Management** - Organizational clients with hierarchy support
- **Person Management** - Employees, dependents, and service providers
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
cp .env.sample .env
# Edit .env with your settings

# Initialize database (see "Database and migrations" below)
uv run alembic upgrade head

# Start the server
uv run uvicorn app.main:app --reload
```

### Database and migrations

- **Alembic** lives at the **project root** (`alembic/`, `alembic.ini`). This is the usual layout; migrations are a top-level concern and stay out of `app/` so they can run against any environment.
- **PostgreSQL** is recommended (database name: `evexia_db`). Set `DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/evexia_db` in `.env`.

To **drop and recreate** the database and run migrations:

```bash
# Drop existing DB (if any), create evexia_db, then migrate
dropdb evexia_db 2>/dev/null || true
createdb evexia_db

# Ensure .env has DATABASE_URL=postgresql+asyncpg://USER:PASSWORD@localhost:5432/evexia_db
uv run alembic upgrade head
```

Replace `USER` and `PASSWORD` with your PostgreSQL user. Tests still use in-memory SQLite by default.

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
| `/persons` | People (employees, providers, dependents) |
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

See the `/docs` folder for detailed documentation:

- [Module Summary](docs/MODULE_SUMMARY.md) - Platform architecture overview
- [Audit Integration](docs/AUDIT_INTEGRATION_SUMMARY.md) - Audit logging guide
- [Backup and Recovery](docs/BACKUP_AND_RECOVERY.md) - Backup, restore, and retention
- [Rollback Runbook](docs/ROLLBACK_RUNBOOK.md) - Application and database rollback
- [Monitoring and Alerting](docs/MONITORING_AND_ALERTING.md) - Health checks and alerts
- [Deployment](docs/DEPLOYMENT.md) - Environment parity and release checklist

## License

See [LICENSE](LICENSE) for details.
