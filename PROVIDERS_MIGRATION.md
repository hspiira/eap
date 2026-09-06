# Provider module migration

Decision record and implementation handoff for the provider module. Updated
2026-09-06 against the assembled integration branch `codex/providers-agent1-core`.
The evidence in "Current implementation and evidence" below describes the
earlier baseline at `3b4daed`; what this branch changed is recorded under
"Phase 1 to 4 verification". Track this document in git. Update it with
each implementation commit; strike completed tasks through rather than deleting
them. Implemented, tested, and applied to a database are separate claims.
Execution ownership and agent prompts are in `PROVIDERS_EXECUTION.md`.

The product owner confirmed the original organisation/practitioner split,
tenant ownership, controlled specialties, optional accounts, and typed profile
fields. On 2026-09-06 the user delegated resolution of the remaining design
questions. The choices below are adopted design decisions under that authority,
not claims that the historical data proves them. They supersede the earlier
single `providers.organisation_id` proposal and phase order.

## Product boundary

A **practitioner** is the individual who delivers a session. `/providers`
continues to mean practitioners; it will not mix people and firms. Existing
provider IDs and session provider references retain their meaning.

A **provider organisation** is a supplier firm with its own identity and
approval status. It is never a practitioner or a login. An **affiliation**
records when a practitioner represents that firm. Employment, affiliation, and
a supplier contract are different facts.

This migration delivers the practitioner directory, affiliations, panel
controls, and trustworthy session attribution. Supplier contract administration,
rate negotiation, invoicing, members, the service catalogue, and tenant staff
are outside this migration. Supporting both firm and individual contracting is
a product requirement, but neither an affiliation nor a missing affiliation
constitutes a contract.

## Current implementation and evidence

At `3b4daed`:

- `providers` still contains required `user_id`, status, and JSON profile and
  licence data. Organisations and affiliations do not exist yet.
- `ProviderEntity`, `ProviderMapper`, and a repository port typed against
  `ProviderEntity` and `ProviderId` are implemented. Session creation no longer
  needs the SQLAlchemy Row shim or a legacy person fallback.
- Provider CRUD exists. Panel tier/status operations emit domain events and
  call the audit handler. General provider creation and patch do not emit
  events and therefore still produce no audit record.
- Migration `f6a8c0e2b4d6` adds provider foreign keys to
  `non_compete_clauses.provider_id` and `outreach_records.counsellor_id`.
  The latter is the actual table behind `care_callback_model.py`. Its preflight
  checks tenant equality, but its foreign keys enforce provider existence only.
  Presence of the migration file does not establish that it was applied.
- The web directory is read-only. Its heading uses `display_name || email`.
  Tier/region filtering runs over the first fetched page of up to 100 rows.
- Three legacy panel use cases still use `PersonRepository`. Graft found only
  test callers for them on 2026-09-06; production panel routes implement the
  operations themselves.

Sources: `apps/api/app/domain/entities/provider.py:15`,
`apps/api/app/infrastructure/mappers/provider_mapper.py:19`,
`apps/api/app/domain/repositories/provider_repository.py:12`,
`apps/api/app/api/routes/providers.py:95`,
`apps/api/app/api/routes/panel.py:42`,
`apps/api/app/api/routes/service_sessions.py:144`,
`apps/api/alembic/versions/f6a8c0e2b4d6_constrain_provider_references.py:37`,
`apps/api/app/application/use_cases/panel_use_cases.py:40`,
`apps/web/src/routes/providers/index.tsx:29`.

### Verification record

The earlier handoff reports local counts of zero providers, service sessions,
and non-compete clauses, with `eap_v2` predating the providers table. This
review has not rerun that database audit. Other environments remain unverified;
no migration may assume they are empty.

The earlier baseline records 1,538 API tests collected and 486 web tests passed
on 2026-09-06. Collection is not a passing backend suite.

