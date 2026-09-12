# UI and backend execution plan, 12 September 2026

Status: planning complete. Application changes, runtime verification and deployment
have not started under this plan.

Source review: [UI_BACKEND_REVIEW_2026_09_12.md](UI_BACKEND_REVIEW_2026_09_12.md).
Planning baseline: `92ef7194`. Owner roles below describe responsibility, not assigned
agents. This plan covers R1-R9; the broader UI proposals are a separately scoped queue.

## Review assessment

Accept the review's distinction between source findings, local observations and
unverified production behaviour. Accept R1/R2 as release blockers for clinical-access
and durable-audit claims, and R3-R7 as operational correctness work before polish.

Current source sampling reconfirms the unguarded session projection
(`apps/api/app/api/routes/service_sessions.py:142`), absent search and single-status
list contract (`:875`), missing dashboard error propagation
(`apps/web/src/components/DashboardMain.tsx:86`), filtering after pagination
(`apps/web/src/components/dashboard/UpcomingBookingsCard.tsx:62`), and generic 401
copy (`apps/web/src/lib/errors.ts:77`). Other findings retain the source review's
evidence status; this planning pass did not independently reproduce every finding.
The outbox measurement is historical local evidence and must be measured again.

Reject deferring all of R8 until the audit console: the current landing assurances
still promise every read is recorded and clinical notes stay with their owners
(`apps/web/src/components/landing/LandingPage.tsx:22`), while R1 documents tenant-only
clinical responses. Split R8 into immediate copy correction and later console work.
This ordering is engineering judgement, not a new product permission policy.

One extension to R1's acceptance criteria is necessary: projection redaction alone
does not close inference paths. The list accepts `clinical_outcome` as a filter and
sort field (`apps/api/app/api/routes/service_sessions.py:857,888`). Include those
operations, counts and aggregates in the permission inventory and scope gate.

## Execution decisions and dependencies

- Use small commits by work package. Recheck the tree and path ownership before
  editing; use graft call graphs before changing shared symbols or multiple files.
- Resolve R1's field policy before implementing its response contract. Q2 explicitly
  leaves owner confirmation outstanding in
  `docs/design/PAGES_REDESIGN.md:397`. The product owner, with the access-control
  owner, must confirm the operational field allowlist, who receives clinical scope,
  and whether identifiable individual-session metadata belongs in employer views.
  Do not assume role names or tenant membership imply clinical entitlement.
- Proposed R1 implementation: one shared authorization-aware projection policy,
  with minimal operational responses and explicit clinical access. Prefer existing
  scope machinery over a new role system. Define denied versus omitted fields in
  OpenAPI so clients do not mistake withheld values for missing clinical data.
- Proposed read-audit policy: persist a durable event before releasing clinical
  content; fail the clinical response if enqueue fails. Record actor, tenant,
  resource identifiers, action and occurrence time, never clinical values. Confirm
  batch-read granularity and failure behaviour with the policy decision above.
  Delivery can remain asynchronous through the existing outbox.
- R2 investigation, R8 copy correction, R3, R6 and R7 do not depend on resolving
  that policy. R4/R5 contract work follows R1 to avoid building against a projection
  that will immediately change. R8 console follows R1/R2 verification.
- No new branding infrastructure, report engine or provider migration belongs in
  the R1-R9 corrective pass. These remain visible in the follow-on queue below.

## Work packages

### 1. Correct assurance copy (R8a)

Owner: product/copy and landing frontend roles. Dependency: none.

Replace unsupported universal auditing, immutability and clinician-ownership
guarantees with scoped statements supported by existing evidence. Check the whole
assurance block for claims needing evidence; remove or qualify unsupported claims
without substituting new guarantees. This does not establish backend compliance.

Gate: each retained assurance has a concrete evidence reference in this handoff;
inspect the rendered landing page for copy and layout. Commit separately so this
correction does not wait for the console.

### 2. Restore and verify audit delivery (R2)

Owner: operations and audit backend roles. Dependency: none for investigation.

Recheck `/health/outbox` and inspect worker configuration, process supervision,
database connectivity and delivery errors. Establish the cause before changing
startup configuration. Integrate the worker with the actual supported local and
deployment process managers and monitor the existing lag probe. Record environment
and commands in `docs/reviews/AUDIT_COVERAGE.md`; do not infer production state from dev.

Drain through the normal consumer after diagnosis. Do not delete or rewrite history.
Use synthetic events and a disposable database for interruption and replay tests.

Gate: a synthetic event reaches `audit_logs` with its original occurrence time;
reprocessing does not duplicate it; interrupt/restart recovery succeeds; the probe
becomes healthy with oldest-event age below the configured threshold. Record before
and after measurements and actual runtime supervision evidence separately from code.

### 3. Close session clinical-access paths (R1)

Owner: access-control and sessions backend roles, with sessions frontend support.
Dependency: confirmed field/scope policy; R2 must pass before durable-delivery claims.

