# Track A: Correctness & Safety

Bugs and risks discovered during the SOLID/DRY review. These take priority over refactors:
several are ship-blocking. Line numbers are as of 2026-07-14 (`main` @ `066f1db`); re-verify with
the greps given in each ticket before starting.

---

## CQ-A01: Live-mode API paths (`/v1/*`) don't exist in the backend schema

**Severity:** 🔴 Critical · **Effort:** M · **Status:** ⬜ Todo · **Owner:** - · **PR:** -

**Problem.** The fixture-backed endpoint modules have "live" branches that call `/v1/...` paths.
The generated OpenAPI schema (`src/api/generated/schema.ts`) contains **zero** `/v1/*` paths,
real backend paths are `/engagements`, `/care-callback-campaigns`, `/survey-campaigns`,
`/diagnoses`, and there is no `/incidents` or `/questionnaires` at all. Sub-resources diverge too:
BE exposes `/engagements/{id}/hours`, `/activate`, `/deliver`, `/close`; FE calls
`/v1/engagements/{id}/time-entries` and `/v1/engagements/{id}/transition`. Every fixture→live
cutover 404s on first request.

**Evidence.**
- `src/api/endpoints/engagements.ts:46-112`
- `src/api/endpoints/incidents.ts:44-68`
- `src/api/endpoints/surveys.ts:40-69` (only module that documents its own drift, lines 5–14)
- `src/api/endpoints/care-callbacks.ts:51-111`
- `src/api/endpoints/questionnaires.ts:23-32`
- `src/api/endpoints/diagnoses.ts:66-78`
- Verify: `grep -c '"/v1/' src/api/generated/schema.ts` → 0.

**Recommended fix.**
1. Audit every `useFixture()` module's live branch against `schema.ts`; correct paths, params,
   and payload shapes.
2. Add a compile-time guard so this cannot recur: either adopt `openapi-fetch`
   (`client.GET('/engagements/{engagement_id}', …)`) or annotate path constants with
   `satisfies keyof paths` from the generated types.
3. Where the BE endpoint genuinely doesn't exist yet (incidents, questionnaires), say so in a
   module-header comment and make the live branch `throw new Error('not implemented on BE')`
   rather than silently 404ing.

**Acceptance criteria.**
- [ ] No literal URL in `src/api/endpoints/**` that is absent from generated `paths` (except
      documented not-on-BE modules).
- [ ] Compile-time path check in place (`openapi-fetch` or `satisfies keyof paths`).
- [ ] `pnpm contracts:check` passes.
- [ ] Manual smoke test of at least one migrated module with its fixture flag set to `'false'`.

---

## CQ-A02: Fixtures default ON; clinical business logic lives in fixture files

**Severity:** 🔴 Critical · **Effort:** M · **Status:** ⬜ Todo · **Owner:** - · **PR:** -

**Problem.** All 7 fixture toggles use `import.meta.env?.VITE_X_USE_FIXTURE !== 'false'`,
fixtures are ON unless every deployment sets 7 env vars explicitly. A missed var ships fake
clinical data (fixture campaigns, PHQ-9 outcomes) to production silently. Worse:
`evaluateCrisisRules` (the PHQ-9 item-9 self-harm crisis rule) is defined inside
`questionnaires-fixture.ts` and imported by a production route; `engagementsApi.allowedTransitions`
delegates to fixture code even in live mode. All fixture files are statically imported, so
~1,800 lines of seed data are always in the bundle.

**Evidence.**
- Toggles: `src/api/endpoints/{diagnoses:24, care-callbacks:34, engagements:35, incidents:29, pricing:19, questionnaires:17, surveys:30}.ts`, verified by grep.
- `src/api/endpoints/questionnaires-fixture.ts:191-200` (`evaluateCrisisRules`) imported by
  `src/routes/care-callbacks/worklist/$caseId.tsx:16`.
- `src/api/endpoints/engagements.ts:69-71` → `engagements-fixture.ts` (`allowedTransitions`).