### Findings referred to review, 2026-09-06

Discovered while checking for other paths where a rule holds in one place and
not others. Neither is repaired on this branch; both are recorded rather than
left unattended.

1. A `PersonId` carries a user id in the clinical case module.
   `Case.assigned_counsellor_id` is typed `PersonId` at
   `apps/api/app/domain/entities/case.py:79`, and `apps/api/app/api/routes/cases.py:164`
   wraps the request value in `PersonId`. But
   `apps/api/app/application/use_cases/case_use_cases.py:107` reads it as
   `UserId(counsellor_id.value)` and requires a user with Clinical access, so
   the value is a user id wearing a `PersonId` label. This is the same class of
   confusion as phase 5's check that no path treats a `PersonId` as a
   `ProviderId`, and it is why that check should not be closed by inspecting
   provider code alone. Not repaired here: the fix changes the clinical
   aggregate, its persistence and its routes, which this migration does not own.
   Needs an owner in the clinical module.

2. Member and service identity have no reconciliation mechanism for the
   historical extract. Practitioner identity does, through tenant- and
   source-scoped aliases. A staged import row can name a resolved practitioner
   but cannot name a member or a service, so no row is importable. Decided out
   of scope for this release: this document's own import prerequisites do not
   include member or service identity, and building a matcher inside the import
   module would create a second source of identity truth for two aggregates the
   provider module does not own. Unowned and unscoped, recorded so that
   "staging and review work" is not read as "import works".

3. Three times in this branch a rule was correct in one path and absent in
   another: the panel routes that started this migration, the delivering
   organisation resolved only on the create response, and the booking gate
   applied on session creation but not on reschedule. All three are fixed. The
   pattern is worth the reviewer's attention rather than the three instances.

### Phase 1 to 4 verification, 2026-09-06

Recorded by the provider-core and integration agent on branch
`codex/providers-agent1-core`, worktree `/Users/piira/Developer/sandbox/eap/wt-agent1`,
base `e672b6f`. Implemented and locally tested. Not deployed, not pushed, and
applied to no database other than the local throwaway `eap_test_agent1`.

Checks run on the assembled branch:

- `ruff check app tests scripts`: passed.
- `ruff format --check app tests scripts`: 596 files already formatted.
- `lint-imports`: 3 contracts kept, 0 broken.
- `pyright_gate.py --run app/domain`: gate OK for `app/domain`.
- `pytest tests/unit` with the 60% coverage gate: 1411 passed, 65.9% coverage.
- `pytest tests --ignore=tests/unit` with every database URL set: 506 passed,
  1 xfailed, 0 skipped. The zero matters: eight of those tests skipped silently
  before `IMPORT_TEST_DATABASE_URL` and `OUTBOX_TEST_DATABASE_URL` were wired.
- `alembic upgrade head` on an empty database, then `downgrade f6a8c0e2b4d6`,
  then `upgrade head` again: all applied, single head throughout, 68 revisions.

Migration order on the assembled branch, one chain, one head:

    f6a8c0e2b4d6 -> a1p1c0d2e4f6 -> a1p2i0d2e4f6 -> a2n1o0r2k4s6 -> a1p3d0d2e4f6

Evidence for the four reviewed defects:

- Viewer mutation. Refused with 403 on every provider and panel mutation, and
  separately for non-Admin roles on the four lifecycle commands. Proved at the
  route, and against PostgreSQL in `test_provider_audit_persistence.py`, which
  asserts the stored row is unchanged and no outbox row exists after refusal.
- Silent create and PATCH audits. Both now emit. The persistence test drains
  the outbox and asserts the `audit_logs` row with its tenant, actor, resource
  and IP. A separate test injects a commit failure after the audit enqueue and
  asserts the state change, the outbox row and the audit row are all absent.
