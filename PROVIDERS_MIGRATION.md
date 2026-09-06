# Provider module migration

Decision record and implementation handoff for the provider module. Updated
2026-09-06 against commit `3b4daed`. Track this document in git. Update it with
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
and non-compete clauses, with `eap_v2` predating the providers table. This review
has not rerun that database audit. Other environments remain unverified; no
migration may assume they are empty.

The earlier baseline records 1,538 API tests collected and 486 web tests passed
on 2026-09-06. Collection is not a passing backend suite.

The focused provider review ran 47 tests successfully and skipped two PostgreSQL
migration tests because `MEMBER_TEST_DATABASE_URL` was unset. The selected files
were `test_provider_audit.py`, `test_provider_mapper.py`,
`test_provider_profile.py`, `test_panel_use_cases.py`, `test_session_members.py`,
`test_audit_coverage.py`, and `test_provider_reference_migration.py`.

Direct API reproductions with mocked persistence established:

- Provider create returned 201 with zero audit-handler calls.
- General provider patch changed tier without a reason, returned 200, and made
  zero audit-handler calls.
- A Viewer changed a tier through the actual app's panel route and received 200.

The migration rejection fixture creates one invalid outreach row and no clause,
but expects `1 non-compete and 1 outreach`. Replaying its preflight query against
an in-memory SQLite fixture produced `0 non-compete and 1 outreach`. This checks
the rejection message, not PostgreSQL DDL or migration-chain correctness.

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
  - [ ] Locate the referenced external SAD and record any conflicts.
  - [ ] Record target-environment counts and migration state before deployment.

- [ ] Phase 1 - Repair the boundary and mutation controls
  - [x] ~~Add ProviderEntity, mapper and typed repository; remove the session
        Row shim and legacy lookup.~~ Implemented in `3b4daed`.
  - [x] ~~Retype non-compete references and add clause/outreach existence FKs.~~
        Implemented in `f6a8c0e2b4d6`; target application unverified.
  - [x] ~~Emit tier and panel events and call the audit handler.~~ Handler calls
        tested; this does not establish auditing of all provider mutations.
  - [ ] Enforce composite tenant constraints and validate outreach assignments.
  - [ ] Restrict lifecycle commands to Admins and reject Viewer writes.
  - [ ] Add creation/update audit events, partial PATCH and protected-field rejection.
  - [ ] Replace Person-based panel operations and port behavioural coverage.
  - [ ] Enforce the practitioner eligibility gate on current booking/outreach
        writes; extend that same policy with affiliations in phase 3.
  - [ ] Correct the stale `providers.ts` module comment.
  - [ ] Correct the migration rejection fixture and require PostgreSQL CI coverage.
  - [ ] Prove forbidden writes do not save, audits persist with changes, and
        failures roll back both state and audit records.
  - [ ] Record contract changes and target migration rehearsal separately.

- [ ] Phase 2 - Independent practitioner identity and usable directory
  - [ ] Add owned name/contact fields, nullable account link and link uniqueness.
  - [ ] Add Admin-only account linking/unlinking and preserve directory visibility
        after account removal.
  - [ ] Add create/edit forms, server-side filters, search, pagination and totals.
  - [x] ~~Use a human-readable detail heading.~~ Existing display name/email heading.
  - [ ] Regenerate contracts; test creation without a login and account-link
        authorization, cross-tenant rejection, and full-dataset filtering.

- [ ] Phase 3 - Organisations, affiliations and session attribution
  - [ ] Add organisation entity, mapper, repository, CRUD and management UI.
  - [ ] Add dated affiliations, pair-overlap constraints and composite references.
  - [ ] Add explicit session delivery context and immutable affiliation attribution.
  - [ ] Extend the booking policy with organisation approval and affiliation validity.
  - [ ] Validate reassignment/corrections and retain referenced history.
  - [ ] Regenerate contracts; prove concurrent affiliations work and moving firms
        does not reattribute old sessions; preserve unknown historical context.

- [ ] Phase 4 - Typed profile, eligibility and import readiness
  - [ ] Promote structured credential/profile fields with validating migrations.
  - [ ] Add global specialties, tenant-owned links and platform write controls.
  - [ ] Add source-scoped aliases with explicit reconciliation and ambiguity handling.
  - [ ] Move the shared booking/outreach policy to the typed profile fields.
  - [ ] Add future-booking review on suspension and eligibility rechecks on changes.
  - [ ] Add Admin-only historical staging/import with provenance and idempotency.
  - [ ] Regenerate contracts; test expiry boundaries, organisation suspension,
        stale eligibility, imports for currently inactive practitioners, rejection
        of future bookings through import, and missing/ambiguous source data.
  - [ ] Complete source audit and reconciliation before any real session import.

- [ ] Phase 5 - Release evidence and cleanup
  - [ ] Verify the full migration chain on representative PostgreSQL data and
        retain diagnostics, rollback/restore notes, and environment revisions.
  - [ ] Confirm generated contracts and web flows for every API phase.
  - [ ] Verify no production or test path still treats a PersonId as a ProviderId.
  - [ ] Update module documentation and record deployed behaviour separately
        from this design's remaining unchecked tasks.

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
