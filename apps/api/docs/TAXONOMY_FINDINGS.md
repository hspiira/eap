# Taxonomy and catalogue: system findings

Defects and gaps in the implementation, found while preparing the service
catalogue and diagnosis taxonomy in `TAXONOMY_CATALOGUE.md`. Opened
2026-09-07.

Each item carries the evidence that established it. Strike an item through when
it lands and record the commit. Do not remove one without being asked.

Status: 1 of 11 done, 10 open.

## Priority order

Ordered by value against cost, not by number. The number is stable so it can be
cited elsewhere.

| # | Finding | Kind | Status |
| --- | --- | --- | --- |
| 1 | ~~The taxonomy's versioning contract is not implemented~~ | Correctness | Done |
| 2 | A diagnosis cannot be moved between types through the API | Missing capability | Open |
| 3 | Diagnosis descriptions are writable but never displayed | Product gap | Open |
| 4 | `ServiceCategory` cannot classify 13 of 20 services | Schema, needs product decision | Open |
| 5 | `data/seed_data.json` cannot load against the current schema | Broken dev path | Open |
| 6 | Three visit services duplicate `service_sessions.location` | Redundancy | Open |
| 7 | `services.is_group_service` duplicates `service_sessions.category` | Redundancy | Open |
| 8 | `services` has no `code` and is matched on `name` | Design, needs product decision | Open |
| 9 | No ICD-11 field on `diagnoses` | Missing field | Open |
| 10 | No treatment or modality field on `service_sessions` | Missing field | Open |
| 11 | Global taxonomy writes cannot use the tenant-scoped audit path | Design | Open |

## 1. ~~The taxonomy's versioning contract is not implemented~~

