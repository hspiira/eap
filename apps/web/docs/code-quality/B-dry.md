# Track B — DRY Consolidations

Duplication removal, ranked by lines removable. Every ticket here is behavior-preserving unless
stated. Line numbers as of 2026-07-14 (`main` @ `066f1db`).

---

## CQ-B01 — `useListPage` hook + `EntityListView`: kill the list-page template

**Severity:** 🟠 High · **Effort:** L · **Status:** 🟨 In progress · **Owner:** Claude · **PR:** `ddcbb46`, `859cb3f` · **Depends on:** CQ-B06, CQ-B09

> Done: `hooks/useListPage.ts` (page/sort/debounced-search state, `?new=1` strip + search→URL sync
> effects, `useEntityList` query) and `components/common/EntityListView.tsx` (loading/error/empty/
> table/pagination shell with sticky sortable header; rows bespoke via `renderRow`). Migrated
> **contracts, users, services** as references. Build passes on each.
>
> **Recipe for the remaining ~8 pages** (persons, clients, service-sessions, service-assignments,
> tags, care-callbacks, engagements, surveys, tenants, providers, incidents, industries):
> 1. `validateSearch: listSearchSchema({ status: enumParam(SomeEnum) })`; `STATUS_OPTIONS =
>    enumOptions(Enum, "All statuses")` — **but keep a curated array if the enum has members that
>    shouldn't be user filters** (e.g. `BaseStatus.Deleted`, see services).
> 2. Replace the state/effects/query block with `useListPage<T>({ from, resource, listFn,
>    extraParams: { status } })`; keep the page's own `useSearch`/`useNavigate` for the typed filter param.
> 3. Define `const COLUMNS: ListColumn[]` and swap the shell for `<EntityListView>`; pass
>    `skeletonCols` to match the old `TableSkeleton cols={n}`.
> 4. `eslint --fix` to drop now-unused imports; `tsc` + `vite build` to verify.
>
> **Note:** engagements/care-callbacks/surveys use the client-driven `useQuery`+`filterAndSort`
> pattern (not `useEntityList`) — they need the CQ-A09 convergence first, or a `useListPage` variant
> that accepts a client-side sorter. The paginate-then-filter bugs (CQ-A04) should be fixed as each
> page with a client-side secondary filter is migrated.

**Problem.** One ~400-line list-page template is copy-pasted across ~12 entities (≈60% of ~7,000
lines across 17 list pages). Each page independently re-implements: state block
(`searchInput`/`addOpen`/`page`/`sort`/`limit`/`toggleSort`), debounced search → URL sync effect,
the loading/error/empty/table/pagination ternary chain, sticky `TableHeader` with select-all +
`SortHeader` cells, and the hover row-action cell (`ExternalLink` + `DropdownMenu`).

**Evidence (byte-for-byte modulo entity type).**
- State block: `contracts/index.tsx:100-110` ≡ `users/index.tsx:104-114` ≡ `persons/index.tsx:103-113`.
- Ternary chain: `contracts:209-288` ≡ `users:212-283` ≡ `persons:238-312` ≡ `clients:200-274`
  ≡ `service-sessions:249-323`.
- Row actions: `contracts:354-386`, `persons:378-412`, `users:348-375`, `clients:328-364`,
  `service-sessions:391-436`, `engagements:409-435`, `care-callbacks:309-332`.
- Search-sync effect duplicated in 7 files (`contracts:123-128`, `clients:109-114`, …); `tags` and
  `tenants` diverge silently (never write the URL back).
- Separately, 4 client-driven pages duplicate a byte-identical 12-line `filterAndSort` comparator:
  `engagements/index.tsx:505-541`, `care-callbacks/index.tsx:390-422`, `surveys/index.tsx:336-364`,
  `care-callbacks/worklist/index.tsx:360`.

**Recommended fix (two layers).**
1. `src/hooks/useListPage.ts` — `useListPage<T, F>({ routeId, resource, listFn, defaultSort, filters })`
   owning page/sort/search state, debounce, URL sync, `useEntityList`. Returns
   `{ items, total, page, setPage, sort, toggleSort, searchInput, setSearchInput, activeFilters, setFilter, clearFilter, hasFilters, loading, error, refetch }`.
