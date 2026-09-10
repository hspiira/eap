# Provider frontend and contract handoff

Frontend record for the provider migration. Use with
`docs/migrations/PROVIDERS_MIGRATION.md`, which holds the design decisions, and
`docs/handoffs/PROVIDERS_EXECUTION.md`, which holds ownership and the dependency
gates. Only the provider-core task updates the shared migration checklist; this
document covers the frontend and generated contracts only.

Implemented, tested against mocks, verified against a real backend, and
deployed are separate claims and are separated below.

## Ownership and branch

- Role: frontend, generated contracts, integrated user-flow verification.
- Branch: `codex/providers-agent3-frontend`.
- Worktree: `/Users/piira/Developer/sandbox/eap/wt-agent3`.
- Base commit: `e672b6f`. Generated contracts come from the integrated
  branch head named by the integration owner.
- Owned paths: `apps/web/`, `apps/web/src/routeTree.gen.ts`,
  `apps/web/src/api/generated/schema.ts`, `apps/api/schema/openapi.json`.
- No backend source is edited here. Backend defects are reported to their owner
  with a reproduction rather than worked around in the browser.

## Contract gate

Both contracts were published and confirmed. Four divergences from the
repository's conventions were raised against the practitioner contract with
parameter counts taken from `apps/api/schema/openapi.json`, and all four were
accepted:

| Raised | Evidence | Outcome |
| --- | --- | --- |
| `search`, not `q` | `search` appears on 13 paths, `q` on none | accepted |
| `sort_by` + `sort_desc`, not a `-` prefixed `sort` | `sort_by`/`sort_desc` on 12 paths each, `sort` on none | accepted |
| `page`, not `offset` | `page` on 22 paths, `offset` on 1, that 1 being `/providers` | accepted |
| Flat or nested `PATCH` body | `provider.replace_profile` at `apps/api/app/api/routes/providers.py:141` is the wholesale replacement decision 8 forbids | resolved: bodies are flat and `provider_profile` is not writable |

The organisations task moved its routes off the `/providers` prefix, which the
provider-core task owns, after that overlap was raised. Its four prefixes are
`/provider-organisations`, `/provider-affiliations`, `/provider-specialties`
and `/session-imports`, and the endpoint modules here are named to match.

Two contract additions were requested and accepted: `is_active` plus
`approval_status` as independent organisation fields, so a suspended supplier
and a deactivated record are distinguishable; and `organisation_name`,
`organisation_is_active` and `organisation_approval_status` joined onto the
affiliation response, so a booking selector can label and pre-qualify its
options without a request per affiliation.

Affiliation validity and accreditation expiry both resolve in Africa/Kampala,
settled between the core and organisations tasks. No timezone arithmetic is
reimplemented in the browser: the form submits what the user typed and displays
what the server decides.

## Delivered

Against the agreed contracts. Commits are on the branch above.

- `7d914be` Error handling. `ApiError` keeps the server's `details` list
  alongside the collapsed per-field map, so a rejection carrying several
  reasons under one field no longer loses all but the last. `useApiForm`
  surfaces a rejection whose fields the form does not have, instead of
  returning early and showing nothing. `apiClient.delete` accepts a body.
- `e60b9b6` Practitioner identity and directory: owned name, optional and
  clearable contact details, creation with no account, server-side
  search/filter/sort/paging with a full-dataset total, four Admin-only
  reason-carrying lifecycle commands, Admin-only account link and unlink, and
  organisation and dated-affiliation management.
- `92da242` Delivery context: explicit direct or organisation choice with no
  default, affiliation options scoped to the scheduled date, honest display of
  unknown and unrecorded context, attribution read from the session's own
  organisation, attribution excluded from general session edit, and every
  server eligibility reason listed.

## Checks run

From `apps/web`, on Node 26.7.0, pnpm 10.9.0, against the integrated head.

| Check | Command | Result |
| --- | --- | --- |
| Types | `pnpm typecheck` | pass |
| Lint | `pnpm lint` | pass |
| Tests | `pnpm test` | 70 files, 536 tests, all passed |
| Build | `pnpm build` | pass |
| Contract drift | `pnpm contracts:check` | pass, exit 0: regeneration is a no-op |

