# Sessions: implementation tasks

Companion to `SESSIONS_REVIEW.md`, which holds the evidence and the decisions.
This document is the work breakdown: one section per task, sized so that a task
is one agent's assignment and one commit or a short series of them.

Written against `c646fe2` on `chore/monorepo`. Sessions are not behind a feature
flag, so this module is in scope under the paused-module rule in
`MODULES_REPAIR_PLAN.md`.

## How to run this with more than one agent

**Phase A is one agent's job. Do not split it.** It changes one aggregate, its
table, its mapper and its migration together; splitting that across agents
produces a broken intermediate state and a merge conflict in every file. The
other phases split cleanly.

Suggested waves, assuming you want the shortest wall-clock:

| Wave | Runs in parallel | Blocked until |
| --- | --- | --- |
| 1 | **A** (one agent, all of Phase A) and **B1** (one agent) | now |
| 2 | **B2+B3** (one agent) and **C1+C2** (one agent) | A merged |
| 3 | **C3+C4** (one agent) | C1 merged |
| — | **D** | not code; needs the counselling team |

B1 is safe in wave 1 because it touches only the staging service, which Phase A
does not open.

### Rules every agent on this work follows

- Read `CLAUDE.md` first and follow it, particularly the comment, writing,
  commit and disagreement rules.
- **Own only the files your task lists.** If you need a change in a file another
  task owns, say so in your report rather than making it.
- Stage by path when committing. No `Co-Authored-By`, no tool attribution.
- Use your own database: `createdb eap_sessions_<task>`, and pass it as
  `TEST_DATABASE_URL` and friends. Do not use `eap_test`.
- **Known pre-existing failure, not yours:**
  `tests/integration/test_provider_audit_persistence.py::TestAuditRecordsPersist::test_an_unchanged_command_writes_neither_state_nor_audit`.
  It fails at `75d500c` too and belongs to the provider worktrees. Any other
  failure is yours.
- Do not commit `apps/web/src/api/generated/` or `apps/api/schema/openapi.json`.
  Run `pnpm contracts:sync` from `apps/web` so your types resolve, but leave
  those two paths out of your commits and say in your report that the schema
  changed. Contracts are regenerated centrally.
- Verification, from `apps/api`:
  `uv run ruff check app tests scripts && uv run ruff format --check app tests scripts && uv run lint-imports`,
  then `pytest tests/unit -q --cov=app --cov-report= --cov-fail-under=60`,
  then `pytest tests --ignore=tests/unit -q` with the five database URLs set.
  From `apps/web`: `pnpm lint && pnpm typecheck && pnpm test`.
- A test that does not fail before your change is not evidence. Revert your
  change, watch it fail, put it back, and say so in your report.

---

# Phase A — a session belongs to a client, and may have no member

Closes S-01, S-02, S-03. One agent. Migration parent is `a1p3d0d2e4f6`; check
`uv run alembic heads` first, as another branch may have extended the chain.

### A1. Enums

**Owns** `app/domain/enums/session.py`.

Add `SessionAttendance` with `INDIVIDUAL = "Individual"` and
`COMPANY_WIDE = "CompanyWide"`. Add `TERMINATED = "Terminated"` to
`SessionClinicalStatus`.

**Done when** both are exported wherever the other session enums are, and
`getStatusLabel` on the frontend renders `CompanyWide` as "Company Wide" (it
splits on the case boundary already, so verify rather than assume).

### A2. Aggregate

**Owns** `app/domain/entities/service_session.py`, `tests/unit/domain/`.

Add `client_id: ClientId` (required) and `attendance: SessionAttendance`. Change
`member_id` to `EligibleMemberId | None`.

Put the invariant on the entity, not only in the route: a `CompanyWide` session
has no member; an `Individual` session has one. Raise `DomainError` otherwise.

**Done when** unit tests cover both directions of the invariant and a
`CompanyWide` session with a headcount and no member constructs cleanly.

### A3. Table, migration, mapper, repository

**Owns** `app/infrastructure/models/service_session_model.py`,
`app/infrastructure/mappers/service_session_mapper.py`,
`app/infrastructure/repositories/service_session_repository.py`,
a new file under `alembic/versions/`,
`app/infrastructure/models/eligible_member_model.py` (one index only).