2. `src/components/common/EntityListView.tsx` — owns skeleton/error/empty/table/pagination and
   the sticky header; `ListColumn<T> = { field?, header, cell(row), sortable? }`.
3. For pages the BE can't filter server-side, extract `filterAndSortClient<T>` into `src/lib/` and
   route both modes through the same hook so error/pagination handling is uniform.
4. Migrate `contracts/index.tsx` first as the reference implementation, then the rest.

**Acceptance criteria.**
- [ ] `contracts` migrated as template; page ≤ ~150 lines (config + columns + row cells).
- [ ] All `useEntityList` list pages migrated; the 4 client-driven pages share one `filterAndSortClient`.
- [ ] The duplicated state block, ternary chain, and search-sync effect appear 0 times outside the hook/component.
- [ ] CQ-A04 and CQ-A09 resolved as part of the migration (or explicitly ticketed per page).
- [ ] `useCanWrite` gate applied uniformly to create buttons (persons/clients/tags currently missing it).

---

## CQ-B02 — Extract `DetailPrimitives` (10+ verbatim copies, ~1,100 lines)

**Severity:** 🟠 High · **Effort:** S · **Status:** ✅ Done · **Owner:** Claude · **PR:** `a72df1f`

> Done: all 5 primitives extracted to `components/common/DetailPrimitives.tsx`; removed from 11 detail routes (verified byte-identical before extraction). tsc + lint + `vite build` pass. `grep "function DetailCard" src/routes` → 0.

**Problem.** Five presentational primitives — `DetailCard`, `RailSection`, `Stat`, `DetailGrid`,
`DetailRow` (~120 lines) — are byte-identical (or trivially divergent) private functions in every
detail route. A styling change must be made in 10+ places.

**Evidence.** `engagements/$engagementId.tsx:871-935`, `service-sessions/$sessionId.tsx:760-822`,
`users/$userId.tsx:649-662,755-802`, `clients/$clientId.tsx:718-771`, `persons/$personId.tsx:610-663`,
`contracts/$contractId.tsx:437-526`, `services/$serviceId.tsx:557-605`, `surveys/$surveyId.tsx:462-530`,
`service-assignments/$assignmentId.tsx:402-460`, `care-callbacks/$campaignId.tsx:631-693`,
`care-callbacks/worklist/$caseId.tsx:577-617` (subset).
Only intentional divergence found: engagements' `Stat` adds `truncate` (:907) — keep it in the shared version.

**Recommended fix.** `src/components/common/DetailPrimitives.tsx` exporting the five components;
drop-in replacement, zero behavior change.

**Acceptance criteria.**
- [ ] `grep -rn "function DetailCard\|function RailSection\|function DetailRow" src/routes` → 0.
- [ ] All 11 files import from `components/common`; visual spot-check of 3 detail pages.

---

## CQ-B03 — Generic `EntityPicker<T>` + `LockedEntitySummary` (~1,250 lines)

**Severity:** 🟠 High · **Effort:** M · **Status:** ⬜ Todo · **Owner:** — · **PR:** — · **Depends on:** CQ-A05

**Problem.** The debounced-search → result-list → selected-summary picker is re-implemented from
scratch in 9 places (~1,100 lines); the "locked entity" summary card is copied 7× (~250 lines),
each with the fetch-by-id-via-search hack. Every picker copy has the latent selected-resolution
bug described in CQ-A05.

**Evidence.**
- `ClientPicker` ×5: `PersonFormSheet.tsx:678-767`, `ContractFormSheet.tsx:346-429`,
  `EngagementFormSheet.tsx:340-428`, `CampaignFormSheet.tsx:392-480`, `SurveyFormSheet.tsx:243+`.
- `ServicePicker` ×2 divergent: `ServiceSessionFormSheet.tsx:451-518` vs
  `ServiceAssignmentFormSheet.tsx:307-398` (one uses `PickerShell`, one inlined; `limit: 8` vs `10`).
- Also `UserPicker`, `PersonPicker`, `ProviderPicker`, `ContractPicker`, `PrimaryEmployeePicker`,
  `CounsellorMultiPicker`.
- Locked summaries: see CQ-A05 evidence list.
- The right abstraction already exists file-locally: `PickerShell<T>` + `ChangeButton` in
  `ServiceSessionFormSheet.tsx:658-711` — promote it.

