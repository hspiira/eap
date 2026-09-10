# Members module migration

This is the working handoff log for the persons → members migration. It is
tracked in git. Future agents should update this file as each phase is
completed; completed items are struck through rather than removed.

## Product boundary

Members are people covered by a client’s wellness programme:

- client employees
- beneficiaries/dependants
- optional portal-account linkage
- wellness eligibility and service history

Providers/counsellors belong in the provider organisation/practitioner domain.
Tenant/platform staff belong in Users & Invitations. Members do not track
employment history; only optional client-supplied identifiers belong here.

## Decisions

- ~~Keep `/persons` as a compatibility API/UI path during the first migration.~~
  Removed after the provider and callback cutovers.
- Use “Members” in product-facing labels and documentation.
- Do not require a User account for every member.
- Keep provider and platform-staff records out of the member workflows.
- Prefer relational member/client and member/beneficiary relationships over
  embedded role-specific employment/provider JSON.
- Keep the first member form roster-focused: required name/member ID,
  relationship, optional profile/contact data, and roster lifecycle data.
  Coverage belongs to the client/company.
- `employer_member_id` is the client/company's member identifier. Do not add a
  second generic `external_id`; government identifiers such as NIN or passport
  need a separate restricted identity model and policy.
- DOB, gender, and phone are now optional member profile fields. Next-of-kin is
  a separate restricted contact workflow so a member can have more than one
  contact without embedding sensitive data in the roster row.

## Phases

- [x] ~~Phase 0 — Baseline, rules, and migration tracking document~~
  - [x] ~~Read repository/agent rules.~~
  - [x] ~~Record current clients/users/providers/persons architecture.~~
  - [x] ~~Capture baseline tests and working-tree state.~~
    - Backend eligible-member unit tests: 21 passed.
    - Frontend suite: 47 files / 400 tests passed (existing React act/query warnings remain).
    - Existing working-tree changes were preserved.
- [x] ~~Phase 1 — Backend member domain and persistence boundary~~
  - [x] ~~Define member-focused schemas and API semantics.~~ Added `/members` list, detail, create, update, lifecycle, and export contracts.
  - [x] ~~Decouple member identity from mandatory User accounts.~~ Member creation uses the existing `eligible_members` aggregate and does not create a `User`.
  - [x] ~~Add tenant-safe member/client/beneficiary validation.~~ Client and primary-employee relationships are checked within the current tenant and client.
  - [x] ~~Remove provider/platform-staff creation from member commands.~~ The new member commands contain neither provider nor tenant-staff creation; `/persons` remains compatibility-only.
- [x] ~~Phase 2 — Backend member workflows~~
  - [x] ~~Create/read/update member and beneficiary workflows.~~ Beneficiaries are linked to an employee member and cannot cross clients.
  - [x] ~~Add eligibility representation.~~ Member status is roster lifecycle state; company/programme coverage remains outside the member record and clinical continuity remains behind the existing pseudonymous link.
  - [x] ~~Define duplicate review and merge as one safe workflow.~~ Administrators explicitly select exactly two records and choose the survivor. The atomic merge requires the same tenant, client and relationship context, transfers beneficiaries, contacts, sessions, account linkage and clinical references, preserves the survivor's clinical identity, audits both records, and never proposes matches from names or email.
  - [x] ~~Add member export and selected-ID export.~~ CSV export supports current filters or selected member IDs.
  - [x] ~~Add core member profile fields.~~ DOB, gender, and phone are persisted and returned by the canonical member API; future government identity fields remain intentionally separate.
  - [x] ~~Add next-of-kin contacts.~~ Contacts are one-to-many, tenant/member scoped, audited, require a name plus phone or email, and support one primary contact.
- [x] ~~Phase 3 — Frontend Members list and detail~~
  - [x] ~~Connect client detail roster, counts, links, and contextual creation to Members.~~ One shared query supplies the preview and total; the existing `tab=staff` URL remains compatible. Viewers can read without a create action, and loading/errors are distinct from an empty roster.
  - [x] ~~Replace client-list legacy employee counts with canonical member counts.~~ The Employees column counts employee members across roster statuses; the `staff_count` API field remains compatible. Saving a member invalidates the client list.
  - [x] ~~Delete the unused legacy staff summary card and its design inventory entry.~~
  - [x] ~~Allow direct month/year selection in the shared date picker.~~ Existing dates open at their saved month; tests cover dates 3, 5, 10, 20 and 30 years ago and future dates.
  - [x] ~~Rename visible Persons language to Members.~~ Primary navigation now points to `/members`; the former `/persons` route is retired.
  - [x] ~~Remove provider/platform-staff options from member UI.~~ The member form has only employee/beneficiary relationships and optional contact data.
  - [x] ~~Add member profile, eligibility, and beneficiary views.~~ The detail view shows both beneficiary directions.
  - [x] ~~Add account access and service history only with real data and authorization workflows.~~ The account panel explicitly links one existing tenant User and grants no permissions; only administrators can change it. Service history reads canonical member sessions and requires Clinical scope.
  - [x] ~~Add DOB, gender, and phone to member forms/details.~~ Values are optional and use the shared date picker.
  - [x] ~~Add next-of-kin management to member detail.~~ Authorized users can add, edit, mark primary, and remove contacts; viewers retain read-only access.
  - [x] ~~Add working selection and export.~~ Duplicate/merge remains deferred until it has an identity policy and an atomic backend contract.
- [x] ~~Phase 4 — Provider and staff boundaries~~
  - [x] ~~Resolve legacy Person-to-Member identity mapping and service-session linkage.~~ The user confirmed there is no legacy data. Replaced the bridge plan with an empty-table cutover: session subjects reference Members and migration refuses any populated service-session table. No name/email matching, bridge table or compatibility reads were added.
  - [x] ~~Verify counsellors use provider organisation/practitioner workflows.~~ Providers now have independent persistence and the Providers workspace no longer calls `/persons`.
  - [x] ~~Verify tenant staff use Users & Invitations.~~ User detail no longer fetches or displays a legacy Person profile; roles and access scopes remain in the Users workflow.
  - [x] ~~Remove obsolete person-module references from docs and navigation.~~ Deleted the client/staff Persons list UI and its stale tests; Persons is removed from navigation and API registration.