Inventory list, detail, member/provider/service histories, chains,
awaiting-confirmation, mutation responses and any other session serializers. Map
their callers before editing the shared mapper. Include clinical filters, sorting,
counts, aggregates and audit-history details. Reuse shared policy rather than
endpoint-specific field removal. Keep clinical values out of ordinary audit payloads.

Add the durable clinical-read event path with explicit transaction semantics; a
read-only decorator must not silently roll back the enqueue. Adapt frontend display,
types and query caches so identity/scope changes cannot retain privileged content.
Preserve historical practitioner attribution and the existing import mutation path.

Gate: synthetic HTTP tests cover no scope, employer scope, clinical scope and wrong
tenant across every inventoried path, including mutation responses and inference
filters. Assert actual serialized fields and database-persisted read events, enqueue
failure behaviour and rollback, not just mocked helper calls. Check operational
scheduling remains usable within the approved allowlist. Regenerate API contracts.
Record the policy and closure evidence in the sessions handoff and this plan.

### 4. Make dashboard states and advice trustworthy (R3, R6)

Owner: dashboard frontend role. Dependency: none for state and copy fixes.

Propagate loading, error, retained-data freshness and retry behaviour to every
aggregate-dependent card. Handle the independent week-ahead request separately.
Allow positive empty states only after success, and never replace unavailable
counts with zero. Label retained data after refetch failure.

Replace unsupported causal advice with measured facts: recorded-session share,
recorded-session change, and separately described roster and import issues.
Do not invent reason-coded aggregates. Preserve queue filters where supported;
finish upcoming-queue linking with package 5.

Gate: aggregate and week-ahead failures independently produce actionable unavailable
states without all-clear copy or permanent skeletons. Cover stale refetch, successful
empty data and non-roster backlog fixtures. Confirm no session-based metric is called
revenue and no decline implies demand moved elsewhere.

### 5. Make session queues and search agree (R4, R5)

Owner: sessions API and dashboard/sessions frontend roles. Dependency: package 3's
approved projection contract. Deliver status/window filtering, then search, as
separate commits with synchronized API/frontend changes.

Extend the existing list contract to accept repeated statuses while preserving the
single-status form. Apply filters before ordering and pagination, with identical
predicates for items and total. Use one explicit time window and boundary convention
for upcoming count, rows and the linked queue; preserve it in URL-backed filters.

Implement bounded server search over policy-approved operational display fields.
Share the search predicate between list and count, retain tenant constraints and
stable pagination, and treat SQL wildcard characters deliberately. Clinical notes
are excluded. Avoid joins that duplicate sessions or require per-row queries.

Gate: 20 excluded sessions followed by an eligible booking still returns the booking;
status/window boundaries, count and destination queue agree on a fixed fixture.
Matching and nonmatching search changes both items and totals; test pagination,
sorting, wildcard input and cross-tenant names. Regenerate API contracts and run
sessions/dashboard integration tests. Measure query plans before adding indexes.

### 6. Distinguish login failure from expiry (R7)

Owner: authentication frontend role. Dependency: none.

Use login-context error mapping for invalid credentials, retaining generic wording
across unknown tenant, unknown user and wrong password. Preserve lockout/rate-limit
guidance and authenticated-session expiry handling.

Gate: initial failure, existing-session expiry, lockout and rate limit each render
appropriate guidance; unknown identities produce indistinguishable login copy.
Use synthetic test credentials, with no resets or real-account mutations.

### 7. Complete the audit console and responsive correction (R8b, R9)

Owner: audit API/UI and landing frontend roles. Dependencies: R8b follows packages
2/3; R9 is independent and may be delivered earlier in its own commit.

Build the console against the existing audit read API with authorized tenant scope,
actor/entity/action/date filters, pagination and redacted change details. Confirm
API support before adding UI filters. Clearly distinguish occurrence and processing
time if both are available; never synthesize a missing processing timestamp.

Gate for R8b: role/tenant HTTP tests and UI tests cover filtered results, pagination,
empty/error states and redaction, including session-related audit entries. Verify
persisted synthetic events appear with the correct occurrence time.

For R9, stagger timeline labels or use the existing text list when chart space is
insufficient. Preserve the accessible description. Gate: browser inspection at
390, 640, 768 and 1280px, including the reported approximately 661px content width,
and enlarged text. Labels stay inside the chart without overlap.

## Verification and delivery protocol

For each package, record commit, exact commands, pass/fail/skip results and remaining
limitations here. Mark implemented, tested and deployed separately. Existing review
test results are baseline evidence only and do not close new acceptance gates.

- Backend: start with affected tests under `apps/api` using `uv run pytest`; clinical
  and audit work also requires PostgreSQL integration tests. Existing audit suites
  are `tests/integration/test_audit_chain.py` and `test_audit_chain_gaps.py`. Inspect
  their fixture requirements; `AUDIT_CHAIN_TEST_DATABASE_URL` is required by the
  latter. A skipped suite leaves its gate open.
