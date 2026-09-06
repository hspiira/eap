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
- Base commit: `e672b6f`. Head at this writing: `92da242`.
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
| Tests | `pnpm test` | 69 files, 522 tests, all passed |
| Build | `pnpm build` | pass; regenerated `routeTree.gen.ts` |

Baseline before this work was 486 tests. The 36 added tests cover: naming a
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
direct and organisation attribution each rendered distinctly.

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
4. `PATCH /provider-affiliations/{id}` is the path assumed for editing an
   interval end. The organisations task specified the field but not the path.
   To confirm with them.
5. Decision 2 requires that changing affiliation dates must not silently
   invalidate completed attribution, and must either be rejected or carried in
   an explicit correction. No contract was published for that case. The
   interval-end form shows whatever the server returns, so a rejection is
   displayed, but the behaviour is unspecified. For the organisations and core
   tasks to settle, and for review to check.
6. Specialties have two incompatible write paths and the conflict is open. See
   the section below. Blocked, not mine to settle; the picker is unbuilt until
   it is.
7. Historical import and alias review have no UI, deliberately. See the
   section below.

## Open contract conflict: two write paths for specialties

The practitioner contract makes `specialties: string[]` an editable key on
`PATCH /providers/{id}`, a whole-list replace when present. The organisations
contract, committed at `9e3d6b1` on
`codex/providers-agent2-organisations`, makes the tenant's links the write
path: `POST /provider-specialties/links` with a `specialty_id`, and
`DELETE /provider-specialties/links/{link_id}`.

Both cannot be the way a specialty is recorded:

- A `string[]` carries no catalogue id. Writing `["Trauma"]` either stores free
  text or is matched by label, and decision 5 states plainly that name
  normalization is not proof of identity.
- Decision 5 says tenants select active entries "through their own provider
  links", which is the link model.
- Selecting a retired specialty is a 422 on the link path and unchecked on the
  PATCH path, so the PATCH path bypasses a rule the other enforces.
- A whole-list replace of strings cannot express keeping an existing link to a
  retired specialty, which decision 5 requires: retired entries stay on
  historical records but cannot be newly selected.

Position taken, and raised with both owners: `specialties` should come off the
general PATCH editable set and become read-only on the response, projected
from the links, leaving the link endpoints as the only write path. That is the
same shape already agreed for tier and accreditation, which are readable in
`provider_profile` and not writable through general edit.

This is a judgement about which of two published contracts is right, not a
citation that settles it. It is for the core and organisations owners to
decide, and for review to check. Until it is decided the practitioner form
still sends `specialties` as free text, because that is what the practitioner
contract asks for. That is left visibly incomplete on purpose rather than
resolved by picking a winner. The endpoint module and the link type are in
place, so implementing the outcome is one commit either way.

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