- [x] ~~Phase 5 — Contracts, docs, tests, and cleanup~~
  - [x] ~~Regenerate OpenAPI and frontend contracts.~~ OpenAPI and TypeScript artifacts were regenerated after adding the next-of-kin endpoints.
  - [x] ~~Add backend authorization, tenant-isolation, and eligibility tests.~~ Route, domain, and focused persistence coverage is included.
  - [x] ~~Add merge tests with the reviewed merge workflow.~~ Route tests cover explicit selection, admin authorization, client isolation, self-merge rejection, transfer results and audit events; repository invariants are enforced under row locks.
  - [x] ~~Add frontend list/form/detail/export tests.~~ Focused Members interaction coverage is included.
  - [x] ~~Update module READMEs and code-quality docs.~~ Member boundary documentation is being added; legacy person references remain only where compatibility is intentional.
  - [x] ~~Decide when `/persons` compatibility aliases can be removed.~~ Removed once providers were independent and care callbacks referenced Members.

## Implementation notes

CSV import is preview-first and accepts only an explicit, stable `Staff_ID` /
`employer_member_id`; `Staff Number` is never used as an identity fallback.
Rows are tenant/client resolved, duplicate checked, and either all committed or
returned with row-level errors. The sample's `IDI-` placeholders are rejected.

Update this log after each phase. Include migrations, compatibility decisions,
tests run, and any follow-up work that remains.

Current handoff status:

- OpenAPI and TypeScript artifacts regenerate reproducibly.
- The beneficiary projection adds a tenant/client-scoped
  `GET /members/{id}/beneficiaries` endpoint; no schema migration was needed
    because it uses the existing eligible-member relationship.
- Latest verification, 2026-09-06: focused member route/domain tests 65 passed;
  local PostgreSQL member and migration suites 17 passed in isolated schemas.
  No application tables were touched by those tests.
- Frontend suite: 58 files / 455 tests passed, including client-to-member integration, member filters/pagination, persisted contract attachment reload and direct date-picker month/year navigation. Existing React test warnings remain.
- Frontend TypeScript, ESLint, Prettier, and production build passed using the
  installed project binaries.
- `lint-imports` passes with 3 contracts kept and 0 broken; the member repository
  composition-root edge is explicitly grandfathered with the existing dependency pattern.
- The optional-field cleanup now follows the client form convention: blank
  values become `null`, optional labels are carried by section/field help, and
  optional emails are validated in the schema.
- `ClientPicker` accepts a resolved selected client, so edit/contextual-create
  forms show the client name only; the client code remains internal to lookup.
- Member profile fields are optional by design: `date_of_birth`, `gender`, and
  `phone` are now part of the canonical API and form. `employer_member_id`
  remains the company-supplied external member ID.
- Next-of-kin is stored in `member_next_of_kin` rather than `eligible_members`.
  Migration `g1h3j5l7n9p1` adds the table. Reads are tenant-scoped and writes
  require a non-viewer user; create/update/delete operations are audited.
- Duplicate review is manual and explicit: the UI makes no similarity claims.
  The atomic contract rejects cross-tenant/client/relationship merges and
  conflicting account or primary-contact ownership.
- Migration `c9e1a3b5d7f9` adds the nullable one-to-one Member/User link and is
  applied locally. Existing members are preserved; the link is admin-managed
  and does not grant roles or scopes.

## Clean cutover and client-detail redesign, 2026-09-06

- [x] ~~Move service-session subjects to Members end to end.~~ Database FK,
  entities, repository, API schemas/filters, form picker, detail/list/history
  links, audit event consumers, test fixtures and generated contracts now use
  `member_id`. `provider_id` still references a service-provider Person.
- [x] ~~Verify the empty-table migration and tenant-safe session creation.~~
  `a7c9e1f3b5d7` is applied locally after confirming zero sessions. Its upgrade
  and downgrade refuse populated tables. No application data was deleted.
  Removed only the obsolete demo session rows from `seed_data.json`; these are
  recoverable from Git and cannot safely be seeded without canonical Members.
- [x] ~~Update historical import mappings to canonical member IDs.~~ The
  validator resolves company member codes within the canonical client ID;
  identical codes in different clients cannot match accidentally. The CLI
  now provides the validation core used by the preview-first roster importer.
- [x] ~~Redesign the client Members tab.~~ Name-first roster table, contact
  details, relationship/status filters, debounced search, server pagination,
  loading/error/empty states and contextual member creation.
- [x] ~~Simplify overview and retain setup state.~~ Deleted the duplicate
  calculated health score. Completed setup disappears from Overview but
  remains available in Setup and is derived from persisted client records on
  reload. Contacts and aliases have dedicated homes; Overview shows actions
  and current relationship activity. At a glance uses real counts and dated
  contract milestones rather than record IDs.
- [x] ~~Group Services by contract.~~ Each term shows its own assignments,
  service names, assignment statuses and notes, including empty contracts.
  All contract/assignment pages are loaded, not just the overview preview.
- [x] ~~Add contract attachments.~~ Optional upload/download on client
  Contracts and contract detail, using the existing Document model. Files are
  linked to the contract and client on the server. Tenant checks, viewer write
  restrictions, size/type checks, private downloads and failed-save cleanup
  are tested. Docker services have persistent attachment volumes. See
  `apps/api/docs/CONTRACT_ATTACHMENTS.md` for storage/deployment requirements.
- [x] ~~Keep Activity and rename Usage to Sessions.~~ Activity remains the
  relationship log. The renamed Sessions tab retains the existing contract
  service-delivery ledger; it is not a new clinical-history workflow. Existing
  `tab=utilisation` links still work.
