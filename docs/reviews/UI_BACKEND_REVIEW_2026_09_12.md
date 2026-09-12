# UI and backend review, 12 September 2026

Status: review and recommendations only. No application fixes or deployment performed.
Source baseline: `9f0466cd`; concurrent import work was present initially and was
committed by its owner during this review. This review does not evaluate those changes.

## Scope and evidence

Reviewed the running local landing and sign-in screens, and sampled current source
for dashboard, sessions, members/practitioner redesign records, practitioner list,
reports, audit, branding and authentication. Read the corresponding API paths for
session authorization/serialization and dashboard aggregation. Queried the local
audit outbox health endpoint. This is not an exhaustive security or module audit.

Browser observations are distinguished from source findings below. No production
environment, database migration, full role matrix, clinical read audit persistence,
or accessibility conformance audit was tested. Earlier review counts are historical,
not current tenant measurements. Credentials are deliberately absent from this record.

Authenticated browser inspection could not be completed: sign-in returned the same
generic expiry message using both native and form-aware input. Credential escaping
clarification was requested; no password reset, account mutation or access bypass was
attempted. Dashboard and internal-page findings are source-based, not visual sign-off.

The graft CLI was not available on PATH and no graft MCP tools were available.
Checked-in graft cards located relevant source; current source established findings.
ListAgents/SendMessage were unavailable. Only this new review document is committed;
no existing shared implementation or migration document is edited.

## Findings, ordered by priority

Priority is engineering judgement: P1 should precede release claims about the affected
capability; P2 should precede declaring that workflow complete; P3 is visual polish.

### R1. P1: Session reads expose clinical content without a clinical-scope check

Source verified. `apps/api/app/core/authorization.py:425` loads a session and checks
tenant ownership, but not clinical scope. List reads use `require_same_tenant` at
`apps/api/app/api/routes/service_sessions.py:878`. The response mapper at `:142`
unconditionally returns notes, feedback, issue topic, diagnoses, partner information
and clinical outcome. The router has no clinical guard at `:123`; the application
dependency at `apps/api/app/main.py:110` blocks Viewer writes, not these reads.
The detail endpoint at `service_sessions.py:1084` uses the same tenant-only loader.

Impact: same-tenant authorization does not establish permission to see clinical
content. This is a source finding, not a claim of a production disclosure.

Recommended change: separate a minimal operational session projection from clinical
detail, apply clinical scope before returning sensitive fields, and audit clinical
reads through a durable path. Cover list, detail, member/provider/service history,
chain, awaiting-confirmation and mutation responses rather than fixing one URL.
Retain operational scheduling access only to fields allowed by the agreed policy.
This follows the unresolved Q2 in `docs/design/PAGES_REDESIGN.md`; it does not claim
the product owner has approved a new permission design in this review.

Acceptance: synthetic HTTP tests for no-scope, employer-scope, clinical-scope and
wrong-tenant users; inspect response fields and persisted read-audit records.
Owner role: backend access-control owner with sessions owner.

### R2. P1: The local audit outbox is materially behind

Live observation: `GET http://localhost:8000/health/outbox` returned
`status=behind`, `depth=3582`, `failed=0`, `lag_seconds=368352`,
`max_lag_seconds=3600` during this review. The observed lag is about 4.3 days.
`apps/api/app/main.py:168` classifies this as unhealthy and `:176` returns 503.
Zero failed rows does not mean delivery is healthy. This finding applies to the local
instance only; production supervision was not inspected. The root cause was not
established, so a stopped worker is a hypothesis, not a diagnosis.

Recommended change: investigate and supervise the outbox worker, monitor this existing
health endpoint, and verify a new synthetic event reaches `audit_logs`. Resolve the
backlog through the normal consumer with idempotency checks. Do not delete or silently
rewrite audit history. Existing context: `docs/reviews/AUDIT_COVERAGE.md`.

Acceptance: healthy probe, bounded oldest-event age, persisted event with correct
occurrence time, and recovery verified after worker interruption. Owner role: operations
and audit backend owner. This review does not start a background worker or drain data.

### R3. P2: A failed dashboard request can report that nothing is blocked

Source verified. `apps/web/src/components/DashboardMain.tsx:59` supplies an empty
attention array when no dashboard data exists; `:86` passes loading but not error.
`apps/web/src/components/dashboard/AttentionCard.tsx:248` interprets an empty array
after loading as "Nothing is blocked." The upcoming card also remains a skeleton
when aggregate data is unavailable (`UpcomingBookingsCard.tsx:112`). Its separate
session query has no error branch before rendering rows.

Recommended change: propagate error and freshness to every dependent card, show a
retry action and unavailable state, and label retained stale data. Reserve the positive
empty state for a successful response. Do not replace unavailable counts with zero.

Acceptance: reject the aggregate request and the week-ahead request independently;
neither failure renders an all-clear message or a permanent loading state. Owner role:
dashboard frontend owner.

