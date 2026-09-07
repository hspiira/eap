# Module repair plan: backend and frontend

Reviewed 2026-09-06 against `e672b6f` on `chore/monorepo`. Status: findings
recorded; fixes are not implemented by this review. This document covers the EAP
application outside the active provider migration. Revalidate affected files
against the provider integration branch before implementing a repair.

Use `PROVIDERS_MIGRATION.md` for provider decisions and ownership. Keep the
existing member and service migration records as their respective sources of
truth. This plan does not reopen their accepted identity or taxonomy decisions.

## Outcome and scope

Access control needs attention before additional modules are enabled. Synthetic
requests through the actual FastAPI app demonstrated unauthenticated report
reads, cross-tenant reads, and cross-tenant writes by a Viewer. Frontend probes
also reproduced retained query-cache data after logout and live response-shape
mismatches. These are executable defects, not recommendations based on style.

Reviewed paths span authentication and tenant state, cases and clinical notes,
programmes, care callbacks, surveys, engagements, critical incidents, reports,
pricing/contracts, benchmark consent, and DSAR. The clients surface was sampled
for integration context; no claim is made that every client workflow was audited.
Home navigation and feature flags were checked to distinguish intentional
rollout restrictions from missing implementation.

This is a targeted cross-module review, not an exhaustive security audit. User
invitation/SSO internals, documents and file storage, KPI calculations, every
client importer/merge path, and every database migration still require dedicated
reviews. No real tenant data, production credentials, or source session records
were used. No browser-rendered flows were verified in this review.

### Evidence levels

- **Reproduced:** an API or frontend diagnostic executed with synthetic data.
  API probes used the real app and dependency injection with mock repositories
  and sessions. They establish route behaviour, not production database state.
- **Source verified:** the cited implementation establishes the issue, but its
  complete database/browser flow was not executed here.
- **Follow-up verification:** a plausible issue requiring its named check before
  it is promoted to a confirmed defect.

P1 findings block release of the affected endpoints or operational outputs.
P2 findings block claiming the affected workflow is complete. Priorities are
engineering judgments based on the cited failure modes, not measured incident
frequency. No finding asserts that a production breach occurred.

## Decisions for the repairs

1. Authentication, tenant ownership, operational role, and clinical scope are
   separate gates. Enforce all required gates server-side before reading or
   changing the target entity. Hidden navigation is not an authorization gate.
2. Standardize tenant-owned entity loads through scoped repository operations
   and typed route dependencies. Do not add another ad hoc coroutine check.
   Use the tenant from authenticated context, not from an untrusted body.
3. Viewers cannot mutate. Clinical scope does not itself grant write permission.
   Restrict pricing changes and execution of DSAR operations to tenant Admins;
   preserve any stricter existing privacy policy. A separate self-service DSAR
   workflow would require verified subject binding and is outside this repair.
4. A change of authenticated identity must cancel/remove the previous query
   cache before rendering the next workspace. Treat logout, expiry, SSO and
   failed authentication consistently, including in-flight responses.
5. A report labelled ready must use real, tenant/client-scoped data. Demo data
   must be explicitly labelled and unavailable as an ordinary production report.
   An unavailable dataset must not look like zero activity or successful output.
6. Survey aggregates expose only approved categorical answers. Free text is not
   made anonymous by counting it. Apply the existing small-cell policy to every
   employer-facing aggregate surface, including labels and totals where needed.
7. Use one list-envelope contract with server pagination, filters and totals for
   growing collections. Generate frontend types from the API; do not declare a
   different response shape through a TypeScript generic.
8. Survey setup will require the provider's form ID and a server-generated secret
   revealed once on creation, with Admin-only rotation. Never return the secret
   in ordinary list/detail responses. This resolves the contradictory existing
   frontend promise and backend input contract.
9. Complete backend and frontend together for each module. Keep intentionally
   disabled modules disabled until their permission and live-contract gates pass.
   Do not build supplier contracting or revive non-compete work under this plan.

## P1: release blockers

### SEC-01: Report templates and results can be read without authentication

**Evidence: reproduced.** `GET /reports/templates/{template_id}` and
`GET /reports/runs/{run_id}` returned 200 with a synthetic tenant-B record when
no authentication header or current-user override was supplied. Their route
and repository dependencies do not require a user or scope the lookup by tenant.

Sources: `apps/api/app/api/routes/reports.py:175` and `:222`;
`apps/api/app/api/dependencies/reporting.py:16` and `:26`.

**Repair, owner: backend access-control owner.** Require authenticated,
tenant-scoped loads for templates and materialized results. Review list, create,
run and read permissions as one contract. Materialization does not remove the
need to authorize each later read. Keep private report parameters and narratives
inside the same boundary as the numeric output.