**Recommended fix.**
1. Move domain rules out of fixtures: `src/lib/domain/crisis-rules.ts`
   (`evaluateCrisisRules`, `PHQ9_ITEM9_KEY`), `src/lib/domain/engagement-transitions.ts`
   (`ALLOWED_TRANSITIONS`). Fixtures import from `lib/domain`, never the reverse.
2. Flip the default: fixtures ON only when `import.meta.env.DEV` or the flag is explicitly
   `'true'`. Production builds default to live.
3. Lazy-load fixtures (`await import('./x-fixture')`) inside the fixture branch so live bundles
   tree-shake the seed data.

**Acceptance criteria.**
- [ ] `grep -r "from.*-fixture" src/routes src/components` → 0 matches.
- [ ] A production build (`pnpm build`) with no `VITE_*_USE_FIXTURE` vars set uses live endpoints
      (verify by inspecting one network call or the toggle unit test).
- [ ] Unit test covering the new toggle default (DEV → fixture, PROD → live).
- [ ] Bundle no longer contains fixture seed strings in prod build (spot-check `dist/`).

---

## CQ-A03: Query-key split-brain: current user cached under two different keys

**Severity:** 🟠 High · **Effort:** S · **Status:** ✅ Done · **Owner:** Claude · **PR:** `dc91516`, `4ef79b0`

> Done: `lib/query-keys.ts` created (`resourceKeys` factory + `queryKeys` map); the three
> `['user', userId]` sites now use `queryKeys.users.detail(id)` so
> `useEntityMutation({resource:'users'})` invalidation reaches them: split-brain fixed. Migrated
> ~27 hand-typed `detail`/`list` key literals across routes + form sheets to the factory;
> `extraInvalidations` widened to `QueryKey`. Three self-consistent paginated sub-keys left as-is.
> **Deferred (own ticket):** have `useEntityFormSheet` fully compose `useEntityMutation` (currently
> re-implements invalidation): tracked under CQ-C01's mutation-idiom convergence.

**Problem.** The current user is cached as `['user', userId]` in three places, while the same
record is cached as `['users', 'detail', id]` elsewhere. Any `useEntityMutation({ resource: 'users' })`
(role change, suspend) invalidates `['users', …]` but never `['user', userId]`, so
`useCanWrite` returns a stale answer until the 5-minute staleTime lapses. More broadly, ~40 call
sites hand-type raw key arrays instead of using the existing `entityListKey`/`entityDetailKey`
helpers from `lib/queries.ts`.

**Evidence.**
- `src/hooks/useCanWrite.ts:10`, `src/routes/me.tsx:87,99`, `src/components/DashboardHeader.tsx:184`
  (verified by grep: `['user', userId]`).
- Hand-typed keys: `src/routes/care-callbacks/$campaignId.tsx:51`,
  `src/routes/engagements/$engagementId.tsx:92,96,110,117`, `src/routes/tenants/$tenantId.tsx:67`, others.
- `src/hooks/useEntityFormSheet.ts:90-97` re-implements the invalidation block of
  `useEntityMutation` (`lib/queries.ts:110-124`) instead of composing it.

**Recommended fix.**
1. Create `src/lib/query-keys.ts`: `resourceKeys(resource)` returning
   `{ all, list(params), detail(id), sub(id, name) }`; export a `queryKeys` map per resource.
2. Replace `['user', userId]` with `queryKeys.users.detail(userId)` at all three sites.
3. Migrate hand-typed key arrays to the factory (mechanical grep-driven sweep).
4. Have `useEntityFormSheet` compose `useEntityMutation` instead of duplicating invalidation.

**Acceptance criteria.**
- [ ] `grep -rn "\['user'," src` → 0 matches.
- [ ] `grep -rn '"detail",' src/routes src/components` → 0 hand-typed detail keys remain.
- [ ] Changing a user's role updates `useCanWrite` without a page refresh (manual test).
- [ ] `useEntityFormSheet` contains no direct `invalidateQueries` duplication.

---

## CQ-A04: Client-side filters silently applied over server-paginated data