**Recommended fix.** `src/components/common/EntityPicker.tsx`:

```tsx
interface EntityPickerProps<T extends { id: string }> {
  value: string
  onChange: (id: string, entity: T | null) => void
  resource: string
  listFn: (params: ListParams) => Promise<Page<T>>
  getById?: (id: string) => Promise<T>   // fixes selected-resolution (CQ-A05)
  renderPrimary: (t: T) => ReactNode
  renderSecondary?: (t: T) => ReactNode
  avatar?: (t: T) => string
  placeholder?: string
  multiple?: boolean                     // covers CounsellorMultiPicker
  locked?: boolean                       // replaces Locked*Summary
}
```

Per-entity one-liners in `components/common/pickers.tsx`
(`export const ClientPicker = (p) => <EntityPicker resource="clients" listFn={clientsApi.list} … />`).
Bind to RHF via `Controller` inside an `EntityPickerField` (removes the hidden-input hack, CQ-C08-adjacent — see CQ-B05).

**Acceptance criteria.**
- [ ] All 9 pickers and 7 locked summaries replaced; ~0 private picker components left in sheets
      (`grep -rn "useDebouncedValue(query" src/components/*FormSheet.tsx` → 0).
- [ ] Edit mode displays pre-selected entities via `getById` (manual test, 3 sheets).
- [ ] Multi-select path covers `CounsellorMultiPicker`.

---

## CQ-B04 — `EntityDetailPage` scaffold: shared detail-page chrome

**Severity:** 🟠 High · **Effort:** L · **Status:** ⬜ Todo · **Owner:** — · **PR:** — · **Depends on:** CQ-B02, CQ-B08

**Problem.** Four blocks are near-verbatim in 11+ detail routes: (1) loading block
(`PageShell` + `DetailSkeleton`), (2) not-found block (`EmptyState` + "Back to X"), (3) header
actions (ghost Back + ghost Refresh + divider + optional Edit — the same whitespace
mis-indentation is replicated in 5 files, proof of copy-paste lineage), (4) the 8/4 grid body and
hero bar. Only `tenants/$tenantId.tsx:97-100` renders a distinct error state — every other page
swallows errors into "not found", losing the retry affordance.

**Evidence.** Loading: `engagements:130-138`, `service-sessions:186-194`, `users:169-177`,
`clients:273-281`, `persons:186-194`, `contracts:142-150`, +5 more. Not-found: same files,
subsequent blocks. Header: 12 files (grep `aria-label="Refresh"`). Hero: `engagements:390-431`,
`service-sessions:462-504`, `users:535-563`, +8 more. Outlier: `incidents/$incidentId.tsx` uses no
`PageShell` at all and hardcodes `bg-white` (:98, :151), likely breaking dark theme.

**Recommended fix.** `src/components/common/EntityDetailPage.tsx`:

```tsx
<EntityDetailPage
  icon={Briefcase}
  backTo="/engagements"
  onRefresh={…}
  query={engagementQuery}              // renders skeleton / error / not-found automatically
  notFound={{ title: "Engagement not found", description: "…" }}
  hero={<EntityHero icon title badges meta />}
  rail={<EngagementRail …/>}
  actions={<Button>Edit</Button>}
>
  {(engagement) => <Tabs>…</Tabs>}
</EntityDetailPage>
```

Removes ~120 lines per page × ~12 pages; gives every page a real error state; brings the
incidents outlier into line.

**Acceptance criteria.**
- [ ] `contracts/$contractId.tsx` migrated first as the template; all classic-shape detail pages follow.
- [ ] Query errors show a retryable error state distinct from not-found on every detail page.
- [ ] `incidents/$incidentId.tsx` uses `PageShell`/scaffold; no hardcoded `bg-white`.

---

## CQ-B05 — RHF field wrappers: `TextField` / `SelectField` / `DateField` / `NumberField`

**Severity:** 🟡 Medium · **Effort:** M · **Status:** ⬜ Todo · **Owner:** — · **PR:** —

**Problem.** Every enum select is 20+ lines of `Controller → Select → SelectTrigger → SelectContent
→ map(SelectItem)`; 21 `Controller` instances across 9 sheets (~16 are this exact pattern —
`UserFormSheet` copy-pastes the language select twice *within the same file*, :173-190 vs
:276-293). Parallel per-file `X_VALUES as const` arrays restate what `types/enums.ts` owns.
Picker-backed fields register hidden `<Input type="hidden">`s (10 sites) to keep RHF tracking a
`setValue`-only field.

