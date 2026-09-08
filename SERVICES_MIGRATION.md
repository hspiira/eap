# Services and diagnoses module migration

Working handoff log for the service catalogue and diagnosis taxonomy redesign.
Intentionally untracked while the migration is in progress, matching
`MEMBERS_MIGRATION.md`. Update this file as each phase completes; strike
completed items through rather than removing them.

Companion review, tracked, carrying the data analysis of `services.csv` and the
entitlement finding in its section 3.6: `apps/api/docs/SERVICES_MODULE.md`.
Cite that file rather than this one; this log is untracked by design.

## Product boundary

Two different kinds of data are in scope. They look similar and must not be
given the same lifecycle.

**Service catalogue** (`services`): the interventions a tenant delivers and a
contract can cover. Tenant-owned, commercial, changes with the contract. The
list page already calls these interventions
(`apps/web/src/routes/services/index.tsx:177`).

**Diagnosis taxonomy** (`diagnosis_types`, `diagnoses`): the clinical
vocabulary describing why a session happened. Shared reference data, changes
rarely, must stay comparable across tenants and across years.

Out of scope: clinical cases, notes, outcomes, and risk tables. They consume
the taxonomy but are not part of this migration.

## Baseline

| Property | `industries` | `services` | `diagnoses` |
| --- | --- | --- | --- |
| Tenant-scoped | yes | yes | no, global |
| Hierarchy | self-referential, any depth | none, free-text `category` | fixed two levels |
| Write API | full CRUD + lifecycle | full CRUD + lifecycle | none, three GETs |
| Removal | `deleted_at` soft delete | `deleted_at` soft delete | `is_active` + `effective_until` + `version` |
| Seeding | per tenant, 541 lines | none | one global migration |
| Admin UI | `/industries` + form sheet | `/services`, `$serviceId`, `new` | none, selector only |

Sources: `apps/api/app/infrastructure/models/industry_model.py:19`,
`apps/api/app/api/routes/industries.py` (8 routes),
`apps/api/app/application/services/industry_seed_data.py`,
`apps/api/app/api/routes/diagnoses.py` (3 read-only routes),
`apps/api/alembic/versions/f4a6b8c1d3e5_add_diagnosis_taxonomy.py`.

The conclusion that follows from this table: **`services` already is the
industries pattern.** It is tenant-scoped, has 11 routes, a status lifecycle,
soft delete, and list/detail/create pages. Rebuilding it in the industries
shape would change nothing. `diagnoses` is the module missing a management
surface.

## Decisions

### Accepted from the industries pattern

- **Give diagnoses a real management surface.** Today the only way to change
  the taxonomy is to write an Alembic migration. `services.csv` shows 53 raw
  spellings arriving from the field for 29 buckets, so the taxonomy will keep
  absorbing new values. A migration per value is not workable. Adopt the
  industries route set: create, patch, activate, deactivate, list, get,
  name-availability.
- **Adopt the industries admin UI shape** for diagnoses: a `/diagnoses` route
  with a list, a form sheet, and a detail card, modelled on
  `apps/web/src/components/IndustryFormSheet.tsx` and `apps/web/src/components/IndustryDetailsCard.tsx`.
- **Adopt seeding as data, not as a migration.** Move `_TAXONOMY` out of
  `f4a6b8c1d3e5` into a `apps/api/app/application/services/diagnosis_seed_data.py` (new) module alongside
  `apps/api/app/application/services/industry_seed_data.py`, so the default taxonomy is reviewable and diffable
  without reading a migration.

### Who may create diagnoses and types

The global-taxonomy decision splits "admin" into two roles. Both primitives
already exist, so this is wiring rather than new authorization.

| Action | Gate | Scope |
| --- | --- | --- |
| Create, edit, retire a type or diagnosis | `require_platform_admin` (`apps/api/app/core/authorization.py:203`) | All tenants |
| Enable, disable, reorder, relabel | `require_tenant_role(TenantRole.ADMIN)` (`apps/api/app/core/authorization.py:87`) | One tenant |
| Read the tree | existing `get_current_user` | One tenant, overlay applied |

Tenant admins must not write global rows. If they can, twenty tenants each mint
their own "Work Stress" and the comparability that decision 1 protects is gone.
`services.csv` is what that looks like after the fact: 53 spellings for 29
concepts, reconciled by hand.