**Severity:** 🟠 High · **Effort:** M · **Status:** ⬜ Todo · **Owner:** - · **PR:** -

**Problem.** Five list pages fetch a server-paginated page (`limit: 20`, `total` from server) and
then apply an additional local filter. Pagination still renders the server total, so counts are
wrong, pages can appear empty while later pages contain matches, and results are silently
incomplete. Each page invented a different one-off local filter instead of a server param.

**Evidence.**
- `src/routes/persons/index.tsx:159-162` (status)
- `src/routes/users/index.tsx:153` (`filterBySecurity`)
- `src/routes/contracts/index.tsx:149` (`filterByRenewal`)
- `src/routes/service-sessions/index.tsx:166` (`filterByRange`)
- `src/routes/industries.tsx:86` (`filterByLevel`)
- Correct precedent: `src/routes/providers/index.tsx:47-53`: explicit unpaginated fetch with a
  comment, pagination footer hidden.

**Recommended fix.** Per filter, either (a) push it into the server `params` if the BE supports
it (extend endpoint param types; see CQ-C06), or (b) adopt the providers pattern: explicit full
fetch, comment, no pagination footer. Never mix silently. Fold into the `useListPage` migration
(CQ-B01) where practical.

**Acceptance criteria.**
- [ ] No list page filters a server-paginated result set client-side.
- [ ] Pagination totals match the visible result semantics on all five pages.
- [ ] Each remaining client-side filter has an explicit comment and unpaginated fetch.

---

## CQ-A05: Entity-by-id resolved via the `search` param hack

**Severity:** 🟠 High · **Effort:** M · **Status:** ⬜ Todo · **Owner:** - · **PR:** -

**Problem.** ~10 sites resolve an entity by id with `list({ page: 1, limit: 1, search: id })`
then `.find(x => x.id === id)`: relying on the search endpoint happening to match an id string.
In form-sheet edit mode, pickers can't display the selected entity unless it happens to be in the
first unsearched page, so they silently render "unselected". Detail pages also fetch related
entities with untyped casts and client-side re-filtering.

**Evidence.**
- Locked summaries: `src/components/ContractFormSheet.tsx:310-315`, `PersonFormSheet.tsx:639-676`,
  `EngagementFormSheet.tsx:301-338`, `CampaignFormSheet.tsx:353-390`, `SurveyFormSheet.tsx:204-242`,
  `ServiceSessionFormSheet.tsx:371-449`, `ServiceAssignmentFormSheet.tsx:174-210`.
- Worst case: `src/routes/service-sessions/$sessionId.tsx:111-123`: provider fetched by passing
  its **id** as `search`, while `providersApi` has a real detail endpoint used by
  `routes/providers/$providerId.tsx:32`.
- Picker resolution bug: `.find()` against current search page, e.g. `ContractFormSheet.tsx:355`.

**Recommended fix.** Use the real `getById` endpoints (add any missing ones to
`api/endpoints/*`). The shared `EntityPicker`/`LockedEntitySummary` (CQ-B03) must accept a
`getById` so selected-entity resolution is correct once, everywhere.

**Acceptance criteria.**
- [ ] `grep -rn "search: .*[iI]d" src/components src/routes` → 0 by-id-via-search calls.
- [ ] Opening any form sheet in edit mode displays the pre-selected entity (manual test on
      contracts, engagements, sessions).
- [ ] All by-id fetches go through typed `getById` endpoints.

---

## CQ-A06: Hardcoded audit reasons, fake-user fallback, hardcoded completion data

**Severity:** 🟡 Medium · **Effort:** S · **Status:** ⬜ Todo · **Owner:** - · **PR:** - · **Depends on:** CQ-B10

**Problem.** Destructive lifecycle actions write meaningless audit trails, and two mutation
payloads fall back to a fake user id.

**Evidence.**
- `"Terminated from UI"` hardcoded reason: `src/routes/contracts/$contractId.tsx:122`,
  `clients/$clientId.tsx:152`, `persons/$personId.tsx:174`. (`users/$userId.tsx:463-530` does it
  right with a reason dialog, but that dialog is inline and non-reusable.)
