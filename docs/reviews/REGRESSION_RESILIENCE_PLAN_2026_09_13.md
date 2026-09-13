# Regression diagnosis and resilience plan

Date: 13 September 2026. Baseline: `c15a1ba6`.
Status: diagnosis and issue backlog only. No application fixes, deployment or
external tracker issues created in this pass. Issue IDs below are local backlog IDs.

## Conclusion

There is evidence of unsafe change propagation and gaps in verification. There is
not enough evidence to say that every regression, or the latest reported member
import failure, is caused by sessions import. The latest failure still needs its
error, phase, time or batch ID to establish that causal chain.

The strongest demonstrated cause is a mismatch between what our tests accept and
what the real system requires. A second cause is incomplete transfer of data between
layers. A third is testing request performance under easier conditions than the
environment where it runs. Shared infrastructure increases the impact of these
mistakes, but sharing itself is not the defect.

The remedy is a modular application with enforceable boundaries and stronger
feedback, not a rewrite or a generic framework for every import. Add the tests that
would have caught the failures first, then change one boundary at a time.

## What the evidence establishes

### E1. A mock concealed an invalid repository call

Commit `503b3e78` fixes session staging passing raw strings where the repository
expects ID value objects and reads `.value`. The original feature was introduced
in the booking-reconciliation work; the fixing commit explicitly records that the
mock accepted the wrong arguments and real staging failed.

The retained regression is
`apps/api/tests/unit/application/test_session_import_staging.py:779`.
Its fixture creates nine unrestricted `AsyncMock()` collaborators at `:69-98`.
The real interface is
`apps/api/app/domain/repositories/service_session_repository.py:248` and its
implementation is `apps/api/app/infrastructure/repositories/service_session_repository.py:441`.

This is a proven historical failure, now fixed. It demonstrates a contract-testing
gap, not that the current repository method is broken. Even `autospec` checks
signatures rather than enforcing annotated argument types at runtime.

### E2. Member staging could look correct while persistence lost data

Commit `a78b3949` fixes employment details present in the member staging preview but
omitted when calling the enrolment use case. The optional argument defaulted to
None, so the omission raised no error. The current conversion is in
`apps/api/app/api/services/member_import.py:607`, with employment passed at `:639`.

This is a proven historical member failure, now fixed. It arose at a mapping
boundary, not from a demonstrated session-import change. Preview assertions alone
cannot prove database fidelity.

### E3. Request duration and resume semantics escaped early checks

Commit `3dc0591e` records member apply exceeding the ordinary 30-second client
timeout on a real roster and a remote database. Commit `61231ec8` fixes resumed,
already-written rows being labelled skipped. Both are fixed historical defects.

Current member and session endpoints each use a 180-second apply timeout, and their
dialogs each use 200-row chunks:
`apps/web/src/api/endpoints/members.ts:130`,
`apps/web/src/api/endpoints/session-imports.ts:32`,
`apps/web/src/components/members/MemberImportDialog.tsx:95`, and
`apps/web/src/components/sessions/SessionImportDialog.tsx:79`.

These values are current implementation choices, not a verified production latency
budget. `docs/operations/IMPORT_TIMING.md` explicitly labels its benchmark local and
leaves remote latency measurement open. Raising a browser timeout cannot extend a
hosting platform's request deadline.

### E4. Changes can affect both importers through legitimate shared paths

The graph confirms both `apply_member_import` and session `apply_batch` call
`BatchedCommit`: `apps/api/app/shared/utils/batched_commit.py:11`,
`apps/api/app/api/routes/members.py:1161`, and
`apps/api/app/api/routes/session_imports.py:467`. They also depend on shared member,
client and repository contracts, database state and the API transport.

Commit `de09661f` changed 29 files across both importers, enrolment, repository
interfaces/implementations, dialogs and tests. Commit `e056ebc1` changed both
transaction paths and introduced the shared commit cadence. These counts come from
`git show --stat`; they establish change breadth, not that those commits broke members.

Changing a shared durability rule is necessarily a cross-module change. The error
is testing or describing it as though it belongs to only one module.

### E5. Green gates have narrower meaning than we sometimes claim

- `package.json:35` blocks type errors only under `app/domain`. A fresh
  `.venv/bin/python scripts/pyright_gate.py --run app/domain` exits successfully
  while reporting 873 advisory errors: 647 in unit tests, 79 in API, 56 in
  infrastructure, 24 in application and 24 in shared code, plus other packages.
  These are diagnostics, not 873 demonstrated runtime failures.