**Evidence.** `PersonFormSheet.tsx:368-389,462-482,500-517,556-573`, `UserFormSheet.tsx:143-160,
173-190,276-293`, `CampaignFormSheet.tsx:234-251,303-320,329-346`, `ContractFormSheet.tsx:245-262`,
`EngagementFormSheet.tsx:188-205`, `SurveyFormSheet.tsx:158-175`, `ClientFormSheet` ×2,
`ServiceFormSheet` ×2. Hidden inputs: `PersonFormSheet.tsx:414,497`, `ContractFormSheet.tsx:192`,
`EngagementFormSheet.tsx:156,295`, `CampaignFormSheet.tsx:176`, `SurveyFormSheet.tsx:131`,
`ServiceAssignmentFormSheet.tsx:132,149`, `ServiceSessionFormSheet.tsx:210,226,244`;
`UserFormSheet.tsx:267` registers a hidden email on an edit form that never sends it.

**Recommended fix.** `src/components/common/fields.tsx`: `TextField`, `SelectField`, `DateField`,
`NumberField` wrapping `FormField` + `Controller`/`register`, deriving `error` from
`useFormState({ name })` (kills the hand-threaded `error={errors.x?.message}` and `htmlFor`/`id`
pairs, ~60 occurrences). `SelectField` takes `options` + `getLabel`. Wrap pickers in `Controller`
(`EntityPickerField`) and delete every hidden input.

**Acceptance criteria.**
- [ ] Each enum select is 1–3 lines at call sites; ≤ 2 raw `Controller` usages remain (genuinely custom fields).
- [ ] `grep -rn 'type="hidden"' src/components` → 0.
- [ ] Option arrays sourced from `types/enums.ts` (or a shared options module), not per-file `*_VALUES`.

---

## CQ-B06 — Move `IconButton`, `ErrorState`, `ROW_BORDER` to `components/common`

**Severity:** 🟡 Medium · **Effort:** XS · **Status:** ✅ Done · **Owner:** Claude · **PR:** `1182cfc`

> Done: `components/common/IconButton.tsx`, `ErrorState.tsx`, `tableStyles.ts` created; 12/8/14 local copies removed; unused `RotateCw` imports cleaned. `grep "function IconButton\|function ErrorState\|const ROW_BORDER" src/routes` → 0. tsc + lint pass.

**Problem.** Verified by grep: `function IconButton` (identical 22 lines) in **12 files**;
`function ErrorState` (identical 13 lines) in **8 files**; `const ROW_BORDER` in **14 files**.

**Evidence.** IconButton: `users:394`, `industries:365`, `engagements:481`, `care-callbacks:366`,
`contracts:405`, `service-assignments:375`, `persons:431`, `tags:206`, `services:376`,
`service-sessions:455`, `clients:383`, `surveys:312` (all `routes/*/index.tsx`).
ErrorState: `users:380`, `service-assignments:361`, `clients:369`, `contracts:391`, `tags:312`,
`persons:417`, `services:362`, `service-sessions:441`.

**Recommended fix.** `components/common/IconButton.tsx`, `components/common/ErrorState.tsx`;
fold `ROW_BORDER` into the shared table row styles (or export from a table-styles module).
Mechanical, zero-risk, ~350 lines deleted. Do this before CQ-B01.

**Acceptance criteria.**
- [ ] `grep -rn "function IconButton\|function ErrorState\|const ROW_BORDER" src/routes` → 0.

---

## CQ-B07 — CRUD + lifecycle endpoint factories

**Severity:** 🟡 Medium · **Effort:** S · **Status:** 🟨 In progress · **Owner:** Claude · **PR:** `2b8960b`

> Done: `api/endpoints/_factory.ts` (`makeCrudEndpoints`, `makeLifecycleEndpoints`). Adopted CRUD in
> clients/services/contracts and full lifecycle in clients (exact body match). **Remaining:** users
> (no `update`, divergent lifecycle incl. `ban`), persons (no `update`, `deactivate` body differs),
> tenants (`create` returns a different type) — their lifecycle bodies (`{}` vs `undefined`) and verb
> subsets diverge, so adopting the factory there needs per-entity care to avoid changing payloads.

