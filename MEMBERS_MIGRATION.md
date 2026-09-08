# Members module migration

This is the working handoff log for the persons → members migration. It is
intentionally untracked while the migration is in progress. Future agents
should update this file as each phase is completed; completed items are struck
through rather than removed.

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
| `Staff_ID` | `employer_member_id` | Use the stable company-supplied identifier; do not create a second `external_id`. |
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
| `Job Title`, `Job Classification`, `Skill`, `Department`, `Unit`, `Contract type` | — | Exclude: these are employment-history/workforce fields, not wellness member data. |
| `Column2`, `Column3` | — | Ignore. |

~~The import phase must include preview, duplicate review, client resolution,
row-level errors, and an explicit decision about whether `Staff_ID` or `Staff
Number` is the client's canonical member ID.~~ The importer now provides all of
those safeguards. `Staff_ID` is the required canonical identifier; rows with
placeholders or blanks remain errors and `Staff Number` is retained only as
reference data, never used as an identity fallback.

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
