# Taxonomy and catalogue: system findings

Defects and gaps in the implementation, found while preparing the service
catalogue and diagnosis taxonomy in `TAXONOMY_CATALOGUE.md`. Opened
2026-09-07.

Each item carries the evidence that established it. Strike an item through when
it lands and record the commit. Do not remove one without being asked.

Status: 6 of 12 done, 5 open, 1 withdrawn. One web item parked, see the note at the end.

## Priority order

Ordered by value against cost, not by number. The number is stable so it can be
cited elsewhere.

| # | Finding | Kind | Status |
| --- | --- | --- | --- |
| 1 | ~~The taxonomy's versioning contract is not implemented~~ | Correctness | Done |
| 2 | ~~A diagnosis cannot be moved between types through the API~~ | Missing capability | Done |
| 3 | ~~Diagnosis descriptions are writable but never displayed~~ | Product gap | Done |
| 4 | ~~`ServiceCategory` cannot classify 13 of 20 services~~ | Decided: do not extend the enum | Done |
| 5 | ~~`data/seed_data.json` cannot load against the current schema~~ | Broken dev path | Done |
| 6 | ~~Three visit services duplicate `service_sessions.location`~~ | Redundancy | Done |
| 7 | ~~`services.is_group_service` duplicates `service_sessions.category`~~ | Withdrawn: not a duplication | Closed |
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

## 2. ~~A diagnosis cannot be moved between types through the API~~

`DiagnosisUpdate` carries name, description and sort_order only
(`app/api/schemas/diagnosis_schemas.py:65-68`), and `update_diagnosis` takes no
`type_id` (`diagnosis_repository.py:180-186`, and the port at
`app/domain/repositories/diagnosis_repository.py:62-69`). The catalogue moves
`CAREER_FATIGUE` from `WORK_STRESS_ANXIETY` to `CAREER_CHALLENGES`, and there
is no route that can do it.

**Landed.** `DiagnosisUpdate` takes an optional `type_id`, the port and the
repository accept it, and `get_type_by_id` was added because the port could
only look a type up by code. The route validates the target through
`_assert_available_type`: unknown is a 404, and retired is a 409 rather than a
silent success, because `list_types` requires `is_active` and a null
`effective_until` and a move onto a type failing either would take the leaf out
of every picker.

A move does not rewrite history. `ServiceSessionEntity.set_clinical_details`
(`app/domain/entities/service_session.py:216-231`) writes
`diagnosis_type_id` and `diagnosis_id` independently, so a session keeps the
type it was recorded against. Prevalence over a period spanning a move will
split across both types, which is a faithful record of what was entered rather
than a defect.

Verified by `tests/unit/api/test_diagnosis_type_move.py`, 4 tests on the guard,
and `tests/integration/test_diagnosis_type_move_persistence.py`, 5 against
local PostgreSQL covering the move, that it leaves the other fields alone, that
it bumps `version`, that a move to the same type is not a change, and the
move-and-rename in one call that the catalogue import performs.

Left open deliberately: the admin UI does not expose the move.
`DiagnosisFormSheet.tsx` edits code, name, description and sort order, and
adding a type selector needs the type list passed into the sheet. The catalogue
import uses the API directly and does not need it.

The regenerated contract is **not** in this commit.
`pnpm contracts:sync` picks up another session's in-flight `ImportReasonCode`
from the practitioner import work, which is not in `HEAD`. Same situation as
phases 1 and 3 recorded in `SERVICES_MIGRATION.md`: whoever lands the
practitioner work regenerates `apps/api/schema/openapi.json` and
`apps/web/src/api/generated/schema.ts`, which will then also carry
`DiagnosisUpdate.type_id`.

## 3. ~~Diagnosis descriptions are writable but never displayed~~

`apps/web/src/components/DiagnosisFormSheet.tsx:29-41` and `:109` create and
edit `description`, and the API returns it on `DiagnosisResponse`
(`app/api/schemas/diagnosis_schemas.py:13`). Neither
`apps/web/src/routes/diagnoses.tsx` nor
`apps/web/src/components/common/DiagnosisSelector.tsx` renders it.

The catalogue supplies a description for all 124 rows. They land in the
database and are invisible at the point a counsellor selects a diagnosis, which
is the only place they change recording quality.

**Landed.** Two surfaces, and the description was already on the web types
(`delivery.ts:111`, `:120`), so no contract change was needed.