**Problem.** Four+ endpoint modules hand-write identical `create/getById/list/update` shapes plus
the lifecycle verb family (`activate/deactivate(reason?)/suspend(reason)/terminate(reason)/
archive/restore`) — each a one-liner differing only in entity type.

**Evidence.** `src/api/endpoints/clients.ts:34-130`, `users.ts:123-145`, `tenants.ts:94-112`,
`persons.ts:92-122`, `services.ts`, `contracts.ts`.

**Recommended fix.** `src/api/endpoints/_factory.ts`:

```ts
export const makeCrudEndpoints = <T, C, U, P extends ListParams = ListParams>(base: string) => ({
  create: (d: C) => apiClient.post<T>(`/${base}`, d),
  getById: (id: string) => apiClient.get<T>(`/${base}/${id}`),
  list: (p?: P) => apiClient.get<PaginatedResponse<T>>(`/${base}`, p),
  update: (id: string, d: U) => apiClient.patch<T>(`/${base}/${id}`, d),
})
export const makeLifecycleEndpoints = <T>(base: string) => ({ activate, deactivate, suspend, terminate, archive, restore })
```

Spread into each module; keep bespoke routes (setTier, verify, 2FA, stats) hand-written.
~250 lines deleted. Coordinate with CQ-A01 so factories build on correct paths.

**Acceptance criteria.**
- [ ] clients/users/tenants/persons/services/contracts compose the factories.
- [ ] No hand-written duplicate of a factory-provided method remains in those modules.

---

## CQ-B08 — Shared formatters: `nameInitials`, `formatDate(Time)`, `formatMoney`, datetime input helpers

**Severity:** 🟡 Medium · **Effort:** S · **Status:** ✅ Done · **Owner:** Claude · **PR:** `a58aa92`, `117e567`

> Done: `nameInitials` added to `lib/display.ts`; `lib/format.ts` created with `formatDate`/`formatDateTime`/`formatMoney`/`toLocalDatetimeInput`. Migrated 15 initials copies, 4 currency copies, 43 plain date calls. Remaining `toLocale*` sites are custom-format (preserved) or number formatting (not dates). tsc + lint pass.

**Problem.** The initials helper is redefined **12×** (components + routes, sometimes under
different names in the same shape) despite `lib/display.ts:40` already exporting `personInitials`
and its header declaring itself the single source of truth. `new Date(x).toLocaleDateString()/
toLocaleString()` appears **50+ times** across 22+ route files — while `User` has
`date_format`/`timezone` preferences that nothing honors. The currency string
`` `${currency ?? ""} ${amount.toLocaleString()}`.trim() `` is copy-pasted at
`contracts/$contractId.tsx:305,416`, `contracts/index.tsx:452`, `engagements/$engagementId.tsx:278`.
`formatRelativeTime`/`formatKpi` are stranded in `lib/dashboard.ts:74-98`. Datetime-input helpers
scattered: `toIsoDatetime`/`fromIsoDatetime` (`ContractFormSheet.tsx:72-82`), `toLocalDatetime`
(`ServiceSessionFormSheet.tsx:363-369`, also `service-sessions/$sessionId.tsx:824-830`).

**Recommended fix.** `src/lib/format.ts` (or extend `lib/display.ts`): `nameInitials(name)`,
`formatDate(iso)`, `formatDateTime(iso)`, `formatMoney(amount, currency?)`,
`formatRelativeTime`, `toIsoDatetime`/`fromIsoDatetime`/`toLocalDatetime`. Locale/timezone policy
then changes in one place; honoring user preferences becomes a one-file change later.

**Acceptance criteria.**
- [ ] `grep -rn "function.*[iI]nitial" src/routes src/components` → 0 (excluding lib).
- [ ] `grep -rn "toLocaleDateString\|toLocaleString" src/routes src/components` → 0.
- [ ] One currency formatter; one datetime-input helper set.

---

## CQ-B09 — Search-param helpers: `enumParam`, `listSearchSchema`, `enumOptions`, `useNewParamSheet`

**Severity:** 🟡 Medium · **Effort:** S · **Status:** 🟨 In progress · **Owner:** Claude · **PR:** `8efd351`