Tenant admins are not left without recourse. They get the overlay, which covers
the real cases: hide a type the tenant never sees, rename `GBV` to whatever
their clinicians call it, reorder the picker.

Note the industries write routes gate on `require_same_tenant`
(`apps/api/app/api/routes/industries.py:80`), not on a role. That is defensible
for tenant-owned data. It is not sufficient here, and the diagnosis routes
should not be copied from it.

Prerequisite: `require_platform_admin` is gated on `PLATFORM_TENANT_ID` being
configured (`apps/api/app/core/authorization.py:199`). If that is unset in an
environment, the platform-admin check does not identify anyone and the write
routes must fail closed rather than open. Confirm the setting before phase 3.

Open question for the product owner: what happens when a tenant admin needs a
diagnosis that does not exist. The options are to block them, to let them write
globally (rejected above), or to add a request path that creates the row
disabled everywhere pending platform review. I recommend the request path but
have not designed it, and it is not costed in the phases below.

### Rejected from the industries pattern

Each rejection is evidence-backed. If the evidence is wrong, reopen the
decision.

**1. Do not give diagnosis rows a `tenant_id`.**

`BenchmarkScope` (`apps/api/app/domain/enums/contract.py:45`) exists for
cross-tenant benchmarking, and `SqlBenchmarkCollector.per_tenant_values`
(`apps/api/app/infrastructure/services/benchmark_collector.py:28`) aggregates
across consenting tenants under k-anonymity. Diagnosis prevalence is the
obvious next scope after `SESSION_VOLUME` and `SATISFACTION`. If every tenant
owns a private copy of the taxonomy, no two tenants share a diagnosis id and
that scope cannot be built without a cross-tenant crosswalk. That crosswalk is
exactly the problem `services.csv` documents at the string level, and it is not
worth recreating at the id level.

Industries differ per tenant because tenants sell into different markets. A
clinical taxonomy does not vary that way.

*Instead*: keep the rows global and add a tenant overlay table for the part
that genuinely is tenant preference.

```
tenant_diagnosis_settings
  tenant_id          String(25)  not null, fk tenants.id
  diagnosis_type_id  String(25)  not null, fk diagnosis_types.id
  diagnosis_id       String(25)  null,     fk diagnoses.id
  is_enabled         Boolean     not null default true
  sort_order         Integer     not null default 0
  local_label        String(255) null
  unique (tenant_id, diagnosis_type_id, diagnosis_id)
```

A tenant hides what it never sees and relabels what it calls something else,
while the underlying id stays comparable. This gives the management surface the
industries pattern is wanted for without the cost.

**2. Do not adopt a self-referential hierarchy.**

`service_sessions` stores the two levels as two independent columns,
`diagnosis_type_id` and `diagnosis_id`
(`apps/api/app/infrastructure/models/service_session_model.py:110-111`). With a
`parent_id` chain, resolving a diagnosis to its reporting group becomes a
recursive query on the hottest reporting path instead of reading a column.
`DiagnosisTreeResponse` (`apps/api/app/api/schemas/diagnosis_schemas.py`) and
`TypeGroupList` (`apps/web/src/components/common/DiagnosisSelector.tsx:237`)
are both built for exactly two levels and would both need rewriting.

Industries needs arbitrary depth because its seed data genuinely nests. The
diagnosis seed is uniformly two deep across all 16 types.

*Instead*: keep `type_id` as an explicit column. If a third level is ever
needed, add it as a named level, not as a generic parent pointer.

**3. Do not switch to soft delete.**

`diagnoses` already carries `version` and `effective_until`; industries carries
`deleted_at`. `report_runs.output` persists rendered report JSON
(`apps/api/alembic/versions/i7d9e3f5a8b2_add_report_templates_and_runs.py:67`),
so a report produced last year must still resolve the labels it was built from.
Soft-deleting a diagnosis breaks that; expiring it with `effective_until` does
not.

*Instead*: keep the existing versioning. Deactivation hides a row from new
selection and leaves history intact. This is a stricter contract than
industries has, deliberately.

**Amended 2026-09-07.** The rejection stands; the claim about the mechanism was
false when written. `version` and `effective_until` were read and filtered on
but never written by any code path, so "keep the existing versioning" kept
nothing: deactivation wrote only `is_active`, and a rename mutated the label in
place. The protection this decision claimed for `report_runs.output` did not
exist.

