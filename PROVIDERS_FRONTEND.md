# Provider frontend and contract handoff

Frontend record for the provider migration. Use with `PROVIDERS_MIGRATION.md`,
which holds the design decisions, and `PROVIDERS_EXECUTION.md`, which holds
ownership and the dependency gates. Only the provider-core task updates the
shared migration checklist; this document covers the frontend and generated
contracts only.

Implemented, tested against mocks, verified against a real backend, and
deployed are separate claims and are separated below.

## Ownership and branch

- Role: frontend, generated contracts, integrated user-flow verification.
- Branch: `codex/providers-agent3-frontend`.
- Worktree: `/Users/piira/Developer/sandbox/eap/wt-agent3`.
- Base commit: `e672b6f`.
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

From `apps/web` at `92da242`, on Node 26.7.0, pnpm 10.9.0.

| Check | Command | Result |
| --- | --- | --- |
| Types | `pnpm typecheck` | pass |
| Lint | `pnpm lint` | pass |
| Tests | `pnpm test` | 70 files, 528 tests, all passed |
| Build | `pnpm build` | pass; regenerated `routeTree.gen.ts` |

Baseline before this work was 486 tests. The 42 added tests cover: naming a
practitioner with no contact email and no account; server-side filters and sort
reaching the API rather than a fetched page; paging past the first page while
the total stays the full matching count; a viewer seeing no create action; a
general edit sending exactly the six ordinary keys and no lifecycle key; no
tier control on edit; clearing optional contacts to null; email validation; a
lifecycle command refusing to send without a reason and sending the reason when
given; a non-admin seeing no lifecycle or account controls; an absent
accreditation expiry reading as not on record; a practitioner staying visible
when their linked account cannot be read; end-exclusive interval labelling;
open-ended affiliations; concurrent affiliations with different firms; an
unapproved firm warned about; ended affiliations included; only the interval end
editable; the overlap rejection shown with its conflicting period; a booking
refusing to submit without an explicit delivery context; direct delivery sent
with a null affiliation; every eligibility reason listed; and unknown, missing,
direct and organisation attribution each rendered distinctly; specialties
read from the catalogue links rather than free text; a link to a retired
specialty kept visible and marked retired; retired and already-linked entries
absent from the picker; a specialty linked by catalogue id; and a viewer given
no specialty controls.

These are component tests against mocked endpoints. They establish the UI's own
behaviour. They do not establish that any backend route exists or behaves this
way.

## Not yet verified

- No generated contract has been regenerated or committed. `pnpm contracts:sync`
  runs only against the backend commit the integration owner names, at the
  directory, attribution and review gates. `apps/api/schema/openapi.json` and
  `apps/web/src/api/generated/schema.ts` are untouched on this branch.
- No flow has been exercised against a running API. Every route this work calls
  except `GET /providers`, `GET /providers/{id}` and the non-compete and session
  routes is part of the contract still being implemented.
- The user-flow list in the execution prompt (creation without a login,
  clearable optional contacts, account permissions, lifecycle reasons, listing
  beyond the first 100 providers, multiple affiliations, explicit session
  attribution, suspended and ineligible booking errors) is covered by mocked
  component tests and is pending real integrated verification at the review
  gate.

## Carried items, with owners

1. `PanelStatus` is missing the agreed `Pending` member. `enums.contract.test.ts`
   compares this enum against `apps/api/schema/openapi.json` in both
   directions, so the value lands with the regenerated contract. Mine, at the
   directory gate.
2. `ServiceSessionCreate` does not carry `delivery_context` or
   `provider_affiliation_id`. `SessionCreateBody` in
   `apps/web/src/components/ServiceSessionFormSheet.tsx` declares them
   explicitly; delete the extension when the contract is regenerated. Mine, at
   the attribution gate.
3. `ProviderAffiliationResponse` carries no practitioner name, so the
   organisation detail page resolves each one with a cached detail query.
   Requested of the organisations task; a `provider_display_name` would remove
   the per-row request.
4. Affiliation interval corrections are rejected, not corrected, when the new
   interval would stop covering a completed session attributed to it. The core
   owner ruled a 409 with `affiliation_change_would_orphan_attribution` and the
   offending session ids in `details`, choosing decision 2's rejection half
   because the privileged correction operation does not exist yet. The
   interval-end form renders those reasons through the same list used for
   eligibility failures. The correction path stays a phase 3 item.
5. Historical import and alias review have no UI, deliberately. See the
   section below.

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

1. `GET /providers` at `apps/api/app/api/routes/providers.py:47` declares only
   `tenant_id`, `limit` and `offset`. Both `page` and `search`, which the web
   app sent, were dropped by FastAPI. Two consequences: the directory had no
   reachable second page, and `ProviderPicker`'s search box was inert. Reported
   to and confirmed by the core task; closed by the phase 2 listing contract.
2. `apps/web/src/routes/service-sessions/$sessionId.tsx:88` resolved a session's
   practitioner through that same ignored `search`, so it requested one
   arbitrary row and matched nothing, and the session detail page showed no
   practitioner. Frontend, mine, fixed in `92da242` by reading
   `GET /providers/{id}` directly.
3. `ProviderRegion` in `apps/web/src/types/enums.ts` offered "Kampala" and
   "Remote / Telehealth", neither of which the API accepts, and omitted three
   real regions. Harmless only because the filter ran in the browser; a
   server-side filter would have returned 422. Frontend, mine, fixed in
   `e60b9b6` against `UgandaRegion` in the generated contract.

## Out of scope here

Backend routes, schemas, migrations and their tests; the shared migration
checklist; supplier contracting; non-compete expansion; and any real data
import. Nothing here deploys, pushes, imports real data, or merges to the
default branch.