**Frontend:** report viewers must distinguish 401, unavailable/not-found, and
failed generation. Clear protected report caches when identity changes.

**Close only when:** anonymous reads return 401; another tenant cannot read a
known ID; an authorized same-tenant user can read the intended report; a
materialized output cannot be fetched through an unguarded alternate route.

### SEC-02: Twelve tenant checks never execute

**Evidence: reproduced and exhaustive source search.** `require_same_tenant`
is async and takes `(tenant_id, current_user)`. Twelve routes call it as
`require_same_tenant(current_user, resource.tenant_id.value)` without awaiting
it. Adding `await` alone would still leave the arguments reversed.

Source: `apps/api/app/core/authorization.py:153`. A graft search for
`require_same_tenant\(current_user` in `apps/api/app/api/routes/` found:

- `benchmark.py:106`: withdrawal of consent.
- `cases.py:142` and `clinical_notes.py:185`: case and case-note reads.
- `dsar.py:130`, `:181`, `:203`, `:238`: export, cancellation, erasure, detail.
- `eap_programmes.py:164`: programme detail.
- `engagements.py:153`, `:172`: engagement detail and summary.
- `surveys.py:134`, `:196`: campaign detail and aggregate.

A tenant-A Viewer received tenant-B engagement and survey details with 200.
The two reads emitted unawaited-coroutine warnings. The other listed routes
were source inspected, not executed against real subjects or clinical data.

**Repair, owner: backend access-control owner.** Replace these calls with the
standard scoped resource dependency or explicit scoped load before any use case
runs. Preserve clinical-scope requirements in addition to tenant ownership.
For consent and DSAR mutations, validate ownership before any change or collector
call, not after obtaining a mutated result.

**Frontend:** maintain capability-based UI, but do not treat hiding a control as
the repair. Clinical details must never be preloaded for an unauthorized context.

**Close only when:** every listed route has cross-tenant rejection coverage,
mutations invoke no save/collector/tombstoner on rejection, and the targeted
suite treats unawaited coroutine warnings as errors. Test missing scope as well
as wrong tenant on clinical routes.

### SEC-03: Several direct-ID operations omit tenant and write-role checks

**Evidence: reproduced for surveys and engagements; source verified elsewhere.**
A tenant-A Viewer activated tenant-B's survey with 200 and added a deliverable to
tenant-B's engagement with 201. Each operation called its repository's save once.
These routes do not merely misuse SEC-02's helper: they lack that check entirely.

`TransitionUseCase.execute` loads by ID and invokes the transition without a
tenant argument. Authentication alone at the route therefore cannot supply the
missing ownership or Viewer restriction.

Sources: `apps/api/app/application/use_cases/transitions.py:44`;
`apps/api/app/api/routes/surveys.py:145`;
`apps/api/app/api/routes/engagements.py:185` and `:263`;
`apps/api/app/api/routes/care_callbacks.py:152`;
`apps/api/app/api/routes/pricing.py:97` and `:121`;
`apps/api/app/api/routes/critical_incidents.py:131`, `:156`, `:176`.

The pricing routes fetch a contract without comparing its tenant. Incident
reads and after-action output likewise load an ID with no tenant comparison.
These examples are not an exhaustive count of affected routes.

**Repair, owner: backend access-control owner, with each module owner.** Inventory
all mounted entity-ID routes, including nested children and previews. Require
a scoped entity plus the appropriate role before passing it to the operation.
Validate supplied parent/client/user references in the same tenant as well.
Do not assume a generic transition dispatcher can infer authentication context.

**Frontend:** use the same capabilities for controls and report clear denials;
Viewers must not see active mutation controls that the server will reject.

**Close only when:** authenticated wrong-tenant users and same-tenant Viewers are
tested separately across read/write/child routes; denied writes have no side
effects; eligible same-tenant operators still succeed. Include pricing previews,
incident after-action reads, campaign transitions and engagement child mutations.

### AUTH-01: Logout leaves the previous user's query data in memory

**Evidence: reproduced.** A diagnostic placed a synthetic case in the shared
query cache, called `authActions.logout()`, and read the same case back from
`queryClient`. Logout clears auth and tenant stores, but does not clear queries.
The bootstrap's tenant-clear path also does not clear queries. Login sets tenant
state directly rather than calling the action that clears the query client.

Sources: `apps/web/src/lib/auth-store.ts:19` and `:143`;
`apps/web/src/lib/tenant-actions.ts:34` and `:78`;
`apps/web/src/components/AppBootstrap.tsx:73`;
`apps/web/src/routes/cases/index.tsx:73`;
`apps/web/src/lib/query-client.ts:3`.

