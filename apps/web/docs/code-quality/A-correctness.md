# Track A — Correctness & Safety

Bugs and risks discovered during the SOLID/DRY review. These take priority over refactors:
several are ship-blocking. Line numbers are as of 2026-07-14 (`main` @ `066f1db`); re-verify with
the greps given in each ticket before starting.

---

## CQ-A01 — Live-mode API paths (`/v1/*`) don't exist in the backend schema

**Severity:** 🔴 Critical · **Effort:** M · **Status:** ⬜ Todo · **Owner:** — · **PR:** —

**Problem.** The fixture-backed endpoint modules have "live" branches that call `/v1/...` paths.
The generated OpenAPI schema (`src/api/generated/schema.ts`) contains **zero** `/v1/*` paths —
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

## CQ-A02 — Fixtures default ON; clinical business logic lives in fixture files

**Severity:** 🔴 Critical · **Effort:** M · **Status:** ⬜ Todo · **Owner:** — · **PR:** —

**Problem.** All 7 fixture toggles use `import.meta.env?.VITE_X_USE_FIXTURE !== 'false'` —
fixtures are ON unless every deployment sets 7 env vars explicitly. A missed var ships fake
clinical data (fixture campaigns, PHQ-9 outcomes) to production silently. Worse:
`evaluateCrisisRules` — the PHQ-9 item-9 self-harm crisis rule — is defined inside
`questionnaires-fixture.ts` and imported by a production route; `engagementsApi.allowedTransitions`
delegates to fixture code even in live mode. All fixture files are statically imported, so
~1,800 lines of seed data are always in the bundle.

**Evidence.**
- Toggles: `src/api/endpoints/{diagnoses:24, care-callbacks:34, engagements:35, incidents:29, pricing:19, questionnaires:17, surveys:30}.ts` — verified by grep.
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

## CQ-A03 — Query-key split-brain: current user cached under two different keys

**Severity:** 🟠 High · **Effort:** S · **Status:** ✅ Done · **Owner:** Claude · **PR:** `dc91516`, `4ef79b0`

> Done: `lib/query-keys.ts` created (`resourceKeys` factory + `queryKeys` map); the three
> `['user', userId]` sites now use `queryKeys.users.detail(id)` so
> `useEntityMutation({resource:'users'})` invalidation reaches them — split-brain fixed. Migrated
> ~27 hand-typed `detail`/`list` key literals across routes + form sheets to the factory;
> `extraInvalidations` widened to `QueryKey`. Three self-consistent paginated sub-keys left as-is.
> **Deferred (own ticket):** have `useEntityFormSheet` fully compose `useEntityMutation` (currently
> re-implements invalidation) — tracked under CQ-C01's mutation-idiom convergence.

**Problem.** The current user is cached as `['user', userId]` in three places, while the same
record is cached as `['users', 'detail', id]` elsewhere. Any `useEntityMutation({ resource: 'users' })`
(role change, suspend) invalidates `['users', …]` but never `['user', userId]` — so
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

## CQ-A04 — Client-side filters silently applied over server-paginated data

**Severity:** 🟠 High · **Effort:** M · **Status:** ⬜ Todo · **Owner:** — · **PR:** —

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
- Correct precedent: `src/routes/providers/index.tsx:47-53` — explicit unpaginated fetch with a
  comment, pagination footer hidden.

**Recommended fix.** Per filter, either (a) push it into the server `params` if the BE supports
it (extend endpoint param types — see CQ-C06), or (b) adopt the providers pattern: explicit full
fetch, comment, no pagination footer. Never mix silently. Fold into the `useListPage` migration
(CQ-B01) where practical.

**Acceptance criteria.**
- [ ] No list page filters a server-paginated result set client-side.
- [ ] Pagination totals match the visible result semantics on all five pages.
- [ ] Each remaining client-side filter has an explicit comment and unpaginated fetch.

---

## CQ-A05 — Entity-by-id resolved via the `search` param hack

**Severity:** 🟠 High · **Effort:** M · **Status:** ⬜ Todo · **Owner:** — · **PR:** —

**Problem.** ~10 sites resolve an entity by id with `list({ page: 1, limit: 1, search: id })`
then `.find(x => x.id === id)` — relying on the search endpoint happening to match an id string.
In form-sheet edit mode, pickers can't display the selected entity unless it happens to be in the
first unsearched page, so they silently render "unselected". Detail pages also fetch related
entities with untyped casts and client-side re-filtering.

