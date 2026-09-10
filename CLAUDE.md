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
  `CLAUDE.md` and any applicable app-specific agent and design rules.
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

- Follow `docs/migrations/PROVIDERS_MIGRATION.md` for provider work. Keep its
  decisions and phase evidence current; reopen a decision explicitly before
  replacing it.
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

## Execute the assigned task

- Complete the assigned scope, run the relevant checks, commit your work, and
  hand back the result. Do not turn a bounded task into an open-ended discussion,
  review cycle, or project-wide improvement effort.
- Make routine, reversible implementation decisions yourself within the agreed
  scope and rules. Do not ask the user or other agents to approve each step,
  reconfirm existing authorization, or debate choices already settled.
- Do not expand scope, implement unsolicited features, refactor unrelated code,
  or direct other agents to do unassigned work. Necessary changes to complete
  the assigned task are in scope; adjacent improvements are not.
- The discoveries rule is not permission to expand scope. Record an unrelated
  finding once in the appropriate handoff document with evidence and a concrete
  follow-up, then continue your task. Fix it now only if it is within your scope.
- Contact another agent only for a shared-path conflict, required dependency,
  actionable correction affecting assigned work, or completed handoff. Send the
  evidence and exact request together. Do not send acknowledgments, repeated
  status requests, speculative suggestions, or agreement/disagreement loops.
- When coordination is required, make one concise request and continue
  independent work. Wait only on the dependent portion. Silence does not grant
  permission to edit another agent's files or take over its assignment.
- Escalate only when missing information, conflicting requirements, an ownership
  conflict, or an authorization boundary prevents safe progress. State the
  blocker, what you checked, and the smallest decision needed in one message.
- Keep progress updates brief and factual. Do not repeatedly narrate unchanged
  status, reread settled context, or rerun passing checks without a new reason.
- Once acceptance criteria and required checks are satisfied, stop. Deliver
  what changed, verification, commit references, and any recorded limitations.
  Do not initiate another review round or wait for ceremonial sign-off.