- `src/routes/service-sessions/$sessionId.tsx:136-148`: `duration: 60`,
  `notes: "Session completed."` on complete; `"Cancelled by counsellor."` on cancel (TODO at :137).
- `useAuthStore((s) => s.user_id) ?? "user-helen"` in
  `src/routes/engagements/$engagementId.tsx:596` and
  `src/routes/care-callbacks/worklist/$caseId.tsx:57`.

**Recommended fix.** Route all reason-gated actions through the shared `ReasonDialog` from
CQ-B10; prompt for session completion details (or read duration from the selected Service);
remove the `"user-helen"` fallback, if `user_id` is null that's an auth bug to surface, not
paper over.

**Acceptance criteria.**
- [ ] `grep -rn '"Terminated from UI"\|user-helen\|Session completed\."' src` → 0 matches.
- [ ] Terminate/suspend flows collect a user-entered reason.
- [ ] Session completion sends real duration/notes or omits them.

---

## CQ-A07: `api/client.ts` internals: triplicated 401-retry, dead 5xx retry, `getBlob` error bypass

**Severity:** 🟠 High · **Effort:** M · **Status:** ⬜ Todo · **Owner:** - · **PR:** -

**Problem.** The transport core duplicates its own logic and one of its safety features never runs:
1. The 401 → refresh → rebuild headers → retry block is copy-pasted 3× (`request()` :557-591,
   `postFormData()` :293-310, `getBlob()` :341-355) and the copies already disagree,
   `request`/`postFormData` skip refresh for `/auth/` paths; `getBlob` doesn't.
2. `buildHeaders` (:227-255) vs `buildAuthHeaders` (:260-277) duplicate token/CSRF/tenant logic,
   differing only in `Content-Type`.
3. **Dead code:** `retryRequest` (:473-496) retries on `error instanceof ApiError && status >= 500`,
   but the wrapped fn is a raw `fetch` that never throws `ApiError` (a 5xx resolves normally;
   `parseError` runs *after* `retryRequest` returns, :598-601). Only network `TypeError`s ever retry.
4. `getBlob` bypasses `parseError` with a hardcoded `'DOWNLOAD_ERROR'` (:362-366), losing error
   normalization.

**Recommended fix.** One private `executeWithAuthRetry(makeRequest, path)` owning refresh + retry +
`handleAuthError`; one `buildHeaders(path, { json?: boolean })`; route `getBlob`/`postFormData`
through both. Fix retry by checking `response.status >= 500` inside the retry loop (or throwing
`ApiError` before retrying).

**Acceptance criteria.**
- [ ] Exactly one 401-refresh-retry implementation; one header builder.
- [ ] Unit test: a 500 response is retried the configured number of times.
- [ ] Unit test: 401 on `/auth/` paths is not refresh-retried; consistent across all verbs incl. blob.
- [ ] `getBlob` errors flow through `parseError`.

---

## CQ-A08: `clients` list never strips `?new=1`

**Severity:** 🟢 Low · **Effort:** XS · **Status:** ✅ Done · **Owner:** Claude · **PR:** `48ac3b3`

> Done: the `?new=1` effect now calls `navigate({ search: (prev) => ({ ...prev, new: undefined }), replace: true })` after opening the sheet, matching every other list route.

**Problem.** Every other list page opens the create sheet from `?new=1` and then strips the
param; `src/routes/clients/index.tsx:105-107` opens the sheet but never strips it, so closing the
sheet and refreshing/back-navigating reopens it.

**Recommended fix.** One-line fix now; permanently solved by `useNewParamSheet` (CQ-B09).

**Acceptance criteria.**
- [ ] Visiting `/clients?new=1`, closing the sheet, and pressing refresh does not reopen the sheet.

---

## CQ-A09: Missing/inconsistent error states on client-filtered list pages

**Severity:** 🟡 Medium · **Effort:** S · **Status:** ⬜ Todo · **Owner:** - · **PR:** - · **Depends on:** CQ-B01