Columns: `client_id String(25) NOT NULL index`, `attendance` NOT NULL, and
`member_id` altered to nullable.

Constraints, all following idioms this table already uses. Read them first:
`fk_service_sessions_provider_tenant` and
`session_affiliation_matches_context_check` are the models to copy.

- `ForeignKeyConstraint(["tenant_id", "client_id"], ["clients.tenant_id", "clients.id"], ondelete="RESTRICT")`.
- `CheckConstraint("(attendance = 'CompanyWide') = (member_id IS NULL)", name="session_attendance_matches_member_check")`.
- `ForeignKeyConstraint(["tenant_id", "client_id", "member_id"], ["eligible_members.tenant_id", "eligible_members.client_id", "eligible_members.id"], ondelete="RESTRICT")`
  so the database refuses a member from another client. This needs a new
  `UniqueConstraint("tenant_id", "client_id", "id")` on `eligible_members`; it
  is a superset of the primary key, so it is guaranteed unique.
- Rewrite `session_clinical_outcome_check` to include `Terminated`.

Migration order, safe because `member_id` is `NOT NULL` today and so every
existing row resolves a client:

1. add `client_id` and `attendance` nullable
2. `UPDATE service_sessions s SET client_id = m.client_id FROM eligible_members m WHERE m.id = s.member_id AND m.tenant_id = s.tenant_id`
3. `UPDATE service_sessions SET attendance = 'Individual'`
4. set both `NOT NULL`, alter `member_id` nullable
5. add the index and the four constraints

The **downgrade must raise** if any `CompanyWide` row exists rather than
dropping columns that hold the only record of those sessions.

`issue_topic` and `partner_name` are encrypted at rest; see
`tests/unit/infrastructure/test_service_session_encryption.py` and do not
disturb that.

**Done when** the migration runs forward and back on a real PostgreSQL database
with rows present, `test_session_member_migration.py` still passes, and a new
test asserts the check constraint rejects a `CompanyWide` row that carries a
member and an `Individual` row that does not.

### A4. API

**Owns** `app/api/schemas/service_session_schemas.py`,
`app/api/routes/service_sessions.py`,
`app/application/use_cases/service_session_use_cases.py`,
`tests/unit/api/`, `tests/e2e/test_service_session_api.py`.

Add the three fields to create, update and response schemas. Validate in the
application layer that an `Individual` session's member belongs to the session's
client, and that a `CompanyWide` session carries a headcount. Headcount is
application validation only, **not** a check constraint: 614 historical group
rows have none and a constraint would make them unwritable.

Do not touch the authorization lines in this route file. They were fixed under
SEC-01 through SEC-04 and are held by that work.

**Done when** creating a company-wide session with a client, a headcount and no
member returns 201, creating one with a member returns 422, and creating an
individual session whose member belongs to a different client returns 422.

### A5. Frontend

**Owns** `apps/web/src/components/ServiceSessionFormSheet.tsx`,
`apps/web/src/routes/service-sessions/new.tsx`,
`apps/web/src/routes/service-sessions/$sessionId.tsx`,
their tests.

The form picks the attendance first, because it decides what the rest of the
form asks for: a member and no headcount, or a client, a headcount and no
member. The client is always required.

**Done when** a company-wide session can be created end to end and the detail
page renders one without a member rather than showing "Member unavailable".

---

# Phase B — import staging

Closes S-04 and S-06. **No row is imported before this exists.**

### B1. Replay-key preflight

**Owns** `app/application/services/session_import_staging.py`,
`tests/unit/application/test_session_import_staging.py`.
Runs in parallel with Phase A.

`_replay_key` is already correct: it uses `source_record_key` when present and
`file:{hash}:row:{n}` otherwise. The danger is upstream. `ACTIVITY LOG ID` looks
like a stable key and is not: 7,079 distinct values across 7,465 rows, 669 rows
colliding in 283 groups. Fed in as `source_record_key`, those 669 rows are
marked `Duplicate` and silently dropped.

Add a preflight over the whole file, before any row is staged: if the nominated
source-key column is not unique across the file, refuse the batch with an error
naming the column and a sample of the collisions. Record the file hash and which
key strategy was used on the batch.

**Done when** a synthetic file with a repeated source key is refused with that
message, a file with unique keys stages normally, and a file nominating no key
column stages on `file:{hash}:row:{n}`.