What the mechanism now is, in code and tested in
`apps/api/tests/integration/test_diagnosis_versioning.py`:

- Retirement is dated. Deactivating sets `effective_until`; reactivating clears
  it. The two conditions the read queries require now always agree.
- Any edit that changes a field bumps `version`.
- `code` is the stable identity. `name` and `description` are mutable display
  labels, edited in place.

Successor-row versioning was considered and rejected: `service_sessions`
references `diagnosis_id` and `diagnosis_type_id` directly, so a new row per
edit would orphan them, and the retention requirement is met by
`report_runs.output` already holding the rendered label. The consequence to
accept explicitly is that a superseded label is not recoverable from these
tables. Recovering one needs an audit trail, which the diagnosis routes do not
write; tracked as item 11 in `apps/api/docs/TAXONOMY_FINDINGS.md`.

### Services decisions

**4. `services.category` must become the `ServiceCategory` enum. This is the
highest-value fix in the module.**

`ProgrammeSessionCap.service_category`
(`apps/api/app/domain/value_objects/programme.py:18`) and
`AuthorizationModel.service_category`
(`apps/api/app/infrastructure/models/eap_programme_model.py:50`) are both the
`ServiceCategory` enum, indexed, and they drive programme session caps.
`services.category` is a free-text `String(100)`
(`apps/api/app/infrastructure/models/service_model.py:41`, schema max_length 100
at `apps/api/app/api/schemas/service_schemas.py:23`).

Nothing derives one from the other. A grep for any expression joining
`service_category` to the service catalogue returns nothing. The consequence:
given a completed session you cannot determine which programme cap it should
draw down, because the only link is a free-text string a user typed.

This gap has already produced a visible frontend defect. A web session read
`service.category` as the `ServiceCategory` enum and routed it through
`getStatusLabel` in `9b950c3`, title-casing what users had typed, so `eap`
rendered as `Eap`. Corrected in `166f221`. The blast radius of the naming
collision is therefore wider than the backend phases below.

Related: `Authorization.consume_session`
(`apps/api/app/domain/entities/authorization.py:89`) has no callers other than a
manual route at `apps/api/app/api/routes/eap_programmes.py:203`. Entitlement
drawdown is entirely manual today. Typing the category is the prerequisite for
automating it.

**5. Do not add a services-to-diagnoses join table.**

`services.csv` gives no evidence for such a relationship; it contains no
intervention data at all. Clinically the mapping is not fixed, since counselling
serves most diagnoses. The session already joins them and carries the tenant,
date, and provider that any real analysis needs. If a "suggested interventions
for this diagnosis" feature is wanted later, add it then as an explicit
editable suggestion table and keep it off the reporting path.

This decision is unchanged from the first review and is unrelated to the
industries question, which had not been evaluated at that point.

**6. Legacy strings resolve through a `diagnosis_aliases` table.**

Schema and rationale in `apps/api/docs/SERVICES_MODULE.md` section 4.1.
Unmapped values are rejected at import rather than bucketed into `Others`,
following the existing contract in
`apps/api/app/application/services/historical_import.py:42`.

## Phases

- [x] ~~Phase 0 — Baseline and tracking~~
  - [x] ~~Read repository agent rules.~~ Root `CLAUDE.md`.
  - [x] ~~Record current industries, services, and diagnosis architecture.~~
        Baseline table above.
  - [x] ~~Analyse `services.csv` and publish the review.~~
        `apps/api/docs/SERVICES_MODULE.md`, committed.
  - [x] ~~Capture baseline test counts before any change.~~ API unit 823
        passed; web 52 files / 421 tests passed. API e2e cannot run in this
        environment: the suite wants a `postgres` role that does not exist.
        Pre-existing, unrelated to this work.