- `package.json:38-40` makes `pnpm verify` run backend unit tests and frontend
  component tests. It does not run backend integration/HTTP tests, Playwright, or
  the production build. Those were run separately in the preceding completion pass.
- CI does run backend integration/HTTP tests (`.github/workflows/ci.yml:114`),
  frontend unit tests and build (`:178`), and generated contract checks (`:234`).
  It is incorrect to say there is no integration coverage.
- No workflow under `.github/workflows` invokes Playwright or `test:e2e`.
  The member browser test at `apps/web/e2e/member-import.spec.ts:86` stubs the API.
  It proves the dialog's behaviour, not that browser, deployed API and database agree.
- CI's web job runs only for web-path changes (`.github/workflows/ci.yml:148`).
  The contract job runs for either side, but a schema diff cannot detect all changes
  in status meaning, pagination, timings or import outcomes.
- `tests/conftest.py:291` derives mocked tenant identity from request parameters;
  `:322,371` bypasses the audit loader's tenant check for ordinary tests.
  The preceding audit fix adds targeted tests using the real loader. The shared
  fixture is still unsuitable as general evidence of production authorization.
- `tests/conftest.py:216,267` creates/drops metadata tables. This is useful isolation
  but is not proof that Alembic upgrades an existing deployed schema correctly.

### E6. Responsibility boundaries and documentation need tightening

Member apply orchestration lives inside HTTP routes (`members.py:1087-1196`), while
session apply has an application use case
(`app/application/use_cases/apply_session_import.py:86`). Member row import accepts
both `TokenData` and the API's `MemberCreate` schema (`api/services/member_import.py:592,607`).
That makes HTTP representations part of an import business workflow.

Session staging's class spans 678 lines and accepts nine repository dependencies
(`application/services/session_import_staging.py:226-903`). Its methods cover
preloading, names, client/member/service resolution, enrichment, delivery context,
booking reconciliation and replay classification. Those separate reasons to change
are a stronger argument for decomposition than line count alone.

The member apply docstring still describes per-row commits (`members.py:1139-1144`),
while the route actually uses batched commits at `:1161`. This is a concrete case of
documentation lagging the durability contract.

Existing import-linter rules already enforce domain/application layering, with
declared exceptions (`apps/api/pyproject.toml:97-132`). Keep those protections;
extend them selectively rather than claiming SOLID is entirely absent.

## How to apply SOLID, DRY and KISS here

- Single responsibility: move member import orchestration into an application use
  case; split session staging by independently testable decisions. Do not split
  functions merely to satisfy a line-count target.
- Dependency inversion and interface segregation: import workflows consume small
  typed ports and application commands, with HTTP/auth translation at the boundary.
  Keep real repository implementations covered against those ports.
- Substitution: mocks/fakes and real repositories must obey the same observable
  contract, including ID types, tenant filtering and failure semantics.
- Open/closed: add an import policy through an explicit input/strategy only when
  there are real variants. A configuration switch for every branch is not progress.
- DRY: share stable mechanics such as progress arithmetic and commit cadence, plus
  their contract tests. Keep member identity rules, historical session acceptance
  and practitioner eligibility distinct. Similar-looking code need not have the
  same business meaning.
- KISS: preserve the modular application and current resumable model while fixing
  boundaries. No microservice split, universal import engine or automatic approval
  of ambiguous identities is proposed.

These are engineering recommendations. They are not findings that every principle
has been violated, and no formal complexity score or production load study was run.

## Issue backlog

All items are proposed and unimplemented in this diagnostic pass. P1 means before
the next import behaviour/performance release; P2 means a sequenced structural
improvement after the safety gates. Owners are responsible roles, not assigned people.

### REG-01 · P1 · Reproduce the latest reported member-import failure

Owner: member-import maintainer. Evidence: current user report; E1-E3 are historical
and do not identify this incident. Dependencies: error/phase/time or batch ID.

Capture release commit, stage/apply request ID, input format and a sanitized minimal
fixture. Identify the last known passing revision and first failing revision using
an isolated checkout if needed. Inspect row outcomes and persisted state, not only
the UI toast. Never upload a real roster into a diagnostic artifact.

Acceptance: one test fails on the identified bad revision and passes with the fix;
the issue names the exact shared dependency or independent defect responsible.
If it is environmental, demonstrate that with the same input/code and controlled
environment difference. Do not close this from unrelated green test counts.

### REG-02 · P1 · Require paired workflow regression gates

Owner: CI/test maintainer with member/session owners. Evidence: E4-E5.
Dependencies: none; start with existing tests.