Baseline before this work was 486 tests. The added tests cover: naming a
practitioner with no contact email and no account; server-side filters and sort
reaching the API rather than a fetched page; paging past the first page while
the total stays the full matching count; a viewer seeing no create action; a
general edit sending exactly the five ordinary keys and no lifecycle key; no
tier control on edit; clearing optional contacts to null; email validation; a
lifecycle command refusing to send without a reason and sending the reason when
given; a non-admin seeing no lifecycle or account controls; an absent
accreditation expiry reading as not on record; a practitioner staying visible
when their linked account cannot be read; end-exclusive interval labelling;
open-ended affiliations; concurrent affiliations with different firms; an
unapproved firm warned about; ended affiliations included; only the interval end
editable, with a reason; the overlap rejection shown with its conflicting
period; a booking refusing to submit without an explicit delivery context;
direct delivery sent with a null affiliation; every eligibility reason listed;
unknown, missing, direct and organisation attribution each rendered distinctly;
specialties read from the catalogue links rather than free text; a link to a
retired specialty kept visible and marked retired; retired and already-linked
entries absent from the picker; a specialty linked by catalogue id; and a viewer
given no specialty controls.

These are component tests against mocked endpoints. They establish the UI's own
behaviour, not the API's.

## Verified against a running API

Separate from the mocked tests above. A dedicated database, `eap_agent3_web`,
was created for this so no other worker's fixtures were touched.

- The full Alembic chain applied to an empty PostgreSQL database and reported a
  single head, `a1p3d0d2e4f6`.
- The API was started against that database and driven over HTTP with the same
  requests and in the same order the web app issues them. 51 of 54 behavioural
  checks passed; the three that did not are recorded below and two of them are
  findings rather than frontend faults.

Confirmed against the real API, not a mock:

- A practitioner is created with no account and no contact details, and comes
  back off-panel and unaccredited rather than active.
- General `PATCH` rejects `tier` and `specialties` with 422, and clears
  `email` and `phone` when sent explicit nulls.
- Each lifecycle command applies with a reason; a Viewer receives 403 for both
  a lifecycle command and an ordinary edit.
- The directory returns `total` 25 while serving 10 rows, page 3 differs from
  page 1, and `region`, `search` and `has_account` filter server-side.
- An organisation starts `Pending` and active, refuses `approval_status` on
  `PATCH`, and approves through its command.
- An affiliation reports the firm's name and current approval, rejects an
  overlapping period with 409, and permits a concurrent affiliation with a
  different firm.
- `valid_at=2026-06-30` includes an interval ending `2026-07-01`, and
  `valid_at=2026-07-01` excludes it. The end-exclusive rule holds at the
  boundary.
- A live booking rejects `Unknown` delivery with 422, and refuses direct
  delivery that cites an affiliation with `affiliation_not_permitted_for_direct`.
- **The delivering organisation is present on every read, not only on create.**
  Checked on the create response, the detail route, the list route and the
  by-practitioner route. This was the defect the integration owner asked to have
  confirmed.
- Suspending a practitioner refuses a new booking with `PROVIDER_NOT_ELIGIBLE`
  and `panel_not_active`, and leaves the completed session's organisation
  attribution untouched.
- Moving an affiliation's end to a date that still covers its attributed
  session is accepted with a reason.
- Account linking is Admin-only, a second practitioner linking the same account
  gets 409, and unlinking leaves the practitioner readable.

The eligibility rejection body was captured from the running API and matches
what the booking form renders: every reason arrives as its own `details` entry
under `field: "eligibility"` with a stable `code`.

Not covered by this run: the specialty link flow, because the global catalogue
is empty on a fresh database and the vocabulary is seeded separately. The
catalogue endpoint itself answers 200.

## Not yet verified

- The verification above drove the API directly over HTTP with the requests the
  web app issues. It did not drive the browser, so it establishes that the
  contract behaves as the UI expects, not that the rendered screens behave
  correctly end to end. The component tests cover the rendering side.
- Nothing has been checked against a deployed environment. The database used was
  created empty for this purpose; target-environment contents and applied
  revisions remain unverified, as `docs/migrations/PROVIDERS_MIGRATION.md`
  records.