Many keys, such as `['cases', 'list']`, contain no tenant or identity. The
existing session epoch guards stale authentication failures; it does not isolate
cached successful query results. Actual cross-login rendering was not browser
tested, so the confirmed observation is cache retention and the resulting
cross-identity display risk.

**Repair, owner: frontend authentication owner.** Centralize identity teardown,
cancel pending queries, clear query and mutation caches, and use a session/tenant
boundary for protected query keys or query-client lifetime. Late successful
responses from the old session must not repopulate the next session's cache.

**Backend:** continue rejecting wrong-tenant requests even after the client fix.

**Close only when:** login as A, cache protected lists/details, logout, login as B
without a full reload, and verify no A data renders or survives in cache. Include
401 expiry, SSO, login failure and a delayed response from A's session.

### REP-01: The ready renewal report prints fixture data unconditionally

**Evidence: source verified.** The report catalogue marks `per-client-renewal`
as ready. Its page initializes data from `renewalPackFixture`, without a fixture
mode check or API query, and enables Print. The route accepts `client_id`, but
this component does not use it to load the selected client's records.

Sources: `apps/web/src/routes/reports/index.tsx:29`;
`apps/web/src/routes/reports/$templateSlug.tsx:117`;
`apps/web/src/components/reports/PerClientRenewalPack.tsx:19`.

**Repair, owner: reporting backend/frontend pair.** Immediately remove its
production-ready state until it uses the real template/run contract. Then bind
client, period and authenticated tenant explicitly and render only the resulting
materialized output. Keep any demonstration version separate and visibly labelled.
Do not invent headline values to fill missing sections.

**Close only when:** a test with fixtures disabled asserts the client-scoped API
request and returned values; changing clients changes the result; loading,
failure, no data and suppressed cells are distinct; print contains the verified
client, period, generation time and output, never an implicit demo record.

### PRIV-01: Survey aggregates disclose raw free-text answers

**Evidence: reproduced and source verified.** `WebhookPayload.answers` accepts
arbitrary values. `GetSurveyAggregateUseCase` turns each value into a string and
returns it as a frequency-table key, without small-cell suppression. A synthetic
single response produced `{'comment': {'Synthetic identifying free text': 1}}`.
An anonymous campaign flag does not change this aggregation.

The report runner suppresses counts but retains those free-text keys. Thus a
value of `<5` can still sit beside the identifying text itself.

Sources: `apps/api/app/api/schemas/survey_schemas.py:69`;
`apps/api/app/application/use_cases/survey_use_cases.py:144`;
`apps/api/app/infrastructure/services/report_query_runner.py:310`;
`apps/api/app/domain/services/cell_suppression.py:40`.

**Repair, owner: privacy/reporting backend owner.** Introduce approved question
metadata and aggregate only categorical choices. Keep free text out of employer
aggregate responses entirely. Apply one disclosure policy to campaign aggregate,
report output and exports, including totals and derived figures that could reveal
suppressed cells. Retain any raw narrative only behind an explicit restricted
workflow; this plan does not authorize displaying it.

**Frontend:** render suppression states, not zeroes, and never render arbitrary
answer strings as employer-facing chart labels.

**Close only when:** synthetic names, phone-like values and narrative answers
never appear in aggregate JSON or printed reports; small cohorts and totals obey
the same policy on every endpoint. Retain categorical aggregate functionality.

### SEC-04: 100 mutating routes authenticated the caller but never checked they may write

**Status: closed.** Evidence: reproduced by dependency-tree scan, then fixed.

SEC-03's repair has two halves. The tenant half was closed first:
`TransitionUseCase.execute` requires the owning tenant and refuses a mismatch,
and the entity-ID reads are scoped. This is the write-role half.

**Correction to the first count recorded here.** The initial scan reported 157
and named `POST /cases/{id}/close`, clinical-note `/sign`, `/users/{id}/ban`
and `/tenants/{id}/terminate` among the exposed routes. That was wrong, and the
claim is withdrawn. `require_tenant_role` and `require_self_or_role` are
factories whose inner function is named `_require`; matching only the factory
name missed them, so 57 already-gated routes were counted as exposed. Cases,
clinical notes, users, tenants, industries and members all carry their own
gate. The corrected figure is **100**.

What was genuinely reachable by a same-tenant Viewer: every DSAR mutation
(`/dsar/export`, `/dsar/erasure`, `/dsar/{id}/cancel`, `/execute-export`,
`/execute-erasure`), every contract command including `/terminate` and
`PATCH /pricing`, benchmark consent withdrawal, the care-callback campaign
lifecycle and member enrolment, every outreach-record transition including
`/triage` and `/escalate`, critical incidents, documents including
`PATCH /confidentiality`, engagements, KPIs, services, service assignments,
service sessions, survey campaigns, contacts, client tags, activities, report
template creation and runs, and `POST /utilisation-events`. Decision 3 in this
plan is "Viewers cannot mutate", and decision 3 also puts pricing changes and
DSAR execution behind tenant Admin specifically.

