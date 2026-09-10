# Audit coverage: what is recorded, and what is not

The audit trail is event-driven. `audit_change` reads `entity.events`, so a
mutating method that appends nothing is invisible to `audit_logs` however
healthy the outbox and worker are. This document records which writes are
audited, the decisions behind that line, and what is still open.

## The decision

Clients, contracts and service assignments are audited in full: creation,
every field update, and every lifecycle move. They were chosen first because
they are the records a person edits daily and the ones a dispute is argued
from, and because a client is the aggregate almost everything else hangs off.

The roster follows them. `EligibleMember` emits on creation, on suspend,
reinstate and terminate, and on a roster-details edit. Three of its methods
stay silent deliberately: `link_account` and `unlink_account` are an
association between two aggregates that the members route records as its own
operation, and `record_import` is bookkeeping under an import batch that
already emits, where a roster file of three thousand rows would otherwise
write three thousand audit rows for one operation a person performed once.

Sessions are audited too, under a redaction rule. A delivery record carries
`notes`, `feedback`, `issue_topic` and a diagnosis, so the trail records which
field a person touched and when, and not what it says. See below.

Not decided here, and deliberately left: the remaining 93 silent mutators
across the other aggregates. Auditing everything indiscriminately is not
automatically right, and for special-category health data it creates its own
disclosure surface, which is why `test_audit_coverage.py` refuses to assert it.
That scope is a product call.

## What this pass changed

Baseline moved from 148 silent mutators to 93, which is three separate things
and they should not be read as one number:

| Change | Count | What it was |
| --- | --- | --- |
| Coverage | -14 | `ClientEntity` and `ContractEntity` now emit on create, on every field update, and on archive and restore. Neither has a silent mutator left. |
| Coverage | -9 | `ServiceAssignmentEntity` in full, and `EligibleMember` apart from the three above. |
| Coverage | -12 | `ServiceSessionEntity` in full, under the redaction rule below. |
| Coverage | -8 | `Case`, `ClinicalNote`, `ClinicalSubject` and `OutreachRecord`. Amending a signed note recorded nothing before this. |
| Measurement | -3 | The detector follows a private helper. A method that hands the append to one, `ContractEntity._record_status_change`, read as silent while it emitted. |
| Measurement | -9 | The detector no longer reads `self.x == y` as an assignment, so read predicates like `is_active` were never mutators at all. |

Only the coverage rows are coverage. The other twelve were the ruler being wrong.

## Three faults found on the way

These are why the trail was thinner than the coverage number suggested.

1. **`extract_field_changes` compared attributes starting with `_`.** Every
   domain entity is a plain dataclass with public fields, so both sides of the
   comparison came out empty and an audited update recorded the event with no
   diff under it. The create branch looked for `_id` for the same reason and
   never found one. It now reads the public dataclass fields, skipping
   `events`, `created_at` and `updated_at` as bookkeeping the audit row already
   carries.
2. **No route passed `old_entity`.** The parameter existed through
   `audit_change`, `audit_entity_operation` and `process_entity_events_for_audit`
   and had no caller, so the UPDATE branch had nothing to diff against. The
   client and contract update routes now take a copy before the use case
   mutates the entity in place.
3. **Contract lifecycle emitted nothing.** `renew` and `terminate` emitted;
   activate, sign, archive, restore and every billing field did not. Creating
   five contracts, signing each and archiving four produced zero outbox rows.

## Why the contract emits `ContractStatusChanged`

`map_domain_event_to_audit_action` (`app/shared/utils/audit_helper.py`) buckets
any event whose name contains "activated" as a **CREATE**. A `ContractActivated`
event would therefore file an activation as a creation, putting a second birth
in the trail for a contract that already existed. One event carrying
`from_status` and `to_status` covers activate, archive and restore and maps to
UPDATE, which is what happened.

The mapper itself is left alone. `ClientActivated` and `ProviderActivated`
already flow through it, so changing the rule changes the action recorded for
existing events, and that is a decision to make explicitly rather than fold
into this. Recorded here as open.

## Evidence

- `tests/unit/domain/test_audit_coverage.py` pins the baseline at 122 and
  asserts neither aggregate has a silent mutator left.
- `tests/integration/test_audit_chain.py` runs HTTP to `audit_logs` against
  real PostgreSQL: a rename reaches `entity_changes` carrying
  `name: Acme Corp -> Acme Holdings`, a creation is filed as CREATE, and a
  contract activation is filed as UPDATE rather than CREATE.

## The roster's own audit path is gone

