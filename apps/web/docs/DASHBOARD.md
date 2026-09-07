# Dashboard design record

Date: 2026-09-08. Scope: the home dashboard (`DashboardMain`) and the
aggregate endpoint behind it (`GET /dashboard`).

## The choice

The dashboard leads with decisions, then delivery analytics:

1. **KPI strip** — sessions in the window (delta vs the prior window,
   sparkline), clients served, covered members with roster coverage, import
   backlog.
2. **Needs attention** — the decision panel. Each row is an action, its
   consequence, and a link to where it is done, ranked by severity then size.
   Derived from figures already on the page, so it cannot disagree with them.
3. **Delivery** — one window control scoping every chart below it: sessions
   over time (stacked area by delivery type), top 5 clients, category donut,
   services in demand, import health.

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

## Chart-form decisions

- **Area, not columns, for sessions delivered.** The question was asked
  directly. For one measure at a fixed monthly granularity, columns win:
  discrete periods, easier magnitude comparison. Two things changed that
  here. The series now carries a Physical/Online composition, and the window
  control varies bucket count from 7 to 31 and density from daily to monthly.
  A stacked band keeps composition legible across that whole span, where
  stacked columns thin to slivers at 31 daily buckets. One form is used at
  every window rather than switching shape, so the chart does not appear to
  change meaning when the range changes.
- **A band with no data is not drawn.** An all-zero series still strokes a
  line along the top of the stack, which reads as a flat series rather than
  an absent one. Bands are filtered on the data, and the legend follows.
- **Import health is a part-to-whole composition, not ranked bars.** The
  earlier bar list failed on dynamic range: 6,444 next to 2 on a shared
  length scale renders everything but the largest reason invisible. The batch
  is now one composition bar (accepted / already held / blocked) with the
  blocked reasons below carrying a share of the blocked total instead of a
  length. Share stays readable across three orders of magnitude.
- **Top clients put label, bar and value in one row**, so the card reads as a
  bar chart rather than a stacked list, capped at five.
- **Category is an active donut**: hovering or focusing a slice lifts it and
  writes its label and count into the ring. The legend carries every count
  and share, so identity never rests on colour.
- **Card headers are a single line.** Title, then the figures that would
  otherwise be a subtitle, then the control. No prose restating what the
  marks already show.

## Colour

Chart series use a fixed categorical order in `--chart-1..4`, plus
`--chart-muted` for an absent value and `--chart-good` / `--chart-serious`
for the import composition, which is state rather than identity. Both themes
were run through the dataviz validator:

- 4-slot set, light: all checks pass; worst adjacent CVD ΔE 9.1, normal-vision
  22.9. Slots 3 and 4 fall below 3:1 on the light surface, so charts using
  them ship visible labels and counts (the relief rule).
- 4-slot set, dark: all checks pass including contrast.
- 2-hue area set: all checks pass in both modes.

Series colour follows the entity, not its rank, so filtering never repaints
the survivors.

## Decisions and their reasons

- **Delivered means status Completed and not soft-deleted.** Scheduled
  bookings are a pipeline, not delivery; the seed data holds only Completed.
- **Flow figures follow the window; stock figures do not.** Sessions, the
  groupings and the service trends are scoped to the selected range. Covered
  members and the import backlog count what stands today and carry no range,
  because a "members added this week" figure would answer a different
  question than the one the card asks.
- **Bucket size is derived, never requested.** Day up to 31 days, week up to
  120, month beyond, so a long window cannot ask for a bucket per day.
- **A service with no prior sessions shows "new", not a percentage.** A rise
  from zero has no percentage to state; printing 100% would be invented.
- **Import backlog is scoped to the latest non-abandoned batch.** The same
  file is staged repeatedly as reference data improves; summing across
  batches would double-count. An abandoned batch's rows are dead.
- **Bucketing is UTC.** `date_trunc` on a timestamptz buckets by the
  connection's timezone, which shifted boundary sessions a month; the query
  normalizes with `timezone('UTC', ...)` first.
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

- `apps/api/tests/e2e/test_dashboard_api.py`: 5 cases passing, covering the
  aggregate, tenant scoping, preset re-bucketing, a custom range, and the
  rejection of a custom range with no start.
- Route queries executed against the dev database across every preset; the
  series, groupings, service trends and KPIs matched psql-derived figures.
- Web: `pnpm test` (700 tests), `pnpm lint`, `pnpm typecheck` all pass.
- Driven in headless Chromium against the dev server: light and dark renders,
  the area tooltip showing the per-type split, the window control re-scoping
  every card, and the donut's active slice writing into the ring.
- The DEV fixture apportions its groupings from the window total, and a test
  asserts no subset outruns the whole. The earlier fixture scaled each
  grouping independently and showed 99 top-client sessions against a window
  total of 80, an invariant the API never produces.
