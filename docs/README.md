# Repository documentation

Migration decisions, review findings and design records that span both apps.
Documentation for a single app lives with it, in `apps/api/docs/` and
`apps/web/docs/`.

Paths in these documents are relative to the repository root.

Each document states its own baseline commit and date. Implemented, tested and
deployed are separate claims throughout; read the status line of a document
before treating its contents as current.

## migrations/

Decision records for a module's move to its current shape. These are the source
of truth for an accepted decision; reopen one explicitly rather than replacing
it in passing.

- [PROVIDERS_MIGRATION.md](migrations/PROVIDERS_MIGRATION.md) - provider
  organisations, practitioners and supplier contracts. Required reading before
  any provider work.
- [MEMBERS_MIGRATION.md](migrations/MEMBERS_MIGRATION.md) - persons to members,
  covering roster eligibility and portal account linkage.
- [SERVICES_MIGRATION.md](migrations/SERVICES_MIGRATION.md) - service catalogue
  and diagnosis taxonomy.

## handoffs/

Work breakdowns and agent handoffs. Ownership, branches and dependency gates.

- [SESSIONS_IMPLEMENTATION.md](handoffs/SESSIONS_IMPLEMENTATION.md) - session
  module task breakdown, sized one task per agent.

## reviews/

Findings recorded against a named commit. A review records evidence; it does not
imply the fixes were made.

- [MODULES_REPAIR_PLAN.md](reviews/MODULES_REPAIR_PLAN.md) - backend and
  frontend defects outside the provider migration, including the access-control
  findings.
- [SESSIONS_REVIEW.md](reviews/SESSIONS_REVIEW.md) - session documents against
  the implementation and the source extract.
- [PRACTITIONERS_REVIEW.md](reviews/PRACTITIONERS_REVIEW.md) - the practitioner
  workbook against the provider implementation.
- [FORMS_REVIEW.md](reviews/FORMS_REVIEW.md) - form sheets in `apps/web`,
  separating what was applied from what is suggested.
- [AUDIT_COVERAGE.md](reviews/AUDIT_COVERAGE.md) - which writes reach
  `audit_logs`, and which deliberately do not.

## gaps/

Capability gaps: something a person cannot currently do in the product.

- [IMPORT_REVIEW_UI_GAP.md](gaps/IMPORT_REVIEW_UI_GAP.md) - which import types
  can be reviewed in the UI and which cannot. The verdict is not uniform.
- [TAXONOMY_MANAGEMENT_GAP.md](gaps/TAXONOMY_MANAGEMENT_GAP.md) - taxonomy
  changes require file edits and scripts, with no admin UI.
- [ORPHANED_ENUMS.md](gaps/ORPHANED_ENUMS.md) - enums defined but referenced
  nowhere.

## design/

Proposals and product decisions. Design judgement, distinguished in each
document from the evidence it rests on.

- [PAGES_REDESIGN.md](design/PAGES_REDESIGN.md) - members, practitioners and
  session pages.
- [NAVIGATION_SEARCH_PLAN.md](design/NAVIGATION_SEARCH_PLAN.md) - global header,
  profile menu and search.
- [WELLNESS_NUGGETS_DECISION.md](design/WELLNESS_NUGGETS_DECISION.md) - wellness
  nugget email delivery and delegation.

## operations/

- [DEV_DATA_LOAD.md](operations/DEV_DATA_LOAD.md) - what was loaded into the dev
  database from the client workbooks, in order, with the counts each pass
  produced.

## archive/

Finished work, kept for the record and still cited as evidence. Not current: do
not follow its instructions, branches or worktree paths. See
[archive/README.md](archive/README.md).

- The three-worktree execution of the provider migration
  ([PROVIDERS_EXECUTION.md](archive/PROVIDERS_EXECUTION.md),
  [PROVIDERS_INTEGRATION_HANDOFF.md](archive/PROVIDERS_INTEGRATION_HANDOFF.md),
  [PROVIDERS_FRONTEND.md](archive/PROVIDERS_FRONTEND.md)), merged into
  `chore/monorepo`. The decisions themselves stay in
  [migrations/PROVIDERS_MIGRATION.md](migrations/PROVIDERS_MIGRATION.md).

## Related

- [AGENTS.md](../AGENTS.md) and [CLAUDE.md](../CLAUDE.md) - working rules for
  every agent in this repository.
- [apps/api/docs/](../apps/api/docs/) - backend module and taxonomy documents.
- [apps/web/docs/](../apps/web/docs/) - frontend dashboard and design documents.