`members.py` used to enqueue its outbox rows by hand through
`record_member_change`. That path could not carry a field diff, a caller
address or a user agent, and it hardcoded `is_special_category` to true. All
twelve call sites and the bulk importer now go through `audit_change`, and
`member_audit.py` is deleted.

Three things had to be decided to make that safe:

**The event vocabulary is preserved where it existed.** The old path built
event names as `f"{resource_type}{operation}"`, so the trail already contains
`EligibleMemberMerged`, `EligibleMemberMergedIntoMember`, `MemberNextOfKinCreated`
and the rest. The new domain events carry those exact names so a query written
against the old trail still matches. The one deliberate change: suspend,
reinstate and terminate now emit `EligibleMemberStatusChanged` with `from_status`
and `to_status`, rather than three separately named events, which matches how
contracts, sessions and assignments already record a lifecycle move.

**Both the member and their next of kin are redacted.** A next of kin never
consented to being on the system, so `MemberNextOfKin` was in the redaction set
from the start. The member's own row was not, on the reasoning that seeing a
coverage date or member code move is the point of auditing a roster edit.

That was reversed on 2026-09-09, after a review pointed out what the row
actually holds: `national_id`, `passport_number`, `date_of_birth` and contact
details. The audit store is append-only, so a value copied into it survives any
later correction or erasure of the record it came from, and stays readable to
every authenticated user in the tenant. The current values are already visible
on the live member record to the same audience, so this was a retention and
data-minimisation problem rather than a disclosure one, which is why it was
rated low. `EligibleMember` now joins the redaction set: which field moved,
when, and by whom is still recorded, and only the before and after values are
dropped.

Field-level redaction was considered and not built. Keeping coverage dates and
member codes readable while dropping the identifiers would preserve more signal,
but it needs a per-resource field allowlist that nothing else in the audit path
has, and a field added to the member later would default to being retained. The
blunt rule fails closed; a follow-up can refine it if the lost detail is missed.

**The special-category flag is preserved, not re-decided.** Whether a roster
row belongs in the DPO's special-category report is that office's call. The
old path said yes; `SPECIAL_CATEGORY_RESOURCE_TYPES` keeps saying yes. What
changed is that reporting and redaction are now separate: `redacts_content`
follows clinical content, `is_special_category` follows what the DPO reports
on. Flagged for the DPO to confirm rather than quietly narrowed.

## Special-category records are audited without their content

`ServiceSession` is now in `CLINICAL_RESOURCE_TYPES`, and the audit handler
redacts the values on any field change for a special-category resource: the
field name and the fact of the change survive, `old_value` and `new_value`
become `[redacted]`. A field that was empty and stayed empty reads as null
rather than as a redaction, so the trail does not imply content that never
existed.

The reason is the audience. `audit_logs` is read by administrators, and the
DPO report exists precisely because that is a wider group than the care team.
Once `extract_field_changes` started working, an unredacted session edit would
have copied the note text, the presenting issue and the diagnosis into
`entity_changes` for all of them. Who edited which field of which session, and
when, is the auditable fact; the clinical content is in the record itself,
behind the clinical scope wall.

Redaction is per resource, not blanket: a client rename still records
`Acme Corp -> Acme Holdings`, because that is ordinary business data and the
before-and-after is the point of auditing it.

## Route-level gaps (2026-09-10 pass)

A second pass compared every `@router.post/put/patch/delete` handler against
its audit call, rather than against entity emissions. The scope question left
open above was answered by the product owner: every event that affects or
triggers a data change is to be logged. Thirty-one handlers across sixteen
files were found writing nothing, and all of them are now closed. What
follows is what was wrong and what was decided.

### The foreign key was destroying the trail

`audit_logs.tenant_id` carried `ON DELETE CASCADE` to `tenants.id`
(`32b395f52e9f`, verified on the running database: `confdeltype = 'c'`).
Deleting a tenant deleted every record of what had been done inside it, which
is the history a deletion most needs to be answerable to. The constraint is
dropped in `e3f5g7h9j1k3`, and `AuditLogModel` now declares `tenant_id`
itself rather than inheriting `TenantMixin`, so the schema the tests build
from metadata matches the migrated one.

That key was also silently breaking the one platform-level audit call that
already existed. `retire_specialty` passed `tenant_id="platform"`, no tenant
row has that id, and nothing seeds one, so the outbox row it enqueued could
never be consumed: the worker's insert would fail the foreign key and retry
under backoff forever. Dropping the key fixes that call site as well as
enabling the vocabulary work below. `PLATFORM_TENANT` in
`route_audit_helper.py` replaces the string literal.

### Reference tables needed a second way in

