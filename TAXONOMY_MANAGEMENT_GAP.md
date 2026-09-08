# Taxonomy management: no admin UI, only file edits and scripts

Recorded 2026-09-08. Scope: how the platform's shared reference taxonomies
(diagnosis types, diagnoses, service categories, services) get created and
changed after the initial import. Distinct from `IMPORT_REVIEW_UI_GAP.md`,
which covers reviewing a batch of imported rows, not maintaining the taxonomy
itself afterwards.

## Current state

Every taxonomy addition today means:

1. Edit a JSON file under `apps/api/data/taxonomy/` (or, for a new
   `ServiceCategory` value before this change, edit a Python enum and write an
   Alembic migration to alter a Postgres `CHECK` constraint).
2. Run `scripts/import_taxonomy.py --apply` against production directly from a
   developer machine, with `PLATFORM_TENANT_ID` set.

There is no in-app way for a non-engineer to add a diagnosis, a diagnosis
type, a service, or a service category. Every change is a code change plus a
manual production script run.

## Why this matters

`service_categories` (added 2026-09-08, replacing the `ServiceCategory` enum)
is the second taxonomy, after `diagnosis_types`, modeled as a real table
specifically so it can grow without a migration. A table alone does not
close the gap: someone still has to run a script against production to add a
row. The next time a category, service, or diagnosis needs to be added,
whoever wants that change still depends on an engineer with production
access.

## Frontend still hardcodes the old fixed list

`service_categories` (below) replaced the `ServiceCategory` enum on the
backend, but `apps/web/src/components/ServiceFormSheet.tsx:26-36` still
defines its own hand-maintained `ServiceCategory` enum, `CATEGORY_LABELS` map,
and `z.nativeEnum(ServiceCategory)` validator (also duplicated in
`apps/web/src/types/enums.ts:689` and consumed by
`apps/web/src/types/entities/{clinical,delivery}.ts`). These are not generated
from the OpenAPI schema, so nothing forces them to track the backend table:
today's 7 real categories still match, but adding a category through
`POST /service-categories` alone does not make it selectable in this form,
reintroducing the code-deploy dependency this migration removed on the
backend. Fixing it means fetching `GET /service-categories` instead of the
hardcoded enum, which is exactly the settings-page work below, scoped smaller.

## Suggested direction (not scoped or started)

A platform-admin settings page backed by the existing
`require_platform_admin` authorization gate (`app/core/authorization.py`),
with per-taxonomy CRUD screens: service categories, services, diagnosis
types, diagnoses. Reads and writes go through the existing routes (or new
ones following the same pattern as `services.py`/`diagnoses.py`), so the
audit trail and tenant-scoping already built for those routes covers this
for free. Needs its own scoping pass before implementation: which fields are
editable, what happens to sessions/authorizations referencing a row that
gets deactivated, and whether retirement should be soft (`is_active`,
`effective_until`, mirroring `diagnosis_types`) rather than deletion.