**Decided (B1, implemented).** Blank values in a nominated key column refuse the
batch alongside repeats, so the rule is completeness and uniqueness, not
uniqueness alone. A blank falls back to `file:{hash}:row:{n}` while its
neighbours use `key:{...}`, which keys one batch two ways: a re-export under a
new hash restages exactly the blank-key rows and returns the rest as duplicates.
`ACTIVITY LOG ID` is blank on 5 of 7,470 rows, so the two rules differ on this
file. Both faults are reported in one message so an operator sees the whole
problem in a single upload.

**No new column.** The batch already records how it was keyed:
`session_import_batches.file_hash` and `source_record_key_field`, which is NULL
exactly when the file-and-row strategy applies. `replay_key_strategy()` in
`session_import_staging.py` names the strategy from that stored column, so a
reconciliation reading a stored batch needs no access to the file. A separate
strategy column would duplicate `source_record_key_field` one-for-one.

**Counts reproduced from the extract** at
`0e8fa212455ea42bba48574eb46c639ade1238bc9fa7382bfc7eee1951774e44`: 7,470 rows,
`ACTIVITY LOG ID` non-empty on 7,465 with 7,079 distinct, 283 repeated values
spanning 669 rows. The rows actually lost to `Duplicate` would be 386, not 669:
the first row of each group stages normally, so the loss is 669 - 283.

### B2. Normalisation tables

**Owns** a new module under `app/shared/utils/` or
`app/application/services/`, plus its tests.
**Depends on** A1 for `SessionAttendance` and the new outcome.

One version-controlled mapping per column, applied at staging, with `Unmapped`
for anything not listed. Never `.title()`, never fuzzy matching.

Engineering can decide these now: `SESSION TYPE` (5 spellings, 2 values),
`CATEGORY` (50 spellings, 4 values), `CLIENT TYPE`, `INTERVENTION` (26 values,
map to the service catalogue).

**`GENDER` is not a mapping job.** `Group` appears as a gender on 642 rows and
is not one; it is the signal that the row is `CompanyWide`. It maps to
attendance, and the member gender is absent.

**Blocked on a clinician**, and must not be guessed: `DIAGNOSIS TYPE` (63
values), `DIAGNOSIS` (251), `CLASSIFICATION` (28). Stage these as `Unmapped`
until the controlled list exists. Say so in the report rather than inventing a
mapping to unblock yourself.

**`CLIENT FEEDBACK` is not imported as a category at all.** 56 free-text
spellings, and PRIV-01 forbids free text reaching an employer aggregate.

**Done when** every distinct value in the source file either maps or is
reported as `Unmapped`, and a test asserts the count of each per column so a
future file that drifts is visible.

**Decided (B2, implemented).** The tables live in
`apps/api/app/shared/utils/session_import_normalisation.py`, importable from
any layer, importing only `app.domain.enums`. Lookup keys are strip, collapse
internal whitespace, casefold; no other transformation. Blank returns `None`,
an unlisted value returns `Unmapped(column, value)`, and nothing defaults.
Every entry was enumerated from the reference extract at
`0e8fa212455ea42bba48574eb46c639ade1238bc9fa7382bfc7eee1951774e44`
(7,470 populated rows).

- `CATEGORY`: 25 of the 50 distinct spellings map, covering 7,024 rows; 49
  rows across the other 25 spellings stay `Unmapped` and 397 are blank. The
  rule adopted: spellings naming a session format map (including the typos
  `Indididual` and `individuual`, and the group formats `Onsite Group`,
  `Health talk`, `Group Presentation`); spellings naming a topic or time stay
  unmapped (`Depression`, `Relationship`, `Marriage`, `10:00AM`, `online`).
  The file's own `SESSION CATEGORY` column corroborates this: rows with
  `CATEGORY` of `Relationship` or `Post RTA debrief and sessions` are cleaned
  there as `Individual`, so topic spellings do not indicate the format. Known
  per-row inconsistency: 6 of the 50 `Group session` rows are cleaned as
  `Couples`; the mapping is per value and maps the spelling as written.
- `GENDER` is a classifier, not a gender mapping: `Female`/`Male` spellings
  return `MemberGender` (6,828 rows), `Group`/`group` return
  `SessionAttendance.COMPANY_WIDE` (642 rows), nothing else appears.