- [x] ~~Regenerate contracts and verify the redesign.~~ OpenAPI/TypeScript,
  TypeScript checking, ESLint, production build and all three architecture
  contracts pass. Browser visual QA was not available. The build reports an
  existing Vite-builder version warning; no dependency changes were made.

The remaining retirement slices are now complete:

- [x] ~~CSV roster import~~ — `POST /members/import` previews by default and
  commits only with `dry_run=false`; strict stable-ID validation, duplicate
  review, tenant/client resolution, and audit events are included.
- [x] ~~Independent provider/practitioner persistence~~ — providers have their
  own table, repository, `/providers` API, frontend endpoint, and service-session
  foreign key. The clean cutover refuses populated sessions.
- [x] ~~Care-callback subject migration~~ — outreach records use `member_id`
  and an `eligible_members` FK; enrolment/search/detail links use Members.
- [x] ~~Final `/persons` API removal~~ — the legacy Persons router is no longer
  registered. Provider/session/callback paths no longer require its API.

## Roster import atomicity (2026-09-07)

Decision: a confirmed roster import commits one row at a time, not the file as
a unit. `POST /members/import` still previews the whole file; the confirmation
now replays the previewed rows through `POST /members/import/commit` in slices
of 25, and that route re-checks and commits each row on its own.

Reason: the single-transaction import undid every accepted row when a later row
failed, and gave the UI nothing to report until the whole file finished. Row
atomicity makes a partial import a legitimate, reportable outcome.

Assumptions and consequences:

- The preview response now carries each row's parsed values (`values`), because
  the commit step replays rows rather than re-uploading the file. The commit
  route trusts none of it: client resolution, in-file duplicate detection,
  existing-member detection and `MemberCreate` validation all run again server
  side before a row is written.
- `MemberRowChecker` and `MemberRowImporter` in `app/api/services/member_import.py`
  are the single implementation used by both routes, so preview and commit
  cannot judge a row differently.
- A file with invalid rows can now be imported for its valid rows. Previously
  any invalid row blocked the whole file. Existing members are still never
  overwritten; a duplicate is reported and skipped.
- Verified: 1577 API unit tests pass, including new coverage for per-row commit,
  a failing row that does not stop the run, duplicate refusal, and a company
  code outside the tenant. Browser verification was not run.

Open finding, not fixed here: `ClientImportDialog` and `POST /clients/import`
still commit a whole file as one unit for files under 5 MB, with no per-row
outcome; larger files go through the queued job instead. The client importer
should get the same row-at-a-time treatment. Only the import table's font size
was corrected in that dialog.

## Coverage visibility in the member API (2026-09-08)

Decision: the product owner reopened the closed decision that coverage is
invisible in the member API. `MemberResponse` now returns `coverage_start`,
`coverage_end`, and `is_currently_eligible`, the last computed by the existing
domain method `EligibleMember.is_currently_eligible()`. Coverage stays
read-only in the member API: `MemberCreate` and `MemberUpdate` accept no
coverage dates, which remain set at the client/programme level and by
`terminate()`.

Consequence, verified against the dev database on 2026-09-08: of 3,305
members, none has a `coverage_start` and one has a `coverage_end`, so
`is_currently_eligible` currently reduces to "status is Active". The domain
method treats a missing bound as open, so this is correct, not a defect.

The same change made `staff_number` searchable in the member list (3,301 of
3,305 dev members carry one) and added `GET /members/stats` for the roster
summary strip, returning status and account-link counts for the list's filter
set.

## Roster import reference

The sample roster at `/Users/piira/Downloads/persons.csv` is handled by the
preview-first importer. Its safe mapping is:

| Sample column | Member field | Decision |
| --- | --- | --- |
| `Company Code` | client lookup | Required tenant-scoped client code; `Company` is informational and is not used as an identity fallback. |
| `Staff_ID` | ~~`employer_member_id`~~ `import_source_id` | ~~Use the stable company-supplied identifier; do not create a second `external_id`.~~ Superseded 2026-09-09 by `b881e8b5`: `employer_member_id` is now always server-issued from the per-client sequence, for every relation. `Staff_ID` maps to the separate `import_source_id` column instead, which exists exactly for this purpose ("do not create a second `external_id`" is honoured by reusing this field, not `employer_member_id`). |
| `Name of Employee` | `display_label` | Required member name. |
| `Email Address` | `work_email` | Normalize `N/A` and blanks to null. |
| `Personal Email` | `personal_email` | Optional personal contact; normalize `N/A` and blanks to null. |
| `Date of Birth` | `date_of_birth` | Optional ISO date (`YYYY-MM-DD`). |
| `Gender` | `gender` | Map only supported controlled values; review unknown values. |
| `Phone` | `phone` | Optional contact number. |
| `National ID` | `national_id` | Optional identification field. |
| `Passport Number` | `passport_number` | Optional identification field. |
| `Status` | member status | Map supported lifecycle values; review non-member statuses. |
| `Staff Number` | import matching aid | Preserve for matching only unless the client confirms it is the canonical ID. |
| `Job Title`, `Job Classification`, `Skill`, `Department`, `Unit`, `Contract type` | `employment.*` | ~~Exclude: these are employment-history/workforce fields, not wellness member data.~~ Reopened 2026-09-10, see below. Captured as optional free text. |
| `Column2`, `Column3` | — | Ignore. |

~~The import phase must include preview, duplicate review, client resolution,
row-level errors, and an explicit decision about whether `Staff_ID` or `Staff
Number` is the client's canonical member ID.~~ The importer now provides all of
those safeguards. `Staff_ID` is the required canonical identifier; rows with
placeholders or blanks remain errors and `Staff Number` is retained only as
reference data, never used as an identity fallback.

## Decision reopened: employment details are captured (2026-09-10)

The 2026-09-08 mapping table excluded `Job Title`, `Job Classification`,
`Skill`, `Department`, `Unit` and `Contract type` as workforce fields rather
than member data. The owner reopened that decision. They are now captured, all
optional, and accepted through the roster import for any client.