`app/infrastructure/models/diagnosis_model.py:5-7` states rows are
"append-only with effective windows; clients filter to `effective_until IS
NULL` for the current taxonomy". The repository filters on it
(`app/infrastructure/repositories/diagnosis_repository.py:90`, `:110`), reads
it and returns it (`:61`, `:75`). Nothing writes it. `version` is never
incremented anywhere.

- `set_type_active` and `set_diagnosis_active` only flip `is_active`
  (`diagnosis_repository.py:156-162`, `:194-200`)
- `update_type` and `update_diagnosis` mutate `name` in place
  (`:141-153`, `:180-191`)

Two consequences. There are two mechanisms for one concept, `is_active` and
`effective_until`, and only one of them works, while the tree query requires
both to agree. And `SERVICES_MIGRATION.md` decision 3 rejected soft delete
specifically to protect the labels persisted in `report_runs.output`; the
mechanism chosen to provide that protection is two columns nothing writes.

This is load-bearing for the catalogue import: 27 of the 88 diagnosis rows are
name updates.

**Decision taken.** Do not build successor-row versioning. It would break the
`service_sessions.diagnosis_id` and `diagnosis_type_id` references, and the
retention requirement is met by `report_runs.output` already holding the
rendered label. Instead make the code honest about what it does:

1. Retirement writes a date. Deactivating stamps `effective_until`;
   reactivating clears it, since a stale date would keep the row filtered out.
   The two predicates then always agree.
2. Any edit that changes a field bumps `version`, so the column stops lying and
   becomes usable as a staleness signal.
3. `code` is the stable identity, `name` is a mutable display label. Correct the
   model docstring and amend decision 3 rather than leaving a false claim in
   place.

Recovering a previous label needs an audit trail, which is item 11.

**Landed.** `_retire` in `diagnosis_repository.py` stamps and clears
`effective_until` alongside `is_active`; `_apply` now reports whether a value
actually changed so `update_type` and `update_diagnosis` bump `version` on a
real edit and not on a no-op patch. The false docstring in `diagnosis_model.py`
is replaced with what the code does, and `SERVICES_MIGRATION.md` decision 3
carries the amendment.

Verified by `apps/api/tests/integration/test_diagnosis_versioning.py`, 8 tests
against local PostgreSQL. Four of them fail against the previous code, which is
what makes them worth having: retirement dating for both tables and the version
bump for both. The other four are regression guards that pass either way,
covering reactivation clearing the date, a no-op patch leaving `version` alone,
and a rename not retiring the row.

## 2. A diagnosis cannot be moved between types through the API

`DiagnosisUpdate` carries name, description and sort_order only
(`app/api/schemas/diagnosis_schemas.py:65-68`), and `update_diagnosis` takes no
`type_id` (`diagnosis_repository.py:180-186`, and the port at
`app/domain/repositories/diagnosis_repository.py:62-69`). The catalogue moves
`CAREER_FATIGUE` from `WORK_STRESS_ANXIETY` to `CAREER_CHALLENGES`, and there
is no route that can do it.

Fix: add an optional `type_id` to `DiagnosisUpdate` and to the port, validate
that the target type exists and is active, and pass it through. A move to a
retired type would remove the leaf from the tree, since `list_types` filters on
`is_active`.

## 3. Diagnosis descriptions are writable but never displayed

`apps/web/src/components/DiagnosisFormSheet.tsx:29-41` and `:109` create and
edit `description`, and the API returns it on `DiagnosisResponse`
(`app/api/schemas/diagnosis_schemas.py:13`). Neither
`apps/web/src/routes/diagnoses.tsx` nor
`apps/web/src/components/common/DiagnosisSelector.tsx` renders it.

The catalogue supplies a description for all 124 rows. They land in the
database and are invisible at the point a counsellor selects a diagnosis, which
is the only place they change recording quality. Cheapest useful fix in this
list: surface it in the selector and on the tree row.

## 4. `ServiceCategory` cannot classify 13 of 20 services

`app/domain/enums/session.py:71-77` has seven values and none covers assessment
or psychoeducation. The catalogue therefore ships 13 services with
`category: null`, covering 474 sessions in the source extract. Category is what
selects the authorization for entitlement drawdown, so those sessions consume
nothing.

Needs a product decision, not only code: extending the enum changes the CHECK
constraint on both `services.category` and `authorizations.service_category`.
Five of the seven existing values have no support anywhere in the source data.

## 5. `data/seed_data.json` cannot load against the current schema

All ten rows under `services` carry a category the `service_category_check`
constraint from migration `a5b8c1d4e7f0` rejects: Counseling, Workshop, Crisis,
Referral, Training, Assessment, Webinar. None is a `ServiceCategory` value, so
`uv run python scripts/load_seed_data.py` fails on that table at head.

Fix: remap the ten values onto the enum or null them. The file is shared, so
coordinate before editing.

## 6. Three visit services duplicate `service_sessions.location`

`Site Visit`, `Hospital Visit` and `Home Visit` are catalogue rows describing
where a session happened. `service_sessions.location` is already
`String(255)` (`app/infrastructure/models/service_session_model.py:169`) and
`session_type` is the Physical/Online enum (`:182`).

This corrects an earlier finding of mine that claimed there was nowhere to
record location. There is. The three rows should be retired once the sessions
that use them are re-recorded against the counselling service actually
delivered, with the location in its own column.

## 7. `services.is_group_service` duplicates `service_sessions.category`

`service_sessions.category` is `SessionCategory`: Individual, Group, Family,
Couples (`app/domain/enums/session.py:25-29`), which is exactly the four-way
vocabulary the source data uses. `services.is_group_service` is a boolean
(`app/infrastructure/models/service_model.py:57`) that cannot express couple or
family.

Also corrects an earlier finding of mine. The delivery shape belongs on the
session, where it already is, and not on the catalogue row. Candidate for
removal rather than for widening into an enum.

## 8. `services` has no `code` and is matched on `name`

`app/infrastructure/models/service_model.py:44-58` has no code column, and the
table is tenant-scoped. `services.json` is applied per tenant matched on name,
so a rename breaks import idempotency, and intervention mix is not comparable
across tenants.

`SERVICES_MIGRATION.md` decision 1 rejected per-tenant diagnosis rows because
"if every tenant owns a private copy of the taxonomy, no two tenants share a
diagnosis id and that scope cannot be built without a cross-tenant crosswalk".
That reasoning applies unchanged to interventions and was not applied to them.

Whether it should be depends on whether intervention mix is ever benchmarked,
which I have not evaluated. This belongs to whoever owns benchmarking.

## 9. No ICD-11 field on `diagnoses`

`app/infrastructure/models/diagnosis_model.py:38-56` carries code, name,
description, sort_order, is_active, version and effective_until. The catalogue
maps roughly fifteen leaves to ICD-11 entities in prose inside the description,
because there is nowhere else to put it.

Fix: a nullable `icd11_code` column, so prevalence can roll up to a standard
classification and a referral or claim can carry it. Note the verification
caveat in `TAXONOMY_CATALOGUE.md`: the codes quoted came from ICD-11 MMS
reference listings and need confirming against the WHO browser before they
enter a clinical or billing record.

## 10. No treatment or modality field on `service_sessions`

`EMDR_INDICATED` exists as a diagnosis leaf only because there is nowhere to
record a treatment decision. `service_sessions` has `notes`, `issue_topic` and
`clinical_outcome` but no modality
(`app/infrastructure/models/service_session_model.py:134-200`).

Fix: record the modality on the session, then retire `EMDR_INDICATED` from the
taxonomy. Counting a treatment decision as a diagnosis inflates trauma
prevalence.

## 11. Global taxonomy writes cannot use the tenant-scoped audit path

Raised by item 1: recovering a previous label needs an audit trail, and the
platform has one. `AuditEventHandler` enqueues domain events on the outbox and
a worker writes `audit_logs` and `entity_changes`
(`app/shared/handlers/audit_event_handler.py`). Diagnosis routes emit nothing:
there is no audit reference anywhere in `app/api/routes/diagnoses.py`.

The obstacle is real rather than an oversight. `AuditLogModel` carries
`TenantMixin`, so `tenant_id` is NOT NULL with a foreign key to `tenants`
(`app/infrastructure/models/base.py:73-83`), while the taxonomy is deliberately
global. Auditing a global write needs either a nullable tenant on audit rows, a
platform tenant to attribute them to, or a separate trail for reference data.
That is a design decision and should not be settled by picking whichever makes
the insert succeed.
