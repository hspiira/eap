# Archived documents

Records of work that is finished. They are kept because they explain how
something was built and what was verified at the time, and because the decision
records still cite them as evidence.

They are not current. Do not follow their instructions, branches or worktree
paths, and do not treat their status claims as describing the code today. When
an archived document disagrees with a document under `docs/migrations/`, the
migration record wins.

## Provider migration, archived 2026-09-10

The three-worktree execution of the provider migration. The work described here
is merged into `chore/monorepo`, the `wt-agent1`, `wt-agent2` and `wt-agent3`
worktrees they name no longer exist, and the `codex/providers-agent*` branches
they coordinate are dormant per the 2026-09-07 entry in
`docs/migrations/PROVIDERS_MIGRATION.md`.

- [PROVIDERS_EXECUTION.md](PROVIDERS_EXECUTION.md) - the three-agent execution
  plan, working agreement and per-agent prompts.
- [PROVIDERS_INTEGRATION_HANDOFF.md](PROVIDERS_INTEGRATION_HANDOFF.md) - what
  the integration branch contained at handoff, with its check results.
- [PROVIDERS_FRONTEND.md](PROVIDERS_FRONTEND.md) - the frontend and generated
  contracts record, separating implemented, tested against mocks, verified
  against a real backend and deployed.

Provider decisions themselves are not archived. They remain in
`docs/migrations/PROVIDERS_MIGRATION.md`, which is still the source of truth for
provider work.