### What the source data shows

Measured from `/Users/piira/Downloads/persons.csv`, 4,945 rows:

| Column | Populated | Distinct |
| --- | --- | --- |
| Job Title | 375 (7.6%) | 192 |
| Job Classification | 323 (6.5%) | 11 |
| Skill | 329 (6.7%) | 6 |
| Department | 329 (6.7%) | 18 |
| Unit | 329 (6.7%) | 53 |
| Contract type | 329 (6.7%) | 2 (Permanent, FTC) |

Every populated row belongs to client `IM`, covering 100% of that client's
rows. No other employer supplies any of them. `Job Classification` carries a
literal `#N/A` in 17 rows.

### Decisions

1. **Free text, not reference tables.** The vocabularies are the employer's own
   org chart (`SME Banking`, `Kampala Road branch`, `Executive Office`), not
   shared platform taxonomy. A per-client reference table would hold one
   client's values and, per `docs/gaps/TAXONOMY_MANAGEMENT_GAP.md`, could only
   be maintained by script. Revisit if a second client supplies them.
2. **Grouped in a value object.** `EmploymentDetails`
   (`apps/api/app/domain/value_objects/staffing.py`) holds the six fields,
   flattened to six nullable `VARCHAR(255)` columns on `eligible_members` and
   `member_import_rows`. `update_roster_details` already took 14 keyword
   arguments; six more flat parameters would have made it unreadable.
3. **Named `employment_type`, not `contract_type`.** The source column is the
   employee's contract of employment (Permanent, FTC). `contract_type` would
   read as the client's commercial contract, which is a different aggregate
   with its own `PricingModel`.
4. **No eligibility meaning.** No domain rule reads these fields; they are
   record and segmentation only. Pinned by
   `tests/unit/domain/test_member_employment_details.py`.
5. **`#N/A` normalises to null.** Added to the placeholder set the parser
   already applied to `N/A`, `NA`, `null` and `-`, so the 17 dirty rows store
   nothing rather than the literal. Not an import error: the owner chose to
   accept these columns for any client without new validation failures.

### Not done, and deliberately

**These fields must stay out of report aggregation until PRIV-01 has
small-cell suppression.** `docs/reviews/MODULES_REPAIR_PLAN.md:230` records
that aggregates return values without it. Group sizes for client `IM`:

| Field | Groups | Median size | Groups under 5 |
| --- | --- | --- | --- |
| Department | 18 | 7 | 6 (20 members) |
| Unit | 53 | 5 | 24 (62 members) |

Nearly half of `Unit`'s groups have fewer than five members, so a utilisation
report broken down by unit would disclose counselling attendance at a cell
size that identifies the person. Capture is safe; segmentation is not yet.

~~The member import preview dialog does not show the new columns.~~ Done
2026-09-10 in a follow-up. `MemberImportRowResponse` returns the same nested
`employment` block as `MemberResponse`, and the preview table renders one
column each, but only when the staged batch carries at least one value: 4,616
of the sample roster's 4,945 rows have none, so unconditional columns would
add six empty ones to every import. The supported-fields copy previously said
"Other workforce columns are ignored", which had become false.

## Bug found and fixed: a stuck Staged batch, and a wrong-row restage (2026-09-10)

Discovered against the local dev database while testing the follow-ups above:
a batch staged and never applied or abandoned blocked every future restage of
that exact file with a 409, and the dialog had no way to discard it. Fixed by
adding a "Discard the stuck batch and retry" action (`MemberImportDialog.tsx`),
backed by the existing `POST /members/import/{id}/abandon` endpoint. The 409's
`details` now carries the conflicting `batch_id` so the client can act on it;
`batch_id` joins `resource_type`/`resource_id` in `test_error_wire_shapes.py`'s
diagnostic-field exemption, since a cuid cannot itself read as a sentence.

Using that new discard action immediately surfaced a second, more serious bug:
restaging the same file a second time raised a raw 500
(`UniqueViolationError` on `uq_member_import_batches_tenant_file_hash`)
instead of the clean 409. `MemberImportRepositoryImpl.find_batch_by_hash`
queried by `(tenant_id, file_hash)` alone, with no status filter and no
`ORDER BY`; once a hash belongs to more than one historical batch (routine
now that a batch can be discarded and restaged), `session.scalar()` can return
an arbitrary one. It returned the abandoned batch, so the route's "already
staged" check saw a non-Staged batch, fell through to `INSERT`, and the
partial unique index (`WHERE status = 'Staged'`) rejected it as unhandled.
Fixed by filtering the query to `status = 'Staged'` directly, matching what
the index actually protects. Reproduced and pinned in
`tests/unit/infrastructure/test_member_import_migration.py`
(`test_find_batch_by_hash_picks_the_staged_one_when_others_share_it`): fails
against the old query (`b1`, the abandoned batch), passes against the fixed
one (`b2`, the staged one).

**Not fixed here, and worth a look:** `session_imports.py` and
`practitioner_imports.py` call the identical unfiltered
`find_batch_by_hash` shape on their own repositories
(`provider_network_repository.py:408`, `practitioner_import_repository.py:37`)
against the same kind of partial-unique-index schema. Neither has a reported
failure, and discarding a batch is a newer, member-only affordance that makes
the multiple-batches-per-hash case routine rather than rare, so they were left
alone rather than expanding this fix into an unrelated module. Whoever adds a
discard/retry action to either flow should apply the same status filter first.

A third bug surfaced testing the same discard/retry path end to end: once a
restage succeeded, the preview never populated any rows. `MemberImportDialog`'s
`fetchAllRows` pages `GET /members/import/{id}/rows` at `limit=200`, but the
route declared `pagination(default_limit=50)` with no `max_limit` override, so
it inherits the shared default cap of 100 and 422s on the very first request.
This has been broken since the route was introduced
(`bb8b631f`): every unit test mocks `imports.list_rows` directly, bypassing
FastAPI's query validation, so nothing ever exercised the real HTTP contract
between this endpoint and its only caller. Fixed by passing
`max_limit=200`, matching the precedent already set by
`care_callbacks.py:671`. Added `test_list_import_rows_accepts_the_200_page_size_the_dialog_uses`,
the route's first HTTP-level test; confirmed it fails on the old signature
with the same 422 the live server produced.

