# Track C — SOLID / Architecture

Structural issues: single-responsibility violations, open/closed violations, type-contract drift,
and paradigm inconsistency (the meta-violation that breeds the Track B duplication). Line numbers
as of 2026-07-14 (`main` @ `066f1db`).

---

## CQ-C01 — Converge on TanStack Query: migrate manual-fetch detail pages to `useEntityDetail`

**Severity:** 🟠 High · **Effort:** L · **Status:** ⬜ Todo · **Owner:** — · **PR:** — · **Depends on:** CQ-A03

**Problem.** Two competing data-fetch paradigms exist for the same job. Query-based pages:
engagements, tenants, surveys, care-callbacks, incidents, providers, reports. Manual
`useState` + `useCallback(fetchX)` + `useEffect` pages: users, clients, persons, service-sessions,
contracts, services, service-assignments. Consequences of the manual pattern: no cache/dedup, no
invalidation from `useEntityMutation` elsewhere, repeated cancelled-flag boilerplate (~15 lines per
related entity — 4 separate copies in persons alone), and form sheets that
`onSaved={(u) => setX(u)}` — silently diverging from the query cache other pages read
(e.g. `clients/$clientId.tsx:348`). `clients/$clientId.tsx:117-142` refetches stats/children/tags
on every `client` object identity change. Meanwhile `lib/queries.ts:62-75` already provides
`useEntityDetail` — **no detail route uses it**, and even query-based pages re-type key literals
instead of calling `entityDetailKey`. `tenants/$tenantId.tsx:183-219` uses a third idiom (raw
`useMutation` + manual `setQueryData`).

**Evidence.** Manual pages: `users/$userId.tsx:62-104`, `clients/$clientId.tsx:72-142`,
`persons/$personId.tsx:67-164`, `service-sessions/$sessionId.tsx:62-130`,
`contracts/$contractId.tsx:51-114`, `services/$serviceId.tsx:61+`,
`service-assignments/$assignmentId.tsx:50+`.

**Recommended fix.**
1. Migrate all 7 manual pages to `useEntityDetail({ resource, id, detailFn })`; related entities
   via `useQuery` with `queryKeys.<resource>.sub(id, name)`.
2. Form sheets write to the cache (`queryClient.setQueryData(entityDetailKey(...), updated)` — the
   pattern `tenants/$tenantId.tsx:183-186` already uses) instead of `onSaved` local-state setters.
3. Standardize mutations on `useEntityMutation` (one idiom, not three).

**Acceptance criteria.**
- [ ] `grep -rn "useEffect(.*fetch" src/routes/**/\$*.tsx` → 0 manual fetch effects.
- [ ] No cancelled-flag boilerplate remains in detail routes.
- [ ] Editing an entity in a form sheet updates every mounted view of it without refetch (manual test).
- [ ] All detail queries use `queryKeys`/`entityDetailKey` (no hand-typed key arrays).

---

## CQ-C02 — Split god detail routes into feature folders

**Severity:** 🟡 Medium · **Effort:** L · **Status:** ⬜ Todo · **Owner:** — · **PR:** — · **Depends on:** CQ-B02, CQ-B04

**Problem.** Every large detail route is one file playing 6+ roles. Anatomy of
`engagements/$engagementId.tsx` (944 lines): 6 queries + 1 mutation (:91-128), page shell/loading/
not-found (:130-160), layout + tabs (:175-387), `Hero` (:390-431), `DeliverablesPanel` with two
mutations and an inline create form (:433-581), `HoursPanel` (:584-723), `TimelinePanel`
(:725-766), `DetailRail` (:776-869), 5 primitives (:871-935), a formatter (:937-944). Same shape
in users (self-mutating `RoleCard` :670-753, reason-dialog state machine :106-167), clients
(`ContractsPanel` :477-584, derived-alerts business logic :176-271), service-sessions
(`FeedbackPanel` :595-675, `RescheduleDialog` :677-758), campaigns, services. Cross-layer smells:
`engagements/$engagementId.tsx:46-49` imports `EngagementStatusPill`/`isOverdue` from the sibling
*route* `engagements/index.tsx`; `persons/$personId.tsx:25` imports `PERSON_TYPE_LABELS` from
`components/PersonFormSheet` (enum labels living inside a form component).

**Recommended fix.** Feature-folder convention; route file = queries + composition (~150 lines):

```
components/engagements/
  EngagementHero.tsx
  DeliverablesPanel.tsx    // owns its mutations — already self-contained
  HoursPanel.tsx
  TimelinePanel.tsx
  EngagementRail.tsx
routes/engagements/$engagementId.tsx   // composition only
```

The inline panels already receive only ids/data via props — hoisting is mechanical. Move
`PERSON_TYPE_LABELS` and friends to `lib/display.ts` or next to the enums. No route may import
from another route file.