- [x] ~~Phase 1 — Type the service category~~ Commit `906bbda`.
  - [x] ~~Data audit.~~ Ran against the local database at head. `services` holds
        0 rows, `service_sessions` 0, `eap_programmes` 0, `authorizations` 0.
        The blocker recorded under open risks was real but empty: there is
        nothing to backfill here. Other environments are unverified, so the
        migration still fails loudly rather than defaulting.
  - [x] ~~Migration.~~ `a5b8c1d4e7f0`. `EnumValueType` persists the enum value as
        a string, so the stored representation does not change and the
        migration adds a CHECK constraint over the existing column. Verified
        against the database: `ShortTermCounselling` and NULL accepted, `eap`
        refused by `service_category_check`.
  - [x] ~~Type the entity, model, mapper, schemas, use cases, and list filter.~~
  - [x] ~~Point the form at the enum.~~ It was offering thirteen hardcoded
        labels ("Individual counselling", "Health talk", "CISM") with no
        relation to `ServiceCategory`, so every service created through the UI
        wrote a category the entitlement side could not read. Labels are an
        explicit map, not derived: `getStatusLabel` splits on a lower-to-upper
        boundary and renders `CISMResponse` as "Cismresponse".
  - [x] ~~Tests.~~ 8 API schema tests, 3 web tests pinning the option list to
        the enum. API unit 831 passed, web 421 passed, `lint-imports` 3 kept 0
        broken.
  - [ ] Commit the regenerated contract. `apps/api/schema/openapi.json` and
        `apps/web/src/api/generated/schema.ts` now carry a `$ref` to
        `ServiceCategory` for all three service schemas, verified, but both
        files also hold another session's in-flight member changes, so they are
        left uncommitted. Whoever lands the member work commits both.
- [x] ~~Phase 2 — Wire entitlement drawdown~~ Commit `f0dc874`.

  The original plan proposed deriving the case from the session. That was
  wrong and stays rejected: a session carries an employer-side `person_id`
  while an authorization is keyed on a case and a pseudonymous
  `ClinicalSubjectId`, and `apps/api/docs/MEMBERS_MODULE.md:77` states plainly
  that a person id is not a member id. There is no bridge, and building one
  would defeat the pseudonymity the case aggregate exists to protect.

  What shipped instead: the case is **supplied** by a caller that already holds
  clinical context, as an optional `case_id` on the completion request. Both
  paths now exist, which is what was asked for. Naming a case draws the session
  down automatically; omitting one leaves the authorization untouched and the
  manual route at `apps/api/app/api/routes/eap_programmes.py:203` unchanged.

  - [x] ~~Derive the category from `service_id`.~~ Possible since phase 1.
  - [x] ~~Consume the matching authorization.~~ Spends the one nearest
        exhaustion first, older grant breaking a tie, so an almost-spent grant
        does not linger behind a fresh one.
  - [x] ~~Report rather than raise.~~ An exhausted, expired, closed or
        wrong-category authorization returns a reason. A completed session is a
        fact and should not fail on a billing condition.
  - [x] ~~Surface the outcome.~~ The response carries it and the detail page
        shows remaining sessions; a silent no-op would be worse than the manual
        route.
  - [x] ~~Tests.~~ 12 covering selection and consumption.
  - [x] ~~Wire a product caller.~~ **This was missing and the phase was marked
        done without it.** The API accepted `case_id`, but both frontend
        callers omitted it, so `drawdown.consumed` was always false and the
        feature never ran outside tests. The completion dialog now offers the
        live cases for the session's client, behind clinical scope. Backfill
        deliberately still sends none: it records history that already
        happened, so spending a live authorization would double count.
        Commit `36b5bfa`.
  - [ ] Automatic resolution from a session alone stays out of scope until the
        members migration retires `/persons`. That is that migration's call,
        not this one's.

- [x] ~~Phase 3 — Diagnosis management surface~~ Commits `48f1110`, `5249c64`.
  - [x] ~~Move `_TAXONOMY` into `diagnosis_seed_data.py`.~~ Verified the
        extracted 16 types and 52 diagnoses match the database exactly.
  - [x] ~~Add write routes gated on `require_platform_admin`.~~ Eight routes:
        create/patch/activate for types and diagnoses, plus the overlay pair.
  - [x] ~~Confirm the write routes fail closed without `PLATFORM_TENANT_ID`.~~
        They do: `require_platform_admin` raises 403 when it is unset
        (`apps/api/app/core/authorization.py:203`). No change needed.
  - [x] ~~Add `tenant_diagnosis_settings`.~~ Migration `b6c9d2e5f8a1`, amended
        by `c7d0e3f6a9b2`.
  - [x] ~~Honour the overlay in the tree endpoint.~~ Missing row inherits;
        `is_enabled` hides; `local_label` replaces the display name while code
        and id stay shared; `sort_order` reorders.
  - [x] ~~Tests.~~ 6 gating tests, 8 overlay tests. API unit 845 passed.
  - [ ] Commit the regenerated contract, blocked with phase 1 on the member
        work in the generated files.

  Defect found and fixed during this phase: the overlay's `sort_order` was
  `NOT NULL DEFAULT 0`, which cannot express "inherit". A tenant that only
  disabled a row would have silently reordered it to first, and a tenant that
  wanted first position could not ask for it. The reordering test failed
  against the original column; `c7d0e3f6a9b2` makes it nullable.