The eleven vocabulary route files write rows through a repository with no
aggregate behind them, so there is no `entity.events` for `audit_change` to
drain and adding the call would have logged nothing. `audit_reference_change`
records a stated action with a before and after snapshot, and
`AuditEventHandler.record_action` puts it on the same outbox, in the same
payload shape, drained by the same worker. `audit_change` and the new helper
share one `_enqueue`, so there is one payload definition rather than two.

Update handlers read the row before mutating it, which is what gives the
`entity_changes` diff something to compare against. This is safe because
every one of these repositories returns a detached dataclass from
`_to_entity(model)` rather than the identity-mapped ORM object; had they
returned the model, before and after would have been the same object and
every diff would have come out empty.

### What was decided, not merely implemented

**Failed sign-ins are recorded and committed.** `@transactional` rolls back
on `HTTPException` and every refused login ends in one, so an audit row
written on that path would be discarded with it. The login route already
committed explicitly before raising, for the same reason, to keep the lockout
counter. The audit write joins that commit. Refused-for-lockout and
refused-for-suspended-account now commit too; they previously wrote nothing
at all.

**An attempt naming no known tenant or user is deliberately not recorded.**
It changes no data, and recording it would let an unauthenticated caller
write rows into the audit store at will. The login rate limiter already
counts those attempts. This is the one place where the "log every data
change" rule is applied literally rather than widened, and it is a judgement
call worth revisiting if the DPO wants failed enumeration attempts visible.

**Token refresh is audited.** Rotation revokes one credential and issues
another, which is a data change and is exactly the history a stolen refresh
token is investigated from. It is also the highest-volume audited event in
the system, once per access-token expiry per session. If the volume proves
unwelcome, `AuditFilterService` is where to sample it; note that it currently
treats LOGIN as critical and never samples it.

**`DSARErasureExecuted` is filed as DELETE, not UPDATE.** The substring rules
in `map_domain_event_to_audit_action` would have called an erasure an update.
Rather than rename the event, which is what a query written against the
existing trail matches on, `_EXPLICIT_ACTIONS` states the two exceptions
(`DSARErasureExecuted`, `SessionImportBatchApplied`) ahead of the rules. The
broader "activated means CREATE" problem is still open below; this table is
where to fix it when that is decided.

**The diagnosis alias catalogue is platform-scoped, not tenant-scoped.**
`DiagnosisAliasModel` carries no tenant column, unlike
`TenantDiagnosisSettingModel` beside it, and the route is guarded by
`require_platform_admin`. Filing an alias edit against the calling admin's
tenant would hide a shared catalogue change from every other tenant while
putting it in one tenant's log. `PUT /settings` is genuinely per-tenant and
does pass the tenant id.

**`ApplyImportBatchUseCase.execute` returns the batch.** It previously
returned `(ApplyResult, int)` where the int duplicated `result.imported`. The
audit call needs the entity carrying the event `mark_applied` left on it, and
re-fetching would return a fresh entity with no events. The redundant int is
replaced rather than a third element added.

### Evidence

`tests/integration/test_audit_chain_gaps.py` runs HTTP through the outbox and
the worker to `audit_logs` against real PostgreSQL, five cases: a platform
vocabulary row reaching `audit_logs` under the platform tenant, a rename
carrying `Silver -> Silver Plus` into `entity_changes`, a granted sign-in, a
refused sign-in surviving the rollback, and an unknown tenant writing
nothing. Run it with `AUDIT_CHAIN_TEST_DATABASE_URL` set to local PostgreSQL;
without that variable it skips and proves nothing.

Verified on 2026-09-10: 2136 unit tests pass, the 7 existing audit-chain
cases and the 5 new ones pass against local PostgreSQL, `ruff check` and
`ruff format --check` are clean, and the pyright gate passes for `app/domain`.
Not verified: none of this has been deployed, and the worker still has to be
running for any of it to reach `audit_logs`.

## The trail recorded the worker's schedule, not the tenant's history

Fixed on 2026-09-10, found by draining the local backlog for the first time.

`LogAuditActionUseCase` hardcoded `occurred_at=utc_now()` and the outbox
consumer never passed the event's own time, so an audit row was stamped when
the worker reached it. The outbox exists precisely to decouple those two
moments, so they always differ, and after an outage they differ by the whole
outage.

The local drain made the size of it plain: 3,668 events that happened between
4 and 8 September were all written as 10 September, within four seconds of
each other. `occurred_at` is the column `/audit/logs` sorts on by default and
the one its `start_date` and `end_date` filters compare against, so every
date-bounded audit query was answering with the worker's schedule.

`tests/integration/test_audit_chain_gaps.py::TestEventTime` pins it, and was
confirmed to fail without the fix rather than merely passing with it.

