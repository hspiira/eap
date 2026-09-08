# Audit coverage: what is recorded, and what is not

The audit trail is event-driven. `audit_change` reads `entity.events`, so a
mutating method that appends nothing is invisible to `audit_logs` however
healthy the outbox and worker are. This document records which writes are
audited, the decisions behind that line, and what is still open.

## The decision

Clients and contracts are audited in full: creation, every field update, and
every lifecycle move. They were chosen first because they are the records a
person edits daily and the ones a dispute is argued from, and because a client
is the aggregate almost everything else hangs off.

Not decided here, and deliberately left: the remaining 122 silent mutators
across the other aggregates. Auditing everything indiscriminately is not
automatically right, and for special-category health data it creates its own
disclosure surface, which is why `test_audit_coverage.py` refuses to assert it.
That scope is a product call.

## What this pass changed

Baseline moved from 148 silent mutators to 122, which is three separate things
and they should not be read as one number:

| Change | Count | What it was |
| --- | --- | --- |
| Coverage | -14 | `ClientEntity` and `ContractEntity` now emit on create, on every field update, and on archive and restore. Neither has a silent mutator left. |
| Measurement | -3 | The detector follows a private helper. A method that hands the append to one, `ContractEntity._record_status_change`, read as silent while it emitted. |
| Measurement | -9 | The detector no longer reads `self.x == y` as an assignment, so read predicates like `is_active` were never mutators at all. |

Only the first is coverage. The other twelve were the ruler being wrong.

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

## Still open

- The other 122 silent mutators, pending the scope call above.
- `map_domain_event_to_audit_action` treating "activated" as CREATE.
- `apps/web/src/routes/audit.tsx` is a placeholder. The read API exists
  (`/audit/logs`, `/logs/{id}/changes`, `/entity/{type}/{id}/changes`) and
  nothing in the UI calls it.
- The worker is a separate process nobody runs in dev, so a local database
  accumulates outbox rows and no audit rows. Local `evexia_db` held 3,668
  undelivered events and 0 audit rows when this was written.