- Missing tenant constraints. `a1p1c0d2e4f6` keys non-compete, outreach and
  session provider references and the account link on `(tenant_id, id)`;
  `a1p3d0d2e4f6` keys session attribution on
  `(tenant_id, affiliation_id, provider_id)`. Each test asserts the specific
  constraint name that rejected the write, so a NOT NULL violation in a fixture
  cannot pass for a working key. Replacing one composite key with an
  existence-only key was verified to make two tests fail.
- Invalid migration test fixture. The fixture that built three stub tables and
  expected `1 non-compete and 1 outreach` from data containing no clause is
  deleted. Its replacement upgrades the real chain into a scratch schema, and
  `alembic/env.py` now honours an injected connection, which is what makes the
  real chain drivable from a test.

Migration rehearsal on populated data:

- Seeded at `a1p1c0d2e4f6`, then upgraded. The backfill takes the display name
  and email from the linked account, records `BackfilledFromUser` provenance,
  and preserves the existing link, status and credential profile.
- It refuses rather than inventing: a linked account with no display name, and
  two practitioners sharing one account, each abort the upgrade with the
  offending row identifiers.
- An existing session becomes `Unknown` delivery, not `Direct`.

Not verified, and not claimed:

- No target environment counts, revisions or migration application. Nothing ran
  anywhere but a local throwaway database.
- Generated OpenAPI and frontend contracts have not been regenerated on this
  branch. `apps/api/schema/openapi.json` is stale against these routes by
  design until the review gate; that is agent 3's step.
- Every web check is against mocked endpoints. No user flow has been exercised
  against a running API.
- Stale-eligibility prevention is structural, a `FOR UPDATE` read inside the
  booking transaction, not proved by a concurrency test.

## Adopted decisions

### 1. Separate entities, with dated affiliations

Keep `providers` for practitioners and add tenant-owned
`provider_organisations` and `provider_affiliations`. An affiliation has a
practitioner, organisation, `valid_from`, and optional `valid_until`; validity
uses a start-inclusive, end-exclusive interval. Reject overlapping intervals
for the same practitioner/organisation pair. Allow concurrent affiliations with
different organisations.

Do not add a mutable organisation parent column to the practitioner. Do not use
a self-referential provider hierarchy. Firms and people have different behaviour;
that is the reason for separate entities, not an assertion that fixed-depth
relationships require recursive queries.

**Reason:** a directory identity should survive a change of employer or agency.
Allowing multiple affiliations avoids duplicating a person for each firm. This
is a chosen capability, not an assertion that the session extract evidences it.

### 2. Preserve the delivery context on each session

Keep the session's practitioner ID. Add a delivery context of `direct`,
`organisation`, or `unknown`, and a nullable `provider_affiliation_id`.
Organisation delivery requires an affiliation belonging to that practitioner
and tenant and valid at the session time. Direct and unknown delivery have no
affiliation. New bookings require an explicit direct or organisation context;
unknown is available only for historical records with missing evidence.
The delivered practitioner remains required in every accepted session.

Report the organisation through the session's chosen affiliation, never through
the practitioner's current affiliations. An affiliation's practitioner and
organisation IDs cannot be repointed. Retain referenced affiliations and firms;
end or deactivate them instead of deleting them. Before delivery, reassignment
must be validated and audited. After delivery, corrections require a privileged,
audited correction recording the prior attribution and reason.
Changing affiliation dates must not silently invalidate completed attribution;
reject the change or include the affected history in an explicit correction.

For existing sessions, use unknown context unless source evidence establishes
otherwise. Do not infer direct contracting from an empty organisation column.

**Reason:** moving a practitioner to another firm must not rewrite the meaning
of past delivery, while incomplete historical records must remain honest.

### 3. Tenant ownership is enforced throughout each relationship

Practitioners, organisations, affiliations, aliases, and session attribution
remain tenant-owned. Use composite foreign keys and their required unique
constraints to enforce tenant equality and, for session affiliation references,
practitioner equality. Apply the same tenant invariant to user links,
non-compete references, outreach assignments, and specialty links to a provider.
A global specialty reference does not carry a tenant ID.