**Evidence.**
- Locked summaries: `src/components/ContractFormSheet.tsx:310-315`, `PersonFormSheet.tsx:639-676`,
  `EngagementFormSheet.tsx:301-338`, `CampaignFormSheet.tsx:353-390`, `SurveyFormSheet.tsx:204-242`,
  `ServiceSessionFormSheet.tsx:371-449`, `ServiceAssignmentFormSheet.tsx:174-210`.
- Worst case: `src/routes/service-sessions/$sessionId.tsx:111-123` — provider fetched by passing
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

## CQ-A06 — Hardcoded audit reasons, fake-user fallback, hardcoded completion data

**Severity:** 🟡 Medium · **Effort:** S · **Status:** ⬜ Todo · **Owner:** — · **PR:** — · **Depends on:** CQ-B10

**Problem.** Destructive lifecycle actions write meaningless audit trails, and two mutation
payloads fall back to a fake user id.

**Evidence.**
- `"Terminated from UI"` hardcoded reason: `src/routes/contracts/$contractId.tsx:122`,
  `clients/$clientId.tsx:152`, `persons/$personId.tsx:174`. (`users/$userId.tsx:463-530` does it
  right with a reason dialog — but that dialog is inline and non-reusable.)
- `src/routes/service-sessions/$sessionId.tsx:136-148` — `duration: 60`,
  `notes: "Session completed."` on complete; `"Cancelled by counsellor."` on cancel (TODO at :137).
- `useAuthStore((s) => s.user_id) ?? "user-helen"` in
  `src/routes/engagements/$engagementId.tsx:596` and
  `src/routes/care-callbacks/worklist/$caseId.tsx:57`.

**Recommended fix.** Route all reason-gated actions through the shared `ReasonDialog` from
CQ-B10; prompt for session completion details (or read duration from the selected Service);
remove the `"user-helen"` fallback — if `user_id` is null that's an auth bug to surface, not
paper over.

**Acceptance criteria.**
- [ ] `grep -rn '"Terminated from UI"\|user-helen\|Session completed\."' src` → 0 matches.
- [ ] Terminate/suspend flows collect a user-entered reason.
- [ ] Session completion sends real duration/notes or omits them.

---

## CQ-A07 — `api/client.ts` internals: triplicated 401-retry, dead 5xx retry, `getBlob` error bypass

**Severity:** 🟠 High · **Effort:** M · **Status:** ⬜ Todo · **Owner:** — · **PR:** —

**Problem.** The transport core duplicates its own logic and one of its safety features never runs:
1. The 401 → refresh → rebuild headers → retry block is copy-pasted 3× (`request()` :557-591,
   `postFormData()` :293-310, `getBlob()` :341-355) and the copies already disagree —
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

## CQ-A08 — `clients` list never strips `?new=1`

**Severity:** 🟢 Low · **Effort:** XS · **Status:** ✅ Done · **Owner:** Claude · **PR:** `48ac3b3`

> Done: the `?new=1` effect now calls `navigate({ search: (prev) => ({ ...prev, new: undefined }), replace: true })` after opening the sheet, matching every other list route.

**Problem.** Every other list page opens the create sheet from `?new=1` and then strips the
param; `src/routes/clients/index.tsx:105-107` opens the sheet but never strips it, so closing the
sheet and refreshing/back-navigating reopens it.

**Recommended fix.** One-line fix now; permanently solved by `useNewParamSheet` (CQ-B09).

**Acceptance criteria.**
- [ ] Visiting `/clients?new=1`, closing the sheet, and pressing refresh does not reopen the sheet.

---

## CQ-A09 — Missing/inconsistent error states on client-filtered list pages

**Severity:** 🟡 Medium · **Effort:** S · **Status:** ⬜ Todo · **Owner:** — · **PR:** — · **Depends on:** CQ-B01

**Problem.** The four client-driven list pages (raw `useQuery` + local `filterAndSort`) have no
pagination and inconsistent error handling: `src/routes/engagements/index.tsx:126-139` renders
nothing at all on query error; `src/routes/care-callbacks/index.tsx:180-186` invents a third
inline error UI different from the shared `ErrorState`. `src/routes/tenants/index.tsx:108-113`
uses `offset` instead of `page` — a third pagination param convention.

**Recommended fix.** Fold these pages onto the shared list scaffold (CQ-B01) so error/empty/
pagination states are uniform; align tenants on the `page` convention (or document why `offset`).

**Acceptance criteria.**
- [ ] Every list page renders a retryable error state on query failure.
- [ ] One pagination param convention across list pages.