Add a documented import verification command and CI job covering both member and
session imports whenever their shared repositories, schema, auth, parser utilities,
transaction helpers or transport change. Run Playwright in CI. Keep quick local
verification distinct from release verification and name the guarantees of each.

Acceptance: an API-only import change and a shared-helper change trigger both
workflows; a deliberate failing member regression blocks a sessions PR. Required
database suites fail when their setup is missing instead of silently skipping.
List the required test IDs and publish their execution results, not just collection.
Configure required branch checks after inspecting existing repository protection.

### REG-03 · P1 · Make boundary type and repository-contract failures blocking

Owner: backend/test maintainer. Evidence: E1 and the 873 advisory diagnostics in E5.
Dependencies: REG-02 for regression protection.

Start with import services and their repository ports. Replace unrestricted mocks
at critical boundaries with typed fixtures/contract tests; use autospec for method
shape but assert value-object and persistence semantics separately. Fix the scoped
diagnostics, then extend the strict gate to those exact paths. Ratchet remaining
diagnostics by file so new errors cannot hide behind an unchanged total.

Acceptance: passing a raw string to `find_awaiting_confirmation` fails a blocking
check before merge; each changed importer boundary has both fake and real-adapter
coverage. No blanket suppression, widening to `Any`, or lowering coverage to pass.
The issue records which paths are strict and which remain advisory.

### REG-04 · P1 · Verify complete import journeys and field fidelity

Owner: import/test maintainers. Evidence: E2, E3, E5.
Dependencies: REG-02; REG-01 adds its reproduction when available.

Build a small synthetic browser -> real API -> PostgreSQL acceptance suite for
member and session upload, stage, review, apply and read-back. Exercise both CSV and
XLSX formats where supported, replay, partial failures and resume. Include employment,
identifiers, dates and session times in the persisted read-back assertions. Run an
upgrade-from-supported-schema path with Alembic as well as clean metadata fixtures.

Acceptance: intentionally dropping employment or shifting a supplied session time
fails the suite. Retry after a lost response writes no duplicate. One invalid row
does not undo committed valid rows. Tenant isolation uses fixed authenticated
identities, not identities inferred from the requested tenant. API-stubbed browser
tests remain useful but are labelled separately.

### REG-05 · P2 · Move member import behind an application boundary

Owner: member-import maintainer. Evidence: E6. Dependencies: REG-03 and REG-04.

Extract stage/apply orchestration from the members router into application services
using domain repository interfaces and an explicit transaction/savepoint port.
Translate `TokenData` into an actor context and `MemberCreate` into an application
command at the HTTP boundary. Keep current routes, outcomes and audit behaviour.
Centralize the roster-to-enrolment mapping and test every supported field once.

Acceptance: the extracted application code imports no FastAPI or API schemas;
existing wire contracts and persisted outcomes are unchanged; import-linter guards
the boundary; the member and session compatibility suites both pass. No simultaneous
schema, performance or eligibility change in this extraction.

### REG-06 · P2 · Decompose session staging by decision ownership

Owner: session-import maintainer. Evidence: E6. Dependencies: REG-03 and REG-04.

Separate subject resolution, practitioner/delivery resolution, and booking/replay
classification behind small typed interfaces. Leave the staging coordinator to
compose decisions. Make preload/cache lifetime explicit per tenant and batch;
preserve original values and reason codes. Extract one decision per commit.

Acceptance: each decision can be tested without constructing nine repositories;
the same golden input produces identical staged outcomes and persisted values;
cache tests prove no cross-tenant reuse or stale eligibility after apply-time
revalidation. Maintain provider migration policies and historical acceptance rules.

### REG-07 · P1 · Test the request, checkpoint and retry contract

Owner: import backend/frontend maintainers. Evidence: E3-E4.
Dependencies: REG-02; performance inputs depend on REG-09.

Specify a common transport contract for pending/processed/failed counts, checkpoint
durability, cancellation, timeout and resume. Keep module-specific outcomes explicit.
Test both importers against the shared commit helper. Use controlled database/network
delay and the actual hosting request deadline to select chunk sizes with headroom.
Do not blindly share equal constants unless they represent an adopted common policy.

Acceptance: disconnect after commit, fail before commit, cancel mid-chunk and apply
the same batch concurrently. Assert row uniqueness, audit persistence and accurate
resume counts. Both workflows survive a commit-helper change. Document measured
request percentiles and an agreed budget; do not present local timings as production.

### REG-08 · P2 · Make test identities and schema setup trustworthy