**Repair.** `block_viewer_writes` in `app/core/authorization.py`, registered as
an application-level dependency in `app/main.py`, so no route can be added
outside it. It refuses an unsafe method to a Viewer's token unless the route is
in `VIEWER_WRITABLE`, which holds six entries, each with its reason in the
source: the four auth endpoints, `POST /search` (a read whose query is a body),
and the signed survey webhook. Anonymous requests pass through, because whether
a route may be called without a token is a separate question that
`test_route_authorization` holds.

Route signatures were deliberately not edited. Hand-editing a hundred of them
is how twelve lost their tenant check in the first place, and an opt-in gate is
only as good as the memory of whoever adds the next route.

**Verified:** `test_viewer_write_gate` refuses a Viewer through the real
application on eight representative routes, confirms `/search` still gets past
the gate, confirms Admin and User are untouched, confirms reads and anonymous
requests are untouched, and pins the allowlist so growth is deliberate. Removing
the registration fails eight of those tests. Unit 1731 passed, coverage 67.48%.
Integration and e2e 500 passed, 1 failed, that failure being the pre-existing
provider audit test recorded in `PROVIDERS_MIGRATION.md`.

**Left open, deliberately.** The 100 routes now rely on the blanket gate rather
than on a role stated at the route. That is a weaker statement of intent than
`Depends(require_not_viewer)` at each one, and decision 3's stricter rule, that
pricing changes and DSAR execution require tenant Admin rather than merely
not-Viewer, is still not enforced. A test asserts the count does not grow while
that is outstanding. Assigning explicit roles route by route is follow-up work
for each module owner.

## P2: workflows and data correctness

### API-01: Survey and engagement lists disagree with their live response types

**Evidence: reproduced.** Backend list routes return JSON arrays. The frontend
live adapters type those arrays as `PaginatedResponse` and list pages read
`data.items`. In fixture mode the adapters wrap arrays in an envelope. Diagnostics
confirmed live adapters return arrays with `items === undefined`.

Sources: `apps/api/app/api/routes/surveys.py:111`;
`apps/api/app/api/routes/engagements.py:127`;
`apps/web/src/api/endpoints/surveys.ts:30`;
`apps/web/src/api/endpoints/engagements.ts:55`;
`apps/web/src/routes/surveys/index.tsx:79`.

**Repair, owner: survey/engagement backend/frontend pair.** Adopt the canonical
paginated envelope and make fixtures match the generated contract. Move filtering,
sorting and total counts to the backend. Add explicit error/retry states rather
than deriving an empty list from every missing `items` field.

**Close only when:** real list responses containing records render those records;
page two works; server errors do not render a successful empty state; fixtures
and production adapters consume the same contract.

### SUR-01: The survey creation form cannot satisfy the API

**Evidence: reproduced.** The form submits name, client, source and period, but
omits required `external_form_id` and `webhook_secret`. Sending that shape through
the app returns 422 naming both fields. The UI promises a webhook URL/token after
saving, while ordinary `SurveyCampaignResponse` contains neither field.

Sources: `apps/web/src/components/SurveyFormSheet.tsx:86`;
`apps/api/app/api/schemas/survey_schemas.py:12` and `:24`;
`apps/web/src/routes/surveys/$surveyId.tsx:196`.

**Repair, owner: survey backend/frontend pair.** Follow decision 8: require form
ID, generate the secret server-side, return it only in a dedicated create/rotate
response and support copy-once setup. Derive the webhook URL from the actual API
configuration. Align source/status enums and optional fields with the generated
contract. Do not claim the webhook is ready before setup succeeds.

**Close only when:** create works against the real API, the displayed URL matches
the mounted endpoint, a correctly signed synthetic submission is accepted, invalid
signatures fail, replay is idempotent, and list/detail never return the secret.

### ENG-01: Engagement child panels call missing or incompatible endpoints

**Evidence: source verified against routes and adapters.** The frontend requests
GET deliverables and GET hours child collections, but the backend defines POST
mutations on those paths and returns child lists embedded in engagement detail.
`getTimeline` requests `/summary` and casts its summary object as an event array.
Fixture behaviour conceals both contract mismatches.

Sources: `apps/web/src/api/endpoints/engagements.ts:87`, `:113`, `:124`;
`apps/api/app/api/routes/engagements.py:71`, `:163`, `:177`, `:227`.