- [x] ~~Phase 4 — Diagnosis admin UI~~ Commit `89885e4`.
  - [x] ~~`/diagnoses` route with the two-level tree and a form sheet.~~
  - [x] ~~Per-tenant hide, show and relabel.~~ Reordering is exposed by the API
        but not yet by the UI; the page has no drag affordance and adding one
        is a larger piece of work than the rest of the page.
  - [x] ~~Hide controls the caller cannot use.~~ Capability comes from
        `GET /diagnoses/capabilities`, added in this phase, rather than from an
        environment variable, so the UI cannot disagree with the API about who
        may write. The overlay is not fetched at all when the caller cannot
        manage it.
  - [x] ~~Tests.~~ 4 page tests covering both capability shapes, the skipped
        overlay fetch, and the relabel badge. Web suite 428 passed.
  - [x] ~~Confirm `DiagnosisSelector` respects the overlay.~~ It does, by
        construction: the selector reads `GET /diagnoses/tree`, and the overlay
        is applied server-side in `_build_tree`. There is no client-side path
        that could disagree.
  - [x] ~~Reordering in the UI.~~ Move up/down on both levels, commit
        `8dd6b6a`. Every sibling position is written, since a null
        `sort_order` means inherit and a partial write would leave the moved
        row tied. Hidden while a search filters the list.
- [ ] Phase 5 — Taxonomy gaps and legacy aliases. Infrastructure done in
      `fedfb04`, aliases made manageable in `7bc3daf`. Only the `Others`
      decision and the values that are not diagnoses remain, and those are a
      clinical call rather than work.
  - [x] ~~Add `diagnosis_aliases`.~~ Migration `d8e1f4a7b0c3`, with
        `diagnosis_id` nullable for the eleven type-only classifications and a
        `confidence` column separating confirmed from inferred.
  - [x] ~~Add a shared normaliser.~~
        `apps/api/app/domain/services/diagnosis_alias.py`. Measured against the
        supplied extract: 53 raw values collapse to 51 keys, two genuine merges,
        and no case where two spellings that merge were classified differently.
  - [x] ~~Add `REJECTED_UNMAPPED_DIAGNOSIS` and wire it into `validate_row`.~~
        A blank diagnosis is accepted with nulls; a value that is present but
        unrecognised fails the row rather than falling into `Others`. The
        original string is kept as `issue_topic`.
  - [x] ~~Alias repository.~~ `list_aliases`, `upsert_alias`, and
        `alias_lookup` shaped for `CanonicalMappings.diagnosis_aliases`.
  - [x] ~~Questions 1 to 3.~~ Answered by the clinical owner 2026-09-05. The
        sixteen inferred assignments are correct and load as `confirmed`;
        `Emotional challenges` folds into `MENTAL_ILL_HEALTH` at type level;
        `Nurturing mental wellness in the workplace` is a promotion, which
        corrects the source rather than transcribing it.
  - [x] ~~Load the confirmed alias rows.~~ Migration `e9f2a5b8c1d4`, 42 rows,
        29 of them type-only. Verified against the database: every held-back
        and non-diagnosis value still rejects.
  - [x] ~~Question 4: load the four rows rather than block on them.~~ Migration
        `c1e4a7b9d2f6` loads them as `confidence = 'inferred'`, which is what
        that column exists for. Rejection was the right default while nothing
        was reviewed, but it blocked the import indefinitely on four values out
        of 53, and a rejected row is not reviewable: it never lands. A reviewer
        lists exactly these with `GET /diagnoses/aliases?confidence=inferred`.
  - [x] ~~Alias management routes.~~ `GET`/`PUT /diagnoses/aliases`, gated on
        platform admin. Adding an alias no longer needs a migration, which was
        the reason unresolved values stayed unmapped. Commit `7bc3daf`.
  - [ ] Question 5 (`Others`) remains open, and so do the two narrative rows,
        `No show` and `Coaching & Mentorship`. None is a diagnosis, so mapping
        them would corrupt prevalence rather than unblock it. Pinned as a test
        so none is quietly mapped later.
