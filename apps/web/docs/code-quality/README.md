# Code Quality Backlog — Evexia UI

> Source: full SOLID/DRY review of `src/` (2026-07-14, ~278 files / ~49k lines).
> Scope: frontend only (`evexia/`). Each ticket lives in its track file with evidence,
> recommended fix, and acceptance criteria.

## How to use this backlog

1. Pick a ticket (respect **Depends on** — waves below give a safe order).
2. Create a branch: `refactor/<ticket-id>-short-slug` (e.g. `refactor/cq-b02-detail-primitives`).
3. Set the ticket **Status** to `🟨 In progress` (here and in the ticket body) and add your name.
4. Do the work; meet every **Acceptance criteria** checkbox in the ticket.
5. Open a PR titled `[CQ-XXX] <ticket title>`; link it in the **PR** column.
6. On merge, set Status to `✅ Done` and check the ticket's criteria boxes.

**Definition of Done (applies to every ticket)**
- All acceptance criteria checked.
- `pnpm lint` and `pnpm test` pass; `pnpm build` succeeds.
- No new copies of the pattern the ticket removes (grep evidence in PR description).
- Behavior-preserving unless the ticket says otherwise; any intentional behavior change called out in the PR.

**Status legend:** ⬜ Todo · 🟨 In progress · ✅ Done · 🚫 Won't do (add reason in ticket)

---

## Dashboard

### Track A — Correctness & Safety ([A-correctness.md](./A-correctness.md))

| ID | Title | Severity | Effort | Depends on | Status | Owner | PR |
|----|-------|----------|--------|------------|--------|-------|----|
| CQ-A01 | Live-mode API paths (`/v1/*`) don't exist in backend schema | 🔴 Critical | M | — | ⬜ | | |
| CQ-A02 | Fixtures default ON; crisis rules live in fixture files | 🔴 Critical | M | — | ⬜ | | |
| CQ-A03 | Query-key split-brain (`['user']` vs `['users','detail']`) + central `queryKeys` | 🟠 High | S | — | 🟨 | Claude | `dc91516` |
| CQ-A04 | Client-side filters silently applied over server-paginated data | 🟠 High | M | — | ⬜ | | |
| CQ-A05 | Entity-by-id resolved via `search` param hack; missing `getById` usage | 🟠 High | M | — | ⬜ | | |
| CQ-A06 | Hardcoded audit reasons, fake-user fallback, hardcoded completion data | 🟡 Medium | S | CQ-B10 | ⬜ | | |
| CQ-A07 | `api/client.ts`: triplicated 401-retry, dead 5xx retry, `getBlob` error bypass | 🟠 High | M | — | ⬜ | | |
| CQ-A08 | `clients` list never strips `?new=1` (sheet reopens on back/refresh) | 🟢 Low | XS | — | ✅ | Claude | `48ac3b3` |
| CQ-A09 | Missing/inconsistent error states on client-filtered list pages | 🟡 Medium | S | CQ-B01 | ⬜ | | |

### Track B — DRY Consolidations ([B-dry.md](./B-dry.md))

| ID | Title | Severity | Effort | Depends on | Status | Owner | PR |
|----|-------|----------|--------|------------|--------|-------|----|
| CQ-B01 | `useListPage` hook + `EntityListView` — kill the ~400-line list-page template (~12 pages) | 🟠 High | L | CQ-B06, CQ-B09 | 🟨 | Claude | `ddcbb46`, `859cb3f` |
| CQ-B02 | Extract `DetailPrimitives` (`DetailCard`/`RailSection`/`Stat`/`DetailGrid`/`DetailRow`) — 10+ copies | 🟠 High | S | — | ✅ | Claude | `a72df1f` |
| CQ-B03 | Generic `EntityPicker<T>` + `LockedEntitySummary` — 9 picker copies (~1,250 lines) | 🟠 High | M | CQ-A05 | ⬜ | | |
| CQ-B04 | `EntityDetailPage` scaffold — loading/not-found/header/hero/8-4 grid chrome (11+ pages) | 🟠 High | L | CQ-B02, CQ-B08 | ⬜ | | |
| CQ-B05 | RHF field wrappers `TextField`/`SelectField`/`DateField` — 20+ Controller+Select copies | 🟡 Medium | M | — | ⬜ | | |
| CQ-B06 | Move `IconButton` (×12), `ErrorState` (×8), `ROW_BORDER` (×14) to `components/common` | 🟡 Medium | XS | — | ✅ | Claude | `1182cfc` |
| CQ-B07 | `makeCrudEndpoints` / `makeLifecycleEndpoints` factories in `api/endpoints` | 🟡 Medium | S | — | 🟨 | Claude | `2b8960b` |
| CQ-B08 | Shared formatters: `nameInitials`, `formatDate(Time)`, `formatMoney`, datetime input helpers | 🟡 Medium | S | — | ✅ | Claude | `a58aa92` |
| CQ-B09 | Search-param helpers: `enumParam`, `listSearchSchema`, `enumOptions`, `useNewParamSheet` | 🟡 Medium | S | — | 🟨 | Claude | `8efd351` |
| CQ-B10 | `useLifecycleActions` hook + shared `ReasonDialog` — 7 copies of the action switch | 🟡 Medium | M | — | ⬜ | | |
| CQ-B11 | Shared zod helpers: date-range refine, numeric-string coercion, required-group | 🟢 Low | S | — | ⬜ | | |
| CQ-B12 | `EntityLinkCard` (20 copies) + shared `Pill` chip | 🟢 Low | S | CQ-B08 | ⬜ | | |
| CQ-B13 | Dedupe fixture wiring: `makeFixtureToggle`, shared `paginate` | 🟢 Low | XS | CQ-A02 | ⬜ | | |