Application lookups validate the same relationships and return controlled
errors; database constraints protect imports, maintenance scripts, and future
write paths. Preflight validates existing data but does not replace constraints.

**Reason:** globally unique IDs prove identity, not tenant compatibility.
There will be no shared cross-tenant practitioner identity in this migration.
Person-level cross-tenant benchmarking is consequently unsupported; shared
specialty definitions remain compatible with tenant-owned practitioner records.

### 4. Practitioner identity is independent of authentication

Move this work immediately after the boundary repairs. A practitioner owns a
required display name and optional contact email/phone. These describe how to
contact the practitioner, not how to authenticate them. `user_id` and API
`email` become nullable; the response email becomes practitioner contact email.
API documentation must make that change explicit.
For existing linked practitioners, backfill the owned name/contact fields from
the linked user with provenance. Missing required names need reconciliation;
never substitute the raw provider ID or create a new account to fill the gap.

Allow at most one linked user per practitioner and one practitioner per linked
user within the tenant. Enforce uniqueness for non-null links. Only tenant
Admins may link or unlink accounts, after same-tenant validation. Do not auto-link
by matching name or email. Linking neither grants a role nor copies contact
changes in either direction. Account deletion/unlinking must not hide or delete
the practitioner or their historical sessions.

**Reason:** identity and operational contact data must exist without creating
credentials. Shared agency access belongs in a future access model, not in a
login representing several individual practitioners.

### 5. Global specialties; tenant- and source-scoped practitioner aliases

Use a global `provider_specialties` vocabulary with stable IDs/codes, display
labels, and active/inactive state. Catalogue writes require platform-level
administration; tenants select active entries through their own provider links.
Do not introduce tenant-specific specialty definitions in this migration.
Retain retired specialties on historical records but prevent new selection.

Practitioner aliases are different: scope them by tenant and source system.
Preserve the source value and the normalization used. An alias can resolve to
one practitioner only after explicit reconciliation. Do not merge equal names
across tenants or source systems. Ambiguous, unmapped, and missing names are
separate review outcomes; no automatic practitioner creation or placeholder
practitioner is allowed.

**Reason:** shared concepts improve matching without sharing people. Name
normalization is not proof of identity.

### 6. Typed profile fields and independent credential ownership

Promote tier, region, panel status, accreditation status, accreditation authority,
and accreditation expiry to typed fields. Keep bio as text and supplementary
licence details as JSON. Eligibility must not read business rules from that
free-form JSON. Add indexes for actual list/matching queries, starting with
tenant-scoped filter combinations; do not index every enum independently.

Practitioner accreditation belongs to the individual and is always assessed
independently. Organisation supplier approval belongs to the firm. Organisation
accreditation evidence may be recorded separately where applicable and never
substitutes for individual accreditation. The initial booking gate requires
organisation approval/active status, not a blanket clinical-accreditation
requirement for every kind of firm. This is an application policy, not a claim
about professional licensing law.

Migrations preserve every existing credential field and reject missing or
invalid required business data with actionable row identifiers. They must not
invent active or accredited defaults. For new records, default to pending
provider approval and off-panel status; require explicit activation.

**Reason:** distinguish individual competence from approval of a supplier, and
keep expiry data queryable alongside the status it qualifies.

### 7. Enforce booking eligibility; preserve historical delivery facts

A new booking requires a non-deleted, active practitioner, active panel status,
and accredited status. A recorded accreditation expiry must cover both today
and the scheduled service date. Treat an expiry date as valid through that date
in the configured tenant timezone, with Africa/Kampala the chosen default for
this release until a tenant timezone is configured.
No expiry means no recorded expiry, not a fabricated expiry date.