**Repair, owner: engagement backend/frontend pair.** Use embedded deliverables
and hours from the canonical detail response for this version. Display the
summary as a summary. If chronological history is required, build an explicit
paginated audit/history contract; do not manufacture events from aggregate totals.
Validate hour-entry user ownership and permissions before saving.

**Close only when:** deliverable and hour panels load without 405s, mutation
invalidations refresh the canonical detail, and no `.map` or event-rendering path
receives a summary object. Verify the same behaviour with fixtures disabled.

### AUD-01: Engagement structural changes omit their audit handoff

**Evidence: reproduced for adding a deliverable; source verified for the other
operations.** Add deliverable, update deliverable status and log hours inject an
audit handler but return without calling it. Their use cases save the aggregate
and return the child. The deliverable probe saved once but produced no audit
handler call; the survey transition in the same probe did call the handler.

Sources: `apps/api/app/api/routes/engagements.py:185`, `:209`, `:235`;
`apps/api/app/application/use_cases/engagement_use_cases.py:72`, `:98`, `:117`.

**Repair, owner: engagement backend owner.** Preserve the mutated aggregate and
its events through one application operation. Persist the actor, tenant, child
identity and relevant before/after values with the mutation. Require appropriate
permission to record hours on behalf of another user. Do not add a silent-mutator
allowlist entry as a substitute for auditing.

**Frontend:** show saved state only after the atomic operation succeeds; surface
failures without implying that a partially audited change completed.

**Close only when:** each mutation writes a persisted audit record, correct actor
and tenant are retained, unchanged requests have deliberate semantics, and an
audit persistence failure rolls back the state change. Mock calls alone do not
close this finding.

### INC-01: Critical-incident note and timeline contracts are incompatible

**Evidence: reproduced for writes; source verified for reads.** `appendNote`
sends `{message}` to `/critical-incidents/{id}/phases`; the backend requires
`phase` and accepts `notes`. A synthetic request returned 422 for missing phase.
`getTimeline` similarly casts an after-action report object to an event array.

Sources: `apps/web/src/api/endpoints/incidents.ts:62` and `:68`;
`apps/api/app/api/schemas/critical_incident_schemas.py:23`;
`apps/api/app/api/routes/critical_incidents.py:170`.

**Repair, owner: incident backend/frontend pair.** Present a real phase-recording
form using the backend enum and notes contract. Render after-action output as a
report, or expose a separately typed history endpoint if needed. Review list and
create shapes against OpenAPI as part of this same slice. Complete SEC-03 first.

**Close only when:** a permitted phase can be recorded and read back through the
real API, invalid transitions are understandable, and timeline/report components
consume the correct shape. A fixture-only phase test is insufficient.

### CASE-01: The case directory cannot reach records beyond the first 100

**Evidence: source verified.** The repository defaults to `limit=100, offset=0`.
The route does not expose pagination and the UI filters the returned array in
memory. Search therefore cannot find an older matching case outside that slice.
The page checks pending/empty states without a distinct query-error branch.

Sources: `apps/api/app/infrastructure/repositories/case_repository.py:60`;
`apps/api/app/api/routes/cases.py:112`;
`apps/web/src/routes/cases/index.tsx:73` and `:137`.

**Repair, owner: clinical backend/frontend pair.** Add server-side paging, search,
filters and totals inside the clinical and tenant boundary. Preserve pseudonymous
subject identity; do not join employer names to improve search. Use the same
contract in case pickers, with authorization and client scope intact.

**Close only when:** a matching case beyond record 100 can be found and selected;
403/500 displays a denied/error state rather than no cases; wrong-scope users
receive no case data; client-specific pickers never fall back to all clients.

### BILL-01: Contract pricing has an API but no usable live UI connection

**Evidence: reproduced at the adapter; source verified for reachability.** The
live pricing adapter substitutes `unknown` when it cannot obtain a contract ID,
sends projected sessions instead of required `period_from`/`period_to`, and expects
an array rather than the backend invoice-preview envelope. Its component exists
but no product route imports it; the contract form edits billing rate/frequency,
not the separate pricing configuration. This is incomplete capability, not a
claim that ordinary contract creation fails.

Sources: `apps/web/src/api/endpoints/pricing.ts:124`;
`apps/web/src/components/common/PricingConfig.tsx:370`;
`apps/web/src/components/ContractFormSheet.tsx:135`;
`apps/web/src/api/endpoints/contracts.ts:11`;
`apps/api/app/api/routes/pricing.py:121`;
`apps/api/app/api/schemas/pricing_schemas.py:49`.

**Repair, owner: commercial backend/frontend pair.** After SEC-03, add a
contract-scoped pricing tab with explicit persisted configuration and date-bounded
invoice preview. Consume server decimal-money/envelope fields. Clearly separate
saved pricing from an unsaved estimate; do not promote fixture arithmetic to the
production billing engine. Preview must not create an invoice or payment.