- The specialty catalogue is empty on a fresh database, so linking a specialty
  is covered only by mocked tests.

## Findings from the running API, and how they closed

Three behaviours differed from what was published. None was a frontend fault.
All three are now fixed, and the second turned out to be the shared cause of
five separate errors across two modules.

1. **The affiliation overlap `details` array was not field errors.** The API
   returned `[{"field": "field", "message": "valid_from", "code": null}, ...]`,
   a key/value bag in which `field` was the literal string `"field"` and the
   message was the field's name. Fixed by the organisations task in `46dbba7`:
   one entry keyed by the real field, carrying the same sentence as the
   top-level message. The affiliation form uses it, so the overlap message now
   appears under the date input the server names, with a banner fallback when
   no usable field is given.

2. **The same defect was in the shared exception serialiser.**
   `EvexiaException.to_api_response` maps each `details` key to a field name
   and its value to that field's message, and `ValidationException.__init__`
   built `details = {"field": field}`. So **every** `ValidationException`
   raised with a field produced
   `{"field": "field", "message": "<the field's name>", "code": null}`. Three
   live call sites, one of them the Unknown-delivery rejection in this
   module's own booking path, and one the client-code validation on an
   unrelated form. Fixed by the core task in `5ef385f`: the field error now
   names the input, and `EvexiaException` takes an explicit `field_errors`
   list for the two things a details dict cannot express, a machine-readable
   code and several entries against one field. The eligibility error stopped
   needing its own `to_api_response` override as a result.

   Two consequences for this module. The Unknown-delivery message now attaches
   to the booking form's delivery-context select rather than to a field that
   does not exist, which is covered by a test asserting the message renders
   inside that field. And the shared form hook's fallback, which routes an
   unattachable error to the form-level banner, is no longer load-bearing for
   these errors; it stays because it is the right behaviour for any error the
   form cannot place.

   The organisations task audited its own modules after this and found two
   more instances of the same shape, an attribution conflict carrying a Python
   list repr and an import conflict carrying a bare id, fixed in `a99e8a9`.
   Neither is in a path this module currently reaches.

   The provenance is worth separating, because two different mistakes share
   one shape: the class defect predates this migration and is the core task's;
   the call-site misuses were each owned by whoever wrote them. Finding the
   class defect came from reading the serialiser to check the organisation
   task's diagnosis, not from the frontend.

3. **A whitespace-only reason returned 400 with no `details`.** Traced to
   `_require_reason` in the provider entity raising a `DomainError` after the
   schema had let the whitespace through, so the practitioner lifecycle
   commands answered 400 with nothing to attach to the reason input. Fixed by
   the core task at the schema: reason fields strip before checking, so `""`,
   `"   "` and `"\t"` all return the same 422 against `reason`, and the reason
   is stored stripped. The domain check stays as the invariant.

   This is why the regenerated contract shows `minLength: 1` giving way to
   `maxLength: 500` on the reason fields. Eight `minLength` constraints went
   and six `maxLength` arrived, because two of the eight fields already had
   `maxLength`. Every reason field checked individually: none lost all
   constraints. The contract cannot express strip-then-validate, so the
   disappearance of `minLength` reads as a loosening and is the opposite:
   `minLength: 1` accepted `"   "` and the server did not.

## Carried items, with owners

1. `ProviderAffiliationResponse` carries no practitioner name, so the
   organisation detail page resolves each one with a cached detail query.
   Requested of the organisations task; a `provider_display_name` would remove
   the per-row request.
2. Historical import and alias review have no UI, deliberately. See below.
3. Linking a specialty is covered by mocked tests only, because the global
   catalogue is platform-seeded and nothing seeds it yet, so a fresh database
   has an empty catalogue. The endpoint itself answers 200.

Closed since the first version of this document: `PanelStatus` now carries
`Pending` and the `SessionCreateBody` extension is deleted, both against the
generated contract rather than ahead of it; `ProviderApprovalStatus` was
renamed `OrganisationApprovalStatus`, which is what the API calls it, and
under the wrong name the bidirectional enum check had been silently skipping
it; and all three running-API findings above are fixed.