Organisation delivery additionally requires an active, approved organisation
and an affiliation valid at the scheduled time. Direct delivery does not inherit
restrictions from an unrelated organisation affiliation. Apply the same policy
when assigning outreach and when reassigning or rescheduling future sessions.
A suspension flags affected future bookings for review; it does not erase them
or alter completed sessions. Recheck eligibility at the start of delivery.

Use one provider-based application policy for the eligibility endpoint and
write paths. Validate within the write transaction, coordinating with status
changes so a stale preview cannot authorize a booking. Return specific failure
reasons. Tenant Admins manage approval, panel, tier and accreditation; Viewers
cannot mutate. Existing non-Viewer operational roles may maintain ordinary
practitioner contact/profile data and book only through the eligibility gate.

Historical import is a separate, Admin-only operation. It requires a resolved,
same-tenant practitioner and preserves source delivery date and context without
requiring that practitioner to be eligible today. Record provenance and any
missing historical credential evidence. This path cannot create future
bookings or silently invoke billing, authorization consumption, or completion
side effects. Quarantine unresolved rows with reasons; do not invent a person,
organisation, accreditation history, or completed-session fact.

**Reason:** present-day restrictions govern new work, while historical records
must describe what the evidence establishes actually happened.

### 8. One audited mutation path, with legacy provider behaviour retired

Emit creation and change events with actor, tenant, time, and changed fields.
Panel, tier, accreditation and activation changes require a non-blank reason.
Persist state changes and audit records atomically. Repeating an unchanged
command is a no-op rather than a new tier-change event.

General PATCH may update ordinary profile/contact fields, but cannot change
panel, tier, accreditation, or activation fields. Reject those fields explicitly
and use dedicated commands. Profile updates are partial; omitted fields remain
unchanged and explicit null clears only a nullable field. Do not keep a wholesale
profile replacement path that bypasses lifecycle rules.

Replace the three Person-based panel use cases with provider-based application
operations used by the actual routes; port their meaningful behavioural cases to
that production path. Then remove the unused implementations and provider-only
Person methods after checking callers. Do not delete unrelated Person behaviour.

**Reason:** the current tests exercise legacy operations while production routes
have separate logic. There should be one executable rule for each operation,
not a tested legacy version and an untested route version.

### 9. Keep supplier contracting and non-compete expansion out of scope

Organisations are supplier records in this migration. Do not repurpose the
existing customer contract or engagement model without a separate supplier
contract design. A future supplier agreement may name a firm or independent
practitioner, but neither affiliation nor null organisation implies an agreement.
No payments or contractual authorization will be inferred by this module.

The product owner's earlier instruction stands: non-compete is not live and is
to remain where it is. Repair its types and references, but do not import clause
data, expand its workflow, or activate a new booking restriction based on it.
The existing eligibility response may retain its fields for compatibility.

**Reason:** supplier administration should not silently expand into procurement
or revive an explicitly deferred workflow.

### 10. Deliver usable vertical slices and honest migration evidence

Provide practitioner create/edit and server-side search/filter/pagination with
account independence, then add organisation management with affiliations. Keep
counts and filters over the full matching dataset, not the first 100 rows.
Regenerate OpenAPI and frontend contracts in every API-changing phase.

A phase closes only when its implementation, relevant passing tests, generated
contracts, and migration rehearsal are recorded separately. The release gate
requires PostgreSQL tests for empty and populated upgrades, invalid references,
cross-tenant writes after upgrade, and the full Alembic chain. Missing database
configuration must fail that gate rather than silently skip it. Rehearse rollback
where safe and document restore requirements for destructive transformations.

No verified deadline for the historical 80-to-8 panel cull is available. Do not
invent one or let an unverified deadline determine sequencing. Locating the
external SAD remains a documentation task, not a prerequisite to these adopted
decisions; any conflict found must be recorded for resolution.

**Reason:** a working directory and reproducible release checks are more useful
than completing disconnected tables or citing test collection counts.

