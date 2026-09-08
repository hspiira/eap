# Dashboard roadmap — handoff guidance

Written 2026-09-08 as a handoff. Audience: any agent or developer extending
the dashboard. Read `DASHBOARD.md` first; it records what exists, why, and
the conventions. This file records what to build next, ranked by business
value, with the evidence, the blockers, and the acceptance gates per item.

Evidence below was measured against the development database (`evexia_db`,
local Postgres) on 2026-09-08. Re-verify counts before building; the import
pipeline changes them.

## Ground rules for any agent working here

These are not suggestions; the existing code enforces or assumes them.

1. **Extend the aggregate, do not fan out.** New figures go into
   `GET /dashboard` (`apps/api/app/api/routes/dashboard.py`, schemas in
   `app/api/schemas/dashboard_schemas.py`). One request drives the page.
   After schema changes run `pnpm contracts:sync` in `apps/web` and add the
   new types to `src/api/generated/index.ts` (hand-maintained barrel).
2. **No dashboard fixtures.** The endpoint is real; sample data goes in
   `apps/web/src/test/dashboard.ts` (`makeDashboard(overrides)`), never in
   `src/api/endpoints/`. See DASHBOARD.md "The dashboard has no fixture
   path" for the reasoning.
3. **Flow vs stock.** Anything that is a rate over time follows the window
   control (`range` param, `ResolvedRange`); anything that counts what
   stands today does not. Do not window a stock figure.
4. **Timezone.** Any date_trunc on `scheduled_at` must go through
   `_utc_scheduled_at()` (normalize to UTC before truncating) or it buckets
   by connection timezone. This bug already happened once.
5. **Charts.** Series colours come from `--chart-1..4` tokens only
   (`src/theme/tokens-light.css` / `tokens-dark.css`), assigned by identity
   in fixed order, never cycled. New palettes must pass the dataviz
   validator in both themes before use. Bands in the sessions chart are
   overlaid, not stacked (a stacked upper line reads as the total). Card
   headers are one line: title, inline figures, control — no subtitles.
6. **Derived advice is guarded.** Signals in
   `src/components/dashboard/AttentionCard.tsx` never fire under 10 window
   sessions, never quote a percentage off a prior window under 3 sessions,
   and a rise from zero is "new", never a percentage. Follow the same
   pattern for new signals; name every threshold as a constant.
7. **Tests and checks before commit.** API:
   `uv run pytest tests/e2e/test_dashboard_api.py` (needs local Postgres,
   `eap_test` db). Web: `pnpm test`, `pnpm lint`, `pnpm typecheck`.
   Then render it: start the API (`uv run uvicorn app.main:app --port 8000`)
   and web (`VITE_AUTH_USE_COOKIES=false pnpm dev`), mint a token with
   `create_access_token` for the user in `users`, put it in
   `localStorage["evexia.auth"]`, and screenshot both themes. Look at the
   screenshot; the suite does not catch layout or misreadable charts.
8. **Commits**: by path, no attribution trailers, several agents share this
   tree. Announce dashboard-path work via ListAgents/SendMessage first.

## Tier 1 — computable from data that exists today

### R1. Revenue (highest value, build first)

- **What**: monthly revenue series, revenue per client, average rate per
  service, and an "unbilled" figure (completed sessions with null
  `rate_ugx`).
- **Evidence**: `rate_ugx` set on 208/369 completed sessions; monthly sums
  are real (2026-07: 3,900,000 UGX over 15 rated sessions; 2026-08:
  3,125,000 over 11). 161 sessions carry no rate — that count is already on
  the dashboard as a data-quality queue.
- **How**: add a `revenue` block to the aggregate (windowed series + top
  clients by revenue + unbilled count). Sum server-side; never average over
  nulls silently — report rated-session count beside any average.
- **Gate**: figures must state coverage ("from N rated sessions") wherever
  rates are partial. Do not present a sum of 56% of sessions as total
  revenue without saying so.

### R2. Client dormancy / renewal risk

- **What**: clients whose last completed session is older than a threshold,
  with last-session date and their trend vs their prior window. This is the
  account-management call sheet.
