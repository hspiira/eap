# Import review UI: what exists and what does not

Recorded 2026-09-08. Scope: whether a person can review and resolve a flagged
import row from the application UI itself, without direct API calls or
backend scripts. This is not uniform across import types — do not generalize
one verdict to all of them.

## Already has real in-UI review

- **Client import** (`apps/web/src/components/clients/ClientImportDialog.tsx:70,168,303`):
  each row previews with a `default_action`; a person can override the action
  per row (`updateDecision`, `ClientImportDecision`) before confirming.
- **Member import** (`apps/web/src/components/members/MemberImportDialog.tsx:97,145,177,443-456`):
  same shape — a per-row Import/Skip select overrides the default decision
  before the batch runs.

## Flagged only, no way to resolve in the UI

- **Session import** (`apps/web/src/components/sessions/SessionImportDialog.tsx:68-79,297,321-331`):
  the review queue lists rows by outcome (`UnresolvedClient`,
  `UnresolvedMember`, `UnresolvedService`) and pages through them, but the only
  actions are batch-level `Apply`/`Abandon`. There is no per-row action.
  Fixing an unresolved row means fixing the underlying client/member/service
  record elsewhere and re-staging the whole file, not resolving it in place.
- **Practitioner import / provider aliases**: confirmed API-only in
  `docs/migrations/PROVIDERS_MIGRATION.md:49,708-711` — "Alias review queue is
  API-only... an operator cannot resolve an ambiguous name without direct API
  calls." No frontend component consumes `GET /provider-aliases`
  (`apps/api/app/api/routes/provider_aliases.py:67-69`).

## Why this matters right now

Two queued items are blocked on this gap specifically, not just on the
underlying data decisions already tracked elsewhere:

- 109 practitioner rows sitting in "needs review"
  (`docs/reviews/PRACTITIONERS_REVIEW.md`,
  `practitioner-import-review/README.md:53-55`).
- 142 unmapped provider aliases (`docs/operations/DEV_DATA_LOAD.md`).

Session import's unresolved rows are visible in the dialog but equally not
fixable in place.

## Status

Missing capability, not a defect. Nothing here means a row was imported
incorrectly — client and member import already prove the pattern works.
Bring session-import and practitioner-import review to the same per-row
resolution UI client and member import already have.