## Session extract and import acceptance

The prior handoff describes `/Users/piira/Downloads/sessions.csv` as 7,486 rows
and 47 columns, with 7,470 populated rows. It reports 158 raw counsellor spellings,
56 cleaned names, 69 raw values without a clean counterpart covering 328 rows,
and 308 further rows with no counsellor. It reports no contradictory raw-to-clean
mapping and an empty `SERVICE PROVIDER` column in the populated rows.

These are inherited audit claims, not independently reverified in this review.
In particular, 56 cleaned names do not establish 56 distinct people. Before an
import, record a reproducible audit with file hash, row inclusion rules, source
system, reconciliation decisions, and distinct accepted/rejected counts. Do not
infer relationships from the empty supplier column.

Import prerequisites are independent practitioner records, typed profile fields,
approved alias mappings, explicit historical attribution, and an idempotent
staging/import contract. Resolve by stable source record key; replay must neither
duplicate sessions nor silently overwrite a previously imported differing row.
If the source has no stable record key, use file hash plus row number to make
replays of that exact file safe. A changed file requires explicit reconciliation
against earlier imports; do not claim automatic deduplication across files.
Produce accepted, duplicate, conflicting, missing-practitioner, unmapped, and
ambiguous outcomes for review. Unresolved rows stay staged for later correction.
Do not import sessions until these gates exist.

## Implementation order and gates

The revised phases replace the earlier order: old phase 4 (optional accounts)
moves to phase 2; organisations follow as phase 3; profile/vocabulary and import
readiness become phase 4. UI and API contracts accompany their owning phase.

- [ ] Phase 0 - Evidence and tracking
  - [x] ~~Read the repository agent rules.~~ `AGENTS.md` and `CLAUDE.md`.
  - [x] ~~Record the provider architecture and original baseline.~~ Updated above.
  - [x] ~~Record the earlier local data audit and its limitations.~~ Not rerun.
  - [x] ~~Record focused review verification.~~ 47 passed, 2 skipped; see above.
  - [ ] Locate the referenced external SAD and record any conflicts. Not found;
        not invented.
  - [ ] Record target-environment counts and migration state before deployment.
        Not done. No environment other than a local throwaway database has been
        inspected or migrated by this work.

- [ ] Phase 1 - Repair the boundary and mutation controls
  - [x] ~~Add ProviderEntity, mapper and typed repository; remove the session
        Row shim and legacy lookup.~~ Implemented in `3b4daed`.
  - [x] ~~Retype non-compete references and add clause/outreach existence FKs.~~
        Implemented in `f6a8c0e2b4d6`; target application unverified.
  - [x] ~~Emit tier and panel events and call the audit handler.~~ Handler calls
        tested; this does not establish auditing of all provider mutations.
  - [x] ~~Enforce composite tenant constraints and validate outreach assignments.~~
        `a1p1c0d2e4f6`. Outreach assignment loads the counsellor in tenant scope
        and applies the booking gate.
  - [x] ~~Restrict lifecycle commands to Admins and reject Viewer writes.~~
  - [x] ~~Add creation/update audit events, partial PATCH and protected-field rejection.~~
        Eight protected keys rejected with 422 naming the command to use instead.
  - [x] ~~Replace Person-based panel operations and port behavioural coverage.~~
        `panel_use_cases.py` and the Person provider methods removed after
        tracing callers; their cases run against the provider aggregate.
  - [x] ~~Enforce the practitioner eligibility gate on current booking/outreach
        writes;~~ extended with affiliations in phase 3 as planned. One policy,
        applied under a row lock inside the write transaction.
  - [ ] Correct the stale `providers.ts` module comment. Agent 3 owns the file
        and reports it done in `7d914be`; not independently verified here.
  - [x] ~~Correct the migration rejection fixture and require PostgreSQL CI coverage.~~
        CI sets every database URL and `REQUIRE_DATABASE_TESTS` turns a missing
        one into a failure.
  - [x] ~~Prove forbidden writes do not save, audits persist with changes, and
        failures roll back both state and audit records.~~ Against PostgreSQL.
  - [ ] Record contract changes and target migration rehearsal separately.
        Contracts published to agents 2 and 3; generation is agent 3's at the
        review gate. Local rehearsal recorded above; no target environment
        has been touched.

