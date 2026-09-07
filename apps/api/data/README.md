# Seed data

`seed_data.json` contains at least 10 records per table for the EAP platform, with placeholder IDs (e.g. `t01`, `u01`, `c01`) that respect foreign-key order. Use it for development, demos, or tests.

**Tables included:** tenants, users, industries, client_tags, clients, contacts, persons, contracts, services, service_assignments, service_sessions, documents, kpis, kpi_assignments, activities, audit_logs, entity_changes, password_set_tokens, refresh_tokens.

## Loading seed data

From the project root (with `.env` configured and database running):

```bash
uv run python scripts/load_seed_data.py
```

To clear existing data in seed tables and then load (useful for resetting test data):

```bash
uv run python scripts/load_seed_data.py --clear
```

The script uses the app’s `DATABASE_URL`, inserts in dependency order, and keeps the seed IDs so all references remain valid. Enum values in the JSON match the application (e.g. `"Active"`, `"Monthly"`).

That last point is enforced, not assumed: `tests/unit/application/test_seed_data_enums.py` checks the seed against the enums themselves. It exists because ten `services` rows once carried categories no `ServiceCategory` had, which broke the loader silently until someone ran it.