**Acceptance criteria.**
- [ ] Engagements split first (largest, already panel-shaped); then users, clients, service-sessions.
- [ ] Each migrated route file ≤ ~200 lines.
- [ ] `grep -rn "from ['\"]@/routes\|from ['\"]\.\./.*routes" src/routes` → no route-to-route imports.
- [ ] No enum label constants exported from form components.

---

## CQ-C03 — Split `PersonFormSheet` by subtype/mode; move save orchestration to the API layer

**Severity:** 🟡 Medium · **Effort:** M · **Status:** ⬜ Todo · **Owner:** — · **PR:** — · **Depends on:** CQ-B03, CQ-B05

**Problem.** `PersonFormSheet.tsx` (884 lines) handles two entity subtypes gated by `person_type`,
a create-only User sub-form, and an optional emergency-contact PATCH. Conditional requiredness is
encoded in `superRefine` (:164-186) so the types no longer document the contract (`client_id`,
`role`, `relationship`, `work_status` typed optional but required per subtype). `save` branches
4 ways on `isEdit` × `person_type` × `emergency_name` (:263-335) — with the emergency-contact
PATCH block duplicated verbatim inside the same function (:283-289 vs :327-333). The component is
also a transaction coordinator (`usersApi.create → personsApi.create → updateEmergencyContact`).

**Recommended fix.** Follow the sibling pattern `UserFormSheet.tsx:66-71` (separate Create/Edit
components, separate schemas): a thin dispatcher rendering `EmployeeCreateSheet` /
`DependentCreateSheet` / edit variants, with `z.discriminatedUnion("person_type", […])` so
required fields are actually required. Extract `saveEmergencyContact(personId, values)` once. Move
multi-call orchestration into `api/endpoints/persons.ts` (e.g. `personsApi.createWithUser`).

**Acceptance criteria.**
- [ ] No `superRefine` encoding subtype requiredness; discriminated union in its place.
- [ ] Emergency-contact save exists exactly once.
- [ ] Component performs one API call per submit; orchestration lives in the endpoint module.
- [ ] Unused `_userId` param in `buildEmploymentInfo` (:590-593) removed.

---

## CQ-C04 — Alias hand-written types to the generated OpenAPI schema

**Severity:** 🟠 High · **Effort:** M · **Status:** ⬜ Todo · **Owner:** — · **PR:** — · **Depends on:** CQ-A01

**Problem.** `types/entities.ts` (918 lines) and `types/enums.ts` (471 lines) hand-mirror the
generated schema with no compile-time link. Drift has already happened: `Person` carries 10
`@deprecated` "NOT on BE response" fields (:221-241), `Contract` 4 (:307-314), `Service` 3
(:330-339) — each a drift incident the generated types would have caught. Generated types are
consumed in only 6 endpoint files, and only for `*Create`/`*Update` inputs; **responses** are
entirely hand-typed. The generated schema already contains `ClientResponse`, `BaseStatus`
(schema.ts:4693), `ContactMethod` (:5364), `PersonType` (:7614), `PaymentFrequency` (:7464) —
byte-identical value sets to the hand-written enums.

**Recommended fix.**
1. Alias BE-backed entities: `export type Client = Schemas['ClientResponse']` (extend locally only
   where the FE genuinely adds fields, and mark those clearly).
2. Keep TS `enum` ergonomics but pin each to the schema:
   ``const _check: Schemas['BaseStatus'] = {} as `${BaseStatus}` `` (or `satisfies`) so
   regeneration breaks the build on drift.
3. Keep hand-written types only for fixture-only domains not in the schema (questionnaires,
   callback cases/outcomes, incidents) — clearly sectioned.

**Acceptance criteria.**
- [ ] Every BE-backed response type is an alias of (or pinned to) a generated type.
- [ ] All `@deprecated` drift fields removed or justified.
- [ ] `pnpm openapi:sync` followed by `tsc` catches an intentionally-introduced enum drift (verify once).

---

## CQ-C05 — Enforce `StatusBadge`/`statusConfig`; delete local status pills

**Severity:** 🟡 Medium · **Effort:** S · **Status:** ✅ Done · **Owner:** Claude · **PR:** `f814866`

> Done: deleted `EngagementStatusPill`, `CampaignStatusPill`, `SurveyStatusPill` + their `statusTone`
> helpers (and a duplicate `CampaignStatusPill` in reports) and the route-to-route imports; all
> render via `StatusBadge`. Aligns a few colors to the canonical palette (Delivered green, Cancelled
> grey) — adjust in `statusColors.ts` if design prefers. **Follow-up:** `CaseStatusPill`
> (`CallbackCaseStatus`, ×3) left as-is because its escalation colors carry semantics.