- [ ] Phase 2 - Independent practitioner identity and usable directory
  - [x] ~~Add owned name/contact fields, nullable account link and link uniqueness.~~
        `a1p2i0d2e4f6`. Partial unique index on `(tenant_id, user_id)` where the
        link is non-null, so unlinked practitioners do not collide.
  - [x] ~~Add Admin-only account linking/unlinking and preserve directory visibility
        after account removal.~~ Unlink keeps the record and its sessions.
  - [x] ~~Add create/edit forms,~~ agent 3, mocked tests only.
        ~~server-side filters, search, pagination and totals.~~ Backend: search,
        five repeatable filters, `has_account`, `page`/`limit`, `sort_by`/
        `sort_desc`, `total` counted over the full filtered set.
  - [x] ~~Use a human-readable detail heading.~~ Existing display name/email heading.
  - [ ] Regenerate contracts; test creation without a login and account-link
        authorization, cross-tenant rejection, and full-dataset filtering.
        Backend cases pass. Contract regeneration has not run.

- [ ] Phase 3 - Organisations, affiliations and session attribution
  - [x] ~~Add organisation entity, mapper, repository, CRUD and management UI.~~
        Backend agent 2; UI agent 3, mocked tests only.
  - [x] ~~Add dated affiliations, pair-overlap constraints and composite references.~~
        `a2n1o0r2k4s6`. Start-inclusive, end-exclusive; adjacency is not overlap.
  - [x] ~~Add explicit session delivery context and immutable affiliation attribution.~~
        `a1p3d0d2e4f6`. Composite FK on `(tenant_id, affiliation_id, provider_id)`
        and a check keeping context and reference consistent both ways. Existing
        rows became Unknown, not Direct.
  - [x] ~~Extend the booking policy with organisation approval and affiliation validity.~~
        One policy extended, not a second one. Organisation active and approved
        stay separate reason codes.
  - [ ] Validate reassignment/corrections and retain referenced history.
        Partially done. Narrowing an affiliation interval that would orphan a
        completed session is refused with
        `affiliation_change_would_orphan_attribution`; the guard is tested
        against PostgreSQL including the Kampala midnight boundary. The
        privileged correction path decision 2 also permits, recording the prior
        attribution and reason, is NOT built. Rejection is the implemented half.
  - [ ] Regenerate contracts; prove concurrent affiliations work and moving firms
        does not reattribute old sessions; preserve unknown historical context.
        Attribution reads the session's own affiliation on every response, so
        moving firms cannot reattribute. Contract regeneration has not run.