- `DiagnosisSelector`: a new `DiagnosisOptionLabel` renders code, name and the
  description clamped to two lines. It replaces markup that was duplicated
  between the flat search list and the grouped list, so the description was
  added in one place rather than two. The full text sits under the trigger once
  a diagnosis is selected: clamped is for picking, full is for confirming.
- `/diagnoses`: the definition renders under each type and diagnosis row,
  outside the toggle button. A paragraph inside a control is read out on every
  focus and makes the row's accessible name unusable.

Verified by 3 tests in `src/routes/diagnoses.test.tsx` and 3 in
`src/components/common/DiagnosisSelector.test.tsx`, each pair covering the type
row, the child row, and a row with no description rendering no placeholder. One
fixture diagnosis gained a description, since `diagnoses-fixture.ts` gave them
to types only and the selector tests read the fixture.

Search still matches code and name only. Matching inside a paragraph-length
description would return leaves whose label has nothing to do with the query;
that is a behaviour change, not a display fix, and is not part of this item.

Two stale claims corrected while in the file: the selector's docstring
described the type groups as ICD-10 categories, which the taxonomy is not.

## 4. ~~`ServiceCategory` cannot classify 13 of 20 services~~

`app/domain/enums/session.py:71-77` has seven values and none covers assessment
or psychoeducation. The catalogue therefore shipped 13 services with
`category: null`, covering 474 sessions in the source extract. Category is what
selects the authorization for entitlement drawdown.

**Correction to how this was first reported.** I wrote that those sessions
"silently consume nothing". The word silently was wrong.
`ConsumeAuthorizationForSessionUseCase.execute` returns
`DrawdownResult(None, "Service has no category, nothing to draw down against")`
(`app/application/use_cases/authorization_drawdown.py:73-74`), the response
carries it, and `test_an_untyped_service_draws_down_nothing`
(`tests/unit/application/test_authorization_drawdown.py:118-123`) already pins
it. A null category is reported, not swallowed. That changes what this finding
is: not a missing signal, but a question about whether these services should be
capped at all.

**Decision: do not extend the enum.** Three reasons, in order of weight.

1. No evidence of demand. `ProgrammeSessionCap` values come from contracts, and
   there is no contract data showing a cap on assessment or psychoeducation. An
   enum value nothing grants is a value nothing can draw against.
2. The enum already has this disease. Five of its seven values,
   `CrisisIntervention`, `SubstanceUse`, `ManagerConsult`, `WorkLifeReferral`
   and `CISMResponse`, had no support anywhere in the source data. Adding an
   eighth unused value makes the enum less trustworthy, not more complete.
3. For most of the 13, a null category is the correct answer rather than a gap.
   A health talk delivered to a room has no individual entitlement to draw
   against, which is the same distinction `SessionAttendance.COMPANY_WIDE`
   already draws at the session level.

**What landed instead.**

- `Trauma Group Counselling` is now `CISMResponse`. Incident-driven group work
  is exactly what that value is for; it was unmapped only because nothing had
  ever been mapped to it. This is an entitlement classification and does not
  license debriefing as the method, which WHO recommends against; the
  description says so.
- The remaining 12 are declared in an `UNCAPPED` table in
  `scripts/taxonomy_catalogue.py`, each with the reason it is never capped, and
  `_check_categories` enforces the pairing at build time. A service with a null
  category that nobody declared fails the build; so does a declared-uncapped
  service that later acquires a category, and so does any category that is not
  a `ServiceCategory` value. A deliberate null is now separable from a
  forgotten one, and force-fitting fails loudly.

Categorised services went from 7 to 8 of 20. Reopen this if a contract ever
grants a cap on assessment or psychoeducation, which is the evidence that was
missing.

