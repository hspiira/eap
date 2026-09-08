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

Not decided here, and deliberately left: the remaining 101 silent mutators
across the other aggregates. Auditing everything indiscriminately is not
automatically right, and for special-category health data it creates its own
disclosure surface, which is why `test_audit_coverage.py` refuses to assert it.
That scope is a product call.

## What this pass changed

Baseline moved from 148 silent mutators to 101, which is three separate things
and they should not be read as one number:

| Change | Count | What it was |
| --- | --- | --- |
| Coverage | -14 | `ClientEntity` and `ContractEntity` now emit on create, on every field update, and on archive and restore. Neither has a silent mutator left. |
| Coverage | -9 | `ServiceAssignmentEntity` in full, and `EligibleMember` apart from the three above. |
| Coverage | -12 | `ServiceSessionEntity` in full, under the redaction rule below. |
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

## Members are audited twice over, by two mechanisms

`members.py` records every roster mutation through `record_member_change`,
which enqueues an outbox row directly with `is_special_category` set and
`field_changes` always empty. `eligible_members.py`, the employer-side router
for the same aggregate, uses `audit_change` instead. Neither calls the other,
so nothing is recorded twice, but the two paths disagree about what an audit
row contains: only the second carries a diff.

Converging `members.py` onto `audit_change` would give roster edits the same
field-level detail the rest now has. It is ten call sites in a route file with
its own tests, so it is named here rather than folded into this pass.

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

## Still open

- The other 113 silent mutators, pending the scope call above.
- `members.py` on its own audit path, above.
- The other clinical aggregates. `Case`, `ClinicalNote` and the rest are
  already in `CLINICAL_RESOURCE_TYPES`, so the redaction rule covers them the
  moment they emit. Nothing in this pass made them emit.
- `map_domain_event_to_audit_action` treating "activated" as CREATE.
- `apps/web/src/routes/audit.tsx` is a placeholder. The read API exists
  (`/audit/logs`, `/logs/{id}/changes`, `/entity/{type}/{id}/changes`) and
  nothing in the UI calls it.
- The worker is a separate process nobody runs in dev, so a local database
  accumulates outbox rows and no audit rows. Local `evexia_db` held 3,668
  undelivered events and 0 audit rows when this was written.
