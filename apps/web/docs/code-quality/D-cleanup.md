# Track D — Cleanup & Dead Code

Dead code, prototype leakage, decorative UI, and small consolidations. Line numbers as of
2026-07-14 (`main` @ `066f1db`).

---

## CQ-D01 — Delete the legacy theme system

**Severity:** 🟡 Medium · **Effort:** M · **Status:** ⬜ Todo · **Owner:** — · **PR:** —

**Problem.** Two complete theme systems ship simultaneously: `src/theme/**` (legacy palette→token,
keyed on `[data-theme="dark"]`) and `src/styles/theme/**` (semantic tokens, keyed on `.dark`).
`styles.css:2-5` imports both; `hooks/useThemeEffect.ts:22-23` sets **both** DOM flags because each
system keys off a different selector. The two dark palettes independently define overlapping
surface/border values (`--token-surface: #171717` in `theme/themes/evexia-dark.css:12` vs
`--surface → #171717` in `styles/theme/tokens-dark.css`) — same colors maintained twice,
guaranteed to drift. `styles.css:16-21` admits it ("Legacy palette tokens — retained for backwards
compatibility… on collision, the later block wins"), and `theme/README.md` still documents the
legacy system as *the* system.

**Recommended fix.**
1. Grep for legacy consumers (`bg-safe|text-natural|nurturing|palette-`), port to semantic tokens.
2. Delete `src/theme/` entirely; drop the `data-theme` attribute from `useThemeEffect`; update the README.
3. Until done: lint ban on new `--palette-*` consumers.

**Acceptance criteria.**
- [ ] `src/theme/` deleted; one CSS token system; one dark-mode DOM flag.
- [ ] Visual regression pass on light + dark for 5 representative pages.

---

## CQ-D02 — Delete dead code

**Severity:** 🟢 Low · **Effort:** XS · **Status:** ✅ Done · **Owner:** Claude · **PR:** `9da91f2`

> Done: deleted `hooks/useRequireAuth.ts`, `lib/route-auth.ts`, `hooks/useModal.ts`, `api/index.ts` (all verified zero-consumer); trimmed `uiSlice` to theme-only. tsc + `vite build` pass.

**Problem.** Verified zero-consumer modules (grep):
- `src/hooks/useRequireAuth.ts` (22 lines) — never imported; live guard is `components/common/RequireAuth.tsx`.
- `src/lib/route-auth.ts` `requireAuthBeforeLoad` (32 lines) — never imported, and broken by
  design in cookie mode (checks `apiClient.getToken()`, always null when `VITE_AUTH_USE_COOKIES=true`).
- `src/hooks/useModal.ts` — never imported.
- `src/store/slices/uiSlice.ts:17-28` — `activeModal`/`globalLoading`/`openModal`/`closeModal`/
  `setGlobalLoading` have zero consumers; only `theme`/`setTheme` are used.
- `src/api/index.ts` barrel exports only auth/users/tenants ("Other endpoints will be exported
  here") while all consumers import `@/api/endpoints/*` directly — a misleading half-abstraction.

**Recommended fix.** Delete the three modules; trim `uiSlice` to theme; complete or delete the
barrel (recommend delete — direct endpoint imports are the established convention).

**Acceptance criteria.**
- [ ] Files deleted; `tsc` and `pnpm build` pass.
- [ ] `uiSlice` exposes only consumed state.

---

## CQ-D03 — Move prototype/mock code out of production trees

**Severity:** 🟡 Medium · **Effort:** S · **Status:** ⬜ Todo · **Owner:** — · **PR:** —

**Problem.** Prototype code ships in real trees where it gets copied as a pattern:
- `src/routes/inbox.tsx` — 781 lines of `MOCK_RULES` with 2017 dates, dept tabs, platform cards.
- `src/components/common/QueryTable.tsx` — mock `AtRiskRow` data, hardcoded `TOTAL_MOCK = 200`,
  and its own fourth badge style (:100-117) — sitting in `components/common` masquerading as reusable.

**Recommended fix.** Either delete, or move behind a clearly-labeled `src/prototypes/` (excluded
from `components/common`), or convert to real implementations. At minimum, nothing mock-backed may
live in `components/common/` or an unflagged route.

**Acceptance criteria.**
- [ ] `components/common/` contains no mock-data components.
- [ ] `inbox.tsx` deleted, converted, or explicitly flagged as a prototype route.

---

## CQ-D04 — Wire up or delete decorative UI

**Severity:** 🟢 Low · **Effort:** S · **Status:** ⬜ Todo · **Owner:** — · **PR:** — · **Depends on:** CQ-B01

**Problem.** Non-functional UI copy-pasted across all list pages:
- `FilterButton` options passed without `onSelect` in every page (`FilterBar.tsx:43-69` supports
  it; e.g. `engagements:174-180`, `clients:160-167`, `users:177-182`) — dropdowns that do nothing.
- `IconButton label="Export" icon={Download}` with no `onClick` in all 12 pages.
- Select-all/row `Checkbox`es with no selection state in every table.
- `clients/index.tsx:91,180-186` — `timeRange` filter rendered and settable but never used in any
  query or filter (dead filter).

**Recommended fix.** Decide per feature: implement (bulk selection, export) or remove. Do it in
the shared `EntityListView` (CQ-B01) so the decision applies everywhere at once. Delete the
`timeRange` dead state now.

**Acceptance criteria.**
- [ ] Every rendered control does something, or is removed.
- [ ] `timeRange` dead state deleted.

---

## CQ-D05 — Small DRY sweep (infrastructure)

**Severity:** 🟢 Low · **Effort:** S · **Status:** ⬜ Todo · **Owner:** — · **PR:** —

**Problem / fixes (one PR, mechanical).**
1. `useCookies()` env check duplicated 3×: `api/client.ts:20-22`, `store/slices/authSlice.ts:14-19`,
   `lib/auth-store.ts:14-16` → one `isCookieAuth()` in a shared env module.
2. Auth bootstrap flows duplicated: `lib/auth-store.ts` `bootstrapFromHash` (:84-106) and
   `bootstrapFromCookies` (:113-136) share an identical `me → setAuth → setTenantId → load tenant`
   block; `login` (:44-53) repeats the tenant-load a third time → extract
   `hydrateSessionFromMe()` / `loadTenantContext(tenantId)`.
3. Response-shape normalization `Array.isArray(res) ? res : res.items ?? []` at `clients.ts:160-161`
   and `persons.ts:174-178` → `unwrapItems<T>()`.
4. `utils/statusConfig.ts` wraps `utils/statusColors.ts` but both are public API → merge (see CQ-C05);
   fix duplicated `'cancelled'` literal at `statusColors.ts:81-82`.
5. `lib/` vs `utils/` split is arbitrary (error helpers in `lib/errors.ts` but
   `utils/globalErrorHandler.ts`; validators in `utils/`) → pick one directory, document in README.
6. Logout-navigate search-params block repeated in `useSessionTimeout.ts:19-25`, `RequireAuth`,
   (dead) `useRequireAuth` → `goToLogin(navigate, redirect?)` helper.
7. `LANGUAGE_OPTIONS` duplicated: `UserFormSheet.tsx:27-37` vs `PersonFormSheet.tsx:85-95` → move
   next to the enum.
8. Currency default inconsistency: `EMPTY.currency = "KES"` (`ContractFormSheet.tsx:66`) vs
   `"UGX"` (`EngagementFormSheet.tsx:73`) — confirm intent with product; centralize the default.

**Acceptance criteria.**
- [ ] Each of the 8 items done or explicitly waived with a reason noted here.

---

## CQ-D06 — Fix dropped form fields (session notes/diagnosis)

**Severity:** 🟡 Medium · **Effort:** S · **Status:** ⬜ Todo · **Owner:** — · **PR:** —

**Problem.** `ServiceSessionFormSheet.tsx:39,335-343` collects `notes` and
`diagnosis_id`/`diagnosis_text`, but `parsePayload` (:123-134) silently drops them — users type
notes that are never sent. Also `:149` hardcodes `duration: 60` with a TODO to read from the
selected Service's `duration_minutes`.

**Recommended fix.** Wire notes/diagnosis to the appropriate follow-up calls (or remove the fields
until the BE supports them — silently swallowing user input is the worst option). Default duration
from the selected Service.

**Acceptance criteria.**
- [ ] Every field rendered in the sheet is either sent to the BE or removed.
- [ ] Duration defaults from the selected Service, editable by the user.