- Frontend: use `pnpm --filter @evexia/web test` with affected test paths, including
  DashboardMain, dashboard-insights, sessions-happy and login-happy where relevant.
  Add meaningful regressions for the failures specified above.
- After API contracts change, run `pnpm contracts` and review generated diffs.
  Before declaring the corrective pass complete, run `pnpm verify` and
  `pnpm --filter @evexia/web build`, plus the explicit database and browser gates.
  Unit coverage and a successful build cannot replace those gates.
- Obtain an authorized authenticated test session for internal browser verification.
  The previous sign-in failure leaves that check pending, not passed. Do not log
  credentials or use real clinical content as fixtures.
- Deployment is a separate action: capture target-environment smoke tests, worker
  supervision and outbox health after deployment before marking deployed.

## Follow-on queue, outside the corrective pass

1. Practitioner readiness directory: follow `docs/migrations/PROVIDERS_MIGRATION.md`
   and the adopted detail-page decisions. Batch eligibility, separate profile
   completeness, and preserve provider identity and historical affiliations.
2. Dashboard range and metric labels: move range to page level, distinguish current
   roster from period delivery, and retain the stated current-roster denominator
   unless a historical metric is explicitly agreed. Complete other filtered links.
3. List context and responsive actions: URL-backed filters/search/sort, useful return
   links and narrow-screen action layout. Verify authenticated viewports first.
4. Tenant branding: confirm it is still desired before scoping tenant-owned assets,
   authorized validation/storage, preview/remove/reset and separate favicon handling.
5. Real renewal reporting: retain demo labelling until tenant/client/period data and
   output reconciliation are implemented and verified.

These entries preserve the review's recommendations without treating optional
product work as a dependency of the nine corrective findings.

## Current evidence ledger

- Planning: source review read; selected current source and Q2 checked at `92ef7194`.
- R1: field policy confirmed by the product owner, 2026-09-12 (see
  `docs/design/PAGES_REDESIGN.md:397` for the prior Q2 answer this restates),
  and implemented. Clinical set: `notes`, `feedback`, `issue_topic`,
  `partner_name`, `partner_relationship`, `diagnosis_type_id`,
  `diagnosis_id`, `clinical_outcome`, nulled without `AccessScope.CLINICAL`
  across all 7 read paths plus mutation responses; `clinical_outcome` as a
  list filter/sort now needs the scope (422 otherwise). Read-audit event
  added (VIEW/LIST, ids and count only) on `@transactional()` routes so a
  failed enqueue fails the response; `ServiceSession` added to
  `SECURITY_SENSITIVE_RESOURCES` so it is never sampled out. Frontend
  `NotesCard` gated to match `ClinicalCard`; outcome filter/sort hidden
  without scope. Full details, an unreconciled `members.py` block-vs-redact
  inconsistency found on the way, and the deliberately out-of-scope write
  side: `docs/handoffs/SESSIONS_IMPLEMENTATION.md`. Verified: 9 new e2e scope
  cases, full `tests/unit` (2336) and `tests/e2e` pass, `pnpm contracts`
  regenerated, frontend `pnpm test` (854) and typecheck pass. Not verified:
  production deployment.
- R8a: implemented and committed (`04123e4a`). Landing assurance copy scoped
  to encryption, lifecycle logging and archival; audit-console and universal
  claims removed. `pnpm --filter @evexia/web typecheck` clean.
- R7: implemented and committed (`8c9e1d3f`). Login-scoped `errorMessage`
  override in `useApiForm`; failed login no longer claims a session expired.
  851 frontend tests pass; typecheck clean.
- R9: implemented and committed (`d84a9af8`). Duty-log chips deferred to
  `lg:` (1024px); verified with Playwright screenshots at 390/640/661/768/
  1023/1280px and 1280px at 125% zoom, no overlap at any width.
- R2: investigated, partially closed. `pnpm dev` now also starts the outbox
  worker (package.json). Local `evexia_db`'s worker path verified healthy
  (synthetic event delivered in 1.4s with correct `occurred_at`; interrupt/
  restart recovery confirmed via the pre-existing `com.evexia.outbox-worker`
  launchd supervision; 20 existing integration tests pass fresh). The
  2026-09-12 review's `depth=3582` reading was not reproduced and its target
  database was not confirmed; root cause is recorded as a probable
  environment mismatch, not verified, in
  `docs/reviews/AUDIT_COVERAGE.md`. Production worker supervision still
  unconfirmed. Not tested: production. Not deployed.
- Tested: see each package above; no `pnpm verify` / full build run yet this
  pass.
- Deployed: none.
- Pending decision: none blocking for R1-R9 as scoped. A dev-database safety
  guard (recommended in `AUDIT_COVERAGE.md`'s R2 section) is a separate,
  unimplemented follow-up for whoever owns deployment configuration.