### R4. P2: Upcoming bookings are filtered after the page limit

Source verified. `apps/web/src/components/dashboard/UpcomingBookingsCard.tsx:62`
requests 20 sessions without a status filter, then `:75` removes everything except
Scheduled/Rescheduled. If the first 20 chronological rows are cancelled or completed,
a later valid booking will be absent even though the aggregate reports it.

Recommended change: filter booking statuses server-side before ordering/limiting and
use the same time window for the header count and rows. Add a bounded operational
projection or support repeated statuses on the existing list endpoint. The "more"
link should preserve the same window/status filters.

Acceptance: 20 excluded rows followed by an eligible booking still show the booking;
count, visible rows and linked queue agree. Owner role: dashboard and sessions API owners.

### R5. P2: Session search is a nonfunctional control

Source verified. `apps/web/src/routes/service-sessions/index.tsx:198` sends
`search: activeSearch` and `:320` offers "Search sessions". The server handler at
`apps/api/app/api/routes/service_sessions.py:875` has no search parameter and passes
none to list/count queries. Its docstring promises searching, but its signature does not.

Recommended change: implement a bounded server search over approved operational fields
(for example service, client and practitioner display names), using identical predicates
for rows and total; or remove the control until this works. Do not implicitly enable
free-text clinical-note search under an operational permission.

Acceptance: matching/nonmatching queries change both items and total; pagination, sort
and tenant isolation hold. Owner role: sessions frontend/backend owners.

### R6. P2: Dashboard advice states causes that its inputs do not establish

Source verified in `apps/web/src/components/dashboard/AttentionCard.tsx`:

- `:112` says importing rosters "unblocks" the entire import backlog whenever any
  client lacks a roster. The total backlog does not identify which rows that fixes.
- `:184` derives a share from session counts but `:191` calls it revenue concentration.
  Different session rates mean those are not interchangeable.
- `:213` says demand shifted to other services when one service declines; a decline
  alone does not establish substitution or even demand rather than recorded delivery.

Recommended change: state the measured fact, such as "share of recorded sessions" and
"fewer recorded sessions than the prior period". Link each action to the exact filtered
queue. Add reason-specific backlog counts only when those causes are represented in
the backend. Avoid parallel frontend business rules for readiness and eligibility.

Acceptance: a synthetic non-roster backlog never claims roster repair will clear it;
session share is never described as revenue share without a monetary calculation.
Owner role: dashboard frontend owner; backend owner for reason-coded aggregates.

### R7. P2: Sign-in failure copy describes a session that never existed

Browser observed during a sign-in attempt: "Your session has expired. Please sign in
again." Source: `apps/web/src/lib/errors.ts:77` maps every 401 to that message.
The login endpoint also uses 401 for invalid tenant/credentials
(`apps/api/app/api/routes/auth.py:217`). The reason this particular credential attempt
failed was not established by that generic message.

Recommended change: context-specific login error, "We couldn't sign you in. Check your
tenant code, email and password." Keep the same response for unknown tenant/user and
incorrect password. Preserve separate lockout/rate-limit guidance and reserve expiry
copy for an existing authenticated session.

Acceptance: failed initial login, expired session and locked account render distinct
appropriate guidance without revealing whether an account exists. Owner role: auth UI owner.

### R8. P2: Public assurance copy is stronger than the verified capability

Browser observed and source verified: `apps/web/src/components/landing/LandingPage.tsx:22`
promises every read, edit and escalation is recorded. The sampled session GET handlers
return through read-only paths with no read-audit call, and R2 shows delayed delivery in
the local environment. `apps/web/src/routes/audit.tsx:15` is still a coming-soon screen.
The placeholder alone does not prove the backend lacks auditing; R1/R2 describe the
specific gaps. Immutability was not tested and should not be asserted as a verified fact.

Recommended change: describe the actual scoped controls and recorded lifecycle changes
until the broader guarantees pass explicit tests. Build the audit console on the existing
read API with actor, entity, action and date filters, redacted changes, and occurrence
time distinguished from processing time where relevant.

Acceptance: published assurance maps to passing evidence; audit UI cannot reveal clinical
values through change details. Owner role: product/copy owner and audit UI/backend owners.

### R9. P3: Landing timeline annotations overlap at intermediate width

Browser observed at an approximately 661px-wide content viewport: the 02:14 and 09:40
annotation labels overlap. `apps/web/src/components/landing/DutyLog.tsx:109` positions
all chips on one absolute row, showing them from the small breakpoint, despite the chart
losing width to its legend.

Recommended change: stagger labels or switch to the already-present text event list
until there is enough chart width. Retain the chart's accessible text description.
Acceptance: inspect 390, 640, 768 and 1280px widths and enlarged text; annotation boxes
do not overlap or leave the chart. Owner role: landing frontend owner.