**Update 2026-09-08: reopened, mechanism changed, decision held.** Migration
`7af2412c8b90` replaced the `ServiceCategory` enum with a `service_categories`
table (see `docs/SERVICES_MODULE.md` §3.6's update of the same date), removing
reason 2 above: a category is now a row, not a code deploy, so the enum can no
longer "get less trustworthy" by growing. `Assessment` and `Psychoeducation`
now exist as rows in that table. I initially assigned them to these 9 services
directly; that was wrong, caught before it reached production, and reverted.
Giving these services a real category, even a fitting one, removes the
structural guarantee that they can never draw down an entitlement (a future
programme cap on `Assessment` or `Psychoeducation` would apply to them),
which is exactly the policy this decision protected. Reason 1, no evidence of
demand, still holds, so the 9 stay `category: null` via `UNCAPPED`
exactly as before. `Assessment` and `Psychoeducation` remain in the table for
a future service that should genuinely be capped.

## 5. ~~`data/seed_data.json` cannot load against the current schema~~

All ten rows under `services` carry a category the `service_category_check`
constraint from migration `a5b8c1d4e7f0` rejects: Counseling, Workshop, Crisis,
Referral, Training, Assessment, Webinar. None is a `ServiceCategory` value, so
`uv run python scripts/load_seed_data.py` fails on that table at head.

**Two rejections, not one.** Verified against PostgreSQL with the schema built
from the models. Through the ORM, which is the path the loader takes,
`EnumValueType` raises `ValueError: Invalid ServiceCategory value: 'Counseling'`
in Python before the statement reaches the database. Through raw SQL, the
`service_category_check` constraint raises `CheckViolationError`. All ten rows
were refused; my first report named only the constraint.

**Landed.** The ten categories are remapped, and the file's one-object-per-line
formatting is preserved, so the diff is ten lines and not the whole file.

| Row | Was | Now | Why |
| --- | --- | --- | --- |
| s01 Individual Counseling | Counseling | `ShortTermCounselling` | One-to-one counselling |
| s02 Group Workshop - Stress | Workshop | null | Psychoeducation, uncapped per item 4 |
| s03 Crisis Support | Crisis | `CrisisIntervention` | 24/7 crisis line |
| s04 Legal Consultation | Referral | `WorkLifeReferral` | Legal advice is a work-life service |
| s05 Financial Counseling | Counseling | `WorkLifeReferral` | Financial consultation is work-life, not clinical |
| s06 Manager Training | Training | null | Employer-commissioned |
| s07 Assessment | Assessment | null | No cap applies, per item 4 |
| s08 Webinar - Wellness | Webinar | null | Psychoeducation |
| s09 Follow-up Session | Counseling | `ShortTermCounselling` | Counselling |
| s10 Couples Counseling | Counseling | `ShortTermCounselling` | Counselling |

`ManagerConsult` stays unused deliberately. It means consulting with a manager
about an employee, not delivering training to managers, and mapping s06 to it
to improve enum coverage is the force-fitting item 4 exists to prevent.

Verified by inserting all ten rows against a schema built from the models: all
ten now commit, where all ten previously failed. Pinned by
`tests/unit/application/test_seed_data_enums.py`, 5 tests asserting the seed
against the enums rather than a snapshot, so a new row with a made-up value
fails there instead of at load time. Confirmed the tests catch the original
defect by stashing the fix: 2 of 5 fail against the old file.

`data/README.md` claimed enum values in the JSON match the application, which
was false when written. It now points at the test that keeps it true.

Root cause worth noting: typing the column in migration `a5b8c1d4e7f0` is what
made the seed invalid, and phase 1 of `SERVICES_MIGRATION.md` audited the
*database* for unmappable values and found none, because the tables were empty.
Nothing audited the seed file.

## 6. ~~Three visit services duplicate `service_sessions.location`~~

`Site Visit`, `Hospital Visit` and `Home Visit` are catalogue rows describing
where a session happened. `service_sessions.location` is already
`String(255)` (`app/infrastructure/models/service_session_model.py:169`) and
`session_type` is the Physical/Online enum (`:182`).

This corrects an earlier finding of mine that claimed there was nowhere to
record location. There is.

**Checked before removing anything.** `location` is not a dead column like
`effective_until` was. It is on the create, update and response schemas
(`app/api/schemas/service_session_schemas.py:53`, `:148`, `:221`) and has a
real input on the session form
(`apps/web/src/components/ServiceSessionFormSheet.tsx:577`). `session_type`,
Physical or Online, is exposed the same way. So a session can already record
Individual Counselling at a named hospital, and removing the three rows loses
nothing.

**Landed.** The three are out of the catalogue, which goes from 20 services to
17. They are recorded in a `NOT_A_SERVICE` table in
`scripts/taxonomy_catalogue.py` with the reason each is not one, alongside
`No show` and `Others`, and `_check_categories` refuses to build a catalogue
that ships any of them. A removed row cannot quietly return.

`Individual Counselling`'s description now says where an off-site session
belongs, because removing the row is only safe if the counsellor knows the
location field is the replacement. The session form's location placeholder was
"Room 4, Zoom, or Phone", which suggested only on-site and remote; it now names
an off-site place too.

Two related guards were added while in the file: an `UNCAPPED` entry naming a
service that is not in the catalogue now fails the build, so a stale
declaration cannot outlive the row it described. All five guard branches
verified against the real catalogue.

Nothing had to be retired in a database. The catalogue has not been imported,
so no session references these rows. Had it been, the order matters: re-record
affected sessions against the counselling service with the location filled,
then deactivate the row.

## 7. ~~`services.is_group_service` duplicates `service_sessions.category`~~

**Withdrawn. I was wrong, and no code changed for it.**

I claimed the boolean duplicates the session enum and was a candidate for
removal. Tracing every consumer before touching it shows the two answer
different questions.

`services.is_group_service` is a definitional constraint on the catalogue row,
and it has live consumers: it gates `max_participants` in
`ServiceEntity.update_group_settings`
(`app/domain/entities/service.py:112-122`), it has its own write path in
`ServiceUpdateGroupSettings` and `PATCH /services/{id}/group-settings` and is
deliberately absent from `ServiceUpdate`
(`app/api/schemas/service_schemas.py:33-54`), it powers the list filter
`?is_group_service=` (`app/api/routes/services.py:257`), and it gates the
`max_participants` input on the web form
(`apps/web/src/components/ServiceFormSheet.tsx:119`).

`service_sessions.category` records what one sitting actually was.

They cannot be collapsed, and the source data proves it. `Family Therapy` is
one group-capable service whose sessions were Family, Couples and Individual.
A single service-level value cannot express that; the session-level enum
already does. My objection that the boolean "cannot express couple or family"
was true and irrelevant, because it is not trying to.

**One correction did follow from getting the meaning right.** `Physical
Wellness` was flagged `is_group_service: false` while the source shows it
delivered to groups in 49 of 206 rows. Read as a capability rather than as a
record, the flag was simply wrong, and it is now true. `max_participants` stays
null: 28 observed headcounts between 5 and 12 describe past delivery, not a
policy anyone set.

## 12. A session's category and headcount are never checked against its service

Found while tracing item 7. `CreateServiceSessionUseCase` takes only the
session repository and never loads the service
(`app/application/use_cases/service_session_use_cases.py:38-39`), so nothing
stops a session recorded as `Group` against a service with
`is_group_service: false`, or a `headcount` above the service's
`max_participants`. The definitional constraint exists and is never enforced.

This is a contradiction rather than a duplication, which is why it is its own
item and not folded into 7. It needs a design decision before code: whether the
check belongs at booking or at completion, whether it should refuse or report
like the drawdown does, and whether the session use case should depend on the
service repository at all given it currently depends on nothing else.

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

## Parked: newest-first on the clients and members lists

`60eb512` gave every list page an explicit `NEWEST_FIRST` default sort.
`clients/index.tsx` and `members/index.tsx` need the same two lines, an import
of `NEWEST_FIRST` and `initialSort: NEWEST_FIRST` on their `useListPage` call,
and both edits are sitting in the working tree uncommitted.

They are not in that commit because both files also carry another session's
in-flight `BulkActionWithReason` work, about forty lines each, and committing
them would have dragged unfinished work in. The change is additive and cannot
conflict, so it will land with whoever commits those files.

Recorded here so it is not lost if that work is discarded rather than
committed. Verify with: both files import `NEWEST_FIRST` and pass it as
`initialSort`.

## Discovered: the web suite has a full-run-only flake

`src/routes/clients/client-members.test.tsx` and
`src/routes/service-sessions/new.test.tsx` fail in a full `pnpm test:web` run
and pass when run on their own. The count varies between runs, three failures
one time and one the next, and it reproduces with an unrelated one-line change
stashed, so it is not caused by any single edit.

Both files log `An update to EntityPicker inside a test was not wrapped in
act(...)` and the same for `DiagnosisSelector`, which is the usual signature of
a state update landing after the assertion. That makes them sensitive to
whatever else is running, so the failure moves around as the suite grows.

Not mine to fix: both files sit in another session's active area, and the suite
grew from 79 files to 83 during this session while that work landed. Recorded
so the next person to see a red web job does not spend the time I did proving
it was pre-existing. Reproduce with `pnpm test:web` twice and compare the
failure list.

## Discovered: the roster rework leaves `client-members.test.tsx` red

The uncommitted `ClientRosterPanel` rewrite in
`apps/web/src/components/clients/ClientManagementPanels.tsx` turned the member
name into a row-click selection rather than a `Link`, replaced the
`Loading members…` paragraph with `TableSkeleton` and the `No members yet.`
paragraph with `EmptyState`. `src/routes/clients/client-members.test.tsx` still
asserts on all three, so seven of its eight tests fail on their own, not only
in a full run. This is not the flake recorded above: it reproduces every time.

Verify with `pnpm --filter @evexia/web vitest run src/routes/clients/client-members.test.tsx`.
The failures name `role="link"` for `Amina Namukasa`, `No members yet.` and
`Loading members…`.

Not mine to fix: the panel rewrite is another session's in-flight work and the
test has to be updated to match whatever that session settles on. Recorded so
whoever commits the roster panel updates the test in the same change.

Closed. That session landed both in `64abbba`, and the file's eight tests pass.

## Uncommitted: `ClientServicesPanel` is deleted in the working tree

Removing the client Services tab left `ClientServicesPanel` in
`ClientManagementPanels.tsx` with no caller. The deletion is applied in the
working tree but not committed, because that file also carries the roster
rewrite above and staging it would drag another session's unfinished work in.
Nothing depends on the deletion: the committed tree still compiles with the
panel present, just unused. It will land with whoever commits that file.

Closed. It landed in `64abbba` with the roster panel; the symbol is gone.

## Discovered: a session never becomes a utilisation event

The client detail Sessions tab reads `utilisation_events`. Nothing in the API
writes one from a session: `UtilisationEventEntity` is constructed in exactly
one place, `POST /utilisation-events` in `app/api/routes/pricing.py`, so the
only way a row appears is somebody calling that endpoint by hand.

The result is a contradiction a user can see. The dashboard counts
`service_sessions` (`dashboard_query_runner.py`), so it reports that clients
have delivered sessions, while each client's own Sessions tab is empty. Before
this change dev held 369 sessions across 35 clients and 0 utilisation events.

`scripts/seed_stanbic_contracts.py` now writes the events for Stanbic Bank, 59
of them, attributing each session to the term its date falls in and carrying
the session id in `source_id` so a rerun skips it. That fills one client's tab
for the demo. It is not the fix: the other 34 clients with sessions still show
nothing, and a session completed in the app tomorrow still records no usage.

The real decision belongs with whoever owns pricing, since it is a billing
question, not a display one:

- does completing a session emit a utilisation event, and is a cancelled or
  no-show session excluded;
- how a session is attributed to a contract, given `service_sessions` carries
  `client_id` and `scheduled_at` but no `contract_id`, and terms can overlap;
- what happens to the 369 sessions already imported;
- what makes the write idempotent, since `utilisation_events.source_id` has no
  unique index.

Left for that work rather than fixed here: `clients.py`,
`utilisation_event_repository.py` and `ClientManagementPanels.tsx` were all
being edited in another session's working tree while this was written.

## Discovered: `ClientUtilisationPanel` is now unreferenced

The client detail Sessions tab reads `service_sessions` as of this change, so
`ClientUtilisationPanel` and the `GET /clients/{client_id}/utilisation-events`
endpoint behind it have no caller left in the app. Both are working code and
were committed the same day in `d18fbfd`, so neither was deleted here.

The reason for the swap: the tab is called Sessions and a utilisation event is
a billing artefact, not a delivery record. Reading `utilisation_events` also
left the tab empty for 34 of the 35 clients that have sessions, per the finding
above. The new panel reads the sessions themselves and needs no seeding.

Utilisation belongs on a contract, which is what it is keyed by. The obvious
home is the contract detail page's Billing tab, beside the pricing model and
the invoice preview that consume the same events. Whoever owns pricing should
either move it there or delete both, rather than leaving them stranded.

Closed for the panel: it now lives on that Billing tab as
`ContractUtilisationPanel`, reading `GET /contracts/{id}/utilisation-events`,
and the client-scoped one is deleted. Still open on the API side:
`GET /clients/{client_id}/utilisation-events` and `utilisationApi.byClient`
have no caller. Both were left rather than deleted, since a client-level
billing view is a reasonable thing to want back. Note the contract endpoint
returns the whole list unpaged, unlike the client one.

The same commit also synced `schema/openapi.json`, which `d18fbfd` had left
behind: the route existed in code but not in the schema, so `contracts:check`
would have failed on it.
