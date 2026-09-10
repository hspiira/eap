# Provider migration execution handoff

**Archived 2026-09-10.** This work is merged into `chore/monorepo`; the
worktrees and branches below no longer exist. Kept as a record of what was
done and verified. Current provider decisions are in
`docs/migrations/PROVIDERS_MIGRATION.md`.

Use with `docs/migrations/PROVIDERS_MIGRATION.md`. The user requested
three-agent implementation followed by independent review. These prompts
authorize implementation of that plan; they do not assert that it is already
implemented, tested, or deployed.

## Team and working agreement

Use three isolated worktrees, starting from the commit that contains this
handoff. Agent 1 owns integration; agents 2 and 3 provide committed changes to
that branch. Do not run all three against a shared mutable checkout. Follow
`AGENTS.md`, `CLAUDE.md`, applicable app/design rules, and graft before source
searches. Commit finished pieces by path without attribution trailers.

Before editing, discover the other tasks/agents and announce role, branch,
worktree, and ownership. Exchange messages only for contracts, dependencies,
shared files, blockers, or review handoffs. Do not spawn additional agents.
Coordinate directly; do not ask the user to relay routine integration details.
If the other tasks are not yet discoverable, continue independent owned work
and publish the handoff details in the task response.

The migration document is the source of design decisions. Make routine
implementation choices within it. Record evidence that requires changing a
product decision and refer it to the review task rather than silently changing
the policy. Do not invent missing source identities, database state, or deadlines.
Do not import real sessions, run production migrations, push, merge to the
protected/default branch, or deploy as part of these prompts.

### Ownership

- **Agent 1: provider core and integration.** Own existing backend files,
  practitioner identity/profile/eligibility operations, lifecycle authorization
  and audit, existing session/outreach routes and schemas, shared dependency and
  model registries, provider CI wiring, and
  `docs/migrations/PROVIDERS_MIGRATION.md` progress. Own new core provider
  migrations and corresponding tests.
- **Agent 2: organisations, vocabulary and historical import.** Own new backend
  organisation, affiliation, specialty, alias, and historical staging/import
  modules, their new migrations and tests. Send required edits to existing
  backend files to agent 1 with exact interfaces and acceptance cases. Agent 2
  must not add an alternative live-session write path to avoid this boundary.
- **Agent 3: frontend, generated contracts and user-flow verification.** Own
  `apps/web/` changes for the provider module, generated route metadata,
  `apps/web/src/api/generated/schema.ts`, and `apps/api/schema/openapi.json`.
  Generate contracts from the agreed backend commit; never hand-edit them.
  Report backend deficiencies to their owner.

Agent 1 owns merge conflict resolution and integration of all three branches.
An owner can explicitly transfer a file in one coordination message; record the
new owner before both agents continue. Do not edit another owner's file on the
assumption that worktrees make incompatible changes harmless.

### Dependency gates

1. **Contract gate.** Agent 1 publishes practitioner and lifecycle request,
   response, permission and error contracts. Agent 2 publishes organisation,
   affiliation, vocabulary and historical-import interfaces. Agree delivery
   context and eligibility inputs with agent 1 before either implements shared
   session integration. Agent 3 confirms these contracts support the UI.
2. **Boundary gate.** Agent 1 proves the four reviewed defects are repaired:
   Viewer mutation, silent create/PATCH audits, missing tenant constraints, and
   the invalid migration test fixture. Existence-only foreign keys and mocked
   audit calls are not sufficient proof.
3. **Directory gate.** Agent 1 delivers optional accounts and owned contact data;
   agent 3 integrates usable create/edit, linking controls and server-side
   listing. Record API generation at this milestone.
4. **Attribution gate.** Agent 2 delivers organisation/affiliation modules; agent 1
   integrates them with actual session routes, persistence and eligibility.
   Agent 3 integrates management and delivery-context selection.
5. **Import gate.** Agent 2 delivers source-scoped reconciliation and an isolated
   historical-import operation; agent 1 integrates typed profile policy and
   shared registries. No actual source import before acceptance checks pass.
6. **Review gate.** Agent 1 assembles the branch and orders migrations into one
   deliberate Alembic chain. Agent 3 regenerates contracts from that branch and
   verifies the integrated UI. All agents submit evidence for independent review.

Agree each migration's parent revision before merging it. Never rewrite a
migration known to have been applied to a shared environment; use a successor.
When application history is unknown, preserve the existing revision and make
repairs in a new migration. Do not accept accidental multiple heads.