## Settled: one write path for specialties

The practitioner contract originally made `specialties: string[]` a writable
key on general `PATCH /providers/{id}`, while the organisations contract made
the tenant's catalogue links the write path. Both cannot be how a specialty is
recorded, and the string list was raised as the wrong one:

- A `string[]` carries no catalogue id, and decision 5 states that name
  normalization is not proof of identity.
- Decision 5 has tenants select active entries "through their own provider
  links".
- Selecting a retired entry is rejected on the link path and unchecked on the
  PATCH path, so the PATCH path bypassed a rule the other enforces.
- A whole-list replace of strings cannot express keeping an existing link to a
  retired specialty, which decision 5 requires.

The organisations owner supplied the deciding citation: decision 6 enumerates
what becomes a typed profile field (tier, region, panel status, accreditation
status, authority and expiry) and what stays as text or JSON (bio, licence
details). Specialties are in neither list, so they are governed by decision 5,
not preserved by decision 6.

Resolved in favour of the link model. The core owner removed `specialties` from
create and from the general PATCH editable set and added it to the protected
fields, so sending it now returns 422 naming the link endpoints. The
practitioner form no longer sends it, and the practitioner page reads
specialties from `GET /provider-specialties/links?provider_id=`, adds them by
catalogue id, and shows a link to a retired entry marked retired rather than
hiding it.

`provider_profile.specialties` on the response is still the stored legacy JSON
list and is not yet a projection of the links; it becomes one when the typed
profile migration lands in phase 4. It is therefore not displayed anywhere:
showing both it and the links would put two sources on one screen that can
disagree.

One consequence, owned by the organisations task and recorded here because it
bears on this decision: whichever migration removes the free-text field must
not discard values silently. Decision 6 requires migrations to preserve every
existing credential field and to reject invalid data with actionable row
identifiers, and free text will not match catalogue codes. Their local audit
found zero providers carrying specialty values, and other environments are
unverified.

## Deliberately not built

The alias review queue (`GET /provider-aliases`, with Admin-only resolve and
reject) and the historical import endpoints (`POST /session-imports` and its
rows and apply) are implemented server-side but have no web surface, and none
is planned here. The execution prompt keeps that tooling backend-owned and
forbids inventing an import dashboard, and
`POST /session-imports/{id}/apply` returns 501 today because the historical
write path is unbuilt. Rendering controls that appear to work would be
dishonest.

If that queue is later wanted, it needs its own scope rather than a table:
unmapped, ambiguous and rejected must stay visibly distinct outcomes,
`candidate_provider_ids` must read as candidates rather than as a suggestion to
accept, and resolution must stay a deliberate per-row Admin action. There is no
automatic-resolution endpoint, by design, and decision 5 forbids one.

## Backend defects found and reported

1. `GET /providers` declared only `tenant_id`, `limit` and `offset`, so the
   `page` and `search` the web app sent were dropped by FastAPI. The directory
   had no reachable second page and `ProviderPicker`'s search was inert.
   Reported to and fixed by the core task; the directory now filters, sorts and
   pages server-side, confirmed against the running API.
2. `apps/web/src/routes/service-sessions/$sessionId.tsx` resolved a session's
   practitioner through that same ignored `search`, requesting one arbitrary
   row and matching nothing, so no practitioner was shown. Frontend, mine,
   fixed by reading `GET /providers/{id}` directly.
3. `ProviderRegion` offered "Kampala" and "Remote / Telehealth", neither of
   which the API accepts, and omitted three real regions. Frontend, mine, fixed
   against `UgandaRegion` in the generated contract.
4. Affiliation creation was posting to
   `/provider-organisations/{id}/affiliations`, a path that does not exist: the
   route is `POST /provider-affiliations` with the organisation as a query
   parameter. It would have returned 404. Frontend, mine, found by generating
   the contract and checking every provider route the web app calls against it
   by path, method and request body. The other nineteen matched.

## Out of scope here

Backend routes, schemas, migrations and their tests; the shared migration
checklist; supplier contracting; non-compete expansion; and any real data
import. Nothing here deploys, pushes, imports real data, or merges to the
default branch.