**Problem.** The four client-driven list pages (raw `useQuery` + local `filterAndSort`) have no
pagination and inconsistent error handling: `src/routes/engagements/index.tsx:126-139` renders
nothing at all on query error; `src/routes/care-callbacks/index.tsx:180-186` invents a third
inline error UI different from the shared `ErrorState`. `src/routes/tenants/index.tsx:108-113`
uses `offset` instead of `page`: a third pagination param convention.

**Recommended fix.** Fold these pages onto the shared list scaffold (CQ-B01) so error/empty/
pagination states are uniform; align tenants on the `page` convention (or document why `offset`).

**Acceptance criteria.**
- [ ] Every list page renders a retryable error state on query failure.
- [ ] One pagination param convention across list pages.

---

## CQ-A10: Engagements cannot be closed; the Invoiced transition is missing from the client

**Severity:** Critical - **Effort:** S - **Status:** Todo - **Owner:** eap-85 - **PR:** -

**Problem.** The engagement lifecycle is Draft, Active, Delivered, Invoiced, Closed. The client
can drive three of those transitions and not the fourth, and the one it cannot drive is a
prerequisite for the last one. So from the UI an engagement reaches Delivered and can never be
closed.

`FSM_ROUTES` maps ACTIVE to `activate`, DELIVERED to `deliver` and CLOSED to `close`. There is no
INVOICED entry, so `transition(id, EngagementStatus.INVOICED)` throws "No FSM route for status".
The backend route it would call does exist. The domain then blocks the last step: `close()` raises
`InvalidStateError` unless the status is already INVOICED, and `invoice()` is the only way to
reach INVOICED.

**Evidence.**
- `src/api/endpoints/engagements.ts:46` - `FSM_ROUTES` has no `INVOICED` key.
- `apps/api/app/api/routes/engagements.py:294` - `POST /engagements/{id}/invoice` exists,
  summarised "Mark a delivered engagement as invoiced".
- `apps/api/app/domain/entities/engagement.py:261` - `invoice()` requires status DELIVERED.
- `apps/api/app/domain/entities/engagement.py:270` - `close()` requires status INVOICED.
- Verify: `grep -n "INVOICED" src/api/endpoints/engagements.ts` returns nothing.

**Recommended fix.** Add `[EngagementStatus.INVOICED]: "invoice"` to `FSM_ROUTES`, then confirm
the engagement detail UI offers Invoice as an action between Deliver and Close. Assigned to eap-85
because that module is mid-refactor for the enum value correction and a one-line change there
would collide.

**Acceptance criteria.**
- An engagement can be taken Draft to Closed entirely from the UI.
- `close` is not offered on an engagement that has not been invoiced.

---

## CQ-A11: The page heading is rendered twice, and 6 pages still have none

**Severity:** Medium - **Effort:** M - **Status:** Todo - **Owner:** - - **PR:** -

**Problem.** `PageShell` now renders the page heading as an `h1`, which is the accessible and
conventional place for it. `DashboardHeader` still derives and renders its own title from the
route, so a list page shows its name twice, once in the global bar and once as the heading.

The global title cannot simply be removed yet. Six routes render content without `PageShell` and
would be left with no heading at all: `providers/index.tsx`, `providers/$providerId.tsx`,
`incidents/index.tsx`, `incidents/$incidentId.tsx`, `tags/$tagId.tsx`, and the `new.tsx` shims
that render rather than redirect.

**Evidence.**
- `src/components/common/PageShell.tsx` renders the `h1`.
- `src/components/DashboardHeader.tsx:46` renders `PageTitle` for every route.
- Verify: `for f in $(find src/routes -name '*.tsx' ! -name '*.test.tsx'); do grep -q PageShell
  "$f" || echo "$f"; done`, then discard the layout and redirect files.

**Recommended fix.** Bring the six content routes onto `PageShell`, then delete `PageTitle`,
`ROUTE_TITLES` and `routeTitle` from `DashboardHeader` and leave the global bar to search,
notifications and the account menu. Do it in that order; removing the title first regresses those
six pages.

