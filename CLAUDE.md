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

## Coordination

- Several agents work in this repo at once. Before editing shared paths, check
  who holds what with `ListAgents` and `SendMessage`, and say where you are
  working.