> Done: `lib/search-params.ts` with `enumParam`, `listSearchSchema`, `enumOptions`; contracts list
> adopted as the reference (removed its hand-enumerated `isStatus` guard and `STATUS_OPTIONS` array).
> **Remaining:** roll out to the other ~11 list pages and add `useNewParamSheet` — folded into the
> CQ-B01 `useListPage` migration (deferred there because `useNewParamSheet` needs a per-route literal
> id for TanStack's typed `useSearch`/`useNavigate`).

**Problem.** Every list page hand-rolls `validateSearch`: enum guards that manually enumerate every
member (break silently when a member is added — OCP violation), the literal
`if (search.new === "1" || search.new === true)` line in **10 files**, per-page
`STATUS_OPTIONS = [{ value: "all", … }]` arrays restating labels that `statusConfig` owns, and the
`?new=1 → open sheet → strip param` effect duplicated in 7 files (with the clients bug, CQ-A08).

**Evidence.** Guards: `engagements/index.tsx:48-67`, `service-sessions:52-60`, `contracts:53-62`,
`users:56-65`, `persons:52-59`, `clients:53-55`, `care-callbacks:49-57`, `tenants:49-56`, `surveys`.
Correct precedent: `providers/index.tsx:25-30` uses `Object.values(Enum).includes(v)`.
Options arrays: `engagements:88-95`, `contracts:75-83`, `users:78-86`, `service-sessions:83-90`,
`care-callbacks:70-77`, `tenants:70-76`. New-param effect: `engagements:119-124`,
`service-sessions:126-131`, `contracts:116-121`, `persons:120-125`, `users:120-125`,
`care-callbacks:90-95`, `tenants:101-106`.

**Recommended fix.** `src/lib/search-params.ts`: `enumParam(Enum)` via `Object.values`;
`listSearchSchema({ status: enumParam(ContractStatus), … })` producing the `validateSearch` fn
(always handling `new` + `search`); `enumOptions(Enum, allLabel)` deriving labels from
`getStatusLabel`. `src/hooks/useNewParamSheet.ts` returning `[open, setOpen]` with param stripping.

**Acceptance criteria.**
- [ ] No hand-enumerated enum guard in any `validateSearch`.
- [ ] `grep -rn 'search.new === "1"' src/routes` → 0.
- [ ] Adding an enum member requires no `validateSearch` change (spot-check one enum).

---

## CQ-B10 — `useLifecycleActions` hook + shared `ReasonDialog`

**Severity:** 🟡 Medium · **Effort:** M · **Status:** ⬜ Todo · **Owner:** — · **PR:** —

**Problem.** The same `setActionLoading → if/else over LifecycleAction → await refetch →
showSuccess → normalizeErrorMessage → finally` block is duplicated in **7 detail pages**. The only
reason-collecting dialog (`users/$userId.tsx:463-530`) is inline, non-reusable, and titles via a
3-level nested ternary (:475-481). `components/common/ConfirmDialog.tsx` exists but none of these
destructive flows use it. `LifecycleActions` (the buttons) is already shared — only the behavior isn't.

**Evidence.** `clients/$clientId.tsx:144-162`, `persons/$personId.tsx:166-184`,
`contracts/$contractId.tsx:116-138`, `users/$userId.tsx:112-131` (+ reason variant 146-167),
`services/$serviceId.tsx:106-115+`, `service-assignments/$assignmentId.tsx:93-102+`,
`service-sessions/$sessionId.tsx:132-156`.

**Recommended fix.**

```ts
const { onAction, loading, dialog } = useLifecycleActions({
  api: clientsApi,                      // entity-specific behavior injected, not switched on
  resource: "clients",
  reasonRequiredFor: ["terminate", "suspend"],  // opens shared ReasonDialog
  confirmFor: ["archive"],                      // uses existing ConfirmDialog
  onDone: () => refetch(),
})
```

Render `{dialog}` once per page. Unblocks CQ-A06 (real reasons).

**Acceptance criteria.**
- [ ] All 7 pages use the hook; both inline reason dialogs deleted.
- [ ] Destructive actions confirm via `ConfirmDialog`/`ReasonDialog`.
- [ ] One error-message helper on the toast path (`normalizeErrorMessage` — retire the mixed
      usage of `defaultErrorMessage` vs inline `err instanceof Error`).

---

## CQ-B11 — Shared zod helpers

**Severity:** 🟢 Low · **Effort:** S · **Status:** ⬜ Todo · **Owner:** — · **PR:** —

**Problem.** The same refinements are hand-rolled per schema with divergent semantics:
end-after-start date refine in 4 variants (string compare in `ContractFormSheet.tsx:54-57`
vs `Date.parse` in `CampaignFormSheet.tsx:52-55` vs `EngagementFormSheet.tsx:55-61`,
`SurveyFormSheet.tsx:43-46`); four slightly-different "positive number/integer" regexes
(`ContractFormSheet.tsx:40-44`, `EngagementFormSheet.tsx:44-52`, `CampaignFormSheet.tsx:56-64`,
`ServiceFormSheet.tsx:44-52`); "required-if-any-sibling-set" `superRefine` ×2
(`ClientFormSheet.tsx:49-62`, `PersonFormSheet.tsx:177-185`); ad-hoc email regexes
(`PersonFormSheet.tsx:160`, `ClientFormSheet.tsx:38`) instead of `z.email()` used elsewhere in the
same files.

**Recommended fix.** `src/lib/zod-helpers.ts`: `zPositiveIntString(msg?)`,
`zPositiveDecimalString(msg?)`, `zOptionalEmail()`, `dateRangeRefine(startKey, endKey)`,
`requiredGroup(keys, triggerKeys)`. Consider `z.coerce.number()` + `valueAsNumber` over
string-typed numeric fields.

**Acceptance criteria.**
- [ ] One date-range refine implementation with one comparison semantic.
- [ ] No ad-hoc email regexes; no per-file numeric regexes.

---

## CQ-B12 — `EntityLinkCard` + shared `Pill`

**Severity:** 🟢 Low · **Effort:** S · **Status:** ⬜ Todo · **Owner:** — · **PR:** — · **Depends on:** CQ-B08

**Problem.** The "entity link card" (avatar/initials + name + subtitle, bordered, hover) markup is
duplicated **20×** across 9 detail files — and inconsistently: some copies are `<Link>`s, some
plain divs (`service-sessions:385-401`). The verified/2FA/overdue pill markup is duplicated in 4+
files. IDs are rendered as `id.slice(0, 8)` mono-text instead of resolved names in contracts
(:325), persons (:362,373), service-sessions (:363,372).

**Evidence.** `service-sessions` ×5 (334-407, 537-578), `persons` ×3 (386-407, 550-589),
`service-assignments` ×3, `engagements` ×2 (325-347, 822-840), `users` ×2 (296-315, 596-615),
`worklist/$caseId` ×2, `contracts`, `campaignId`, `surveys` ×1. Pills: `users:549-560`,
`clients:467-472`, `engagements:264-269,423-428`, `persons:507-509`.

**Recommended fix.** `components/common/EntityLinkCard.tsx`
(`to/params`, `avatar` | `icon`, `title`, `subtitle`, `subtitleMono`) and a `Pill` chip component.
Optionally an `<EntityRef resource id />` that resolves + links, replacing `id.slice(0, 8)`.

**Acceptance criteria.**
- [ ] All 20 card copies replaced; consistent link behavior.
- [ ] Pills use the shared component.

---

## CQ-B13 — Dedupe fixture wiring

**Severity:** 🟢 Low · **Effort:** XS · **Status:** ⬜ Todo · **Owner:** — · **PR:** — · **Depends on:** CQ-A02

**Problem.** `function useFixture()` is copy-pasted **7×** (identical body, different env var);
`function paginate<T>()` copy-pasted **3×** (`care-callbacks.ts:37`, `engagements.ts:38`,
`surveys.ts:33`); every method repeats the `if (useFixture()) … else …` branch ~10× per file.

**Recommended fix.** `src/api/endpoints/_shared.ts`: `makeFixtureToggle(name)` and one `paginate`;
optionally a `fixtureBacked(flag, fixtureImpl, liveImpl)` factory that picks the whole
implementation object once instead of per-method branching.

**Acceptance criteria.**
- [ ] One `paginate`; one toggle factory; per-method `if (useFixture())` branches eliminated or
      reduced to the factory pattern.