- [x] ~~Phase 6 — Reporting and cleanup~~ Commit `473fc71`.
  - [x] ~~Replace the `no_data` stub with a group-by on `diagnosis_type_id`.~~
        The session columns had existed since the taxonomy landed; only the
        query was missing. Run against a live database to confirm it executes.
  - [x] ~~Report at type level.~~ Also reports `unclassified_sessions`, so a
        small total is not read as low demand when it is really low recording.
        Suppression hides a cell without removing it from the total.
  - [x] ~~Regenerate OpenAPI and frontend contracts.~~ No longer blocked: the
        member work landed in `cd47805` and `b423c48` synced the generated
        files, which picked up all nine diagnosis paths, the `ServiceCategory`
        `$ref`, and the capabilities schema. Regenerating now produces no drift.
  - [ ] ~~Consider adding `DIAGNOSIS_PREVALENCE` to `BenchmarkScope`.~~
        **Rejected, and this phase item was wrong.** `per_tenant_values`
        returns `dict[str, float]`, one number per tenant
        (`apps/api/app/infrastructure/services/benchmark_collector.py:28`), and
        its docstring says that shape is deliberate so the k-anon gate stays
        focused on disclosure rather than metric semantics. Prevalence is a
        distribution across 16 types, not one number. Adding the scope would
        mean either reshaping a contract that was kept simple on purpose, or
        picking one number to stand for prevalence, which is a product decision
        rather than a technical one. Reopen with a product owner, not as
        cleanup.

## Status

All six phases are implemented, and the follow-ups from the 2026-09-06 review
(`apps/api/docs/SERVICES_REVIEW_2026_09_06.md`) have landed:

- Drawdown has a product caller (`36b5bfa`). Before this, phase 2 was marked
  complete while the feature could not run outside tests.
- Legacy aliases are manageable through the API, and the four question-4 values
  load as `inferred` rather than blocking the import (`7bc3daf`).
- The platform-admin gate fails closed on the frontend (`2e82313`). Two copies
  read an env var and skipped themselves when it was unset.
- Reordering is in the admin UI (`8dd6b6a`).

What remains is data, not code: question 5 in
`apps/api/docs/SERVICES_MODULE.md` section 5, and the values that are not
diagnoses at all. Those stay rejected at import rather than guessed.

One thing is still deliberately undone: automatic case resolution from a
session alone. A session carries an employer-side member id and a case is keyed
on a pseudonymous subject, so there is no bridge that does not defeat the
privacy wall. It needs the members migration to retire `/persons`, and that is
that migration's call. Naming the case explicitly, which now works, is the
correct interim answer rather than a workaround.

## Resolved: the platform-admin gate failed open on the frontend

Found while building phase 4, fixed 2026-09-06 in `2e82313`.

`isItemEnabled` in `AppSidebar.tsx` and `PlatformGate` in
`RequirePlatformAdmin.tsx` both read `VITE_PLATFORM_TENANT_ID` and skipped the
check when it was empty, so every tenant saw the Tenants link and reached the
route, then got a 403 from an API that fails closed
(`app/core/authorization.py:203`). The second was the more serious: it guards
whole routes, and its docstring stated the skip as intended.

`/auth/me` now returns `is_platform_admin`, derived server-side from the same
setting the API enforces with, and both gates read it. This is the pattern the
phase 4 capabilities endpoint established: one source of truth, and it is the
one that actually enforces.

## Open risks

- ~~Existing `services.category` contents are unaudited.~~ Resolved: 0 rows in
  the local database. Other environments remain unverified; the migration is
  written to fail rather than guess.
- ~~The 16 inferred classification assignments are my reading of the labels.~~
  Confirmed by the clinical owner 2026-09-05; they load as `confirmed`. The
  four values behind question 4 are still a reading, and now say so in the
  data: they load as `confidence = 'inferred'` and are listable.
- ~~`diagnoses.py` is read-only, which callers may be assuming.~~ Writes were
  added in phase 3 and aliases in `7bc3daf`. Reads stayed open to every user
  except the alias list, which is platform-gated because it exposes review
  state rather than selector data.
- The platform-admin split is a design decision, not something the codebase
  states. If the product intends tenant admins to own their own taxonomy, then
  decision 1 above is wrong too and both should be reopened together.