A fourth bug reached production directly: staging a real roster raised a raw
500, `UniqueViolationError` on `uq_member_import_rows_tenant_replay`, for a
Staff_ID already held by a row in an earlier batch nobody had applied or
abandoned. `member_import_repository` already exposes `find_row_by_replay_key`
(used by `member_import_repository.py:181`), and `session_import_staging.py:166`
and `practitioner_import_staging.py:107` both call it before inserting a row,
exactly to classify this case as a graceful Duplicate rather than let the
database catch it. `stage_member_import` never called it — an incomplete port
from the `bb8b631f` precedent, invisible for the same reason as the previous
two: nothing staged an overlapping roster in a unit test. `MemberRowChecker`
now takes the import repository and performs this lookup, but only while
staging (`file_hash` passed); the apply-time re-check omits it, since the row
being re-checked already holds the exact key it would be checking against. A
collision gets a deferred key, `duplicate:{batch}:{key}` via
`app.shared.utils.replay_key.deferred_key`, the same shape session_import
already uses, so persisting the Duplicate classification cannot itself
collide. Reproduced at the route level in
`test_stage_flags_a_row_still_claimed_by_another_unresolved_batch`: fails
(row comes back New) without the fix, passes (Duplicate, named batch and row)
with it.

## Fifth defect: a dependant could never import without their own Staff_ID

`member_csv.py`'s row-level parse check required every row to carry a Staff_ID,
with no exception for `Relation`. A real roster's dependants (spouse, child,
etc.) are identified by `Primary Staff ID`, not their own Staff_ID — the
manual "Add member" form has never required one for a beneficiary, and
`MemberCreate.import_source_id` is documented as optional for anyone. The CSV
path was the one place still treating it as mandatory for every row, which
meant every dependant lacking their own Staff_ID was permanently `Invalid`
("Stable Staff_ID is required") regardless of whether `Primary Staff ID`
correctly resolved to an already-imported employee.

Decision (confirmed 2026-09-10): a row whose `Relation` names anything other
than Employee (blank defaults to Employee, matching `_member_create`'s own
default) is exempt from needing its own Staff_ID, but a dirty one (still
ending in `-`) is still flagged regardless of relation — that is bad data
either way, not an absent one. In exchange, a dependant now must carry a
resolvable `Primary Staff ID`: `_primary_member_id` previously treated a blank
one as "no primary, fine" for every relation, which was correct for an
employee but would have let an orphaned dependant in with no link to anyone.
It now rejects a beneficiary row with neither ID: "Primary Staff ID is
required for a beneficiary."

Two more call sites assumed a Staff_ID was never blank and needed the same
exemption to avoid a *new* defect from this one's fix:
- `_claim_staff_id`'s intra-file duplicate guard keyed on `(client_id,
  Staff_ID or "")`; two dependants with no Staff_ID in the same file would
  have collided with each other on the shared `""` key. It now only claims a
  key when Staff_ID is present.
- `_already_enrolled` looked up `find_by_import_source_id(..., Staff_ID or
  "")`; harmless against a real Postgres column (`NULL` never equals `''`,
  so nothing already stored can match), but skipped explicitly anyway to
  avoid depending on that column's NULL-vs-empty-string semantics.

Pinned by five tests: two in `test_member_csv.py` (blank exempt for a
dependant, dirty still flagged regardless of relation) and three at the route
level (dependant with a resolving primary imports as `New`; dependant with
neither id is `Invalid`; two id-less dependants in one file both come back
`New`, not `Duplicate` of each other).

### Verification

Migration `q6s8u0w2y4a6`, applied to the dev database and reversed, both
confirmed against `information_schema`. Merge revision `p5r7t9v1x3z5` first
resolves a pre-existing two-head divergence (`e3f5g7h9j1k3` and
`n3q5s7u9w1y3`, both branched from `d8x1y3z5a7c9` on 2026-09-10) that made
`alembic upgrade head` ambiguous.

The real roster parses to the counts above, `job_classification` dropping to
306 as the 17 `#N/A` rows normalise to null, and the six columns raise no new
row issues: all 1,653 remain the pre-existing missing-`Staff_ID` errors.

2,168 API unit tests and 757 web tests pass. Nothing is deployed.

## Open finding: next-of-kin relationship lookup returns a coroutine (2026-09-08)

Found while verifying the members page redesign, in work that was uncommitted
in the shared tree at the time and belongs to another agent. Not fixed here,
because fixing another agent's in-flight file would collide with their work.

`NextOfKinRelationshipRepository.get_by_code`
(`apps/api/app/infrastructure/repositories/next_of_kin_relationship_repository.py:59`)
passes an unawaited coroutine to `_to_entity`, so `_assert_known_relationship`
(`apps/api/app/api/routes/members.py:240`) raises
`AttributeError: 'coroutine' object has no attribute 'id'` and both next-of-kin
write routes answer 500.

Reproduced by `uv run pytest tests/ -k member` in the working tree:
`test_contact_mutations_commit_with_audit[post-/members/m1/next-of-kin-payload0-CREATE]`
and the `patch` case fail. The same selection passes on committed state
(169 passed, 20 skipped) in a clean worktree at HEAD, which is what places the
defect in the uncommitted change rather than in the members module.

Fix: await the result before mapping it. Whoever owns the next-of-kin
relationship taxonomy should confirm no other method in that repository has
the same shape.

## Design: member import staging batch (2026-09-10)

Product owner request: give member roster import a persisted staging table so
an import attempt can be audited and duplicates tracked consistently, matching
the pattern already used by practitioner and session import. Design only;
nothing in this section has been implemented yet.