**Problem.** `utils/statusConfig.ts:1-4` declares itself the single source of truth ("no ad-hoc
status strings"), and `StatusBadge` is used by contracts/persons/users/clients/tenants/incidents —
yet three pages define local pills with their own `statusTone` switches, rendering the raw enum
value instead of `getStatusLabel` (casing/labels differ page to page). One is exported and leaks
into the detail route.

**Evidence.** `engagements/index.tsx:440-469` (`EngagementStatusPill`, exported — imported by
`$engagementId.tsx`), `care-callbacks/index.tsx:337-364` (`CampaignStatusPill`),
`surveys/index.tsx:285-310` (`SurveyStatusPill`), `persons/index.tsx:351-353` (inline role pill).
Also `utils/statusColors.ts:81-82` duplicates the `'cancelled'` literal, and
`components/common/QueryTable.tsx:100-117` defines a fourth badge style.

**Recommended fix.** Add the three enums' colors to `statusColors`/`statusConfig`; delete the
local pills; `<StatusBadge status={row.status} />` everywhere. Merge `statusConfig`/`statusColors`
into one module (two public entry points for one concern — see CQ-D05).

**Acceptance criteria.**
- [ ] `grep -rn "StatusPill\|statusTone" src/routes` → 0.
- [ ] All status rendering goes through `StatusBadge` + `getStatusLabel`.

---

## CQ-C06 — Type list-filter params; remove `as Record<string, unknown>` casts

**Severity:** 🟡 Medium · **Effort:** S · **Status:** ⬜ Todo · **Owner:** — · **PR:** — · **Depends on:** CQ-A04

**Problem.** Detail pages pass untyped extra filters into `list()` and then re-filter client-side
because the endpoint signatures don't accept them — both a type hole and a correctness risk
(pagination means the filtered item may not be in the fetched page).

**Evidence.** `clients/$clientId.tsx:105-115`
(`contractsApi.list({ limit: 20, ...({ client_id } as Record<string, unknown>) })` then
`.filter().slice()`), `persons/$personId.tsx:152-164` (`person_id`),
`contracts/$contractId.tsx:77-91` (`contract_id`).

**Recommended fix.** Extend endpoint param types (`ListParams & { client_id?: string }` etc. —
sourced from the generated schema's query params per CQ-A01) so filters are typed and server-side;
delete the casts and client-side re-filtering.

**Acceptance criteria.**
- [ ] `grep -rn "as Record<string, unknown>" src/routes` → 0.
- [ ] Related-entity lists are filtered server-side with typed params.

---

## CQ-C07 — Pin zod schemas to generated request types

**Severity:** 🟡 Medium · **Effort:** S · **Status:** ⬜ Todo · **Owner:** — · **PR:** — · **Depends on:** CQ-C04

**Problem.** Form zod schemas are free-hand, connected to the generated request types only by
comments ("Audited against openapi.json" — `PersonFormSheet.tsx:13-22`,
`ServiceAssignmentFormSheet.tsx:20-22`). Drift is caught only at runtime via casts like
`values.work_status as WorkStatus` (`PersonFormSheet.tsx:601`), `values.sampling as
CallbackSamplingStrategy` (`CampaignFormSheet.tsx:129`). `ServiceSessionFormSheet.tsx:137-140`
admits the update payload shape is unknown.

**Recommended fix.** Cheapest guard: annotate every `parsePayload` return type with the generated
request type (`(values): ContractCreate => …`) — ContractFormSheet/ServiceAssignmentFormSheet
already do this; CampaignFormSheet/EngagementFormSheet use the equivalent
`Parameters<typeof api.create>[0]`. Standardize one of the two. Longer term: generate zod from
openapi (`openapi-zod-client` / `typed-openapi`) and derive form schemas via `.pick()`/`.extend()`.

**Acceptance criteria.**
- [ ] Every `parsePayload` has an explicit generated-type return annotation.
- [ ] No `as SomeEnum` casts in submit paths.

---

## CQ-C08 — `SheetForm` dirty-state discard guard

**Severity:** 🟡 Medium · **Effort:** S · **Status:** ⬜ Todo · **Owner:** — · **PR:** —

**Problem.** Cancel and overlay-dismiss call `onOpenChange(false)` directly
(`components/common/SheetForm.tsx:126`); a half-filled form is silently discarded.
`ConfirmDialog` exists but is unused here, and `useEntityFormSheet` already exposes
`formState.isDirty`. This is the payoff of having the shared wrapper: one change protects all 13 sheets.

**Recommended fix.** Optional `isDirty?: boolean` prop on `SheetForm`; intercept
`onOpenChange(false)` when dirty and show `ConfirmDialog` ("Discard changes?"). Wire
`formState.isDirty` through `useEntityFormSheet`.

**Acceptance criteria.**
- [ ] Dismissing a dirty sheet (Cancel, overlay, Esc) prompts before discarding; clean sheets close directly.
- [ ] Behavior verified on 3 sheets without per-sheet changes.