## Recommended next UI pass

These are design judgements, not measured user preferences or newly adopted policy.
The product owner should confirm priority and terminology when implementation is assigned.

1. Keep the current visual direction. The landing page has a clear type hierarchy and
   distinctive brand treatment. The implementation now includes an aggregate dashboard,
   a decision panel, session chains and entity history. Prioritize reliability of those
   workflows over another wholesale restyle.
2. Put the dashboard time range at page level. It affects several KPIs/charts but is
   nested inside SessionsAreaCard (`DashboardMain.tsx:79`). Explicitly label current
   roster/pipeline figures separately from period delivery figures. The header's "today"
   copy should not imply every tile covers today.
3. Make attention rows deep links to the work they describe: awaiting confirmation,
   missing rates, pending practitioners, expiring contracts. Keep counts and predicates
   in the same API contract. An aggregate followed by an unfiltered list wastes context.
4. Complete the practitioner directory's readiness framing already proposed in
   `docs/design/PAGES_REDESIGN.md`. The current list remains tier/region/panel/accreditation
   oriented (`apps/web/src/routes/providers/index.tsx:102`). Separate booking eligibility
   from profile completeness, and obtain list readiness in a batch, not one request per row.
5. Preserve list context across detail/edit/back: URL-backed search, sort, selected filters
   and meaningful return links. Use the member master-detail pattern as a starting point
   only where it suits the workflow, not for every record type.
6. Give compact list headers a responsive action policy. `PageShell.tsx:51` keeps a
   shrinking title beside nonshrinking actions (`:81`). Move secondary actions to a menu
   and allow a second row on narrow screens. This is a source-based layout risk needing
   authenticated viewport verification, not an observed mobile overflow finding.
7. Complete tenant branding as a real setting if still desired: preview, upload, remove
   and reset to default, preserving image aspect ratio. The sidebar still reads a fixed
   `/evexia.png` (`AppSidebar.tsx:18`); the tenant form exposes only a creation-time
   branding checkbox (`TenantFormSheet.tsx:250`). Add tenant-owned asset metadata/storage,
   validation and authorized upload first. Keep favicon separate, consistent with the
   earlier request. Do not represent the boolean as a working logo override.

## Backend priorities beyond individual fixes

- Expand the existing route-authentication inventory into a role/tenant/scope matrix.
  Authentication coverage is progress, but it cannot establish field-level privacy or
  authorized writes. Prioritize session projections and all alternate read paths.
- Keep dashboard metrics explicitly defined. `dashboard-insights.ts:76` divides period
  sessions by the current Active roster (`dashboard_query_runner.py:143`), not historical
  eligible member-time. Label that basis; if reporting needs historical utilisation,
  agree the denominator and implement it server-side. Do not present this as a verified
  industry standard or silently change the metric in the client.
- Prefer filtered, bounded list/read models for dashboard queues and readiness. Avoid
  client-side filtering after pagination and avoid N+1 readiness requests. Performance
  budgets and database indexes should follow query plans and measured latency; neither
  production load nor query plans were evaluated here.
- Keep report maturity explicit. The renewal pack is now demo-only in the catalogue
  (`reports/index.tsx:39`), with a prominent sample-data banner in
  `PerClientRenewalPack.tsx:17`. Next, bind it to real tenant/client/period output before
  promoting it. Do not reopen the old finding that it is currently labelled ready.
- Treat worker supervision, lag monitoring and persisted audit verification as a release
  capability alongside the API/web processes. Keep imports on their existing authorized
  path; this review does not prescribe changes to the concurrent import implementation.

## Progress worth retaining

Source-confirmed improvements relative to earlier documents: logout calls
`resetIdentityState()` (`auth-store.ts:163`); renewal reports are explicitly demo;
session detail uses `EntityActivityPanel` (`service-sessions/$sessionId.tsx:290`);
session response hydration now includes display names; dashboard clinical outcome mix
is explicitly scope-gated (`apps/api/app/api/routes/dashboard.py:404`). These are
specific improvements, not a blanket claim that the full modules are verified.

## Verification performed

- Frontend: 32 tests passed across DashboardMain, dashboard-insights,
  sessions-happy and reports (four files).
- Backend: three `tests/unit/api/test_route_authorization.py` tests passed.
- Frontend run emitted Recharts zero-size warnings in jsdom. This does not establish
  a browser layout failure. Follow-up: give chart test containers dimensions if these
  tests need layout assertions; do not suppress unrelated runtime warnings blindly.
- Live local outbox probe and browser observations as described above.
- Full build, full suite, production deployment, tenant permission matrix, and load
  tests were not run. Passing existing tests does not close the listed findings.

Suggested implementation sequence: R1/R2 first; R3-R7 for trustworthy operational
workflows; audit console and practitioner readiness; responsive polish and tenant branding.
Each item above has an acceptance check and owner role for the next assigned task.