**Close only when:** each supported pricing model can be saved and read back by
an authorized operator; previews use the real contract and period; currency,
rounding and missing-rate errors agree with the backend; Viewers cannot change
pricing and another tenant cannot preview the contract.

### REP-02: Report sections apply client, period and deletion filters inconsistently

**Evidence: source verified plus compiled-SQL probe.** With a client filter and
an end date of 2026-01-31, `_sessions_by_month` generated SQL containing only tenant,
status and date filters, with `scheduled_at <= '2026-01-31 00:00:00'`. It omitted
client scope and the soft-deletion predicate. Diagnosis prevalence also does not
use client scope. Contract utilisation does filter by client. Callback outcomes
and satisfaction distribution do not apply the date window at all.

Sources: `apps/api/app/infrastructure/services/report_query_runner.py:96`,
`:175`, `:214`, `:258`, `:310`.

**Repair, owner: reporting backend owner.** Normalize one report context with
tenant, optional client, timezone and period. Pass it to every section and reject
unsupported parameters instead of silently ignoring them. Use an inclusive
calendar end date expressed as an exclusive next-day timestamp for timestamp
columns, and consistently exclude retired/deleted records where applicable.
Validate that any supplied campaign belongs to the requested client and tenant.

**Frontend:** show the exact scope and period applied by the server, not just the
query string the page originally requested.

**Close only when:** a PostgreSQL fixture with two clients, records just inside
and outside the date window, a last-day afternoon record and deleted records
produces the expected counts in every section. Verify timezone boundaries and
that switching the client changes all sections consistently.

### DATA-01: Survey aggregate totals silently cap at 10,000 responses

**Evidence: source verified.** `GetSurveyAggregateUseCase` fetches at most 10,000
responses, builds frequencies in memory and labels `len(responses)` as the
response total. It does not signal truncation or reconcile the campaign's total.

Source: `apps/api/app/application/use_cases/survey_use_cases.py:168`.

**Repair, owner: survey/reporting backend owner.** Aggregate approved categorical
answers over the entire eligible dataset in the database, or use bounded streaming
that still yields an exact result. Apply PRIV-01 after aggregation. Do not expose
an exact cohort size where the disclosure policy requires suppression.

**Frontend:** display the aggregate's scope and completeness; do not interpret a
query limit as the total campaign population.

**Close only when:** a dataset exceeding 10,000 responses is counted correctly,
filters match the source population, query/memory costs are bounded, and privacy
suppression remains consistent with the smaller campaign endpoint.

## Follow-up verification, not yet a confirmed database defect

### VERIFY-01: Failed report runs may disappear on rollback

`RunReportTemplateUseCase.execute` saves a failed state and re-raises on query
errors (`apps/api/app/application/use_cases/report_use_cases.py:160`). Its route
is transactional (`apps/api/app/api/routes/reports.py:192`) and the decorator
rolls back exceptions (`apps/api/app/shared/decorators/transaction.py:69`). This
suggests the failure record is rolled back along with the run, but persistence
was not tested on PostgreSQL here.

**Owner: reporting backend owner.** Force a section query failure in a database
test and inspect the run record after the request. If it disappears, preserve a
safe failed-job envelope separately from rolled-back result work. Return a run ID
and safe error status; do not leak database exception text to ordinary users.

## Checks, exclusions and limits

Synthetic API probes used `httpx.ASGITransport(app=app)`, fresh clients, injected
mock repositories, and explicit tenant-A/tenant-B records. The authorization
probe used `TokenData(user_id='viewer-a', tenant_id='tenant-a', role='Viewer')`.
Public report probes removed that override and supplied no credentials. No
collector/tombstoner was exercised on real data.

The frontend diagnostics ran with fixtures disabled and confirmed these existing
behaviours: cache retention after logout, arrays without `items`, and a pricing
request to `/contracts/unknown/invoice-preview`. All three diagnostic assertions
passed because they intentionally describe the bugs. These are not regression
passing tests for a repaired application. Temporary diagnostic files were removed
from the working tree.

Existing selected regression suites also passed: 130 backend tests and 30
frontend tests across seven files each, with no skips reported in those runs.
These results do not replace the new negative tests. In particular, the existing
endpoint fixture tests can pass while their live contracts are incompatible.

Backend command, from `apps/api`:

```sh
.venv/bin/python -m pytest \
  tests/unit/application/test_survey_use_cases.py \
  tests/unit/application/test_pricing_engine.py \
  tests/unit/application/test_transition_use_case.py \
  tests/unit/application/test_dsar_use_cases.py \
  tests/unit/domain/test_engagement.py \
  tests/unit/domain/test_report.py \
  tests/unit/api/test_use_case_call_sites.py -q
```

