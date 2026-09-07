# Dashboard design record

Date: 2026-09-08. Scope: the home dashboard (`DashboardMain`) and the
aggregate endpoint behind it (`GET /dashboard`).

## The choice

The dashboard leads with delivery and operational work queues instead of
entity totals:

- KPI strip: sessions delivered in 90 days (with delta and sparkline),
  clients served, covered members with roster coverage, import backlog.
- Main column: monthly sessions trend, sessions by client, sessions by
  category, and an import-health card with per-outcome resolution queues.
- Right rail: quick actions and derived data-quality queues. The onboarding
  checklist appears only for a tenant with no clients.

One aggregate endpoint (`apps/api/app/api/routes/dashboard.py`) replaces the
previous fan-out of six `limit=1` list calls.

## Why

Evidence from the development database (evexia_db, profiled 2026-09-07):

- The old KPIs were mostly dead: critical_incidents 0 rows, contracts 1,
  service_assignments 0, audit_logs 0. Half the page rendered zeros.
- The data with depth was invisible: 369 completed sessions across
  24 months, 3,305 eligible members (5 of 42 clients with rosters),
  29,884 staged import rows of which only 368 accepted, 112 of 113
  practitioners pending.
- The largest actionable queues were import-resolution outcomes:
  UnresolvedMember 6,444 and MissingPractitioner 637 in the latest applied
  batch.

## Decisions and their reasons

- **Delivered means status Completed and not soft-deleted.** Scheduled
  bookings are a pipeline, not delivery; the seed data holds only Completed.
- **Import backlog is scoped to the latest non-abandoned batch.** The same
  file is staged repeatedly as reference data improves; summing across
  batches would double-count. An abandoned batch's rows are dead.
- **Month bucketing is UTC.** `date_trunc` on a timestamptz buckets by the
  connection's timezone, which shifted boundary sessions a month; the query
  normalizes with `timezone('UTC', ...)` first.
- **Charts are single-hue.** Every chart compares magnitude (columns, ranked
  bars), so the brand hue on a lighter same-ramp track is used throughout and
  no categorical palette exists to validate. Status tones (warning) mark the
  import and data-quality queues, always with icon and label, never colour
  alone.
- **The activity feed was removed from the dashboard.** It mapped
  `audit_logs`, which has 0 rows, so it could only ever show an empty state.
  The component (`ActivityFeedCard`) remains for the design showcase and can
  return once audit writes populate the table.

## Assumptions (not verified data)

- The dev snapshot is representative of production shape. Confirm before
  treating the layout as final; the queries themselves are shape-agnostic.
- Session `attendance` (368/369 CompanyWide), `delivery_context` (368/369
  Unknown), `issue_topic` and `headcount` (all null) look like import
  defaults, so no widget is built on them. Someone who knows the source
  workbook should confirm.

## Unresolved findings

- `audit_logs` is empty although `audit_change` is called from many routes
  (apps/api/app/shared/utils/route_audit_helper.py). Not investigated here.
  Follow-up: verify the audit write path persists, then decide whether the
  activity feed returns to the dashboard.
- Clinical outcome is null on 186 of 369 completed sessions, so no outcome
  widget was built; the gap is surfaced in the data-quality card instead.

## Verification

- `apps/api/tests/e2e/test_dashboard_api.py`: seeded aggregate and empty
  tenant cases, including tenant scoping, both passing.
- Route queries executed against the dev database matched the psql-derived
  figures (monthly series, queues, KPIs).
- Web: `pnpm test` (696 tests), `pnpm lint`, `pnpm typecheck` all pass;
  light and dark renders and the chart hover tooltip verified in headless
  Chromium against the dev server with fixtures.