### Why today's design does not meet that ask

`POST /members/import` (`apps/api/app/api/routes/members.py:745-821`) and
`POST /members/import/commit` (`:824-850`) are stateless server-side. Preview
parses and validates the upload in memory and returns every row's full parsed
values (`MemberImportRowValues`, `member_schemas.py:231-253`) to the browser;
nothing is written to the database unless `dry_run=false`. Commit does not
look anything up by an id, it takes those same values back from the request
body (`MemberImportCommitRow.values`, `:283-289`) and re-validates from
scratch. There is no batch/job id anywhere in either schema. Confirmed by
direct inspection of both handlers and by grepping `apps/api/alembic/versions`
and `apps/api/app/infrastructure/models` for an import-batch table scoped to
members: none exists. The only member-import migration is
`d8x1y3z5a7c9_add_eligible_member_import_source_id.py`, which adds the
`import_source_id` column and its per-client unique index to `eligible_members`
directly, not a staging table.

Consequence: the state of an import run lives in the browser tab between
preview and commit, and there is no audit trail of who staged or applied a
roster, unlike practitioner and session import.

### Two capabilities already in place that this redesign must not regress

- **Row atomicity.** "Roster import atomicity (2026-09-07)" above is a
  deliberate, already-reasoned decision: a confirmed import commits one row at
  a time because a single-transaction import "undid every accepted row when a
  later row failed, and gave the UI nothing to report until the whole file
  finished." Any apply step in the new design must keep writing rows
  one at a time and must not roll the batch back on one row's failure.
- **Per-row decision before commit.** `docs/gaps/IMPORT_REVIEW_UI_GAP.md`
  records that member import already has real in-UI review: a person can
  override each row's Import/Skip decision before the batch runs
  (`MemberImportDialog.tsx`, `decisionsFor`/`updateDecision`/`ImportRow`).
  Session import, the flow this design mirrors, has no equivalent per-row
  decision, only batch-level apply/abandon
  (`docs/gaps/IMPORT_REVIEW_UI_GAP.md:19-24`). The new member design keeps the
  member-import capability rather than regressing to the session-import
  shape; see "Deviation from precedent" below.

### Precedent mirrored: session import staging

Session import (`apps/api/app/api/routes/session_imports.py`,
`apps/api/app/application/services/session_import_staging.py`,
`apps/api/app/application/use_cases/apply_session_import.py`) is the closest
existing flow: an external roster is matched against existing entities and can
be staged once, reviewed, and applied later. Its shape:

- `POST /session-imports` stages the whole file in one request: hash the
  upload (`file_hash`), reject only if a batch with the same tenant+hash is
  still `Staged` (409), persist one `SessionImportBatchModel` row, then persist
  one `SessionImportRowModel` per row with a computed `outcome` and a
  `replay_key` (`{prefix}:{source_record_key}` if present, else
  `file:{hash}:row:{n}`) that is unique per tenant so the same source record
  cannot be staged twice.
- `GET /session-imports/{id}/rows` is a paginated, filterable read of the
  persisted rows. Nothing about a row can be changed from here.
- `POST /session-imports/{id}/apply` takes no body, only `batch_id`. It loads
  persisted rows page by page, writes only the ones whose outcome is
  `Accepted` and that are not already imported, marks each row's
  `imported_session_id` with one update per row immediately (not a bulk
  update), and only flips the batch to `Applied` after every row has been
  processed.
- `POST /session-imports/{id}/abandon` records a reason and moves the batch to
  `Abandoned`.

Two things about the batch table are worth calling out because they were bugs
in this exact precedent, not just design notes: the original migration
(`a2n1o0r2k4s6_provider_network_tables.py:177-181`) gave
`session_import_batches` a plain `UniqueConstraint(tenant_id, file_hash)`,
which meant an applied or abandoned batch permanently blocked ever restaging
that file again. Two follow-up migrations
(`h3b5d7f9j1l3_abandoned_batches_free_their_file_hash.py`,
`j5d7f9h1k3m5_only_an_undecided_batch_holds_its_file_hash.py`) narrowed this to
a partial unique index, `WHERE status = 'Staged'`, so only a batch still
awaiting a decision holds the hash. The member design should start with the
partial index directly rather than repeat the two-migration fix.

### Proposed schema

Two new tables, `member_import_batches` and `member_import_rows`, same shape
as `session_import_batches`/`session_import_rows`
(`apps/api/app/infrastructure/models/session_import_model.py:34-140`):

`member_import_batches`

| Column | Type | Notes |
| --- | --- | --- |
| `id` | cuid PK | |
| `tenant_id` | FK `tenants.id` | |
| `file_name` | string(500) | |
| `file_hash` | string(128), indexed | sha256 of the upload |
| `row_count` | int, default 0 | |
| `status` | `ImportBatchStatus` | `Staged` / `Applied` / `Abandoned`, see below |
| `staged_by` | string(25) | user id |
| `applied_by` | string(25), nullable | |
| `applied_at` | timestamptz, nullable | |
| `notes` | text, nullable | abandon reason |

Constraints: `UniqueConstraint(tenant_id, id)`; partial unique index on
`(tenant_id, file_hash)` `WHERE status = 'Staged'`, adopting the corrected
session-import behaviour directly.

`member_import_rows`

| Column | Type | Notes |
| --- | --- | --- |
| `id` | cuid PK | |
| `tenant_id`, `batch_id` | composite FK to batch, `ondelete=CASCADE` | |
| `row_number` | int | |
| `replay_key` | string(500), unique per tenant | see open decision below |
| `client_code`, `import_source_id`, `staff_number`, `display_label`, `work_email`, `personal_email`, `gender`, `date_of_birth`, `phone`, `national_id`, `passport_number`, `status`, `relation`, `primary_import_source_id` | same fields as `MemberImportRowValues` (`member_schemas.py:231-253`) | the persisted row replaces the client-resent `values` payload |
| `outcome` | `MemberImportRowOutcome` | `New` / `Duplicate` / `Invalid` / `Skipped`, mirrors today's `RowCheck.state` (`member_import.py:144-208`) |
| `decision` | `import` / `skip` | new column, not present in session import; carries the per-row override the UI already exposes |
| `message` | text, nullable | validation/duplicate message, one string, matching today's shape rather than adopting the practitioner-import `ImportReasonCode` taxonomy, which member import has no use for yet |
| `imported_member_id` | string(25), nullable, FK `eligible_members.id` `ondelete=SET NULL` | set by apply, mirrors `imported_session_id` |