Agent 2 may build its new aggregates while agent 1 repairs the boundary. Agent 3
may inspect app rules and build the practitioner UI against the agreed contract
while the backend is being implemented. Final tests must use the real integrated
contracts and routes, not a mock-only substitute. An isolated worktree does not
isolate PostgreSQL: use a dedicated test database or unique schema per worker,
never a shared database whose fixtures create/drop other agents' tables.

## Prompt for agent 1: provider core and integration

You are the provider-core implementer and integration owner. Read AGENTS.md,
CLAUDE.md, docs/migrations/PROVIDERS_MIGRATION.md and
docs/archive/PROVIDERS_EXECUTION.md first. Create an isolated worktree on a
codex/ branch from the documentation handoff commit. Announce your identity and
ownership to the other provider tasks. Use graft for context and call/reference
tracing. Do not spawn subagents.

Implement the adopted provider-core decisions and own integration of the other
two agents. Start with phase 1's authorization, audit and composite-constraint
repairs. Add actual route and persisted-audit tests, including rollback. General
PATCH must not bypass lifecycle commands. Replace the unused Person-based panel
operations with provider-based application operations called by production
routes; preserve meaningful behavioural tests and remove retired code only
after tracing its callers. Do not revive non-compete booking enforcement.

Publish exact core API contracts early. Implement independent practitioner
identity, owned contact data, partial updates, safe Admin-only account linking,
server-side search/filter/pagination, and the shared eligibility policy. Promote
structured profile/credential fields with validating migrations. Preserve data;
do not default malformed legacy profiles to active or accredited.

Own all edits to existing backend files, including session/outreach consumers,
shared registries and CI. Coordinate with agent 2 on affiliation/import interfaces
and integrate their new modules into real production routes. Extend one eligibility
policy with organisation approval and dated affiliation checks. Delegate generated
OpenAPI/frontend artifacts to agent 3; do not edit their outputs. Agent 2 owns new
organisation/vocabulary/import modules and agent 3 owns frontend files.

Commit coherent pieces, send contract/migration updates to the other agents, and
integrate their commits into your feature branch. Keep
docs/migrations/PROVIDERS_MIGRATION.md accurate: completed implementation, test
results and migration application are separate facts. Do not mark another
agent's tasks complete without their evidence. Coordinate migration parents and
use isolated test databases/schemas. Run the relevant backend checks and the
full PostgreSQL migration chain; require the provider migration CI job to
execute rather than skip its tests.

Your final handoff must identify the integration branch/worktree, base and head
commits, included agent commits, changed API contracts, migration order, exact
checks and results, skips/blockers, and remaining unchecked document items. Do
not deploy, import real sessions, push, or merge to the default branch. Send the
handoff to the review task named below for an independent review and address
its concrete findings before claiming completion.

## Prompt for agent 2: organisations and historical data support

You own new backend organisation, affiliation, vocabulary, alias and historical
import modules. Read AGENTS.md, CLAUDE.md,
docs/migrations/PROVIDERS_MIGRATION.md and docs/archive/PROVIDERS_EXECUTION.md
first. Start an isolated codex/ worktree from the handoff commit. Announce your
identity/ownership to the other provider tasks and use graft before source work.
Do not spawn subagents.

Implement tenant-owned organisations and dated affiliations with concurrent firms,
non-overlapping periods for the same pair, immutable endpoints and retained
referenced history. Publish request/response contracts and repository/policy
interfaces early. Agree session delivery context, affiliation references,
composite constraints and migration parents with agent 1. Supply the new modules
and tests; agent 1 owns edits to existing session routes/schemas, provider files,
registries and shared CI. Do not create a duplicate booking implementation.

Implement the global specialty vocabulary with platform write controls and
tenant-owned provider links. Implement tenant- and source-scoped aliases with
explicit identity reconciliation. Missing, unmapped and ambiguous practitioner
names must remain separate outcomes. Do not convert normalized names into
verified people or auto-create placeholders.

Implement an Admin-only, staged historical-import contract with provenance,
explicit direct/organisation/unknown delivery context and idempotency. It must
preserve verified past delivery by practitioners who are inactive today, reject
future bookings through the historical path, and avoid live booking/completion,
billing or authorization side effects. Use file hash plus row number only for
exact-file replay when stable upstream IDs are unavailable; require explicit
reconciliation across changed files. Do not import the real sessions.csv.

