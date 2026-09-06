# Working rules for this repo

Rules the user has set. They apply to every agent working here, and to future
sessions. Add to this list when the user gives a new rule; do not remove one
without being asked.

## Comments

- Do not add unnecessary comments. Most code does not need one.
- A comment explains what a function or method does. It is not a place for
  narration, history, or reasoning at length.
- Keep comments short and grammatical. No verbose block comments.
- While editing a file, delete comments that are unnecessary.

## Implementation

- Read and follow the project agent rules before starting work, including
  `AGENTS.md` and any applicable app-specific agent and design rules.
- Reduce cyclomatic complexity when writing or touching code. Prefer small,
  focused functions and components over long branching handlers.

## Writing

- Avoid em dashes.
- Avoid uppercase for emphasis unless asked for it.
- Keep a professional tone.

## Commits

- Commit your work when a piece of it is finished. Do not leave it sitting in
  the working tree.
- Commit with no affiliation: no `Co-Authored-By` trailer and no tool
  attribution in the message or PR body.
- Stage by path. Several agents share this tree, so commit only your own files.

## Discoveries

- Never leave a new discovery unattended. Fix it there and then if you can. If
  you cannot, either record it where it will be picked up again or hand it to
  another agent by name. Do not simply mention it and move on.

## Disagreement

- Always disagree when the evidence supports it, including with the user and
  with a design they have already proposed. Agreement is not the default.
- Back a disagreement with evidence: a `file:line`, a query result, a count
  from the data. An opinion without a citation is not a disagreement, it is a
  preference, and it should be labelled as one.
- Say plainly which parts of a proposal you accept and which you reject. Do not
  soften a rejection into a partial agreement.
- Separate what the evidence shows from what you inferred. When a
  recommendation rests on judgement rather than a citation, say so and name who
  should confirm it.
- If you never evaluated something, say that rather than implying a position.

## Data and sources

- Never invent data, statistics, sources, or references. Research and cite
  something real, or say plainly that there is no verified source.

## Design decisions and migration evidence

- When the user delegates a design choice, decide within that scope and record
  the choice, reason, assumptions, and implementation consequences. Distinguish
  adopted policy from verified data; do not turn missing facts into assumptions
  presented as evidence.
- Keep migration decisions and unresolved findings in version-controlled
  handoff documents. Separate implemented, tested, and deployed status. A
  collected or skipped test is not a passing verification gate.

## Provider module

- Follow `PROVIDERS_MIGRATION.md` for provider work. Keep its decisions and
  phase evidence current; reopen a decision explicitly before replacing it.
- Keep practitioner identity, user accounts, organisation affiliations, and
  supplier contracts distinct. Preserve historical session attribution.
- Enforce tenant relationships in application validation and database
  constraints. A migration preflight alone does not enforce future writes.
- Use one authorized, audited mutation path for provider lifecycle changes.
  General profile updates must not bypass it. Verify persisted audit records
  and rollback behaviour, not only that an audit helper was called.
- Keep new-booking eligibility separate from historical import acceptance.
  Preserve source provenance and quarantine unresolved identities; never
  invent practitioners or infer identity from a normalized name alone.

## Coordination

- Several agents work in this repo at once. Before editing shared paths, check
  who holds what with `ListAgents` and `SendMessage`, and say where you are
  working.
- Focus on your own work. Message another agent when there is a reason to:
  a shared path, a handoff, a correction they need. Not to acknowledge, agree,
  or continue a thread that has nothing left in it.
- Prefer one message that closes the loop over several that keep it open.
  Correspondence is not progress on the task.