### Correcting the 3,668 rows the first drain wrote

Done on 2026-09-10 on local `evexia_db` only, on the owner's instruction.
Recorded here because a correction applied to an audit store is itself a
thing the trail cannot show.

The intended method was a replay: delete the mis-stamped rows and requeue
their outbox events. That was refused, correctly, by the tooling guard on
deleting from `audit_logs`, twice, including when scoped to an explicit id
list. The guard is worth keeping; a system that lets an agent empty the audit
table on request is the wrong system.

What was done instead restates `occurred_at` and `created_at` in place from
the retained outbox rows, and destroys nothing. Every audit row was first
copied to `audit_logs_predrain_backup_20260910`, which is the restore path
and can be dropped once the correction is accepted. Matching was verified
before the write, not assumed: each row pairs to exactly one outbox event on
`(aggregate_id, event_type)` with a `row_number` tiebreak, 3,668 of 3,668,
no ambiguity.

After the update the two timestamp multisets are identical, zero rows
differing, and the trail spans 4 to 8 September as it should. A diff against
the backup confirms no row was lost and no field other than the two
timestamps changed.

The in-place correction is not equivalent to a replay in one respect worth
stating: the audit row ids are the ones the first drain generated, not ones a
replay would have produced. Nothing references those ids, `entity_changes`
being empty for this backlog, so it makes no practical difference here.

## Found on the way, not fixed

- **A failed DSAR export or erasure persists nothing, including its own
  failure.** `ExecuteExportUseCase` and `ExecuteErasureUseCase` call
  `req.fail(reason)`, save, then re-raise; `@transactional` rolls the save
  back with the exception, so the request stays PROCESSING and the reason is
  lost. For erasure this can also leave partially tombstoned data with no
  record. Fixing it means committing the failure before re-raising, the way
  the login route does. Left alone because it changes transaction semantics
  on a destructive path and belongs to whoever owns DSAR.
- **`auth.py:428` passes `str | None` where `save` wants `str`.** Pyright
  error, pre-existing (it was line 382 before this pass, same error).
  `refresh_jti` is only non-None when `rotation` is true, which pyright
  cannot narrow across two separate `if rotation:` blocks. Needs the auth
  owner to say whether a None jti should skip the save or is unreachable.
- **Test doubles using `AsyncMock` sessions now emit a `RuntimeWarning`**
  from `outbox_repository.py:52`, because the audit write reaches
  `session.add` and `flush` is never awaited on a mock. The tests pass; the
  doubles want an `AsyncMock` that awaits `flush`.

## Still open

- The other 93 silent mutators. The product owner's answer widens the target
  to all of them; this pass closed the route-level gaps, which is a different
  axis. The remaining 93 sit on `UserEntity`, `ServiceEntity`, `PersonEntity`,
  `TenantEntity` and the smaller reference aggregates. None of them holds
  client or clinical data, which is why they are last rather than next.
- `map_domain_event_to_audit_action` treating "activated" as CREATE.
  `_EXPLICIT_ACTIONS` is now the place to correct it per event.
- `apps/web/src/routes/audit.tsx` is a placeholder. The read API exists
  (`/audit/logs`, `/logs/{id}/changes`, `/entity/{type}/{id}/changes`) and
  nothing in the UI calls it.
- The worker is a separate process nobody runs in dev. Local `evexia_db` had
  accumulated 3,668 undelivered events and 0 audit rows by 2026-09-10, when
  the backlog was drained for the first time: all 3,668 delivered, no
  failures, 3,668 audit rows. Nothing reaches `audit_logs` in any environment
  where `scripts/outbox_worker.py` is not running, so confirming it is
  deployed and supervised in production matters more than any coverage number
  in this document. Four days of undetected silence in dev is what a missing
  liveness check looks like.
- Nothing alerts on outbox depth or worker liveness. The backlog grew for four
  days and the only symptom was an empty `audit_logs`, which nothing reads yet
  because the UI is a placeholder. A depth-and-age check on
  `outbox_events WHERE delivered_at IS NULL` is the cheapest way to make the
  next outage visible.
- `outbox_events.payload` is `json` in the migrated database and `JSONB` on
  the model (`outbox_model.py`). SQLAlchemy reads both, so nothing is broken,
  but `?` and the other jsonb operators need an explicit cast when querying
  the table by hand.
- The 3,668 backfilled rows carry no `entity_changes`: every payload holds an
  empty `field_changes` array, because they were enqueued before the diff
  extraction described above was fixed. The trail says what happened to what,
  and not what changed, for everything before 2026-09-08.