Owner: test/platform maintainer. Evidence: E5. Dependencies: REG-02.

Introduce an explicit authenticated test client with a fixed tenant, role and scopes,
using real authorization dependencies. Migrate affected security tests off the
request-derived identity fixture without changing all test files at once. Standardize
isolated database/schema setup, and refuse destructive fixtures against a non-test
or non-local database. Preserve intentionally lightweight unit tests.

Acceptance: requesting tenant B as tenant A stays tenant A; another tenant's detail
and history are denied. Test setup cannot drop application tables accidentally.
Real migration tests and fresh-schema tests are visibly distinguished in reports.

### REG-09 · P1 · Connect runtime feedback to release and environment

Owner: operations and import backend maintainers. Evidence: E3 and the environment
ambiguity recorded in `docs/reviews/AUDIT_COVERAGE.md` under the R2 investigation.
Dependencies: authorized deployment target for production measurements.

Extend existing import timing logs with release identity and a non-secret environment
identifier. Correlate batch, request, outcome, retry and checkpoint state. Monitor
stalled applies and outbox age, with an owner and a recovery runbook. Keep credentials,
raw row contents and clinical values out of telemetry. Use locked dependencies in
release builds; CI currently uses `uv sync --group dev` without `--frozen` at
`.github/workflows/ci.yml:87,224`.

Acceptance: a synthetic failure can be traced from UI request to batch state and
release; a forced worker interruption produces a detectable unhealthy state and
recovers through the existing idempotent path. A drifted lockfile fails CI.
Record local, staging and production evidence separately.

### REG-10 · P1 · Make change completion and scope evidence enforceable

Owner: engineering maintainer. Evidence: E4-E6 and the prematurely closed R4
exception corrected in `docs/handoffs/SESSIONS_IMPLEMENTATION.md`.
Dependencies: none for the checklist; REG-02 supplies automated evidence.

For a shared change, identify affected consumers, preserved contracts, rollback
behaviour and required checks before editing. Separate structural extraction from
behaviour changes. Keep an originally required acceptance gate open until it passes;
an implementer cannot relabel it out of scope to claim completion. Update durability
documentation with the implementation. Record unrelated findings once in this backlog.

Acceptance: the PR template and release record link to executed gates and explicitly
state implemented/tested/deployed status. A shared commit-cadence change lists both
importers. Replace the stale per-row-commit description with the tested savepoint and
checkpoint contract. No extra ceremonial approvals for routine reversible work.

## Execution order and stopping conditions

1. Establish the incident and safety net: REG-01, REG-02, REG-10. REG-01 can remain
   pending on incident details while the independent safety-net work proceeds.
2. Close escapes: REG-03, REG-04, REG-07, REG-09. Start with the four historical
   reproductions, shared commit behaviour and a real two-module smoke suite.
3. Refactor only behind passing gates: REG-05 and REG-06, one boundary per commit.
   Improve security/test setup through REG-08 alongside those migrations.
4. Reassess autonomy after reliability: current applies are browser-driven and
   resumable, not unattended jobs. If imports must continue after the browser closes,
   separately authorize a durable job worker with leases, idempotency, bounded retries
   and operator-visible dead letters. That is new capability, not a hidden requirement
   for closing the observed bugs. Never auto-resolve ambiguous identities.

Success means the historical failures are caught before merge, both importers are
verified after shared changes, runtime failures identify their release/environment,
and recovery has a tested outcome. Zero coupling, zero duplicated lines and a larger
raw test count are not acceptance criteria. Do not start a broad rewrite after the
listed gates pass.

## Checks performed in this diagnostic pass

- Read current source, graft dependency results, CI/test configuration and the
  fixing commits named above. Missing graph edges were supplemented with literal
  symbol searches; the graph is not claimed to be a complete dependency proof.
- Ran, from `apps/api`, with `MEMBER_TEST_DATABASE_URL` explicitly set to local
  `eap_test`: `.venv/bin/pytest tests/integration/test_members_persistence.py
  tests/unit/application/test_session_import_staging.py
  tests/unit/application/test_apply_session_import.py
  tests/unit/shared/test_batched_commit.py -q`: **126 passed**, no skips.
- Ran `.venv/bin/python scripts/pyright_gate.py --run app/domain`: gate passed,
  873 advisory diagnostics reported. Results are for this baseline only.
- No production access, real-roster replay, first-bad-commit bisection, concurrency
  load test or complete architecture audit was performed. The latest reported
  member failure remains unconfirmed pending its identifying details (REG-01).