- **Evidence**: 20 of 35 clients with any sessions have none in 120+ days.
- **How**: stock figure (not windowed): per client `max(scheduled_at)` where
  completed and not deleted. Add as a list card or as high-signal rows in
  the attention panel ("Stanbic Bank quiet for 5 months"). Threshold is a
  policy decision: name it as a constant, default 120 days, note it in
  DASHBOARD.md.

### R3. Practitioner load and key-person risk

- **What**: sessions per practitioner in the window; concentration signal
  when the top practitioner exceeds a share threshold.
- **Evidence**: top practitioner delivered 86/369 all-time (23%); top two
  37%; only 12 practitioners active in the last 90 days of 113 registered.
- **How**: windowed grouping joined to `providers.display_name`, same shape
  as `_top_clients`. Add a concentration signal mirroring the client one
  (same guards). Careful: provider names are personal data — this view is
  for the tenant's own console, fine; do not put practitioner names into
  logs or error messages.

### R4. Clinical continuity per service

- **What**: continued vs closed vs referred per service in the window.
- **Evidence**: outcomes are dominated by ToBeContinued everywhere
  (Family Therapy 31 continued vs 3 completed; Health Talk 50 vs 23). But
  186/369 sessions have no outcome at all.
- **Gate**: ship only with the null share visible (e.g. "of N sessions with
  a recorded outcome"); the existing "record outcomes" queue is what makes
  this view converge. A continuity chart hiding 50% missing data would lie.

### R5. New vs repeat split

- **What**: small split of windowed sessions by `client_type`.
- **Evidence**: 200 Repeat / 165 New / 4 null. Cheap; could ride inside the
  sessions card header as a third inline stat rather than a new card.

## Tier 2 — build ready, fills as data improves

### R6. Utilisation rate (the industry KPI)

- **What**: distinct members served ÷ covered members, per client. This is
  the number client HR teams renew on.
- **Blocker**: only 1/369 sessions carries `member_id`; the historical
  import quarantines unresolved identities rather than guessing (a
  deliberate rule — see CLAUDE.md provider-module rules; do not weaken it).
  It becomes real as rosters land and batches re-stage.
- **How**: compute per client `count(distinct member_id)` over windowed
  sessions ÷ active members. Show explicitly how many sessions are
  member-linked ("based on N identified sessions") so early numbers are not
  mistaken for the truth. Wire it now; it self-heals as imports resolve.

### R7. Contract utilisation

- **Blocker**: `contracts` has 1 row, `eap_programmes` (entitlements) 0.
  Do not build until contracts are captured; there is nothing to divide by.

### R8. Booking lag / responsiveness

- **Blocker**: history was imported, so `created_at` ≈ import time, not
  booking time. Only meaningful for sessions created through the live
  booking flow — filter to `import_source_id IS NULL` when building it.

## Tier 3 — the artifact that earns renewals

### R9. Per-client scorecard export

- **What**: a quarterly per-client report (utilisation, sessions by
  category, outcomes, coverage) an account manager sends to the client's HR.
  The dashboard serves the operator; this serves the people who pay.
- **How**: reuse the aggregate queries with a `client_id` filter; the empty
  `report_templates` / `report_runs` tables are the intended home. Assume
  nothing about layout — this is a judgement call recorded in DASHBOARD.md
  as unconfirmed: **whoever owns client relationships must confirm the
  scorecard's content before it is built.**

## Explicitly not worth building (measured, not opinion)

- Dependant/demographic splits: all 3,305 members are relation=Employee.
- Duration analytics: `duration` set on 1/369 sessions.
- Survey/NPS widgets: `survey_campaigns`, `survey_responses` empty.
- Incident widgets: `critical_incidents` empty (this is why the old
  dashboard was rebuilt; do not reintroduce dead tiles).

Revisit each if its table starts filling.

## Open findings inherited from the rebuild

- `audit_logs` is empty although `audit_change` is called from many routes.
  Verify the audit write path persists before resurfacing any activity feed.
- `attendance`, `delivery_context`, `issue_topic`, `headcount` on imported
  sessions look like import defaults (e.g. 368/369 CompanyWide). Confirm
  against the source workbook before building anything on them.
- The range filter resets on reload; putting it in the URL would make
  filtered views shareable. Small, unclaimed.