Test tenant isolation at the database and route boundaries, affiliation interval
edges and overlap rejection, preservation of old session attribution, vocabulary
permissions, ambiguous/missing aliases, replay and conflicting imports. Coordinate
integration tests with agent 1 using production paths and with agent 3 for the
organisation UI. Use a dedicated test schema/database and record PostgreSQL
migration evidence. Keep supplier-contract workflows and non-compete expansion
outside scope.

Commit completed slices and hand them to agent 1 with exact dependency edits,
migration parents and test evidence. Only agent 1 updates the shared migration
checklist. Your final report must give branch/worktree, commit IDs, delivered
interfaces, tests, integration requirements and any remaining gaps. Do not deploy,
import real data, push, or merge to the default branch. Send your handoff to the
review task for review; resolve its findings in coordination with the file owner.

## Prompt for agent 3: frontend and contracts

You own the provider frontend, generated contracts and integrated user-flow
verification. Read AGENTS.md, CLAUDE.md, docs/migrations/PROVIDERS_MIGRATION.md,
docs/archive/PROVIDERS_EXECUTION.md and applicable web/design rules. Use an
isolated codex/ worktree from the handoff commit. Announce your
identity/ownership and use graft for repository context. Do not spawn subagents.

Coordinate API contracts early with agents 1 and 2. Implement practitioner
create/edit with owned names and optional contact/account data, Admin-only
account-link controls, lifecycle actions requiring reasons, and a directory
with server-side search/filter/pagination and accurate totals. General edit
must not send protected lifecycle fields through PATCH. Preserve established
application design, loading/error handling, accessibility and permission patterns.

Build organisation management and dated-affiliation controls from agent 2's
actual contracts. Session booking must explicitly select direct or organisation
delivery and display server eligibility failures. Historical unknown context
must display honestly; do not default it to direct delivery. Preserve historical
attribution in session views. Historical import tooling remains backend-owned
unless an existing UI requires integration; do not invent a new import dashboard.

Own apps/web changes, generated route metadata, apps/web/src/api/generated/schema.ts
and apps/api/schema/openapi.json. Generate from the exact integrated backend
commit at each API milestone using the repository's established scripts. Do not
hand-edit generated artifacts or compensate for incorrect backend behaviour in
the browser. Hand backend bugs to their owner with a reproduction.

Run the appropriate web checks and verify real integrated flows: creation without
a login, clearable optional contacts, account permissions, lifecycle reasons,
listing beyond the first 100 providers, multiple affiliations, explicit session
attribution, and suspended/ineligible booking errors. Record the backend revision
used and distinguish mocked component tests from real integrated verification.
Coordinate with agent 1 to test the assembled feature branch after agents 1 and 2
are integrated. Commit final generated outputs only against that agreed revision.

Commit coherent slices, give agent 1 commit IDs and checks, and report any missing
API functionality. Only agent 1 updates the shared migration checklist. Your final
handoff must include branch/worktree, commits, backend revision, generated-contract
commands, test/build results, UI verification and remaining gaps. Do not deploy,
push, import real data, or merge to the default branch. Send the report to the
review task and address findings within your ownership.

## Independent review and completion

The review task is `Review providers migration`, ID
`01a076a5-c023-74a2-b32c-c49bb68f0387`. When available, use the Codex
`send_message_to_thread` tool to send a concise milestone or final handoff to that
task. Include role, branch, worktree, base/head commits, tests and actionable gaps.
Do not send recurring unchanged status updates. If task messaging is unavailable,
return the same handoff to the user to paste into the review task.

The reviewer checks implementation against the adopted decisions, inspects the
combined diff and actual consumers, reproduces suspected defects, and asks the
owning agent to correct concrete findings. Review must cover:

- Authorization, tenant constraints, audit persistence and atomic failure handling.
- Account independence and identity-link uniqueness without accidental role grants.
- Affiliation validity and stable historical attribution.
- Eligibility on all actual write paths, expiry boundaries and stale previews.
- Historical source truth, ambiguity, provenance and idempotency.
- One migration chain, representative PostgreSQL upgrade tests and no hidden skips.
- Generated contract alignment and real directory/booking flows.
- Remaining legacy Person provider paths and incomplete phase evidence.

Passing agent reports are inputs to review, not approval. Close findings only
with correction and verification evidence. Mark the migration implemented only
when the integrated acceptance gates pass; deployment remains a separate action.