Constraints: `UniqueConstraint(batch_id, row_number)`;
`UniqueConstraint(tenant_id, replay_key)`; composite FK to the batch.

### New domain enum

`MemberImportRowOutcome(str, Enum)`: `NEW`, `DUPLICATE`, `INVALID`, `SKIPPED`.

Reusing `ImportBatchStatus` from `app/domain/enums/provider_network.py:59-64`
as-is is a name smell: that module is documented as "Enums for the provider
network" (`provider_network.py:1`), and importing it from the members domain
couples members to a provider-network module for a three-value enum that is
already generic. Recommendation, not yet decided: move `ImportBatchStatus` to
a neutral module (for example `app/domain/enums/imports.py`) shared by
practitioner, session, and member import, and update the two existing
importers. This is a larger blast radius than the member feature alone
(`graft callers ImportBatchStatus` should be run before touching it) and
should be confirmed before implementation, not assumed.

### Deviation from precedent: per-row decision endpoint

Session import's row list is read-only; there is no route that changes a row
after staging. Member import needs one, to preserve the Import/Skip override
`docs/gaps/IMPORT_REVIEW_UI_GAP.md` already credits it with. Proposed:
`PATCH /members/import/{batch_id}/rows/{row_id}` with body `{decision: "import" | "skip"}`,
tenant-scoped, rejecting rows whose outcome is not `New` (a duplicate or
invalid row cannot be queued regardless of decision, matching today's
`isQueued` guard). This route has no equivalent in session or practitioner
import; it exists because member import's UI capability is ahead of theirs,
not because the precedent was followed loosely.

### Proposed API surface

| Method/path | Replaces | Behaviour |
| --- | --- | --- |
| `POST /members/import` | current `POST /members/import` (preview) | Stage: hash, reject only if same tenant+hash batch is still `Staged`, persist batch + one row per CSV row with a computed outcome. Returns `MemberImportBatchResponse`. |
| `GET /members/import/{batch_id}` | — | Batch status, row_count, outcome counts. |
| `GET /members/import/{batch_id}/rows` | — | Paginated, filterable by outcome/decision. Shipped with only an `outcome` filter (`members.py:871`); no `decision` query param exists. Low impact: `MemberImportDialog.tsx`'s `fetchAllRows` pages through every row unfiltered and filters client-side, so nothing depends on the missing param, but a future consumer reading only this table would expect one. |
| `PATCH /members/import/{batch_id}/rows/{row_id}` | — | New. Set a row's decision. |
| `POST /members/import/{batch_id}/apply` | current `POST /members/import/commit` | No body but `batch_id`. Applies rows with `decision=import` and `outcome=New` one at a time, immediately persisting `imported_member_id` per row (row atomicity preserved), then marks the batch `Applied`. |
| `POST /members/import/{batch_id}/abandon` | — | Records a reason, marks `Abandoned`, frees the file hash per the corrected partial index. |

`MemberRowChecker.check` (`member_import.py:144-208`) is reused unchanged for
computing a row's outcome at stage time; the difference is that the result is
persisted once instead of being recomputed from client-resent values at every
commit slice.

### Open decision: replay key for a blank Staff ID

This is the question the earlier "no Staff ID" discussion deferred to this
design. Today `import_source_id` is mandatory at parse time
(`member_csv.py:88-91`, "Stable Staff_ID is required") specifically because it
is the only dedup/re-import key (`member_import.py:167`, `176-178`); a blank
value cannot safely disambiguate two different people in the same client. A
persisted `replay_key` does not remove that problem by itself, it only
changes what a blank Staff ID's key looks like:

- `key:{client_id}:{import_source_id}` when Staff ID is present, stable
  across re-imports, matching today's behaviour.