Frontend command, from `apps/web`:

```sh
./node_modules/.bin/vitest run \
  src/api/endpoints/engagements.test.ts \
  src/api/endpoints/surveys.test.ts \
  src/api/endpoints/incidents.test.ts \
  src/api/endpoints/pricing.test.ts \
  src/routes/reports/reports.test.tsx \
  src/routes/cases/cases-happy.test.tsx \
  src/routes/auth/login-happy.test.tsx --reporter=dot
```

The three temporary frontend diagnostics were run separately with fixtures
disabled. PostgreSQL integration, full application suites and browser interaction
were not executed as part of this documentation review.

Ruled out or deliberately not filed as defects:

- The report runner's `not_implemented` fallback exists, but all five current
  `ReportQueryType` enum members have concrete handlers. No current valid enum
  was found that reaches that fallback, so it is not listed as a live defect.
- The home route passes null children, but `AppLayout` renders `DashboardMain`
  as its fallback. It is not an empty-dashboard defect.
- Sidebar flags intentionally disable campaigns, worklist, surveys and engagements
  and hide several other modules by default. Do not enable them simply to remove
  a disabled link. Their mounted APIs still require SEC-01 through SEC-03 checks.
- Provider forms, affiliations and session eligibility remain owned by the active
  provider agents. Reconcile shared-file fixes with that integration owner.
- Earlier service-review issues are already recorded as fixed. This document
  does not relabel them as new findings without fresh evidence.

## Implementation phases and acceptance gates

These are repair work packages, not new product domains. An implementation owner
must add commit IDs, exact commands/results and deployment state to its phase.
Keep unchecked items open until their stated acceptance checks pass.

- [ ] Phase 1 - Access control and identity isolation
  - [x] ~~Close SEC-01~~ across all mounted routes in scope. The scan found 26
        routes resolving no user, not the 2 recorded; all are authenticated and
        tenant-scoped except the justified public surface, which
        `test_route_authorization` now holds as an explicit allowlist.
        `GET /provider-specialties` is listed there as pending, not approved:
        it belongs to the provider worktrees.
  - [x] ~~Close SEC-02.~~ All twelve unawaited calls replaced with the
        synchronous `assert_same_tenant`; `test_use_case_call_sites` fails the
        build if the async form is called outside `Depends` again.
  - [x] ~~Close SEC-03.~~ Tenant half: `TransitionUseCase.execute` takes a
        required keyword-only `tenant_id`, enforced fail-closed in both
        directions, and all 82 route call sites plus the one application-layer
        call site pass the authenticated caller's tenant. Write-role half:
        closed by SEC-04's blanket gate. Per-route role statements remain
        follow-up work for each module owner.
  - [x] ~~Close AUTH-01 for logout, expiry, SSO and delayed responses.~~
        `resetIdentityState` is reached from all of them; verified against a
        real query client, including a response arriving after the reset.
  - [~] Anonymous, wrong-tenant and wrong-role regression cases added
        (`test_cross_tenant_reads`, `test_route_authorization`,
        `test_transition_use_case`, `test_viewer_write_gate`). Wrong-scope
        cases on clinical routes are not written yet.
  - [ ] Verify forbidden operations have no save, export or erasure side effects.
        Partly done: the transition guard is asserted to leave the aggregate
        unchanged and unsaved. Not yet done for DSAR export/erasure.
  - [ ] Reconcile shared authorization/outreach/session files with provider work.
        Not started. `service_sessions.py`, `non_compete_clauses.py` and
        `panel.py` received tenant arguments at their transition call sites and
        the provider worktrees must rebase onto that.

- [ ] Phase 2 - Reporting truth and privacy
  - [ ] Close REP-01, PRIV-01, REP-02 and DATA-01.
  - [ ] Execute VERIFY-01 and record either its repair or evidence ruling it out.
  - [ ] Verify client/period scoping and privacy using synthetic PostgreSQL data.
  - [ ] Verify real report output and print behaviour with fixtures disabled.

- [ ] Phase 3 - Complete the survey and engagement connections
  - [ ] Close API-01, SUR-01, ENG-01 and AUD-01.
  - [ ] Regenerate OpenAPI and frontend types from the integrated backend commit.
  - [ ] Verify signed synthetic webhook setup, list/detail, child mutation and audit.
  - [ ] Keep rollout flags disabled until the real API flows pass.

- [ ] Phase 4 - Clinical directory, incident and commercial workflows
  - [ ] Close CASE-01, INC-01 and BILL-01.
  - [ ] Verify case search beyond the first page without breaking the privacy wall.
  - [ ] Verify real incident phase recording and typed after-action output.
  - [ ] Verify persisted pricing and date-bounded previews for each supported model.