- [ ] Phase 4 - Typed profile, eligibility and import readiness
  - [ ] Promote structured credential/profile fields with validating migrations.
        NOT DONE. Tier, region, panel status, accreditation status, authority
        and expiry are still in the `provider_profile` JSON column. The mapper
        is the single place the filters reach into that JSON, so the promotion
        changes one function, but the migration is not written. Eligibility
        reads typed enum values off the parsed profile rather than raw JSON, so
        decision 6's "eligibility must not read business rules from that
        free-form JSON" holds in behaviour; the storage change does not.
  - [x] ~~Add global specialties, tenant-owned links and platform write controls.~~
        Agent 2. Retired entries stay on records and are refused for new
        selection. `specialties` is not writable through the practitioner PATCH.
  - [x] ~~Add source-scoped aliases with explicit reconciliation and ambiguity handling.~~
        Agent 2. Missing, unmapped and ambiguous stay separate outcomes.
  - [ ] Move the shared booking/outreach policy to the typed profile fields.
        Blocked on the promotion above. The policy is already shared by every
        write path; only its storage is untyped.
  - [ ] Add future-booking review on suspension and eligibility rechecks on changes.
        NOT DONE. Suspension changes panel status but does not flag affected
        future bookings for review, so decision 7's "a suspension flags affected
        future bookings for review" is unimplemented. Rescheduling does recheck
        the whole gate; delivery start does not.
  - [x] ~~Add Admin-only historical staging/import with provenance and idempotency.~~
        Staging, review outcomes and the Admin-only contract are agent 2's.
        `RecordHistoricalSessionUseCase` is the write path: it does not consult
        the booking gate, refuses a future date, an unresolved or cross-tenant
        practitioner and an inconsistent context, and performs no billing,
        drawdown or completion side effects. Applying imports zero rows today
        because a staged row cannot name a member or a service. See finding 2;
        that is a real gap, not a passing importer.
  - [ ] Regenerate contracts; test expiry boundaries, organisation suspension,
        stale eligibility, imports for currently inactive practitioners,
        rejection of future bookings through import, and missing/ambiguous
        source data. Contract regeneration has NOT run. All listed cases are
        covered except stale eligibility, which is prevented structurally
        rather than by a concurrency test.
  - [ ] Complete source audit and reconciliation before any real session import.
        Not started. No session data has been imported.

- [ ] Phase 5 - Release evidence and cleanup
  - [ ] Verify the full migration chain on representative PostgreSQL data and
        retain diagnostics, rollback/restore notes, and environment revisions.
        Partially done. The chain applies to head on an empty database, the
        provider migrations downgrade and re-upgrade, and the identity backfill
        is rehearsed on seeded rows. Not done on representative production-scale
        data, and no environment revision has been recorded because no target
        environment has been inspected.
  - [ ] Confirm generated contracts and web flows for every API phase.
        NOT DONE. No contract regeneration has run on this branch and every web
        check is against mocked endpoints.
  - [ ] Verify no production or test path still treats a PersonId as a ProviderId.
        Provider paths are clear: the three Person-based panel use cases and the
        provider methods on `PersonEntity` are removed. But see finding 1, a
        `PersonId` carrying a user id in the clinical case module, which is why
        this item should not be closed from provider code alone.
  - [ ] Update module documentation and record deployed behaviour separately
        from this design's remaining unchecked tasks. Nothing is deployed.

## Remaining risks and ownership

There are no unanswered design choices blocking the phases above. The decisions
are adopted under the user's delegated authority; implementation remains the
responsibility of the agent taking each phase, which must record its evidence.

- Target database contents and applied revisions remain unverified. The deploying
  agent must run preflight and retain actionable rejection diagnostics.
- Historical practitioner identities and delivery context need source
  reconciliation. The import operator must resolve evidence gaps; the importer
  must not guess.
- External SAD content and a panel-cull deadline remain unavailable facts. The
  documentation owner should record them if supplied, without inventing either.
- Supplier contracts and shared cross-tenant practitioner identity are deferred
  capabilities requiring their own design if the product owner requests them.
- Alias reconciliation is API-only. No review queue is exposed in the UI, which
  is consistent with keeping import tooling backend-owned, but it means an
  operator cannot resolve an ambiguous name without direct API calls. A product
  owner should decide whether that is acceptable for the first import.
- Member and service identity for the historical extract have no owner. See
  finding 2. Until they do, applying a staged batch imports nothing.
- The privileged attribution-correction path from decision 2 is not built. Only
  the rejection half is implemented.
- `apps/api/alembic` is outside the ruff gate, which scopes to `app tests
  scripts`. 65 pre-existing migrations would need reformatting to bring it in.
  Deliberately deferred rather than done in a release that is already extending
  the chain; the migrations that matter here are covered by tests that execute
  them.