### Track C — SOLID / Architecture ([C-solid.md](./C-solid.md))

| ID | Title | Severity | Effort | Depends on | Status | Owner | PR |
|----|-------|----------|--------|------------|--------|-------|----|
| CQ-C01 | Converge on TanStack Query: migrate 7 manual-fetch detail pages to `useEntityDetail` | 🟠 High | L | CQ-A03 | ⬜ | | |
| CQ-C02 | Split god detail routes into feature folders (route = composition only) | 🟡 Medium | L | CQ-B02, CQ-B04 | ⬜ | | |
| CQ-C03 | Split `PersonFormSheet` by subtype/mode; move save orchestration to API layer | 🟡 Medium | M | CQ-B03, CQ-B05 | ⬜ | | |
| CQ-C04 | Alias hand-written `types/entities.ts` / `enums.ts` to generated OpenAPI types | 🟠 High | M | CQ-A01 | ⬜ | | |
| CQ-C05 | Enforce `StatusBadge`/`statusConfig`; delete 3 local status-pill implementations | 🟡 Medium | S | — | ✅ | Claude | `f814866` |
| CQ-C06 | Type list-filter params in endpoints; remove `as Record<string, unknown>` casts | 🟡 Medium | S | CQ-A04 | ⬜ | | |
| CQ-C07 | Zod schemas ↔ generated request types: `satisfies`/typed `parsePayload` everywhere | 🟡 Medium | S | CQ-C04 | ⬜ | | |
| CQ-C08 | `SheetForm` dirty-state discard guard via existing `ConfirmDialog` | 🟡 Medium | S | — | ⬜ | | |

### Track D — Cleanup & Dead Code ([D-cleanup.md](./D-cleanup.md))

| ID | Title | Severity | Effort | Depends on | Status | Owner | PR |
|----|-------|----------|--------|------------|--------|-------|----|
| CQ-D01 | Delete legacy theme system (`src/theme/`); single dark-mode flag | 🟡 Medium | M | — | ⬜ | | |
| CQ-D02 | Delete dead code: `useRequireAuth`, `route-auth.ts`, `useModal`, unused `uiSlice` state, stale `api/index.ts` barrel | 🟢 Low | XS | — | ✅ | Claude | `9da91f2` |
| CQ-D03 | Move prototype/mock code out of prod trees (`inbox.tsx`, `QueryTable.tsx`) | 🟡 Medium | S | — | ⬜ | | |
| CQ-D04 | Wire up or delete decorative UI (Export buttons, no-op filters, selection checkboxes, dead `timeRange`) | 🟢 Low | S | CQ-B01 | ⬜ | | |
| CQ-D05 | Small DRY sweep: `isCookieAuth`, auth bootstrap dedupe, `unwrapItems`, statusConfig/statusColors merge, `goToLogin`, `LANGUAGE_OPTIONS`, currency default | 🟢 Low | S | — | ⬜ | | |
| CQ-D06 | Fix dropped form fields: session `notes`/`diagnosis` collected but never sent | 🟡 Medium | S | — | ⬜ | | |

---

## Suggested execution waves

| Wave | Tickets | Theme |
|------|---------|-------|
| **1 — Safety** | CQ-A01, CQ-A02, CQ-A03, CQ-A07 | Ship-blocking correctness; nothing else depends on UI refactors |
| **2 — Mechanical extractions** | CQ-B02, CQ-B06, CQ-B08, CQ-B13, CQ-D02 | Zero-behavior-change moves; deletes ~1,700 lines; unblocks scaffolds |
| **3 — Scaffolds** | CQ-B09 → CQ-B01 (migrate `contracts` first as template), CQ-B04, CQ-A04/CQ-A09 fixed during migration | List + detail page templates |
| **4 — Data layer convergence** | CQ-C01, CQ-C04, CQ-C06, CQ-B07, CQ-A05 → CQ-B03 | One fetch paradigm, typed params, generated types |
| **5 — Forms & lifecycle** | CQ-B05, CQ-B10 → CQ-A06, CQ-C03, CQ-C07, CQ-C08, CQ-B11, CQ-D06 | Form stack consolidation |
| **6 — Polish** | CQ-C02, CQ-C05, CQ-B12, CQ-D01, CQ-D03, CQ-D04, CQ-D05 | Feature folders, theme cleanup, dead UI |

## What is already good (do not regress)

These are the codebase's standards — new code must use them, and tickets consolidate *toward* them:

- `lib/queries.ts` — `useEntityList` / `useEntityDetail` / `useEntityMutation` + key helpers.
- Form stack: `hooks/useApiForm.ts` → `hooks/useEntityFormSheet.ts` → `components/common/SheetForm.tsx` / `FormField` / `FormSection`.
- `types/api.ts` `ApiError` + `lib/errors.ts` + `client.ts` `parseError` normalization.
- `lib/storage.ts` namespaced storage discipline.
- `components/common/`: `PageShell`, `Tabs` + `useTabSearchParam`, `EmptyState`, `FilterBar`, `StatusBadge` + `utils/statusConfig.ts`, `TableSkeleton`, `Pagination`, `SortHeader`, `ConfirmDialog`.
- `UserFormSheet` split (separate Create/Edit components) and `PricingConfig` discriminated-union dispatch — the OCP patterns to copy.