- **Blocked on a clinician:** the `DIAGNOSIS TYPE` (63 distinct),
  `DIAGNOSIS` (251) and `CLASSIFICATION` (28) tables exist and are empty, so
  every value stages as `Unmapped` until the controlled clinical list exists.
  Engineering must not populate them.
- `CLIENT FEEDBACK` has no mapper by design; PRIV-01 forbids the free text
  reaching an aggregate. The module docstring says so.
- `INTERVENTION` (26 distinct) maps to the service catalogue, not to a domain
  enum, so it needs catalogue identifiers and belongs to the staging wiring
  task, not to this module. Still open.

### B3. Status mapping

**Owns** the same module as B2. Same agent.

The source status spans two enums. `Ongoing` to `ToBeContinued`, `Completed` to
`Completed`, `Referred` to `Referred`, `Terminated` to the new `Terminated`, and
`No Show` to `SessionStatus`, not to a clinical outcome. The 811 rows with no
status get none; do not default them.

**Decided (B3, implemented).** `map_status` returns a frozen `StatusMapping`
with `clinical_status` and `session_status` fields, exactly one set, so a
caller cannot collapse the two enums into one string. On the reference
extract: 6,658 rows map to a clinical status (6,408 `Ongoing`, 215
`Completed`, 25 `Referred`, 10 `Terminated`), 1 `No Show` row maps to
`SessionStatus.NO_SHOW`, 811 blanks return `None`, and nothing is unmapped.

---

# Phase C — the read path

Closes S-07 and S-08, and finishes the UI begun in `7a9ab41`.

### C1. Hydrate the list response

**Owns** `app/api/schemas/service_session_schemas.py`,
`app/api/routes/service_sessions.py`,
`app/infrastructure/repositories/service_session_repository.py`.
**Depends on** Phase A merged.

Add `client_id`, `client_name`, `member_display_label`, `provider_display_name`
and `service_name` to the list response. The members list already does this with
`client_name`; copy that approach and resolve in one query, not per row.

This is what lets the Client column render for company-wide sessions, which have
no member to read it from.

**Done when** a list response carries the names, and a test asserts the endpoint
issues a bounded number of queries for a 20-row page rather than one per row.

### C2. Constrain sorting

**Owns** the same files as C1. Same agent.

`sort_by` is a free string passed through. Constrain it to an explicit list,
reject anything else with 422, and include the columns the UI now shows that
can be sorted server-side.

### C3. Consume the hydrated response

**Owns** `apps/web/src/routes/service-sessions/index.tsx`,
`apps/web/src/api/endpoints/service-sessions.ts`.
**Depends on** C1 merged.

Remove the per-row `membersApi.getById` and the services and providers lookup
queries, and read the names off the row. Render the Client column from the
session's own client, not the member's.

**Done when** a 20-row page issues one request, and the sessions list tests
still pass.

### C4. Filters

**Owns** the same frontend files as C3, plus the query parameters in
`app/api/routes/service_sessions.py` if C1's agent has finished with it.

Add counsellor, mode, category and outcome filters. These are the dimensions an
operator slices by and none are filterable today.

---

# Phase D — better than the activity log

Not code. Each item needs the counselling team to agree before a field is made
required, and each is recorded in `SESSIONS_REVIEW.md` with its evidence.

- **Require headcount on company-wide sessions.** Recorded on 28 of 7,470 rows
  today, so group reach is currently unmeasurable.
- **Retire `ISSUE GROUP`** (6,492 of 7,470 are `Other`) and
  **`PARTNER RELATIONSHIP`** (empty in all 7,470) from reporting.
- **Stop collecting gender as a session shape**, once A1 makes attendance
  explicit.
- **Consider a controlled feedback scale**; 3,357 rows already have no feedback,
  so the field is closer to optional than it looks.

---

## Sequencing summary

```
A1 → A2 → A3 → A4 → A5        (one agent, serial)
B1                             (parallel with all of A)
        A merged → B2 → B3     (one agent)
        A merged → C1 → C2     (one agent)
                   C1 merged → C3 → C4   (one agent)
D: not code
```

Blocked and needing a person, not an agent: the clinical vocabulary in B2, and
every item in Phase D.