- [ ] Phase 5 - Integrated release review
  - [ ] Run relevant backend, frontend, generated-contract and PostgreSQL checks.
  - [ ] Add a fixtures-disabled contract suite; existing fixture tests remain useful
        but must not be the only evidence that a module works.
  - [ ] Test error, loading, empty and forbidden states as well as successful paths.
  - [ ] Record the reviewed base/head, integrated commits and application revisions.
  - [ ] Run the same checkout's backend and frontend before browser verification.
  - [ ] Mark implemented, tested and deployed separately. A hidden navigation item
        or a passing mock test is not evidence of endpoint safety or deployment.

## Active ownership (read before editing any file named here)

Claimed 2026-09-07. Update this block when a stream is picked up or released;
do not start work on a claimed path without agreeing the handover here first.

| Stream | Findings | Owner | State |
| --- | --- | --- | --- |
| 1. Access control and session state | SEC-01, SEC-02, SEC-03, SEC-04, AUTH-01 | stream 1 agent (this branch, `chore/monorepo`) | all closed; per-route roles left as module-owner follow-up, see SEC-04 |
| 2. Reporting and privacy | REP-01, PRIV-01, REP-02, DATA-01 | delegated 2026-09-07 | in progress |
| 3. Module integration | API-01, ENG-01, AUD-01 | delegated 2026-09-07 | in progress |
| 3b. Module integration, later round | SUR-01, INC-01, CASE-01, BILL-01 | unclaimed | open |

**Files stream 1 holds.** Backend: `app/core/authorization.py`,
`app/api/dependencies/reporting.py`, `app/application/use_cases/transitions.py`,
and the authorization lines only of `app/api/routes/`: `reports.py`,
`benchmark.py`, `engagements.py`, `surveys.py`, `eap_programmes.py`, `cases.py`,
`clinical_notes.py`, `dsar.py`, `care_callbacks.py`, `pricing.py`,
`critical_incidents.py`. Frontend: `src/lib/auth-store.ts`,
`src/lib/tenant-actions.ts`, `src/lib/query-client.ts`,
`src/components/AppBootstrap.tsx`.

**What this means for streams 2 and 3.** `surveys.py`, `engagements.py`,
`critical_incidents.py`, `pricing.py` and `cases.py` are also stream 3 files.
Stream 1 goes first in them, as the plan's execution ownership requires, and
touches only the authorization guard and route signature. Response shapes, use
case bodies and schemas in those files are untouched and stay with stream 3.
Take them once stream 1's commits for that file have landed; rebase rather than
edit in parallel.

**Interface stream 1 publishes.** `assert_same_tenant(current_user, tenant_id)`
in `app/core/authorization.py` is the in-body ownership guard. It is
deliberately synchronous: the defect SEC-02 records is twelve unawaited calls to
the async `require_same_tenant`, which a synchronous function cannot repeat.
`require_same_tenant` keeps its existing, correct meaning as a FastAPI
dependency (`Depends(require_same_tenant)`) for routes carrying `tenant_id` in
the path or query. Use the dependency where a route takes a tenant argument, and
`assert_same_tenant` where the tenant is only known after loading the entity.

**Not claimed by stream 1.** The provider module, held by `wt-agent1`,
`wt-agent2` and `wt-agent3`. See also the red provider CI test recorded under
"Remaining risks and ownership" in `PROVIDERS_MIGRATION.md`: the api job cannot
go green until its owner fixes it, independently of this plan.

## Execution ownership

After coordinating with the active provider integration owner, use three repair
streams if parallel work is desired:

1. **Access-control and session-state owner:** SEC-01 through SEC-03 and AUTH-01.
   Own shared auth/dependency changes and the permission inventory. Establish
   these interfaces before module owners modify the same routes.
2. **Reporting and privacy owner:** REP-01, PRIV-01, REP-02, DATA-01 and VERIFY-01.
   Own report queries, materialized output, survey aggregate policy and report UI.
   Coordinate survey schema changes with stream 3.
3. **Module integration owner:** API-01, SUR-01, ENG-01, AUD-01, INC-01, CASE-01
   and BILL-01, delivered in small backend/frontend slices. Own generation of
   shared OpenAPI/frontend artifacts after the other streams provide commits.

Use isolated worktrees and isolated test databases/schemas. Agree migration
parents and shared-path ownership before editing. Do not overwrite the provider
agents' in-flight work or regenerate contracts from a stale backend. The reviewer
must check the combined branch and reproduce corrected boundaries before closing
findings. Production migrations, real data import and deployment are separate
from implementing this plan.
