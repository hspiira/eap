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

# Initialize database
alembic upgrade head

# Start the server
uvicorn app.main:app --reload
```

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

## Testing and linting

Run the same checks as CI locally:

```bash
uv sync --group dev
uv run ruff check app tests
uv run pytest tests -v
```

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