**Acceptance criteria.**
- Every route that renders content has exactly one `h1`.
- The global header carries no page title.

---

## CQ-A12: Clinical detail pages are titled with a truncated id

**Severity:** Low - **Effort:** S - **Status:** Todo - **Owner:** - - **PR:** -

**Problem.** `cases/$caseId.tsx` and `care-callbacks/worklist/$caseId.tsx` had a full UUID as the
page heading. They now show `Case 9f2c4b1e` and `Callback 9f2c4b1e`, following the truncation
already used for contract references, which is an improvement but still not a name a person
recognises.

Neither page has a human identifier in scope. Both could resolve one: the worklist page holds
`outreach.person_id` and could fetch the person. That was not done deliberately, because the
clinical module identifies subjects as `clinical_subject_id` rather than by name, which reads as
intentional pseudonymisation. Surfacing a name here is a privacy decision, not a UI cleanup.

**Question for the product owner.** Should a counsellor see the person's name in the heading of a
clinical case, or is the pseudonymous id deliberate? The answer decides whether these pages fetch
a name or gain a case reference number instead.

**Evidence.**
- `src/routes/cases/$caseId.tsx` heading uses `caseData.clinical_subject_id`.
- `src/routes/care-callbacks/worklist/$caseId.tsx` heading uses `outreach.person_id`.

---

## CQ-A13: A design sketch is reachable from the command palette without its label

**Severity:** Low - **Effort:** S - **Status:** Todo - **Owner:** - - **PR:** -

**Correction.** This ticket previously said the At Risk page shipped fabricated compliance
records as live data, and called it critical. That framing was wrong and is withdrawn. The page is
a deliberate design sketch, confirmed by the product owner, and the codebase says so in two
places: `routes/me.tsx:294-300` renders it under a "Preview pages" heading reading "Work-in-progress
screens, not yet linked from the main nav", and its own entry at `routes/me.tsx:290` describes it as
"PHQ-9 / no-show driven at-risk list: placeholder, ships in Phase 3." Reaching it the intended way
tells you what it is before you arrive. I recorded the finding before reading those lines.

**What actually remains.** One entry point bypasses that framing. `CommandPalette.tsx:46` lists
"At Risk" in the "Quick" group alongside real destinations, so a user pressing the palette shortcut
and selecting it lands on the sketch with nothing on the page saying it is one. The sketch's
contents are placeholder by design, including `LoggedInDevicesCard`, whose `DEFAULT_SESSIONS` shows
example devices and locations. That is fine on a page understood to be a sketch and misleading on a
page that looks live.

**Evidence.**
- `src/components/CommandPalette.tsx:46` puts `/at-risk` in the "Quick" group.
- `src/routes/me.tsx:294-300` is the labelled "Preview pages" entry point.
- `src/routes/at-risk.tsx` redirects `/at-risk` into the view.

**Recommended fix.** Either drop the palette entry so the labelled route is the only way in, or
give preview views an in-page marker. The second has an existing convention to follow rather than
invent: `common/FixtureBanner.tsx` already renders a thin warning strip for "sample data, not from
the API", mounted once in `AppLayout`. A preview marker gated the same way would read consistently.

**Not a defect.** `QueryTable` holding `MOCK_DATA`, and its filters and pagination being inert,
are properties of a sketch and need no fix while it stays one. `design.tsx:637` already tracks it as
`status: "rebuild"`. If the view is ever promoted to a real page, the data source it names is
PHQ-9 scores and session no-shows, which is clinical, so see BE-B03 on the missing
`require_clinical_scope` in `care_callbacks.py` before wiring anything.

---

## CQ-A14: List routes duplicate a row-border constant the primitive could own

**Severity:** Low - **Effort:** M - **Status:** Todo - **Owner:** - - **PR:** -

**Problem.** `TableRow` defaults to `border-fg/20`. Sixteen files pass `border-fg/8` instead, most
of them via their own local copy of the constant rather than the `ROW_BORDER` export that exists
for it.