- `file:{file_hash}:row:{row_number}` when Staff ID is absent (mirroring
  session import's own fallback, `session_import_staging.py:448-451`) makes
  every row's key unique **within one file**, which fixes the in-file
  collision bug described earlier, but gives no cross-file identity: the same
  person without a Staff ID re-imported next month gets a new row and,
  eventually, a new member record. That is the "no dedup guarantee" tradeoff
  from the earlier options, not a new option.

Whether that tradeoff is acceptable, or whether a blank Staff ID should
instead require a second field (National ID, email) to stand in as the key,
is a product decision. I have not decided it here; whoever owns the roster
data-quality policy should confirm before this is implemented, and the
decision should be recorded in this file once made, per the "Decisions"
convention at the top of this document.

### Frontend consequence, not yet designed in detail

`MemberImportDialog.tsx` currently holds every row's full values in browser
state and resends them in slices of 25 to commit
(`BATCH_SIZE`, `importRows`). Under the new design it would instead: stage
once, fetch rows a page at a time, PATCH a row's decision when the user
changes the select, and call apply with only the batch id. This is a
rewrite of the dialog's data flow, not a small patch, and is out of scope for
this design note; it should be scoped separately once the backend shape above
is confirmed.

### Decisions made, 2026-09-10

- Replay key: use both, as designed above. `key:{client_id}:{import_source_id}`
  when Staff ID is present; `file:{file_hash}:row:{row_number}` fallback when
  absent. Cross-file re-identification of a person with no Staff ID is
  accepted as a known limitation, not solved by this change.
- `ImportBatchStatus` (`app/domain/enums/provider_network.py:59-64`) is reused
  as-is for member import rather than relocated. Decision: it is treated as a
  generic import-lifecycle enum despite living in a provider-network-named
  module; not moved.
- Cutover is direct: the old stateless `POST /members/import` and
  `POST /members/import/commit` are replaced, not kept alongside the new
  contract, consistent with this document's existing cutover precedent
  (Phase 4).

### Implementation, 2026-09-10

Backend:

- New tables `member_import_batches`/`member_import_rows`
  (`alembic/versions/n3q5s7u9w1y3_member_import_staging.py`), domain entities
  `MemberImportBatchEntity`/`MemberImportRowEntity`
  (`app/domain/entities/member_import.py`), repository interface/impl
  (`app/domain/repositories/member_import_repository.py`,
  `app/infrastructure/repositories/member_import_repository.py`), and mapper
  (`app/infrastructure/mappers/member_import_mapper.py`).
- `POST /members/import` now stages (hash, persist batch + one row per CSV
  row, `MemberRowChecker.check` reused unchanged) instead of previewing.
  `GET /members/import/{id}`, `GET /members/import/{id}/rows`,
  `PATCH /members/import/{id}/rows/{row_id}` (the new per-row decision
  endpoint, no equivalent in session import), `POST /members/import/{id}/apply`,
  and `POST /members/import/{id}/abandon` round out the surface
  (`app/api/routes/members.py`). The old `POST /members/import/commit` is
  gone; the cutover is direct, per the recorded decision.
- Apply keeps the existing row-atomicity guarantee: `_apply_row` commits or
  rolls back per row, re-running `MemberRowChecker.check` fresh against the
  roster as it now stands rather than trusting the row's staged outcome. A
  row that fails or is no longer importable is marked `Failed` with a message
  and the loop continues; only after every row is processed does the batch
  itself commit as `Applied`. This is a deliberate divergence from
  `ApplyImportBatchUseCase` in session import, which commits the whole apply
  as one transaction; members cannot use that shape without reintroducing the
  bug the 2026-09-07 atomicity fix closed.
- `ImportBatchStatus` is reused from `app.domain.enums.provider_network` as
  decided, not relocated. A new `MemberImportRowOutcome` enum
  (`New`/`Duplicate`/`Invalid`/`Failed`) lives in `app.domain.enums.person`
  alongside the other member enums. There is no `Skipped` outcome value: Skip
  is the row's mutable `decision` field, not a classification, since a New
  row can be toggled between Import and Skip after staging.
- Replay key: `key:{client_id}:{import_source_id}` when Staff ID is present,
  `file:{file_hash}:row:{row_number}` otherwise, exactly as decided. Cross-file
  re-identification of a person with no Staff ID remains unsolved by this
  change; every such re-import still creates a new row.
- `MemberImportRowEntity.mark_imported`, `mark_failed`, and `set_decision` are
  accepted silent mutators (`tests/unit/domain/test_audit_coverage.py`,
  `KNOWN_SILENT_MUTATORS` 93 -> 95): the batch already emits
  `MemberImportBatchApplied`/`Abandoned` with actor and counts, and each row
  carries its own `imported_member_id` or failure message as persisted detail,
  the same reasoning already recorded there for
  `SessionImportRowEntity.mark_imported`.
- `pyproject.toml`'s import-linter config grandfathers
  `app.api.dependencies.clinical -> app.infrastructure.repositories.member_import_repository`
  alongside the existing composition-root edges; `lint-imports` still passes
  3 kept, 0 broken.

Frontend: `MemberImportDialog.tsx` and `api/endpoints/members.ts` were
rewritten for the new stage/rows/decision/apply/abandon contract. One UX
trade-off, not a defect: apply is now a single request that returns only once
the whole batch is processed, so the old per-slice live progress bar is gone.
This matches session import's own `apply` shape (also one all-or-nothing
call with no client-visible per-row progress); the old member-specific
slice-by-slice progress was a feature of the stateless design being replaced,
not something the new design tries to preserve.

Also included in this pass, at the user's request and independent of the
staging redesign: a "refresh from disk" control on the CSV picker using the
File System Access API where the browser supports it (Chromium only; other
browsers keep the plain file input with no refresh button).

Verified:

- Backend: `ruff check`/`ruff format` clean on every touched file;
  `lint-imports` 3 kept, 0 broken; `uv run pytest tests/unit` 2145 passed, 16
  skipped (pre-existing, unrelated to this change).
- Migration: verified against a real local PostgreSQL instance in an isolated
  schema (`tests/unit/infrastructure/test_member_import_migration.py`, 5
  passed) — table/column/FK shape, the partial unique index (a Staged batch
  blocks a same-hash restage, an Applied one does not), the per-tenant replay
  key uniqueness constraint, and a clean downgrade.
- Frontend: `tsc --noEmit` clean, `eslint` clean, `prettier --check` clean,
  full `vitest run` 746 passed (91 files) including 9 new/updated
  `membersApi` endpoint tests.

Not verified: no browser session exercised the rewritten `MemberImportDialog`
end to end; only the API layer underneath it and its unit tests were run.

Discoveries recorded, not fixed here (out of scope for this change):

- `alembic heads` shows two heads on this branch,
  `n3q5s7u9w1y3` (this change, chained off `d8x1y3z5a7c9`) and a pre-existing
  `e3f5g7h9j1k3` unrelated to members. The second head predates this work.
  Whoever integrates branches will need an `alembic merge` before a combined
  `upgrade head` (singular) will succeed; `upgrade heads` (plural) works today.
- Session import's own `stage_import` route calls `audit_change(batch, ...)`
  immediately after staging, but nothing ever appends a
  `SessionImportBatchStaged` event to the batch (the event class exists,
  `grep -rn "SessionImportBatchStaged("` finds no call site), so that audit
  call is a silent no-op today. Member import does not repeat this: `stage_member_import`
  calls `batch.mark_staged(at=now)` before persisting, so the equivalent
  `MemberImportBatchStaged` event actually fires.