**Correction to an earlier finding.** This was previously recorded as a correctness bug, on the
grounds that two single-class selectors of equal specificity leave the winner to stylesheet order.
That was wrong. `cn` is `twMerge(clsx(...))`, and tailwind-merge removes the conflicting earlier
class, so the value passed at the call site deterministically wins. Verified directly:
`twMerge("border-b border-fg/20", "border-fg/8")` yields `border-b border-fg/8`. The rendered
result is predictable; only the duplication is a problem.

**Why the primitive default was not simply changed.** Of 63 `TableRow` usages, 8 set a border
explicitly and the rest inherit `border-fg/20`. Changing the default to `/8` would lighten row
borders on roughly 55 rows across the app, which is a visible restyle rather than a cleanup, so it
wants to be a deliberate design decision rather than a side effect.

**Recommended fix.** Decide the intended row-border weight once. If it is `/8`, change the
primitive default and delete all sixteen overrides in the same commit so the change is reviewable
as one visual diff. Until then, import `ROW_BORDER` from `common/tableStyles` rather than
redeclaring it, as `routes/clients/index.tsx` now does.

---

## CQ-A15: Enum wire values are printed to users in place of labels

**Severity:** Medium - **Effort:** M - **Status:** Partly fixed - **Owner:** - - **PR:** -

**Problem.** Enum values are wire values, not display text. Where a component renders one directly
the user sees the wire form. This stayed invisible while values read as English, and became visible
when they were corrected to the PascalCase forms the API accepts.

Six sites were live defects, showing `ClientEmployee` rather than "Client Employee". Those are
fixed by routing through `getStatusLabel`, with a test asserting no value of `PersonType` survives
labelling with a case boundary intact.

**Correction, and one of the seven was my error.** I also routed `service.category` on the service
detail page through `getStatusLabel`, on the stated grounds that it is a `ServiceCategory` enum
holding PascalCase values. It is not. `service_model.py:41` declares it
`Mapped[str | None] = mapped_column(String(100), nullable=True)`, free text, and the contract types
it `{"anyOf": [{"type": "string"}, {"type": "null"}]}`, a plain string with no `$ref`. Labelling free
text silently rewrites what a user typed: `eap` displayed as `Eap`, `wellness` as `Wellness`. That
site now shows the value as entered.

The confusion is real and worth knowing about, not just mine. There are two different fields spelled
alike: `Service.category` is free text (`types/entities/delivery.ts:22`, `category?: string | null`),
while `ProgrammeSessionCap.service_category` and `AuthorizationModel.service_category` are the
`ServiceCategory` enum (`types/entities/clinical.ts:116`). Nothing links them, so a completed session
cannot be mapped to the programme cap it consumes. That gap is logged separately in
`apps/api/docs/SERVICES_MODULE.md`, section 3.6.

The check that distinguishes them: an enum-backed field has a `$ref` in the contract and a CHECK
constraint or enum column in the model. `person_type` has both, which is why the other six sites are
correct. Confirm that before routing any field through a label helper.

**What remains.** About thirty further raw renders exist across the app. Each is currently correct
only because its enum happens to hold single-word values, so each is a latent defect that becomes
visible the next time a value is corrected. Examples: `payment_frequency` and `payment_status` in
`routes/contracts/$contractId.tsx`, `role` in `routes/persons/$personId.tsx` and
`routes/persons/index.tsx`, `region`, `panel_status`, `tier` and `accreditation_status` across
both providers routes, and the `Status is ${searchParams.status}` filter chips on five list routes.

**Guard added.** `src/utils/statusLabel.test.ts` now asserts that labelling round-trips for every
PascalCase value of every enum: removing the spaces from the label returns the wire value exactly.
That is 252 values across 57 enums, so a new member is covered without anyone writing a case. It
catches both failure modes this helper has shipped, words left glued and an acronym flattened.
Verified by restoring the previous helper, which fails it. The narrower "contains no case boundary"
assertions do not catch the second mode, because `Cismresponse` has no boundary left to find.

**Which enums need a label map.** The helper cannot tell `DAP` from `CALL`; both are just
all-capital strings, so the right treatment is undecidable from the value and has to be declared.
It splits cleanly, verified against the enum file:

| Enum | All-capital values | Wants |
| --- | --- | --- |
| `TriageInstrumentCode` | CSSRS, WSAS | case kept, real acronyms |
| `ClinicalNoteType` | DAP, SOAP | case kept, real acronyms |
| `CaseReferralSource` | HR | case kept, real acronym |
| `ActivityType` | CALL, EMAIL, MEETING, NOTE | title case, shouty constants |
| `ActionType` | CREATE, UPDATE, DELETE and 8 more | title case, shouty constants |

So two enums want a label map and three want what the helper already does. The round-trip guard
currently pins `CALL` and the rest as caps-preserving, so introducing the map will fail that
assertion, which is the intended signal rather than a problem.

**One display question this raised.** Preserving a run of capitals means a value that is entirely
capitals is now left alone, so `ActivityType` values render as `CALL` and `EMAIL` rather than `Call`
and `Email`. That is correct for `DAP` and `SOAP`, and shouty for the rest.
`components/clients/ClientActivityCard.tsx:93` renders `activity_type` raw as a fallback title, so it
already shows the capitals; routing it through the helper would not fix it. Those enums want a label
map rather than a derived label, which is a copy decision.

**Previous limit, now fixed.** `getStatusLabel` splits on a lower-to-upper boundary, so an embedded
acronym is lost: `CISMFollowUp` becomes "Cismfollow Up" and `CISMResponse` becomes "Cismresponse".
`CaseReferralSource` and `ClinicalNoteType` both carry CISM values. Fixed in `c1823a8`, which
splits on the boundary between an acronym and a following word and preserves an all-capital word,
so these now read `CISM Follow Up` and `CISM Response`.

**Recommended fix.** Two parts, in order. Sweep the remaining raw renders, per module rather than in one pass,
since three sessions share this tree. A lint rule barring a bare enum-typed field inside JSX braces
would prevent recurrence, but the enum drift guard added in `a7bbd31` only checks values against the
contract, not how they are displayed.

**Why this recurs.** Two sessions each shipped a regression of this exact shape within a day, both
found by the other checking rather than by a test. There is no guard on the display side.

---

## CQ-A16: The client overview shows a fabricated campaign badged "Live"

**Severity:** High - **Effort:** S - **Status:** Todo - **Owner:** - - **PR:** -

**Problem.** `routes/clients/$clientId.tsx` renders `<EmailCampaignCard />` with no props. The
component's defaults then supply everything on screen: a campaign named "Wellness check-in · Q2
2026", a delivery rate of 98.0% from 415,581 sent, and an open rate of 32.4% from 131,955 opened.
The card also renders an unconditional `Live` badge, so the page asserts the figures are current.

Because the call site passes nothing, the card cannot be about the client being viewed. Whichever
client you open, the same invented campaign appears with the same numbers.

This is distinct from CQ-A13. The At Risk screen is a design sketch, labelled as one and reached
through a "Preview pages" heading that says so. The client detail page is a live page in the module
this review covers, and nothing on it marks this card as placeholder.

**Evidence.**
- `src/routes/clients/$clientId.tsx` renders `<EmailCampaignCard />`, no props.
- `src/components/EmailCampaignCard.tsx:26` declares `DEFAULT_SECTIONS` with the figures above.
- `src/components/EmailCampaignCard.tsx:57` defaults the subtitle to the campaign name.
- `src/components/EmailCampaignCard.tsx:67` renders the `Live` badge unconditionally.
- Seen rendered in a browser on the Minet Uganda overview tab.

**Recommended fix.** The component itself is fine: it is presentational, with defaults that suit a
gallery. The defect is the call site. Either pass real campaign data for the client, or remove the
card from the overview tab until there is a source for it. A search of the published contract found
no endpoint serving campaign delivery metrics scoped to a client, so removal is the available
option today. Make the `Live` badge conditional on real data either way.

**Acceptance criteria.**
- No live page renders campaign figures that are the same for every client.
- A "Live" badge appears only when the figures came from the API.

